Server Configuration
====================

The Isso configuration file is an `INI-style`__ textfile. It reads integers,
booleans, strings and lists. Here's the default isso configuration:
`isso.conf <https://github.com/posativ/isso/blob/master/share/isso.conf>`. A
basic configuration from scratch looks like this:

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
    host =
    max-age = 15m
    notify = stdout
    log-file =

dbpath
    file location to the SQLite3 database, highly recommended to change this
    location to a non-temporary location!

name
    required to dispatch :ref:`multiple websites <configure-multiple-sites>`,
    not used otherwise.

host
    Your website(s). If Isso is unable to connect to at least on site, you'll
    get a warning during startup and comments are most likely non-functional.

    You'll need at least one host/website to run Isso. This is due to security
    reasons: Isso uses CORS_ to embed comments and to restrict comments only to
    your website, you have to "whitelist" your website(s).

    I recommend the first value to be a non-SSL website that is used as fallback
    if Firefox users (and only those) supress their HTTP referer completely.

    .. code-block:: ini

        [general]
        host =
            http://example.tld/
            https://example.tld/

max-age
    time range that allows users to edit/remove their own comments. See
    :ref:`Appendum: Timedelta <appendum-timedelta>` for valid values.

notify
    Select notification backend(s) for new comments, separated by comma.
    Available backends:

    stdout
        Log to standard output. Default, if none selected. Note, this
        functionality is broken since a few releases.

    smtp
        Send notifications via SMTP on new comments with activation (if
        moderated) and deletion links.

log-file
    Log console messages to file instead of standard out.


.. _CORS: https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS


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
        listen = http://localhost:1234/

    When ``gevent`` is available, it is automatically used for `http://`
    Currently, gevent can not handle http requests on unix domain socket
    (see `#295 <https://github.com/surfly/gevent/issues/295>`_ and
    `#299 <https://github.com/surfly/gevent/issues/299>`_ for details).

    Does not apply for `uWSGI`.

reload
    reload application, when the source code has changed. Useful for
    development. Only works with the internal webserver.

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
    port = 587
    security = starttls
    to =
    from =
    timeout = 10

username
    self-explanatory, optional

password
    self-explanatory (yes, plain text, create a dedicated account for
    notifications), optional.

host
    SMTP server

port
    SMTP port

security
    use a secure connection to the server, possible values: *none*, *starttls*
    or *ssl*. Note, that there is no easy way for Python 2.7 and 3.3 to
    implement certification validation and thus the connection is vulnerable to
    Man-in-the-Middle attacks. You should definitely use a dedicated SMTP
    account for Isso in that case.

to
    recipient address, e.g. your email address

from
    sender address, e.g. `"Foo Bar" <isso@example.tld>`

timeout
    specify a timeout in seconds for blocking operations like the
    connection attempt.


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
    require-author = false
    require-email = false

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

require-author
    force commenters to enter a value into the author field. No validation is
    performed on the provided value.

    Do not forget to configure the client accordingly.

require-email
    force commenters to enter a value into the email field. No validation is
    performed on the provided value.

    Do not forget to configure the client.

Markup
------

Customize markup and sanitized HTML. Currently, only Markdown (via Misaka) is
supported, but new languages are relatively easy to add.

.. code-block:: ini

    [markup]
    options = strikethrough, superscript, autolink
    allowed-elements =
    allowed-attributes =

options
    `Misaka-specific Markdown extensions <http://misaka.61924.nl/api/>`_, all
    flags starting with `EXT_` can be used there, separated by comma.

allowed-elements
    Additional HTML tags to allow in the generated output, comma-separated. By
    default, only *a*, *blockquote*, *br*, *code*, *del*, *em*, *h1*, *h2*,
    *h3*, *h4*, *h5*, *h6*, *hr*, *ins*, *li*, *ol*, *p*, *pre*, *strong*,
    *table*, *tbody*, *td*, *th*, *thead* and *ul* are allowed.

allowed-attributes
    Additional HTML attributes (independent from elements) to allow in the
    generated output, comma-separated. By default, only *align* and *href* are
    allowed.

To allow images in comments, you just need to add ``allowed-elements = img`` and
``allowed-attributes = src``.

Hash
----

Customize used hash functions to hide the actual email addresses from
commenters but still be able to generate an identicon.

.. code-block:: ini

    [hash]
    salt = Eech7co8Ohloopo9Ol6baimi
    algorithm = pbkdf2

salt
    A salt is used to protect against rainbow tables. Isso does not make use of
    pepper (yet). The default value has been in use since the release of Isso
    and generates the same identicons for same addresses across installations.

algorithm
    Hash algorithm to use -- either from Python's `hashlib` or PBKDF2 (a
    computational expensive hash function).

    The actual identifier for PBKDF2 is `pbkdf2:1000:6:sha1`, which means 1000
    iterations, 6 bytes to generate and SHA1 as pseudo-random family used for
    key strengthening.
    Arguments have to be in that order, but can be reduced to `pbkdf2:4096`
    for example to override the iterations only.

User
----

Give yourself, your friends and/or your contributors lightweight accounts. These can be used
to later stylize your comments through CSS and distinguish them from the from anonymous commenters.

.. code-block:: ini

    [user]
    accounts =
        Administrator,hunter9
        John Smith,passw0rd

accounts
    List of protected accounts. Each account is a name / password pair.
    If a commenter enters a protected account name, they will be required to enter
    the corresponding password in order to post their comment.
    The password field will be offered in place of email.

    The "sluggified" user names will then be added as CSS classses on the comments.
    For the above example, classes will be: `isso-known-user isso-user-administrator`
    and `isso-known-user isso-user-john_smith`.


Appendum
--------

.. _appendum-timedelta:

Timedelta
    A human-friendly representation of a time range: `1m` equals to 60
    seconds. This works for years (y), weeks (w), days (d) and seconds (s),
    e.g. `30s` equals 30 to seconds.

    You can add different types: `1m30s` equals to 90 seconds, `3h45m12s`
    equals to 3 hours, 45 minutes and 12 seconds (12512 seconds).
