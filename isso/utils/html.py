# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
import html

import bleach
import misaka

from configparser import NoOptionError


class Sanitizer(object):

    def __init__(self, elements, attributes):
        # attributes found in Sundown's HTML serializer [1]
        # except for <img> tag,
        # because images are not generated anyways.
        #
        # [1] https://github.com/vmg/sundown/blob/master/html/html.c
        self.elements = ["a", "p", "hr", "br", "ol", "ul", "li",
                         "pre", "code", "blockquote",
                         "del", "ins", "strong", "em",
                         "h1", "h2", "h3", "h4", "h5", "h6",
                         "table", "thead", "tbody", "th", "td"] + elements

        # href for <a> and align for <table>
        self.attributes = ["align", "href"] + attributes

    def sanitize(self, text):
        clean_html = bleach.clean(text, tags=self.elements, attributes=self.attributes, strip=True)

        def set_links(attrs, new=False):
            href_key = (None, u'href')

            if href_key not in attrs:
                return attrs
            if attrs[href_key].startswith(u'mailto:'):
                return attrs

            rel_key = (None, u'rel')
            rel_values = [val for val in attrs.get(rel_key, u'').split(u' ') if val]

            for value in [u'nofollow', u'noopener']:
                if value not in [rel_val.lower() for rel_val in rel_values]:
                    rel_values.append(value)

            attrs[rel_key] = u' '.join(rel_values)
            return attrs

        linker = bleach.linkifier.Linker(callbacks=[set_links])
        return linker.linkify(clean_html)


def Markdown(extensions=("strikethrough", "superscript", "autolink",
                         "fenced-code"), flags=[]):

    renderer = Unofficial(flags=flags)
    md = misaka.Markdown(renderer, extensions=extensions)

    def inner(text):
        rv = md(text).rstrip("\n")
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

    def blockcode(self, text, lang):
        lang = ' class="{0}"'.format(html.escape(lang)) if lang else ''
        return "<pre><code{1}>{0}</code></pre>\n".format(html.escape(text, False), lang)


class Markup(object):

    def __init__(self, conf):

        try:
            conf_flags = conf.getlist("flags")
        except NoOptionError:
            conf_flags = []
        parser = Markdown(extensions=conf.getlist("options"), flags=conf_flags)
        sanitizer = Sanitizer(
            conf.getlist("allowed-elements"),
            conf.getlist("allowed-attributes"))

        self._render = lambda text: sanitizer.sanitize(parser(text))

    def render(self, text):
        return self._render(text)
