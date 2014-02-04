# -*- encoding: utf-8 -*-

import os
from os.path import join, dirname
from isso.core import Config
from isso.db import Adapter
from isso.migrate import disqus
import base

class TestMigration(base.TestCase):
    def database_uri(self):
        env = os.getenv('DB', 'sqlite')
        if env == 'sqlite':
            return 'sqlite:///:memory:'
        elif env == 'postgresql':
            return 'postgresql:///isso-test'
        elif env == 'mysql':
            return 'mysql:///isso-test'

    def setUp(self):
        self.db = Adapter(self.database_uri(), Config.load(None))
        self.xml = join(dirname(__file__), "disqus.xml")

    def test_disqus(self):
        disqus(self.db, self.xml)

        assert self.db.threads["/"]["title"] == "Hello, World!"
        assert self.db.threads["/"]["id"] == 1

        a = self.db.comments.get(1)

        assert a["author"] == "peter"
        assert a["email"] == "foo@bar.com"

        b = self.db.comments.get(2)
        assert b["parent"] == a["id"]
