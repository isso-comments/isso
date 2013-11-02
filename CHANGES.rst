Changelog for Isso
==================

0.3.2 (unreleased)
------------------

- Nothing changed yet.


0.3.1 (2013-11-02)
------------------

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

