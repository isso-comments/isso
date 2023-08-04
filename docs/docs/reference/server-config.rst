Server Configuration
====================

The Isso configuration file is an `INI-style`__ textfile. It reads integers,
booleans, strings and lists. Here's the default isso configuration:
`isso.cfg <https://github.com/posativ/isso/blob/master/isso/isso.cfg>`_. A
basic configuration from scratch looks like this:

.. code-block:: ini
   :caption: ``isso.cfg``

    [general]
    dbpath = /var/lib/isso/comments.db
    host = https://example.tld/
    [server]
    listen = http://localhost:1234/

To use your configuration file with Isso, append ``-c /path/to/isso.cfg`` to
the executable or run Isso with an environment variable:

.. code-block:: console

    (.venv) $ isso -c /path/to/isso.cfg
    (.venv) $ env ISSO_SETTINGS=/path/to/isso.cfg$ isso

__ https://en.wikipedia.org/wiki/INI_file

Sections covered in this document:

.. contents::
    :local:

General
-------

.. _configure-general:

In this section, you configure most comment-related options such as database path,
session key and hostname.

Here are the **default values** for this section:

.. code-block:: ini

    [general]
    dbpath = /tmp/comments.db
    name =
    host =
    max-age = 15m
    notify = stdout
    log-file =
    gravatar = false
    gravatar-url = https://www.gravatar.com/avatar/{}?d=identicon&s=55
    latest-enabled = false

dbpath
    File location to the SQLite3 database, highly recommended to change this
    location to a non-temporary location!

    Default: ``/tmp/comments.db``

name
    Required to dispatch :ref:`multiple websites <configure-multiple-sites>`,
    not used otherwise.

    Default: (empty)

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

    Default: (empty)

max-age
    Time range that allows users to edit/remove their own comments. See
    :ref:`Appendum: Timedelta <appendum-timedelta>` for valid values.

    Default: ``15m``

notify
    Select notification backend(s) for new comments, separated by comma.
    Available backends:

    stdout
        Log to standard output. Default, if none selected. Note, this
        functionality is broken since a few releases.

    smtp
        Send notifications via SMTP on new comments with activation (if
        moderated) and deletion links.

    Default: ``stdout``

reply-notifications
    Allow users to request E-mail notifications for replies to their post.

    It is highly recommended to also turn on moderation when enabling this
    setting, as Isso can otherwise be easily exploited for sending spam.

    Default: ``false``

log-file
    Log console messages to file instead of standard out.

    Default: (empty)

gravatar
    When set to ``true`` this will add the property "gravatar_image"
    containing the link to a gravatar image to every comment. If a comment
    does not contain an email address, gravatar will render a random icon.
    This is only true when using the default value for "gravatar-url"
    which contains the query string param ``d=identicon`` ...

    Default: ``false``

gravatar-url
    Url for gravatar images. The ``{}`` is where the email hash will be placed.

    Default: ``https://www.gravatar.com/avatar/{}?d=identicon&s=55``

latest-enabled
    If true it will enable the ``/latest`` endpoint.

    Default: ``false``


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
    Enable comment moderation queue. This option only affects new comments.
    Comments in moderation queue are not visible to other users until you
    activate them.

    Default: ``false``

approve-if-email-previously-approved
    Automatically approve comments by an email address if that address has
    had a comment approved within the last 6 months. No ownership verification
    is done on the entered email address. This means that if someone is able
    to guess correctly the email address used by a previously approved author,
    they will be able to have their new comment auto-approved.

    Default: ``false``

purge-after
    Remove unprocessed comments in moderation queue after given time.

    Default: ``30d``


.. _configure-server-block:

Server
------

HTTP server configuration.

.. code-block:: ini

    [server]
    listen = http://localhost:8080
    public-endpoint =
    reload = false
    profile = false
    trusted-proxies =
    samesite =

listen
    Interface to listen on. Isso supports TCP/IP and unix domain sockets:

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

    Default: ``http://localhost:8080``

