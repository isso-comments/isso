# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import codecs
import hashlib

from isso.utils import types
from isso.compat import string_types, text_type as str

try:
    from werkzeug.security import pbkdf2_bin as pbkdf2
except ImportError:
    try:
        from passlib.utils.pbkdf2 import pbkdf2 as _pbkdf2

        def pbkdf2(val, salt, iterations, dklen, func):
            return _pbkdf2(val, salt, iterations, dklen, ("hmac-" + func).encode("utf-8"))
    except ImportError as ex:
        raise ImportError("No PBKDF2 implementation found. Either upgrade " +
                          "to `werkzeug` 0.9 or install `passlib`.")


class Hash(object):

    func = None
    salt = b"Eech7co8Ohloopo9Ol6baimi"

    def __init__(self, salt=None, func="sha1"):

        if func is not None:
            hashlib.new(func)  # may not be available
            self.func = func

        if salt is not None:
            types.require(salt, bytes)
            self.salt = salt

    def hash(self, val):
        """Calculate hash from value (must be bytes).
        """

        types.require(val, bytes)

        rv = self.compute(val)

        types.require(rv, bytes)

        return rv

    def uhash(self, val):
        """Calculate hash from unicode value and return hex value as unicode
        """
        types.require(val, string_types)
        return codecs.encode(self.hash(val.encode("utf-8")), "hex_codec").decode("utf-8")

    def compute(self, val):
        if self.func is None:
            return val

        h = hashlib.new(self.func)
        h.update(val)

        return h.digest()


class PBKDF2(Hash):
    
    def __init__(self, salt=None, iterations=1000, dklen=6, func="sha1"):
        super(PBKDF2, self).__init__(salt)

        self.iterations = iterations
        self.dklen = dklen
        self.func = func

    def compute(self, val):
        return pbkdf2(val, self.salt, self.iterations, self.dklen, self.func)


def new(algorithm, salt=None):
    """Factory to create hash functions from configuration section. If an
    algorithm takes custom parameters, you can separate them by a colon like
    this: pbkdf2:arg1:arg2:arg3."""

    if salt is None:
        salt = ''
    salt = salt.encode("utf-8")

    if algorithm == "none":
        return Hash(salt, None)
    elif algorithm.startswith("pbkdf2"):
        kwargs = {}
        tail = algorithm.partition(":")[2]
        for func, key in ((int, "iterations"), (int, "dklen"), (str, "func")):
            head, _, tail = tail.partition(":")
            if not head:
                break
            kwargs[key] = func(head)

        return PBKDF2(salt, **kwargs)
    else:
        return Hash(salt, algorithm)


sha1 = Hash(func="sha1").uhash