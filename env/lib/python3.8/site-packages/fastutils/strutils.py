"""
String operate functions.
"""
import itertools
import random
import string
import binascii
import base64
import typing
from unittest import result
import bizerror
import math
import re
import uuid
from decimal import Decimal


HEXLIFY_CHARS = "0123456789abcdefABCDEF"
URLSAFEB64_CHARS = "-0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz\r\n"
BASE64_CHARS = "+/0123456789=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\r\n"

SHI = 10
BAI = SHI * 10
QIAN = BAI * 10
WAN = QIAN * 10
YI = WAN * WAN

default_encodings = ["utf8", "gb18030"]

def random_string(length, choices=string.ascii_letters):
    """Generates a random string of specified length using specified characters.

    In [3]: strutils.random_string(8)
    Out[3]: 'wJhsaYVq'

    In [4]: strutils.random_string(32)
    Out[4]: 'JtYNblzfEFYdgwcTjNiorwucrlHuIeTQ'

    In [5]: import string

    In [8]: strutils.random_string(32, choices=string.ascii_letters+string.punctuation)
    Out[8]: "]ivN^F]v#jPraNLC:F?<}:!'}aox=lKY"

    In [9]: strutils.random_string(32, choices=string.ascii_letters+string.punctuation)
    Out[9]: 'Flx,TOkDV_g&CsHq#l`RZ:(J#eVxENYJ'
    """
    return "".join(random.choices(choices, k=length))

def char_force_to_int(char):
    if callable(char):
        char = char()
    if char is None:
        return None
    if isinstance(char, int):
        return char
    return ord(char)

def force_bytes(value, encoding=None):
    if callable(value):
        value = value()
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    encoding = encoding or "utf-8"
    if isinstance(value, str):
        return value.encode(encoding)
    else:
        return str(value).encode(encoding)

def force_text(value, encoding=None):
    if callable(value):
        value = value()
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if not isinstance(value, bytes):
        return str(value)
    if not encoding:
        encodings = default_encodings
    elif isinstance(encoding, (set, list, tuple)):
        encodings = encoding
    else:
        encodings = [encoding]
    for encoding in encodings:
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError()

def force_int(value):
    if callable(value):
        value = value()
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, Decimal):
        return int(value.to_integral_value())
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    value = str(value)
    return int(value)

def force_float(value):
    if callable(value):
        value = value()
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    value = str(value)
    return float(value)

def force_numberic(value):
    if callable(value):
        value = value()
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    value = str(value)
    if "." in value:
        return float(value)
    else:
        return int(value)

def wholestrip(text):
    """Remove all white spaces in text. White spaces are ' \\t\\n\\r\\x0b\\x0c\\u3000'. 
    
    Note: 
    
    It's NOT only trim the left and right white characters, 
    but also remove white characters in the middle of the text.
    """
    if text is None:
        return None
    for space in string.whitespace + "\u3000":
        text = text.replace(space, "")
    return text

def split2(text, seps=None):
    """Split string into two parts.
    """
    if text is None:
        return None
    if not seps:
        ss = text.split(maxsplit=1)
    else:
        if not isinstance(seps, (list, set, tuple)):
            seps = [seps]
        min_index = len(text)
        min_sep = None
        for sep in seps:
            try:
                index = text.index(sep)
                if index < min_index:
                    min_index = index
                    min_sep = sep
            except ValueError:
                pass
        ss = text.split(min_sep, maxsplit=1)
    if len(ss) == 0:
        ss.append("")
    if len(ss) == 1:
        ss.append("")
    return ss

def split(text, seps, strip=False):
    """Split string with a list of sperators. seps is a list of string, all sep in the seps are treated as delimiter.
    """
    if not text:
        return []
    if not isinstance(seps, (list, set, tuple)):
        seps = [seps]
    results = [text]
    for sep in seps:
        row = []
        for value in results:
            row += value.split(sep)
        results = row
    if strip:
        row = []
        for value in results:
            row.append(value.strip())
        results = row
    return results

def str_composed_by(text, choices):
    """Test if text is composed by chars in the choices.
    """
    for char in text:
        if not char in choices:
            return False
    return True

is_str_composed_by_the_choices = str_composed_by

