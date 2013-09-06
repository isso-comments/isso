# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import cgi
import urllib

from itsdangerous import SignatureExpired, BadSignature

from werkzeug.wrappers import Response
from werkzeug.exceptions import abort, BadRequest

from isso import models, utils


class requires:

    def __init__(self, type, param):
        self.param = param
        self.type = type

    def __call__(self, func):
        def dec(app, env, req, *args, **kwargs):

            if self.param not in req.args:
                raise BadRequest("missing %s query" % self.param)

            try:
                kwargs[self.param] = self.type(req.args[self.param])
            except TypeError:
                raise BadRequest("invalid type for %s, expected %s" % (self.param, self.type))

            return func(app, env, req, *args, **kwargs)

        return dec


@requires(str, 'uri')
def create(app, environ, request, uri):

    if app.PRODUCTION and not utils.urlexists(app.HOST, uri):
        return Response('URI does not exist', 400)

    try:
        comment = models.Comment.fromjson(request.data, ip=request.remote_addr)
    except ValueError as e:
        return Response(unicode(e), 400)

    for attr in 'author', 'website':
        if getattr(comment, attr) is not None:
            try:
                setattr(comment, attr, cgi.escape(getattr(comment, attr)))
            except AttributeError:
                Response('', 400)

    try:
        rv = app.db.add(uri, comment, request.remote_addr)
    except ValueError:
        abort(400)  # FIXME: custom exception class, error descr

    md5 = rv.md5
    rv.text = app.markdown(rv.text)

    resp = Response(app.dumps(rv), 202 if rv.pending else 201,
        content_type='application/json')
    resp.set_cookie('%s-%s' % (uri, rv.id), app.sign([uri, rv.id, md5]),
       max_age=app.MAX_AGE, path='/')
    return resp


@requires(str, 'uri')
def get(app, environ, request, uri):

    id = request.args.get('id', None)

    rv = list(app.db.retrieve(uri)) if id is None else app.db.get(uri, id)
    if not rv:
        abort(404)

    if request.args.get('plain', '1') == '0':
        if isinstance(rv, list):
            for item in rv:
                item.text = app.markdown(item.text)
        else:
            rv.text = app.markdown(rv.text)

    return Response(app.dumps(rv), 200, content_type='application/json')


@requires(str, 'uri')
@requires(int, 'id')
def modify(app, environ, request, uri, id):

    try:
        rv = app.unsign(request.cookies.get('%s-%s' % (uri, id), ''))
    except (SignatureExpired, BadSignature) as e:
        try:
            rv = app.unsign(request.cookies.get('admin', ''))
        except (SignatureExpired, BadSignature):
            abort(403)

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if not (rv == '*' or rv[0:2] == [uri, id] or app.db.get(uri, id).md5 != rv[2]):
        abort(403)

    if request.method == 'PUT':
        try:
            rv = app.db.update(uri, id, models.Comment.fromjson(request.data))
            rv.text = app.markdown(rv.text)
            return Response(app.dumps(rv), 200, content_type='application/json')
        except ValueError as e:
            return Response(unicode(e), 400) # FIXME: custom exception and error descr

    if request.method == 'DELETE':
        rv = app.db.delete(uri, id)

        resp = Response(app.dumps(rv), 200, content_type='application/json')
        resp.delete_cookie(uri + '-' + str(id), path='/')
        return resp


@requires(str, 'uri')
@requires(int, 'id')
def like(app, environ, request, uri, id):

    nv = app.db.like(uri, id, request.remote_addr)
    return Response(str(nv), 200)


def approve(app, environ, request, path, id):

    try:
        if app.unsign(request.cookies.get('admin', '')) != '*':
            abort(403)
    except (SignatureExpired, BadSignature):
        abort(403)

    app.db.activate(path, id)
    return Response(app.dumps(app.db.get(path, id)), 200,
        content_type='application/json')
