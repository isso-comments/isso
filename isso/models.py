# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from __future__ import unicode_literals

import hashlib


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

    fields = ["text", "author", "website", "votes", "hash", "parent", "mode", "id",
              "created", "modified"]

    def __init__(self, **kwargs):

        self.values = {}

        for key in Comment.fields:
            self.values[key] = kwargs.get(key, None)

    def __getitem__(self, key):
        return self.values[key]

    def __setitem__(self, key, value):
        self.values[key] = value

    def iteritems(self):
        for key in Comment.fields:
            yield key, self.values[key]

    @property
    def pending(self):
        return self.values["mode"] == 2

    @property
    def deleted(self):
        return self.values["mode"] == 4

    @property
    def md5(self):
        hv = hashlib.md5()

        for key, value in self.iteritems():
            if key == "parent" or value is None:
                continue
            hv.update(unicode(self.values.get(key, "")).encode("utf-8", "replace")) # XXX

        return hv.hexdigest()
