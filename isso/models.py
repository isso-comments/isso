# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import json
import time
import hashlib

aluhut = lambda ip: hashlib.sha1(ip + '\x082@t9*\x17\xad\xc1\x1c\xa5\x98').hexdigest()


class Comment(object):
    """This class represents a regular comment. It needs at least a text
    field, all other fields are optional (or automatically set by the
    database driver.

    The field `mode` has a special meaning:

    1: normal
    2: in moderation queue
    4: deleted

    You can query for them like with UNIX permission bits, so you get both
    normal and queued using MODE=3.
    """

    protected = ['path', 'id', 'mode', 'created', 'modified', 'hash']
    fields = ['text', 'author', 'website', 'parent']

    def __init__(self, **kw):

        for field in self.protected + self.fields:
            setattr(self, field, kw.get(field))

    def iteritems(self, protected=True):
        for field in self.fields:
            yield field, getattr(self, field)
        if protected:
            for field in self.protected:
                yield field, getattr(self, field)

    @classmethod
    def fromjson(self, data, ip='127.0.0.1'):

        if '.' in ip:
            ip = ip.rsplit('.', 1)[0] + '.0'

        data = json.loads(data)
        comment = Comment(
            created=time.time(),
            hash=hashlib.md5(data.get('email', aluhut(ip))).hexdigest())

        for field in self.fields:
            if field == 'text' and field not in data:
                raise ValueError('Comment needs at least text, but no text was provided.')
            setattr(comment, field, data.get(field))

        return comment

    @property
    def pending(self):
        return self.mode == 2

    @property
    def deleted(self):
        return self.mode == 4

    @property
    def md5(self):
        hv = hashlib.md5()
        for key in set(self.fields) - set(['parent', ]):
            hv.update((getattr(self, key) or u"").encode('utf-8', errors="replace"))
        return hv.hexdigest()