def is_hex_digits(text):
    """Test if all chars in text is hex digits.
    """
    if not text:
        return False
    return str_composed_by(text, HEXLIFY_CHARS)

def join_lines(text):
    """Join multi-lines into single line.
    """
    if isinstance(text, str):
        return "".join(text.splitlines())
    else:
        return b"".join(text.splitlines())

def is_urlsafeb64_decodable(text):
    """Test if the text can be decoded by urlsafeb64 method.
    """
    text = wholestrip(text)
    if not text:
        return False
    if len(text) % 4 != 0:
        return False
    text = join_lines(text)
    return str_composed_by(text, URLSAFEB64_CHARS)

def is_base64_decodable(text):
    """Test  if the text can be decoded by base64 method.
    """
    text = wholestrip(text)
    if not text:
        return False
    if len(text) % 4 != 0:
        return False
    text = join_lines(text)
    return str_composed_by(text, BASE64_CHARS)

def is_unhexlifiable(text):
    """Test if the text can be decoded by unhexlify method.
    """
    text = wholestrip(text)
    if not text:
        return False
    if len(text) % 2 != 0:
        return False
    return str_composed_by(text, HEXLIFY_CHARS)

def text_display_length(text, unicode_display_length=2, encoding=None):
    """Get text display length.
    """
    text = force_text(text, encoding)
    length = 0
    for c in text:
        if ord(c) <= 128:
            length += 1
        else:
            length += unicode_display_length
    return length

def text_display_shorten(text, max_length, unicode_display_length=2, suffix="...", encoding=None):
    """Shorten text to fix the max display length.
    """
    text = force_text(text, encoding)
    if max_length < len(suffix):
        max_length = len(suffix)
    tlen = text_display_length(text, unicode_display_length=unicode_display_length)
    if tlen <= max_length:
        return text
    result = ""
    tlen = 0
    max_length -= len(suffix)
    for c in text:
        if ord(c) <= 128:
            tlen += 1
        else:
            tlen += unicode_display_length
        if tlen < max_length:
            result += c
        elif tlen == max_length:
            result += c
            break
        else:
            break
    result += suffix
    return result

def smart_get_binary_data(text):
    if isinstance(text, str):
        if is_unhexlifiable(text):
            return binascii.unhexlify(text)
        elif is_urlsafeb64_decodable(text):
            return base64.urlsafe_b64decode(text.encode("utf-8"))
        elif is_base64_decodable(text):
            return base64.decodebytes(text.encode("utf-8"))
        else:
            return text.encode("utf-8")
    elif isinstance(text, bytes):
        return text
    else:
        raise bizerror.NotSupportedTypeToCast()

def is_chinese_character(c):
    """
    Block                                   Range       Comment
    CJK Unified Ideographs                  4E00-9FFF   Common
    CJK Unified Ideographs Extension A      3400-4DBF   Rare
    CJK Unified Ideographs Extension B      20000-2A6DF Rare, historic
    CJK Unified Ideographs Extension C      2A700–2B73F Rare, historic
    CJK Unified Ideographs Extension D      2B740–2B81F Uncommon, some in current use
    CJK Unified Ideographs Extension E      2B820–2CEAF Rare, historic
    CJK Compatibility Ideographs            F900-FAFF   Duplicates, unifiable variants, corporate characters
    CJK Compatibility Ideographs Supplement 2F800-2FA1F Unifiable variants
    """
    c = ord(c)
    if 0x4E00 <= c <= 0x9FFF:
        return True
    if 0x3400 <= c <= 0x4DBF:
        return True
    if 0x20000 <= c <= 0x2A6DF:
        return True
    if 0x2A700 <= c <= 0x2B73F:
        return True
    if 0x2B740 <= c <= 0x2B81F:
        return True
    if 0x2B820 <= c <= 0x2CEAF:
        return True
    if 0xF900 <= c <= 0xFAFF:
        return True
    if 0x2F800 <=c <= 0x2FA1F:
        return True
    return False

