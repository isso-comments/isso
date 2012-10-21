# XXX: BBCode -- http://pypi.python.org/pypi/bbcode

try:
    import misaka
except ImportError:
    misaka = None  # NOQA


class Markup:

    def __init__(self, conf):
        return

    def convert(self, text):
        return text


class Markdown(Markup):

    def __init__(self, conf):
        if misaka is None:
            raise ImportError("Markdown requires 'misaka' lib!")
        return

    def convert(self, text):
        return misaka.html(text, extensions = misaka.EXT_STRIKETHROUGH \
            | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK \
            | misaka.HTML_SKIP_HTML  | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)
