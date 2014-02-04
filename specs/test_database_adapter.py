# -*- encoding: utf-8 -*-

from isso.core import Config
from isso.db import Adapter

import base
import time

class TestDatabaseAdapter(base.TestCase):
    def setUp(self):
        super(base.TestCase, self).setUp()
        self.db = Adapter(self.database_uri(), Config.load(None))

    # HELPERS

    def thread_count(self):
        return self.db.execute('SELECT COUNT(id) FROM threads').fetchone()[0]

    def comments_count(self):
        return self.db.execute('SELECT COUNT(id) FROM comments').fetchone()[0]

    # TESTS

    def test_init(self):
        # TODO: Test table creation
        pass

    def test_threads_new(self):
        # Preconditions
        self.assertEqual(0, self.thread_count())

        # Operation
        self.db.threads.new('/path', 'Title')

        # Postconditions
        self.assertEqual(1, self.thread_count())
        self.assertEqual('/path', self.db.execute('SELECT uri FROM threads').fetchone()[0])
        self.assertEqual('Title', self.db.execute('SELECT title FROM threads').fetchone()[0])

    def test_threads_getitem(self):
        # Preconditions
        self.db.execute(self.db.threads.table.insert().values(uri='/path', title='Title'))
        self.assertEqual(1, self.thread_count())

        # Operation
        thread = self.db.threads['/path']

        # Postconditions
        self.assertEqual("/path", thread['uri'])
        self.assertEqual("Title", thread['title'])

    def test_comments_add(self):
        # Preconditions
        self.assertEqual(0, self.comments_count())
        self.db.threads.new('/path', 'Title')
        local_time = time.time()

        # Operation
        self.db.comments.add('/path', {'text': 'Text', 'mode': 1, 'remote_addr': '127.0.0.1',
                                       'author': 'John', 'website': 'https://google.com',
                                       'parent': 1, 'created': local_time})

        # Postconditions
        res = self.db.execute('SELECT author, website, mode, remote_addr, parent, ' +
                              'created, uri FROM comments JOIN threads ON ' +
                              'comments.tid = threads.id').fetchone()
        self.assertEqual(
            ('John', 'https://google.com', 1, '127.0.0.1', 1, local_time, '/path'),
            res
        )

    def test_comments_count(self):
        # Preconditions
        self.db.threads.new('/path', 'Title')
        self.db.comments.add('/path', {'text': 'Text', 'mode': 1, 'remote_addr': '127.0.0.1'})
        self.db.comments.add('/path', {'text': 'Text 2', 'mode': 1, 'remote_addr': '127.0.0.1'})

        # Operations
        count = self.db.comments.count('/path')

        # Postconditions
        self.assertEqual(2, count)

class TestDatabaseAdapterPg(TestDatabaseAdapter):
    def database_type(self):
        return 'postgresql'


class TestDatabaseAdapterMy(TestDatabaseAdapter):
    def database_type(self):
        return 'mysql'