public-endpoint
    Public URL that Isso is accessed from by end users. Should always be
    a ``http://`` or ``https://`` absolute address. If left blank, automatic
    detection is attempted. Normally only needs to be specified if different
    than the ``listen`` setting.

    This URL must not end in a ``/`` slash, i.e. ``http://foo.bar:8080/`` is
    forbidden but ``http://foo/bar:8080`` is fine.

    Default: (empty)

    .. versionchanged:: 0.13
        Trailing slash now forbidden.

reload
    Reload application, when the source code has changed. Useful for
    development. Only works with the internal webserver.

    Default: ``false``

profile
    Show 10 most time consuming function in Isso after each request. Do
    not use in production.

    Default: ``false``

trusted-proxies
    An optional list of reverse proxies IPs behind which you have deployed
    your Isso web service (e.g. `127.0.0.1`).
    This allow for proper remote address resolution based on a
    `X-Forwarded-For` HTTP header, which is important for the mechanism
    forbiding several comment votes coming from the same subnet.

    Default: (empty)

samesite
    Override ``Set-Cookie`` header ``SameSite`` value.
    Needed for setups where isso is not hosted on the same domain, e.g. called
    from example.org and hosted under comments.example.org.
    By default, isso will set ``SameSite=None`` when served over https and
    ``SameSite=Lax`` when served over http
    (see `MDM: SameSite <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite>`_
    and `#682 <https://github.com/posativ/isso/issues/682>`_ for details).

    Accepted values: ``None``, ``Lax``, ``Strict``

    Default: (empty)

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
    Self-explanatory, *optional*

    Default: (empty)

password
    self-explanatory (yes, plain text, create a dedicated account for
    notifications), *optional*.

    Default: (empty)

host
    SMTP server

    Default: ``localhost``

port
    SMTP port

    Default: ``587``

security
    Use a secure connection to the server.

    Accepted values: ``none``, ``starttls``, ``ssl``

    Default: ``starttls``

    .. todo: Following is outdated.
       Note that there is no easy way for Python 2.7 and 3.3 to implement
       certification validation and thus the connection is vulnerable to
       Man-in-the-Middle attacks. You should definitely use a dedicated SMTP
       account for Isso in that case.

to
    Recipient address, e.g. your email address

    Default: (empty)

from
    Sender address, e.g. ``"Foo Bar" <isso@example.tld>``

    Default: (empty)

timeout
    Specify a timeout in seconds for blocking operations like the
    connection attempt.

    Default: ``10``


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
    Enable guard, recommended in production. Not useful for debugging
    purposes.

    Default: ``true``

ratelimit
    Limit to N new comments per minute.

    Default: ``2``