def binarify(data:bytes) -> str:
    """Turn bytes into binary string. Similar to binascii.hexlify(), but using binary instread hex.
    
    Examples:

    In [11]: strutils.binarify(b'0')
    Out[11]: '00110000'

    In [12]: strutils.binarify(b'a')
    Out[12]: '01100001'

    In [13]: strutils.binarify(b'hello')
    Out[13]: '0110100001100101011011000110110001101111'
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "".join(["{:08b}".format(x) for x in data])

def unbinarify(text):
    if not text:
        return b""
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    from .listutils import chunk
    return bytes([int(x, 2) for x in chunk(text, 8)])

def ints2bytes(ints):
    result = b""
    for value in ints:
        if value:
            result += int2bytes(value)
        else:
            result += b'\x00'
    return result

def int2bytes(value):
    bs = []
    while value:
        bs.append(value % 256)
        value = value // 256
    bs.reverse()
    return bytes(bs)

def substrings(value, lengths=None):
    value = value or ""
    subs = set()
    if lengths is None:
        lengths = list(range(len(value)))
    elif isinstance(lengths, int):
        lengths = [lengths]
    for length in lengths:
        for start in range(len(value) - length + 1):
            sub = value[start: start + length]
            subs.add(sub)
    return subs

def combinations2(values: typing.List[str], length:int) -> typing.List[str]:
    """同combinations，使用了itertools.product实现，简化了实现逻辑。但性能仅为combinations的一半。仅供参考。
    """
    results = set()
    min_length = min([len(x) for x in values])
    repeat = math.ceil(length / min_length * 2)
    for vs in itertools.product(values, repeat=repeat):
        line = "".join(vs)
        line_length = len(line)
        max_start_index = line_length - length
        for index in range(max_start_index+1):
            word = line[index:index+length]
            results.add(word)
    return results

def combinations(values: typing.List[str], length:int) -> typing.List[str]:
    """取values中各字符串的任意连接（可重复取），在组成的新字符串中，取任意指定长度子串所形成的集合。

    例如：

    In [96]: strutils.combinations(['abc', 'xyz'], 5)
    Out[96]:
    {'abcab',
    'abcxy',
    'bcabc',
    'bcxyz',
    'cabca',
    'cabcx',
    'cxyza',
    'cxyzx',
    'xyzab',
    'xyzxy',
    'yzabc',
    'yzxyz',
    'zabca',
    'zabcx',
    'zxyza',
    'zxyzx'}

    """
    values = list(values)
    min_length = min([len(x) for x in values])
    max_length = max([len(x) for x in values])
    repeat = math.ceil((length - min_length)/min_length)
    repeat_incr = False
    if length <= min_length:
        repeat_incr = True
    if length % min_length == 2 and length % max_length == 2:
        repeat_incr = True
    if length % min_length == 0 and length % max_length == 0:
        repeat_incr = True
    if repeat_incr:
        repeat += 1
    check_length = length + 2 * max_length - 1
    good_words = set()
    short_words = set(values)
    for i in range(repeat):
        new_words = set()
        for value in values:
            for word in short_words:
                new_word = word + value
                if len(new_word) >= check_length:
                    good_words.add(new_word)
                else:
                    new_words.add(new_word)
        short_words = new_words
        if not short_words:
            break
    for x in short_words:
        if len(x) >= length:
            good_words.add(x)
    result_words = set()
    for word in good_words:
        for subword in substrings(word, length):
            result_words.add(subword)
    return result_words

def captital_number(value, yuan="圆", digits="零壹贰叁肆伍陆柒捌玖", places="拾佰仟万亿", negative="负", float_places="角分厘毫丝忽微"):
    from .numericutils import float_split

    sign, int_part, float_part = float_split(value, precision=7)

    def parse4(value):
        qian = value // QIAN
        value = value % QIAN
        bai = value // BAI
        value = value % BAI
        shi = value // SHI
        value = value % SHI
        ge = value
        return digits[qian] + places[2] + digits[bai] + places[1] + digits[shi] + places[0] + digits[ge]

    def parse8(value):
        high = value // WAN
        low = value % WAN
        return parse4(high) + places[3] + parse4(low)

    def parse(value):
        yis = []
        while value:
            yis.append(value % YI)
            value //= YI
        yis.reverse()
        return places[4].join([parse8(x) for x in yis])

    def remove0(value_string):
        z0 = digits[0]
        z00 = digits[0] +  digits[0]
        for place in places:
            value_string = value_string.replace(digits[0] + place, digits[0])
        while z00 in value_string:
            value_string = value_string.replace(z00, z0)
        if value_string.startswith(z0):
            value_string = value_string[1:]
        if value_string.endswith(z0):
            value_string = value_string[:-1]
        return value_string

    def parse_float_part(value):
        if not value:
            return ""
        result = ""
        for index, c in enumerate("{:07d}".format(value)):
            if index > len(float_places):
                break
            cv = int(c)
            if cv:
                result += digits[cv] + float_places[index]
        return result

    int_string = parse(int_part)
    int_string = remove0(int_string)
    if not int_string:
        int_string = digits[0]

    float_string = parse_float_part(float_part)

    result = int_string + yuan + float_string
    if sign < 0:
        result = negative + result

    return result

def clean(value, keep_chars):
    """Clean the string value and only keep characters in keep_chars.
    """
    if not isinstance(keep_chars, set):
        keep_chars = set(keep_chars)
    value2 = ""
    for c in value:
        if c in keep_chars:
            value2 += c
    return value2

do_clean = clean # Alias of clean

def camel(value, clean=False, keep_chars=string.ascii_letters + string.digits, lower_first=False):
    if value is None:
        return None
    words = []
    word_chars = set(string.ascii_letters)
    word = ""
    non_word = ""
    for c in value:
        if c in word_chars:
            word += c
            if non_word:
                words.append(non_word)
                non_word = ""
        else:
            non_word += c
            if word:
                words.append(word.capitalize())
                word = ""
    if word:
        words.append(word.capitalize())
    if non_word:
        words.append(non_word)
    if clean:
        keep_chars = set(keep_chars)
        result = "".join([do_clean(x, keep_chars) for x in words])
    else:
        result = "".join(words)
    if len(result) < 1:
        return result
    if lower_first:
        result = result[0].lower() + result[1:]
    return result

def no_mapping(value):
    return value

def none_to_empty_string(value):
    if value is None:
        return ""
    else:
        return value

def strip_string(value):
    """If value is str, then do string strip, or else returns the value itself.
    """
    if isinstance(value, str):
        return value.strip()
    else:
        return value


def format_with_mapping(template, mapping, *args, **kwargs):
    def trans(value):
        if callable(mapping):
            return mapping(value)
        else:
            return mapping.get(value, value)
    new_args = []
    new_kwargs = {}
    names = re.findall('{([^}:]*)', template)
    counter = 0
    for index in range(len(names)):
        if names[index] == "":
            names[index] = counter
            counter += 1
        elif names[index].isdigit():
            names[index] = int(names[index])
    ps_args = [x for x in names if isinstance(x, int)]
    if ps_args:
        max_args_index = max(ps_args)
        for index in range(max_args_index+1):
            if index in names:
                value = trans(args[index])
            else:
                value = None
            new_args.append(value)
    for key, value in kwargs.items():
        if key in names:
            value = trans(kwargs[key])
        new_kwargs[key] = value
    return template.format(*new_args, **new_kwargs)


default_quotes = [
    '"""', # quote left and quote right are the same
    "'''",
    '"',
    "'",
    "`",
    ('“', '”'), # quote left and quote right are NOT the same
    ("‘", "’"),
    ("『", "』"),
    ("「", "」"),
    ("﹁", "﹂"),
    ("﹃", "﹄"),
    ("｢", "｣"),
    ]

