
from __future__ import unicode_literals

import os
import json
import tempfile
import unittest

from werkzeug.wrappers import Response

from isso import Isso, core
from isso.utils import http

from fixtures import curl, loads, FakeIP, JSONClient
import base
http.curl = curl


class TestVote(base.TestCase):

    def makeClient(self, ip):
        conf = core.Config.load(None)

        self.database_conf(conf)

        conf.set("guard", "enabled", "off")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, ip)

        return JSONClient(self.app, Response)

    def tearDown(self):
        self.app.db.drop()

    def testZeroLikes(self):

        rv = self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.assertEqual(loads(rv.data)['likes'], 0)
        self.assertEqual(loads(rv.data)['dislikes'], 0)

    def testSingleLike(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = self.makeClient("0.0.0.0").post("/id/1/like")

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)["likes"], 1)

    def testSelfLike(self):

        bob = self.makeClient("127.0.0.1")
        bob.post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = bob.post('/id/1/like')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)["likes"], 0)

    def testMultipleLikes(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        for num in range(15):
            rv = self.makeClient("1.2.%i.0" % num).post('/id/1/like')
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(loads(rv.data)["likes"], num + 1)

    def testVoteOnNonexistentComment(self):
        rv = self.makeClient("1.2.3.4").post('/id/1/like')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), None)

    def testTooManyLikes(self):

        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        for num in range(256):
            rv = self.makeClient("1.2.%i.0" % num).post('/id/1/like')
            self.assertEqual(rv.status_code, 200)

            if num >= 142:
                self.assertEqual(loads(rv.data)["likes"], 142)
            else:
                self.assertEqual(loads(rv.data)["likes"], num + 1)

    def testDislike(self):
        self.makeClient("127.0.0.1").post("/new?uri=test", data=json.dumps({"text": "..."}))
        rv = self.makeClient("1.2.3.4").post('/id/1/dislike')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data)['likes'], 0)
        self.assertEqual(loads(rv.data)['dislikes'], 1)
