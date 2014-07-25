# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import time
import unittest

from isso import db

from isso.models import Thread
from isso.controllers import comments

IP = "127.0.0.1"
TH = Thread(1, "/")


class TestValidator(unittest.TestCase):

    def test_validator(self):

        default = dict(zip(["parent", "text", "author", "email", "website"], [None]*5))
        new = lambda **z: dict(default, **z)
        verify = lambda data: comments.Validator.verify(data)[0]

        # invalid types
        self.assertFalse(verify(new(text=None)))
        self.assertFalse(verify(new(parent="xxx")))
        for key in ("author", "website", "email"):
            self.assertFalse(verify(new(text="...", **{key: 3.14})))

        # text too short and/or blank
        for text in ("", "\n\n\n"):
            self.assertFalse(verify(new(text=text)))

        # email/website length
        self.assertTrue(verify(new(text="...", email="*"*254)))
        self.assertTrue(verify(new(text="...", website="google.de/" + "a"*128)))

        self.assertFalse(verify(new(text="...", email="*"*1024)))
        self.assertFalse(verify(new(text="...", website="google.de/" + "*"*1024)))

        # invalid url
        self.assertFalse(verify(new(text="...", website="spam")))

    def test_isurl(self):
        isurl = comments.Validator.isurl

        # valid website url
        self.assertTrue(isurl("example.tld"))
        self.assertTrue(isurl("http://example.tld"))
        self.assertTrue(isurl("https://example.tld"))
        self.assertTrue(isurl("https://example.tld:1337/"))
        self.assertTrue(isurl("https://example.tld:1337/foobar"))
        self.assertTrue(isurl("https://example.tld:1337/foobar?p=1#isso-thread"))

        self.assertFalse(isurl("ftp://example.tld/"))
        self.assertFalse(isurl("tel:+1234567890"))
        self.assertFalse(isurl("+1234567890"))
        self.assertFalse(isurl("spam"))


