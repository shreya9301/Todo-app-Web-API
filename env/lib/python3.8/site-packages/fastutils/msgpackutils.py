"""
Python's object serialization using msgpack.
Extra types are supported: datetime, UUID, set.
Add a data wrapper class [Msg] for rpc client&server communications. 
"""
import datetime
import uuid
import msgpack
from . import cipherutils


# Note: Tuple class can not be auto translated, it will be always treated as List type.

msgpack_custom_type_encode_infos = {
    datetime.datetime: {
        "type": "Datetime",
        "encode": lambda obj: obj.isoformat(),
    },
    uuid.UUID: {
        "type": "UUID",
        "encode": lambda obj: str(obj),
    },
    set: {
        "type": "Set",
        "encode": lambda obj: list(obj),
    },
}

msgpack_custom_type_decode_infos = {
    "Datetime": lambda value: datetime.datetime.fromisoformat(value),
    "UUID": lambda value: uuid.UUID(value),
    "Set": lambda value: set(value),
}

def _msg_encode(obj):
    """Add extra data type handler for msgpack.dumps.
    """
    for _type, type_info in msgpack_custom_type_encode_infos.items():
        if isinstance(obj, _type):
            obj = {
                "__msg_type__": type_info["type"],
                "__msg_value__": type_info["encode"](obj)
            }
            break
    return obj

def _msg_decode(obj):
    """Add extra data type handler for msgpack.loads. Work together with _msg_encode.
    """
    if isinstance(obj, dict):
        if "__msg_type__" in obj:
            return msgpack_custom_type_decode_infos[obj["__msg_type__"]](obj["__msg_value__"])
    return obj

def dumps(*args, **kwargs):
    """Do msgpack.dumps with extra data type handlers.
    """
    if not "default" in kwargs:
        kwargs["default"] = _msg_encode
    return msgpack.dumps(*args, **kwargs)

def loads(*args, **kwargs):
    """Do msgpack.loads with extra data type handlers.
    """
    if not "object_hook" in kwargs:
        kwargs["object_hook"] = _msg_decode
    return msgpack.loads(*args, **kwargs)

pack = dumps # alias
unpack = loads # alias

class WrongMsgType(Exception):
    """Msg's type must be one of MSG_REQUEST or MSG_RESPONSE.
    """
    pass

class EmptyMsgData(Exception):
    """Can not load Msg from an empty bytes.
    """
    pass

class MsgDecryptFailed(Exception):
    """Can not decrypt the Msg bytes. Check if the password matches in dump and load.
    """
    pass

class Msg(object):
    """Message wrapper.

    A message is an object contains id, type and data fields. e.g.
    {
        "id": "10cb2df9-0a51-4301-976e-1bdcaa70269b",
        "type": 10, # 10 means MSG_REQUEST, 20 means MSG_RESPONSE
        "data": {"user defined message structure": "user value"},
    }

    Example:

    In [7]: from fastutils import msgpackutils

    In [8]: msg = msgpackutils.Msg.make(msgpackutils.Msg.MSG_REQUEST, {"user defined message structure": "user value"})

    In [9]: msg
    Out[9]: <fastutils.msgpackutils.Msg at 0x1e4e9179c10>

    In [10]: print(msg)
    Msg(MSG_REQUEST,10cb2df9-0a51-4301-976e-1bdcaa70269b)

    In [13]: msg.dumps()
    Out[13]: b'\\x93\\xd9$da2226a3-1da7-4a1c-94de-bc9ca279437a\\n\\x81\\xbeuser defined message structure\\xaauser value'
    """
    MAGIC_CODE = b"EMsg" # MAGIC leading bytes after doing AES encryption.

    MSG_REQUEST = 10
    MSG_RESPONSE = 20
    MSG_TYPES = {
        MSG_REQUEST: "MSG_REQUEST",
        MSG_RESPONSE: "MSG_RESPONSE",
    }
    MSG_TYPE_UNKNOWN_DISPLAY = "MSG_TYPE_UNKNOWN"

    def __init__(self, password=None, cipher=None):
        """Create an empty Msg instance.

        If the parameter password or cipher is given, it will do encrypt while doing dumps and it will do decrypt while doing loads.
        If the parameter cipher is given, use the given cipher to do encrypt and decrypt.
        If the parameter cipher is NOT given and password is given, use AesCipher(password=password) as the final cipher.
        """
        self.type = None
        self.data = None
        self.id = None
        if cipher:
            self.cipher = cipher
        elif password:
            self.cipher = cipherutils.AesCipher(password=password)
        else:
            self.cipher = None

    def __str__(self):
        """Better Msg display in print.
        """
        type_display = self.get_type_display()
        id_display = str(self.id)
        return f"Msg({type_display},{id_display})"

    def get_type_display(self):
        if self.type is None:
            return "None"
        elif self.type in self.MSG_TYPES:
            return self.MSG_TYPES[self.type]
        else:
            return self.MSG_TYPE_UNKNOWN_DISPLAY

    def as_dict(self):
        """Turn a Msg to a dict.
        """
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
        }

    @classmethod
    def make(cls, type:int, data:dict, id:str=None, password:str=None):
        """Make a Msg instance with the given field values.
        """
        if not type in cls.MSG_TYPES:
            raise WrongMsgType()
        obj = cls(password=password)
        obj.id = id or str(uuid.uuid4())
        obj.type = type
        obj.data = data
        return obj
    
    @classmethod
    def make_msg(cls, msg:dict, password:str=None):
        """Make a Msg instance from a dict. Returns a new Msg instance.
        """
        return cls.make(password=password, **msg)

    def dumps(self):
        """Dump instance fields' value into bytes.
        """
        data = dumps((self.id, self.type, self.data), default=_msg_encode)
        if self.cipher:
            data = self.cipher.encrypt(self.MAGIC_CODE+data)
        return data

    def loads(self, data):
        """Load data into instance's fields. Note: All instance's field value will be overrided.
        """
        if not data:
            raise EmptyMsgData()
        if self.cipher:
            data = self.cipher.decrypt(data)
        if not data.startswith(self.MAGIC_CODE):
            raise MsgDecryptFailed()
        data = data[len(self.MAGIC_CODE):]
        self.id, self.type, self.data = loads(data, object_hook=_msg_decode)
        return self
