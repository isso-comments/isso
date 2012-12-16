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

__version__ = '0.3'

import sys; reload(sys)
sys.setdefaultencoding('utf-8')  # we only support UTF-8 and python 2.X :-)

import io
import os
import json
import traceback

from optparse import OptionParser, make_option, SUPPRESS_HELP

from itsdangerous import URLSafeTimedSerializer

from isso import admin, comment, db, migrate, wsgi
from isso.utils import determine, import_object, IssoEncoder

# override default json :func:`dumps`.
_dumps = json.dumps
setattr(json, 'dumps', lambda obj, **kw: _dumps(obj, cls=IssoEncoder, **kw))


class Isso(object):

    PRODUCTION = True
    SECRET = 'secret'
    SECRET_KEY = ',\x1e\xbaY\xbb\xdf\xe7@\x85\xe3\xd9\xb4A9\xe4G\xa6O'
    MODERATION = False
    SQLITE = None

    HOST = 'http://localhost:8080/'
    MAX_AGE = 15 * 60

    HTTP_STATUS_CODES = {
        200: 'Ok', 201: 'Created', 202: 'Accepted',
        301: 'Moved Permanently', 304: 'Not Modified',
        400: 'Bad Request', 404: 'Not Found', 403: 'Forbidden',
        500: 'Internal Server Error',
    }

    def __init__(self, conf):

        self.__dict__.update(dict((k, v) for k, v in conf.iteritems() if k.isupper()))
        self.signer = URLSafeTimedSerializer(self.SECRET_KEY)
        self.HOST = determine(self.HOST)

        if self.SQLITE:
            self.db = db.SQLite(self)

        self.markup = import_object(conf.get('MARKUP', 'isso.markup.Markdown'))(conf)
        self.adapter = map(
            lambda r: (wsgi.Rule(r[0]), r[1], r[2] if isinstance(r[2], list) else [r[2]]), [

            # moderation panel
            ('/', admin.login, ['HEAD', 'GET', 'POST']),
            ('/admin/', admin.index, ['HEAD', 'GET', 'POST']),

            # assets
            ('/<(static|js):directory>/<(.+?):path>', wsgi.static, ['HEAD', 'GET']),

            # comment API, note that the client side quotes the URL, but this is
            # actually unnecessary. PEP 333 aka WSGI always unquotes PATH_INFO.
            ('/1.0/<(.+?):path>/new', comment.create,'POST'),
            ('/1.0/<(.+?):path>/<(int):id>', comment.get, ['HEAD', 'GET']),
            ('/1.0/<(.+?):path>/<(int):id>', comment.modify, ['PUT', 'DELETE']),
            ('/1.0/<(.+?):path>/<(int):id>/approve', comment.approve, 'PUT'),

            ('/1.0/<(.+?):path>', comment.get, 'GET'),
        ])

    def sign(self, obj):
        return self.signer.dumps(obj)

    def unsign(self, obj):
        return self.signer.loads(obj, max_age=self.MAX_AGE)

    def status(self, code):
        return '%i %s' % (code, self.HTTP_STATUS_CODES[code])

    def dispatch(self, path, method):

        for rule, handler, methods in self.adapter:
            if isinstance(methods, basestring):
                methods = [methods, ]
            if method not in methods:
                continue
            m = rule.match(path)
            if m is not None:
                return handler, m
        else:
            return (lambda app, environ, request, **kw: (404, 'Not Found', {}), {})

    def wsgi(self, environ, start_response):

        try:
            request = wsgi.Request(environ)
            handler, kwargs = self.dispatch(environ['PATH_INFO'], request.method)
            code, body, headers = handler(self, environ, request, **kwargs)

            if code == 404:
                try:
                    code, body, headers = wsgi.sendfile(environ['PATH_INFO'], os.getcwd(), environ)
                except (IOError, OSError):
                    try:
                        path = environ['PATH_INFO'].rstrip('/') + '/index.html'
                        code, body, headers = wsgi.sendfile(path, os.getcwd(), environ)
                    except (IOError, OSError):
                        pass

            if request == 'HEAD':
                body = ''

            start_response(self.status(code), headers.items())
            return body

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            traceback.print_exc(file=sys.stderr)
            headers = [('Content-Type', 'text/html; charset=utf-8')]
            start_response(self.status(500), headers)
            return '<h1>' + self.status(500) + '</h1>'

    def __call__(self, environ, start_response):
        return self.wsgi(environ, start_response)


class ReverseProxied(object):

    def __init__(self, app, prefix=None):
        self.app = app
        self.prefix = prefix if prefix is not None else ''

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', self.prefix)
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)


def main():

    options = [
        make_option("--version", action="store_true", help="print version info and exit"),
        make_option("--sqlite", dest="sqlite", metavar='FILE', default="/tmp/sqlite.db",
            help="use SQLite3 database"),
        make_option("--port", dest="port", default=8000, help="webserver port"),
        make_option("--debug", dest="production", action="store_false", default=True,
            help=SUPPRESS_HELP),
    ]

    parser = OptionParser(option_list=options)
    options, args = parser.parse_args()

    if options.version:
        print 'isso', __version__
        sys.exit(0)

    app = Isso({'SQLITE': options.sqlite, 'PRODUCTION': options.production, 'MODERATION': True})

    if len(args) > 0 and args[0] == 'import':
        if len(args) < 2:
            print 'Usage: isso import FILE'
            sys.exit(2)

        with io.open(args[1], encoding='utf-8') as fp:
            migrate.disqus(app.db, fp.read())

    else:
        from wsgiref.simple_server import make_server
        httpd = make_server('127.0.0.1', 8080, app, server_class=wsgi.ThreadedWSGIServer)
        httpd.serve_forever()
