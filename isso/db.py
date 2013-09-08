# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import abc
import time
import sqlite3

from isso.utils import Bloomfilter
from isso.models import Comment


class Abstract:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, dbpath, moderation):
        return

    @abc.abstractmethod
    def add(self, path, comment):
        """Add a new comment to the database. Returns a Comment object."""
        return

    @abc.abstractmethod
    def activate(self, path, id):
        """Activate comment id if pending and return comment for (path, id)."""
        return

    @abc.abstractmethod
    def update(self, path, id, comment):
        """
        Update an existing comment, but only writeable fields such as text,
        author, email, website and parent. This method should set the modified
        field to the current time.
        """
        return

    @abc.abstractmethod
    def delete(self, path, id):
        """
        Delete a comment. There are two distinctions: a comment is referenced
        by another valid comment's parent attribute or stand-a-lone. In this
        case the comment can't be removed without losing depending comments.
        Hence, delete removes all visible data such as text, author, email,
        website sets the mode field to 4.

        In the second case this comment can be safely removed without any side
        effects."""
        return

    @abc.abstractmethod
    def retrieve(self, path, mode):
        """
        Return all comments for `path` with `mode`.
        """
        return

    @abc.abstractmethod
    def recent(self, mode=7, limit=None):
        """
        Return most recent comments with `mode`. If `limit` is None, return
        *all* comments that are currently stored, otherwise limit by `limit`.
        """
        return

    @abc.abstractmethod
    def like(self, path, id, remote_addr):
        """+1 a given comment. Returns the new like count (may not change because
        the creater can't vote on his/her own comment and multiple votes from the
        same ip address are ignored as well)."""
        return

class SQLite(Abstract):
    """A basic :class:`Abstract` implementation using SQLite3.  All comments
    share a single database. The tuple (id, path) acts as unique identifier
    for a comment. Multiple comments per path (= that is the URI to your blog
    post) are ordered by that id."""

    fields = [
        'path', 'id', 'created', 'modified',
        'text', 'author', 'hash', 'website', 'parent', 'mode', 'voters'
    ]

    def __init__(self, dbpath, moderation):

        self.dbpath = dbpath
        self.mode = 2 if moderation else 1

        with sqlite3.connect(self.dbpath) as con:
            sql = ('main.comments (path VARCHAR(255) NOT NULL, id INTEGER NOT NULL,'
                   'created FLOAT NOT NULL, modified FLOAT, text VARCHAR,'
                   'author VARCHAR(64), hash VARCHAR(32), website VARCHAR(64),'
                   'parent INTEGER, mode INTEGER,'
                   'likes INTEGER DEFAULT 0, dislikes INTEGER DEFAULT 0, voters BLOB NOT NULL,'
                   'PRIMARY KEY (id, path))')
            con.execute("CREATE TABLE IF NOT EXISTS %s;" % sql)

            # increment id if (id, path) is no longer unique
            con.execute("""\
                CREATE TRIGGER IF NOT EXISTS increment AFTER INSERT ON comments
                BEGIN
                    UPDATE comments SET
                       id=(SELECT MAX(id)+1 FROM comments WHERE path=NEW.path)
                    WHERE rowid=NEW.rowid;
                END;""")

            # threads (path -> title for now)
            sql = ('main.threads (path VARCHAR(255) NOT NULL, title TEXT'
                   'PRIMARY KEY path)')
            con.execute("CREATE TABLE IF NOT EXISTS %s;" % sql)

    def query2comment(self, query):
        if query is None:
            return None

        return Comment(
            text=query[4], author=query[5], hash=query[6], website=query[7], parent=query[8],
            path=query[0], id=query[1], created=query[2], modified=query[3], mode=query[9],
            votes=query[10]
        )

    def add(self, uri, c, remote_addr):
        voters = buffer(Bloomfilter(iterable=[remote_addr]).array)
        with sqlite3.connect(self.dbpath) as con:
            keys = ','.join(self.fields)
            values = ','.join('?' * len(self.fields))
            con.execute('INSERT INTO comments (%s) VALUES (%s);' % (keys, values), (
                uri, 0, time.time(), None, c["text"], c["author"], c["hash"], c["website"],
                c["parent"], self.mode, voters)
            )

        with sqlite3.connect(self.dbpath) as con:
            return self.query2comment(
                con.execute('SELECT *, MAX(id) FROM comments WHERE path=?;', (uri, )).fetchone())

    def activate(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            con.execute("UPDATE comments SET mode=1 WHERE path=? AND id=? AND mode=2", (path, id))
        return self.get(path, id)

    def update(self, path, id, values):
        with sqlite3.connect(self.dbpath) as con:
            for key, value in values.iteritems():
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?;' % key,
                    (value, path, id))

        with sqlite3.connect(self.dbpath) as con:
            con.execute('UPDATE comments SET modified=? WHERE path=? AND id=?',
                (time.time(), path, id))
        return self.get(path, id)

    def get(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            return self.query2comment(con.execute(
                'SELECT * FROM comments WHERE path=? AND id=?;', (path, id)).fetchone())

    def _remove_stale(self, con, path):

        sql = ('DELETE FROM',
               '    comments',
               'WHERE',
               '    path=? AND mode=4 AND id NOT IN (',
               '        SELECT',
               '            parent',
               '        FROM',
               '            comments',
               '        WHERE path=? AND parent IS NOT NULL)')

        while con.execute(' '.join(sql), (path, path)).rowcount:
            continue

    def delete(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            sql = 'SELECT * FROM comments WHERE path=? AND parent=?'
            refs = con.execute(sql, (path, id)).fetchone()

            if refs is None:
                con.execute('DELETE FROM comments WHERE path=? AND id=?', (path, id))
                self._remove_stale(con, path)
                return None

            con.execute('UPDATE comments SET text=? WHERE path=? AND id=?', ('', path, id))
            con.execute('UPDATE comments SET mode=? WHERE path=? AND id=?', (4, path, id))
            for field in ('author', 'website'):
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?' % field,
                    (None, path, id))

            self._remove_stale(con, path)

        return self.get(path, id)

    def like(self, path, id, remote_addr):
        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute("SELECT likes, dislikes, voters FROM comments" \
               + " WHERE path=? AND id=?", (path, id)).fetchone()

        likes, dislikes, voters = rv
        if likes + dislikes >= 142:
            return likes

        bf = Bloomfilter(bytearray(voters), likes + dislikes)
        if remote_addr in bf:
            return likes

        bf.add(remote_addr)
        with sqlite3.connect(self.dbpath) as con:
            con.execute("UPDATE comments SET likes = likes + 1 WHERE path=? AND id=?", (path, id))
            con.execute("UPDATE comments SET voters = ? WHERE path=? AND id=?", (
                buffer(bf.array), path, id))

        return likes + 1

    def retrieve(self, path, mode=5):
        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute("SELECT * FROM comments WHERE path=? AND (? | mode) = ?" \
               + " ORDER BY id ASC;", (path, mode, mode)).fetchall()

        for item in rv:
            yield self.query2comment(item)

    def recent(self, mode=7, limit=None):

        sql = 'SELECT * FROM comments WHERE (? | mode) = ? ORDER BY created DESC'
        args = [mode, mode]

        if limit:
            sql += ' LIMIT ?'
            args.append(limit)

        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute(sql + ';', args).fetchall()

        for item in rv:
            yield self.query2comment(item)

