Multi Site Configuration
========================

Isso is designed to serve comments for a single website and therefore stores
comments for a relative URL to support HTTP, HTTPS and even domain transfers
without manual intervention. But you can chain Isso to support multiple
websites on different domains.

The following example uses `gunicorn <http://gunicorn.org/>`_ as WSGI server (
you can use uWSGI as well). Let's say you maintain two websites, like
foo.example and other.foo:

.. code-block:: bash

    $ cat /etc/isso.d/foo.example.cfg
    [general]
    host = http://foo.example/
    dbpath = /var/lib/isso/foo.example.db

    $ cat /etc/isso.d/other.foo.cfg
    [general]
    host = http://other.foo/
    dbpath = /var/lib/isso/other.foo.db

Then you run Isso using gunicorn:

.. code-block:: bash

    $ export ISSO_SETTINGS="/etc/isso.d/foo.example.cfg;/etc/isso.d/other.foo.cfg"
    $ gunicorn isso.dispatch -b localhost:8080

In your webserver configuration, proxy Isso as usual:

.. code-block:: nginx

      server {
          listen [::]:80;
          server_name comments.example;

          location / {
              proxy_pass http://localhost:8080;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Real-IP $remote_addr;
          }
      }

To verify the setup, run:

.. code-block:: bash

      $ curl -vH "Origin: http://foo.example" http://comments.example/
      ...
      $ curl -vH "Origin: http://other.foo" http://comments.example/
      ...

In case of a 418 (I'm a teapot), the setup is *not* correctly configured.
