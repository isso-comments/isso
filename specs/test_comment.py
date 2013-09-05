
import json
import urllib
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso
from isso.models import Comment


def comment(**kw):
    return Comment.fromjson(Isso.dumps(kw))


class TestComments(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        self.app = Isso(self.path, '...', '...', 15*60, "...")

        self.client = Client(self.app, Response)
        self.get = lambda *x, **z: self.client.get(*x, **z)
        self.put = lambda *x, **z: self.client.put(*x, **z)
        self.post = lambda *x, **z: self.client.post(*x, **z)
        self.delete = lambda *x, **z: self.client.delete(*x, **z)

    def testGet(self):

        self.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Lorem ipsum ...')))
        r = self.get('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200

        rv = json.loads(r.data)

        assert rv['id'] == 1
        assert rv['text'] == 'Lorem ipsum ...'

    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Lorem ipsum ...')))

        assert rv.status_code == 201
        assert len(filter(lambda header: header[0] == 'Set-Cookie', rv.headers)) == 1

        c = Comment.fromjson(rv.data)

        assert not c.pending
        assert not c.deleted
        assert c.text == '<p>Lorem ipsum ...</p>\n'

    def testCreateAndGetMultiple(self):

        for i in range(20):
            self.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Spam')))

        r = self.get('/?uri=%2Fpath%2F')
        assert r.status_code == 200

        rv = json.loads(r.data)
        assert len(rv) == 20

    def testGetInvalid(self):

        assert self.get('/?uri=%2Fpath%2F&id=123').status_code == 404
        assert self.get('/?uri=%2Fpath%2Fspam%2F&id=123').status_code == 404
        assert self.get('/?uri=?uri=%foo%2F').status_code == 404

    def testUpdate(self):

        self.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Lorem ipsum ...')))
        self.put('/?uri=%2Fpath%2F&id=1', data=Isso.dumps(comment(
            text='Hello World', author='me', website='http://example.com/')))

        r = self.get('/?uri=%2Fpath%2F&id=1&plain=1')
        assert r.status_code == 200

        rv = json.loads(r.data)
        assert rv['text'] == 'Hello World'
        assert rv['author'] == 'me'
        assert rv['website'] == 'http://example.com/'
        assert 'modified' in rv

    def testDelete(self):

        self.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Lorem ipsum ...')))
        r = self.delete('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200
        assert json.loads(r.data) == None
        assert self.get('/?uri=%2Fpath%2F&id=1').status_code == 404

    def testDeleteWithReference(self):

        client = Client(self.app, Response)
        client.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='First')))
        client.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='First', parent=1)))

        r = client.delete('/?uri=%2Fpath%2F&id=1')
        assert r.status_code == 200
        assert Comment(**json.loads(r.data)).deleted

        assert self.get('/?uri=%2Fpath%2F&id=1').status_code == 200
        assert self.get('/?uri=%2Fpath%2F&id=2').status_code == 200

    def testPathVariations(self):

        paths = ['/sub/path/', '/path.html', '/sub/path.html', 'path', '/']

        for path in paths:
            assert self.post('/new?' + urllib.urlencode({'uri': path}),
                             data=Isso.dumps(comment(text='...'))).status_code == 201

        for path in paths:
            assert self.get('/?' + urllib.urlencode({'uri': path})).status_code == 200
            assert self.get('/?' + urllib.urlencode({'uri': path, id: 1})).status_code == 200

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):

        mallory = Client(self.app, Response)
        mallory.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Foo')))
        mallory.delete('/?uri=%2Fpath%2F&id=1')

        bob = Client(self.app, Response)
        bob.post('/new?uri=%2Fpath%2F', data=Isso.dumps(comment(text='Bar')))

        assert mallory.delete('/?uri=%2Fpath%2F&id=1').status_code == 403
        assert bob.delete('/?uri=%2Fpath%2F&id=1').status_code == 200
