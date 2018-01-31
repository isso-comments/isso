
from __future__ import unicode_literals

import unittest

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso.wsgi import CORSMiddleware, origin


def hello_world(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["Hello, World."]


class CORSTest(unittest.TestCase):

    def test_simple(self):

        app = CORSMiddleware(hello_world,
                             origin=origin([
                                 "https://example.tld/",
                                 "http://example.tld/",
                             ]),
                             allowed=("Foo", "Bar"), exposed=("Spam", ))

        client = Client(app, Response)

        rv = client.get("/", headers={"Origin": "https://example.tld"})

        self.assertEqual(
            rv.headers["Access-Control-Allow-Origin"], "https://example.tld")
        self.assertEqual(
            rv.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(
            rv.headers["Access-Control-Allow-Methods"], "HEAD, GET, POST, PUT, DELETE")
        self.assertEqual(
            rv.headers["Access-Control-Allow-Headers"], "Foo, Bar")
        self.assertEqual(rv.headers["Access-Control-Expose-Headers"], "Spam")

        a = client.get("/", headers={"Origin": "http://example.tld"})
        self.assertEqual(
            a.headers["Access-Control-Allow-Origin"], "http://example.tld")

        b = client.get("/", headers={"Origin": "http://example.tld"})
        self.assertEqual(
            b.headers["Access-Control-Allow-Origin"], "http://example.tld")

        c = client.get("/", headers={"Origin": "http://foo.other"})
        self.assertEqual(
            c.headers["Access-Control-Allow-Origin"], "https://example.tld")

    def test_preflight(self):

        app = CORSMiddleware(hello_world, origin=origin(["http://example.tld"]),
                             allowed=("Foo", ), exposed=("Bar", ))
        client = Client(app, Response)

        rv = client.open(method="OPTIONS", path="/",
                         headers={"Origin": "http://example.tld"})
        self.assertEqual(rv.status_code, 200)

        for hdr in ("Origin", "Headers", "Credentials", "Methods"):
            self.assertIn("Access-Control-Allow-%s" % hdr, rv.headers)

        self.assertEqual(
            rv.headers["Access-Control-Allow-Origin"], "http://example.tld")
