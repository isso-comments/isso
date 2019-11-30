Quickstart
==========

Assuming you have successfully :doc:`installed <install>` Isso, here's
a quickstart guide that covers the most common setup. Sections covered:

.. contents::
    :local:
    :depth: 1

Configuration
-------------

You must provide a custom configuration to set `dbpath` (your database
location) and `host` (a list of websites for CORS_). All other options have
sane defaults.

.. code-block:: ini

    [general]
    ; database location, check permissions, automatically created if it
    does not exist
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
configuration. To serve comments for different websites, refer to
:ref:`Multiple Sites <configure-multiple-sites>`.

The moderation is done with signed URLs sent by email or logged to stdout.
By default, comments are accepted and immediately shown to other users. To
enable moderation queue, add:

.. code-block:: ini

    [moderation]
    enabled = true

To moderate comments, either use the activation or deletion URL in the logs or
:ref:`use SMTP <configure-smtp>` to get notified of new comments, including the
URLs for activation and deletion:

.. code-block:: ini

    [general]
    notify = smtp
    [smtp]
    ; SMTP settings

For more options, see :doc:`server <configuration/server>` and :doc:`client
<configuration/client>` configuration.

Migration
---------

Isso provides a tool for importing comments from Disqus_ or WordPress_.
You can also import comments from any other comment system, but this topic is more
complex and is covered in :doc:`advanced migration <extras/advanced-migration>`.

To export your comments from Disqus, log into Disqus, go to your website, click
on *Discussions* and select the *Export* tab. You'll receive an email with your
comments. Unfortunately, Disqus does not export up- and downvotes.

To export comments from your previous WordPress installation, go to *Tools*,
export your data. It has been reported that WordPress may generate broken XML.
Try to repair the file using ``xmllint`` before you continue with the import.

Now import the XML dump:

.. code-block:: sh

    ~> isso -c /path/to/isso.cfg import -t [disqus|wordpress] disqus-or-wordpress.xml
    [100%]  53 threads, 192 comments

.. _Disqus: https://disqus.com/
.. _WordPress: https://wordpress.org/

Running Isso
------------

To run Isso, simply execute:

.. code-block:: sh

    $ isso -c /path/to/isso.cfg run
    2013-11-25 15:31:34,773 INFO: connected to HTTP server

Next, we configure Nginx_ to proxy Isso. Do not run Isso on a public interface!
A popular but often error-prone (because of CORS_) setup to host Isso uses a
dedicated domain such as ``comments.example.tld``.

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

    <script data-isso="//comments.example.tld/"
            src="//comments.example.tld/js/embed.min.js"></script>

    <section id="isso-thread"></section>

Note, that `data-isso` is optional, but when a website includes a script using
``async`` it is no longer possible to determine the script's external URL.

That's it. When you open your website, you should see a commenting form. Leave
a comment to see if the setup works. If not, see :doc:`troubleshooting`.

Going Further
-------------

There are several server and client configuration options not covered in this
quickstart, check out :doc:`configuration/server` and
:doc:`configuration/client` for more information. For further website
integration, see :doc:`extras/advanced-integration`.

To launch Isso automatically, check the :ref:`init-scripts` section from the
installation guide. A different approach to deploy a web application is
written here: :doc:`Deployment of Isso <extras/deployment>`.

.. _Nginx: http://nginx.org/
.. _CORS: https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS
