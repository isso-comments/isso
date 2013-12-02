Contribute
==========

Write some code.
----------------

I appreciate any help and love pull requests. Here are some things you
need to respect:

*  no hard-wired external services (e.g. Gravatar, Akismet)
*  no support for ancient browsers (e.g. IE6-9)

If you create a feature request, start a new branch. If you fix an
issue, start off the *master* branch and pull request against the
master. I'll cherry-pick/backport the fix onto the current legacy
(maintenance) release.

Report issues
-------------

- **Disqus import fails** – if ``isso import /path/to/disqus.xml`` fails,
  please do *NOT* attach the raw dump file to GH:Issues. Please anonymize all
  IP addresses inside the ``<ipAddress>`` tag first, as second step, replace
  all ``<email>`` addresses with a generic one.

- **embed.min.js-related issues** –  if you get a cryptic JavaScript error in
  the console, embed ``embed.dev.js`` instead of ``embed.min.js`` and create an
  issue with ±10 lines of code around the error.

- **Isso-related issues** – Copy and paste traceback into a ticket and provide
  some details of your usage.

Where I need help.
------------------

Isso is my first projects which involves JavaScript. If you are more
experienced in JS, please take a look at the code (that does not mean, the
Python code is perfect ;-). A few feature requests and issues, where I
definitely need help:

* `Admin Web Interface <https://github.com/posativ/isso/issues/10>`_ –
  administration via email is cumbersome with a high amount of comments. A
  administration web interface should include the ability to:

  - delete or activate comments matching a filter (e.g. name, email, ip address)

  - close threads and remove threads completely

  - edit comments

* `Pagination <https://github.com/posativ/isso/issues/14>`_ – while Isso is
  generally a lot faster than Disqus, after approx. 50 comments you will
  notice roughly 1 second rendering time. It would be nice if the client
  fetches only N comments and continues when the user scrolls down (or click
  on a button to fetch more).

* CSS improvements. For some websites, the Isso integration just looks ugly.
  If you can improve it, please do it :)
