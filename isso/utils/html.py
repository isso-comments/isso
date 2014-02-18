# -*- encoding: utf-8 -*-

import pkg_resources
import operator

from isso.compat import reduce

import html5lib
html5lib_version = pkg_resources.get_distribution("html5lib").version

from html5lib.sanitizer import HTMLSanitizer
from html5lib.serializer import HTMLSerializer
from html5lib.treewalkers import getTreeWalker

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

    builder = "simpletree" if html5lib_version == "0.95" else "etree"
    stream = html5lib.treewalkers.getTreeWalker(builder)(domtree)
    serializer = HTMLSerializer(quote_attr_values=True, omit_optional_tags=False)

    return serializer.render(stream)


def Markdown(extensions=("strikethrough", "superscript", "autolink")):

    flags = reduce(operator.xor, map(
        lambda ext: getattr(misaka, 'EXT_' + ext.upper()), extensions), 0)

    def inner(text):
        rv = misaka.html(text, extensions=flags).rstrip("\n")
        if not rv.endswith("<p>") and not rv.endswith("</p>"):
            return "<p>" + rv + "</p>"
        return rv

    return inner


class Markup(object):

    def __init__(self, conf):

        parser = Markdown(conf.getlist("options"))
        sanitizer = Sanitizer(
            conf.getlist("allowed-elements"),
            conf.getlist("allowed-attributes"))

        self._render = lambda text: sanitize(sanitizer, parser(text))

    def render(self, text):
        return self._render(text)
