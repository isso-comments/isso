# -*- encoding: utf-8 -*-

import time

from isso.utils import Bloomfilter
from isso.compat import buffer


class Comments:
    """Hopefully DB-independend SQL to store, modify and retrieve all
    comment-related actions.  Here's a short scheme overview:

        | tid (thread id) | id (comment id) | parent | ... | voters | remote_addr |
        +-----------------+-----------------+--------+-----+--------+-------------+
        | 1               | 1               | null   | ... | BLOB   | 127.0.0.0   |
        | 1               | 2               | 1      | ... | BLOB   | 127.0.0.0   |
        +-----------------+-----------------+--------+-----+--------+-------------+

    The tuple (tid, id) is unique and thus primary key.
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

    def add(self, uri, c):
        """
        Add new comment to DB and return a mapping of :attribute:`fields` and
        database values.
        """

        if c.get("parent") is not None:
            ref = self.get(c["parent"])
            if ref.get("parent") is not None:
                c["parent"] = ref["parent"]

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
            c.get('created') or time.time(), None, c["mode"], c['remote_addr'],
            c['text'], c.get('author'), c.get('email'), c.get('website'), buffer(
                Bloomfilter(iterable=[c['remote_addr']]).array),
            uri)
        )

        return dict(zip(Comments.fields, self.db.execute(
            'SELECT *, MAX(c.id) FROM comments AS c INNER JOIN threads ON threads.uri = ?',
            (uri, )).fetchone()))

    def activate(self, id):
        """
        Activate comment id if pending.
        """
        self.db.execute([
            'UPDATE comments SET',
            '    mode=1',
            'WHERE id=? AND mode=2'], (id, ))

    def update(self, id, data):
        """
        Update comment :param:`id` with values from :param:`data` and return
        updated comment.
        """
        self.db.execute([
            'UPDATE comments SET',
                ','.join(key + '=' + '?' for key in data),
            'WHERE id=?;'],
            list(data.values()) + [id])

        return self.get(id)

    def get(self, id):
        """
        Search for comment :param:`id` and return a mapping of :attr:`fields`
        and values.
        """
        rv = self.db.execute('SELECT * FROM comments WHERE id=?', (id, )).fetchone()
        if rv:
            return dict(zip(Comments.fields, rv))

        return None

    def fetch(self, uri, mode=5, after=0, parent='any', order_by='id', limit=None):
        """
        Return comments for :param:`uri` with :param:`mode`.
        """
        sql = [ 'SELECT comments.* FROM comments INNER JOIN threads ON',
                '    threads.uri=? AND comments.tid=threads.id AND (? | comments.mode) = ?',
                '    AND comments.created>?']

        sql_args = [uri, mode, mode, after]

        if parent != 'any':
            if parent is None:
                sql.append('AND comments.parent IS NULL')
            else:
                sql.append('AND comments.parent=?')
                sql_args.append(parent)

        sql.append('ORDER BY ? ASC')
        sql_args.append(order_by)

        if limit:
            sql.append('LIMIT ?')
            sql_args.append(limit)

        rv = self.db.execute(sql, sql_args).fetchall()
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

    def reply_count(self, url, after=0):
        """
        Return comment count for main thread and all reply threads for one url.
        """

        sql = [ 'SELECT comments.parent,count(*) FROM comments INNER JOIN threads ON', 
                '   threads.uri=? AND comments.tid=threads.id', 
                '   AND comments.mode = 1 AND comments.created>? GROUP BY comments.parent;']

        return dict(self.db.execute(sql, [url, after]).fetchall())

    def count(self, *urls):
        """
        Return comment count for one ore more urls..
        """

        threads = dict(self.db.execute([
            'SELECT threads.uri, COUNT(comments.id) FROM comments',
            'LEFT OUTER JOIN threads ON threads.id = tid AND comments.mode = 1',
            'GROUP BY threads.uri'
        ]).fetchall())

        return [threads.get(url, 0) for url in urls]

    def purge(self, delta):
        """
        Remove comments older than :param:`delta`.
        """
        self.db.execute([
            'DELETE FROM comments WHERE mode = 2 AND ? - created > ?;'
        ], (time.time(), delta))
        self._remove_stale()
