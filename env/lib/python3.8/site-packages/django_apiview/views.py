import logging
import functools
import json
import uuid
from inspect import signature

import bizerror
from fastutils import jsonutils
from fastutils import rsautils
from fastutils import strutils
from fastutils import funcutils
from fastutils import typingutils
from fastutils import cipherutils

from django.http import HttpResponse
from django.conf import settings

from .utils import get_request_data
from .pack import SimpleJsonResultPacker
from .pack import SafeJsonResultPacker

logger = logging.getLogger(__name__)

simple_result_packer = SimpleJsonResultPacker()

class _Null(object):
    pass
_Null = _Null()

def setup_result_packer(packer):
    global simple_result_packer
    simple_result_packer = packer

class DoNotPack(RuntimeError):
    pass

class ApiviewDecorator(object):
    """Decorator base class.
    """

    def __call__(self, func):
        def wrapper(_django_apiview_request):
            return self.main(_django_apiview_request, func)
        wrapper._apiview_decorator = True
        return functools.wraps(func)(wrapper)

    def main(self, _django_apiview_request, func):
        return _django_apiview_request.process(func)

class ApiviewRequest(object):
    """Process class of apiview.
    """

    def __init__(self, request, defaults, **kwargs):
        self._apiview_decorator = False
        self.request = request
        self.kwargs = kwargs
        self.data = {}
        self.data.update(defaults)
        self.data.update(get_request_data(self.request, self.kwargs))
        self.data["_django_apiview_request"] = self
        self.data["_django_apiview_response"] = HttpResponse(content_type="application/json;charset=UTF-8")

    def process(self, func):
        if hasattr(func, "_apiview_decorator") and getattr(func, "_apiview_decorator"):
            return func(_django_apiview_request=self)
        else:
            logger.debug("ApiviewRequest calling funcutils.call_with_inject: func={func} data={data}".format(func=signature(func), data=self.data))
            result = funcutils.call_with_inject(func, self.data)
            logger.debug("ApiviewRequest call funcutils.call_with_inject done, result={result}".format(result=result))
            return result

class Apiview(object):
    def __init__(self, packer, preload_plugins=None, extra_parameters=None, **kwargs):
        self.packer = packer
        self.extra_parameters = extra_parameters or {}
        self.preload_plugins = preload_plugins or []
        self.apiview_init_kwargs = kwargs

    def set_packer(self, packer):
        self.packer = packer

    def add_preload_plugin(self, plugin):
        self.preload_plugins.append(plugin)

    def put_extra_parameter(self, key, value):
        self.extra_parameters[key] = value

    def put_extra_parameters(self, params):
        self.extra_parameters.update(params)

    def __call__(self, func):
        """Turn the view function into apiview function. Must use as the first decorator.
        """
        def wrapper(request, **kwargs):
            target_func = func
            defaults = {}
            defaults.update(self.extra_parameters)
            defaults.update(funcutils.get_default_values(func))
            _django_apiview_request = ApiviewRequest(request, defaults, **kwargs)
            package = {}
            try:
                for plugin in reversed(self.preload_plugins):
                    target_func = plugin(target_func)
                result = _django_apiview_request.process(target_func)
                package = self.packer.pack_result(result, **_django_apiview_request.data)
                package_json = jsonutils.simple_json_dumps(package, ensure_ascii=False, allow_nan=True, sort_keys=True)
                _django_apiview_request.data["_django_apiview_response"].write(package_json)
            except DoNotPack:
                # do not need to do result pack
                pass
            except Exception as error:
                logger.exception("apiview process failed: {}".format(str(error)))
                if not isinstance(error, bizerror.BizErrorBase):
                    error = bizerror.BizError(error)
                package = self.packer.pack_error(error, **_django_apiview_request.data)
                package_json = jsonutils.simple_json_dumps(package, ensure_ascii=False, allow_nan=True, sort_keys=True)
                _django_apiview_request.data["_django_apiview_response"].write(package_json)
            return _django_apiview_request.data["_django_apiview_response"]
        wrapper.csrf_exempt = True
        return functools.wraps(func)(wrapper)

apiview = Apiview(simple_result_packer)

