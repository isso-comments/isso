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
        import gevent.monkey; gevent.monkey.patch_all()
    except ImportError:
        pass

import os
import errno
import atexit
import logging

from os.path import dirname, join
from argparse import ArgumentParser
from functools import partial, reduce

try:
    input = raw_input
except NameError:
    pass

from itsdangerous import URLSafeTimedSerializer

from werkzeug.routing import Map, Rule, redirect
from werkzeug.exceptions import HTTPException, InternalServerError

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.local import Local, LocalManager
from werkzeug.serving import run_simple
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.contrib.profiler import ProfilerMiddleware

local = Local()
local_manager = LocalManager([local])

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso import cache, config, db, migrate, queue, spam, tasks, views, wsgi
from isso.wsgi import origin, urlsplit
from isso.utils import http, JSONRequest, html, hash

from isso.ext.notifications import Stdout, SMTP

logging.getLogger('werkzeug').setLevel(logging.WARN)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")

logger = logging.getLogger("isso")


class Isso(object):

    def __init__(self, conf, cacheobj=None, dbobj=None):

        if cacheobj is None:
            cacheobj = cache.Cache(1024)

        if dbobj is None:
            dbobj = db.Adapter("sqlite:///:memory:")

        self.conf = conf
        self.db = dbobj

        signer = URLSafeTimedSerializer(
            dbobj.preferences.get("session-key"))
        markup = html.Markup(
            conf.getlist("markup", "options"),
            conf.getlist("markup", "allowed-elements"),
            conf.getlist("markup", "allowed-attributes"))
        hasher = hash.new(
            conf.get("hash", "algorithm"),
            conf.get("hash", "salt"))
        guard = spam.Guard(
            dbobj,
            conf.getboolean("guard", "enabled"),
            conf.getint("guard", "ratelimit"),
            conf.getint("guard", "direct-reply"),
            conf.getboolean("guard", "reply-to-self"),
            conf.getint("general", "max-age"))

        urls = Map()
        Isso.routes(
            urls,
            views.API(conf, cacheobj, dbobj, guard, hasher.uhash, markup, signer),
            views.Info(conf))

        self.urls = urls

    @classmethod
    def routes(cls, urls, api, info):

        for rule in [
            Rule("/demo/", endpoint=lambda *z: redirect("/demo/index.html")),
            Rule("/info", endpoint=info.show)
        ]:
            urls.add(rule)

        for func, (method, rule) in [
            ('fetch',   ('GET', '/')),
            ('new',     ('POST', '/new')),
            ('count',   ('POST', '/count')),
            ('view',    ('GET', '/id/<int:id>')),
            ('edit',    ('PUT', '/id/<int:id>')),
            ('delete',  ('DELETE', '/id/<int:id>')),
            ('moderate',('GET',  '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
            ('moderate',('POST', '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
            ('like',    ('POST', '/id/<int:id>/like')),
            ('dislike', ('POST', '/id/<int:id>/dislike')),
        ]:
            urls.add(Rule(rule, methods=[method], endpoint=getattr(api, func)))

    def dispatch(self, request):
        local.request = request

        local.host = wsgi.host(request.environ)
        local.origin = origin(self.conf.getiter("general", "host"))(request.environ)

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
                logger.exception("%s %s", request.method, request.environ["PATH_INFO"])
                return InternalServerError()
            else:
                return response

    def wsgi_app(self, environ, start_response):
        response = self.dispatch(JSONRequest(environ))
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def make_app(conf):


    if uwsgi is not None:
        cacheobj = cache.uWSGICache(timeout=3600)
    else:
        cacheobj = cache.SACache(conf.get("general", "dbpath"), threshold=2048)

    dbobj = db.Adapter(conf.get("general", "dbpath"))

    jobs = tasks.Jobs()
    jobs.register("db-purge", dbobj, conf.getint("moderation", "purge-after"))
    jobs.register("http-fetch", dbobj)

    queueobj = queue.SAQueue(conf.get("general", "dbpath"), 1024)
    worker = queue.Worker(queueobj, jobs)

    isso = Isso(conf, cacheobj, dbobj)

    atexit.register(worker.join, 0.1)
    worker.start()

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

    if conf.getboolean("server", "profile"):
        wrapper.append(partial(ProfilerMiddleware,
            sort_by=("cumulative", ), restrictions=("isso/(?!lib)", 10)))

    wrapper.append(partial(SharedDataMiddleware, exports={
        '/js': join(dirname(__file__), 'js/'),
        '/css': join(dirname(__file__), 'css/'),
        '/demo': join(dirname(__file__), 'demo/')
    }))

    wrapper.append(partial(wsgi.CORSMiddleware,
        origin=origin(conf.getiter("general", "host")),
        allowed=("Origin", "Referer", "Content-Type"),
        exposed=("X-Set-Cookie", "Date")))

    wrapper.extend([wsgi.SubURI, ProxyFix])

    return reduce(lambda x, f: f(x), wrapper, isso)


def main():

    parser = ArgumentParser(description="a blog comment hosting service")
    subparser = parser.add_subparsers(help="commands", dest="command")

    parser.add_argument('--version', action='version', version='%(prog)s ' + dist.version)
    parser.add_argument("-c", dest="conf", default="/etc/isso.conf",
                        metavar="/etc/isso.conf", help="set configuration file")

    imprt = subparser.add_parser('import', help="import Disqus XML export")
    imprt.add_argument("dump", metavar="FILE")
    imprt.add_argument("-n", "--dry-run", dest="dryrun", action="store_true",
                       help="perform a trial run with no changes made")
    imprt.add_argument("-t", "--type", dest="type", default=None,
                       choices=["disqus", "wordpress"], help="export type")

    serve = subparser.add_parser("run", help="run server")

    args = parser.parse_args()
    conf = config.load(join(dist.location, "isso", "defaults.ini"), args.conf)

    if args.command == "import":
        from isso.controllers import threads, comments

        dburl = "sqlite:///:memory:" if args.dryrun else conf.get("general", "dbpath")
        dbobj = db.Adapter(dburl)

        tc = threads.Controller(dbobj)
        cc = comments.Controller(dbobj)

        if not cc.empty():
            if input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
                raise SystemExit("Abort.")

        migrate.dispatch(tc, cc, args.type, args.dump)
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

    app = make_app(conf)

    if conf.get("server", "listen").startswith("http://"):
        host, port, _ = urlsplit(conf.get("server", "listen"))
        try:
            from gevent.pywsgi import WSGIServer
            WSGIServer((host, port), app).serve_forever()
        except ImportError:
            run_simple(host, port, app, threaded=True,
                       use_reloader=conf.getboolean('server', 'reload'))
    else:
        sock = conf.get("server", "listen").partition("unix://")[2]
        try:
            os.unlink(sock)
        except OSError as ex:
            if ex.errno != errno.ENOENT:
                raise
        wsgi.SocketHTTPServer(sock, app).serve_forever()
