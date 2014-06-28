# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import json

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from werkzeug.wrappers import Response

from isso import Isso, config, dist
from isso.utils import http
from isso.views import comments

from isso.compat import iteritems

from fixtures import curl, loads, FakeIP, JSONClient
http.curl = curl


class TestComments(unittest.TestCase):

    def setUp(self):
        conf = config.load(os.path.join(dist.location, "isso", "defaults.ini"))
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.app = Isso(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    def testGet(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.get('/id/1')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)

        self.assertEqual(rv['id'], 1)
        self.assertEqual(rv['text'], '<p>Lorem ipsum ...</p>')

    def testCreate(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))

        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)

        rv = loads(rv.data)

        self.assertEqual(rv["mode"], 1)
        self.assertEqual(rv["text"], '<p>Lorem ipsum ...</p>')

    def textCreateWithNonAsciiText(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Здравствуй, мир!'}))

        self.assertEqual(rv.status_code, 201)
        rv = loads(rv.data)

        self.assertEqual(rv["mode"], 1)
        self.assertEqual(rv["text"], '<p>Здравствуй, мир!</p>')

    def testCreateMultiple(self):

        a = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        b = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        c = self.post('/new?uri=test', data=json.dumps({'text': '...'}))

        self.assertEqual(loads(a.data)["id"], 1)
        self.assertEqual(loads(b.data)["id"], 2)
        self.assertEqual(loads(c.data)["id"], 3)

    def testCreateAndGetMultiple(self):

        for i in range(20):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Spam'}))

        r = self.get('/?uri=%2Fpath%2F')
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv['replies']), 20)

    def testCreateInvalidParent(self):

        self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        self.post('/new?uri=test', data=json.dumps({'text': '...', 'parent': 1}))
        invalid = self.post('/new?uri=test', data=json.dumps({'text': '...', 'parent': 2}))

        self.assertEqual(loads(invalid.data)["parent"], 1)

    def testVerifyFields(self):

        verify = lambda comment: comments.API.verify(comment)[0]

        # text is missing
        self.assertFalse(verify({}))

        # invalid types
        self.assertFalse(verify({"text": "...", "parent": "xxx"}))
        for key in ("author", "website", "email"):
            self.assertFalse(verify({"text": True, key: 3.14}))

        # text too short and/or blank
        for text in ("", "\n\n\n"):
            self.assertFalse(verify({"text": text}))

        # email/website length
        self.assertTrue(verify({"text": "...", "email": "*"*254}))
        self.assertTrue(verify({"text": "...", "website": "google.de/" + "a"*128}))

        self.assertFalse(verify({"text": "...", "email": "*"*1024}))
        self.assertFalse(verify({"text": "...", "website": "google.de/" + "*"*1024}))

        # valid website url
        self.assertTrue(comments.isurl("example.tld"))
        self.assertTrue(comments.isurl("http://example.tld"))
        self.assertTrue(comments.isurl("https://example.tld"))
        self.assertTrue(comments.isurl("https://example.tld:1337/"))
        self.assertTrue(comments.isurl("https://example.tld:1337/foobar"))
        self.assertTrue(comments.isurl("https://example.tld:1337/foobar?p=1#isso-thread"))

        self.assertFalse(comments.isurl("ftp://example.tld/"))
        self.assertFalse(comments.isurl("tel:+1234567890"))
        self.assertFalse(comments.isurl("+1234567890"))
        self.assertFalse(comments.isurl("spam"))

    def testGetInvalid(self):

        self.assertEqual(self.get('/?uri=%2Fpath%2F&id=123').status_code, 404)
        self.assertEqual(self.get('/?uri=%2Fpath%2Fspam%2F&id=123').status_code, 404)
        self.assertEqual(self.get('/?uri=?uri=%foo%2F').status_code, 404)

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

    def testDelete(self):

        self.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Lorem ipsum ...'}))
        r = self.delete('/id/1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(loads(r.data), None)
        self.assertEqual(self.get('/id/1').status_code, 404)

    def testDeleteWithReference(self):

        client = JSONClient(self.app, Response)
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First', 'parent': 1}))

        r = client.delete('/id/1')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(loads(r.data)['mode'], 4)
        self.assertIn('/path/', self.app.db.threads)

        data = loads(client.get("/?uri=%2Fpath%2F").data)
        self.assertEqual(data["total_replies"], 1)

        self.assertEqual(self.get('/?uri=%2Fpath%2F&id=1').status_code, 200)
        self.assertEqual(self.get('/?uri=%2Fpath%2F&id=2').status_code, 200)

        r = client.delete('/id/2')
        self.assertEqual(self.get('/?uri=%2Fpath%2F').status_code, 404)
        self.assertNotIn('/path/', self.app.db.threads)

    def testDeleteWithMultipleReferences(self):
        """
        [ comment 1 ]
            |
            --- [ comment 2, ref 1 ]
            |
            --- [ comment 3, ref 1 ]
        [ comment 4 ]
        """
        client = JSONClient(self.app, Response)

        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'First'}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Second', 'parent': 1}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Third', 'parent': 1}))
        client.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Last'}))

        client.delete('/id/1')
        self.assertEqual(self.get('/?uri=%2Fpath%2F').status_code, 200)
        client.delete('/id/2')
        self.assertEqual(self.get('/?uri=%2Fpath%2F').status_code, 200)
        client.delete('/id/3')
        self.assertEqual(self.get('/?uri=%2Fpath%2F').status_code, 200)
        client.delete('/id/4')
        self.assertEqual(self.get('/?uri=%2Fpath%2F').status_code, 404)

    def testPathVariations(self):

        paths = ['/sub/path/', '/path.html', '/sub/path.html', 'path', '/']

        for path in paths:
            self.assertEqual(self.post('/new?' + urlencode({'uri': path}),
                             data=json.dumps({'text': '...'})).status_code, 201)

        for i, path in enumerate(paths):
            self.assertEqual(self.get('/?' + urlencode({'uri': path})).status_code, 200)
            self.assertEqual(self.get('/id/%i' % (i + 1)).status_code, 200)

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):

        mallory = JSONClient(self.app, Response)
        mallory.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Foo'}))
        mallory.delete('/id/1')

        bob = JSONClient(self.app, Response)
        bob.post('/new?uri=%2Fpath%2F', data=json.dumps({'text': 'Bar'}))

        self.assertEqual(mallory.delete('/id/1').status_code, 403)
        self.assertEqual(bob.delete('/id/1').status_code, 200)

    def testHash(self):

        a = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Aaa"}))
        b = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Bbb"}))
        c = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "Ccc", "email": "..."}))

        a = loads(a.data)
        b = loads(b.data)
        c = loads(c.data)

        self.assertNotEqual(a['hash'], '192.168.1.1')
        self.assertEqual(a['hash'], b['hash'])
        self.assertNotEqual(a['hash'], c['hash'])

    def testVisibleFields(self):

        rv = self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "...", "invalid": "field"}))
        self.assertEqual(rv.status_code, 201)

        rv = loads(rv.data)

        for key in comments.API.FIELDS:
            rv.pop(key)

        self.assertListEqual(list(rv.keys()), [])

    def testCounts(self):

        self.assertEqual(self.get('/count?uri=%2Fpath%2F').status_code, 404)
        self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), 1)

        for x in range(3):
            self.post('/new?uri=%2Fpath%2F', data=json.dumps({"text": "..."}))

        rv = self.get('/count?uri=%2Fpath%2F')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), 4)

        for x in range(4):
            self.delete('/id/%i' % (x + 1))

        rv = self.get('/count?uri=%2Fpath%2F')
        self.assertEqual(rv.status_code, 404)

    def testMultipleCounts(self):

        expected = {'a': 1, 'b': 2, 'c': 0}

        for uri, count in iteritems(expected):
            for _ in range(count):
                self.post('/new?uri=%s' % uri, data=json.dumps({"text": "..."}))

        rv = self.post('/count', data=json.dumps(list(expected.keys())))
        self.assertEqual(loads(rv.data), list(expected.values()))

    def testModify(self):
        self.post('/new?uri=test', data=json.dumps({"text": "Tpyo"}))

        self.put('/id/1', data=json.dumps({"text": "Tyop"}))
        self.assertEqual(loads(self.get('/id/1').data)["text"], "<p>Tyop</p>")

        self.put('/id/1', data=json.dumps({"text": "Typo"}))
        self.assertEqual(loads(self.get('/id/1').data)["text"], "<p>Typo</p>")

    def testDeleteCommentRemovesThread(self):

        self.client.post('/new?uri=%2F', data=json.dumps({"text": "..."}))
        self.assertIn('/', self.app.db.threads)
        self.client.delete('/id/1')
        self.assertNotIn('/', self.app.db.threads)

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


class TestModeratedComments(unittest.TestCase):

    def setUp(self):
        conf = config.load(os.path.join(dist.location, "isso", "defaults.ini"))
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.app = Isso(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def testAddComment(self):

        rv = self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.assertEqual(rv.status_code, 202)

        self.assertEqual(self.client.get('/id/1').status_code, 200)
        self.assertEqual(self.client.get('/?uri=test').status_code, 404)

        self.app.db.comments.activate(1)
        self.assertEqual(self.client.get('/?uri=test').status_code, 200)


class TestPurgeComments(unittest.TestCase):

    def setUp(self):
        conf = config.load(os.path.join(dist.location, "isso", "defaults.ini"))
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.app = Isso(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def testPurgeDoesNoHarm(self):
        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.activate(1)
        self.app.db.comments.purge(0)
        self.assertEqual(self.client.get('/?uri=test').status_code, 200)

    def testPurgeWorks(self):
        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(0)
        self.assertEqual(self.client.get('/id/1').status_code, 404)

        self.client.post('/new?uri=test', data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(3600)
        self.assertEqual(self.client.get('/id/1').status_code, 200)
