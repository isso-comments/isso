# -*- encoding: utf-8 -*-

import socket

try:
    import httplib
except ImportError:
    import http.client as httplib

from isso import dist
from isso.wsgi import urlsplit


class curl(object):
    """Easy to use wrapper around :module:`httplib`.  Use as context-manager
    so we can close the response properly.

    .. code-block:: python

        with http.curl('GET', 'http://localhost:8080', '/') as resp:
            if resp:  # may be None if request failed
                return resp.status
    """

    default_headers = {
        "User-Agent": "Isso/{0} (+http://posativ.org/isso)".format(dist.version)
    }

    def __init__(self, method, host, path, body=None, extra_headers={}, timeout=3):
        self.method = method
        self.host = host
        self.path = path
        self.body = body
        self.headers = self.default_headers.copy()
        self.headers.update(extra_headers)
        self.timeout = timeout

    def __enter__(self):

        host, port, ssl = urlsplit(self.host)
        http = httplib.HTTPSConnection if ssl else httplib.HTTPConnection

        self.con = http(host, port, timeout=self.timeout)

        try:
            self.con.request(self.method, self.path, body=self.body, headers=self.headers)
        except (httplib.HTTPException, socket.error):
            return None

        try:
            return self.con.getresponse()
        except (httplib.HTTPException, socket.timeout, socket.error):
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close()
