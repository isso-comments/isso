# -*- encoding: utf-8 -*-

import html5lib

from html5lib.sanitizer import HTMLSanitizer
from html5lib.serializer import HTMLSerializer
from html5lib.treewalkers import getTreeWalker

import misaka


class MarkdownSanitizer(HTMLSanitizer):

    # attributes found in Sundown's HTML serializer [1] except for <img> tag,
    # because images are not generated anyways.
    #
    # [1] https://github.com/vmg/sundown/blob/master/html/html.c
    allowed_elements = ["a", "p", "hr", "br", "ol", "ul", "li",
                        "pre", "code", "blockquote",
                        "del", "ins", "strong", "em",
                        "h1", "h2", "h3", "h4", "h5", "h6",
                        "table", "thead", "tbody", "th", "td"]

    # href for <a> and align for <table>
    allowed_attributes = ["align", "href"]

    # remove disallowed tokens from the output
    def disallowed_token(self, token, token_type):
        return None


def sanitize(document):

    parser = html5lib.HTMLParser(tokenizer=MarkdownSanitizer)
    domtree = parser.parseFragment(document)

    stream = html5lib.treewalkers.getTreeWalker('etree')(domtree)
    serializer = HTMLSerializer(quote_attr_values=True, omit_optional_tags=False)

    return serializer.render(stream)


def markdown(text):
    """Convert Markdown to (safe) HTML.

    >>> markdown("*Ohai!*") # doctest: +IGNORE_UNICODE
    '<p><em>Ohai!</em></p>'
    >>> markdown("<em>Hi</em>") # doctest: +IGNORE_UNICODE
    '<p><em>Hi</em></p>'
    >>> markdown("<script>alert('Onoe')</script>") # doctest: +IGNORE_UNICODE
    "<p>alert('Onoe')</p>"
    >>> markdown("http://example.org/ and sms:+1234567890") # doctest: +IGNORE_UNICODE
    '<p><a href="http://example.org/">http://example.org/</a> and sms:+1234567890</p>'
    """

    # ~~strike through~~, sub script: 2^(nd) and http://example.org/ auto-link
    exts = misaka.EXT_STRIKETHROUGH | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK

    # remove HTML tags, skip <img> (for now) and only render "safe" protocols
    html = misaka.HTML_SKIP_STYLE | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK

    rv = misaka.html(text, extensions=exts, render_flags=html).rstrip("\n")
    if not rv.startswith("<p>") and not rv.endswith("</p>"):
        rv = "<p>" + rv + "</p>"

    return sanitize(rv)
