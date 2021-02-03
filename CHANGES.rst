Changelog for Isso
==================

0.12.4 (2021-02-03)
-------------------

- Require Python >= 3.5, for consistency with werkzeug.
  (#698, Stefan Gehn)

- Use npm for pacakge installation.
  (#695, Stefan Gehn)

- Use sassc. (Stefan Gehn)

- Cope with broken HTTP clients that require specific casing of
  "200 OK". (#646, #347, Konzertheld)

- Add European Portuguese translation. (#692, boturon)

- Various doc updates. (ix5)

- Add Turkish translation. (Özcan Oğuz, #669)

- Drop Python 2 support. (Jelmer Vernooĳ)

0.12.3 (2020-02-22)
-------------------

- New "flags" option in the [markdown] section to customize Misaka's Markdown
  HTML rendering. By default, no flags are set.

      [markup]
      flags = skip-html, escape, hard-wrap

  Check docs/configuration/server.rst for more details. #616

* Fix compatibility with newer versions of werkzeug. #614

* Add Python 3.8 support. #600, #615

* New 'latest' endpoint to serve latest comments. #556

* include admin.js in Python Package. #606

* Add a approve-if-email-previously-approved setting.

* Fall back to author names in gravatars (#482)

* Make Isso compatible with Content Security Policies without `script-src 'unsafe-inline'`. #597

* Set subject for notification about new comment, subject should not be empty. #589

* Fix rendering of disabled.html for 'Sub URI' sites.

* contrib: Add Blogger importer tool. #529

* Return 200 with empty array when there are no comments. #301

* Translation updates for Polish, Slovak, Occitan.

* Redirect to comment after moderation. #358


0.12.2 (2019-01-21)
-------------------

- Revert use of labels instead of placeholders, since it breaks
  mail notifications. #524

0.12.1 (2019-01-19)
-------------------

- Revert fix for duplicate slashes, as it prevents isso from
  starting in some cases. #523

0.12.0 (2019-01-18)
-------------------

- Fix compatibility with new XML API.
- Don't enable admin interface with default password by default.  #491
- Add support and documentation for "generic" imports.
- Remove potential duplicate slashes in URLs from
  email links. #420
- Add data-isso-reply-notifications to attributes in configuration.
- Use default IP in imports if none is found. Fixes imports of some comments.
- embed: fix feed link creation on older browsers.
- Properly handle to field in mail notifications when using uWSGI spooler
- css: fix vertical alignment of notification checkbox

0.11.1 (2018-11-03)
-------------------

- Include pre-built minified JavaScript and CSS.

0.11.0 (2018-11-03)
-------------------

Bugs & features:

- Fix link in moderation mails if isso is setup on a sub-url (e.g. domain.tld/comments/)
- Add reply notifications
- Add admin interface
- Add links highlighting in comments
- Add apidoc
- Add rc.d script for FreeBSD
- Add the possibility to set CORS Origin through ISSO_CORS_ORIGIN environ variable
- Add preview button
- Add Atom feed at /feed?uri={thread-id}
- Add optionnal gravatar support
- Add nofollow noopener on links inside comments
- Add Dockerfile
- Upgraded to Misaka 2
- Some tests/travis/documentation improvements and fixes + pep8

Translations:

- Fix Chinese translation & typo in CJK
- Add Danish translation
- Add Hungarian translation
- Add Persian translation
- Improvement on german translation

0.10.6 (2016-09-22)
-------------------

- fix missing configuration field


0.10.5 (2016-09-20)
-------------------

- add support for different vote levels, #260

  List of vote levels used to customize comment appearance based on score.
  Provide a comma-separated values (eg. `"0,5,10,25,100"`) or a JSON array (eg.
  `"[-5,5,15]"`).

  For example, the value `"-5,5"` will cause each `isso-comment` to be given
  one of these 3 classes:

  - `isso-vote-level-0` for scores lower than `-5`
  - `isso-vote-level-1` for scores between `-5` and `4`
  - `isso-vote-level-2` for scores of `5` and greater

  These classes can then be used to customize the appearance of comments (eg.
  put a star on popular comments).

- add new post preview API endpoint, #254

- add an option for mandatory author, #257

- clients can now use `data-title` to get the HTML title for a new page, #252

- add finish translation and other minor bugfixes


0.10.4 (2016-04-12)
-------------------

- fix wrapper attribute when using data-isso-require-mail="true", #238
- fix reponse for OPTIONS response on Python 3, #242


0.10.3 (2016-02-24)
-------------------

- follow redirects, #193


0.10.2 (2016-02-21)
-------------------

- fix getAttribute return value


0.10.1 (2016-02-06)
-------------------

- fix empty author, email and website values when writing a comment


0.10 (2016-02-06)
-----------------

- add new configuration section for hash handling.

    [hash]
    salt = Eech7co8Ohloopo9Ol6baimi
    algorithm = pbkdf2

  You can customize the salt, choose different hash functions and tweak the
  parameters for PBKDF2.

- Python 3.4+ validate TLS connections against the system's CA. Previously no
  validation was in place, see PEP-446__ for details.

- add `fenced_code` and `no_intra_emphasis` to default configuration.

  Fenced code allows to write code without indentation using `~~~` delimiters
  (optionally with language identifier).

  Intra emphasis would compile `foo_bar_baz` to foo<em>bar</em>baz. This
  behavior is very confusing for users not knowing the Markdown spec in detail.

- new configuration to require an email when submitting comments, #199. Set

    [guard]
    require-email = true

  and use `data-isso-require-email="true"` to enable this feature. Disabled by
  default.

- new Bulgarian translation by sahwar, new Swedish translation by Gustav
  Näslund – #143, new Vietnamese translation by Đinh Xuân Sâm, new Croatian
  translation by streger, new Czech translation by Jan Chren

- fix SMTP setup without credentials, #174

- version pin Misaka to 1.x, html5lib to 0.9999999

.. __: https://www.python.org/dev/peps/pep-0466/


0.9.10 (2015-04-11)
-------------------

- fix regression in SMTP authentication, #174


0.9.9 (2015-03-04)
------------------

- several Python 3.x related bugfixes

- don't lose comment form if the server rejected the POST request, #144

- add localStorage fallback if QUOTA_EXCEEDED_ERR is thrown (e.g. Safari
  private browsing)

- add '--empty-id' flag to Disqus import, because Disqus' export sucks

- (re)gain compatibility with Werkzeug 0.8 and really old html5lib versions
  available in Debian Squeeze, #170 & #168

- add User-Agent when Isso requests the URL, an alternate way to #151 (add
  'X-Isso' when requesting).

0.9.8 (2014-10-08)
------------------

- add compatibility with configparser==3.5.0b1, #128


0.9.7 (2014-09-25)
------------------

- fix SMTP authentication using CRAM-MD5 (incorrect usage of
  `smtplib`), #126


0.9.6 (2014-08-18)
------------------

- remember name, email and website in localStorage, #119

- add option to hide voting feature, #115

    data-isso-vote="true|false"

- remove email field from JSON responses

  This is a quite serious issue. For the identicon, an expensive hash is used
  to avoid the leakage of personal information like a real email address. A
  `git blame` reveals, the email has been unintenionally exposed since the very
  first release of Isso :-/

  The testsuite now contains a dedicated test to prevent this error in the
  future.


0.9.5 (2014-08-10)
------------------

- prevent no-break space (&nbsp;) insertion to enable manual line breaks using
  two trailing spaces (as per Markdown convention), #112

- limit request size to 256 kb, #107

  Previously unlimited or limited by proxy server). 256 kb is a rough
  approximation of the next database schema with comments limited to 65535
  characters and additional fields.

- add support for logging to file, #103

    [general]
    log-file =

- show timestamp when hovering <time>, #104

- fix a regression when editing comments with multiple paragraphs introduced
  in 0.9.3 which would HTML escape manually inserted linebreaks.


0.9.4 (2014-07-09)
------------------

- fixed a regression when using Isso and Gevent


0.9.3 (2014-07-09)
------------------

- remove scrollIntoView while expanding further comments if a fragment is used
  (e.g. #isso-thread brought you back to the top, unexpectedly)

- implement a custom Markdown renderer to support multi-line code listings. The
  extension "fenced_code" is now enabled by default and generates HTML
  compatible with Highlight.js__.

- escape HTML entities when editing a comment with raw HTML

- fix CSS for input

- remove isso.css from binary distribution to avoid confusion (it's still there
  from the very first release, but modifications do not work)

.. __: http://highlightjs.org/


0.9 (2014-05-29)
----------------

- comment pagination by Srijan Choudhary, #15

  Isso can now limit the amount of comments shown by default and add link to
  show more. By default, all top-level comments are shown but only 5 nested
  comments (per reply). You can override the settings:

    isso-data-max-comments-top="N"
    isso-data-max-comments-nested="N"

  Where N is a number from 0 to infinity ("inf"). If you limit the amount of
  shown top level comments, the overall comment count may be incorrect and a
  known issue.

  You can also configure the amount of comments shown per click (5 by default):

    isso-data-reveal-on-click="N"

  This feature also required a change in the comment structure. Previously, all
  comments are stored tree-like but shown linearly. To ease the implementation
  of pagination, the comment tree is now limited to a maximum depth of one.
  Jeff Atwood explains, why `discussions are flat by design`__.

  .. __: http://blog.codinghorror.com/web-discussions-flat-by-design/

  When you upgrade, Isso will automatically normalize the tree and some
  information gets lost. All new replies to a comment are now automatically a
  direct child of the top-level comment.

- style improvements by William Dorffer, #39, #84 #90 and #91

  Isso now longer uses a fat SCSS library, but plain CSS instead. The design is
  now responsive and no longer sets global CSS rules.

- experimental WordPress import, #75

  Isso should be able to import WXR 1.0-1.2 exports. The import code is based
  on two WXR dumps I found (and created) and may not work for you. Please
  report any failure.

- avatar changes, #49

  You can now configure the client to not show avatars:

    data-isso-avatar="false"

  Also there is no longer an avatar shown next to the comment box. This is due
  to the new CSS and removes two runtime dependencies.

- you may now set a full From header, #87

    [smtp]
    from = Foo Bar <spam@local>

- SMTP (all caps) is now recognized for notifications, #95

- Isso now ships a small demo site at /demo, #44

- a few bugfixes: Disqus import now anonymizes IP addresses, uWSGI spooling for
  Python 3, HTTP-Referer fallback for HTTP-Origin

- remove Django's PBKDF2 implementation in favour of the PBKDF2 function
  available in werkzeug 0.9 or higher. If you're still using werkzeug 0.8, Isso
  imports passlib__ as fallback (if available).


This release also features a new templating engine Jade__ which replaces
Markup.js__. Jade can compile directly to JavaScript with a tiny runtime module
on the client. Along with the removal of sha1.js and pbkdf2.js and a few build
optimizations, the JS client now weighs only 40kb (12kb gzipped) – 52kb resp.
17kb before.

.. __: https://pypi.python.org/pypi/passlib
.. __: http://jade-lang.com/
.. __: https://github.com/adammark/Markup.js


0.8 (2014-03-28)
----------------

- replace ``<textarea>`` with ``<div contentedtiable="true">`` to remove the
  sluggish auto-resize on input feature. If you use a custom CSS, replace
  ``textarea`` with ``.textarea`` and also set ``white-space: pre``.

- remove superscript extension from Markdown defaults as it may lead to
  unexpected behavior for certain smileys such as "^^". To enable the extension,
  add

    [markup]
    options = superscript
    allowed-elements = sup

  to your configuration.

- comment count requests are now bundled into a single POST request, but the old
  API is still there (deprecated though).

- store *session-key* in database (once generated on database creation). That
  means links to activate, edit or delete comments are now always valid even
  when you restart Isso.

  Currently statically set session keys in ``[general]`` are automatically
  migrated into the database on startup and you will get a notice that you can
  remove this option.

- fix undefined timestamp when client time differs for more than 1 second.
  The human-readable "time ago" deltas have been refined to match `Moment.js`_
  behavior.

- avatar colors and background can now be customized:

  * ``data-isso-avatar-bg="#f0f0f0"`` sets the background color
  * ``data-isso-avatar-fg="#9abf88 #5698c4 #e279a3 #9163b6 ..."`` sets possible
    avatar colors (up to 8 colors are possible).

- new [markup] section to customize Misaka's Markdown generation (strikethrough,
  superscript and autolink enabled by default). Furthermore, you can now allow
  certain HTML elemenets and attributes in the generated output, e.g. to enable
  images, set

      [markup]
      allowed-elements = img
      allowed-attributes = src

  Check docs/configuration/server.rst for more details.

- replace requirejs-domready with a (self-made) HTML5 idiom, #51

.. _Moment.js: http://momentjs.com/docs/#/displaying/fromnow/


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

