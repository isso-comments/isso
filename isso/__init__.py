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
# policies, either expressed or implied, of Martin Zimmermann <info@posativ.org>.
#
# Isso – a lightweight Disqus alternative

from __future__ import print_function

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import sys
import io
import os
import json
import locale
import traceback

from os.path import dirname, join
from optparse import OptionParser, make_option

import misaka
from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple

from jinja2 import Environment, FileSystemLoader

from isso import db, utils, migrate
from isso.views import comment, admin

url_map = Map([
    Rule('/', methods=['HEAD', 'GET'], endpoint=views.comment.get),
    Rule('/', methods=['PUT', 'DELETE'], endpoint=views.comment.modify),
    Rule('/new', methods=['POST'], endpoint=views.comment.create),

    Rule('/admin/', endpoint=views.admin.index)
])


class Isso(object):

    BASE_URL = 'http://localhost:8080/'
    MAX_AGE = 15 * 60
    PRODUCTION = False

    def __init__(self, dbpath, secret, base_url, max_age):

        self.DBPATH = dbpath
        self.BASE_URL = utils.normalize(base_url)

        self.db = db.SQLite(dbpath, moderation=False)
        self.signer = URLSafeTimedSerializer(secret)
        self.j2env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates/')))

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj):
        return self.signer.loads(obj, max_age=self.MAX_AGE)

    def markdown(self, text):
        return misaka.html(text, extensions=misaka.EXT_STRIKETHROUGH \
            | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK \
            | misaka.HTML_SKIP_HTML  | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)

    def render(self, tt, **ctx):
        tt = self.j2env.get_template(tt)
        return tt.render(**ctx)

    @classmethod
    def dumps(cls, obj, **kw):
        return json.dumps(obj, cls=utils.IssoEncoder, **kw)

    def dispatch(self, request, start_response):
        adapter = url_map.bind_to_environ(request.environ)
        try:
            handler, values = adapter.match()
            return handler(self, request.environ, request, **values)
        except NotFound as e:
            return Response('Not Found', 404)
        except HTTPException as e:
            return e
        except InternalServerError as e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):
        response = self.dispatch(Request(environ), start_response)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():

    options = [
        make_option("--version", action="store_true",
            help="print version info and exit"),

        make_option("--dbpath", dest="dbpath", metavar='FILE', default=":memory:",
            help="database location"),
        make_option("--base-url", dest="base_url", default="http://localhost:8080/",
            help="set base url for comments"),
        make_option("--secret-key", dest="secret", default=None,
            help="fixed secret key (admin auth etc.)"),
        make_option("--max-age", dest="max_age", default=15*60, type=int,
            help="..."),

        make_option("--host", dest="host", default="localhost",
            help="webserver address"),
        make_option("--port", dest="port", default=8080,
            help="webserver port"),
    ]

    parser = OptionParser(option_list=options)
    options, args = parser.parse_args()

    if options.version:
        print('isso', dist.version)
        sys.exit(0)

    isso = Isso(dbpath=options.dbpath, secret=options.secret or utils.mksecret(12),
               base_url=options.base_url, max_age=options.max_age)

    if len(args) > 0 and args[0] == 'import':
        if len(args) < 2:
            print('Usage: isso import FILE')
            sys.exit(2)

        migrate.disqus(isso.db, args[1])
        sys.exit(0)

    app = SharedDataMiddleware(isso.wsgi_app, {
        '/static': join(dirname(__file__), 'static/')
        })

    print(' * Session Key:', isso.signer.secret_key)
    run_simple(options.host, options.port, app, threaded=True)
