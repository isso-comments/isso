
import os
import json
import time
import tempfile
import unittest

from isso.models import Comment
from isso.db import SQLite


def comment(**kw):
    return Comment.fromjson(json.dumps(kw))


class TestSQLite(unittest.TestCase):

    def setUp(self):

        fd, self.path = tempfile.mkstemp()
        self.db = SQLite()
        self.db.initialize({'SQLITE': self.path})

    def test_get(self):

        rv = self.db.add('/', comment(text='Spam'))
        c = self.db.get(*rv)

        assert c.id == 1
        assert c.text == 'Spam'

    def test_add(self):

        x = self.db.add('/', comment(text='Foo'))
        self.db.add('/', comment(text='Bar'))
        self.db.add('/path/', comment(text='Baz'))

        rv = list(self.db.retrieve('/'))
        assert rv[0].id == 2
        assert rv[0].text == 'Bar'

        assert rv[1].id == 1
        assert rv[1].text == 'Foo'

        rv = list(self.db.retrieve('/path/'))
        assert rv[0].id == 1
        assert rv[0].text == 'Baz'

    def test_update(self):

        path, id = self.db.add('/', comment(text='Foo'))
        time.sleep(0.1)
        path, id = self.db.update(path, id, comment(text='Bla'))
        c = self.db.get(path, id)

        assert c.id == 1
        assert c.text == 'Foo'
        assert c.created < c.modified

    def test_delete(self):

        path, id = self.db.add('/', comment(
            text='F**CK', author='P*NIS', website='http://somebadhost.org/'))

        self.db.delete(path, id)
        c = self.db.get(path, id)

        assert c.id == 1
        assert c.text == ''
        assert c.author is None
        assert c.website is None

    def tearDown(self):
        os.unlink(self.path)
