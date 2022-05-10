import json
import uuid
import binascii
import datetime
import decimal
from io import BytesIO
from functools import partial

import bizerror

try:
    from PIL.Image import Image
except ImportError:
    Image = None
try:
    from django.db.models import Model
except ImportError:
    Model = None
try:
    from django.db.models import QuerySet
except ImportError:
    QuerySet = None
try:
    from django.db.models.sql.query import Query
except ImportError:
    Query = None
try:
    from django.core import serializers
except ImportError:
    serializers = None

try:
    from django.apps import apps
    from django.utils import timezone
except ImportError:
    apps = None
    timezone = None

default_simple_json_encoder_base = json.encoder.JSONEncoder

class JsonEncodeLibrary(object):

    def __init__(self, bases=tuple([default_simple_json_encoder_base])):
        self.bases = bases
        self.encoders = {}
        self.__encoder = None

    def get_encoder(self):
        if self.__encoder is not None:
            return self.__encoder
        def __default(encoder, o):
            for t, encoder in self.encoders.items():
                try:
                    isinstance_flag = isinstance(o, t)
                except:
                    isinstance_flag = False
                if isinstance_flag:
                    return encoder(o)
                try:
                    issubclass_flag = issubclass(o, t)
                except:
                    issubclass_flag = False
                if issubclass_flag:
                    return encoder(o)
            return super().default(o)
        self.__encoder = type("SimpleJsonEncoder", self.bases, {"default": __default})
        setattr(self.__encoder, "library", self)
        return self.__encoder

    def register(self, type, encode):
        self.encoders[type] = encode

    def unregister(self, type):
        if type in self.encoders:
            del self.encoders[type]

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def set_datetime_format(format):
    global DATETIME_FORMAT
    DATETIME_FORMAT = format

def encode_datetime(value):
    if apps and timezone and apps.ready:
        value = timezone.make_naive(value)
    return value.strftime(DATETIME_FORMAT)

def encode_bytes(value):
    return binascii.hexlify(value).decode()

def encode_decimal(value):
    return float(value)

def encode_complex(value):
    return [value.real, value.imag]

def encode_uuid(value):
    return str(value)

def encode_image(image):
    from . import imageutils
    buffer = BytesIO()
    image.save(buffer, format="png")
    return imageutils.get_base64image(buffer.getvalue())

def encode_exception(error):
    return bizerror.BizError(error).json

def encode_bizerror(error):
    return error.json

def encode_django_model(django_model):
    try:
        isinstance_flag = isinstance(django_model, Model)
    except:
        isinstance_flag = False
    try:
        issubclass_flag = issubclass(django_model, Model)
    except:
        issubclass_flag = False
    if issubclass_flag:
        return ".".join([django_model._meta.app_label, django_model._meta.model_name])
    if isinstance_flag:
        pk_name = django_model._meta.pk.name
        text = serializers.serialize("json", [django_model])
        results = json.loads(text)
        obj = results[0]["fields"]
        obj[pk_name] = results[0]["pk"]
        return obj
    return None

def encode_django_queryset(django_queryset):
    pk_name = django_queryset.model._meta.pk.name
    text = serializers.serialize("json", django_queryset)
    results = json.loads(text)
    data = []
    for result in results:
        obj = result["fields"]
        obj[pk_name] = result["pk"]
        data.append(obj)
    return data

def encode_django_query(django_query):
    return str(django_query)

GLOBAL_ENCODERS = {}

def register_global_encoder(type, encoder):
    GLOBAL_ENCODERS[type] = encoder

def register_simple_encoders(library):
    for type, encoder in GLOBAL_ENCODERS.items():
        library.register(type, encoder)


register_global_encoder((datetime.datetime, datetime.date, datetime.time), encode_datetime)
register_global_encoder(bytes, encode_bytes)
register_global_encoder(decimal.Decimal, encode_decimal)
register_global_encoder(complex, encode_complex)
register_global_encoder(uuid.UUID, encode_uuid)
register_global_encoder(bizerror.BizErrorBase, encode_bizerror)
register_global_encoder(Exception, encode_exception)
if Image:
    register_global_encoder(Image, encode_image)
if Model:
    register_global_encoder(Model, encode_django_model)
if QuerySet:
    register_global_encoder(QuerySet, encode_django_queryset)
if Query:
    register_global_encoder(Query, encode_django_query)


def make_simple_json_encoder(bases=tuple([default_simple_json_encoder_base])):
    library = JsonEncodeLibrary(bases)
    register_simple_encoders(library)
    return library.get_encoder()

SimpleJsonEncoder = make_simple_json_encoder()
simple_json_dumps = partial(json.dumps, cls=SimpleJsonEncoder)

