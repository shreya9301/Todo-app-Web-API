import string
from pypinyin import lazy_pinyin

from . import strutils
from . import listutils

def to_pinyin(value, clean=True, keep_chars=string.ascii_letters + string.digits):
    """Turn chinese text to pinyin string.

    Example:

    In [1]: from fastutils import pinyinutils

    In [2]: pinyinutils.to_pinyin('测试')
    Out[2]: 'CeShi'
    """
    words = lazy_pinyin(value)
    words = listutils.replace(words, {"lve": "lue"})
    title = " ".join([x.capitalize() for x in words])
    result = strutils.camel(title, clean=clean, keep_chars=keep_chars)
    return result
