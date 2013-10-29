# -*- encoding: utf-8 -*-

import socket

from contextlib import closing

try:
    import httplib
except ImportError:
    import http.client as httplib

from isso.utils import parse


def curl(method, host, path, timeout=3):

    host, port, ssl = parse.host(host)
    http = httplib.HTTPSConnection if ssl else httplib.HTTPConnection

    with closing(http(host, port, timeout=timeout)) as con:
        try:
            con.request(method, path)
        except (httplib.HTTPException, socket.error):
            return None
        return con.getresponse()