class requires(ApiviewDecorator):
    """Make sure the parameters are given.
    """
    def __init__(self, *required_parameter_names):
        self.required_parameter_names = required_parameter_names

    def main(self, _django_apiview_request, func):
        missing_names = []
        for name in self.required_parameter_names:
            if isinstance(name, str):
                if not name in _django_apiview_request.data:
                    missing_names.append(name)
            elif isinstance(name, (list, set, tuple)):
                flag = False
                for element in name:
                    if _django_apiview_request.data.get(element, None):
                        flag = True
                        break
                if not flag:
                    missing_names.append("({0})".format(" or ".join(name)))
        if missing_names:
            raise bizerror.MissingParameter(parameter=",".join(missing_names))
        return super().main(_django_apiview_request, func)

class choices(ApiviewDecorator):
    """Make sure field's value is in the choices.
    """
    def __init__(self, field, choices, annotation=None, allow_none=False):
        self.field = field
        self.choices = choices
        self.annotation = annotation
        self.allow_none = allow_none

    def main(self, _django_apiview_request, func):
        if callable(self.choices):
            params = funcutils.get_inject_params(self.choices, _django_apiview_request.data)
            values = self.choices(**params)
        else:
            values = self.choices
        value = _django_apiview_request.data.get(self.field, None)
        if self.annotation:
            value = typingutils.smart_cast(self.annotation, value)
        if (self.allow_none and value is None) or (value in self.choices):
            return super().main(_django_apiview_request, func)
        else:
            raise bizerror.BadParameter("field {0}'s value '{1}' is not in choices {2}.".format(self.field, value, values))

class between(ApiviewDecorator):
    """Make sure field's numeric value is in range of (min, max).
    """

    def __init__(self, field, min, max, include_min=True, include_max=True, annotation=typingutils.Number, allow_none=False):
        self.field = field
        self.min = min
        self.max = max
        self.include_min = include_min
        self.include_max = include_max
        self.annotation = annotation
        self.allow_none = allow_none
    
    def main(self, _django_apiview_request, func):
        field = self.field
        min = self.min
        max = self.max
        include_min = self.include_min
        include_max = self.include_max
        annotation = self.annotation
        allow_none = self.allow_none

        if callable(min):
            params = funcutils.get_inject_params(min, _django_apiview_request.data)
            min_value = min(**params)
        else:
            min_value = min
        if callable(max):
            params = funcutils.get_inject_params(max, _django_apiview_request.data)
            max_value = max(**params)
        else:
            max_value = max
        value = _django_apiview_request.data.get(field, None)
        value = typingutils.smart_cast(self.annotation, value)
        if (allow_none and value is None) or ((include_min and min_value <= value or min_value < value) and (include_max and max_value >= value or max_value > value)):
            return super().main(_django_apiview_request, func)
        else:
            raise bizerror.BadParameter("field {0}'s value '{1}' is not in range of {2}{3}, {4}{5}.".format(
                field, value,
                include_min and "[" or "(", 
                min_value, max_value,
                include_max and "]" or ")",
                ))

class rsa_decrypt(ApiviewDecorator):
    """Do rsa-decrypt to the given field with private_key.
    """

    def __init__(self, field, private_key):
        self.field = field
        self.private_key = private_key
    
    def main(self, _django_apiview_request, func):
        if self.field in _django_apiview_request.data:
            field_value = _django_apiview_request.data[self.field]
            if field_value:
                field_data = rsautils.smart_get_binary_data(field_value)
                plain_data = rsautils.decrypt(field_data, self.private_key)
                plain_text = plain_data.decode("utf-8")
                _django_apiview_request.data[self.field] = plain_text
        return super().main(_django_apiview_request, func)

class cookie_variable(ApiviewDecorator):
    """Get variable from cookies.
    """
    def __init__(self, variable_name, cookie_name):
        self.variable_name = variable_name
        self.cookie_name = cookie_name
    
    def main(self, _django_apiview_request, func):
        value = _django_apiview_request.request.COOKIES.get(self.cookie_name, _Null)
        if not value is _Null:
            _django_apiview_request.data[self.variable_name] = value
        return super().main(_django_apiview_request, func)

class meta_variable(ApiviewDecorator):
    """Get variable from meta.
    """
    def __init__(self, variable_name, meta_name):
        self.variable_name = variable_name
        self.meta_name = meta_name
    
    def main(self, _django_apiview_request, func):
        value = _django_apiview_request.request.META.get(self.meta_name, _Null)
        if not value is _Null:
            _django_apiview_request.data[self.variable_name] = value
        return super().main(_django_apiview_request, func)

