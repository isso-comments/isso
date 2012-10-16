
from werkzeug.wrappers import Response


class Comment(object):

    fields = ['text', 'author', 'email', 'website', 'id', 'parent', 'timestamp']

    def __init__(self, **kw):

        for field in self.fields:
            if field == 'text' and field not in kw:
                raise ValueError('Comment needs at least text, but no text was provided.')
            self.__dict__[field] = kw.get(field)


    @property
    def json(self):
        return ''


def comment(app, environ, request, path, id=None):
    return Response('', 200)
