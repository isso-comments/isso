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
import socket
import httplib
import urlparse

from os.path import dirname, join
from argparse import ArgumentParser
from ConfigParser import ConfigParser

import misaka
from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, MethodNotAllowed

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple
from werkzeug.contrib.fixers import ProxyFix

from jinja2 import Environment, FileSystemLoader

from isso import db, utils, migrate, views, wsgi, notify, colors
from isso.views import comment, admin

url_map = Map([
    Rule('/', methods=['HEAD', 'GET'], endpoint=views.comment.get),
    Rule('/', methods=['PUT', 'DELETE'], endpoint=views.comment.modify),
    Rule('/new', methods=['POST'], endpoint=views.comment.create),
    Rule('/like', methods=['POST'], endpoint=views.comment.like),
    Rule('/count', methods=['GET'], endpoint=views.comment.count),

    Rule('/admin/', endpoint=views.admin.index)
])


class Isso(object):

    PRODUCTION = False

    def __init__(self, dbpath, secret, origin, max_age, passphrase, mailer):

        self.DBPATH = dbpath
        self.ORIGIN = origin
        self.PASSPHRASE = passphrase
        self.MAX_AGE = max_age

        self.db = db.SQLite(dbpath, moderation=False)
        self.signer = URLSafeTimedSerializer(secret)
        self.j2env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates/')))
        self.notify = lambda *args, **kwargs: mailer.sendmail(*args, **kwargs)

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
        except MethodNotAllowed:
            return Response("Yup.", 200)
        except HTTPException as e:
            return e
        except InternalServerError as e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):
        response = self.dispatch(Request(environ), start_response)
        if hasattr(response, 'headers'):
            response.headers["Access-Control-Allow-Origin"] = self.ORIGIN.rstrip('/')
            response.headers["Access-Control-Allow-Headers"] = "Origin, Content-Type"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():

    parser = ArgumentParser(description="a blog comment hosting service")
    subparser = parser.add_subparsers(help="commands", dest="command")

    parser.add_argument('--version', action='version', version='%(prog)s ' + dist.version)
    parser.add_argument("-c", dest="conf", default="/etc/isso.conf",
            metavar="/etc/isso.conf", help="set configuration file")

    imprt = subparser.add_parser('import', help="import Disqus XML export")
    imprt.add_argument("dump", metavar="FILE")

    serve = subparser.add_parser("run", help="run server")

    defaultcfg = [
        "[general]",
        "dbpath = /tmp/isso.db", "secretkey = %r" % os.urandom(24),
        "host = http://localhost:8080/", "passphrase = p@$$w0rd",
        "max_age = 450",
        "[server]",
        "host = localhost", "port = 8080", "reload = off",
        "[SMTP]",
        "username = ", "password = ",
        "host = localhost", "port = 465", "ssl = on",
        "to = ", "from = "
    ]

    args = parser.parse_args()
    conf = ConfigParser(allow_no_value=True)
    conf.readfp(io.StringIO(u'\n'.join(defaultcfg)))
    conf.read(args.conf)

    if args.command == "import":
        migrate.disqus(db.SQLite(conf.get("general", "dbpath"), False), args.dump)
        sys.exit(0)

    if not conf.get("general", "host").startswith(("http://", "https://")):
        sys.exit("error: host must start with http:// or https://")

    try:
        print(" * connecting to SMTP server", end=" ")
        mailer = notify.SMTPMailer(conf)
        print("[%s]" % colors.green("ok"))
    except (socket.error, notify.SMTPException):
        print("[%s]" % colors.red("failed"))
        mailer = notify.NullMailer()

    try:
        print(" * connecting to HTTP server", end=" ")
        rv = urlparse.urlparse(conf.get("general", "host"))
        host = (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc
        httplib.HTTPConnection(host, timeout=5).request('GET', rv.path)
        print("[%s]" % colors.green("ok"))
    except (httplib.HTTPException, socket.error):
        print("[%s]" % colors.red("failed"))

    isso = Isso(
        dbpath=conf.get('general', 'dbpath'),
        secret=conf.get('general', 'secretkey'),
        origin=conf.get('general', 'host'),
        max_age=conf.getint('general', 'max_age'),
        passphrase=conf.get('general', 'passphrase'),
        mailer=mailer
    )

    app = ProxyFix(wsgi.SubURI(SharedDataMiddleware(isso.wsgi_app, {
        '/static': join(dirname(__file__), 'static/'),
        '/js': join(dirname(__file__), 'js/')
        })))

    run_simple(conf.get('server', 'host'), conf.getint('server', 'port'),
        app, threaded=True, use_reloader=conf.getboolean('server', 'reload'))
