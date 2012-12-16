#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import os
import re
import cgi
import wsgiref
import tempfile
import urlparse
import mimetypes

from time import gmtime, mktime, strftime, strptime, timezone
from email.utils import parsedate
from os.path import join, dirname, abspath

from urllib import quote
from Cookie import SimpleCookie
from SocketServer import ThreadingMixIn
from wsgiref.simple_server import WSGIServer


class Request(object):

    def __init__(self, environ):

        # from bottle.py Copyright 2012, Marcel Hellkamp, License: MIT.
        maxread = max(0, int(environ['CONTENT_LENGTH'] or '0'))
        stream = environ['wsgi.input']
        body = tempfile.TemporaryFile(mode='w+b')
        while maxread > 0:
            part = stream.read(maxread)
            if not part:
                break
            body.write(part)
            maxread -= len(part)

        self.body = body
        self.body.seek(0)
        self.environ = environ
        self.query_string = self.environ['QUERY_STRING']

    @property
    def data(self):
        self.body.seek(0)
        return self.body.read()

    @property
    def method(self):
        return self.environ['REQUEST_METHOD']

    @property
    def args(self):
        return urlparse.parse_qs(self.environ['QUERY_STRING'])

    @property
    def form(self):
        if self.environ['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            return cgi.FieldStorage(fp=self.body, environ=self.environ)
        return dict()

    @property
    def cookies(self):
        cookie = SimpleCookie(self.environ.get('HTTP_COOKIE', ''))
        return {v.key: v.value for v in cookie.values()}


class Rule(str):

    repl = {'int': r'[0-9]+', 'float': r'\-?[0-9]+\.[0-9]+'}

    def __init__(self, string):

        first, last, rv = 0, -1, []
        f = lambda m: '(?P<%s>%s)' % (m.group(2), self.repl.get(m.group(1), m.group(1)))

        for i, c in enumerate(string):
            if c == '<':
                first = i
                rv.append(re.escape(string[last+1:first]))
            if c == '>':
                last = i
            if last > first:
                rv.append(re.sub(r'<\(([^:]+)\):(\w+)>', f, string[first:last+1]))
                first = last

        rv.append(re.escape(string[last+1:]))
        self.rule = re.compile('^' + ''.join(rv) + '$')

    def match(self, obj):

        match = re.match(self.rule, obj)
        if not match: return

        kwargs = match.groupdict()
        for key, value in kwargs.items():
            for type in int, float:
                try:
                    kwargs[key] = type(value)
                    break
                except ValueError:
                    pass

        return kwargs


def sendfile(filename, root, environ):

    headers = {}
    root = abspath(root) + os.sep
    filename = abspath(join(root, filename.strip('/\\')))

    if not filename.startswith(root):
        return 403, '', headers

    mimetype, encoding = mimetypes.guess_type(filename)
    if mimetype: headers['Content-Type'] = mimetype
    if encoding: headers['Content-Encoding'] = encoding

    stats = os.stat(filename)
    headers['Content-Length'] = str(stats.st_size)
    headers['Last-Modified'] = strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime(stats.st_mtime))

    ims = environ.get('HTTP_IF_MODIFIED_SINCE')
    if ims:
        ims = parsedate(ims)

    if ims is not None and mktime(ims) - timezone >= stats.st_mtime:
        headers['Date'] = strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())
        return 304, '', headers

    return 200, io.open(filename, 'rb'), headers


def static(app, environ, request, directory, path):

    try:
        return sendfile(path, join(dirname(__file__), directory), environ)
    except (OSError, IOError):
        return 404, '', {}


def setcookie(name, value, **kwargs):
    return '; '.join([quote(name, '') + '=' + quote(value, '')] +
        [k.replace('_', '-') + '=' + str(v) for k, v in kwargs.iteritems()])


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    pass
