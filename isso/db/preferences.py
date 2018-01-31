# -*- encoding: utf-8 -*-

import os
import binascii


class Preferences:

    defaults = [
        ("session-key", binascii.b2a_hex(os.urandom(24)).decode('utf-8')),
    ]

    def __init__(self, db):

        self.db = db
        self.db.execute([
            'CREATE TABLE IF NOT EXISTS preferences (',
            '   key VARCHAR PRIMARY KEY, value VARCHAR',
            ');'])

        for (key, value) in Preferences.defaults:
            if self.get(key) is None:
                self.set(key, value)

    def get(self, key, default=None):
        rv = self.db.execute(
            'SELECT value FROM preferences WHERE key=?', (key, )).fetchone()

        if rv is None:
            return default

        return rv[0]

    def set(self, key, value):
        self.db.execute(
            'INSERT INTO preferences (key, value) VALUES (?, ?)', (key, value))
