# -*- encoding: utf-8 -*-

import json
import unittest

from werkzeug.exceptions import BadRequest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request

from isso import error_handler, wsgi
from isso.utils import JSONResponse


class TestWSGIUtilities(unittest.TestCase):

    def test_urlsplit(self):

        examples = [
            ("http://example.tld/", ('example.tld', 80, False)),
            ("https://example.tld/", ('example.tld', 443, True)),
            ("example.tld", ('example.tld', 80, False)),
            ("example.tld:42", ('example.tld', 42, False)),
            ("https://example.tld:80/", ('example.tld', 80, True))]

        for (hostname, result) in examples:
            self.assertEqual(wsgi.urlsplit(hostname), result)

    def test_urljoin(self):

        examples = [
            (("example.tld", 80, False), "http://example.tld"),
            (("example.tld", 42, True), "https://example.tld:42"),
            (("example.tld", 443, True), "https://example.tld")]

        for (split, result) in examples:
            self.assertEqual(wsgi.urljoin(*split), result)

    def test_origin(self):

        self.assertEqual(wsgi.origin([])({}), "http://invalid.local")

        origin = wsgi.origin(["http://foo.bar/", "https://foo.bar"])
        self.assertEqual(origin({"HTTP_ORIGIN": "http://foo.bar"}),
                         "http://foo.bar")
        self.assertEqual(origin({"HTTP_ORIGIN": "https://foo.bar"}),
                         "https://foo.bar")
        self.assertEqual(origin({"HTTP_REFERER": "http://foo.bar"}),
                         "http://foo.bar")
        self.assertEqual(origin({"HTTP_ORIGIN": "http://spam.baz"}),
                         "http://foo.bar")
        self.assertEqual(origin({}), "http://foo.bar")

    def test_errorhandler(self):
        """
        Test out MIME type accept parsing:

        >>> from werkzeug.datastructures import MIMEAccept
        >>> a = MIMEAccept([('text/html', 0.5), ('application/json', 1),])
        >>> a.best
        'application/json'
        """

        # Client prefers response with `text/html` MIME type
        env = create_environ(headers=((
            'Accept', 'text/html, application/xml;q=0.9'),
        ))
        req = Request(env)
        error = BadRequest
        # Error is simply passed through
        self.assertEqual(error_handler(env, req, error), BadRequest)

        # Client prefers response with `application/json` MIME type
        env = create_environ(headers=((
            'Accept', 'text/html;q=0.7, application/json;q=0.9, */*;q=0.8'),
        ))
        req = Request(env)
        error = BadRequest('invalid data')
        self.assertEqual(req.accept_mimetypes.best, "application/json")
        # Error is converted to JSONResponse
        self.assertIsInstance(error_handler(env, req, error), JSONResponse)
        # Error code is retained by JSONResponse
        self.assertEqual(error_handler(env, req, error).status_code, 400)

        # Missing error codes get converted to 500
        error.code = None
        self.assertEqual(json.loads(
            error_handler(env, req, error).response[0])['message'],
            '??? Unknown Error: invalid data'
        )
        self.assertEqual(error_handler(env, req, error).status_code, 500)

        # Request's accept_mimetypes.best should always return, even if no
        # Accept MimeTypes supplied
        env = create_environ()
        req = Request(env)
        self.assertEqual(req.accept_mimetypes.best, None)
