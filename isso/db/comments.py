# -*- encoding: utf-8 -*-

import time

from isso.db import spam
from isso.utils import Bloomfilter


class Comments:
    """Hopefully DB-independend SQL to store, modify and retrieve all
    comment-related actions.  Here's a short scheme overview:

        | tid (thread id) | cid (comment id) | parent | ... | likes | remote_addr |
        +-----------------+------------------+--------+-----+-------+-------------+
        | 1               | 1                | null   | ... | BLOB  | 127.0.0.0   |
        | 1               | 2                | 1      | ... | BLOB  | 127.0.0.0   |
        +-----------------+------------------+--------+-----+-------+-------------+

    The tuple (tid, cid) is unique and thus primary key.
    """

    fields = ['tid', 'id', 'parent', 'created', 'modified', 'mode', 'remote_addr',
              'text', 'author', 'email', 'website', 'likes', 'dislikes', 'voters']

    def __init__(self, db):

        self.db = db
        self.db.execute([
            'CREATE TABLE IF NOT EXISTS comments (',
            '    tid REFERENCES threads(id), id INTEGER PRIMARY KEY, parent INTEGER,',
            '    created FLOAT NOT NULL, modified FLOAT, mode INTEGER, remote_addr VARCHAR,',
            '    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,',
            '    likes INTEGER DEFAULT 0, dislikes INTEGER DEFAULT 0, voters BLOB NOT NULL);'])

    @spam.check
    def add(self, uri, c):
        """
        Add a new comment to the database and return public fields as dict.
        Initializes voter bloom array with provided :param:`remote_addr` and
        adds a new thread to the `main.threads` table.
        """
        self.db.execute([
            'INSERT INTO comments (',
            '    tid, parent,'
            '    created, modified, mode, remote_addr,',
            '    text, author, email, website, voters )',
            'SELECT',
            '    threads.id, ?,',
            '    ?, ?, ?, ?,',
            '    ?, ?, ?, ?, ?',
            'FROM threads WHERE threads.uri = ?;'], (
            c.get('parent'),
            c.get('created') or time.time(), None, self.db.mode, c['remote_addr'],
            c['text'], c.get('author'), c.get('email'), c.get('website'), buffer(
                Bloomfilter(iterable=[c['remote_addr']]).array),
            uri)
        )

        return dict(zip(Comments.fields, self.db.execute(
            'SELECT *, MAX(c.id) FROM comments AS c INNER JOIN threads ON threads.uri = ?',
            (uri, )).fetchone()))

    # def activate(self, path, id):
    #     """Activate comment id if pending and return comment for (path, id)."""
    #     with sqlite3.connect(self.dbpath) as con:
    #         con.execute("UPDATE comments SET mode=1 WHERE path=? AND id=? AND mode=2", (path, id))
    #     return self.get(path, id)

    def update(self, id, data):
        """
        Update an existing comment, but only writeable fields such as text,
        author, email, website and parent. This method should set the modified
        field to the current time.
        """

        self.db.execute([
            'UPDATE comments SET',
                ','.join(key + '=' + '?' for key in data),
            'WHERE id=?;'],
            data.values() + [id])

        return self.get(id)

    def get(self, id):

        rv = self.db.execute('SELECT * FROM comments WHERE id=?', (id, )).fetchone()
        if rv:
            return dict(zip(Comments.fields, rv))

        return None

    def fetch(self, uri, mode=5):
        """
        Return all comments for `path` with `mode`.
        """
        rv = self.db.execute([
            'SELECT comments.* FROM comments INNER JOIN threads ON',
            '    threads.uri=? AND comments.tid=threads.id AND (? | comments.mode) = ?'
            'ORDER BY id ASC;'], (uri, mode, mode)).fetchall()

        for item in rv:
            yield dict(zip(Comments.fields, item))

    def _remove_stale(self):

        sql = ('DELETE FROM',
               '    comments',
               'WHERE',
               '    mode=4 AND id NOT IN (',
               '        SELECT',
               '            parent',
               '        FROM',
               '            comments',
               '        WHERE parent IS NOT NULL)')

        while self.db.execute(sql).rowcount:
            continue

    def delete(self, id):
        """
        Delete a comment. There are two distinctions: a comment is referenced
        by another valid comment's parent attribute or stand-a-lone. In this
        case the comment can't be removed without losing depending comments.
        Hence, delete removes all visible data such as text, author, email,
        website sets the mode field to 4.

        In the second case this comment can be safely removed without any side
        effects."""

        refs = self.db.execute('SELECT * FROM comments WHERE parent=?', (id, )).fetchone()

        if refs is None:
            self.db.execute('DELETE FROM comments WHERE id=?', (id, ))
            self._remove_stale()
            return None

        self.db.execute('UPDATE comments SET text=? WHERE id=?', ('', id))
        self.db.execute('UPDATE comments SET mode=? WHERE id=?', (4, id))
        for field in ('author', 'website'):
            self.db.execute('UPDATE comments SET %s=? WHERE id=?' % field, (None, id))

        self._remove_stale()
        return self.get(id)

    def vote(self, upvote, id, remote_addr):
        """+1 a given comment. Returns the new like count (may not change because
        the creater can't vote on his/her own comment and multiple votes from the
        same ip address are ignored as well)."""

        rv = self.db.execute(
            'SELECT likes, dislikes, voters FROM comments WHERE id=?', (id, )) \
            .fetchone()

        if rv is None:
            return None

        likes, dislikes, voters = rv
        if likes + dislikes >= 142:
            return {'likes': likes, 'dislikes': dislikes}

        bf = Bloomfilter(bytearray(voters), likes + dislikes)
        if remote_addr in bf:
            return {'likes': likes, 'dislikes': dislikes}

        bf.add(remote_addr)
        self.db.execute([
            'UPDATE comments SET',
            '    likes = likes + 1,' if upvote else 'dislikes = dislikes + 1,',
            '    voters = ?'
            'WHERE id=?;'], (buffer(bf.array), id))

        if upvote:
            return {'likes': likes + 1, 'dislikes': dislikes}
        return {'likes': likes, 'dislikes': dislikes + 1}

    def count(self, uri):
        """
        return count of comments for uri.
        """
        return self.db.execute([
            'SELECT COUNT(comments.id) FROM comments INNER JOIN threads ON',
            '    threads.uri=? AND comments.tid=threads.id AND comments.mode=1;'],
            (uri, )).fetchone()
