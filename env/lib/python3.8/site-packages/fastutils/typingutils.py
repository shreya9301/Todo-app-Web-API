import json
import binascii
import base64
import typing
import decimal
import uuid
from numbers import Number

import bizerror
from . import strutils

STRING_ENCODINGS = ["utf-8", "gb18030"]


def cast_int(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        raise bizerror.CastToIntegerFailed()

def cast_float(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, float):
        return value
    try:
        return float(value)
    except Exception:
        raise bizerror.CastToFloatFailed()

def cast_bool(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ["true", "yes", "y", "t", "1"]:
            return True
        else:
            return False
    if isinstance(value, int):
        if value != 0:
            return True
        else:
            return False
    if value:
        return True
    else:
        return False

def cast_list(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except:
            try:
                value = [x.strip() for x in value.split(",")]
            except:
                pass
    if not isinstance(value, list):
        return [value]
    else:
        return value

def cast_bytes(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        if strutils.is_unhexlifiable(value):
            return binascii.unhexlify(value)
        elif strutils.is_base64_decodable(value):
            return base64.decodebytes(value.encode())
        elif strutils.is_urlsafeb64_decodable(value):
            return base64.urlsafe_b64decode(value.encode())
        else:
            return value.encode("utf-8")
    value = str(value)
    return value.encode("utf-8")

def cast_str(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode()
        except:
            for encoding in STRING_ENCODINGS:
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    pass
    return str(value)

def cast_dict(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value.encode("utf-8"))
        except:
            pass
    return dict(value)

def cast_numeric(value):
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
    if isinstance(value, Number):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    value = str(value)
    if "." in value:
        return float(value)
    else:
        return int(value)

def cast_uuid(value):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, bytes):
        return uuid.UUID(bytes=value)
    elif isinstance(value, (tuple, list)):
        return uuid.UUID(fields=value)
    elif isinstance(value, int):
        return uuid.UUID(int=value)
    else:
        return uuid.UUID(value)


TYPE_CASTERS = {}

def register_global_caster(type, caster):
    TYPE_CASTERS[type] = caster

register_global_caster(int, cast_int)
register_global_caster(float, cast_float)
register_global_caster(bool, cast_bool)
register_global_caster(bytes, cast_bytes)
register_global_caster(str, cast_str)
register_global_caster(list, cast_list)
register_global_caster(typing.List, cast_list)
register_global_caster(dict, cast_dict)
register_global_caster(typing.Mapping, cast_dict)
register_global_caster(Number, cast_numeric)
register_global_caster(uuid.UUID, cast_uuid)

def smart_cast(type, value, field_name=None):
    field_name = field_name or ""
    if type in TYPE_CASTERS:
        type_func = TYPE_CASTERS[type]
    elif callable(type):
        type_func = type
    else:
        raise bizerror.NotSupportedTypeToCast(field=field_name, type=str(type(value)), value=str(value))
    try:
        return type_func(value)
    except Exception as error:
        if not isinstance(error, bizerror.CastFailedError):
            error = bizerror.CastFailedError(error=str(error))
        error.update(field=field_name, value=str(value))
        raise error


