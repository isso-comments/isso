# -*- encoding: utf-8 -*-

import socket

try:
    from urllib.parse import quote

    from socketserver import ThreadingMixIn
    from http.server import HTTPServer
except ImportError:
    from urllib import quote

    from SocketServer import ThreadingMixIn
    from BaseHTTPServer import HTTPServer

from werkzeug.serving import WSGIRequestHandler
from werkzeug.datastructures import Headers


def host(environ):
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

    def __init__(self, app, origin):
        self.app = app
        self.origin = origin

    def __call__(self, environ, start_response):

        def add_cors_headers(status, headers, exc_info=None):
            headers = Headers(headers)
            headers.add("Access-Control-Allow-Origin", self.origin(environ))
            headers.add("Access-Control-Allow-Headers", "Origin, Content-Type")
            headers.add("Access-Control-Allow-Credentials", "true")
            headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
            headers.add("Access-Control-Expose-Headers", "X-Set-Cookie")
            return start_response(status, headers.to_list(), exc_info)

        if environ.get("REQUEST_METHOD") == "OPTIONS":
            add_cors_headers("200 Ok", [("Content-Type", "text/plain")])
            return ['200 Ok']

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
