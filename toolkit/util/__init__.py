import random
import string


def compare_constant_time(a, b):
    """Compare a and b in constant time.
    Use to reduce risk of timing attacks"""
    assert isinstance(a, str)
    assert isinstance(b, str)
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def generate_random_string(length=32):
    return ''.join([random.choice(string.ascii_letters + string.digits) for d in range(length)])
