# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from werkzeug.utils import redirect
from werkzeug.wrappers import Response

from mako.lookup import TemplateLookup
from itsdangerous import SignatureExpired, BadSignature

mako = TemplateLookup(directories=['isso/templates'], input_encoding='utf-8')
render = lambda template, **context: mako.get_template(template).render_unicode(**context)


def login(app, environ, request):

    if request.method == 'POST':
        if request.form.get('secret') == app.SECRET:
            rdr = redirect('/admin/', 301)
            rdr.set_cookie('session-admin', app.signer.dumps('*'), max_age=app.MAX_AGE)
            return rdr

    return Response(render('login.mako'), content_type='text/html')


def index(app, environ, request):

    try:
        app.unsign(request.cookies.get('session-admin', ''))
    except (SignatureExpired, BadSignature):
        return redirect('/')

    return Response(render('admin.mako'), content_type='text/html')
