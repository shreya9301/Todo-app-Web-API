# -*- coding: utf-8 -*-
import os
import hashlib
import binascii
import base64
from Crypto.Cipher import AES
from . import strutils
from . import listutils


AES_BLOCK_SIZE = AES.block_size

def get_raw_aes_key(key):
    return strutils.force_bytes(key)[:16]

def get_mysql_aes_key(key):
    final_key = bytearray(16)
    for i, c in enumerate(key):
        final_key[i % 16] ^= ord(c)
    return bytes(final_key)

def get_sha1prng_key(key):
    """
    encrypt key with SHA1PRNG
    same as java AES crypto key generator SHA1PRNG
    """
    key = strutils.force_bytes(key)
    signature = hashlib.sha1(key).digest()
    signature = hashlib.sha1(signature).digest()
    return signature[:16]

def get_md5_key(key):
    key = strutils.force_bytes(key)
    signature = hashlib.md5(key).digest()
    return signature

def padding_ansix923(value):
    padsize = AES.block_size - len(value) % AES.block_size
    return value + listutils.int_list_to_bytes([0] * (padsize -1)) + listutils.int_list_to_bytes([padsize])

def remove_padding_ansix923(value):
    padsize = strutils.char_force_to_int(value[-1])
    return value[:-1*padsize]

def padding_iso10126(value):
    padsize = AES.block_size - len(value) % AES.block_size
    return value + os.urandom(padsize-1) + listutils.int_list_to_bytes([padsize])

def remove_padding_iso10126(value):
    padsize = strutils.char_force_to_int(value[-1])
    return value[:-1*padsize]

def padding_pkcs5(value):
    padsize = AES.block_size - len(value) % AES.block_size
    value = value + listutils.int_list_to_bytes([padsize] * padsize)
    return value

def remove_padding_pkcs5(value):
    padsize = strutils.char_force_to_int(value[len(value) - 1])
    return value[:-1*padsize]


def get_padding_remove_method(padding):
    if padding == padding_pkcs5:
        return remove_padding_pkcs5
    elif padding == padding_ansix923:
        return remove_padding_ansix923
    elif padding == padding_iso10126:
        return remove_padding_iso10126
    else:
        raise RuntimeError("Padding method {} have NOT define a remove method...".format(str(padding)))

def encrypt(data, password, padding=padding_pkcs5, key=get_sha1prng_key, mode=AES.MODE_ECB):
    """AES encrypt with AES/ECB/Pkcs5padding/SHA1PRNG options
    """
    data_padded = padding(data)
    final_key = key(password)
    cipher = AES.new(final_key, mode)
    data_encrypted = cipher.encrypt(data_padded)
    return data_encrypted

def decrypt(data_encrypted, password, padding=padding_pkcs5, key=get_sha1prng_key, mode=AES.MODE_ECB):
    """AES decrypt with AES/ECB/Pkcs5padding/SHA1PRNG options
    """
    final_key = key(password)
    cipher = AES.new(final_key, mode)
    data_padded = cipher.decrypt(data_encrypted)
    padding_remove_method = get_padding_remove_method(padding)
    data = padding_remove_method(data_padded)
    return data

def encrypt_and_base64encode(data, password, **kwargs):
    data = strutils.force_bytes(data)
    data_encrypted = encrypt(data, password, **kwargs)
    data_base64_encoded = base64.encodebytes(data_encrypted)
    return strutils.join_lines(data_base64_encoded).decode()

def decrypt_and_base64decode(text, password, **kwargs):
    text = strutils.force_bytes(text)
    data_encrypted = base64.decodebytes(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data

def encrypt_and_safeb64encode(data, password, **kwargs):
    data = strutils.force_bytes(data)
    data_encrypted = encrypt(data, password, **kwargs)
    data_safeb64_encoded = base64.urlsafe_b64encode(data_encrypted)
    return strutils.join_lines(data_safeb64_encoded).decode()

def decrypt_and_safeb64decode(text, password, **kwargs):
    text = strutils.force_bytes(text)
    data_encrypted = base64.urlsafe_b64decode(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data

def encrypt_and_hexlify(data, password, **kwargs):
    data = strutils.force_bytes(data)
    data_encrypted = encrypt(data, password, **kwargs)
    return binascii.hexlify(data_encrypted).decode()

def decrypt_and_unhexlify(text, password, **kwargs):
    text = strutils.force_bytes(text)
    data_encrypted = binascii.unhexlify(text)
    data = decrypt(data_encrypted, password, **kwargs)
    return data


def get_aes_mode(mode):
    return getattr(AES, "MODE_{}".format(mode.upper()))
