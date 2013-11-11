Changelog for Isso
==================

0.5 (unreleased)
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

- add an option to prevent the client from appending the CSS to the document, #29

  Enabled by default. Add `data-isso-css="false"` to the <script> tag to disable
  this behavior.

- add support for `gevent <http://www.gevent.org/>`_, a coroutine-based Python
  networking library that uses greenlets (lightweight threads). Recommended
  WSGI server when not running with uWSGI (unfortunately stable gevent is not
  yet able to listen on a UNIX domain socket).

Minor improvements:

- `ipaddr` is now used as `ipaddress` fallback for Python 2.6 and 2.7, #32
- changed URL to activate and delete comments to `/id/<N:int>/activate` etc.
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

