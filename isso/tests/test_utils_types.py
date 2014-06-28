# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso.compat import string_types
from isso.utils import types


class TestTypes(unittest.TestCase):

    def test_require(self):

        try:
            types.require("foo", string_types)
        except TypeError:
            self.assertTrue(False)

    def test_require_raises(self):

        self.assertRaises(TypeError, types.require, 1, bool)
        self.assertRaises(TypeError, types.require, 1, str)

