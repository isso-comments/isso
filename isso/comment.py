
from werkzeug.wrappers import Response
from werkzeug.exceptions import abort

from isso import json, models


def create(app, environ, request, path):

    try:
        rv = app.db.add(path, models.Comment.fromjson(request.data))
    except ValueError as e:
        return Response(unicode(e), 400)

    return Response(json.dumps(app.db.get(*rv)), 201, content_type='application/json')


def get(app, environ, request, path, id=None):

    rv = list(app.db.retrieve(path)) if id is None else app.db.get(path, id)
    if not rv:
        abort(404)
    return Response(json.dumps(rv), 200, content_type='application/json')
