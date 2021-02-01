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

.. _configure-general:

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
    Your website(s). If Isso is unable to connect to at least one site, you'll
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

reply-notifications
    Allow users to request E-mail notifications for replies to their post.

    It is highly recommended to also turn on moderation when enabling this
    setting, as Isso can otherwise be easily exploited for sending spam.

    Do not forget to configure the client accordingly.

log-file
    Log console messages to file instead of standard out.

gravatar
    When set to ``true`` this will add the property "gravatar_image"
    containing the link to a gravatar image to every comment. If a comment
    does not contain an email address, gravatar will render a random icon.
    This is only true when using the default value for "gravatar-url"
    which contains the query string param ``d=identicon`` ...

gravatar-url
    Url for gravatar images. The "{}" is where the email hash will be placed.
    Defaults to "https://www.gravatar.com/avatar/{}?d=identicon"

latest-enabled
    If True it will enable the ``/latest`` endpoint. Optional, defaults
    to False.



.. _CORS: https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS


.. _configure-moderation:

Moderation
----------

Enable moderation queue and handling of comments still in moderation queue

.. code-block:: ini

    [moderation]
    enabled = false
    approve-if-email-previously-approved = false
    purge-after = 30d

enabled
    enable comment moderation queue. This option only affects new comments.
    Comments in moderation queue are not visible to other users until you
    activate them.

approve-if-email-previously-approved
    automatically approve comments by an email address if that address has
    had a comment approved within the last 6 months. No ownership verification
    is done on the entered email address. This means that if someone is able
    to guess correctly the email address used by a previously approved author,
    they will be able to have their new comment auto-approved.

purge-after
    remove unprocessed comments in moderation queue after given time.


.. _configure-server-block:

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

public-endpoint
    public URL that Isso is accessed from by end users. Should always be
    a http:// or https:// absolute address. If left blank, automatic
    detection is attempted. Normally only needs to be specified if
    different than the `listen` setting.

reload
    reload application, when the source code has changed. Useful for
    development. Only works with the internal webserver.

profile
    show 10 most time consuming function in Isso after each request. Do
    not use in production.

trusted-proxies
    an optional list of reverse proxies IPs behind which you have deployed
    your Isso web service (e.g. `127.0.0.1`).
    This allow for proper remote address resolution based on a
    `X-Forwarded-For` HTTP header, which is important for the mechanism
    forbiding several comment votes coming from the same subnet.

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

    Do not forget to configure the `client <client>`_ accordingly

require-author
    force commenters to enter a value into the author field. No validation is
    performed on the provided value.

    Do not forget to configure the `client <client>`_ accordingly.

require-email
    force commenters to enter a value into the email field. No validation is
    performed on the provided value.

    Do not forget to configure the `client <client>`_ accordingly.

.. _configure-markup:

Markup
------

Customize markup and sanitized HTML. Currently, only Markdown (via Misaka) is
supported, but new languages are relatively easy to add.

.. code-block:: ini

    [markup]
    options = strikethrough, superscript, autolink, fenced-code
    flags = skip-html, escape, hard-wrap
    allowed-elements =
    allowed-attributes =

options
    `Misaka-specific Markdown extensions <https://misaka.61924.nl/#api>`_, all
    extension flags can be used there, separated by comma, either by their name
    or as ``EXT_``.

    **Careful:** Misaka 1.0 used ``snake_case``, but 2.0 needs ``dashed-case``!

flags
    `Misaka-specific HTML rendering flags
    <https://misaka.61924.nl/#html-render-flags>`_, all html rendering flags
    can be used here, separated by comma, either by their name or as ``HTML_``.
    Per Misaka's defaults, no flags are set.

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

.. _configure-rss:

RSS
---

Isso can provide an Atom feed for each comment thread. Users can use
them to subscribe to comments and be notified of changes. Atom feeds
are enabled as soon as there is a base URL defined in this section.

.. code-block:: ini

    [rss]
    base =
    limit = 100

base
    base URL to use to build complete URI to pages (by appending the URI from Isso)

limit
    number of most recent comments to return for a thread

Admin
-----

.. _configure-admin:

Isso has an optional web administration interface that can be used to moderate
comments. The interface is available under ``/admin`` on your isso URL.

.. code-block:: ini

   [admin]
   enabled = true
   password = secret

enabled
   whether to enable the admin interface

password
   the plain text password to use for logging into the administration interface

Appendum
--------

.. _appendum-timedelta:

Timedelta
    A human-friendly representation of a time range: `1m` equals to 60
    seconds. This works for years (y), weeks (w), days (d) and seconds (s),
    e.g. `30s` equals 30 to seconds.

    You can add different types: `1m30s` equals to 90 seconds, `3h45m12s`
    equals to 3 hours, 45 minutes and 12 seconds (12512 seconds).

Environment variables
---------------------

.. _environment-variables:

Isso also support configuration through some environment variables:

ISSO_CORS_ORIGIN
    By default, `isso` will use the `Host` or else the `Referrer` HTTP header
    of the request to defines a CORS `Access-Control-Allow-Origin` HTTP header
    in the response.
    This environent variable allows you to define a broader fixed value,
    in order for example to share a single Isso instance among serveral of your
    subdomains : `ISSO_CORS_ORIGIN=*.example.test`
