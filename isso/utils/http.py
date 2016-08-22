# -*- encoding: utf-8 -*-

import socket

try:
    import httplib
except ImportError:
    import http.client as httplib

from isso import dist
from isso.utils.parse import urlsplit, urlunsplit


class curl(object):
    """Easy to use wrapper around :module:`httplib`.  Use as context-manager
    so we can close the response properly.

    .. code-block:: python

        with http.curl('GET', 'http://localhost:8080/') as resp:
            if resp:  # may be None if request failed
                return resp.status
    """

    default_headers = {
        "User-Agent": "Isso/{0} (+http://posativ.org/isso)".format(dist.version)
    }

    def __init__(self, method, url, body=None, extra_headers={}, timeout=3):
        self.method = method
        self.url = url
        self.body = body
        self.headers = self.default_headers.copy()
        self.headers.update(extra_headers)
        self.timeout = timeout

    def __enter__(self):

        u = urlsplit(self.url, "http")
        host = u.netloc.rsplit(':')[0]
        path = urlunsplit(("", "") + u[2:])
        http = httplib.HTTPSConnection if u.scheme == "https" else httplib.HTTPConnection

        self.con = http(host, u.port, timeout=self.timeout)

        try:
            self.con.request(self.method, path, body=self.body, headers=self.headers)
        except (httplib.HTTPException, socket.error):
            return None

        try:
            return self.con.getresponse()
        except (httplib.HTTPException, socket.timeout, socket.error):
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close()
