# -*- encoding: utf-8 -*-

# from isso import compat
# from isso.compat import text_type as str, string_types

str = unicode
string_types = (unicode, str)


# @compat.implements_to_string
class ANSIString(object):

    style = 0
    color = 30

    def __init__(self, obj, style=None, color=None):

        if isinstance(obj, ANSIString):
            if style is None:
                style = obj.style
            if color is None:
                color = obj.color
            obj = obj.obj
        elif not isinstance(obj, string_types):
            obj = str(obj)

        self.obj = obj
        if style:
            self.style = style
        if color:
            self.color = color

    def __str__(self):
        return '\033[%i;%im' % (self.style, self.color) + self.obj + '\033[0m'

    def __add__(self, other):
        return str.__add__(str(self), other)

    def __radd__(self, other):
        return other + str(self)

    def encode(self, encoding):
        return str(self).encode(encoding)


normal, bold, underline = [lambda obj, x=x: ANSIString(obj, style=x)
    for x in (0, 1, 4)]

black, red, green, yellow, blue, \
magenta, cyan, white = [lambda obj, y=y: ANSIString(obj, color=y)
    for y in range(30, 38)]
