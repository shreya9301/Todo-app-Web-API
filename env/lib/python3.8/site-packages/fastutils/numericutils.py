
def binary_decompose(value):
    values = set()
    binary_string = bin(value)[2:]
    length = len(binary_string) - 1
    for c in binary_string:
        if c == "1":
            values.add(2**length)
        length -= 1
    return values


def decimal_change_base(number, base=16, characters="0123456789abcdefghijklmnopqrstuvwxyz"):
    digits = []
    while number:
        digits.append( number % base )
        number //= base
    digits.reverse()
    if not digits:
        digits.append(0)
    if characters:
        return "".join([characters[x] for x in digits])
    else:
        return digits


def get_float_part(value, precision=7):
    value = abs(value)
    mod = 10 ** precision
    value_all = int(value * mod)
    value_int = int(value) * mod
    value_float = value_all - value_int
    return value_float

def float_split(value, precision=7):
    if value >= 0:
        sign = 1
    else:
        sign = -1
    value = abs(value)
    int_value = int(value)
    float_value = get_float_part(value, precision)
    return sign, int_value, float_value


NUMERIC_TYPES = (int, float)
