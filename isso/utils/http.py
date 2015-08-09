# -*- encoding: utf-8 -*-

import socket

import requests

from isso import dist
from isso.wsgi import urlsplit


class curl(object):
    """Easy to use wrapper around :module:`requests`.  Use as context-manager
    so we can close the response properly.

    .. code-block:: python

        with http.curl('GET', 'http://localhost:8080', '/') as resp:
            if resp:  # may be None if request failed
                return resp.status_code
    """

    headers = {
        "User-Agent": "Isso/{0} (+http://posativ.org/isso)".format(dist.version)
    }
    methods = {
        "GET": requests.get,
        "HEAD": requests.head
    }

    def __init__(self, method, host, path, timeout=3):
        self.method = method
        self.host = host
        self.path = path
        self.timeout = timeout

    def __enter__(self):

        host, port, ssl = urlsplit(self.host)

        try:
            return self.methods[self.method](self.host + self.path,
                    timeout=self.timeout, headers=self.headers)
        except (KeyError, requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        pass
