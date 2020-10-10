# -*- encoding: utf-8 -*-

import unittest
import textwrap

from isso import config
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
        convert = html.Markdown(extensions=("fenced-code", ))

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

    def test_sanitizer(self):
        sanitizer = html.Sanitizer(elements=[], attributes=[])
        examples = [
            ('Look: <img src="..." />', 'Look: '),
            ('<a href="http://example.org/">Ha</a>',
             ['<a href="http://example.org/" rel="nofollow noopener">Ha</a>',
              '<a rel="nofollow noopener" href="http://example.org/">Ha</a>']),
            ('<a href="sms:+1234567890">Ha</a>', '<a>Ha</a>'),
            ('<p style="visibility: hidden;">Test</p>', '<p>Test</p>'),
            ('<script>alert("Onoe")</script>', 'alert("Onoe")')]

        for (input, expected) in examples:
            if isinstance(expected, list):
                self.assertIn(sanitizer.sanitize(input), expected)
            else:
                self.assertEqual(sanitizer.sanitize(input), expected)

    def test_sanitizer_extensions(self):
        sanitizer = html.Sanitizer(elements=["img"], attributes=["src"])
        examples = [
            ('<img src="cat.gif" />', '<img src="cat.gif">'),
            ('<script src="doge.js"></script>', '')]

        for (input, expected) in examples:
            self.assertEqual(sanitizer.sanitize(input), expected)

    def test_render(self):
        conf = config.new({
            "markup": {
                "options": "autolink",
                "flags": "",
                "allowed-elements": "",
                "allowed-attributes": ""
            }
        })
        renderer = html.Markup(conf.section("markup")).render
        self.assertIn(renderer("http://example.org/ and sms:+1234567890"),
                      ['<p><a href="http://example.org/" rel="nofollow noopener">http://example.org/</a> and sms:+1234567890</p>',
                       '<p><a rel="nofollow noopener" href="http://example.org/">http://example.org/</a> and sms:+1234567890</p>'])

    def test_code_blocks(self):
        convert = html.Markdown(extensions=('fenced-code',))
        examples = [
            ("```\nThis is a code-fence. <hello>\n```", "<p><pre><code>This is a code-fence. &lt;hello&gt;\n</code></pre></p>"),
            ("```c++\nThis is a code-fence. <hello>\n```", "<p><pre><code class=\"c++\">This is a code-fence. &lt;hello&gt;\n</code></pre></p>"),
            ("    This is a four-character indent. <hello>", "<p><pre><code>This is a four-character indent. &lt;hello&gt;\n</code></pre></p>")]

        for (input, expected) in examples:
            self.assertEqual(convert(input), expected)
