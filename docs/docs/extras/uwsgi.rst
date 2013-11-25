uWSGI
=====

In short: `uWSGI <http://uwsgi-docs.readthedocs.org/>`_ is awesome. Isso
has builtin support for it (and simple fallback if uWSGI is not
available). Use uWSGI if you think that the builtin WSGI server is a bad
choice or slow (hint: it's both).

With uWSGI, you have roughly 100% performance improvements for just
using it. Instead of one thread per request, you can use multiple
processes, hence it is more "web scale". Other side effects: spooling,
fast inter-process caching.

Installation
------------

You need uWSGI 1.9 or higher, fortunately you can install it with
Python:

.. code-block:: sh

    ~> apt-get install build-essential python-dev
    ~> pip install uwsgi

Configuration
-------------

For convenience, I recommend a INI-style configuration (you can also
supply everything as command-line arguments):

.. code-block:: ini

    [uwsgi]
    http = :8080
    master = true
    processes = 4
    cache2 = name=hash,items=1024,blocksize=32
    spooler = %d/mail
    module = isso
    virtualenv = %d
    env = ISSO_SETTINGS=%d/sample.cfg

You shoud adjust ``processes`` to your CPU count. Then, save this file
to a directory if choice. Next to this file, create an empty directory
called ``mail``:

.. code-block:: sh

    ~> mkdir mail/
    ~> ls
    uwsgi.ini  mail/

Now start Isso:

.. code-block:: sh

    ~> uwsgi /path/to/uwsgi.ini
