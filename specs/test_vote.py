
import os
import json
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso


class FakeIP(object):

    def __init__(self, app, ip):
        self.app = app
        self.ip = ip

    def __call__(self, environ, start_response):
        environ['REMOTE_ADDR'] = self.ip
        return self.app(environ, start_response)


class TestVote(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def makeClient(self, ip):

        app = Isso(self.path, '...', '...', 15*60, "...")
        app.wsgi_app = FakeIP(app.wsgi_app, ip)

        return Client(app, Response)

    def testZeroLikes(self):

        rv = self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        assert json.loads(rv.data)['votes'] == 0

    def testSingleLike(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = self.makeClient("0.0.0.0").post("/like?uri=test&id=1")

        assert rv.status_code == 200
        assert rv.data == "1"

    def testSelfLike(self):

        bob = self.makeClient("127.0.0.1")
        bob.post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = bob.post('/like?uri=test&id=1')

        assert rv.status_code == 200
        assert rv.data == "0"

    def testMultipleLikes(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        for num in range(15):
            rv = self.makeClient("1.2.3.%i" % num).post('/like?uri=test&id=1')
            assert rv.status_code == 200
            assert rv.data == str(num + 1)

    def testTooManyLikes(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        for num in range(256):
            rv = self.makeClient("1.2.3.%i" % num).post('/like?uri=test&id=1')
            assert rv.status_code == 200

            if num >= 142:
                assert rv.data == "142"
            else:
                assert rv.data == str(num + 1)

