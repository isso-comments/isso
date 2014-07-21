# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import json

import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso, config, dist
from isso.utils import http


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


class Dummy(object):

    status = 200

    def __enter__(self):
        return self

    def read(self):
        return ''

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


curl = lambda method, host, path: Dummy()
loads = lambda data: json.loads(data.decode('utf-8'))

http.curl = curl


class TestComments(unittest.TestCase):

    def setUp(self):
        conf = config.load(os.path.join(dist.location, "isso", "defaults.ini"))
        conf.set("general", "dbpath", "sqlite:///:memory:")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.app = Isso(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    # done (except Markup)
    def testGet(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.get('/id/1')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)

        self.assertEqual(rv['id'], 1)
        self.assertEqual(rv['text'], '<p>Lorem ipsum ...</p>')

    # done (except Set-Cookie)
    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))

        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        self.assertIn("X-Set-Cookie", rv.headers)

        rv = loads(rv.data)

        self.assertEqual(rv["mode"], 1)
        self.assertEqual(rv["text"], '<p>Lorem ipsum ...</p>')

    def testGetLimited(self):

        for i in range(20):
            self.post('/new?uri=test', data=json.dumps({'text': '...'}))

        r = self.get('/?uri=test&limit=10')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv['replies']), 10)

    def testGetNested(self):

        self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        self.post('/new?uri=test', data=json.dumps({'text': '...', 'parent': 1}))

        r = self.get('/?uri=test&parent=1')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv['replies']), 1)

    def testGetLimitedNested(self):

        self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        for i in range(20):
            self.post('/new?uri=test', data=json.dumps({'text': '...', 'parent': 1}))

        r = self.get('/?uri=test&parent=1&limit=10')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv['replies']), 10)

    # done (except plain)
    def testUpdate(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        self.put('/id/1', data=json.dumps({
            'text': 'Hello World', 'author': 'me', 'website': 'http://example.com/'}))

        r = self.get('/id/1?plain=1')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(rv['text'], 'Hello World')
        self.assertEqual(rv['author'], 'me')
        self.assertEqual(rv['website'], 'http://example.com/')
        self.assertIn('modified', rv)

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):

        mallory = JSONClient(self.app, Response)
        mallory.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Foo'}))
        mallory.delete('/id/1')

        bob = JSONClient(self.app, Response)
        bob.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Bar'}))

        self.assertEqual(mallory.delete('/id/1').status_code, 403)
        self.assertEqual(bob.delete('/id/1').status_code, 200)

    def testCSRF(self):

        js = "application/json"
        form = "application/x-www-form-urlencoded"

        self.post('/new?uri=%2F', data=json.dumps({"text": "..."}))

        # no header is fine (default for XHR)
        self.assertEqual(self.post('/id/1/dislike', content_type="").status_code, 200)

        # x-www-form-urlencoded is definitely not RESTful
        self.assertEqual(self.post('/id/1/dislike', content_type=form).status_code, 403)
        self.assertEqual(self.post('/new?uri=%2F', data=json.dumps({"text": "..."}),
                                         content_type=form).status_code, 403)
        # just for the record
        self.assertEqual(self.post('/id/1/dislike', content_type=js).status_code, 200)
