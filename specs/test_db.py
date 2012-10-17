
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
        self.db = SQLite({'SQLITE': self.path})

    def test_get(self):

        rv = self.db.add('/', comment(text='Spam'))
        c = self.db.get('/', rv.id)

        assert c.id == 1
        assert c.text == 'Spam'

    def test_add(self):

        self.db.add('/', comment(text='Foo'))
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

        rv = self.db.add('/', comment(text='Foo'))
        time.sleep(0.1)
        rv = self.db.update('/', rv.id, comment(text='Bla'))
        c = self.db.get('/', rv.id)

        assert c.id == 1
        assert c.text == 'Bla'
        assert c.created < c.modified

    def test_delete(self):

        rv = self.db.add('/', comment(
            text='F**CK', author='P*NIS', website='http://somebadhost.org/'))

        self.db.delete('/', rv.id)
        c = self.db.get('/', rv.id)

        assert c.id == 1
        assert c.text == ''
        assert c.author is None
        assert c.website is None

    def tearDown(self):
        os.unlink(self.path)
