# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import cgi
import json
import hashlib
import sqlite3
import logging

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
        data = json.loads(request.data)
    except ValueError:
        return Response("No JSON object could be decoded", 400)

    if not data.get("text"):
        return Response("No text given.", 400)

    if "id" in data and not isinstance(data["id"], int):
        return Response("Parent ID must be an integer.")

    if "email" in data:
        hash = data["email"]
    else:
        hash = utils.salt(utils.anonymize(unicode(request.remote_addr)))

    comment = models.Comment(
        text=data["text"], parent=data.get("parent"),

        author=data.get("author") and cgi.escape(data.get("author")),
        website=data.get("website") and cgi.escape(data.get("website")),

        hash=hashlib.md5(hash).hexdigest())

    try:
        rv = app.db.add(uri, comment, utils.anonymize(unicode(request.remote_addr)))
    except sqlite3.Error:
        logging.exception('uncaught SQLite3 exception')
        abort(400)

    rv["text"] = app.markdown(rv["text"])

    resp = Response(app.dumps(rv), 202 if rv.pending else 201,
        content_type='application/json')
    resp.set_cookie('%s-%s' % (uri, rv["id"]), app.sign([uri, rv["id"], rv.md5]),
       max_age=app.MAX_AGE, path='/')
    return resp


@requires(str, 'uri')
def get(app, environ, request, uri):

    id = request.args.get('id', None)

    rv = list(app.db.retrieve(uri)) if id is None else app.db.get(uri, id)
    if not rv:
        abort(404)

    if request.args.get('plain', '0') == '0':
        if isinstance(rv, list):
            for item in rv:
                item['text'] = app.markdown(item['text'])
        else:
            rv['text'] = app.markdown(rv['text'])

    return Response(app.dumps(rv), 200, content_type='application/json')


@requires(str, 'uri')
@requires(int, 'id')
def modify(app, environ, request, uri, id):

    try:
        rv = app.unsign(request.cookies.get('%s-%s' % (uri, id), ''))
    except (SignatureExpired, BadSignature):
        try:
            rv = app.unsign(request.cookies.get('admin', ''))
        except (SignatureExpired, BadSignature):
            abort(403)

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if not (rv == '*' or rv[0:2] == [uri, id] or app.db.get(uri, id).md5 != rv[2]):
        abort(403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.data)
        except ValueError:
            return Response("No JSON object could be decoded", 400)

        if not data.get("text"):
            return Response("No text given.", 400)

        for key in data.keys():
            if key not in ("text", "author", "website"):
                data.pop(key)

        try:
            rv = app.db.update(uri, id, data)
        except sqlite3.Error:
            logging.exception('uncaught SQLite3 exception')
            abort(400)

        rv["text"] = app.markdown(rv["text"])
        return Response(app.dumps(rv), 200, content_type='application/json')

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


@requires(str, 'uri')
def count(app, environ, request, uri):

    rv = app.db.count(uri, mode=1)[0]

    if rv == 0:
        abort(404)

    return Response(json.dumps(rv), 200, content_type='application/json')
