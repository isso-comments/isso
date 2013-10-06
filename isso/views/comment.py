# -*- encoding: utf-8 -*-

import cgi
import json
import time
import hashlib
import logging
import sqlite3

from itsdangerous import SignatureExpired, BadSignature

from werkzeug.wrappers import Response
from werkzeug.exceptions import abort, BadRequest

from isso import utils, notify, db
from isso.crypto import pbkdf2

FIELDS = {'id', 'parent', 'text', 'author', 'website', 'email', 'mode', 'created',
          'modified', 'likes', 'dislikes', 'hash'}


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
def new(app, environ, request, uri):

    if uri not in app.db.threads and not utils.urlexists(app.conf.get('general', 'host'), uri):
        return Response('URI does not exist', 404)

    try:
        data = json.loads(request.data)
    except ValueError:
        return Response("No JSON object could be decoded", 400)

    for field in set(data.keys()) - set(['text', 'author', 'website', 'email', 'parent']):
        data.pop(field)

    if not data.get("text"):
        return Response("No text given.", 400)

    if "id" in data and not isinstance(data["id"], int):
        return Response("Parent ID must be an integer.")

    for field in ("author", "email"):
        if data.get(field):
            data[field] = cgi.escape(data[field])

    data['remote_addr'] = utils.anonymize(unicode(request.remote_addr))

    with app.lock:
        if uri not in app.db.threads:
            app.db.threads.new(uri, utils.heading(app.conf.get('general', 'host'), uri))
    title = app.db.threads[uri].title

    try:
        with app.lock:
            rv = app.db.comments.add(uri, data)
    except sqlite3.Error:
        logging.exception('uncaught SQLite3 exception')
        abort(400)
    except db.IssoDBException:
        abort(403)

    href = (app.conf.get('general', 'host').rstrip("/") + uri + "#isso-%i" % rv["id"])
    app.notify(title, notify.format(rv, href, utils.anonymize(unicode(request.remote_addr))))

    # save checksum of text into cookie, so mallory can't modify/delete a comment, if
    # he add a comment, then removed it but not the signed cookie.
    checksum = hashlib.md5(rv["text"].encode('utf-8')).hexdigest()

    rv["text"] = app.markdown(rv["text"])
    rv["hash"] = pbkdf2(rv.get('email') or rv['remote_addr'], app.salt, 1000, 6)

    for key in set(rv.keys()) - FIELDS:
        rv.pop(key)

    resp = Response(json.dumps(rv), 202 if rv["mode"] == 2 else 201,
        content_type='application/json')
    resp.set_cookie(str(rv["id"]), app.sign([rv["id"], checksum]), max_age=app.conf.getint('general', 'max-age'))
    return resp


def single(app, environ, request, id):

    if request.method == 'GET':
        rv = app.db.comments.get(id)
        if rv is None:
            abort(404)

        for key in set(rv.keys()) - FIELDS:
            rv.pop(key)

        if request.args.get('plain', '0') == '0':
            rv['text'] = app.markdown(rv['text'])

        return Response(json.dumps(rv), 200, content_type='application/json')

    try:
        rv = app.unsign(request.cookies.get(str(id), ''))
    except (SignatureExpired, BadSignature):
        try:
            rv = app.unsign(request.cookies.get('admin', ''))
        except (SignatureExpired, BadSignature):
            abort(403)

    if rv[0] != id:
        abort(403)

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if rv[1] != hashlib.md5(app.db.comments.get(id)["text"].encode('utf-8')).hexdigest():
        abort(403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.data)
        except ValueError:
            return Response("No JSON object could be decoded", 400)

        if data.get("text") is not None and len(data['text']) < 3:
            return Response("No text given.", 400)

        for key in set(data.keys()) - set(["text", "author", "website"]):
            data.pop(key)

        data['modified'] = time.time()

        try:
            rv = app.db.comments.update(id, data)
        except sqlite3.Error:
            logging.exception('uncaught SQLite3 exception')
            abort(400)

        for key in set(rv.keys()) - FIELDS:
            rv.pop(key)

        checksum = hashlib.md5(rv["text"].encode('utf-8')).hexdigest()
        rv["text"] = app.markdown(rv["text"])

        resp = Response(json.dumps(rv), 200, content_type='application/json')
        resp.set_cookie(str(rv["id"]), app.sign([rv["id"], checksum]), max_age=app.conf.getint('general', 'max-age'))
        return resp

    if request.method == 'DELETE':

        rv = app.db.comments.delete(id)
        if rv:
            for key in set(rv.keys()) - FIELDS:
                rv.pop(key)

        resp = Response(json.dumps(rv), 200, content_type='application/json')
        resp.delete_cookie(str(id), path='/')
        return resp


@requires(str, 'uri')
def fetch(app, environ, request, uri):

    rv = list(app.db.comments.fetch(uri))
    if not rv:
        abort(404)

    for item in rv:

        item['hash'] = pbkdf2(item['email'] or item['remote_addr'], app.salt, 1000, 6)

        for key in set(item.keys()) - FIELDS:
            item.pop(key)

    if request.args.get('plain', '0') == '0':
        for item in rv:
            item['text'] = app.markdown(item['text'])

    return Response(json.dumps(rv), 200, content_type='application/json')


def like(app, environ, request, id):

    nv = app.db.comments.vote(True, id, utils.anonymize(unicode(request.remote_addr)))
    return Response(json.dumps(nv), 200)


def dislike(app, environ, request, id):

    nv = app.db.comments.vote(False, id, utils.anonymize(unicode(request.remote_addr)))
    return Response(json.dumps(nv), 200)


@requires(str, 'uri')
def count(app, environ, request, uri):

    rv = app.db.comments.count(uri)[0]

    if rv == 0:
        abort(404)

    return Response(json.dumps(rv), 200, content_type='application/json')


def checkip(app, env, req):
    return Response(utils.anonymize(unicode(req.remote_addr)), 200)
