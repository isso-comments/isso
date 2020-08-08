#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2012-2014 Martin Zimmermann.
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

from __future__ import print_function, unicode_literals

import pkg_resources
dist = pkg_resources.get_distribution("isso")

# check if exectuable is `isso` and gevent is available
import sys

if sys.argv[0].startswith("isso"):
    try:
        import gevent.monkey
        gevent.monkey.patch_all()
    except ImportError:
        pass

import os
import errno
import logging
import tempfile

from os.path import dirname, join
from argparse import ArgumentParser
from functools import partial, reduce

import pkg_resources
werkzeug = pkg_resources.get_distribution("werkzeug")

from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map
from werkzeug.exceptions import HTTPException, InternalServerError

from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.local import Local, LocalManager
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.profiler import ProfilerMiddleware

local = Local()
local_manager = LocalManager([local])

from isso import config, db, migrate, wsgi, ext, views
from isso.core import ThreadedMixin, ProcessMixin, uWSGIMixin
from isso.wsgi import origin, urlsplit
from isso.utils import http, JSONRequest, html, hash
from isso.views import comments

from isso.ext.notifications import Stdout, SMTP

logging.getLogger('werkzeug').setLevel(logging.WARN)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")

logger = logging.getLogger("isso")


class ProxyFixCustom(ProxyFix):
    def __init__(self, app):
        # This is needed for werkzeug.wsgi.get_current_url called in isso/views/comments.py
        # to work properly when isso is hosted under a sub-path
        # cf. https://werkzeug.palletsprojects.com/en/1.0.x/middleware/proxy_fix/
        super().__init__(app, x_prefix=1)


class Isso(object):

    def __init__(self, conf):

        self.conf = conf
        self.db = db.SQLite3(conf.get('general', 'dbpath'), conf)
        self.signer = URLSafeTimedSerializer(
            self.db.preferences.get("session-key"))
        self.markup = html.Markup(conf.section('markup'))
        self.hasher = hash.new(conf.section("hash"))

        super(Isso, self).__init__(conf)

        subscribers = []
        smtp_backend = False
        for backend in conf.getlist("general", "notify"):
            if backend == "stdout":
                subscribers.append(Stdout(None))
            elif backend in ("smtp", "SMTP"):
                smtp_backend = True
            else:
                logger.warn("unknown notification backend '%s'", backend)
        if smtp_backend or conf.getboolean("general", "reply-notifications"):
            subscribers.append(SMTP(self))

        self.signal = ext.Signal(*subscribers)

        self.urls = Map()

        views.Info(self)
        views.Metrics(self)
        comments.API(self, self.hasher)

    def render(self, text):
        return self.markup.render(text)

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj, max_age=None):
        return self.signer.loads(obj, max_age=max_age or self.conf.getint('general', 'max-age'))

    def dispatch(self, request):
        local.request = request

        local.host = wsgi.host(request.environ)
        local.origin = origin(self.conf.getiter(
            "general", "host"))(request.environ)

        adapter = self.urls.bind_to_environ(request.environ)

        try:
            handler, values = adapter.match()
        except HTTPException as e:
            return e
        else:
            try:
                response = handler(request.environ, request, **values)
            except HTTPException as e:
                return e
            except Exception:
                logger.exception("%s %s", request.method,
                                 request.environ["PATH_INFO"])
                return InternalServerError()
            else:
                return response

    def wsgi_app(self, environ, start_response):
        response = self.dispatch(JSONRequest(environ))
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def make_app(conf=None, threading=True, multiprocessing=False, uwsgi=False):

    if not any((threading, multiprocessing, uwsgi)):
        raise RuntimeError("either set threading, multiprocessing or uwsgi")

    if threading:
        class App(Isso, ThreadedMixin):
            pass
    elif multiprocessing:
        class App(Isso, ProcessMixin):
            pass
    else:
        class App(Isso, uWSGIMixin):
            pass

    isso = App(conf)

    # check HTTP server connection
    for host in conf.getiter("general", "host"):
        with http.curl('HEAD', host, '/', 5) as resp:
            if resp is not None:
                logger.info("connected to %s", host)
                break
    else:
        logger.warn("unable to connect to your website, Isso will probably not "
                    "work correctly. Please make sure, Isso can reach your "
                    "website via HTTP(S).")

    wrapper = [local_manager.make_middleware]

    if isso.conf.getboolean("server", "profile"):
        wrapper.append(partial(ProfilerMiddleware,
                               sort_by=("cumulative", ), restrictions=("isso/(?!lib)", 10)))

    wrapper.append(partial(SharedDataMiddleware, exports={
        '/js': join(dirname(__file__), 'js/'),
        '/css': join(dirname(__file__), 'css/'),
        '/img': join(dirname(__file__), 'img/'),
        '/demo': join(dirname(__file__), 'demo/')
    }))

    wrapper.append(partial(wsgi.CORSMiddleware,
                           origin=origin(isso.conf.getiter("general", "host")),
                           allowed=("Origin", "Referer", "Content-Type"),
                           exposed=("X-Set-Cookie", "Date")))

    wrapper.extend([wsgi.SubURI, ProxyFixCustom])

    if werkzeug.version.startswith("0.8"):
        wrapper.append(wsgi.LegacyWerkzeugMiddleware)

    return reduce(lambda x, f: f(x), wrapper, isso)


