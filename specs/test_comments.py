# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import json
import tempfile
import unittest

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from werkzeug.wrappers import Response

from isso import Isso, core
from isso.utils import http
from isso.views import comments

from fixtures import curl, loads, FakeIP, JSONClient
http.curl = curl


class TestComments(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = core.Config.load(None)
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    def tearDown(self):
        os.unlink(self.path)

    def testGet(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.get('/id/1')
        assert r.status_code == 200

        rv = loads(r.data)

        assert rv['id'] == 1
        assert rv['text'] == '<p>Lorem ipsum ...</p>'

    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))

        assert rv.status_code == 201
        assert any(filter(lambda header: header[0] == 'Set-Cookie', rv.headers))

        rv = loads(rv.data)

        assert rv["mode"] == 1
        assert rv["text"] == '<p>Lorem ipsum ...</p>'

    def textCreateWithNonAsciiText(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Здравствуй, мир!'}))

        assert rv.status_code == 201
        assert any(filter(lambda header: header[0] == 'Set-Cookie', rv.headers))

        rv = loads(rv.data)

        assert rv["mode"] == 1
        assert rv["text"] == '<p>Здравствуй, мир!</p>'

    def testCreateMultiple(self):

        a = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        b = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        c = self.post('/new?uri=test', data=json.dumps({'text': '...'}))

        assert loads(a.data)["id"] == 1
        assert loads(b.data)["id"] == 2
        assert loads(c.data)["id"] == 3

    def testCreateAndGetMultiple(self):

        for i in range(20):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Spam'}))

        r = self.get('/?uri=%2Fpath%2F')
        assert r.status_code == 200

        rv = loads(r.data)
        assert len(rv) == 20

    def testCreateBlank(self):
        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': ''}))
        assert rv.status_code == 400
        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': "\n\n\n"}))
        assert rv.status_code == 400

    def testGetInvalid(self):

        assert self.get('/?uri=%2Fpath%2F&id=123').status_code == 404
        assert self.get('/?uri=%2Fpath%2Fspam%2F&id=123').status_code == 404
        assert self.get('/?uri=?uri=%foo%2F').status_code == 404

    def testUpdate(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        self.put('/id/1', data=json.dumps({
            'text': 'Hello World', 'author': 'me', 'website': 'http://example.com/'}))

        r = self.get('/id/1?plain=1')
        assert r.status_code == 200

        rv = loads(r.data)
        assert rv['text'] == 'Hello World'
        assert rv['author'] == 'me'
        assert rv['website'] == 'http://example.com/'
        assert 'modified' in rv

    def testDelete(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.delete('/id/1')
        assert r.status_code == 200
        assert loads(r.data) == None
        assert self.get('/id/1').status_code == 404

    def testDeleteWithReference(self):

        client = JSONClient(self.app, Response)
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First', 'parent': 1}))

        r = client.delete('/id/1')
        assert r.status_code == 200
        assert loads(r.data)['mode'] == 4
        assert '/path/' in self.app.db.threads

        assert self.get('/?uri=%2Fpath%2F&id=1').status_code == 200
        assert self.get('/?uri=%2Fpath%2F&id=2').status_code == 200

        r = client.delete('/id/2')
        assert self.get('/?uri=%2Fpath%2F').status_code == 404
        assert '/path/' not in self.app.db.threads

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
        client = JSONClient(self.app, Response)

        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Second', 'parent': 1}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Third 1', 'parent': 2}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Third 2', 'parent': 2}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': '...'}))

        client.delete('/id/1')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/id/2')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/id/3')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/id/4')
        assert self.get('/?uri=%2Fpath%2F').status_code == 200
        client.delete('/id/5')
        assert self.get('/?uri=%2Fpath%2F').status_code == 404

    def testPathVariations(self):

        paths = ['/sub/path/', '/path.html', '/sub/path.html', 'path', '/']

        for path in paths:
            assert self.post('/new?' + urlencode({'uri': path}),
                             data=json.dumps({'text': '...'})).status_code == 201

        for i, path in enumerate(paths):
            assert self.get('/?' + urlencode({'uri': path})).status_code == 200
            assert self.get('/id/%i' % (i + 1)).status_code == 200

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):

        mallory = JSONClient(self.app, Response)
        mallory.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Foo'}))
        mallory.delete('/id/1')

        bob = JSONClient(self.app, Response)
        bob.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Bar'}))

        assert mallory.delete('/id/1').status_code == 403
        assert bob.delete('/id/1').status_code == 200

    def testHash(self):

        a = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Aaa"}))
        b = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Bbb"}))
        c = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Ccc", "email": "..."}))

        assert a.status_code == b.status_code == c.status_code == 201
        a = loads(a.data)
        b = loads(b.data)
        c = loads(c.data)

        assert isinstance(int(a['hash'], 16), int)
        assert a['hash'] != '192.168.1.1'
        assert a['hash'] == b['hash']
        assert a['hash'] != c['hash']

    def testVisibleFields(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))
        assert rv.status_code == 201

        rv = loads(rv.data)

        for key in comments.API.FIELDS:
            rv.pop(key)

        assert not any(rv.keys())

    def testCounts(self):

        assert self.get('/count?uri=%2Fpath%2F').status_code == 404
        self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 200
        assert loads(rv.data) == 1

        for x in range(3):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 200
        assert loads(rv.data) == 4

        for x in range(4):
            self.delete('/id/%i' % (x + 1))

        rv = self.get('/count?uri=%2Fpath%2F')
        assert rv.status_code == 404

    def testModify(self):
        self.post('/new?uri=test', data=json.dumps({"text": "Tpyo"}))

        self.put('/id/1', data=json.dumps({"text": "Tyop"}))
        assert loads(self.get('/id/1').data)["text"] == "<p>Tyop</p>"

        self.put('/id/1', data=json.dumps({"text": "Typo"}))
        assert loads(self.get('/id/1').data)["text"] == "<p>Typo</p>"

    def testDeleteCommentRemovesThread(self):

        rv = self.client.post('/new?uri=%2F', data=json.dumps({"text": "..."}))
        assert '/' in self.app.db.threads
        self.client.delete('/id/1')
        assert '/' not in self.app.db.threads

    def testCSRF(self):

        js = "application/json"
        form = "application/x-www-form-urlencoded"

        self.post('/new?uri=%2F', data=json.dumps({"text": "..."}))

        # no header is fine (default for XHR)
        assert self.post('/id/1/dislike', content_type="").status_code == 200

        # x-www-form-urlencoded is definitely not RESTful
        assert self.post('/id/1/dislike', content_type=form).status_code == 403
        assert self.post('/new?uri=%2F', data=json.dumps({"text": "..."}),
                                         content_type=form).status_code == 403
        # just for the record
        assert self.post('/id/1/dislike', content_type=js).status_code == 200

    def testCheckIP(self):
        assert self.get('/check-ip').data.decode("utf-8") == '192.168.1.0'


class TestModeratedComments(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = core.Config.load(None)
        conf.set("general", "dbpath", self.path)
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def tearDown(self):
        os.unlink(self.path)

    def testAddComment(self):

        rv = self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        assert rv.status_code == 202

        assert self.client.get('/id/1').status_code == 200
        assert self.client.get('/?uri=test').status_code == 404

        self.app.db.comments.activate(1)
        assert self.client.get('/?uri=test').status_code == 200


class TestPurgeComments(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = core.Config.load(None)
        conf.set("general", "dbpath", self.path)
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def testPurgeDoesNoHarm(self):
        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.activate(1)
        self.app.db.comments.purge(0)
        assert self.client.get('/?uri=test').status_code == 200

    def testPurgeWorks(self):
        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(0)
        assert self.client.get('/id/1').status_code == 404

        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(3600)
        assert self.client.get('/id/1').status_code == 200
