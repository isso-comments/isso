# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso import db, spam
from isso.models import Thread
from isso.controllers import comments

bob = "127.0.0.1"
alice = "127.0.0.2"

comment = dict(text="...")


class TestGuard(unittest.TestCase):

    def setUp(self):
        self.db = db.Adapter("sqlite:///:memory:")

    def test_ratelimit(self):
        thread = Thread(0, "/")

        guard = spam.Guard(self.db, enabled=True, ratelimit=2)
        controller = comments.Controller(self.db, guard)

        for _ in range(2):
            controller.new(bob, thread, comment)

        try:
            controller.new(bob, thread, comment)
        except Exception as ex:
            self.assertIsInstance(ex, comments.Denied)
            self.assertIn("ratelimit exceeded", ex.message)
        else:
            self.assertTrue(False)

        # check if Alice can still comment
        for _ in range(2):
            controller.new(alice, thread, comment)

        # 60 seconds are gone now
        self.db.engine.execute(
            self.db.comments.update().values(
                created=self.db.comments.c.created - 60
            ).where(self.db.comments.c.remote_addr == bob))

        controller.new(bob, thread, comment)

    def test_direct_reply(self):
        threads = [Thread(0, "/foo"), Thread(1, "/bar")]

        guard = spam.Guard(self.db, enabled=True, ratelimit=-1, direct_reply=3)
        controller = comments.Controller(self.db, guard)

        for thread in threads:
            for _ in range(3):
                controller.new(bob, thread, comment)

        for thread in threads:
            try:
                controller.new(bob, thread, comment)
            except Exception as ex:
                self.assertIsInstance(ex, comments.Denied)
                self.assertIn("direct response", ex.message)
            else:
                self.assertTrue(False)

    def test_self_reply(self):
        thread = Thread(0, "/")

        guard = spam.Guard(self.db, enabled=True, reply_to_self=False)
        controller = comments.Controller(self.db, guard)

        ref = controller.new(bob, thread, comment).id

        try:
            controller.new(bob, thread, dict(text="...", parent=ref))
        except Exception as ex:
            self.assertIsInstance(ex, comments.Denied)
            self.assertIn("editing frame is still open", ex.message)
        else:
            self.assertTrue(False)

        # fast-forward `max-age` seconds
        self.db.engine.execute(
            self.db.comments.update().values(
                created=self.db.comments.c.created - guard.max_age
            ).where(self.db.comments.c.id == ref))

        controller.new(bob, thread, dict(text="...", parent=ref))
