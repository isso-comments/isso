
import json
import time

class Comment(object):
    """This class represents a regular comment. It needs at least a text
    field, all other fields are optional (or automatically set by the
    database driver.

    The field `mode` has a special meaning:

    0: normal
    1: in moderation queue
    2: deleted
    """

    protected = ['id', 'mode', 'created', 'modified']
    fields = ['text', 'author', 'email', 'website', 'parent']

    def __init__(self, **kw):

        for field in self.protected + self.fields:
            self.__dict__[field] = kw.get(field)

    def iteritems(self, protected=True):
        for field in self.fields:
            yield field, getattr(self, field)
        if protected:
            for field in self.protected:
                yield field, getattr(self, field)

    @classmethod
    def fromjson(self, data):

        data = json.loads(data)
        comment = Comment(created=time.time())

        for field in self.fields:
            if field == 'text' and field not in data:
                raise ValueError('Comment needs at least text, but no text was provided.')
            comment.__dict__[field] = data.get(field)

        return comment

    @property
    def pending(self):
        return self.mode == 1

    @property
    def deleted(self):
        return self.mode == 2
