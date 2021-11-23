import random
import string


def compare_constant_time(a, b):
    """Compare a and b in constant time.
    Use to reduce risk of timing attacks"""
    assert isinstance(a, bytes)
    assert isinstance(b, bytes)
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(bytearray(a), bytearray(b)):
        result |= x ^ y
    return result == 0


def generate_random_string(length=32):
    return "".join(
        [
            random.choice(string.ascii_letters + string.digits)
            for _ in range(length)
        ]
    )
