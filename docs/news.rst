:orphan:

News
====

Isso version 0.12.6.2 released
------------------------------

*Date: 2022-04-23*

- Hotfix release to note compatibility with werkzeug 2.1+

Isso version 0.12.6.1 released
------------------------------

*Date: 2022-03-20*

- Hotfix release to restore position of Postbox before comments
  (#815, ix5)

Isso version 0.12.6 released
----------------------------

*Date: 2022-03-06*

- Serve isso.css separately to avoid ``style-src: unsafe-inline`` CSP and allow
  clients to override fetch location (#704, ix5):

  .. code-block:: html

      data-isso-css-url="https://comments.example.org/css/isso.css"

- New "samesite" option in [server] section to override SameSite header for
  cookies. (#700, ix5)
- Fallback for SameSite header depending on whether host is served over https
  or http (#700, ix5)
- Have client read out shared settings from server. (#311, pellenilsson)
  This affects these settings for which ``data-isso-*`` values will be ignored:

  .. code-block:: ini

      [general]
      reply-notifications
      gravatar
      [guard]
      reply-to-self
      require-author
      require-email
- Improved detection of browser-supplied language preferences (#521)
  Isso will now honor the newer ``navigator.languages`` global property
  as well as ``navigator.language`` and ``navigator.userLanguage``.
  There is a new configuration property ``data-isso-default-lang``
  that specifies the language to use (instead of English) when none
  of these is available.  (The existing ``data-isso-lang`` *overrides*
  browser-supplied language preferences.)
- Remove ``ISSO_CORS_ORIGIN`` environ variable, which never worked at all
  (#803, ix5)
