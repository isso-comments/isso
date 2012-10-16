
import shutil
import tempfile
import unittest

from isso.comments import Comment
from isso.db import SQLite


class TestSQLite(unittest.TestCase):

    def setUp(self):

        self.path = tempfile.mkdtemp()
        self.db = SQLite()
        self.db.initialize({'DATA_DIR': self.path})

    def test_add(self):

        self.db.add('/', Comment(text='Foo'))
        self.db.add('/', Comment(text='Bar'))
        self.db.add('/path/', Comment(text='Baz'))

        rv = list(self.db.retrieve('/'))
        assert rv[0].id == 2
        assert rv[0].text == 'Bar'

        assert rv[1].id == 1
        assert rv[1].text == 'Foo'

        rv = list(self.db.retrieve('/path/'))
        assert rv[0].id == 1
        assert rv[0].text == 'Baz'

    def tearDown(self):
        shutil.rmtree(self.path)
