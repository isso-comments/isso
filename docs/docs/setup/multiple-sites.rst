
.. _configure-multiple-sites:

Multiple Sites
--------------

Isso is designed to serve comments for a single website and therefore stores
comments for a relative URL. This is done to support HTTP, HTTPS and even domain transfers
without manual intervention. You can chain Isso to support multiple
websites on different domains.

The following example uses `gunicorn <http://gunicorn.org/>`_ as WSGI server (
you can use uWSGI as well). Let's say you maintain two websites, like
foo.example and other.bar:

.. code-block:: sh

    $ cat /etc/isso.d/foo.example.cfg
    [general]
    name = foo
    host = http://foo.example/
    dbpath = /var/lib/isso/foo.example.db

    $ cat /etc/isso.d/other.bar.cfg
    [general]
    name = bar
    host = http://other.bar/
    dbpath = /var/lib/isso/other.bar.db

Then you run Isso with gunicorn (separate multiple configuration files by
semicolon):

.. code-block:: sh

    $ export ISSO_SETTINGS="/etc/isso.d/foo.example.cfg;/etc/isso.d/other.bar.cfg"
    $ gunicorn isso.dispatch -b localhost:8080

In your webserver configuration, proxy Isso as usual:

.. code-block:: nginx

      server {
          listen [::]:80;
          server_name comments.example;

          location / {
              proxy_pass http://localhost:8080;
          }
      }

When you now visit http://comments.example/, you will see your different Isso
configuration separated by /`name`.

.. code-block:: text

    $ curl http://comments.example/
    /foo
    /bar

Just embed the JavaScript including the new relative path, e.g.
*http://comments.example/foo/js/embed.min.js*. Make sure, you don't mix the
URLs on both sites as it will most likely cause CORS-related errors.
