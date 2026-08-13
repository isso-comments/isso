Technical Documentation: Server
===============================

Dependencies
------------

Isso uses some of the following dependencies:

- `werkzeug <https://github.com/mitsuhiko/werkzeug>`_ – WSGI toolkit
- `itsdangerous <https://github.com/mitsuhiko/itsdangerous>`_ – store signed data on untrusted clients
- `misaka <http://misaka.61924.nl/>`_ – fast Markdown processor written in C, not maintained anymore
  and optional, being replaced by mistune, see next point
- `mistune <https://mistune.lepture.com/>`_ – a fast yet powerful Python Markdown parser
- `html5lib <https://github.com/html5lib/html5lib-python>`_ – HTML(5) parser and sanitizer

Security
--------

- **HTML sanitization:** Isso sanitizes the HTML generated from comment
  Markdown with ``bleach``. The default renderer (Mistune) also escapes raw
  HTML in comments.

- **Signed cookies:** Isso uses ``itsdangerous`` to sign the cookies used
  for administrator sessions and comment editing.

- **Field length limits:** Each submitted comment field is limited to 65535
  characters. Some fields like ``email`` is limited to `254 characters <http://tools.ietf.org/html/rfc5321#section-4.5.3>`__.

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/isso-comments/isso/issues/797>`_
   for further information.

   **What's missing?**

   - Technologies used (flask, werkzeug, misaka, ...)
   - Explain code structure
   - Request handling and HTTP
   - Database handling code
   - Comment schema
   - Comment (Markdown) rendering using misaka and custom extensions
   - Cross-Origin Resource Sharing (CORS)
   - Content Security Policy
   - Future plans: Rewrite/Refactor, SQLAlchemy, MVC

   ... and other things about the server that should be documented.
