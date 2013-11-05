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
import logging

from os.path import dirname, join
from argparse import ArgumentParser

try:
    import httplib
except ImportError:
    import http.client as httplib

import misaka
from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response
from werkzeug.exceptions import HTTPException, InternalServerError

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.serving import run_simple
from werkzeug.contrib.fixers import ProxyFix

from isso import db, migrate, views, wsgi
from isso.core import ThreadedMixin, uWSGIMixin, Config
from isso.utils import parse, http, JSONRequest
from isso.views import comment

logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")

logger = logging.getLogger("isso")


class Isso(object):

    salt = b"Eech7co8Ohloopo9Ol6baimi"
    urls = Map([
        Rule('/new', methods=['POST'], endpoint=views.comment.new),

        Rule('/id/<int:id>', methods=['GET', 'PUT', 'DELETE'], endpoint=views.comment.single),
        Rule('/id/<int:id>/like', methods=['POST'], endpoint=views.comment.like),
        Rule('/id/<int:id>/dislike', methods=['POST'], endpoint=views.comment.dislike),

        Rule('/', methods=['GET'], endpoint=views.comment.fetch),
        Rule('/count', methods=['GET'], endpoint=views.comment.count),
        Rule('/delete/<string:auth>', endpoint=views.comment.delete),
        Rule('/activate/<string:auth>', endpoint=views.comment.activate),

        Rule('/check-ip', endpoint=views.comment.checkip)
    ])

    @classmethod
    def CORS(cls, request, response, hosts):
        for host in hosts:
            if request.environ.get("HTTP_ORIGIN", None) == host.rstrip("/"):
                origin = host.rstrip("/")
                break
        else:
            origin = host.rstrip("/")

        hdrs = response.headers
        hdrs["Access-Control-Allow-Origin"] = origin
        hdrs["Access-Control-Allow-Headers"] = "Origin, Content-Type"
        hdrs["Access-Control-Allow-Credentials"] = "true"
        hdrs["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"

        return response

    def __init__(self, conf):

        self.conf = conf
        self.db = db.SQLite3(conf.get('general', 'dbpath'), conf)
        self.signer = URLSafeTimedSerializer(conf.get('general', 'session-key'))

        super(Isso, self).__init__(conf)

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj, max_age=None):
        return self.signer.loads(obj, max_age=max_age or self.conf.getint('general', 'max-age'))

    def markdown(self, text):
        return misaka.html(text, extensions=misaka.EXT_STRIKETHROUGH
            | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK
            | misaka.HTML_SKIP_HTML  | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)

    def dispatch(self, request):
        adapter = Isso.urls.bind_to_environ(request.environ)

        try:
            handler, values = adapter.match()
        except HTTPException as e:
            return e
        else:
            try:
                response = handler(self, request.environ, request, **values)
            except HTTPException as e:
                return e
            except Exception:
                logger.exception("%s %s", request.method, request.environ["PATH_INFO"])
                return InternalServerError()
            else:
                return response

    def wsgi_app(self, environ, start_response):

        response = self.dispatch(JSONRequest(environ))
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

    for host in conf.getiter("general", "host"):
        with http.curl('HEAD', host, '/', 5) as resp:
            if resp is not None:
                logger.info("connected to HTTP server")
                break
    else:
        logger.warn("unable to connect to HTTP server")

    if isso.conf.getboolean("server", "profile"):
        from werkzeug.contrib.profiler import ProfilerMiddleware as Profiler
        ProfilerMiddleware = lambda app: Profiler(app, sort_by=("cumtime", ), restrictions=("isso/(?!lib)", 10))
    else:
        ProfilerMiddleware = lambda app: app

    app = ProxyFix(
            wsgi.SubURI(
                wsgi.CORSMiddleware(
                    SharedDataMiddleware(
                        ProfilerMiddleware(isso), {
                            '/js': join(dirname(__file__), 'js/'),
                            '/css': join(dirname(__file__), 'css/')}),
                    list(isso.conf.getiter("general", "host")))))

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
