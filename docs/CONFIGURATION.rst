Isso Configuration
==================

The Isso configuration file is an `INI-style`__ textfile.  Below is an example for
a basic Isso configuration. Each section has its own documentation.

.. code-block:: ini

    [general]
    dbpath = /var/lib/isso/comments.db
    host = https://example.tld/
    [server]
    port = 1234

You can point Isso to your configuration file either witg a command-line parameter
or using an environment variable:

.. code-block:: sh

    ~> isso -c path/to/isso.cfg
    ~> env ISSO_SETTINGS=path/to/isso.cfg isso

__ https://en.wikipedia.org/wiki/INI_file


General
-------

In this section, you configure most comment-related options such as database path,
session key and hostname. Here are the default values for this section:

.. code-block:: ini

    [general]
    dbpath = /tmp/isso.db
    host = http://localhost:8080/
    max-age = 15m
    session-key = ... # python: binascii.b2a_hex(os.urandom(24))

dbpath
    file location to the SQLite3 database, highly recommended to change this
    location to a non-temporary location!

host
    URL to your website. When you start Isso, it will probe your website with
    a simple ``GET /`` request to see if it can reach the webserver. If this
    fails, Isso may not be able check if a web page exists, thus fails to
    accept new comments.

session-key
    private session key to validate client cookies. If you restart the
    application several times per hour for whatever reason, use a fixed
    key.

max-age
    time range that allows users to edit/remove their own comments. See
    :ref:`Appendum: Timedelta <appendum-timedelta>` for valid values.


Moderation
----------

Enable moderation queue and handling of comments still in moderation queue

.. code-block:: ini

    [moderation]
    enabled = false
    purge-after = 30d

enabled
    enable comment moderation queue. This option only affects new comments.
    Comments in modertion queue are not visible to other users until you
    activate them.

purge-after
    remove unprocessed comments in moderation queue after given time.


Server
------

HTTP server configuration, does **not** apply to uWSGI.

.. code-block:: ini

    [server]
    host = localhost
    port = 8080
    reload = off

host
    listen on specified interface

port
    application port

reload
    reload application, when the source code has changed. Useful for
    development (don't forget to use a fixed `session-key`).


SMTP
----

Isso can notify you on new comments via SMTP. In the email notification, you
also can moderate comments. If the server connection fails during startup, a
null mailer is used.

.. code-block:: ini

    [smtp]
    username =
    password =
    host = localhost
    port = 465
    ssl = on
    to =
    from =

username
    self-explanatory, optional

password
    self-explanatory (yes, plain text, create a dedicated account for
    notifications), optional.

host
    SMTP server

port
    SMTP port

ssl
    use SSL to connect to the server. Python probably does not validate the
    certificate. Needs research, though. But you should use a dedicated
    email account anyways.

to
    recipient address, e.g. your email address

from
    sender address, e.g. isso@example.tld


Guard
-----

Enable basic spam protection features, e.g. rate-limit per IP address (``/24``
for IPv4, ``/48`` for IPv6).

.. code-block:: ini

    [guard]
    enabled = true
    ratelimit = 2

enabled
    enable guard, recommended in production. Not useful for debugging
    purposes.

ratelimit: N
    limit to N new comments per minute.


Appendum
---------

.. _appendum-timedelta:

Timedelta
    A human-friendly representation of a time range: `1m` equals to 60
    seconds. This works for years (y), weeks (w), days (d) and seconds (s),
    e.g. `30s` equals 30 to seconds.

    You can add different types: `1m30s` equals to 90 seconds, `3h45m12s`
    equals to 3 hours, 45 minutes and 12 seconds (12512 seconds).
