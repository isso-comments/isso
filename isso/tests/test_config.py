# -*- encoding: utf-8 -*-

import unittest
import io
import os

from isso import config


class TestConfig(unittest.TestCase):

    def test_parser(self):

        parser = config.IssoParser()
        parser.read_file(io.StringIO("""
            [foo]
            bar = 1h
            baz = 12
            spam = a, b, cdef
            bla =
                spam
                ham
            asd = fgh
            password = %s%%foo"""))

        self.assertEqual(parser.getint("foo", "bar"), 3600)
        self.assertEqual(parser.getint("foo", "baz"), 12)
        self.assertEqual(parser.getlist("foo", "spam"), ['a', 'b', 'cdef'])
        self.assertEqual(list(parser.getiter("foo", "bla")), ['spam', 'ham'])
        self.assertEqual(list(parser.getiter("foo", "asd")), ['fgh'])

        # Strings containing '%' should not be python-interpolated
        self.assertEqual(parser.get("foo", "password"), '%s%%foo')

        # Section.get() should function the same way as plain IssoParser
        foosection = parser.section("foo")
        self.assertEqual(foosection.get("password"), '%s%%foo')

    def test_parser_with_environment_variables(self):

        parser = config.IssoParser()
        parser.read_file(io.StringIO("""
            [foo]
            bar = $TEST_ENV_VAR
            baz = ${TEST_ENV_VAR2}
        """))

        # Set environment variables
        os.environ['TEST_ENV_VAR'] = 'test_value'
        os.environ['TEST_ENV_VAR2'] = 'another_test_value'

        # Test environment variable expansion
        self.assertEqual(parser.get("foo", "bar"), 'test_value')
        self.assertEqual(parser.get("foo", "baz"), 'another_test_value')

        # Test Section.get() with environment variables
        foosection = parser.section("foo")
        self.assertEqual(foosection.get("bar"), 'test_value')
        self.assertEqual(foosection.get("baz"), 'another_test_value')

        # Clean up environment variables
        del os.environ['TEST_ENV_VAR']
        del os.environ['TEST_ENV_VAR2']

    def test_parser_with_missing_environment_variables(self):

        parser = config.IssoParser()
        parser.read_file(io.StringIO("""
            [foo]
            bar = $MISSING_ENV_VAR
        """))

        self.assertEqual(parser.get("foo", "bar"), '$MISSING_ENV_VAR')

    def test_parser_with_special_characters_in_environment_variables(self):

        os.environ['SPECIAL_ENV_VAR'] = 'value_with_$pecial_characters'
        parser = config.IssoParser()
        parser.read_file(io.StringIO("""
            [foo]
            bar = $SPECIAL_ENV_VAR
        """))

        self.assertEqual(parser.get("foo", "bar"), 'value_with_$pecial_characters')
        del os.environ['SPECIAL_ENV_VAR']
