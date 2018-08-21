# -*- encoding: utf-8 -*-

import unittest
import io

from isso import config


class TestConfig(unittest.TestCase):

    def test_parser(self):

        parser = config.IssoParser(allow_no_value=True)
        parser.read_file(io.StringIO(u"""
            [foo]
            bar = 1h
            baz = 12
            spam = a, b, cdef
            bla =
                spam
                ham
            asd = fgh"""))

        self.assertEqual(parser.getint("foo", "bar"), 3600)
        self.assertEqual(parser.getint("foo", "baz"), 12)
        self.assertEqual(parser.getlist("foo", "spam"), ['a', 'b', 'cdef'])
        self.assertEqual(list(parser.getiter("foo", "bla")), ['spam', 'ham'])
        self.assertEqual(list(parser.getiter("foo", "asd")), ['fgh'])

    def test_smtp(self):

        cases = [
            ('"abc" <def@example.org>',     '"abc" <def@example.org>'),
            ('abc <def@example.org>',       'abc <def@example.org>'),
            ('"abc def" <def@example.org>', '"abc def" <def@example.org>'),
            ('abc def <def@example.org>',   'abc def <def@example.org>'),
            ('def@example.org',             'Ich schrei sonst! <def@example.org>'),
            ('"abc" def@example.org',       ''),
            ('"abc"',                       ''),
            ('abc',                         ''),
        ]

        for (config_value, expected) in cases:
            parser = config.IssoParser(allow_no_value=True)
            parser.read_file(io.StringIO(u"""
                [smtp]
                from = """ + config_value))

            self.assertEqual(parser.get("smtp", "from"), expected)
