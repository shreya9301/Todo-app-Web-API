import rsa
import base64
import typing

from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import PKCS1_v1_5 as PKCS1_v1_5_SIGNATURE
from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import MD5
from Crypto.Hash import SHA
from Crypto.Hash import SHA1
from Crypto.Hash import SHA224
from Crypto.Hash import SHA256
from Crypto.Hash import SHA384
from Crypto.Hash import SHA512

from .strutils import smart_get_binary_data

HASH_METHODS = {
    "MD5": MD5,
    "SHA": SHA,
    "SHA1": SHA1,
    "SHA224": SHA224,
    "SHA256": SHA256,
    "SHA384": SHA384,
    "SHA512": SHA512,
}

def newkeys(nbits=2048):
    """Generate a new RSA key pair.

    In [1]: from fastutils import rsautils

    In [2]: rsautils.newkeys()
    Out[2]:
    (RsaKey(n=1234...7891, e=65537), RsaKey(n=1234...7891, e=65537, d=2345...6789, p=3456...9087, q=4567..9876, u=6789...1234))
    
    """
    sk = RSA.generate(nbits)
    pk = sk.publickey()
    return pk, sk

def load_private_key(text, passphrase=None):
    """Load private key from PEM string.
    """
    if isinstance(text, RsaKey):
        return text
    if isinstance(text, rsa.PrivateKey):
        text = text.save_pkcs1()
    sk = RSA.import_key(text, passphrase=passphrase)
    return sk

def load_public_key(text):
    """Load public key from PEM string.
    """
    if isinstance(text, RsaKey):
        return text.public_key()
    if isinstance(text, (rsa.PublicKey, rsa.PrivateKey)):
        text = text.save_pkcs1()
    pk = RSA.import_key(text)
    if hasattr(pk, "public_key"):
        pk = pk.public_key()
    else:
        pk = pk.publickey()
    return pk

def load_public_key_from_private_key(text, passphrase=None):
    """Get public key from private key.
    """
    sk = load_private_key(text, passphrase)
    if hasattr(sk, "public_key"):
        pk = sk.public_key()
    else:
        pk = sk.publickey()
    return pk

