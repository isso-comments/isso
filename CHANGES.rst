Changelog for Isso
==================

0.8 (unreleased)
----------------

- Nothing changed yet.


0.7 (2014-01-29)
----------------

- fix malicious HTML injection (due to wrong API usage). All unknown/unsafe
  HTML tags are now removed from the output (`html5lib` 0.99(9) or later) or
  properly escaped (older `html5lib` versions).

  See 36d702c and 3a1f92b for more details.

- remove kriskowal/q JS library (promises implementation) in favour of a
  self-made 50 LoC implementation to ease packaging (for Debian), #51

- add documentation to display a comment counter, #56 and #57

- SMTP notifications now support STARTTLS and use this transport security
  by default, #48 and #58. This also changes the configuration option from
  `ssl = [yes|no]` to `security = [none|starttls|ssl]`.

- translation can now be made (and updated) with Transifex_. If you want to
  take ownership for a language, contact me on IRC.

- fix french pluralform

- the (by default random) session-key is now shown on application startup
  to make different keys per startup more visible
- use `threading.lock` by default for systems without semaphore support

.. _Transifex: https://www.transifex.com/projects/p/isso/


0.6 (2013-12-16)
----------------

Major improvements:

- override thread discovery with data-isso-id="...", #27

  To use the same thread for different URLs, you can now add a custom
  ``data-isso-id="my-id"`` attribute which is used to identify and retrieve
  comments (defaults to current URL aka `window.location.pathname`).

- `isso.dispatch` now dispatches multiple websites (= configurations) based on
  URL prefixes

- fix a cross-site request forgery vulnerability for comment creation, voting,
  editing and deletion, #40

- show modal dialog to confirm comment deletion and activation, #36

- new, comprehensive documentation based on reST + Sphinx:
  http://posativ.org/docs (or docs/ in the repository). Also includes an
  annotated `example.conf`, #43

- new italian and russian translations

Minor improvements:

- move `isso:application` to `isso.run:application` to avoid uneccessary
  initialization in some cases (change module if you use uWSGI or Gunicorn)
- add Date header to email notifications, #42
- check for blank text in new comment, #41
- work around IE10's HTML5 abilities for custom data-attributes
- add support for Gunicorn (and other pre-forking WSGI servers)


0.5 (2013-11-17)
----------------

Major improvements:

- `listen` option replaces `host` and `port` to support UNIX domain sockets, #25

  Instead of `host = localhost` and `port = 8080`, use
  `listen = http://localhost:8080`. To listen on a UNIX domain socket, replace
  `http://` with `unix://`, e.g. `unix:///tmp/isso.sock`.

- new option `notify` (in the general section) is used to choose (one or more)
  notification backends (currently only SMTP is available, though). Isso will
  no longer automatically use SMTP for notifications if the initial connection
  succeeds.

- new options to control the client integration

  * ``data-isso-css="false"`` prevents the client from appending the CSS to the
    document. Enabled by default.

  * ``data-isso-lang="de"`` overrides the useragent's preferred language (de, en
    and fr are currently supported).

  * ``data-isso-reply-to-self="true"`` should be set, when you allow reply to
    own comments (see server configuration for details).

- add support for `gevent <http://www.gevent.org/>`_, a coroutine-based Python
  networking library that uses greenlets (lightweight threads). Recommended
  WSGI server when not running with uWSGI (unfortunately stable gevent is not
  yet able to listen on a UNIX domain socket).

- fix a serious issue with the voters bloomfilter. During an Isso run, the
  ip addresses from all commenters accumulated into the voters bloomfilter
  for new comments. Thus, previous commenters could no longer vote other
  comments. This fixes the rare occurences of #5.

  In addition to this fix, the current voters bloomfilter will be re-initialized
  if you are using Isso 0.4 or below (this is not necessary, but on the
  other hand, the current bloomfilter for each comment is sort-of useless).

- french translation (thanks to @sploinga), #38

- support for multiple sites, part of #34

Minor improvements:

- `ipaddr` is now used as `ipaddress` fallback for Python 2.6 and 2.7, #32
- changed URL to activate and delete comments to `/id/<N:int>/activate` etc.
- import command uses `<link>` tag instead of `<id>` to extract the relative
  URL path, #37
- import command now uses `isDeleted` to mark comments as deleted (and
  eventually remove stale comments). This seems to affect only a few comments
  from a previous WordPress import into Disqus.
- import command lists orphaned comments after import.
- import command now has a ``--dry-run`` option to do no actual operation on
  the database.


0.4 (2013-11-05)
----------------

- Isso now handles cross-domain requests and cookies, fixes #24
- Isso for Python 2.x now supports werkzeug>=0.8
- limit email length to 254 to avoid Hash-DDoS
- override Isso API location with ``data-isso="..."`` in the script tag
- override HTML title parsing with a custom ``data-title="..."`` attribute
  in ``<div id="isso-thread"></div>``


0.3 (2013-11-01)
----------------

- improve initial comment loading performance in the client
- cache slow REST requests, see #18
- add a SQLite trigger that detects and removes stale threads (= threads,
  with all comments being removed) from the database when a comment is
  removed.
- PyPi releases now include an uncompressed version of the JavaScript
  files -- `embed.dev.js` and `count.dev.js` -- to track down errors.
- use uWSGI's internal locking instead of a self-made shared memory lock


0.2 (2013-10-29)
----------------

- initial PyPi release

