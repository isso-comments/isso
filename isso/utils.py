# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import json
from isso.models import Comment


class IssoEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Comment):
            return dict((field, value) for field, value in obj.iteritems())

        return json.JSONEncoder.default(self, obj)
