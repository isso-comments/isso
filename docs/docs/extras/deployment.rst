Deployment
----------

Isso ships with a built-in web server, which is useful for the initial setup
and may be used in production for low-traffic sites (up to 20 requests per
second). Running a "real" WSGI server supports nice things such as UNIX domain
sockets, daemonization and solid HTTP handler while being more stable, secure
and web-scale than the built-in web server.

* gevent_, coroutine-based network library
* uWSGI_, full-featured uWSGI server
* gunicorn_, Python WSGI HTTP Server for UNIX
* mod_wsgi_, Apache interface to WSGI
* mod_fastcgi_, Apache  interface to FastCGI
* uberspace.de, `try this guide (in german) <http://blog.posativ.org/2014/isso-und-uberspace-de/>`_


`gevent <http://gunicorn.org/>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ 

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


`uWSGI <http://uwsgi-docs.readthedocs.org/en/latest/>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Isso has special support for uWSGI, namely fast IPC caching, job spooling and
delayed jobs. It is the author's choice, but not the only one. You need
uWSGI 1.9 or higher, fortunately you can install it from PyPi:

.. code-block:: sh

    ~> apt-get install build-essential python-dev
    ~> pip install uwsgi

For convenience, I recommend a INI-style configuration (you can also
supply everything as command-line arguments):

.. code-block:: ini

    [uwsgi]
    http = :8080
    master = true
    ; set to `nproc`
    processes = 4
    cache2 = name=hash,items=1024,blocksize=32
    ; you may change this
    spooler = /tmp/isso/mail
    module = isso.run
    ; uncomment if you use a virtual environment
    ; virtualenv = /path/to/isso
    env = ISSO_SETTINGS=/path/to/isso.cfg

Then, create the spooling directory and start Isso via uWSGI:

.. code-block:: sh

    ~> mkdir /tmp/isso/mail
    ~> uwsgi /path/to/uwsgi.ini


`gunicorn <http://gunicorn.org>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX with a pre-fork
worker ported from Ruby's Unicorn project. Install gunicorn_ via PIP:

.. code-block:: sh

    $ pip install gunicorn

To execute Isso, use a command similar to:

.. code-block:: sh

    $ export ISSO_SETTINGS="/path/to/isso.cfg"
    $ gunicorn -b localhost:8080 -w 4 --preload isso.run


`mod_wsgi <https://code.google.com/p/modwsgi/>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This information may be incorrect, if you have more knowledge on how
   to deploy Python via `mod_wsgi`, consider extending/correcting this section.

   For more information, see `Flask: Configuring Apache
   <http://flask.pocoo.org/docs/deploying/mod_wsgi/#configuring-apache>`_.

.. code-block:: apache

    <VirtualHost *>
        ServerName example.org

        WSGIDaemonProcess isso user=www-data group=www-data threads=5
        WSGIScriptAlias / /var/www/isso.wsgi
    </VirtualHost>

Next, copy'n'paste to `/var/www/isso.wsgi`:

.. code-block:: python

    from isso import make_app
    from isso.core import Config

    application = make_app(Config.load("/path/to/isso.cfg"))

Also make sure, you set a static key because `mod_wsgi` generates a session
key per thread/process. This may result in random 403 errors when you edit or
delete comments.

.. code-block:: ini

    [general]
    ; cat /dev/urandom | strings | grep -o '[[:alnum:]]' | head -n 30 | tr -d '\n'
    session-key = superrandomkey1

`mod_fastcgi <http://www.fastcgi.com/mod_fastcgi/docs/mod_fastcgi.html>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This information may be incorrect, if you have more knowledge on how
   to deploy Python via `mod_fastcgi`, consider extending/correcting this section.

   For more information, see `Flask: Configuring Apache
   <http://flask.pocoo.org/docs/deploying/fastcgi/#configuring-apache>`_.

.. code-block:: apache

    LoadModule fastcgi_module /usr/lib64/httpd/modules/mod_fastcgi.so

    FastCgiServer /var/www/html/yourapplication/app.fcgi -idle-timeout 300 -processes 5

    <VirtualHost *>
        ServerName example.org

        AddHandler fastcgi-script fcgi
        ScriptAlias / /var/www/isso.fcgi

        <Location />
            SetHandler fastcgi-script
        </Location>
    </VirtualHost>

Next, copy'n'paste to `/var/www/isso.fcgi` (or whatever location you prefer):

.. code-block:: python

    #!/usr/bin/env python2.7

    from isso import make_app
    from isso.core import Config

    from flup.server.fcgi import WSGIServer

    application = make_app(Config.load("/path/to/isso.cfg"))
    WSGIServer(application).run()

Similar to mod_wsgi_, set a static session key if you are using more than one process
to avoid random errors.

.. code-block:: ini

    [general]
    ; cat /dev/urandom | strings | grep -o '[[:alnum:]]' | head -n 30 | tr -d '\n'
    session-key = superrandomkey1
