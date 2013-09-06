
import os
import json
import urllib
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso
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

        self.app = Isso(self.path, '...', '...', 15*60, "...")
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
        assert rv['text'] == 'Lorem ipsum ...'

    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))

        assert rv.status_code == 201
        assert len(filter(lambda header: header[0] == 'Set-Cookie', rv.headers)) == 1

        c = Comment.fromjson(rv.data)

        assert not c.pending
        assert not c.deleted
        assert c.text == '<p>Lorem ipsum ...</p>\n'

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
