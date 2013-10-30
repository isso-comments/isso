# -*- encoding: utf-8 -*-

import socket

from contextlib import closing

try:
    import httplib
except ImportError:
    import http.client as httplib

from isso.utils import parse


class curl(object):

    def __init__(self, method, host, path, timeout=3):
        self.method = method
        self.host = host
        self.path = path
        self.timeout = timeout

    def __enter__(self):

        host, port, ssl = parse.host(self.host)
        http = httplib.HTTPSConnection if ssl else httplib.HTTPConnection

        self.con = http(host, port, timeout=self.timeout)

        try:
            self.con.request(self.method, self.path)
        except (httplib.HTTPException, socket.error):
            return None

        return self.con.getresponse()

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close()
