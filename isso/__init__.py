#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2012-2013 Martin Zimmermann.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Isso – a lightweight Disqus alternative

from __future__ import print_function

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import sys
import os
import socket

from os.path import dirname, join
from argparse import ArgumentParser

try:
    import httplib
    import urlparse
except ImportError:
    import http.client as httplib
    import urllib.parse as urlparse

import misaka
from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple
from werkzeug.contrib.fixers import ProxyFix

from jinja2 import Environment, FileSystemLoader

from isso import db, migrate, views, wsgi, colors
from isso.core import ThreadedMixin, uWSGIMixin, Config
from isso.views import comment, admin

rules = Map([
    Rule('/new', methods=['POST'], endpoint=views.comment.new),

    Rule('/id/<int:id>', methods=['GET', 'PUT', 'DELETE'], endpoint=views.comment.single),
    Rule('/id/<int:id>/like', methods=['POST'], endpoint=views.comment.like),
    Rule('/id/<int:id>/dislike', methods=['POST'], endpoint=views.comment.dislike),

    Rule('/', methods=['GET'], endpoint=views.comment.fetch),
    Rule('/count', methods=['GET'], endpoint=views.comment.count),
    Rule('/delete/<string:auth>', endpoint=views.comment.delete),
    Rule('/activate/<string:auth>', endpoint=views.comment.activate),
    Rule('/admin/', endpoint=views.admin.index),

    Rule('/check-ip', endpoint=views.comment.checkip)
])


class Isso(object):

    salt = b"Eech7co8Ohloopo9Ol6baimi"

    def __init__(self, conf):

        self.conf = conf
        self.db = db.SQLite3(conf.get('general', 'dbpath'), conf)
        self.signer = URLSafeTimedSerializer(conf.get('general', 'session-key'))
        self.j2env = Environment(loader=FileSystemLoader(join(dirname(__file__), 'templates/')))

        super(Isso, self).__init__(conf)

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj, max_age=None):
        return self.signer.loads(obj, max_age=max_age or self.conf.getint('general', 'max-age'))

    def markdown(self, text):
        return misaka.html(text, extensions=misaka.EXT_STRIKETHROUGH \
            | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK \
            | misaka.HTML_SKIP_HTML  | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)

    def render(self, tt, **ctx):
        tt = self.j2env.get_template(tt)
        return tt.render(**ctx)

    def dispatch(self, request, start_response):
        adapter = rules.bind_to_environ(request.environ)
        try:
            handler, values = adapter.match()
            return handler(self, request.environ, request, **values)
        except NotFound:
            return Response('Not Found', 404)
        except MethodNotAllowed:
            return Response("Yup.", 200)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        response = self.dispatch(Request(environ), start_response)
        if hasattr(response, 'headers'):
            response.headers["Access-Control-Allow-Origin"] = self.conf.get('general', 'host').rstrip('/')
            response.headers["Access-Control-Allow-Headers"] = "Origin, Content-Type"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def make_app(conf=None):

    try:
        import uwsgi
    except ImportError:
        class App(Isso, ThreadedMixin):
            pass
    else:
        class App(Isso, uWSGIMixin):
            pass

    isso = App(conf)

    if not conf.get("general", "host").startswith(("http://", "https://")):
        raise SystemExit("error: host must start with http:// or https://")

    try:
        print(" * connecting to HTTP server", end=" ")
        rv = urlparse.urlparse(conf.get("general", "host"))
        host = (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc
        httplib.HTTPConnection(host, timeout=5).request('GET', rv.path)
        print("[%s]" % colors.green("ok"))
    except (httplib.HTTPException, socket.error):
        print("[%s]" % colors.red("failed"))

    app = ProxyFix(wsgi.SubURI(SharedDataMiddleware(isso.wsgi_app, {
        '/static': join(dirname(__file__), 'static/'),
        '/js': join(dirname(__file__), 'js/'),
        '/css': join(dirname(__file__), 'css/')
        })))

    return app


def main():

    parser = ArgumentParser(description="a blog comment hosting service")
    subparser = parser.add_subparsers(help="commands", dest="command")

    parser.add_argument('--version', action='version', version='%(prog)s ' + dist.version)
    parser.add_argument("-c", dest="conf", default="/etc/isso.conf",
            metavar="/etc/isso.conf", help="set configuration file")

    imprt = subparser.add_parser('import', help="import Disqus XML export")
    imprt.add_argument("dump", metavar="FILE")

    serve = subparser.add_parser("run", help="run server")

    args = parser.parse_args()
    conf = Config.load(args.conf)

    if args.command == "import":
        conf.set("guard", "enabled", "off")
        migrate.disqus(db.SQLite3(conf.get('general', 'dbpath'), conf), args.dump)
        sys.exit(0)

    run_simple(conf.get('server', 'host'), conf.getint('server', 'port'), make_app(conf),
               threaded=True, use_reloader=conf.getboolean('server', 'reload'))


try:
    import uwsgi
except ImportError:
    pass
else:
    application = make_app(Config.load(os.environ.get('ISSO_SETTINGS')))
