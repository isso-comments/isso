# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import abc
import json

from isso.utils import types
from isso.compat import string_types


def pickle(value):
    return json.dumps(value).encode("utf-8")


def unpickle(value):
    return json.loads(value.decode("utf-8"))


class Base(object):
    """Base class for all cache objects.

    Arbitrary values are set by namespace and key. Namespace and key must be
    strings, the underlying cache implementation may use :func:`pickle` and
    :func:`unpickle:` to safely un-/serialize Python primitives.

    :param threshold: maximum size of the cache
    :param timeout: key expiration
    """

    __metaclass__ = abc.ABCMeta

    # enable serialization of Python primitives
    serialize = False

    def __init__(self, threshold, timeout):
        self.threshold = threshold
        self.timeout = timeout

    def get(self, ns, key, default=None):
        types.require(ns, string_types)
        types.require(key, string_types)

        try:
            value = self._get(ns.encode("utf-8"), key.encode("utf-8"))
        except KeyError:
            return default
        else:
            if self.serialize:
                value = unpickle(value)
            return value

    @abc.abstractmethod
    def _get(self, ns, key):
        return

    def set(self, ns, key, value):
        types.require(ns, string_types)
        types.require(key, string_types)

        if self.serialize:
            value = pickle(value)

        return self._set(ns.encode("utf-8"), key.encode("utf-8"), value)

    @abc.abstractmethod
    def _set(self, ns, key, value):
        return

    def delete(self, ns, key):
        types.require(ns, string_types)
        types.require(key, string_types)

        return self._delete(ns.encode("utf-8"), key.encode("utf-8"))

    @abc.abstractmethod
    def _delete(self, ns, key):
        return


class Cache(Base):
    """Implements a simple in-memory cache; once the threshold is reached, all
    cached elements are discarded (the timeout parameter is ignored).
    """

    def __init__(self, threshold=512, timeout=-1):
        super(Cache, self).__init__(threshold, timeout)
        self.cache = {}

    def _get(self, ns, key):
        return self.cache[ns + b'-' + key]

    def _set(self, ns, key, value):
        if len(self.cache) > self.threshold - 1:
            self.cache.clear()
        self.cache[ns + b'-' + key] = value

    def _delete(self, ns, key):
        self.cache.pop(ns + b'-' + key, None)


from .sa import SACache
from .uwsgi import uWSGICache

__all__ = ["Cache", "SACache", "uWSGICache"]
