# -*- encoding: utf-8 -*-

import json
import tempfile
import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso import Isso, config, core
from isso.utils import http

from fixtures import curl, FakeIP

http.curl = curl


class TestGuard(unittest.TestCase):
    data = json.dumps({"text": "Lorem ipsum."})

    def setUp(self):
        self.path = tempfile.NamedTemporaryFile().name

    def makeClient(
        self, ip, ratelimit=2, direct_reply=3, self_reply=False, require_email=False, require_author=False, moderation=False
    ):
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("hash", "algorithm", "none")
        conf.set("guard", "enabled", "true")
        conf.set("guard", "ratelimit", str(ratelimit))
        conf.set("guard", "direct-reply", str(direct_reply))
        conf.set("guard", "reply-to-self", "1" if self_reply else "0")
        conf.set("guard", "require-email", "1" if require_email else "0")
        conf.set("guard", "require-author", "1" if require_author else "0")
        conf.set("moderation", "enabled", "1" if moderation else "0")

        class App(Isso, core.Mixin):
            pass

        app = App(conf)

        app.wsgi_app = FakeIP(app.wsgi_app, ip)

        return Client(app, Response)

    def testRateLimit(self):
        bob = self.makeClient("127.0.0.1", 2)

        for i in range(2):
            rv = bob.post("/new?uri=test", data=self.data)
            self.assertEqual(rv.status_code, 201)

        rv = bob.post("/new?uri=test", data=self.data)

        self.assertEqual(rv.status_code, 403)
        self.assertEqual(json.loads(rv.data)["reason"], "ratelimit")

        alice = self.makeClient("1.2.3.4", 2)
        for i in range(2):
            self.assertEqual(alice.post("/new?uri=test", data=self.data).status_code, 201)

        bob.application.db.execute(["UPDATE comments SET", "    created = created - 60", "WHERE remote_addr = '127.0.0.0'"])

        self.assertEqual(bob.post("/new?uri=test", data=self.data).status_code, 201)

    def testDirectReply(self):
        client = self.makeClient("127.0.0.1", 15, 3)

        for url in ("foo", "bar", "baz", "spam"):
            for _ in range(3):
                rv = client.post("/new?uri=%s" % url, data=self.data)
                self.assertEqual(rv.status_code, 201)

        for url in ("foo", "bar", "baz", "spam"):
            rv = client.post("/new?uri=%s" % url, data=self.data)

            self.assertEqual(rv.status_code, 403)
            self.assertEqual(json.loads(rv.data)["reason"], "direct-reply")

    def testSelfReply(self):
        def payload(id):
            return json.dumps({"text": "...", "parent": id})

        client = self.makeClient("127.0.0.1", self_reply=False)
        self.assertEqual(client.post("/new?uri=test", data=self.data).status_code, 201)
        rv = client.post("/new?uri=test", data=payload(1))
        self.assertEqual(rv.status_code, 403)
        self.assertEqual(json.loads(rv.data)["reason"], "reply-to-self")

        client.application.db.execute(
            ["UPDATE comments SET", "    created = created - ?", "WHERE id = 1"],
            (client.application.conf.getint("general", "max-age"),),
        )

        self.assertEqual(client.post("/new?uri=test", data=payload(1)).status_code, 201)

        client = self.makeClient("128.0.0.1", ratelimit=3, self_reply=False)
        self.assertEqual(client.post("/new?uri=test", data=self.data).status_code, 201)
        self.assertEqual(client.post("/new?uri=test", data=payload(1)).status_code, 201)
        self.assertEqual(client.post("/new?uri=test", data=payload(2)).status_code, 201)

    def testSelfReplyAfterOtherReply(self):
        def payload(id):
            return json.dumps({"text": "...", "parent": id})

        alice = self.makeClient("127.0.0.1", ratelimit=5, self_reply=False)
        bob = self.makeClient("128.0.0.1", ratelimit=5, self_reply=False)

        # alice starts the (still editable) thread
        self.assertEqual(alice.post("/new?uri=test", data=self.data).status_code, 201)

        # replying to her own fresh comment is still blocked
        self.assertEqual(alice.post("/new?uri=test", data=payload(1)).status_code, 403)

        # bob replies to alice
        self.assertEqual(bob.post("/new?uri=test", data=payload(1)).status_code, 201)

        # now alice may reply again: it is a conversation, not self-padding
        self.assertEqual(alice.post("/new?uri=test", data=payload(1)).status_code, 201)

        # but a second consecutive self-reply is blocked again: alice's own reply
        # is now the most recent one, so the gate is closed until bob replies once
        # more
        self.assertEqual(alice.post("/new?uri=test", data=payload(1)).status_code, 403)

        # bob replies again, unlocking exactly one more self-reply for alice
        self.assertEqual(bob.post("/new?uri=test", data=payload(1)).status_code, 201)
        self.assertEqual(alice.post("/new?uri=test", data=payload(1)).status_code, 201)

    def testSelfReplyAfterModeratedOtherReply(self):
        def payload(id):
            return json.dumps({"text": "...", "parent": id})

        alice = self.makeClient("127.0.0.1", ratelimit=5, self_reply=False, moderation=True)
        bob = self.makeClient("128.0.0.1", ratelimit=5, self_reply=False, moderation=True)

        # alice starts the (still editable) thread
        self.assertEqual(alice.post("/new?uri=test", data=self.data).status_code, 202)

        # bob replies to alice, but it lands in the moderation queue (mode 2)
        self.assertEqual(bob.post("/new?uri=test", data=payload(1)).status_code, 202)

        # a pending foreign reply must not open the reply-to-self gate
        self.assertEqual(alice.post("/new?uri=test", data=payload(1)).status_code, 403)

    def testRequireEmail(self):
        def payload(email):
            return json.dumps({"text": "...", "email": email})

        client = self.makeClient("127.0.0.1", ratelimit=4, require_email=False)
        client_strict = self.makeClient("127.0.0.2", ratelimit=4, require_email=True)

        # if we don't require email
        self.assertEqual(client.post("/new?uri=test", data=payload("")).status_code, 201)
        self.assertEqual(client.post("/new?uri=test", data=payload("test@me.more")).status_code, 201)

        # if we do require email
        rv = client_strict.post("/new?uri=test", data=payload(""))
        self.assertEqual(rv.status_code, 403)
        self.assertEqual(json.loads(rv.data)["reason"], "require-email")
        self.assertEqual(client_strict.post("/new?uri=test", data=payload("test@me.more")).status_code, 201)

    def testRequireAuthor(self):
        def payload(author):
            return json.dumps({"text": "...", "author": author})

        client = self.makeClient("127.0.0.1", ratelimit=4, require_author=False)
        client_strict = self.makeClient("127.0.0.2", ratelimit=4, require_author=True)

        # if we don't require author
        self.assertEqual(client.post("/new?uri=test", data=payload("")).status_code, 201)
        self.assertEqual(client.post("/new?uri=test", data=payload("pipo author")).status_code, 201)

        # if we do require author
        rv = client_strict.post("/new?uri=test", data=payload(""))
        self.assertEqual(rv.status_code, 403)
        self.assertEqual(json.loads(rv.data)["reason"], "require-author")
        self.assertEqual(client_strict.post("/new?uri=test", data=payload("pipo author")).status_code, 201)
