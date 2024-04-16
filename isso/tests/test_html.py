# -*- encoding: utf-8 -*-

import unittest

from isso import config, html
from isso.html import Sanitizer


class TestHTML(unittest.TestCase):
    def test_sanitizer(self):
        sanitizer = Sanitizer(elements=["p", "a", "code"], attributes=["href"])
        examples = [
            ('Look: <img src="..." />', "Look: "),
            (
                '<a href="http://example.org/">Ha</a>',
                [
                    '<a href="http://example.org/" rel="nofollow noopener">Ha</a>',
                    '<a rel="nofollow noopener" href="http://example.org/">Ha</a>',
                ],
            ),
            ('<a href="sms:+1234567890">Ha</a>', "<a>Ha</a>"),
            ("ld.so", "ld.so"),
            ("/usr/lib/x86_64-linux-gnu/libc/memcpy-preload.so", "/usr/lib/x86_64-linux-gnu/libc/memcpy-preload.so"),
            ('<p style="visibility: hidden;">Test</p>', "<p>Test</p>"),
            ('<code class="language-cpp">Test</code>', '<code class="language-cpp">Test</code>'),
            ('<code class="test language-cpp">Test</code>', "<code>Test</code>"),
            ('<script>alert("Onoe")</script>', 'alert("Onoe")'),
        ]

        for markup, expected in examples:
            if isinstance(expected, list):
                self.assertIn(sanitizer.sanitize(markup), expected)
            else:
                self.assertEqual(sanitizer.sanitize(markup), expected)

    def test_sanitizer_extensions(self):
        sanitizer = Sanitizer(elements=["img"], attributes=["src"])
        examples = [('<img src="cat.gif" />', '<img src="cat.gif">'), ('<script src="doge.js"></script>', "")]

        for element, expected in examples:
            self.assertEqual(sanitizer.sanitize(element), expected)

    @staticmethod
    def _markup_conf(mistune_plugins="", **markup_options):
        """Build a full config (as passed to `html.Markup`, i.e. *not*
        pre-sectioned) with the given options merged into [markup]. Renders
        with Mistune, which also needs a [markup.mistune] section; pass
        `mistune_plugins` (e.g. "url") to enable Mistune plugins."""
        options = {"renderer": "mistune", "allowed-attributes": ""}
        options.update(markup_options)
        return config.new(
            {
                "markup": options,
                "markup.mistune": {"plugins": mistune_plugins, "parameters": ""},
            }
        )

    def test_render(self):
        conf = self._markup_conf(mistune_plugins="url", **{"allowed-elements": "a, p", "allowed-attributes": "href"})
        renderer = html.Markup(conf).render
        self.assertIn(
            renderer("http://example.org/ and sms:+1234567890"),
            [
                '<p><a href="http://example.org/" rel="nofollow noopener">http://example.org/</a> and sms:+1234567890</p>',
                '<p><a rel="nofollow noopener" href="http://example.org/">http://example.org/</a> and sms:+1234567890</p>',
            ],
        )

    def test_render_with_allowed_html_elements(self):
        conf = self._markup_conf(**{"allowed-elements": "a, p", "allowed-html-elements": "p", "allowed-attributes": "href"})
        renderer = html.Markup(conf).render
        self.assertEqual(renderer("http://example.org/ and sms:+1234567890"), "<p>http://example.org/ and sms:+1234567890</p>")

    def test_render_allowed_elements_missing_defaults_to_builtin_list(self):
        """Neither `allowed-elements` nor `allowed-html-elements` is set: the
        built-in element list still applies and nothing crashes."""
        conf = self._markup_conf()
        renderer = html.Markup(conf).render
        self.assertEqual(renderer("plain text"), "<p>plain text</p>")

    def test_render_allowed_html_elements_missing_falls_back_to_allowed_elements(self):
        """`allowed-html-elements` absent from the config file entirely (not
        just empty) should not crash, and `allowed-elements` still applies."""
        conf = self._markup_conf(**{"allowed-elements": "img", "allowed-attributes": ""})
        renderer = html.Markup(conf).render
        # Mistune escapes raw HTML, so exercise the `img` element through a
        # Markdown image rather than a literal <img> tag.
        self.assertEqual(renderer("![](cat.gif)"), '<p><img src="cat.gif"></p>')

    def test_render_merges_allowed_elements_into_allowed_html_elements(self):
        """When both options are set, `allowed-elements` is added on top of
        `allowed-html-elements`, and a deprecation warning is logged."""
        conf = self._markup_conf(
            mistune_plugins="url", **{"allowed-html-elements": "p", "allowed-elements": "a, p", "allowed-attributes": "href"}
        )

        with self.assertLogs("isso", level="WARNING") as cm:
            markup = html.Markup(conf)

        self.assertTrue(any("allowed-elements" in message and "deprecated" in message for message in cm.output))
        self.assertIn(
            markup.render("http://example.org/ and plain"),
            [
                '<p><a href="http://example.org/" rel="nofollow noopener">http://example.org/</a> and plain</p>',
                '<p><a rel="nofollow noopener" href="http://example.org/">http://example.org/</a> and plain</p>',
            ],
        )

    def test_render_no_warning_when_allowed_elements_already_covered(self):
        """No new elements are merged in, so no deprecation warning is logged."""
        conf = self._markup_conf(**{"allowed-html-elements": "a, p", "allowed-elements": "a", "allowed-attributes": "href"})

        with self.assertNoLogs("isso", level="WARNING"):
            html.Markup(conf)
