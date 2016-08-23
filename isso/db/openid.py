# -*- encoding: utf-8 -*-

import time

class OpenIDSessions:

    fields = ['id', 'created', 'identifier', 'issuer', 'client_id', 'client_secret', 'userinfo_endpoint', 'authorized']

    def __init__(self, db):
        self.db = db
        self.db.execute([
            'CREATE TABLE IF NOT EXISTS openid_sessions (',
            '    id VARCHAR PRIMARY KEY, created FLOAT NOT NULL, identifier VARCHAR,',
            '    issuer VARCHAR, client_id VARCHAR, client_secret VARCHAR,',
            '    userinfo_endpoint VARCHAR, authorized INTEGER);'])

    def add(self, s):
        self.db.execute([
            'INSERT INTO openid_sessions (',
            '    id, created, identifier, issuer, client_id, client_secret, userinfo_endpoint, authorized )',
            'VALUES (',
            '    ?, ?, ?, ?, ?, ?, ?, 0);'], (
                s.get('id'), time.time(), s.get('identifier'), s.get('issuer'), s.get('client_id'),
                s.get('client_secret'), s.get('userinfo_endpoint'))
        )

    def authorize(self, id):
        self.db.execute('UPDATE openid_sessions SET authorized=1 WHERE id=?;', (id,))

    def delete(self, id):
        self.db.execute('DELETE FROM openid_sessions WHERE id=?;', (id,))

    def purge(self, delta):
        self.db.execute([
            'DELETE FROM openid_sessions WHERE ? - created > ?;'
        ], (time.time(), delta))

    def get(self, id):
        rv = self.db.execute('SELECT * FROM openid_sessions WHERE id=?;', (id, )).fetchone()
        if rv:
            return dict(zip(self.fields, rv))
        return None
