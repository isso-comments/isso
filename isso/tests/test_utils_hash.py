# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso import config

from isso.utils.hash import Hash, PBKDF2, new


class TestHasher(unittest.TestCase):

    def test_hash(self):
        self.assertRaises(TypeError, Hash, "Foo")

        self.assertEqual(Hash(b"").salt, b"")
        self.assertEqual(Hash().salt, Hash.salt)

        h = Hash(b"", func=None)

        self.assertRaises(TypeError, h.hash, "...")
        self.assertEqual(h.hash(b"..."), b"...")
        self.assertIsInstance(h.uhash(u"..."), (str, ))

    def test_uhash(self):
        h = Hash(b"", func=None)
        self.assertRaises(TypeError, h.uhash, b"...")


class TestPBKDF2(unittest.TestCase):

    def test_default(self):
        # original setting (and still default)
        pbkdf2 = PBKDF2(iterations=1000)
        self.assertEqual(pbkdf2.uhash(""), "42476aafe2e4")

    def test_different_salt(self):
        a = PBKDF2(b"a", iterations=1)
        b = PBKDF2(b"b", iterations=1)
        self.assertNotEqual(a.hash(b""), b.hash(b""))


class TestCreate(unittest.TestCase):

    def test_custom(self):

        def _new(val):
            conf = config.new({
                "hash": {
                    "algorithm": val,
                    "salt": ""
                }
            })
            return new(conf.section("hash"))

        sha1 = _new("sha1")
        self.assertIsInstance(sha1, Hash)
        self.assertEqual(sha1.func, "sha1")
        self.assertRaises(ValueError, _new, "foo")

        pbkdf2 = _new("pbkdf2:16")
        self.assertIsInstance(pbkdf2, PBKDF2)
        self.assertEqual(pbkdf2.iterations, 16)

        pbkdf2 = _new("pbkdf2:16:2:md5")
        self.assertIsInstance(pbkdf2, PBKDF2)
        self.assertEqual(pbkdf2.dklen, 2)
        self.assertEqual(pbkdf2.func, "md5")
