# -*- encoding: utf-8 -*-

import socket

try:
    from urllib2 import urlopen, Request, URLError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import URLError

from isso import dist
from isso.utils.parse import urlsplit, urlunsplit


class curl(object):
    """Easy to use wrapper around :module:`urllib`.

    .. code-block:: python

        with http.curl('GET', 'http://localhost:8080/') as resp:
            if resp:  # may be None if request failed
                return resp.getcode()
    """

    default_headers = {
        "User-Agent": "Isso/{0} (+http://posativ.org/isso)".format(dist.version)
    }

    def __init__(self, method, url, body=None, extra_headers={}, timeout=3):
        self.method = method
        self.url = url
        if body is None:
            self.body = None
        else:
            self.body = body.encode("utf8")
        self.headers = self.default_headers.copy()
        self.headers.update(extra_headers)
        self.timeout = timeout

    def __enter__(self):

        try:
            req = Request(self.url, self.body, self.headers, method=self.method)
        except TypeError:
            req = Request(self.url, self.body, self.headers)

        try:
            return urlopen(req, None, self.timeout)
        except URLError:
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        pass
