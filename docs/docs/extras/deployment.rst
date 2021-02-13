Deployment
----------

Isso ships with a built-in web server, which is useful for the initial setup
and may be used in production for low-traffic sites (up to 20 requests per
second). Running a "real" WSGI server supports nice things such as UNIX domain
sockets, daemonization and solid HTTP handler. WSGI servers are more stable, secure
and web-scale than the built-in web server.

* gevent_, coroutine-based network library
* uWSGI_, full-featured uWSGI server
* gunicorn_, Python WSGI HTTP Server for UNIX
* mod_wsgi_, Apache interface to WSGI
* mod_fastcgi_, Apache  interface to FastCGI
* uberspace.de, `try this guide (in german) <http://blog.posativ.org/2014/isso-und-uberspace-de/>`_
* Openshift, Isso has a one click installer


`gevent <http://www.gevent.org/>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

First, create a startup script, called `isso.wsgi`. If Isso is in your system module
search path, then the script is quite simple. This script is included in the
isso distribution as `run.py`:

.. code-block:: python

    from __future__ import unicode_literals

    import os

    from isso import make_app
    from isso import dist, config

    application = make_app(
    config.load(
        os.path.join(dist.location, dist.project_name, "defaults.ini"),
        "/path/to/isso.cfg"),
    multiprocessing=True)

If you have installed Isso in a virtual environment, then you will have to add the path
of the virtualenv to the site-specific paths of Python:

.. code-block:: python

    from __future__ import unicode_literals

    import site
    site.addsitedir("/path/to/isso_virtualenv")

    import os

    from isso import make_app
    from isso import dist, config

    application = make_app(
    config.load(
        os.path.join(dist.location, dist.project_name, "defaults.ini"),
        "/path/to/isso.cfg",
    multiprocessing=True)

Using the aforementioned script will load system modules when available and modules
from the virtualenv otherwise. Should you want the opposite behavior, where modules from
the virtualenv have priority over system modules, the following script does the trick:

.. code-block:: python

    from __future__ import unicode_literals

    import os
    import site
    import sys

    # Remember original sys.path.
    prev_sys_path = list(sys.path)

    # Add the new site-packages directory.
    site.addsitedir("/path/to/isso_virtualenv")

    # Reorder sys.path so new directories at the front.
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path

    from isso import make_app
    from isso import dist, config

    application = make_app(
    config.load(
        os.path.join(dist.location, dist.project_name, "defaults.ini"),
        "/path/to/isso.cfg",
    multiprocessing=True)

The last two scripts are based on those given by
`mod_wsgi documentation <https://code.google.com/p/modwsgi/wiki/VirtualEnvironments>`_.

The Apache configuration will then be similar to the following:

.. code-block:: apache

    <VirtualHost *>
        ServerName example.org

        WSGIDaemonProcess isso user=www-data group=www-data threads=5
        WSGIScriptAlias /mounted_isso_path /path/to/isso.wsgi
    </VirtualHost>

You will need to adjust the user and group according to your Apache installation and
security policy. Be aware that the directory containing the comments database must
be writable by the user or group running the WSGI daemon process: having a writable
database only is not enough, since SQLite will need to create a lock file in the same
directory.

`mod_fastcgi <http://www.fastcgi.com/mod_fastcgi/docs/mod_fastcgi.html>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use this method if your hosting provider doesn't allow you to have long
running processes. If FastCGI has not yet been configured in your server,
please follow these steps:

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

Next, to run isso as a FastCGI script you'll need to install ``flup`` with
PIP:

.. code-block:: sh

    $ pip install flup

Finally, copy'n'paste to `/var/www/isso.fcgi` (or whatever location you prefer):

.. code-block:: python

    #!/usr/bin/env python
    #: uncomment if you're using a virtualenv
    # import sys
    # sys.path.insert(0, '<your_local_path>/lib/python3.<ver>/site-packages')

    from isso import make_app, dist, config
    import os

    from flup.server.fcgi import WSGIServer

    application = make_app(config.load(
            os.path.join(dist.location, dist.project_name, "defaults.ini"),
            "/path/to/isso.cfg"))
    WSGIServer(application).run()

`Openshift <http://openshift.com>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With `Isso Openshift Deployment Kit`_, Isso can be installed on Open
Shift with just one click. Make sure you already have installed ``rhc``
(`instructions`_) and completed the setup.

1. Run the following, you will get an Open Shift instance installed with
   Isso:

   ::

       rhc create-app appname python-2.7 --from-code https://github.com/avinassh/isso-openshift.git

2. Above step also clones Git repository of your Open Shift instance, in
   current directory. Make changes to the configuration file and push
   back to Openshift, it will be redeployed with new settings.

3. Visit ``http://<yourappname>-<openshift-namespace>.com/info`` to
   verify Isso is deployed properly and is working.

.. _Isso Openshift Deployment Kit: https://github.com/avinassh/isso-openshift
.. _instructions: https://developers.openshift.com/en/managing-client-tools.html
