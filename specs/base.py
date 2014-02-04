# -*- encoding: utf-8 -*-
from _ctypes import ArgumentError

import os
import unittest
import tempfile


class TestCase(unittest.TestCase):
    """
    Test case base class providing database related test helpers.
    """

    def database_temp_file(self):
        if not hasattr(self, '_database_temp_path'):
            self._database_temp_path = tempfile.NamedTemporaryFile().name
        return self._database_temp_path

    def database_type(self):
        env = os.getenv('DB', 'sqlite')
        if env == 'sqlite':
            return 'sqlite'
        elif env == 'postgresql':
            return 'postgresql'
        elif env == 'mysql':
            return 'mysql'
        else:
            raise ArgumentError('Unknown database type: ' + env)

    def database_uri(self):
        """
        Return a database URI. Specify DBMS by `DB` environment variable.

        Allowed values are `sqlite`, `postgresql`, `mysql`. SQLite database will point to a
        generated temp file path.
        """

        dbms = self.database_type()
        if dbms == 'sqlite':
            return self.database_type() + ':///' + self.database_temp_file()
        else:
            return self.database_type() + ':///isso-test'

    def database_conf(self, conf):
        """
        Configure given `conf` object to use test database. See `#database_uri`.
        """

        conf.set("general", "database", self.database_uri())

    def tearDown(self):
        if hasattr(self, 'app'):
            # Drop database tables after tests
            self.app.db.drop()

        if hasattr(self, 'db'):
            # Drop database tables after tests
            self.db.drop()

        if hasattr(self, '_database_temp_path'):
            os.unlink(self._database_temp_path)

