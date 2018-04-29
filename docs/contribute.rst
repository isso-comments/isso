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

Translations
------------

Isso supports multiple languages and it is fairly easy to add new translations.
You can either use the `english translation file`__ or use Transifex_. Contact
me on IRC (@posativ) if you want to be the main contributor for a language.

You may notice some "weird" newlines in translations -- that's the separator
for pluralforms_ in the templating engine.

.. __: https://github.com/posativ/isso/blob/master/isso/js/app/i18n/en.js
.. _Transifex: https://www.transifex.com/projects/p/isso/
.. _pluralforms: http://docs.translatehouse.org/projects/localization-guide/en/latest/l10n/pluralforms.html?id=l10n/pluralforms

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
