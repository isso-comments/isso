
import os
import time
import tempfile
import unittest

from isso.models import Comment
from isso.db import SQLite


class TestSQLite(unittest.TestCase):

    def setUp(self):

        fd, self.path = tempfile.mkstemp()
        self.db = SQLite(self.path, False)

    def test_get(self):

        rv = self.db.add('/', Comment(text='Spam'), '')
        c = self.db.get('/', rv["id"])

        assert c["id"] == 1
        assert c["text"] == 'Spam'

    def test_add(self):

        self.db.add('/', Comment(text='Foo'), '')
        self.db.add('/', Comment(text='Bar'), '')
        self.db.add('/path/', Comment(text='Baz'), '')

        rv = list(self.db.retrieve('/'))
        assert rv[0]["id"] == 1
        assert rv[0]["text"] == 'Foo'

        assert rv[1]["id"] == 2
        assert rv[1]["text"] == 'Bar'

        rv = list(self.db.retrieve('/path/'))
        assert rv[0]["id"] == 1
        assert rv[0]["text"] == 'Baz'

    def test_add_return(self):

        self.db.add('/', Comment(text='1'), '')
        self.db.add('/', Comment(text='2'), '')

        assert self.db.add('/path/', Comment(text='1'), '')["id"] == 1

    def test_update(self):

        rv = self.db.add('/', Comment(text='Foo'), '')
        time.sleep(0.1)
        rv = self.db.update('/', rv["id"], {"text": "Bla"})
        c = self.db.get('/', rv["id"])

        assert c["id"] == 1
        assert c["text"] == 'Bla'
        assert c["created"] < c["modified"]

    def test_delete(self):

        rv = self.db.add('/', Comment(
            text='F**CK', author='P*NIS', website='http://somebadhost.org/'), '')
        assert self.db.delete('/', rv["id"]) == None

    def test_recent(self):

        self.db.add('/path/', Comment(text='2'), '')

        for x in range(5):
            self.db.add('/', Comment(text='%i' % (x+1)), '')

        assert len(list(self.db.recent(mode=7))) == 6
        assert len(list(self.db.recent(mode=7, limit=5))) == 5

    def tearDown(self):
        os.unlink(self.path)


class TestSQLitePending(unittest.TestCase):

    def setUp(self):

        fd, self.path = tempfile.mkstemp()
        self.db = SQLite(self.path, True)

    def test_retrieve(self):

        self.db.add('/', Comment(text='Foo'), '')
        assert len(list(self.db.retrieve('/'))) == 0

    def test_activate(self):

        self.db.add('/', Comment(text='Foo'), '')
        self.db.add('/', Comment(text='Bar'), '')
        self.db.activate('/', 2)

        assert len(list(self.db.retrieve('/'))) == 1
        assert len(list(self.db.retrieve('/', mode=3))) == 2

    def tearDown(self):
        os.unlink(self.path)
