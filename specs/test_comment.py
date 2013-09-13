
from __future__ import unicode_literals

import os
import json
import urllib
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso, notify
from isso.models import Comment


class FakeIP(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['REMOTE_ADDR'] = '192.168.1.1'
        return self.app(environ, start_response)


class TestComments(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()

        self.app = Isso(self.path, '...', '...', 15*60, "...", notify.NullMailer())
        self.app.wsgi_app = FakeIP(self.app.wsgi_app)

        self.client = Client(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    def tearDown(self):
        os.unlink(self.path)

    def testGet(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.get('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200

        rv = json.loads(r.data)

        assert rv['id'] == 1
        assert rv['text'] == '<p>Lorem ipsum ...</p>\n'

    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))

        assert rv.status_code == 201
        assert len(filter(lambda header: header[0] == 'Set-Cookie', rv.headers)) == 1

        rv = json.loads(rv.data)

        assert rv["mode"] == 1
        assert rv["text"] == '<p>Lorem ipsum ...</p>\n'

    def testCreateAndGetMultiple(self):

        for i in range(20):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Spam'}))

        r = self.get('/?uri=%2Fpath%2F')
        assert r.status_code == 200

        rv = json.loads(r.data)
        assert len(rv) == 20

    def testGetInvalid(self):

        assert self.get('/?uri=%2Fpath%2F&id=123').status_code == 404
        assert self.get('/?uri=%2Fpath%2Fspam%2F&id=123').status_code == 404
        assert self.get('/?uri=?uri=%foo%2F').status_code == 404

    def testUpdate(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        self.put('/?uri=%2Fpath%2F&id=1', data=json.dumps({
            'text': 'Hello World', 'author': 'me', 'website': 'http://example.com/'}))

        r = self.get('/?uri=%2Fpath%2F&id=1&plain=1')
        assert r.status_code == 200

        rv = json.loads(r.data)
        assert rv['text'] == 'Hello World'
        assert rv['author'] == 'me'
        assert rv['website'] == 'http://example.com/'
        assert 'modified' in rv

    def testDelete(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.delete('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200
        assert json.loads(r.data) == None
        assert self.get('/?uri=%2Fpath%2F&id=1').status_code == 404

    def testDeleteWithReference(self):

        client = Client(self.app, Response)
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First', 'parent': 1}))

        r = client.delete('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200
        assert Comment(**json.loads(r.data)).deleted

        assert self.get('/?uri=%2Fpath%2F&id=1').status_code == 200
        assert self.get('/?uri=%2Fpath%2F&id=2').status_code == 200

        r = client.delete('/?uri=%2Fpath%2F&id=2')
        assert self.get('/?uri=%2Fpath%2F').status_code == 404

    def testDeleteWithMultipleReferences(self):
        """
        [ comment 1 ]
            |
            --- [ comment 2, ref 1 ]
                    |
                    --- [ comment 3, ref 2 ]
                    |
                    --- [ comment 4, ref 2 ]
        [ comment 5 ]
        """
        client = Client(self.app, Response)

        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Second', 'parent': 1}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Third 1', 'parent': 2}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Third 2', 'parent': 2}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': '...'}))

        client.delete('/?uri=%2Fpath%2F&id=1')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/?uri=%2Fpath%2F&id=2')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/?uri=%2Fpath%2F&id=3')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/?uri=%2Fpath%2F&id=4')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/?uri=%2Fpath%2F&id=5')
        assert self.get('/?uri=%2Fpath%2F').status_code == 404

    def testPathVariations(self):

        paths = ['/sub/path/', '/path.html', '/sub/path.html', 'path', '/']

        for path in paths:
            assert self.post('/new?' + urllib.urlencode({'uri': path}),
                             data=json.dumps({'text': '...'})).status_code == 201

        for path in paths:
            assert self.get('/?' + urllib.urlencode({'uri': path})).status_code == 200
            assert self.get('/?' + urllib.urlencode({'uri': path, id: 1})).status_code == 200

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):

        mallory = Client(self.app, Response)
        mallory.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Foo'}))
        mallory.delete('/?uri=%2Fpath%2F&id=1')

        bob = Client(self.app, Response)
        bob.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Bar'}))

        assert mallory.delete('/?uri=%2Fpath%2F&id=1').status_code == 403
        assert bob.delete('/?uri=%2Fpath%2F&id=1').status_code == 200

    def testHash(self):

        a = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Aaa"}))
        b = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Bbb"}))
        c = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Ccc", "email": "..."}))

        assert a.status_code == b.status_code == c.status_code == 201
        a = json.loads(a.data)
        b = json.loads(b.data)
        c = json.loads(c.data)

        assert a['hash'] != '192.168.1.1'
        assert a['hash'] == b['hash']
        assert a['hash'] != c['hash']

    def testVisibleFields(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))
        assert rv.status_code == 201

        rv = json.loads(rv.data)

        for key in Comment.fields:
            rv.pop(key)

        assert rv.keys() == []

    def testCounts(self):

        assert self.get('/count?uri=%2Fpath%2F').status_code == 404
        self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 200
        assert json.loads(rv.data) == 1

        for x in range(3):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 200
        assert json.loads(rv.data) == 4

        for x in range(4):
            self.delete('/?uri=%%2Fpath%%2F&id=%i' % (x + 1))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 404

