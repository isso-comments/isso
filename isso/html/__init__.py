import logging
import re

import bleach

logger = logging.getLogger("isso")


class Sanitizer(object):
    # pattern to match a valid class attribute for code tags
    code_language_pattern = re.compile(r"^language-[a-zA-Z0-9]{1,20}$")

    @staticmethod
    def allow_attribute_class(tag, name, value):
        return name == "class" and bool(Sanitizer.code_language_pattern.match(value))

    def __init__(self, elements, attributes):
        self.elements = elements

        # allowed attributes for tags
        self.attributes = {"table": ["align"], "a": ["href"], "code": Sanitizer.allow_attribute_class, "*": attributes}

    def sanitize(self, text):
        clean_html = bleach.clean(text, tags=self.elements, attributes=self.attributes, strip=True)

        def set_links(attrs, new=False):
            # Linker can misinterpret text as a domain name and create new invalid links.
            # To prevent this, we only allow existing links to be modified.
            if new:
                return None

            href_key = (None, "href")

            if href_key not in attrs:
                return attrs
            if attrs[href_key].startswith("mailto:"):
                return attrs

            rel_key = (None, "rel")
            rel_values = [val for val in attrs.get(rel_key, "").split(" ") if val]

            for value in ["nofollow", "noopener"]:
                if value not in [rel_val.lower() for rel_val in rel_values]:
                    rel_values.append(value)

            attrs[rel_key] = " ".join(rel_values)
            return attrs

        linker = bleach.linkifier.Linker(callbacks=[set_links])
        return linker.linkify(clean_html)


class Markup(object):
    def __init__(self, conf):
        conf_markup = conf.section("markup")

        if conf_markup.has_option("renderer") and conf_markup.get("renderer") == "mistune":
            from isso.html.mistune import MistuneMarkdown

            self.parser = MistuneMarkdown(conf.section("markup.mistune"))
            logging.info("Using Mistune as Markdown rendering engine")
        elif not conf_markup.has_option("renderer") or conf_markup.get("renderer") == "misaka":
            # We do not want to depend on Misaka unless it is actually used
            from isso.html.misaka import MisakaMarkdown

            self.parser = MisakaMarkdown(conf)
            logging.warning(
                "Misaka has been deprecated. Please switch to Mistune for Markdown rendering before the next release."
            )
        else:
            logging.fatal(
                "The `renderer` configuration option is set to an unknown value: %s. Set to either `mistune` or `misaka`.",
                conf_markup.get("renderer"),
            )
            raise ValueError("Invalid renderer value: %s. Set to either `mistune` or `misaka`." % conf_markup.get("renderer"))

        # Filter out empty strings. Both options are optional and may be
        # missing from the configuration file entirely.
        allowed_html_elements = (
            [x for x in conf_markup.getlist("allowed-html-elements") if x]
            if conf_markup.has_option("allowed-html-elements")
            else []
        )
        allowed_attributes = [x for x in conf_markup.getlist("allowed-attributes") if x]

        # "allowed-elements" is deprecated in favor of "allowed-html-elements",
        # so it may no longer be present in the configuration file.
        legacy_allowed_elements = (
            [x for x in conf_markup.getlist("allowed-elements") if x] if conf_markup.has_option("allowed-elements") else []
        )

        # if "allowed-html-elements" option is set, add "allowed-elements" on top of it
        if allowed_html_elements:
            allowed_elements = list(allowed_html_elements)

            new_elements = [x for x in legacy_allowed_elements if x not in allowed_elements]
            if new_elements:
                allowed_elements += new_elements
                logger.warning(
                    "The `allowed-elements` configuration option is deprecated and will be removed in a "
                    "future release. Please migrate the following elements to `allowed-html-elements`: %s",
                    ", ".join(new_elements),
                )
        else:
            # attributes found in Sundown's HTML serializer [1]
            # - except for <img> tag, because images are not generated anyways.
            # - sub and sup added
            #
            # [1] https://github.com/vmg/sundown/blob/master/html/html.c
            allowed_elements = [
                "a",
                "p",
                "hr",
                "br",
                "ol",
                "ul",
                "li",
                "pre",
                "code",
                "blockquote",
                "del",
                "ins",
                "strong",
                "em",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "sub",
                "sup",
                "table",
                "thead",
                "tbody",
                "tr",
                "th",
                "td",
            ] + legacy_allowed_elements

        # If images are allowed, source element should be allowed as well
        if "img" in allowed_elements and "src" not in allowed_attributes:
            allowed_attributes.append("src")

        self.sanitizer = Sanitizer(allowed_elements, allowed_attributes)

    def render(self, text):
        return self.sanitizer.sanitize(self.parser.render(text))
