# -*- encoding: utf-8 -*-

# Test mail format customization

from __future__ import unicode_literals

import unittest
import os
import json
import tempfile

from werkzeug.wrappers import Response
from isso import Isso, core, config, local, dist
from isso.utils import http
from fixtures import curl, loads, FakeIP, JSONClient
from isso.ext.notifications import SMTP
http.curl = curl


class TestMail(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(os.path.join(dist.location, "share", "isso.conf"))
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        self.conf = conf

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete
        self.public_endpoint = conf.get("server", "public-endpoint") or local("host")

        self.smtp = SMTP(self.app)

    def tearDown(self):
        os.unlink(self.path)

    def testSubject_default(self):
        """Test subject default parsing"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous", }))
        rv_1 = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        rv_2 = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is also a sub-class comment",
                 "parent": 1}))
        pa = loads(pa.data)
        rv_1 = loads(rv_1.data)
        rv_2 = loads(rv_2.data)

        self.assertEqual(self.smtp.notify_subject(thread_test, rv_1, pa, pa), "Re: New comment posted on %s" % thread_test["title"])
        self.assertEqual(self.smtp.notify_subject(thread_test, rv_2, pa, rv_1), "Re: New comment posted on %s" % thread_test["title"])
        self.assertEqual(self.smtp.notify_subject(thread_test, pa, admin=True), thread_test["title"])

    def testSubject_customization(self):
        """Test subject customization parsing"""
        self.conf.set("mail", "subject_admin", "{replier} commented on your post {title}")
        self.conf.set("mail", "subject_user_new_comment", "{receiver}, {replier} replied to {repliee}'s comment on the post {title}")
        self.conf.set("mail", "subject_user_reply", "{replier} replied to your comment on the post {title}")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous", }))
        rv_1 = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        rv_2 = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is also a sub-class comment",
                 "parent": 1}))
        pa = loads(pa.data)
        rv_1 = loads(rv_1.data)
        rv_2 = loads(rv_2.data)

        self.assertEqual(self.smtp.notify_subject(thread_test, rv_1, pa, pa), "Sim replied to your comment on the post Hello isso!")
        self.assertEqual(self.smtp.notify_subject(thread_test, rv_2, pa, rv_1), "Sim, Anonymous replied to Anonymous's comment on the post Hello isso!")
        self.assertEqual(self.smtp.notify_subject(thread_test, pa, admin=True), "Anonymous commented on your post Hello isso!")