def encrypt(data: bytes, pk: typing.Union[RSA.RsaKey, rsa.PublicKey, str], envelope=PKCS1_OAEP) -> str:
    """Use public key to encrypt the data, so that only the owner of the private key can decrypt the data.

    Use envelope=PKCS1_v1_5 so that you will get most compatible with other libraries, 
    but we suggest to use envelope=PKCS1_OAEP so that you will be more secure.

    if the RSA KEY's nbits == 1024, the max data length is 117(PKCS1_v1_5), 86(PKCS1_OAEP)
    if the RSA KEY's nbits == 2048, the max data length is 245(PKCS1_v1_5), 214(PKCS1_OAEP)
    if the RSA KEY's nbits == 4096, the max data length is 501(PKCS1_v1_5), 470(PKCS1_OAEP)
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    pk = load_public_key(pk)
    gen = envelope.new(pk)
    encrypted_data = gen.encrypt(data)
    return "".join(base64.encodebytes(encrypted_data).decode().splitlines())

def decrypt(data: str, sk: typing.Union[RSA.RsaKey, rsa.PrivateKey, str], envelope=PKCS1_OAEP) -> bytes:
    """Use private key to decrypt the data that encrypted with the public key.

    Both PKCS1_v1_5 and PKCS1_OAEP will be used to do decrypt.
    If envelope=PKCS1_v1_5, we will try PKCS1_v1_5 first and then PKCS1_OAEP.
    If envelope=PKCS1_OAEP, we will try PKCS1_OAEP first and then PKCS1_v1_5.
    """
    encrypted_data = smart_get_binary_data(data)
    sk = load_private_key(sk)
    def do_decrypt(message, gen, envelope):
        if envelope == PKCS1_OAEP:
            try:
                return gen.decrypt(message)
            except:
                return None
        else:
            try:
                return gen.decrypt(message, None)
            except:
                return None
    gen = envelope.new(sk)
    data = do_decrypt(encrypted_data, gen, envelope)
    if data is None:
        if envelope == PKCS1_v1_5:
            gen = PKCS1_OAEP.new(sk)
            envelope = PKCS1_OAEP
        else:
            gen = PKCS1_v1_5.new(sk)
            envelope = PKCS1_v1_5
        data = do_decrypt(encrypted_data, gen, envelope)
    return data

def export_key(rsakey: typing.Union[RSA.RsaKey, rsa.PublicKey, rsa.PrivateKey, str]):
    """Export the private key or the public key to PEM string.
    """
    if not isinstance(rsakey, RsaKey):
        if isinstance(rsakey, (rsa.PublicKey, rsa.PrivateKey)):
            rsakey = rsakey.save_pkcs1()
        if isinstance(rsakey, bytes):
            rsakey = rsakey.decode()
        if isinstance(rsakey, str):
            rsakey = RSA.import_key(rsakey)
    return rsakey.export_key().decode()

def get_hash_method(hash_method):
    if isinstance(hash_method, str):
        return HASH_METHODS[hash_method.upper()]
    return hash_method

def sign(data:bytes, sk:typing.Union[RSA.RsaKey, rsa.PrivateKey], hash_method="SHA", sign_method=PKCS1_PSS):
    """Use RSA private key to sign a data and get a data signature.

    data: The raw data to be signed.
    sk: The RSA private key used to do the sign.
    hash_method: The Hash method will be used to calc the hash of the data. We only sign the hash of data.
    sign_method: We prefer PKCS1_PSS instread of old sign method PKCS1_v1_5_SIGNATURE.

    Note:
    - Call twice sign method with the same parameters will always get different result.

    Usage:

    In [7]: from fastutils import rsautils

    In [8]: pk, sk = rsautils.newkeys()

    In [10]: rsautils.sign(b"hello world", sk)
    Out[10]: 'O696w8AfsiKsLCcZpfZ+zoTmnIQp3BHWUOFos20Jrh2T+9ecACiGrmicXGMn17Ls6w4yiwSxzog3v0z8mh8VBNjRUXP2nPTRKutP+t3iDCIUfjqr/Ws3R7qBYCTDAmYUPunG5163aM5Z50KCiWM3SexvS19UcAfOTQpEcVUNnOk+7605XDBFjWpOh8bhP1nBqCr+1GzBT2G64yzVZh5jp07LlULXP8gbsfZ87LyT/fIuGCNeFngvf31UF+MEWU/rnQYVEU5p1STOmj+BpClH20tbysR/3/yQTkEPwNt/uJ5u8neGYXAcKF6ODK/yC3EtXIDI1vgxNNcdbB7ejTVKFg=='

    In [11]: rsautils.sign(b"hello world", sk)
    Out[11]: 'GouA3UT9jHvjocTsAduM/o5nhji7gRULnUpFe85B4QgLNg03TaSmff+qpI8kzqRavFmKhjT5FIkReQTNPXF5X7BkzUXsP5ZwdKU93MsSH46w4/1b6GY0huhgmy5BBA0lm/ELyeU8Ej+elunku5CJAuXel06VSyR1oLhFPYeLzA+sVciIngFGV9V46L9tCpVkvzDuAIvW69g0oVai5zoqgH4fkkeVJxgfzsJiU3b/1U0z/vNraPjhZK4XWYrUmbqQXLAjyeBHkbyRu8zD+U/shFkjgLenGaw50E4JiSAi6jre77gC5/FrLsdF/r6ObOOUgC0r+aeCKWttKqZju5bQaQ=='

    In [12]: rsautils.sign(b"hello world", sk)
    Out[12]: 'NcufFFQI4s8DDsvmql5FZFwIhHMoWqWApeRyEG8aR5amITEYPnMgLfmiz6krVQ1Wsm+N+R1bXMWz3axHiqCYDEbCwL4d/jTHLwgh3cgsTb5fenY91V8l9huBqEO5uzNxiiB14Hn0Ciy/FXdWSQ+Nf2vmmIvmLSXy6vg/Qk0C6qjkXstGM6IVlnxmaZfwoP2O37jZ3tFWiytwObolvmqOVNj3xFqXG8rAPRMS1dPItfrE48kR9z6/qKlUNLMTCkAH4v4aElBTwoLfjJZWUzd0mMQc6gEtBcTrIR1ZI+kx6tkNFy6gnAUGGneOEUljHjzhkEqJjsjCbz/F1zUym0MISw=='

    In [13]: rsautils.sign(b"hello world", sk)
    Out[13]: 'dAz9WnyIhs+NUFygXGznV4POmKAPz3JnL3HzhlSTh/rfV/KGVXKqEh6a5GU5fDU5BywRFg1ike2vt23qQMMr4T1z9Ihta1BgPS/OIMmuDgttC/NjyXEvcxCN3tUb0PXwSsZnHzWRWs9D+LuGkYgUH/hJ//2AAq917ePebyd3ylPOfGCXzo9YkXC1F4wC94MEgIUsTeR2O5nlm9wvMcZv1TvLDATqIDp/F7XX+cfbH75b676qGQQ7+0PuW3AXQSU1A4zPyvy4Es7Kk3CBd2WUIOUf+jeIzyVXHUwnCEy5y+xoG/Ry4+BjQBntS8pEN4kMdNtCX57G0e8fyk1nF5rzCQ=='

    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hash_method = get_hash_method(hash_method)
    hash_gen = hash_method.new()
    hash_gen.update(data)

    sign_gen = sign_method.new(sk)
    sign_data = sign_gen.sign(hash_gen)
    return base64.encodebytes(sign_data).decode("utf-8").replace("\n", "")

