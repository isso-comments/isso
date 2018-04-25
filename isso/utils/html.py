# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import operator
import pkg_resources

from distutils.version import LooseVersion as Version

HTML5LIB_VERSION = Version(pkg_resources.get_distribution("html5lib").version)
HTML5LIB_SIMPLETREE = Version("0.95")

from isso.compat import reduce

import html5lib
from html5lib.sanitizer import HTMLSanitizer
from html5lib.serializer import HTMLSerializer

import misaka


def Sanitizer(elements, attributes):

    class Inner(HTMLSanitizer):

        # attributes found in Sundown's HTML serializer [1] except for <img> tag,
        # because images are not generated anyways.
        #
        # [1] https://github.com/vmg/sundown/blob/master/html/html.c
        allowed_elements = ["a", "p", "hr", "br", "ol", "ul", "li",
                            "pre", "code", "blockquote",
                            "del", "ins", "strong", "em",
                            "h1", "h2", "h3", "h4", "h5", "h6",
                            "table", "thead", "tbody", "th", "td"] + elements

        # href for <a> and align for <table>
        allowed_attributes = ["align", "href"] + attributes

        # remove disallowed tokens from the output
        def disallowed_token(self, token, token_type):
            return None

    return Inner


def sanitize(tokenizer, document):

    parser = html5lib.HTMLParser(tokenizer=tokenizer)
    domtree = parser.parseFragment(document)

    if HTML5LIB_VERSION > HTML5LIB_SIMPLETREE:
        builder = "etree"

        for link in domtree.findall(".//{http://www.w3.org/1999/xhtml}a"):
            if link.get('href', None):
                link.set("rel", "nofollow noopener")

    else:
        builder = "simpletree"

    stream = html5lib.treewalkers.getTreeWalker(builder)(domtree)
    serializer = HTMLSerializer(
        quote_attr_values=True, omit_optional_tags=False)

    return serializer.render(stream)


def Markdown(extensions=("strikethrough", "superscript", "autolink")):

    flags = reduce(operator.xor, map(
        lambda ext: getattr(misaka, 'EXT_' + ext.upper()), extensions), 0)
    md = misaka.Markdown(Unofficial(), extensions=flags)

    def inner(text):
        rv = md.render(text).rstrip("\n")
        if rv.startswith("<p>") or rv.endswith("</p>"):
            return rv
        return "<p>" + rv + "</p>"

    return inner


class Unofficial(misaka.HtmlRenderer):
    """A few modifications to process "common" Markdown.

    For instance, fenced code blocks (~~~ or ```) are just wrapped in <code>
    which does not preserve line breaks. If a language is given, it is added
    to <code class="$lang">, compatible with Highlight.js.
    """

    def block_code(self, text, lang):
        lang = ' class="{0}"'.format(lang) if lang else ''
        return "<pre><code{1}>{0}</code></pre>\n".format(text, lang)


class Markup(object):

    def __init__(self, conf):

        parser = Markdown(conf.getlist("options"))
        sanitizer = Sanitizer(
            conf.getlist("allowed-elements"),
            conf.getlist("allowed-attributes"))

        self._render = lambda text: sanitize(sanitizer, parser(text))

    def render(self, text):
        return self._render(text)
