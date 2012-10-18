# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import abc
import time
import sqlite3

from isso.models import Comment


class Abstract:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, app):
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
        website sets the mode field to 2.

        In the second case this comment can be safely removed without any side
        effects."""
        return

    @abc.abstractmethod
    def retrieve(self, path, limit=20):
        return


class SQLite(Abstract):
    """A basic :class:`Abstract` implementation using SQLite3.  All comments
    share a single database. The tuple (id, path) acts as unique identifier
    for a comment. Multiple comments per path (= that is the URI to your blog
    post) are ordered by that id."""

    fields = [
        'id', 'path', 'created', 'modified',
        'text', 'author', 'email', 'website', 'parent', 'mode'
    ]

    def __init__(self, app):

        self.dbpath = app.SQLITE
        self.mode = 2 if app.MODERATION else 1

        with sqlite3.connect(self.dbpath) as con:
            sql = ('main.comments (id INTEGER NOT NULL, path VARCHAR(255) NOT NULL,'
                   'created FLOAT NOT NULL, modified FLOAT, text VARCHAR,'
                   'author VARCHAR(64), email VARCHAR(64), website VARCHAR(64),'
                   'parent INTEGER, mode INTEGER, PRIMARY KEY (id, path))')
            con.execute("CREATE TABLE IF NOT EXISTS %s;" % sql)

            # increment id if (id, path) is no longer unique
            con.execute("""\
                CREATE TRIGGER IF NOT EXISTS increment AFTER INSERT ON comments
                BEGIN
                    UPDATE comments SET
                       id=(SELECT MAX(id)+1 FROM comments WHERE path=NEW.path)
                    WHERE rowid=NEW.rowid;
                END;""")

    def query2comment(self, query):
        if query is None:
            return None

        return Comment(
            text=query[4], author=query[5], email=query[6], website=query[7],
            parent=query[8], mode=query[9], id=query[0], created=query[2], modified=query[3]
        )

    def add(self, path, c):
        with sqlite3.connect(self.dbpath) as con:
            keys = ','.join(self.fields)
            values = ','.join('?'*len(self.fields))
            con.execute('INSERT INTO comments (%s) VALUES (%s);' % (keys, values), (
                0, path, c.created, c.modified, c.text, c.author, c.email, c.website,
                c.parent, self.mode)
            )

        with sqlite3.connect(self.dbpath) as con:
            return self.query2comment(
                con.execute('SELECT *, MAX(id) FROM comments;').fetchone())

    def activate(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            con.execute("UPDATE comments SET mode=1 WHERE path=? AND id=? AND mode=2", (path, id))
        return self.get(path, id)

    def update(self, path, id, comment):
        with sqlite3.connect(self.dbpath) as con:
            for field, value in comment.iteritems(False):
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?;' % field,
                    (value, path, id))

        with sqlite3.connect(self.dbpath) as con:
            con.execute('UPDATE comments SET modified=? WHERE path=? AND id=?',
                (time.time(), path, id))
        return self.get(path, id)

    def get(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            return self.query2comment(con.execute(
                'SELECT * FROM comments WHERE path=? AND id=?;', (path, id)).fetchone())

    def delete(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            refs = con.execute('SELECT * FROM comments WHERE parent=?', (id, )).fetchone()

            if refs is None:
                con.execute('DELETE FROM comments WHERE path=? AND id=?', (path, id))
                return None

            con.execute('UPDATE comments SET text=? WHERE path=? AND id=?', ('', path, id))
            con.execute('UPDATE comments SET mode=? WHERE path=? AND id=?', (4, path, id))
            for field in set(Comment.fields) - set(['text', 'parent']):
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?' % field,
                    (None, path, id))
        return self.get(path, id)

    def retrieve(self, path, limit=20, mode=1):
        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute("SELECT * FROM comments WHERE path=? AND (? | mode) = ?" \
               + " ORDER BY id DESC LIMIT ?;", (path, mode, mode, limit)).fetchall()

        for item in rv:
            yield self.query2comment(item)
