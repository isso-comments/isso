Server Configuration
====================

The Isso configuration file is an `INI-style`__ textfile. It reads integers,
booleans and strings.  Below is a basic example:

.. code-block:: ini

    [general]
    dbpath = /var/lib/isso/comments.db
    host = https://example.tld/
    [server]
    listen = http://localhost:1234/

To use your configuration file with Isso, append ``-c /path/to/cfg`` to the
executable or run Isso with an environment variable:

.. code-block:: sh

    ~> isso -c path/to/isso.cfg
    ~> env ISSO_SETTINGS=path/to/isso.cfg isso

__ https://en.wikipedia.org/wiki/INI_file

Sections covered in this document:

.. contents::
    :local:


General
-------

In this section, you configure most comment-related options such as database path,
session key and hostname. Here are the default values for this section:

.. code-block:: ini

    [general]
    dbpath = /tmp/isso.db
    name =
    host = http://localhost:8080/
    max-age = 15m
    session-key = ... ; python: binascii.b2a_hex(os.urandom(24))
    notify =

dbpath
    file location to the SQLite3 database, highly recommended to change this
    location to a non-temporary location!

name
    required to dispatch :ref:`multiple websites <configure-multiple-sites>`,
    not used otherwise.

host
    URL to your website. When you start Isso, it will probe your website with
    a simple ``GET /`` request to see if it can reach the webserver. If this
    fails, Isso may not be able check if a web page exists, thus fails to
    accept new comments.

    You can supply more than one host:

    .. code-block:: ini

        [general]
        host =
            http://localhost/
            https://localhost/

    This is useful, when your website is available on HTTP and HTTPS.

session-key
    private session key to validate client cookies. If you restart the
    application several times per hour for whatever reason, use a fixed
    key.

max-age
    time range that allows users to edit/remove their own comments. See
    :ref:`Appendum: Timedelta <appendum-timedelta>` for valid values.

notify
    Select notification backend for new comments. Currently, only SMTP
    is available.


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

HTTP server configuration.

.. code-block:: ini

    [server]
    listen = http://localhost:8080
    reload = off
    profile = off

listen
    interface to listen on. Isso supports TCP/IP and unix domain sockets:

    .. code-block:: ini

        ; UNIX domain socket
        listen = unix:///tmp/isso.sock
        ; TCP/IP
        listen = http:///localhost:1234/

    When ``gevent`` is available, it is automatically used for `http://`
    Currently, gevent can not handle http requests on unix domain socket
    (see `#295 <https://github.com/surfly/gevent/issues/295>`_ and
    `#299 <https://github.com/surfly/gevent/issues/299>`_ for details).

    Does not apply for `uWSGI`.

reload
    reload application, when the source code has changed. Useful for
    development (don't forget to use a fixed `session-key`). Only works
    when ``gevent`` and ``uwsgi`` are *not* available.

profile
    show 10 most time consuming function in Isso after each request. Do
    not use in production.

.. _configure-smtp:

SMTP
----

Isso can notify you on new comments via SMTP. In the email notification, you
also can moderate (=activate or delete) comments. Don't forget to configure
``notify = smtp`` in the general section.

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
    direct-reply = 3
    reply-to-self = false

enabled
    enable guard, recommended in production. Not useful for debugging
    purposes.

ratelimit
    limit to N new comments per minute.

direct-reply
    how many comments directly to the thread (prevent a simple
    `while true; do curl ...; done`.

reply-to-self
    allow commenters to reply to their own comments when they could still edit
    the comment. After the editing timeframe is gone, commenters can reply to
    their own comments anyways.

    Do not forget to configure the client.


Appendum
--------

.. _appendum-timedelta:

Timedelta
    A human-friendly representation of a time range: `1m` equals to 60
    seconds. This works for years (y), weeks (w), days (d) and seconds (s),
    e.g. `30s` equals 30 to seconds.

    You can add different types: `1m30s` equals to 90 seconds, `3h45m12s`
    equals to 3 hours, 45 minutes and 12 seconds (12512 seconds).
