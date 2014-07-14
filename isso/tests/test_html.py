# -*- encoding: utf-8 -*-

import textwrap
import unittest

from isso.utils import html


class TestHTML(unittest.TestCase):

    def test_markdown(self):
        convert = html.Markdown(extensions=())
        examples = [
            ("*Ohai!*", "<p><em>Ohai!</em></p>"),
            ("<em>Hi</em>", "<p><em>Hi</em></p>"),
            ("http://example.org/", '<p>http://example.org/</p>')]

        for (input, expected) in examples:
            self.assertEqual(convert(input), expected)

    def test_markdown_extensions(self):
        convert = html.Markdown(extensions=("strikethrough", "superscript"))
        examples = [
            ("~~strike~~ through", "<p><del>strike</del> through</p>"),
            ("sup^(script)", "<p>sup<sup>script</sup></p>")]

        for (input, expected) in examples:
            self.assertEqual(convert(input), expected)

    def test_github_flavoured_markdown(self):
        convert = html.Markdown(extensions=("fenced_code", ))

        # without lang
        _in = textwrap.dedent("""\
            Hello, World

            ```
            #!/usr/bin/env python
            print("Hello, World")""")
        _out = textwrap.dedent("""\
            <p>Hello, World</p>
            <pre><code>#!/usr/bin/env python
            print("Hello, World")
            </code></pre>""")

        self.assertEqual(convert(_in), _out)

        # w/ lang
        _in = textwrap.dedent("""\
            Hello, World

            ```python
            #!/usr/bin/env python
            print("Hello, World")""")
        _out = textwrap.dedent("""\
            <p>Hello, World</p>
            <pre><code class="python">#!/usr/bin/env python
            print("Hello, World")
            </code></pre>""")

    @unittest.skipIf(html.html5lib_version == "0.95", "backport")
    def test_sanitizer(self):
        sanitizer = html.Sanitizer(elements=[], attributes=[])
        examples = [
            ('Look: <img src="..." />', 'Look: '),
            ('<a href="http://example.org/">Ha</a>', '<a href="http://example.org/">Ha</a>'),
            ('<a href="sms:+1234567890">Ha</a>', '<a>Ha</a>'),
            ('<p style="visibility: hidden;">Test</p>', '<p>Test</p>'),
            ('<script>alert("Onoe")</script>', 'alert("Onoe")')]

        for (input, expected) in examples:
            self.assertEqual(html.sanitize(sanitizer, input), expected)

    @unittest.skipIf(html.html5lib_version == "0.95", "backport")
    def test_sanitizer_extensions(self):
        sanitizer = html.Sanitizer(elements=["img"], attributes=["src"])
        examples = [
            ('<img src="cat.gif" />', '<img src="cat.gif">'),
            ('<script src="doge.js"></script>', '')]

        for (input, expected) in examples:
            self.assertEqual(html.sanitize(sanitizer, input), expected)

    def test_render(self):
        renderer = html.Markup(["autolink", ]).render
        self.assertEqual(renderer("http://example.org/ and sms:+1234567890"),
                         '<p><a href="http://example.org/">http://example.org/</a> and sms:+1234567890</p>')