def unquote(value, quotes=None):
    """Trim one level quote. If not quoted, do nothing.
    """
    quotes = quotes or default_quotes
    for quote_pair in quotes:
        if isinstance(quote_pair, str):
            quote_pair = (quote_pair, quote_pair)
        if value.startswith(quote_pair[0]) and value.endswith(quote_pair[1]):
            return value[len(quote_pair[0]):-1*len(quote_pair[1])]
    return value


def is_uuid(value, allow_bad_characters=False):
    """Test if the value is UUID typed or UUID liked str.
    
    If allow_bad_characters=True, 
    treat c1fd56f3-bd79-42ed-a45c-d711c4032bag liked string as UUID,
    even it contains NON hex character(the last character g is NOT a hex digist).
    """
    if isinstance(value, uuid.UUID):
        return True
    if isinstance(value, bytes):
        try:
            _ = uuid.UUID(bytes=value)
            return True
        except ValueError:
            return False
    elif isinstance(value, (tuple, list)):
        try:
            _ = uuid.UUID(fields=value)
            return True
        except ValueError:
            return False
    elif isinstance(value, int):
        try:
            _ = uuid.UUID(int=value)
            return True
        except ValueError:
            return False
    else:
        try:
            _ = uuid.UUID(value)
            return True
        except ValueError:
            if allow_bad_characters:
                pattern = '^[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}$'
                if re.match(pattern, value):
                    return True
            return False

