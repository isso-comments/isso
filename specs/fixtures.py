# -*- encoding: utf-8 -*-

import json


class FakeIP(object):

    def __init__(self, app, ip):
        self.app = app
        self.ip = ip

    def __call__(self, environ, start_response):
        environ['REMOTE_ADDR'] = self.ip
        environ['HTTP_ORIGIN'] = "http://localhost:8080"
        return self.app(environ, start_response)


class Dummy:

    status = 200

    def __enter__(self):
        return self

    def read(self):
        return ''

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

curl = lambda method, host, path: Dummy()
loads = lambda data: json.loads(data.decode('utf-8'))
