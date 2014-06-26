# -*- encoding: utf-8 -*-


def _TypeError(expected, val):
    if isinstance(expected, (list, tuple)):
        expected = ", ".join(expected.__name__)
    else:
        expected = expected.__name__
    return TypeError("Expected {0}, not {1}".format(
        expected, val.__class__.__name__))


def require(val, expected):
    if not isinstance(val, expected):
        raise _TypeError(expected, val)