def stringlist_append(string_value, new_element, separator=",", allow_duplicate=True):
    elements = split(string_value, [separator], strip=True)
    if allow_duplicate or (not new_element in elements):
        elements.append(new_element)
    return separator.join(elements)

def html_element_css_append(classes, new_class_name):
    return stringlist_append(classes, new_class_name, separator=" ", allow_duplicate=False)


def remove_prefix(thestring, prefix):
    if thestring.startswith(prefix):
        return thestring[len(prefix):]
    else:
        return thestring

def remove_suffix(thestring, suffix):
    if thestring.endswith(suffix):
        if len(suffix):
            return thestring[:-len(suffix)]
        else:
            return thestring
    else:
        return thestring

def encodable(value:str, encoding:str="utf-8") -> bool:
    """Test if the string value can be encoded by special encoding.

    Examples:

    In [11]: strutils.encodable('hello') # ascii letters can be encoded by utf-8 encoding.
    Out[11]: True

    In [12]: strutils.encodable('测试') # 中文 测试 can be encoded by utf-8 encoding.
    Out[12]: True

    In [13]: strutils.encodable('测试', encoding='big5') # 中文 测试 can NOT be encoded by big5 encoding.
    Out[13]: False

    """
    try:
        value.encode(encoding)
        return True
    except UnicodeEncodeError:
        return False

def decodable(value:bytes, encoding:str="utf-8") -> bool:
    """Test if the bytes value can be decoded by special encoding.

    Examples:

    In [2]: strutils.decodable('测试'.encode('gbk')) # string encoded by gbk can not be decoded by utf-8
    Out[2]: False

    In [3]: strutils.decodable('测试'.encode('gbk'), encoding='gbk') # string encoded by gbk can be decoded by gbk
    Out[3]: True

    """
    try:
        value.decode(encoding)
        return True
    except UnicodeDecodeError:
        return False

def chunk(value:str, size:int) -> typing.List[str]:
    """Split string value into chunks. Chunk size must be greater than 0.

    Examples:

    In [33]: strutils.chunk('hello', 3)
    Out[33]: ['hel', 'lo']

    In [34]: strutils.chunk('hello', 6)
    Out[34]: ['hello']

    In [35]: strutils.chunk('hello', 5)
    Out[35]: ['hello']

    """
    if size < 1:
        raise ValueError("chunk size must be greater than 0...")
    if value is None:
        return []
    chunks = []
    length = len(value)
    start = 0
    while start < length:
        chunks.append(value[start:start+size])
        start += size
    return chunks


def get_all_substrings(value):
    """Get all substrings of the value.
    
    Examples:

    In [4]: strutils.get_all_substrings('a')
    Out[4]: {'a'}

    In [5]: strutils.get_all_substrings('ab')
    Out[5]: {'a', 'ab', 'b'}

    In [6]: strutils.get_all_substrings('abc')
    Out[6]: {'a', 'ab', 'abc', 'b', 'bc', 'c'}

    In [7]: strutils.get_all_substrings('abcd')
    Out[7]: {'a', 'ab', 'abc', 'abcd', 'b', 'bc', 'bcd', 'c', 'cd', 'd'}

    In [8]: strutils.get_all_substrings('abcde')
    Out[8]: 
    {'a',
    'ab',
    'abc',
    'abcd',
    'abcde',
    'b',
    'bc',
    'bcd',
    'bcde',
    'c',
    'cd',
    'cde',
    'd',
    'de',
    'e'}
    """
    substrings = set()
    for length in range(len(value)):
        length += 1
        for index in range(len(value)-length+1):
            substring = value[index:index+length]
            substrings.add(substring)
    return substrings

