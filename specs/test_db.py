
import os
import json
import tempfile
import unittest

from isso.comments import Comment
from isso.db import SQLite


def comment(**kw):
    return Comment.fromjson(json.dumps(kw))


class TestSQLite(unittest.TestCase):

    def setUp(self):

        fd, self.path = tempfile.mkstemp()
        self.db = SQLite()
        self.db.initialize({'SQLITE': self.path})

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

    def tearDown(self):
        os.unlink(self.path)
