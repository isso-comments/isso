:orphan:

News
====

Isso version 0.13.0 released
----------------------------

*Date: 2022-06-12*

New Features
^^^^^^^^^^^^

- Add ``data-isso-reply-notifications-default-enabled`` option to configure
  whether or not the subscribe to replies checkbox should be checked by default.
  (`#846`_, BBaoVanC)
- Accessibility: Use labels rather than placeholders for name, email & website
  in post box (`#861`_, ix5)
- Add ``data-isso-page-author-hashes`` option to client which makes it possible
  to style comments and replies made by the page's author(s).
- Add Ukrainian localisation (`#878`_, okawo80085)
- Enable Turkish localisation (`#879`_)

Breaking Changes
^^^^^^^^^^^^^^^^

- css, js: Prefix all classes with ``isso-`` (`#816`_, ix5)
  Now Isso's CSS is "namespaced" in order not to conflict with other classes on
  the page.
  This change necessitates adjusting custom CSS files to the new names.
- Drop support for outdated Python version 3.5 (`#808`_, l33tname)
- Strip trailing slash from ``public-endpoint``. A trailing slash in ``[server]
  public-endpoint`` is now discouraged and throws a warning (`#876`_, ix5)

Bugfixes & Improvements
^^^^^^^^^^^^^^^^^^^^^^^

- Replace ``contenteditable`` ``div`` with ``textarea`` to fix issues when
  editing messages that contain indented code (`#887`_, BBaoVanC)
- Fix avatar sizing, limit default gravatar images to 55px (`#831`_, l33tname)
  In case of a custom gravatar URL, the ``&s=55`` size parameter will have
  to be added, see `Gravatar - Image requests`_.
- Re-enable ``no-intra-emphasis`` misaka extension in default config (`#865`_, ix5)
- Allow ``sup`` and ``sub`` HTML elements by default (`#865`_, ix5)
- Move ``isso-dev.cfg`` to ``contrib/`` folder (`#882`_, ix5)
- Drop ``Flask-Caching`` dependency and use drop-in solution instead (`#893`_, ix5)
- Run automated screenshot comparisons for testing (`#889`_, ix5)
- wsgi: Return HTTP errors as JSON if client prefers it (`#488`_, sundbry)
- Verify that parent of new comment is in same thread (`#885`_, ix5)
- When importing from WordPress single newlines are now converted to line breaks
  (`#903`_, projectgus)
- **API:**

  - Add ``/config`` endpoint for fetching server configuration options that
    affect the client (`#880`_, ix5)
  - Remove ``/count`` GET endpoint (use POST instead) (`#883`_, ix5)

.. _Gravatar - Image requests: http://en.gravatar.com/site/implement/images/
.. _#488: https://github.com/posativ/isso/pull/488
.. _#808: https://github.com/posativ/isso/pull/808
.. _#816: https://github.com/posativ/isso/pull/816
.. _#831: https://github.com/posativ/isso/pull/831
.. _#846: https://github.com/posativ/isso/pull/846
.. _#861: https://github.com/posativ/isso/pull/861
.. _#865: https://github.com/posativ/isso/pull/865
.. _#876: https://github.com/posativ/isso/pull/876
.. _#878: https://github.com/posativ/isso/pull/878
.. _#879: https://github.com/posativ/isso/pull/879
.. _#880: https://github.com/posativ/isso/pull/880
.. _#882: https://github.com/posativ/isso/pull/882
.. _#883: https://github.com/posativ/isso/pull/883
.. _#885: https://github.com/posativ/isso/pull/885
.. _#887: https://github.com/posativ/isso/pull/887
.. _#889: https://github.com/posativ/isso/pull/889
.. _#893: https://github.com/posativ/isso/pull/893
.. _#903: https://github.com/posativ/isso/pull/903

Isso version 0.13.0.beta1 released
----------------------------------

*Date: 2022-06-05*

New Features
^^^^^^^^^^^^

- Add ``data-isso-reply-notifications-default-enabled`` option to configure
  whether or not the subscribe to replies checkbox should be checked by default.
  (`#846`_, BBaoVanC)
- Accessibility: Use labels rather than placeholders for name, email & website
  in post box (`#861`_, ix5)
- Add ``data-isso-page-author-hashes`` option to client which makes it possible
  to style comments and replies made by the page's author(s).
- Add Ukrainian localisation (`#878`_, okawo80085)
- Enable Turkish localisation (`#879`_)

Breaking Changes
^^^^^^^^^^^^^^^^

- css, js: Prefix all classes with ``isso-`` (`#816`_, ix5)
  Now Isso's CSS is "namespaced" in order not to conflict with other classes on
  the page.
  This change necessitates adjusting custom CSS files to the new names.
- Drop support for outdated Python version 3.5 (`#808`_, l33tname)
- Strip trailing slash from ``public-endpoint``. A trailing slash in ``[server]
  public-endpoint`` is now discouraged and throws a warning (`#876`_, ix5)

Bugfixes & Improvements
^^^^^^^^^^^^^^^^^^^^^^^

- Replace ``contenteditable`` ``div`` with ``textarea`` to fix issues when
  editing messages that contain indented code (`#887`_, BBaoVanC)
- Fix avatar sizing, limit default gravatar images to 55px (`#831`_, l33tname)
  In case of a custom gravatar URL, the ``&s=55`` size parameter will have
  to be added, see `Gravatar - Image requests`_.
- Re-enable ``no-intra-emphasis`` misaka extension in default config (`#865`_, ix5)
- Allow ``sup`` and ``sub`` HTML elements by default (`#865`_, ix5)
- Move ``isso-dev.cfg`` to ``contrib/`` folder (`#882`_, ix5)
- Drop ``Flask-Caching`` dependency and use drop-in solution instead (`#893`_, ix5)
- Run automated screenshot comparisons for testing (`#889`_, ix5)
- wsgi: Return HTTP errors as JSON if client prefers it (`#488`_, sundbry)
- Verify that parent of new comment is in same thread (`#885`_, ix5)
- **API:**

  - Add ``/config`` endpoint for fetching server configuration options that
    affect the client (`#880`_, ix5)
  - Remove ``/count`` GET endpoint (use POST instead) (`#883`_, ix5)

.. _Gravatar - Image requests: http://en.gravatar.com/site/implement/images/
.. _#488: https://github.com/posativ/isso/pull/488
.. _#808: https://github.com/posativ/isso/pull/808
.. _#816: https://github.com/posativ/isso/pull/816
.. _#831: https://github.com/posativ/isso/pull/831
.. _#846: https://github.com/posativ/isso/pull/846
.. _#861: https://github.com/posativ/isso/pull/861
.. _#865: https://github.com/posativ/isso/pull/865
.. _#876: https://github.com/posativ/isso/pull/876
.. _#878: https://github.com/posativ/isso/pull/878
.. _#879: https://github.com/posativ/isso/pull/879
.. _#880: https://github.com/posativ/isso/pull/880
.. _#882: https://github.com/posativ/isso/pull/882
.. _#883: https://github.com/posativ/isso/pull/883
.. _#885: https://github.com/posativ/isso/pull/885
.. _#887: https://github.com/posativ/isso/pull/887
.. _#889: https://github.com/posativ/isso/pull/889
.. _#893: https://github.com/posativ/isso/pull/893

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
