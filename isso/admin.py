# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from os.path import join, dirname

from mako.lookup import TemplateLookup
from itsdangerous import SignatureExpired, BadSignature

from isso.wsgi import setcookie


mako = TemplateLookup(directories=[join(dirname(__file__), 'templates')], input_encoding='utf-8')
render = lambda template, **context: mako.get_template(template).render_unicode(**context)


def login(app, environ, request):

    if request.method == 'POST':
        if request.form.getfirst('secret') == app.SECRET:
            return 301, '', {
                'Location': '/admin/',
                'Set-Cookie': setcookie('admin', app.signer.dumps('*'),
                    max_age=app.MAX_AGE, path='/')
            }

    return 200, render('login.mako').encode('utf-8'), {'Content-Type': 'text/html'}


def index(app, environ, request):

    try:
        app.unsign(request.cookies.get('admin', ''))
    except (SignatureExpired, BadSignature):
        return 301, '', {'Location': '/'}

    ctx = {'app': app, 'request': request}
    return 200, render('admin.mako', **ctx).encode('utf-8'), {'Content-Type': 'text/html'}
