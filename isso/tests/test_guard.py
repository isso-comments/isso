# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import json
import tempfile

from werkzeug import __version__
from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso, config, core, dist
from isso.utils import http

from fixtures import curl, FakeIP
http.curl = curl

if __version__.startswith("0.8"):
    class Response(Response):

        def get_data(self, as_text=False):
            return self.data.decode("utf-8")


class TestGuard(unittest.TestCase):

    data = json.dumps({"text": "Lorem ipsum."})

    def setUp(self):
        self.path = tempfile.NamedTemporaryFile().name

    def makeClient(self, ip, ratelimit=2, direct_reply=3, self_reply=False,
                   require_email=False, require_author=False):

        conf = config.load(os.path.join(dist.location, "share", "isso.conf"))
        conf.set("general", "dbpath", self.path)
        conf.set("hash", "algorithm", "none")
        conf.set("guard", "enabled", "true")
        conf.set("guard", "ratelimit", str(ratelimit))
        conf.set("guard", "direct-reply", str(direct_reply))
        conf.set("guard", "reply-to-self", "1" if self_reply else "0")
        conf.set("guard", "require-email", "1" if require_email else "0")
        conf.set("guard", "require-author", "1" if require_author else "0")

        class App(Isso, core.Mixin):
            pass

        app = App(conf)

        app.wsgi_app = FakeIP(app.wsgi_app, ip)

        return Client(app, Response)

    def testRateLimit(self):

        bob = self.makeClient("127.0.0.1", 2)

        for i in range(2):
            rv = bob.post('/new?uri=test', data=self.data)
            self.assertEqual(rv.status_code, 201)

        rv = bob.post('/new?uri=test', data=self.data)

        self.assertEqual(rv.status_code, 403)
        self.assertIn("ratelimit exceeded", rv.get_data(as_text=True))

        alice = self.makeClient("1.2.3.4", 2)
        for i in range(2):
            self.assertEqual(alice.post(
                "/new?uri=test", data=self.data).status_code, 201)

        bob.application.db.execute([
            "UPDATE comments SET",
            "    created = created - 60",
            "WHERE remote_addr = '127.0.0.0'"
        ])

        self.assertEqual(
            bob.post("/new?uri=test", data=self.data).status_code, 201)

    def testDirectReply(self):

        client = self.makeClient("127.0.0.1", 15, 3)

        for url in ("foo", "bar", "baz", "spam"):
            for _ in range(3):
                rv = client.post("/new?uri=%s" % url, data=self.data)
                self.assertEqual(rv.status_code, 201)

        for url in ("foo", "bar", "baz", "spam"):
            rv = client.post("/new?uri=%s" % url, data=self.data)

            self.assertEqual(rv.status_code, 403)
            self.assertIn("direct responses to", rv.get_data(as_text=True))

    def testSelfReply(self):

        def payload(id):
            return json.dumps({"text": "...", "parent": id})

        client = self.makeClient("127.0.0.1", self_reply=False)
        self.assertEqual(client.post(
            "/new?uri=test", data=self.data).status_code, 201)
        self.assertEqual(client.post(
            "/new?uri=test", data=payload(1)).status_code, 403)

        client.application.db.execute([
            "UPDATE comments SET",
            "    created = created - ?",
            "WHERE id = 1"
        ], (client.application.conf.getint("general", "max-age"), ))

        self.assertEqual(client.post(
            "/new?uri=test", data=payload(1)).status_code, 201)

        client = self.makeClient("128.0.0.1", ratelimit=3, self_reply=False)
        self.assertEqual(client.post(
            "/new?uri=test", data=self.data).status_code, 201)
        self.assertEqual(client.post(
            "/new?uri=test", data=payload(1)).status_code, 201)
        self.assertEqual(client.post(
            "/new?uri=test", data=payload(2)).status_code, 201)

    def testRequireEmail(self):

        def payload(email):
            return json.dumps({"text": "...", "email": email})

        client = self.makeClient("127.0.0.1", ratelimit=4, require_email=False)
        client_strict = self.makeClient(
            "127.0.0.2", ratelimit=4, require_email=True)

        # if we don't require email
        self.assertEqual(client.post(
            "/new?uri=test", data=payload("")).status_code, 201)
        self.assertEqual(client.post(
            "/new?uri=test", data=payload("test@me.more")).status_code, 201)

        # if we do require email
        self.assertEqual(client_strict.post(
            "/new?uri=test", data=payload("")).status_code, 403)
        self.assertEqual(client_strict.post(
            "/new?uri=test", data=payload("test@me.more")).status_code, 201)

    def testRequireAuthor(self):

        def payload(author):
            return json.dumps({"text": "...", "author": author})

        client = self.makeClient(
            "127.0.0.1", ratelimit=4, require_author=False)
        client_strict = self.makeClient(
            "127.0.0.2", ratelimit=4, require_author=True)

        # if we don't require author
        self.assertEqual(client.post(
            "/new?uri=test", data=payload("")).status_code, 201)
        self.assertEqual(client.post(
            "/new?uri=test", data=payload("pipo author")).status_code, 201)

        # if we do require author
        self.assertEqual(client_strict.post(
            "/new?uri=test", data=payload("")).status_code, 403)
        self.assertEqual(client_strict.post(
            "/new?uri=test", data=payload("pipo author")).status_code, 201)
