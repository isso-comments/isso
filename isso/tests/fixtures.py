# -*- encoding: utf-8 -*-

import json

from werkzeug.test import Client


class FakeIP(object):

    def __init__(self, app, ip):
        self.app = app
        self.ip = ip

    def __call__(self, environ, start_response):
        environ['REMOTE_ADDR'] = self.ip
        return self.app(environ, start_response)


class JSONClient(Client):

    def open(self, *args, **kwargs):
        kwargs.setdefault('content_type', 'application/json')
        return super(JSONClient, self).open(*args, **kwargs)


class Dummy:

    status = 200

    def __enter__(self):
        return self

    def read(self):
        return ''

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def curl(method, host, path):
    return Dummy()


def loads(data):
    return json.loads(data.decode('utf-8'))
