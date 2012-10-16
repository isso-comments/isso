
import json
from isso.models import Comment

# def prove(f):

#     def dec(app, env, req, *args, **kwargs):

#         pass


# def sign(response):
#     pass


class IssoEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Comment):
            return dict((field, value) for field, value in obj.iteritems())

        return json.JSONEncoder.default(self, obj)
