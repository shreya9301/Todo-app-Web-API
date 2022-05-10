import copy
import json
import base64
import binascii
import string

from Crypto.Cipher import AES

from . import strutils
from . import randomutils
from . import aesutils
from . import rsautils
from . import funcutils

from .aesutils import get_aes_mode

from .aesutils import get_md5_key as md5_key
from .aesutils import get_mysql_aes_key as mysql_aes_key
from .aesutils import get_sha1prng_key as sha1prng_key
from .aesutils import get_raw_aes_key as raw_aes_key

from .aesutils import padding_ansix923 as aes_padding_ansix923
from .aesutils import padding_iso10126 as aes_padding_iso10126
from .aesutils import padding_pkcs5 as aes_padding_pkcs5
from .listutils import first

class DecryptFailed(RuntimeError):
    pass

class EncoderBase(object):

    def encode(self, data: bytes) -> str:
        raise NotImplementedError()

    def decode(self, data: str) -> bytes:
        raise NotImplementedError()

class RawDataEncoder(EncoderBase):

    def encode(self, data: bytes) -> bytes:
        return data
    
    def decode(self, data: bytes) -> bytes:
        return data

class HexlifyEncoder(EncoderBase):

    def encode(self, data: bytes) -> str:
        if data is None:
            return None
        return binascii.hexlify(data).decode()

    def decode(self, data: str) -> bytes:
        if data is None:
            return None
        return binascii.unhexlify(data.encode("utf-8"))

class Base64Encoder(EncoderBase):

    def encode(self, data: bytes) -> str:
        if data is None:
            return None
        return strutils.join_lines(base64.encodebytes(data)).decode()

    def decode(self, data: str) -> bytes:
        if data is None:
            return None
        return base64.decodebytes(data.encode("utf-8"))

class SafeBase64Encoder(EncoderBase):

    def encode(self, data: bytes) -> str:
        if data is None:
            return None
        return strutils.join_lines(base64.urlsafe_b64encode(data)).decode()

    def decode(self, data: str) -> bytes:
        if data is None:
            return None
        return base64.urlsafe_b64decode(data.encode("utf-8"))

class Utf8Encoder(EncoderBase):
    
    def encode(self, data: bytes) -> str:
        if not data:
            return None
        return data.decode("utf-8")

    def decode(self, data: str) -> bytes:
        if not data:
            return None
        return data.encode("utf-8")

class _SimpleCipher(object):

    def __init__(self, encrypt, decrypt):
        self.encrypt = encrypt
        self.decrypt = decrypt

