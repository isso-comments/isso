# -*- encoding: utf-8 -*-


def _TypeError(expected, val):
    if isinstance(expected, (list, tuple)):
        expected = ", ".join(ex.__name__ for ex in expected)
    else:
        expected = expected.__name__
    return TypeError("Expected {0}, not {1}".format(
        expected, val.__class__.__name__))


def require(val, expected):
    """Assure that :param val: is an instance of :param expected: or raise a
    :exception TypeError: indicating what's expected.

    >>> require(23, int)
    >>> require(None, bool)
    Traceback (most recent call last):
        ...
    TypeError: Expected bool, not NoneType
    """
    if not isinstance(val, expected):
        raise _TypeError(expected, val)
