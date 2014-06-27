# -*- encoding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

try:
    import uwsgi
except ImportError:
    uwsgi = None

from . import Base


class uWSGICache(Base):
    """Utilize uWSGI caching framework, in-memory and SMP-safe.
    """

    serialize = True

    def __init__(self, threshold=-1, timeout=3600):
        if uwsgi is None:
            raise RuntimeError("uWSGI not available")

        super(uWSGICache, self).__init__(threshold, timeout)

    def _get(self, ns, key):
        if not uwsgi.cache_exists(key, ns):
            raise KeyError
        return uwsgi.cache_get(key, ns)

    def _delete(self, ns, key):
        uwsgi.cache_del(key, ns)

    def _set(self, ns, key, value):
        uwsgi.cache_set(key, value, self.timeout, ns)