class CipherBase(object):
    """params: password, result_encoder, force_text, text_encoding, cipher_core, encrypt, decrypt, encrypt_kwargs, decrypt_kwargs
    """
    default_encrypt_force_bytes = True
    default_decrypt_force_bytes = True
    default_encrypt_kwargs = {}
    default_decrypt_kwargs = {}
    default_result_encoder = None
    default_force_text = None
    default_text_encoding = None
    default_cipher_core = None

    def get_defaults(self):
        defaults = {
            "encrypt_force_bytes": self.default_encrypt_force_bytes,
            "decrypt_force_bytes": self.default_decrypt_force_bytes,
            "encrypt_kwargs": self.default_encrypt_kwargs,
            "decrypt_kwargs": self.default_decrypt_kwargs,
            "result_encoder": self.default_result_encoder,
            "force_text": self.default_force_text,
            "text_encoding": self.default_text_encoding,
            "cipher_core": self.default_cipher_core,
        }
        if hasattr(self, "defaults"):
            defaults.update(getattr(self, "defaults"))
        return defaults

    def __init__(self, 
            password=None,
            encrypt_force_bytes=None,
            decrypt_force_bytes=None,
            encrypt_kwargs=None,
            decrypt_kwargs=None,
            result_encoder=None,
            force_text=None,
            text_encoding=None,
            cipher_core=None,
            encrypt=None,
            decrypt=None,
            kwargs=None,
            **extra_kwargs,
            ):
        kwargs = kwargs or {}
        defaults = self.get_defaults()
        self.password = password
        self.encrypt_force_bytes = first(encrypt_force_bytes, defaults["encrypt_force_bytes"], True)
        self.decrypt_force_bytes = first(decrypt_force_bytes, defaults["decrypt_force_bytes"], True)
        self.result_encoder = first(result_encoder, defaults["result_encoder"], RawDataEncoder())
        self.force_text = first(force_text, defaults["force_text"], False)
        self.text_encoding = first(text_encoding, defaults["text_encoding"], "utf-8")
        self.cipher_core = first(cipher_core, defaults["cipher_core"], None)
        self.encrypt_kwargs = first(encrypt_kwargs, defaults["encrypt_kwargs"], {})
        self.decrypt_kwargs = first(decrypt_kwargs, defaults["decrypt_kwargs"], {})
        for key, value in kwargs.items():
            self.encrypt_kwargs.setdefault(key, value)
            self.decrypt_kwargs.setdefault(key, value)
        self.kwargs = extra_kwargs
        self.cipher_instance = None
        if self.cipher_core:
            self.cipher_instance = funcutils.call_with_inject(self.cipher_core, self.kwargs)
        else:
            if encrypt or decrypt:
                self.cipher_instance = _SimpleCipher(encrypt, decrypt)

    def encrypt(self, data, **kwargs):
        if data is None:
            return None
        if self.encrypt_force_bytes:
            data = strutils.force_bytes(data, self.text_encoding)
        encrypted_data = self.do_encrypt(data, **kwargs)
        return self.result_encoder.encode(encrypted_data)

    def decrypt(self, text, **kwargs):
        if text is None:
            return None
        data = self.result_encoder.decode(text)
        if self.decrypt_force_bytes:
            data = strutils.force_bytes(data, self.text_encoding)
        decrypted_data = self.do_decrypt(data, **kwargs)
        if self.force_text:
            return strutils.force_text(decrypted_data, self.text_encoding)
        else:
            return decrypted_data

    def do_encrypt(self, data, **kwargs):
        if self.cipher_instance:
            return self.cipher_instance.encrypt(data, **self.encrypt_kwargs, **kwargs)
        else:
            raise NotImplementedError("No encrypt method...")

    def do_decrypt(self, data, **kwargs):
        if self.cipher_instance:
            return self.cipher_instance.decrypt(data, **self.decrypt_kwargs, **kwargs)
        else:
            return NotImplementedError("NO decrypt method...")

class AesCipher(CipherBase):
    """AesCipher.

    mode: AES.MODE_ECB
    padding: aes_padding_pkcs5
    key: sha1prng_key # use sha1prng to transform the original password

    Example:

    In [47]: from fastutils import cipherutils

    In [48]: cipherutils.AesCipher(password='hello')
    Out[48]: <fastutils.cipherutils.AesCipher at 0x2285d130c10>

    In [49]: cipher = cipherutils.AesCipher(password='hello')

    In [50]: cipher.encrypt('hello')
    Out[50]: b'\\xa0\\x96<YaIOy`fiw\\x0b\\xf3\\xf7\\x84'

    In [51]: cipher.decrypt(cipher.encrypt('hello'))
    Out[51]: b'hello'

    In [59]: cipher = cipherutils.AesCipher(password='hello', result_encoder=cipherutils.Base64Encoder(), force_text=True)

    In [60]: cipher.encrypt('hello')
    Out[60]: 'oJY8WWFJT3lgZml3C/P3hA=='

    In [61]: cipher.decrypt('oJY8WWFJT3lgZml3C/P3hA==')
    Out[61]: 'hello'
    """
    def __init__(self, password, padding=aes_padding_pkcs5, key=sha1prng_key, mode=AES.MODE_ECB, **kwargs):
        self.aes_params = {
            "password": password,
            "padding": padding,
            "key": key,
            "mode": mode,
        }
        super().__init__(password=password, **kwargs)
    
    def do_encrypt(self, data, **kwargs):
        return aesutils.encrypt(data, **self.aes_params, **kwargs)
    
    def do_decrypt(self, data, **kwargs):
        return aesutils.decrypt(data, **self.aes_params, **kwargs)