direct-reply
    How many comments directly to the thread (prevent a simple
    `while true; do curl ...; done`.

    Default: ``3``

reply-to-self
    Allow commenters to reply to their own comments when they could still edit
    the comment. After the editing timeframe is gone, commenters can reply to
    their own comments anyways.

    Default: ``false``

require-author
    Force commenters to enter a value into the author field. No validation is
    performed on the provided value.

    Default: ``false``

require-email
    Force commenters to enter a value into the email field. No validation is
    performed on the provided value.

    Default: ``false``

.. _configure-markup:

Markup
------

Customize markup and sanitized HTML. Currently, only Markdown (via Misaka) is
supported, but new languages are relatively easy to add.
For a more detailed explanation, see :doc:`/docs/reference/markdown-config`.

.. code-block:: ini

    [markup]
    options = strikethrough, superscript, autolink, fenced-code
    flags =
    allowed-elements =
    allowed-attributes =

options
    `Misaka-specific Markdown extensions <https://misaka.61924.nl/#api>`_, all
    extension options can be used there, separated by comma, either by their
    name (``fenced-code``) or as ``EXT_FENCED_CODE``.

    Note: Use e.g. ``fenced-code`` (with a ``-`` dash) instead of
    ``fenced_code`` (underline) to refer to extension names.

    For a more detailed explanation, see
    :ref:`Markdown Configuration: Extensions <available-markdown-options>`

    Default: ``strikethrough, superscript, autolink, fenced-code``

flags
    `Misaka-specific HTML rendering flags
    <https://misaka.61924.nl/#html-render-flags>`_, all html rendering flags
    can be used here, separated by comma, either by their name (``hard-wrap``)
    or as e.g. ``HTML_HARD_WRAP``.

    For a more detailed explanation, see :doc:`/docs/reference/markdown-config`.

    Default: (empty)

    .. versionadded:: 0.12.4

allowed-elements
    **Additional** HTML tags to allow in the generated output, comma-separated.

    By default, only ``a``, ``blockquote``, ``br``, ``code``, ``del``, ``em``,
    ``h1``, ``h2``, ``h3``, ``h4``, ``h5``, ``h6``, ``hr``, ``ins``, ``li``,
    ``ol``, ``p``, ``pre``, ``strong``, ``table``, ``tbody``, ``td``, ``th``,
    ``thead`` and ``ul`` are allowed.

    For a more detailed explanation, see :doc:`/docs/reference/markdown-config`.

    .. warning::

       This option (together with ``allowed-attributes``) is frequently
       misunderstood. Setting e.g. this list to only ``a, blockquote`` will
       mean that ``br, code, del, ...`` and all other default allowed tags are
       still allowed. You can only add *additional* elements here.

       It is planned to change this behavior, see
       `this issue <https://github.com/posativ/isso/issues/751>`_.

    Default: (empty)

allowed-attributes
    **Additional** HTML attributes (independent from elements) to allow in the
    generated output, comma-separated.

    By default, only ``align`` and ``href`` are allowed (same caveats as for
    ``allowed-elements`` above apply)

    For a more detailed explanation, see :doc:`/docs/reference/markdown-config`.

    Default: (empty)

.. note:: To allow images in comments, you need to add
   ``allowed-elements = img`` and *also* ``allowed-attributes = src``.

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

    Default: ``Eech7co8Ohloopo9Ol6baimi``

algorithm
    Hash algorithm to use -- either from Python's ``hashlib`` or PBKDF2 (a
    computational expensive hash function).

    The actual identifier for PBKDF2 is ``pbkdf2:1000:6:sha1``, which means
    1000 iterations, 6 bytes to generate and SHA1 as pseudo-random family used
    for key strengthening.
    Arguments have to be in that order, but can be reduced to ``pbkdf2:4096``
    for example to override the iterations only.

    Default: ``pbkdf2``

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
    Base URL to use to build complete URI to pages (by appending the URI from Isso)

    Default: (empty)

limit
    number of most recent comments to return for a thread

    Default: ``100``

Admin
-----

.. _configure-admin:

Isso has an optional web administration interface that can be used to moderate
comments. The interface is available under ``/admin`` on your isso URL.

.. code-block:: ini

   [admin]
   enabled = true
   password = please_choose_a_strong_password

enabled
   Whether to enable the admin interface

   Default: ``false``

password
   The plain text password to use for logging into the administration interface

   Default: ``please_choose_a_strong_password``

Appendum
--------

.. _appendum-timedelta:

Timedelta
    A human-friendly representation of a time range: `1m` equals to 60
    seconds. This works for years (y), weeks (w), days (d) and seconds (s),
    e.g. `30s` equals 30 to seconds.

    You can add different types: `1m30s` equals to 90 seconds, `3h45m12s`
    equals to 3 hours, 45 minutes and 12 seconds (12512 seconds).

.. _appendum-values:

URLs
    Strings should not contain quotes, e.g. ``public-endpoint = https://isso.dev``
    is correct, ``= "https://isso.dev"`` is wrong
Booleans
    For items that can be turned either on or off, acceptable values are (see
    `getboolean`_):

    - For ``True``, use ``1``, ``yes``, ``true``, or ``on``
    - For ``False``, use ``0``, ``no``, ``false``, or ``off``

.. todo:: Unify on ``true``/``false`` and remove occurrences of
   ``on``/``off`` etc.

.. _getboolean: https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.getboolean
