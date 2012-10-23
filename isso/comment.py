# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import cgi
import urllib

from werkzeug.wrappers import Response
from werkzeug.exceptions import abort

from itsdangerous import SignatureExpired, BadSignature

from isso import json, models, utils


def create(app, environ, request, path):

    if app.PRODUCTION and not utils.urlexists(app.HOST, '/' + path):
        return abort(404)

    try:
        comment = models.Comment.fromjson(request.data)
    except ValueError:
        return abort(400)

    for attr in 'author', 'email', 'website':
        if getattr(comment, attr) is not None:
            try:
                setattr(comment, attr, cgi.escape(getattr(comment, attr)))
            except AttributeError:
                abort(400)

    try:
        rv = app.db.add(path, comment)
    except ValueError:
        return abort(400)

    md5 = rv.md5
    rv.text = app.markup.convert(rv.text)

    response = Response(json.dumps(rv), 201, content_type='application/json')
    response.set_cookie('session-%s-%s' % (urllib.quote(path, ''), rv.id),
        app.signer.dumps([path, rv.id, md5]), max_age=app.MAX_AGE)
    return response


def get(app, environ, request, path, id=None):

    rv = list(app.db.retrieve(path)) if id is None else app.db.get(path, id)
    if not rv:
        abort(404)

    if isinstance(rv, list):
        for item in rv:
            item.text = app.markup.convert(item.text)
    else:
        rv.text = app.markup.convert(rv.text)

    return Response(json.dumps(rv), 200, content_type='application/json')


def modify(app, environ, request, path, id):

    try:
        rv = app.unsign(request.cookies.get('session-%s-%s' % (urllib.quote(path, ''), id), ''))
    except (SignatureExpired, BadSignature):
        return abort(403)

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if app.db.get(path, id).md5 != rv[2]:
        abort(403)

    if not (rv[0] == '*' or rv[0:2] == [path, id]):
        abort(403)

    if request.method == 'PUT':
        try:
            rv = app.db.update(path, id, models.Comment.fromjson(request.data))
            return Response(json.dumps(rv), 200, content_type='application/json')
        except ValueError as e:
            return Response(unicode(e), 400)

    if request.method == 'DELETE':
        rv = app.db.delete(path, id)

        response = Response(json.dumps(rv), 200, content_type='application/json')
        response.delete_cookie('session-%s-%s' % (urllib.quote(path, ''), id))
        return response
