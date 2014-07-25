# -*- encoding: utf-8 -*-

import unittest

import itsdangerous

from isso import utils
from isso.utils import parse


class TestUtils(unittest.TestCase):

    def test_anonymize(self):

        examples = [
            (u'12.34.56.78', u'12.34.56.0'),
            (u'1234:5678:90ab:cdef:fedc:ba09:8765:4321', u'1234:5678:90ab:0000:0000:0000:0000:0000'),
            (u'::ffff:127.0.0.1', u'127.0.0.0')]

        for (addr, anonymized) in examples:
            self.assertEqual(utils.anonymize(addr), anonymized)


class TestURLSafeTimedSerializer(unittest.TestCase):

    def test_serializer(self):
        signer = utils.URLSafeTimedSerializer("")
        payload = [1, "x" * 1024]
        self.assertEqual(signer.loads(signer.dumps(payload)), payload)

    def test_nocompression(self):
        plain = utils.URLSafeTimedSerializer("")
        zlib = itsdangerous.URLSafeTimedSerializer("")

        payload = "x" * 1024
        self.assertTrue(zlib.dumps(payload).startswith("."))
        self.assertNotEqual(plain.dumps(payload), zlib.dumps(payload))


class TestParse(unittest.TestCase):

    def test_thread(self):
        self.assertEqual(parse.thread("asdf"), (None, 'Untitled.'))

        self.assertEqual(parse.thread("""
            <html>
            <head>
                <title>Foo!</title>
            </head>
            <body>
                <header>
                    <h1>generic website title.</h1>
                    <h2>subtile title.</h2>
                </header>
                <article>
                    <header>
                        <h1>Can you find me?</h1>
                    </header>
                    <section id="isso-thread">
                    </section>
                </article>
            </body>
            </html>"""), (None, 'Can you find me?'))

        self.assertEqual(parse.thread("""
            <html>
            <body>
            <h1>I'm the real title!1
            <section data-title="No way%21" id="isso-thread">
            """), (None, 'No way!'))

        self.assertEqual(parse.thread("""
            <section id="isso-thread" data-title="Test" data-isso-id="test">
            """), ('test', 'Test'))

        self.assertEqual(parse.thread('<section id="isso-thread" data-isso-id="Fuu.">'),
                                      ('Fuu.', 'Untitled.'))
