# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import cgi
import urllib

from itsdangerous import SignatureExpired, BadSignature

from isso import json, models, utils, wsgi


def create(app, environ, request, path):

    if app.PRODUCTION and not utils.urlexists(app.HOST, '/' + path):
        return 400, 'URL does not exist', {}

    try:
        comment = models.Comment.fromjson(request.data)
    except ValueError as e:
        return 400, unicode(e), {}

    for attr in 'author', 'email', 'website':
        if getattr(comment, attr) is not None:
            try:
                setattr(comment, attr, cgi.escape(getattr(comment, attr)))
            except AttributeError:
                return 400, '', {}

    try:
        rv = app.db.add(path, comment)
    except ValueError:
        return 400, '', {}

    md5 = rv.md5
    rv.text = app.markup.convert(rv.text)

    return 202 if rv.pending else 201, json.dumps(rv), {
        'Content-Type': 'application/json',
        'Set-Cookie': wsgi.setcookie('%s-%s' % (path, rv.id),
            app.sign([path, rv.id, md5]), max_age=app.MAX_AGE, path='/')
    }


def get(app, environ, request, path, id=None):

    rv = list(app.db.retrieve(path)) if id is None else app.db.get(path, id)
    if not rv:
        return 400, '', {}

    if request.args.get('plain', '0') == '0':
        if isinstance(rv, list):
            for item in rv:
                item.text = app.markup.convert(item.text)
        else:
            rv.text = app.markup.convert(rv.text)

    return 200, json.dumps(rv), {'Content-Type': 'application/json'}


def modify(app, environ, request, path, id):

    try:
        rv = app.unsign(request.cookies.get('%s-%s' % (urllib.quote(path, ''), id), ''))
    except (SignatureExpired, BadSignature) as e:
        try:
            rv = app.unsign(request.cookies.get('admin', ''))
        except (SignatureExpired, BadSignature):
            return 403, '', {}

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if not (rv == '*' or rv[0:2] == [path, id] or app.db.get(path, id).md5 != rv[2]):
        return 403, '', {}

    if request.method == 'PUT':
        try:
            rv = app.db.update(path, id, models.Comment.fromjson(request.data))
            rv.text = app.markup.convert(rv.text)
            return 200, json.dumps(rv), {'Content-Type': 'application/json'}
        except ValueError as e:
            return 400, unicode(e), {}

    if request.method == 'DELETE':
        rv = app.db.delete(path, id)

        return 200, json.dumps(rv), {
            'Content-Type': 'application/json',
            'Set-Cookie': wsgi.setcookie(path + '-' + str(id), 'deleted', max_age=0, path='/')
        }


def approve(app, environ, request, path, id):

    try:
        if app.unsign(request.cookies.get('admin', '')) != '*':
            return 403, '', {}
    except (SignatureExpired, BadSignature):
        return 403, '', {}

    app.db.activate(path, id)
    return 200, json.dumps(app.db.get(path, id)), {'Content-Type': 'application/json'}
