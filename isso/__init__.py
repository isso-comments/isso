#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of posativ <info@posativ.org>.
#
# Isso – a lightweight Disqus alternative

__version__ = '0.1'

import json

from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError

from isso import admin, comment, db, utils


_dumps = json.dumps
setattr(json, 'dumps', lambda obj, **kw: _dumps(obj, cls=utils.IssoEncoder, **kw))


url = lambda path, endpoint, methods: Rule(path, endpoint=endpoint, methods=methods)
url_map = Map([
    # moderation panel
    url('/', 'admin.index', ['GET', 'POST']),

    # comments API
    url('/comment/<string:path>/', 'comment.get', ['GET']),
    url('/comment/<string:path>/new', 'comment.create', ['POST']),
    url('/comment/<string:path>/<int:id>', 'comment.get', ['GET']),
    url('/comment/<string:path>/<int:id>', 'comment.modify', ['PUT', 'DELETE']),
])


class Isso:

    PRODUCTION = True
    SECRET_KEY = ',\x1e\xbaY\xbb\xdf\xe7@\x85\xe3\xd9\xb4A9\xe4G\xa6O'
    MODERATION = False
    SQLITE = None

    HOST = 'http://localhost:8000/'
    MAX_AGE = 15*60

    def __init__(self, conf):

        self.__dict__.update(dict((k, v) for k, v in conf.iteritems() if k.isupper()))
        self.signer = URLSafeTimedSerializer(self.SECRET_KEY)
        self.HOST = utils.determine(self.HOST)

        if self.SQLITE:
            self.db = db.SQLite(self)

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj):
        return self.signer.loads(obj, max_age=self.MAX_AGE)

    def dispatch(self, request, start_response):
        adapter = url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            module, function = endpoint.split('.', 1)
            handler = getattr(globals()[module], function)
            return handler(self, request.environ, request, **values)
        except NotFound, e:
            return Response('Not Found', 404)
        except HTTPException, e:
            return e
        except InternalServerError, e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request, start_response)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():

    app = Isso({'SQLITE': '/tmp/sqlite.db'})
    run_simple('127.0.0.1', 8080, app)
