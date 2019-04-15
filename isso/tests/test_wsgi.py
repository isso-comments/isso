# -*- encoding: utf-8 -*-

import unittest

from isso import wsgi


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