class cache(ApiviewDecorator):

    related_models_mapping = {}

    @classmethod
    def get_entry_points(cls, app_label=None):
        if not app_label:
            eps = list(cls.related_models_mapping.values())
            eps.sort(key=lambda x:x["entry_point"])
            return eps
        else:
            eps = []
            for ep in list(cls.related_models_mapping.keys()):
                if app_label == ep.split(".")[0]:
                    eps.append(cls.related_models_mapping[ep])
            eps.sort(key=lambda x:x["entry_point"])
            return eps

    def keep_related_models_mapping(self):
        entry_point = id(self)
        self.related_models_mapping[entry_point] = {
            "entry_point": entry_point,
            "related_models": [] + self.related_models,
            "key": self.key,
        }
        logger.info("Cache entry discovered: {0}".format(self.related_models_mapping[entry_point]))

    def __init__(self, key, expire=None, cache_name="default", get_from_cache=None, set_to_cache=True, disable_get_from_cache_header=None, batch_mode=False, ignore_cache_errors=True, related_models=None):
        self.key = key
        self.expire = expire or getattr(settings, "DJANGO_APIVIEW_DEFAULT_CACHE_EXPIRE", None)
        self.expire = self.expire and int(self.expire) or None
        self.cache_name = cache_name
        self.get_from_cache = get_from_cache
        self.set_to_cache = set_to_cache
        self.disable_get_from_cache_header = disable_get_from_cache_header or getattr(settings, "DJANGO_APIVIEW_DISABLE_CACHE_HEADER_NAME", "HTTP_DISABLE_CACHE")
        self.batch_mode = batch_mode
        self.ignore_cache_errors = ignore_cache_errors
        self.related_models = related_models or []
        self.keep_related_models_mapping()

    def main(self, _django_apiview_request, func):
        # Import here, so that we don't need django-redis by default.
        # Only if you use cache, then you need pip install django-redis
        from django_redis import get_redis_connection

        key_template = self.key
        expire = self.expire
        cache_name = self.cache_name
        get_from_cache = self.get_from_cache
        set_to_cache = self.set_to_cache
        disable_get_from_cache_header = self.disable_get_from_cache_header
        batch_mode = self.batch_mode
        ignore_cache_errors = self.ignore_cache_errors

        if get_from_cache == False:
            get_from_cache_final = False
        else:
            if _django_apiview_request.request.META.get(disable_get_from_cache_header, "false") == "true":
                get_from_cache_final = False
            else:
                get_from_cache_final = True

        set_to_cache_final = set_to_cache
        use_cache = get_from_cache_final or set_to_cache_final

        cache = None
        if use_cache:
            try:
                cache = get_redis_connection(cache_name)
            except Exception as error:
                logger.exception("get redis connection failed @cache, error_message={0}".format(str(error)))
                if ignore_cache_errors:
                    cache = None
                else:
                    raise

        if cache and get_from_cache:
            try:
                key = strutils.format_with_mapping(
                    key_template,
                    funcutils.chain(strutils.none_to_empty_string, strutils.strip_string),
                    **_django_apiview_request.data,
                    )
                result_text = cache.get(key)
                if not result_text is None:
                    return json.loads(result_text)
            except Exception as error:
                logger.exception("query redis failed @cache, error_message={0}".format(str(error)))
                if not ignore_cache_errors:
                    raise

        result = super().main(_django_apiview_request, func)

        def _set_cache(result, **kwargs):
            if isinstance(result, dict):
                key = strutils.format_with_mapping(
                    key_template,
                    funcutils.chain(strutils.none_to_empty_string, strutils.strip_string),
                    **_django_apiview_request.data, **result, **kwargs
                    )
            else:
                key = strutils.format_with_mapping(
                    key_template,
                    funcutils.chain(strutils.none_to_empty_string, strutils.strip_string),
                    **_django_apiview_request.data, **kwargs,
                    )
            result_text = jsonutils.simple_json_dumps(result, allow_nan=True, sort_keys=True)
            cache.set(key, result_text)
            if expire:
                cache.expire(key, expire) # Old version redis don't support add ttl while doing set key value, so do set ttl separately
        
        if cache and set_to_cache_final:
            try:
                if batch_mode:
                    if isinstance(result, list):
                        for element in result:
                            _set_cache(element)
                    elif isinstance(result, dict):
                        for key, value in result.items():
                            _set_cache(value, __key=key, __value=value)
                else:
                    _set_cache(result)
            except Exception as error:
                logger.exception("write redis failed @cache, error_message={0}".format(str(error)))
                if not ignore_cache_errors:
                    raise

        return result