class TestController(unittest.TestCase):

    def setUp(self):
        self.controller = comments.Controller(db.Adapter("sqlite:///:memory:"))

    def test_new(self):
        obj = self.controller.new(IP, TH, dict(text="Здравствуй, мир!"))

        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.text, "Здравствуй, мир!")
        self.assertLess(obj.created, time.time())
        self.assertIn(IP, obj.voters)
        self.assertFalse(obj.moderated)
        self.assertFalse(obj.deleted)

        sec = self.controller.new(IP, TH, dict(text="Ohai"), moderated=True)
        self.assertEqual(sec.id, 2)
        self.assertEqual(sec.text, "Ohai")
        self.assertTrue(sec.moderated)
        self.assertFalse(sec.deleted)

        self.assertRaises(comments.Invalid, self.controller.new, IP, TH, dict())

    def test_create_invalid_parent(self):
        a = self.controller.new(IP, TH, dict(text="..."))
        b = self.controller.new(IP, TH, dict(text="...", parent=a.id))
        c = self.controller.new(IP, TH, dict(text="...", parent=b.id))

        # automatic insertion to a maximum nesting level of 1
        self.assertEqual(c.parent, b.parent)

        # remove invalid reference
        d = self.controller.new(IP, TH, dict(text="...", parent=42))
        self.assertIsNone(d.parent)

    def test_edit(self):
        a = self.controller.new(IP, TH, dict(text="Hello!"))
        z = self.controller.new(IP, TH, dict(text="Dummy"))

        a = self.controller.edit(a.id, dict(
            text="Hello, World!", author="Hans", email="123", website="http://example.tld/"))
        b = self.controller.get(a.id)

        self.assertEqual(a.text, "Hello, World!")
        self.assertEqual(a.author, "Hans")
        self.assertEqual(a.email, "123")
        self.assertEqual(a.website, "http://example.tld/")

        for attr in ("text", "author", "email", "website"):
            self.assertEqual(getattr(a, attr), getattr(b, attr))

        self.assertEqual(self.controller.get(z.id).text, z.text)

        # edit invalid data
        self.assertRaises(comments.Invalid, self.controller.edit, a.id, dict(text=""))

        # edit invalid comment
        self.assertIsNone(self.controller.edit(23, dict(text="...")))

    def test_get(self):
        obj = self.controller.get(23)
        self.assertIsNone(obj)

        self.controller.new(IP, TH, dict(text="..."))
        obj = self.controller.get(1)

        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.thread, 1)

    def test_all(self):
        foo, bar = Thread(0, "/foo"), Thread(1, "/bar")
        args = ("One", "Two", "three")

        for text in args:
            self.controller.new(IP, foo, dict(text=text))

        # control group
        self.controller.new(IP, bar, dict(text="..."))

        rv = self.controller.all(foo)
        self.assertEqual(len(rv), 3)

        for text, obj in zip(args, rv):
            self.assertEqual(text, obj.text)

    def test_delete(self):
        for _ in range(3):
            self.controller.new(IP, TH, dict(text="..."))

        for n in range(3):
            self.controller.delete(n + 1)
            self.assertIsNone(self.controller.get(n+1))

        # delete invalid comment
        self.assertIsNone(self.controller.delete(23))

    def test_delete_nested(self):
        p = self.controller.new(IP, TH, dict(text="parent"))
        c1 = self.controller.new(IP, TH, dict(text="child", parent=p.id))
        c2 = self.controller.new(IP, TH, dict(text="child", parent=p.id))

        self.controller.delete(p.id)
        p = self.controller.get(p.id)

        self.assertIsNotNone(p)
        self.assertTrue(p.deleted)
        self.assertEqual(p.text, "")

        self.controller.delete(c1.id)

        self.assertIsNone(self.controller.get(c1.id))
        self.assertIsNotNone(self.controller.get(c2.id))
        self.assertIsNotNone(self.controller.get(p.id))

        self.controller.delete(c2.id)
        self.assertIsNone(self.controller.get(p.id))

    def test_empty(self):
        self.assertTrue(self.controller.empty())
        self.controller.new(IP, TH, dict(text="..."))
        self.assertFalse(self.controller.empty())

    def test_count(self):
        threads = [Thread(0, "a"), None, Thread(1, "c")]
        counter = [1, 0, 2]

        self.assertEqual(self.controller.count(*threads), [0, 0, 0])

        for thread, count in zip(threads, counter):
            if thread is None:
                continue
            for _ in range(count):
                self.controller.new(IP, thread, dict(text="..."))

        self.assertEqual(self.controller.count(*threads), counter)

    def test_votes(self):
        author = "127.0.0.1"
        foo, bar = "1.2.3.4", "1.3.3.7"

        c = self.controller.new(author, TH, dict(text="..."))
        self.assertEqual(c.likes, 0)
        self.assertEqual(c.dislikes, 0)

        # author can not vote on own comment
        self.assertFalse(self.controller.like(author, c.id))

        # but others can (at least once)
        self.assertTrue(self.controller.like(foo, c.id))
        self.assertTrue(self.controller.dislike(bar, c.id))

        self.assertFalse(self.controller.like(foo, c.id))
        self.assertFalse(self.controller.like(bar, c.id))

        c = self.controller.get(c.id)
        self.assertEqual(c.likes, 1)
        self.assertEqual(c.dislikes, 1)

        # vote a non-existent comment
        self.assertFalse(self.controller.like(foo, 23))

    def test_activation(self):
        c = self.controller.new(IP, TH, dict(text="..."), moderated=True)
        self.assertEqual(len(self.controller.all(TH)), 0)

        self.assertTrue(self.controller.activate(c.id))
        self.assertFalse(self.controller.activate(c.id))
        self.assertEqual(len(self.controller.all(TH)), 1)

        # invalid comment returns False
        self.assertFalse(self.controller.activate(23))

    def test_prune(self):

        c = self.controller.new(IP, TH, dict(text="..."), moderated=True)
        self.assertEqual(self.controller.prune(42), 0)
        self.assertIsNotNone(self.controller.get(c.id))

        self.assertEqual(self.controller.prune(0), 1)
        self.assertIsNone(self.controller.get(c.id))
