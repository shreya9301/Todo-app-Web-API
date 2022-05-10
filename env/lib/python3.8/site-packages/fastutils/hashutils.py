# -*- coding: utf-8 -*-
import re
import random
import string
import hashlib
import base64
import functools
import codecs
from . import strutils

def method_load(method):
    if isinstance(method, str):
        return getattr(hashlib, method)
    else:
        return method

def get_file_hash(filename, method, buffer_size=1024*64):
    method = method_load(method)
    gen = method()
    with open(filename, "rb") as fobj:
        while True:
            buffer = fobj.read(buffer_size)
            if not buffer:
                break
            gen.update(buffer)
    return gen.hexdigest()

get_file_md5 = functools.partial(get_file_hash, method=hashlib.md5)
get_file_sha = functools.partial(get_file_hash, method=hashlib.sha1)
get_file_sha1 = functools.partial(get_file_hash, method=hashlib.sha1)
get_file_sha224 = functools.partial(get_file_hash, method=hashlib.sha224)
get_file_sha256 = functools.partial(get_file_hash, method=hashlib.sha256)
get_file_sha384 = functools.partial(get_file_hash, method=hashlib.sha384)
get_file_sha512 = functools.partial(get_file_hash, method=hashlib.sha512)

def get_hash_hexdigest(*args, **kwargs):
    method = kwargs.get("method", "md5")
    method = method_load(method)
    data = b""
    for arg in args:
        if isinstance(arg, bytes):
            data += arg
        else:
            data += str(arg).encode("utf-8")
    gen = method(data)
    return gen.hexdigest()

get_md5 = get_md5_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.md5)
get_sha = get_sha_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha1)
get_sha1 = get_sha1_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha1)
get_sha224 = get_sha224_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha224)
get_sha256 = get_sha256_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha256)
get_sha384 = get_sha384_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha384)
get_sha512 = get_sha512_hexdigest = functools.partial(get_hash_hexdigest, method=hashlib.sha512)

def get_hash_base64(*args, **kwargs):
    method = kwargs.get("method", "md5")
    method = method_load(method)
    data = b""
    for arg in args:
        if isinstance(arg, bytes):
            data += arg
        else:
            data += str(arg).encode("utf-8")
    gen = method(data)
    data = gen.digest()
    text = codecs.encode(data, "base64").decode()
    return strutils.join_lines(text)

get_md5_base64 = functools.partial(get_hash_base64, method=hashlib.md5)
get_sha_base64 = functools.partial(get_hash_base64, method=hashlib.sha1)
get_sha1_base64 = functools.partial(get_hash_base64, method=hashlib.sha1)
get_sha224_base64 = functools.partial(get_hash_base64, method=hashlib.sha224)
get_sha256_base64 = functools.partial(get_hash_base64, method=hashlib.sha256)
get_sha384_base64 = functools.partial(get_hash_base64, method=hashlib.sha384)
get_sha512_base64 = functools.partial(get_hash_base64, method=hashlib.sha512)


def get_pbkdf2_hmac(text, salt=None, iterations=2048, hash_name="sha256"):
    if salt is None:
        salt = strutils.random_string(16, choices=string.ascii_letters)
    data = hashlib.pbkdf2_hmac(hash_name, text.encode("utf-8"), salt.encode("utf-8"), iterations)
    return "pbkdf2_{hash_name}${iterations}${salt}${data}".format(
        hash_name=hash_name,
        iterations=iterations,
        salt=salt,
        data=strutils.join_lines(codecs.encode(data, "base64").decode()),
    )

def validate_pbkdf2_hmac(password, text):
    matches = re.findall(r"pbkdf2_(.+)\$(\d+)\$(.+)\$(.+)", text)
    if len(matches) != 1:
        return False
    hash_name, iterations, salt, _ = matches[0]
    if not iterations.isdigit():
        return False
    else:
        iterations = int(iterations)
    data = get_pbkdf2_hmac(password, salt=salt, iterations=iterations, hash_name=hash_name)
    if data == text:
        return True
    else:
        return False

get_pbkdf2_sha512 = functools.partial(get_pbkdf2_hmac, hash_name="sha512")
validate_pbkdf2_sha512 = validate_pbkdf2_hmac

get_pbkdf2_sha384 = functools.partial(get_pbkdf2_hmac, hash_name="sha384")
validate_pbkdf2_sha384 = validate_pbkdf2_hmac

get_pbkdf2_sha256 = functools.partial(get_pbkdf2_hmac, hash_name="sha256")
validate_pbkdf2_sha256 = validate_pbkdf2_hmac

get_pbkdf2_sha224 = functools.partial(get_pbkdf2_hmac, hash_name="sha224")
validate_pbkdf2_sha224 = validate_pbkdf2_hmac

get_pbkdf2_sha1 = functools.partial(get_pbkdf2_hmac, hash_name="sha1")
validate_pbkdf2_sha1 = validate_pbkdf2_hmac

get_pbkdf2_sha = functools.partial(get_pbkdf2_hmac, hash_name="sha1")
validate_pbkdf2_sha = validate_pbkdf2_hmac

get_pbkdf2_md5 = functools.partial(get_pbkdf2_hmac, hash_name="md5")
validate_pbkdf2_md5 = validate_pbkdf2_hmac
