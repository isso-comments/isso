
from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso.wsgi import CORSMiddleware
from isso.utils import origin


def hello_world(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["Hello, World."]


class CORSTest(unittest.TestCase):

    def test_simple(self):

        app = CORSMiddleware(hello_world, origin=origin([
            "https://example.tld/",
            "http://example.tld/",
            "http://example.tld",
        ]))

        client = Client(app, Response)

        rv = client.get("/", headers={"ORIGIN": "https://example.tld"})

        self.assertEqual(rv.headers["Access-Control-Allow-Origin"], "https://example.tld")
        self.assertEqual(rv.headers["Access-Control-Allow-Headers"], "Origin, Content-Type")
        self.assertEqual(rv.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(rv.headers["Access-Control-Allow-Methods"], "GET, POST, PUT, DELETE")
        self.assertEqual(rv.headers["Access-Control-Expose-Headers"], "X-Set-Cookie")

        a = client.get("/", headers={"ORIGIN": "http://example.tld"})
        self.assertEqual(a.headers["Access-Control-Allow-Origin"], "http://example.tld")

        b = client.get("/", headers={"ORIGIN": "http://example.tld"})
        self.assertEqual(b.headers["Access-Control-Allow-Origin"], "http://example.tld")

        c = client.get("/", headers={"ORIGIN": "http://foo.other"})
        self.assertEqual(c.headers["Access-Control-Allow-Origin"], "https://example.tld")


    def test_preflight(self):

        app = CORSMiddleware(hello_world, origin=origin(["http://example.tld"]))
        client = Client(app, Response)

        rv = client.open(method="OPTIONS", path="/", headers={"ORIGIN": "http://example.tld"})
        self.assertEqual(rv.status_code, 200)

        for hdr in ("Origin", "Headers", "Credentials", "Methods"):
            self.assertIn("Access-Control-Allow-%s" % hdr, rv.headers)

        self.assertEqual(rv.headers["Access-Control-Allow-Origin"], "http://example.tld")
