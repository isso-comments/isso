# -*- encoding: utf-8 -*-

import socket

try:
    import httplib
    from urlparse import urlparse
except ImportError:
    import http.client as httplib
    from urllib.parse import urlparse

from isso import dist
from isso.wsgi import urlsplit

MAX_RETRY_COUNT = 3


class curl(object):
    """Easy to use wrapper around :module:`httplib`.  Use as context-manager
    so we can close the response properly.

    .. code-block:: python

        with http.curl('GET', 'http://localhost:8080', '/') as resp:
            if resp:  # may be None if request failed
                return resp.status
    """

    headers = {
        "User-Agent": "Isso/{0} (+https://posativ.org/isso)".format(dist.version)
    }

    def __init__(self, method, host, path, timeout=3):
        self.method = method
        self.host = host
        self.path = path
        self.timeout = timeout

    def __enter__(self):
        host, port, ssl = urlsplit(self.host)
        http = httplib.HTTPSConnection if ssl else httplib.HTTPConnection

        for _ in range(MAX_RETRY_COUNT):
            self.con = http(host, port, timeout=self.timeout)
            try:
                self.con.request(self.method, self.path, headers=self.headers)
            except (httplib.HTTPException, socket.error):
                return None

            try:
                resp = self.con.getresponse()
                if resp.status == 301:
                    location = resp.getheader('Location')
                    if location:
                        self.con.close()
                        self.path = urlparse(location).path
                    else:
                        return None
                else:
                    return resp
            except (httplib.HTTPException, socket.timeout, socket.error):
                return None

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close()