class MysqlAesCipher(AesCipher):
    """AesCipher.

    mode: AES.MODE_ECB
    padding: aes_padding_pkcs5
    key: mysql_aes_key # use mysql default way to transform the original password

    Example:

    In [52]: from fastutils import cipherutils

    In [53]: cipher = cipherutils.MysqlAesCipher(password='hello')

    In [54]: cipher.encrypt('hello')
    Out[54]: b'\\xca\\xb2\\x9e\\xe5\\x9e\\xe9\\xec\\xc3j\\xc7\\xdf\\x82l\\x1b\\xcd\\xa9'

    In [55]: cipher.decrypt(cipher.encrypt('hello'))
    Out[55]: b'hello'

    In [56]: cipher = cipherutils.MysqlAesCipher(password='hello', result_encoder=cipherutils.Base64Encoder(), force_text=True)

    In [57]: cipher.encrypt('hello')
    Out[57]: 'yrKe5Z7p7MNqx9+CbBvNqQ=='

    In [58]: cipher.decrypt('yrKe5Z7p7MNqx9+CbBvNqQ==')
    Out[58]: 'hello'
    """
    def __init__(self, password, padding=aes_padding_pkcs5, key=mysql_aes_key, mode=AES.MODE_ECB, **kwargs):
        super().__init__(password, padding, key, mode, **kwargs)

class RawKeyAesCipher(AesCipher):
    """AesCipher.

    mode: AES.MODE_ECB
    padding: aes_padding_pkcs5
    key: raw_aes_key # use password as aes key directly, so that the password must be 16 chars length.
    
    Most java applications do AES encrypt like code below.

    function encrypt(String content, String password) {
        // password length must equals 16
        try {
            byte[] key = password.getBytes();
            SecretKeySpec skey = new SecretKeySpec(key, "AES")
            Cipher cipher = Cipher.getInstance(ALGORITHMSTR);
            cipher.init(Cipher.ENCRYPT_MODE, skey);
            byte[] contentBytes = content.getBytes("utf-8");
            byte[] contentEncrypted = cipher.doFinal(contentBytes);
            return Base64.encodeBase64String(contentEncrypted);
        } catch (Exception e) {
            return null;
        }
    }

    It is not good to generate the key by taking the first 16 bytes of the password. Add this to make life easy.

    Example:

    In [1]: from fastutils import cipherutils

    In [2]: cipher = cipherutils.RawKeyAesCipher(password='hello')

    In [3]: cipher.encrypt('hello') # Since password length is not 16, so encrypt get error
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
<ipython-input-3-f47a0d4a8ca0> in <module>
......
......
ValueError: Incorrect AES key length (5 bytes)

    """

    def __init__(self, password, padding=aes_padding_pkcs5, key=raw_aes_key, mode=AES.MODE_ECB, **kwargs):
        if len(password) < 16:
            raise ValueError("The password must be in 16 chars length. More that 16 chars will be truncate the first 16 chars.")
        super().__init__(password, padding, key, mode, **kwargs)

StupidJavaAesCipher = RawKeyAesCipher