def main():

    parser = ArgumentParser(description="a blog comment hosting service")
    subparser = parser.add_subparsers(help="commands", dest="command")

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + dist.version)
    parser.add_argument("-c", dest="conf", default="/etc/isso.conf",
                        metavar="/etc/isso.conf", help="set configuration file")

    imprt = subparser.add_parser('import', help="import Disqus XML export")
    imprt.add_argument("dump", metavar="FILE")
    imprt.add_argument("-n", "--dry-run", dest="dryrun", action="store_true",
                       help="perform a trial run with no changes made")
    imprt.add_argument("-t", "--type", dest="type", default=None,
                       choices=["disqus", "wordpress", "generic"], help="export type")
    imprt.add_argument("--empty-id", dest="empty_id", action="store_true",
                       help="workaround for weird Disqus XML exports, #135")

    # run Isso as stand-alone server
    subparser.add_parser("run", help="run server")

    args = parser.parse_args()
    conf = config.load(
        join(dist.location, dist.project_name, "defaults.ini"), args.conf)

    if args.command == "import":
        conf.set("guard", "enabled", "off")

        if args.dryrun:
            xxx = tempfile.NamedTemporaryFile()
            dbpath = xxx.name
        else:
            dbpath = conf.get("general", "dbpath")

        mydb = db.SQLite3(dbpath, conf)
        migrate.dispatch(args.type, mydb, args.dump, args.empty_id)

        sys.exit(0)

    if conf.get("general", "log-file"):
        handler = logging.FileHandler(conf.get("general", "log-file"))

        logger.addHandler(handler)
        logging.getLogger("werkzeug").addHandler(handler)

        logger.propagate = False
        logging.getLogger("werkzeug").propagate = False

    if not any(conf.getiter("general", "host")):
        logger.error("No website(s) configured, Isso won't work.")
        sys.exit(1)

    if conf.get("server", "listen").startswith("http://"):
        host, port, _ = urlsplit(conf.get("server", "listen"))
        try:
            from gevent.pywsgi import WSGIServer
            WSGIServer((host, port), make_app(conf)).serve_forever()
        except ImportError:
            run_simple(host, port, make_app(conf), threaded=True,
                       use_reloader=conf.getboolean('server', 'reload'))
    else:
        sock = conf.get("server", "listen").partition("unix://")[2]
        try:
            os.unlink(sock)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise
        wsgi.SocketHTTPServer(sock, make_app(conf)).serve_forever()
