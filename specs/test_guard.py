# -*- encoding: utf-8 -*-

import unittest

import os
import json
import tempfile

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso, core
from isso.utils import http

from fixtures import curl, FakeIP
http.curl = curl


class TestGuard(unittest.TestCase):

    data = json.dumps({"text": "Lorem ipsum."})

    def setUp(self):
        self.path = tempfile.NamedTemporaryFile().name

    def makeClient(self, ip, ratelimit=2, direct_reply=3):

        conf = core.Config.load(None)
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "true")
        conf.set("guard", "ratelimit", str(ratelimit))
        conf.set("guard", "direct-reply", str(direct_reply))

        class App(Isso, core.Mixin):
            pass

        app = App(conf)
        app.wsgi_app = FakeIP(app.wsgi_app, ip)

        return Client(app, Response)

    def testRateLimit(self):

        bob = self.makeClient("127.0.0.1", 2)

        for i in range(2):
            rv = bob.post('/new?uri=test', data=self.data)
            assert rv.status_code == 201

        rv = bob.post('/new?uri=test', data=self.data)

        assert rv.status_code == 403
        assert "ratelimit exceeded" in rv.data

        alice = self.makeClient("1.2.3.4", 2)
        for i in range(2):
            assert alice.post("/new?uri=test", data=self.data).status_code == 201

        bob.application.db.execute([
            "UPDATE comments SET",
            "    created = created - 60",
            "WHERE remote_addr = '127.0.0.0'"
        ])

        assert bob.post("/new?uri=test", data=self.data).status_code == 201

    def testDirectReply(self):

        client = self.makeClient("127.0.0.1", 15, 3)

        for url in ("foo", "bar", "baz", "spam"):
            for _ in range(3):
                rv = client.post("/new?uri=%s" % url, data=self.data)
                assert rv.status_code == 201

        for url in ("foo", "bar", "baz", "spam"):
            rv = client.post("/new?uri=%s" % url, data=self.data)

            assert rv.status_code == 403
            assert "direct responses to" in rv.data
