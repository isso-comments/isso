# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from werkzeug.wrappers import Response


def index(app, environ, request):
    return Response('', 200)
