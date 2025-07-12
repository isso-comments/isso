# -*- encoding: utf-8 -*-

import logging
import time

from isso.utils import Bloomfilter


logger = logging.getLogger("isso")


MAX_LIKES_AND_DISLIKES = 142

MESSAGE_TYPES = {
    'comment': 'comment',                    # 普通评论
    'system_notification': 'system_notification',  # 系统通知
    #'task_created': 'task_created',          # 任务创建
    #'task_updated': 'task_updated',          # 任务更新
    #'content_modified': 'content_modified',   # 内容修改
    #'user_mention': 'user_mention',          # 用户提及
    #'status_change': 'status_change'         # 状态变更
}


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

    fields = ['tid', 'id', 'parent', 'created', 'modified',
              'mode',  # status of the comment 1 = valid, 2 = pending,
                       # 4 = soft-deleted (cannot hard delete because of replies)
              'remote_addr', 'text', 'author', 'email', 'website',
              'likes', 'dislikes', 'voters', 'notification',
              'message_type', 'system_data']

    # This method is used in the migration script from version 4 to 5.
    # You need to write a new migration if you change the database schema!
    @staticmethod
    def create_table_query(table_name):
        return f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                tid REFERENCES threads(id),
                id INTEGER PRIMARY KEY,
                parent INTEGER,
                created FLOAT NOT NULL,
                modified FLOAT,
                mode INTEGER,
                remote_addr VARCHAR,
                text VARCHAR NOT NULL,
                author VARCHAR,
                email VARCHAR,
                website VARCHAR,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                voters BLOB NOT NULL,
                notification INTEGER DEFAULT 0,
                message_type VARCHAR(50) DEFAULT 'comment',
                system_data TEXT
            );
        '''

    def __init__(self, db):

        self.db = db
        self.db.execute(Comments.create_table_query("comments"))

    def add(self, uri, c):
        """
        Add new comment to DB and return a mapping of :attribute:`fields` and
        database values.
        """

        # Comment parent must be valid and be of same thread
        # If parent itself has a valid parent, use that
        def _find(uri, parent):
            if parent in ["0", 0, None]:
                return None
            obj = self.get(parent)
            if obj is None:  # parent does not exist
                return None
            rv = self.db.execute([
                'SELECT CASE WHEN EXISTS(',
                '   SELECT comments.id FROM comments INNER JOIN threads',
                '       ON comments.tid=threads.id WHERE threads.uri=?',
                '       AND comments.id=?)',
                '   THEN 1 ELSE 0 END;'],
                (uri, parent)).fetchone()
            if rv[0] == 0:  # parent is not in current thread
                return None
            return _find(uri, obj.get("parent")) or parent

        if c.get("parent") is not None:
            c["parent"] = _find(uri, c["parent"])

        self.db.execute([
            'INSERT INTO comments (',
            '    tid, parent,'
            '    created, modified, mode, remote_addr,',
            '    text, author, email, website, voters, notification,'
            '    message_type, system_data)',
            'SELECT',
            '    threads.id, ?,',
            '    ?, ?, ?, ?,',
            '    ?, ?, ?, ?, ?, ?,',
            '    ?, ?',
            'FROM threads WHERE threads.uri = ?;'], (
            c.get('parent'),
            c.get('created') or time.time(), None, c["mode"], c['remote_addr'],
            c['text'], c.get('author'), c.get('email'), c.get('website'), memoryview(
                Bloomfilter(iterable=[c['remote_addr']]).array), c.get('notification'),
                c.get('message_type', 'comment'),
                c.get('system_data'),
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

    def is_previously_approved_author(self, email):
        """
        Search for previously activated comments with this author email.
        """

        # if the user has not entered email, email is None, in which case we can't check if they have previous comments
        if email is not None:
            # search for any activated comments within the last 6 months by email
            # this SQL should be one of the fastest ways of doing this check
            # https://stackoverflow.com/questions/18114458/fastest-way-to-determine-if-record-exists
            rv = self.db.execute([
                'SELECT CASE WHEN EXISTS(',
                '    select * from comments where email=? and mode=1 and ',
                '    created > strftime("%s", DATETIME("now", "-6 month"))',
                ') THEN 1 ELSE 0 END;'], (email,)).fetchone()
            return rv[0] == 1
        else:
            return False

    def unsubscribe(self, email, id):
        """
        Turn off email notifications for replies to this comment.
        """
        self.db.execute([
            'UPDATE comments SET',
            '    notification=0',
            'WHERE email=? AND (id=? OR parent=?);'], (email, id, id))

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
        rv = self.db.execute(
            'SELECT * FROM comments WHERE id=?', (id, )).fetchone()
        if rv:
            return dict(zip(Comments.fields, rv))

        return None

    def count_modes(self):
        """
        Return comment mode counts for admin
        """
        comment_count = self.db.execute(
            'SELECT mode, COUNT(comments.id) FROM comments '
            'GROUP BY comments.mode').fetchall()
        return dict(comment_count)

    def fetchall(self, mode=5, after=0, parent='any', order_by='id',
                 limit=100, page=0, asc=1, comment_id=None, thread_uri=None, message_type=None):
        """
        Return comments for admin with :param:`mode`.
        """
        fields_comments = ['tid', 'id', 'parent', 'created', 'modified',
                           'mode', 'remote_addr', 'text', 'author',
                           'email', 'website', 'likes', 'dislikes']
        fields_threads = ['uri', 'title']
        sql_comments_fields = ', '.join(['comments.' + f
                                         for f in fields_comments])
        sql_threads_fields = ', '.join(['threads.' + f
                                        for f in fields_threads])
        sql = ['SELECT ' + sql_comments_fields + ', ' + sql_threads_fields + ' '
               'FROM comments INNER JOIN threads '
               'ON comments.tid=threads.id '
               'WHERE ']

        if comment_id:
            sql.append('comments.id = ? ')
            sql_args = [comment_id]
        elif thread_uri:
            sql.append('threads.uri = ? ')
            sql_args = [thread_uri]
        else:
            sql.append('comments.mode = ? ')
            sql_args = [mode]


        if message_type:
            sql.append('AND comments.message_type = ? ')
            sql_args.append(message_type)

        if parent != 'any':
            if parent is None:
                sql.append('AND comments.parent IS NULL')
            else:
                sql.append('AND comments.parent=?')
                sql_args.append(parent)

        # custom sanitization
        if order_by not in ['id', 'created', 'modified', 'likes', 'dislikes', 'tid']:
            sql.append('ORDER BY ')
            sql.append("comments.created")
            if not asc:
                sql.append(' DESC')
        else:
            sql.append('ORDER BY ')
            sql.append('comments.' + order_by)
            if not asc:
                sql.append(' DESC')
            sql.append(", comments.created")

        if limit:
            sql.append('LIMIT ?,?')
            sql_args.append(page * limit)
            sql_args.append(limit)

        rv = self.db.execute(sql, sql_args).fetchall()
        for item in rv:
            yield dict(zip(fields_comments + fields_threads, item))

    def fetch(self, uri, mode=5, after=0, parent='any',
              order_by='id', asc=1, limit=None, offset=0, message_type=None):
        """
        Return comments for :param:`uri` with :param:`mode`.
        """
        sql = ['SELECT comments.*, likes - dislikes AS karma FROM comments INNER JOIN threads ON',
               '    threads.uri=? AND comments.tid=threads.id AND (? | comments.mode) = ?',
               '    AND comments.created>?']

        sql_args = [uri, mode, mode, after]

        if parent != 'any':
            if parent is None:
                sql.append('AND comments.parent IS NULL')
            else:
                sql.append('AND comments.parent=?')
                sql_args.append(parent)

        if message_type:
            sql.append('AND comments.message_type=?')
            sql_args.append(message_type)

        # custom sanitization
        if order_by not in ['id', 'created', 'modified', 'likes', 'dislikes', 'karma']:
            order_by = 'id'
        sql.append('ORDER BY ')
        sql.append(order_by)
        if not asc:
            sql.append(' DESC')

        if offset and limit:
            sql.append('LIMIT ?,?')
            sql_args.append(offset)
            sql_args.append(limit)
        elif limit:
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

        refs = self.db.execute(
            'SELECT * FROM comments WHERE parent=?', (id, )).fetchone()

        if refs is None:
            self.db.execute('DELETE FROM comments WHERE id=?', (id, ))
            self._remove_stale()
            return None

        self.db.execute('UPDATE comments SET text=? WHERE id=?', ('', id))
        self.db.execute('UPDATE comments SET mode=? WHERE id=?', (4, id))
        for field in ('author', 'website'):
            self.db.execute('UPDATE comments SET %s=? WHERE id=?' %
                            field, (None, id))

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

        operation_name = 'Upvote' if upvote else 'Downvote'
        likes, dislikes, voters = rv
        if likes + dislikes >= MAX_LIKES_AND_DISLIKES:
            message = '{} denied due to a "likes + dislikes" total too high ({} >= {})'.format(operation_name, likes + dislikes, MAX_LIKES_AND_DISLIKES)
            logger.debug('Comments.vote(id=%s): %s', id, message)
            return {'likes': likes, 'dislikes': dislikes, 'message': message}

        bf = Bloomfilter(bytearray(voters), likes + dislikes)
        if remote_addr in bf:
            message = '{} denied because a vote has already been registered for this remote address: {}'.format(operation_name, remote_addr)
            logger.debug('Comments.vote(id=%s): %s', id, message)
            return {'likes': likes, 'dislikes': dislikes, 'message': message}

        bf.add(remote_addr)
        self.db.execute([
            'UPDATE comments SET',
            '    likes = likes + 1,' if upvote else 'dislikes = dislikes + 1,',
            '    voters = ?'
            'WHERE id=?;'], (memoryview(bf.array), id))

        if upvote:
            return {'likes': likes + 1, 'dislikes': dislikes}
        return {'likes': likes, 'dislikes': dislikes + 1}

    def reply_count(self, url, mode=5):
        """
        Return comment count for main thread and all reply threads for one url.
        """

        sql = ['SELECT comments.parent,count(*)',
               'FROM comments INNER JOIN threads ON',
               '   threads.uri=? AND comments.tid=threads.id AND',
               '   (? | comments.mode = ?)',
               'GROUP BY comments.parent']

        return dict(self.db.execute(sql, [url, mode, mode]).fetchall())

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
        Remove stale pending comments older than :param:`delta`.
        """
        self.db.execute([
            'DELETE FROM comments WHERE mode = 2 AND ? - created > ?;'
        ], (time.time(), delta))
        self._remove_stale()