class RsaCipher(CipherBase):

    default_result_encoder = Utf8Encoder()
    default_force_text = True

    def __init__(self, public_key=None, private_key=None, passphrase=None, **kwargs):
        self.passphrase = passphrase
        if public_key:
            if isinstance(public_key, str):
                self.public_key = rsautils.load_public_key(public_key)
            else:
                self.public_key = public_key
        else:
            self.public_key = None
        if private_key:
            if isinstance(private_key, str):
                self.private_key = rsautils.load_private_key(private_key, passphrase)
            else:
                self.private_key = private_key
            if not self.public_key:
                self.public_key = self.private_key.publickey()
        else:
            self.private_key = None
        super().__init__(**kwargs)

    def do_encrypt(self, text, **kwargs):
        if not self.public_key:
            raise RuntimeError("public_key NOT provided...")
        return rsautils.encrypt(text, self.public_key).encode("utf-8")
    
    def do_decrypt(self, data, **kwargs):
        if not self.private_key:
            raise RuntimeError("private_key NOT provided...")
        data = data.decode("utf-8")
        return rsautils.decrypt(data, self.private_key)

class IvCipher(CipherBase):
    """Int value encryption and decryption cipher.

    Example:

    In [38]: from fastutils import cipherutils

    In [39]: cipher = cipherutils.IvCipher(password='hello')

    In [40]: for i in range(10):
        ...:     print(i, cipher.encrypt(i))
        ...:
    0 0
    1 97
    2 112
    3 204
    4 205
    5 253
    6 294
    7 339
    8 364
    9 447
    """
    default_encrypt_force_bytes = False
    default_decrypt_force_bytes = False

    def __init__(self, password, **kwargs):
        self.password = password
        self.iv_params = self.get_iv_params()
        super().__init__(passowrd=password, **kwargs)

    def get_iv_params(self):
        gen = randomutils.Random(self.password)
        n = gen.randint(1024, 9999)
        iv = [gen.randint(1, 100) for _ in range(n)]
        return n, iv

    def do_encrypt(self, number:int, **kwargs) -> int:
        number = strutils.force_int(number)
        flag = False
        if number < 0:
            number = -1 * number
            flag = True
        n, iv = self.iv_params
        s = sum(iv)
        a = number // n
        b = number % n
        r = a * s + sum(iv[:b])
        if flag:
            r = -1 * r
        return r

    def do_decrypt(self, number:int, **kwargs) -> int:
        number = strutils.force_int(number)
        flag = False
        if number < 0:
            number = -1 * number
            flag = True
        n, iv = self.iv_params
        s = sum(iv)
        a = number // s
        t = s * a
        if t == number:
            r = a * n
        else:
            for delta in range(n):
                t += iv[delta]
                if t == number:
                    r = a * n + delta + 1
                    break
            if t != number:
                raise DecryptFailed("iv_decrypt failed: number={}".format(number))
        if flag:
            r = -1 * r
        return r

class IvfCipher(IvCipher):
    """Float value encryption and decryption cipher.

    Example:

    In [41]: from fastutils import cipherutils

    In [42]: cipher = cipherutils.IvfCipher(password='hello')

    In [43]: for i in range(10):
        ...:     print(i, cipher.encrypt(i), type(cipher.encrypt(i)))
        ...:
        ...:
    0 +0000000000000000000000 <class 'str'>
    1 +0000000000005004032834 <class 'str'>
    2 +0000000000010008064455 <class 'str'>
    3 +0000000000015012094180 <class 'str'>
    4 +0000000000020016127691 <class 'str'>
    5 +0000000000025020160338 <class 'str'>
    6 +0000000000030024191109 <class 'str'>
    7 +0000000000035028221552 <class 'str'>
    8 +0000000000040032254031 <class 'str'>
    9 +0000000000045036286491 <class 'str'>
    """
    def __init__(self, password, int_digits=12, float_digits=4, **kwargs):
        """password is required.
        int_digits is the max length of int part value. Add 0 padding to left.
        float_digits is the max length of float part value. Add 0 padding to right.
        """
        self.int_digits = int_digits
        self.float_digits = float_digits
        self.module = 10 ** (float_digits * 2)
        self.max_value_length = float_digits * 2 + self.int_digits + 2
        self.max = 10 ** self.max_value_length - 1
        self.value_template = "{:0%dd}" % self.max_value_length
        super().__init__(password=password, **kwargs)

    def do_encrypt(self, number:float, **kwargs) -> str:
        number = int(number * self.module)
        number = super().do_encrypt(number)
        if number >= 0:
            return "+" + self.value_template.format(number)
        else:
            return "*" + self.value_template.format(self.max - abs(number))

    def do_decrypt(self, number:str, **kwargs) -> float:
        sign = number[0]
        number = int(number[1:])
        if sign == "*":
            number = self.max - number
        number = super().do_decrypt(number)
        number = round(number / self.module, self.float_digits)
        if self.float_digits == 0:
            number = int(number)
        if sign == "*":
            return -1 * number
        else:
            return number

