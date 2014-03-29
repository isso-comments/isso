# -*- encoding: utf-8 -*-

import socket

try:
    from urllib.parse import quote, urlparse

    from socketserver import ThreadingMixIn
    from http.server import HTTPServer
except ImportError:
    from urllib import quote
    from urlparse import urlparse

    from SocketServer import ThreadingMixIn
    from BaseHTTPServer import HTTPServer

from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import Headers

from isso.compat import string_types


def host(environ):  # pragma: no cover
    """
    Reconstruct host from environment. A modified version
    of http://www.python.org/dev/peps/pep-0333/#url-reconstruction
    """

    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
                url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
                url += ':' + environ['SERVER_PORT']

    return url + quote(environ.get('SCRIPT_NAME', ''))


def urlsplit(name):
    """
    Parse :param:`name` into (netloc, port, ssl)
    """

    if not (isinstance(name, string_types)):
        name = str(name)

    if not name.startswith(('http://', 'https://')):
        name = 'http://' + name

    rv = urlparse(name)
    if rv.scheme == 'https' and rv.port is None:
        return (rv.netloc, 443, True)
    return (rv.netloc.rsplit(':')[0], rv.port or 80, rv.scheme == 'https')


def urljoin(netloc, port, ssl):
    """
    Basically the counter-part of :func:`urlsplit`.
    """

    rv = ("https" if ssl else "http") + "://" + netloc
    if ssl and port != 443 or not ssl and port != 80:
        rv += ":%i" % port
    return rv


def origin(hosts):
    """
    Return a function that returns a valid HTTP Origin or localhost
    if none found.
    """

    hosts = [urlsplit(h) for h in hosts]

    def func(environ):

        if not hosts:
            return "http://invalid.local"

        loc = environ.get("HTTP_ORIGIN", environ.get("HTTP_REFERER", None))

        if loc is None:
            return urljoin(*hosts[0])

        for split in hosts:
            if urlsplit(loc) == split:
                return urljoin(*split)
        else:
            return urljoin(*hosts[0])

    return func


class SubURI(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        script_name = environ.get('HTTP_X_SCRIPT_NAME')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        return self.app(environ, start_response)


class CORSMiddleware(object):
    """Add Cross-origin resource sharing headers to every request."""

    methods = ("HEAD", "GET", "POST", "PUT", "DELETE")

    def __init__(self, app, origin, allowed=[], exposed=[]):
        self.app = app
        self.origin = origin
        self.allowed = allowed
        self.exposed = exposed

    def __call__(self, environ, start_response):

        def add_cors_headers(status, headers, exc_info=None):
            headers = Headers(headers)
            headers.add("Access-Control-Allow-Origin", self.origin(environ))
            headers.add("Access-Control-Allow-Credentials", "true")
            headers.add("Access-Control-Allow-Methods", ", ".join(self.methods))
            if self.allowed:
                headers.add("Access-Control-Allow-Headers", ", ".join(self.allowed))
            if self.exposed:
                headers.add("Access-Control-Expose-Headers", ", ".join(self.exposed))
            return start_response(status, headers.to_list(), exc_info)

        if environ.get("REQUEST_METHOD") == "OPTIONS":
            add_cors_headers("200 Ok", [("Content-Type", "text/plain")])
            return [b'200 Ok']

        return self.app(environ, add_cors_headers)


class SocketWSGIRequestHandler(WSGIRequestHandler):

    def run_wsgi(self):
        self.client_address = ("<local>", 0)
        super(SocketWSGIRequestHandler, self).run_wsgi()


class SocketHTTPServer(HTTPServer, ThreadingMixIn):
    """
    A simple SocketServer to serve werkzeug's WSGIRequesthandler.
    """

    multithread = True
    multiprocess = False

    allow_reuse_address = 1
    address_family = socket.AF_UNIX

    request_queue_size = 128

    def __init__(self, sock, app):
        HTTPServer.__init__(self, sock, SocketWSGIRequestHandler)
        self.app = app
        self.ssl_context = None
        self.shutdown_signal = False
