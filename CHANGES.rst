Changelog for Isso
==================

0.4.1 (2013-11-13)
------------------

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