class decode_encrypted_data(ApiviewDecorator):

    def __init__(self, result_encoder=cipherutils.SafeBase64Encoder(), privatekey=None, server_rsa_privatekey_filedname="RSA_PRIVATEKEY", encrypted_password_fieldname="encryptedPassword", encrypted_data_fieldname="encryptedData"):
        self.result_encoder = result_encoder
        self.server_rsa_privatekey_filedname = server_rsa_privatekey_filedname
        self.privatekey = privatekey
        self.encrypted_password_fieldname = encrypted_password_fieldname
        self.encrypted_data_fieldname = encrypted_data_fieldname

    def main(self, _django_apiview_request, func):
        privatekey = self.privatekey or getattr(settings, self.server_rsa_privatekey_filedname, None)
        encrypted_password = _django_apiview_request.data.get(self.encrypted_password_fieldname, "")
        encrypted_data = _django_apiview_request.data.get(self.encrypted_data_fieldname, "")
        if privatekey and encrypted_password and encrypted_data:
            password = rsautils.decrypt(encrypted_password, privatekey)
            cipher = cipherutils.AesCipher(password=password, result_encoder=self.result_encoder)
            data_text = cipher.decrypt(encrypted_data)
            data = json.loads(data_text)
            _django_apiview_request.data.update(data)
        return super().main(_django_apiview_request, func)

def safe_apiview(packer_class=SafeJsonResultPacker, **kwargs):
    return Apiview(
        packer=funcutils.call_with_inject(packer_class, kwargs),
        preload_plugins = [
            funcutils.call_with_inject(decode_encrypted_data, kwargs),
            ],
        extra_parameters=kwargs,
        )

DEFAULT_RANDOM_DJANGO_APIVIEW_ACLKEY = str(uuid.uuid4())
logger.info("Default random DJANGO_APIVIEW_ACLKEY={0}".format(DEFAULT_RANDOM_DJANGO_APIVIEW_ACLKEY))

class check_aclkey(ApiviewDecorator):

    def __init__(self, aclkey=None, aclkey_field_name="aclkey"):
        self.aclkey_field_name = aclkey_field_name
        self.aclkey = aclkey or getattr(settings, "DJANGO_APIVIEW_ACLKEY", DEFAULT_RANDOM_DJANGO_APIVIEW_ACLKEY)
    
    def main(self, _django_apiview_request, func):
        if not self.aclkey_field_name in _django_apiview_request.data:
            raise bizerror.MissingParameter(parameter=self.aclkey_field_name)
        aclkey = _django_apiview_request.data[self.aclkey_field_name]
        if not self._check_aclkey(aclkey, _django_apiview_request):
            raise bizerror.AppAuthFailed()
        return super().main(_django_apiview_request, func)

    def _check_aclkey(self, aclkey, _django_apiview_request):
        if callable(self.aclkey):
            aclkey = funcutils.call_with_inject(self.aclkey, _django_apiview_request.data)
        return self.aclkey == aclkey

class string_length_limit(ApiviewDecorator):
    """Check string parameter length.
    """
    def __init__(self, field, max_length, min_length=0, string_too_short_error_message=None, string_too_long_error_message=None):
        self.field = field
        self.max_length = max_length
        self.min_length = min_length
        self.string_too_short_error_message = string_too_short_error_message
        self.string_too_long_error_message = string_too_long_error_message
    
    def main(self, _django_apiview_request, func):
        value = _django_apiview_request.data.get(self.field, None)
        if not value is None:
            value_length = len(value)
            if value_length < self.min_length:
                raise bizerror.StringTooShort(message=self.string_too_short_error_message, min_length=self.min_length)
            if value_length > self.max_length:
                raise bizerror.StringTooLong(message=self.string_too_long_error_message, max_length=self.max_length)
        return super().main(_django_apiview_request, func)