class MappingCipher(CipherBase):
    """Turn every byte in encode string to another value.

    0 -> b'randseed01'
    1 -> b'randseed02'
    ... -> ...
    255 -> b'randseed03'

    """
    def __init__(self, password=None, **kwargs):
        super().__init__(password=password, **kwargs)
        self.password = password
        self.seeds = self.try_to_load_seeds(password)
        if not self.seeds:
            self.randomGenerator = randomutils.Random(password)
            self.seeds = self.get_seeds()
        self.encrypt_mapping = self.get_encrypt_mapping()
        self.decrypt_mapping = self.get_decrypt_mapping()

    def get_seeds(self):
        raise NotImplementedError()

    def get_encrypt_mapping(self):
        mapping = {}
        for i in range(256):
            mapping[bytes([i])] = self.seeds[i]
        return mapping
    
    def get_decrypt_mapping(self):
        mapping = {}
        for i in range(256):
            mapping[self.seeds[i]] = bytes([i])
        return mapping
    
    def do_encrypt(self, data, **kwargs):
        if data is None:
            return None
        result = b""
        for c in data:
            result += self.encrypt_mapping[bytes([c])]
        return result
    
    def do_decrypt(self, data, **kwargs):
        if data is None:
            return None
        result = b""
        data_length = len(data)
        max_seed_length = max([len(x) for x in self.decrypt_mapping.keys()])
        start = 0
        while start < data_length:
            found = False
            for seed_length in range(1, max_seed_length+1):
                seed = data[start: start+seed_length]
                if seed in self.decrypt_mapping:
                    result += self.decrypt_mapping[seed]
                    start += seed_length
                    found = True
                    break
            if not found:
                raise DecryptFailed()
        return result

    def dumps(self):
        seeds = [binascii.hexlify(x).decode() for x in self.seeds]
        data = json.dumps(seeds)
        data = binascii.hexlify(data.encode()).decode()
        return data

    @classmethod
    def loads(cls, data):
        return cls(password=data)

    @classmethod
    def try_to_load_seeds(cls, data):
        try:
            data = binascii.unhexlify(data.encode())
            seeds = json.loads(data)
            seeds = [binascii.unhexlify(x) for x in seeds]
            return seeds
        except Exception:
            return None

    @classmethod
    def password_to_key(cls, password):
        cipher = cls(password=password)
        return cipher.dumps()

class S1Cipher(MappingCipher):

    def get_seeds(self):
        seeds = list(range(256))
        self.randomGenerator.shuffle(seeds)
        return [bytes([x]) for x in seeds]

class S2Cipher(MappingCipher):
    def get_seeds(self):
        letters = string.ascii_lowercase
        seeds = set()
        for a in letters:
            for b in letters:
                seeds.add(a+b)
        seeds = list(seeds)
        self.randomGenerator.shuffle(seeds)
        seeds = [x.encode() for x in seeds[:256]]
        return seeds

class S12Cipher(MappingCipher):
    def get_seeds(self):
        v = randomutils.Random(self.password).get_bytes(256)
        values = list(range(256))
        delta = 0
        for index in range(256):
            delta += v[index]
            values[index] += delta
        seeds = []
        for code in range(256):
            value = values[code]
            high = value // 256
            low = value % 256
            seeds.append(bytes([high, low]))
        return seeds