def verify(data:bytes, sign_data:str, pk:typing.Union[RSA.RsaKey, rsa.PublicKey], hash_method="SHA", sign_method=PKCS1_PSS):
    """Use RSA public key to verify if the data and the signautre is match of not.

    data: The signed raw data.
    sign_data: The result of the rsautils.sign.
    pk: The RSA public key used to do the verify. It must match the private key used to do the sign.
    hash_method:  The Hash method will be used to calc the hash of the data.
    sign_method: We will try both PKCS1_PSS and PKCS1_v1_5_SIGNATURE to do the verify, and use sign_method to do the first verify.

    Usage:

    In [1]: from fastutils import rsautils

    In [2]: pk, sk = rsautils.newkeys()

    In [4]: sign_data = rsautils.sign(b"hello world", sk)

    In [5]: sign_data
    Out[5]: 'cijyMq5i49awZUBz5yArxUujYxsz08TISPJwxf3uGJMXGvkCSmjMlpvKu/0ll4C/pZB0M0ZI82pCskc1mQ+PttzbHMXJLRaKprSuw6glVpWPzTejl+r82M1VPUQXqcMtAVPzx3OWTUtq6bzbyC9tM/EpeHBvcJMZFCLiv2EEbn1VhbYo9VgrxocqW38UKE3H6Uk8+8gCa7VEXDeniLOwrvOWdVMJqISoV3tit3ikERbNlHU5m3D22SqaFKidJli2bQc5ygdz+M9X8SxkvYGMt2Idmqii03lK/P/AQdooItSm3ulg7eM/uV22dU1+LcBAYtp89ga4JdFNwulKtdmGQA=='

    In [6]: rsautils.verify(b"hello world", sign_data, pk)
    Out[6]: True

    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    hash_method = get_hash_method(hash_method)
    hash_gen = hash_method.new()
    hash_gen.update(data)

    sign_data = smart_get_binary_data(sign_data)

    def do_verify(sign_method, hash_gen, sign_data):
        try:
            sign_gen = sign_method.new(pk)
            return sign_gen.verify(hash_gen, sign_data)
        except:
            return None

    result = do_verify(sign_method, hash_gen, sign_data)
    if not result:
        if sign_method == PKCS1_PSS:
            sign_method = PKCS1_v1_5_SIGNATURE
        else:
            sign_method = PKCS1_PSS
        result = do_verify(sign_method, hash_gen, sign_data)
    return result
