
from werkzeug.wrappers import Response


class Comment(object):
    """This class represents a regular comment. It needs at least a text
    field, all other fields are optional (or automatically set by the
    database driver.

    The field `mode` has a special meaning:

    0: normal
    1: in moderation queue
    2: deleted
    """

    fields = ['text', 'author', 'email', 'website', 'id', 'parent', 'timestamp', 'mode']

    def __init__(self, **kw):

        for field in self.fields:
            if field == 'text' and field not in kw:
                raise ValueError('Comment needs at least text, but no text was provided.')
            self.__dict__[field] = kw.get(field)


    @property
    def json(self):
        return ''

    @property
    def pending(self):
        return self.mode == 1

    @property
    def deleted(self):
        return self.mode == 2



def comment(app, environ, request, path, id=None):
    return Response('', 200)
