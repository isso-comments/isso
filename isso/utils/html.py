# -*- encoding: utf-8 -*-

import html
import re

import bleach
import misaka


class Sanitizer(object):

    # pattern to match a valid class attribute for code tags
    code_language_pattern = re.compile(r"^language-[a-zA-Z0-9]{1,20}$")

    @staticmethod
    def allow_attribute_class(tag, name, value):
        return name == "class" and bool(Sanitizer.code_language_pattern.match(value))

    def __init__(self, elements, attributes):
        self.elements = elements

        # allowed attributes for tags
        self.attributes = {
            "table": ["align"],
            "a": ["href"],
            "code": Sanitizer.allow_attribute_class,
            "*": attributes
        }

    def sanitize(self, text):
        clean_html = bleach.clean(text, tags=self.elements, attributes=self.attributes, strip=True)

        def set_links(attrs, new=False):
            # Linker can misinterpret text as a domain name and create new invalid links.
            # To prevent this, we only allow existing links to be modified.
            if new:
                return None

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


def Markdown(extensions=("autolink", "fenced-code", "no-intra-emphasis",
                         "strikethrough", "superscript"), flags=[]):

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
    to <code class="language-$lang">, compatible with Highlight.js.
    """

    def blockcode(self, text, lang):
        lang = ' class="language-{0}"'.format(html.escape(lang)) if lang else ''
        return "<pre><code{1}>{0}</code></pre>\n".format(html.escape(text, False), lang)


class Markup(object):

    def __init__(self, conf):
        self.flags = conf.getlist("flags")
        self.extensions = conf.getlist("options")

        # Normalize render flags and extensions for misaka 2.0, which uses
        # `dashed-case` instead of `snake_case` (misaka 1.x) for options.
        self.flags = [x.replace("_", "-") for x in self.flags]
        self.extensions = [x.replace("_", "-") for x in self.extensions]

        parser = Markdown(extensions=self.extensions,
                          flags=self.flags)
        # Filter out empty strings:
        strictly_allowed_html_elements = [x for x in conf.getlist("strictly-allowed-html-elements") if x]
        allowed_attributes = [x for x in conf.getlist("allowed-attributes") if x]

        # if "strictly-allowed-html-elements" option is set, use it instead of "allowed-elements"
        if strictly_allowed_html_elements:
            allowed_elements = strictly_allowed_html_elements
        else:
            allowed_elements = [x for x in conf.getlist("allowed-elements") if x]

            # attributes found in Sundown's HTML serializer [1]
            # - except for <img> tag, because images are not generated anyways.
            # - sub and sup added
            #
            # [1] https://github.com/vmg/sundown/blob/master/html/html.c
            allowed_elements = ["a", "p", "hr", "br", "ol", "ul", "li",
                                "pre", "code", "blockquote",
                                "del", "ins", "strong", "em",
                                "h1", "h2", "h3", "h4", "h5", "h6", "sub", "sup",
                                "table", "thead", "tbody", "tr", "th", "td"] + allowed_elements

        # If images are allowed, source element should be allowed as well
        if 'img' in allowed_elements and 'src' not in allowed_attributes:
            allowed_attributes.append('src')

        # If 'highlight' extension is enabled, allow 'mark' element
        if 'highlight' in self.extensions and 'mark' not in allowed_elements:
            allowed_elements.append('mark')

        # If 'underline' extension is enabled, allow 'u' element
        if 'underline' in self.extensions and 'u' not in allowed_elements:
            allowed_elements.append('u')

        sanitizer = Sanitizer(allowed_elements, allowed_attributes)

        self._render = lambda text: sanitizer.sanitize(parser(text))

    def render(self, text):
        return self._render(text)
