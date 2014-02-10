Quickstart
==========

Assuming you have successfully :doc:`installed <install>` Isso, here's
a quickstart quide that covers common setups. Sections covered:

.. contents::
    :local:
    :depth: 1


Configuration
-------------

You must provide a custom configuration. Most default parameters are useful for
development, not persistence. The two most important options are `dbpath` to
set the location of your database and your website's name `host` where you want
to comment on:

.. code-block:: ini

    [general]
    ; database location, check permissions, created if not exists
    dbpath = /var/lib/isso/comments.db
    ; your website or blog (not the location of Isso!)
    host = http://example.tld/
    ; you can add multiple hosts for local development
    ; or SSL connections. There is no wildcard to allow
    ; any domain.
    host =
        http://localhost:1234/
        http://example.tld/
        https://example.tld/

Note, that multiple, *different* websites are **not** supported in a single
configuration. To serve comments for diffent websites, refer to
:ref:`Multiple Sites <configure-multiple-sites>`.

You moderate Isso through signed URLs sent by email or logged. By default,
comments are accepted and immediately shown to other users. To enable
moderation queue, add:

.. code-block:: ini

    [moderation]
    enabled = true

To moderate comments, either use the activation or deletion URL in the logs or
:ref:`use SMTP <configure-smtp>` to get notified on new comments including the
URLs for activation and deletion:

.. code-block:: ini

    [general]
    notify = smtp
    [smtp]
    ; SMTP settings

For more details, see :doc:`server <configuration/server>` and
:doc:`client <configuration/client>` configuration.

Migration
---------

You can migrate your existing comments from Disqus_. Log into Disqus, go to
your website, click on *Discussions* and select the *Export* tab. You'll
receive an email with your comments. Unfortunately, Disqus does not export
up- and downvotes.

To import existing comments, run Isso with your new configuration file:

.. code-block:: sh

    ~> isso -c /path/to/isso.cfg import user-2013-09-02T11_39_22.971478-all.xml
    [100%]  53 threads, 192 comments

.. _Disqus: <https://disqus.com/>


Running Isso
------------

To run Isso, simply execute:

.. code-block:: sh

    $ isso -c /path/to/isso.cfg run
    2013-11-25 15:31:34,773 INFO: connected to HTTP server

Next, we configure Nginx_ to proxy Isso. Do not run Isso on a public interface!
A popular but often error-prone (because of CORS_) setup to host Isso uses a
dedicated domain such as ``comments.example.tld``; see
:doc:`configuration/setup` for alternate ways.

Assuming both, your website and Isso are on the same server, the nginx
configuration looks like this:

.. code-block:: nginx

    server {
        listen [::]:80 default ipv6only=off;
        server_name example.tld;
        root ...;
    }

    server {
        listen [::]:80;
        server_name comments.example.tld;

        location / {
            proxy_pass http://localhost:8080;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

Integration
-----------

Now, you embed Isso to your website:

.. code-block:: html

    <script data-isso="http://comments.example.tld/"
            src="http://comments.example.tld/js/embed.min.js"></script>

    <section id="isso-thread"></section>

Note, that `data-isso` is optional, but when a website includes a script using
``async`` it is no longer possible to determine the script's external URL.

That's it. When you open your website, you should see a commenting form. Leave
a comment to see if the setup works. If not, see :doc:`troubleshooting`.


For further integration, look at :doc:`advanced-integration`.

.. _Nginx: http://nginx.org/
.. _CORS: https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS


Deployment
----------

Isso ships with a built-in web server, which is useful for the initial setup
and may be used in production for low-traffic sites (up to 20 requests per
second). It is recommended to use a "real" WSGI server to run Isso, e.g:

* gevent_, coroutine-based network library
* uWSGI_, full-featured uWSGI server
* gunicorn_, Python WSGI HTTP Server for UNIX

.. _gevent: http://www.gevent.org/
.. _uWSGI: http://uwsgi-docs.readthedocs.org/en/latest/
.. _gunicorn: http://gunicorn.org/

gevent
^^^^^^

Probably the easiest deployment method. Install with PIP (requires libevent):

.. code-block:: sh

    $ pip install gevent

Then, just use the ``isso`` executable as usual. Gevent monkey-patches Python's
standard library to work with greenlets.

To execute Isso, just use the commandline interface:

.. code-block:: sh

    $ isso -c my.cfg run

Unfortunately, gevent 0.13.2 does not support UNIX domain sockets (see `#295
<https://github.com/surfly/gevent/issues/295>`_ and `#299
<https://github.com/surfly/gevent/issues/299>`_ for details).

uWSGI
^^^^^

The author's favourite WSGI server. Due the complexity of uWSGI, there is a
:doc:`separate document <extras/uwsgi>` on how to setup uWSGI for use
with Isso.

gunicorn
^^^^^^^^

Install gunicorn_ via PIP:

.. code-block:: sh

    $ pip install gunicorn

To execute Isso, use a command similar to:

.. code-block:: sh

    $ export ISSO_SETTINGS="/path/to/isso.cfg"
    $ gunicorn -b localhost:8080 -w 4 --preload isso.run

mod_wsgi
^^^^^^^^

I have no experience at all with `mod_wsgi`, most things are taken from
`Flask: Configuring Apache <http://flask.pocoo.org/docs/deploying/mod_wsgi/#configuring-apache>`_:

.. code-block:: apache

    <VirtualHost *>
        ServerName example.org

        WSGIDaemonProcess isso user=... group=... threads=5
        WSGIScriptAlias / /var/www/isso.wsgi
    </VirtualHost>

Now, you need to create a new `isso.wsgi` file:

.. code-block:: python

    import os

    from isso import make_app
    from isso.core import Config

    application = make_app(Config.load("/path/to/isso.cfg"))

Unless you know how to preload the application, add a static session key to
your `isso.cfg`:

.. code-block:: ini

    [general]
    ; cat /dev/urandom | strings | grep -o '[[:alnum:]]' | head -n 30 | tr -d '\n'
    session-key = superrandomkey1

