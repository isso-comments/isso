Contribute
==========

.. list-table:: **I am looking to...**

    * - ... :ref:`report an issue <contribute-report-issues>`
      - ... :ref:`translate Isso into my language <contribute-translations>`
      - ... :ref:`improve the documentation <contribute-docs>`
      - ... :ref:`contribute code <contribute-code>`

*The Isso community welcomes your changes. We don't bite and are happy for
anyone who donates their time and effort to the project.*

.. _contribute-report-issues:

Report issues
-------------

You are welcome report issues at the
`GitHub Issue tracker <https://github.com/posativ/isso/issues>`_.

If you need help or want to request a feature, please `open a discussion`__
instead. For more ways to get in contact, see the :doc:`/community` page.

.. __: https://github.com/posativ/isso/discussions

Here are a few general rules to keep in mind when reporting issues:

- **Disqus import fails** – if ``isso import /path/to/disqus.xml`` fails,
  please do *NOT* attach the raw dump file to GH:Issues. Please anonymize all
  IP addresses inside the ``<ipAddress>`` tag first, as second step, replace
  all ``<email>`` addresses with a generic one.

- **embed.min.js-related issues** –  if you get a cryptic JavaScript error in
  the console, embed ``embed.dev.js`` instead of ``embed.min.js`` and create an
  issue with ±10 lines of code around the error.

- **Isso-related issues** – Copy and paste traceback into a ticket and provide
  some details of your usage.

.. _contribute-translations:

Translations
------------

Isso supports multiple languages and it is fairly easy to add new translations.
You can use the `english translation file`__ and `other translations`__ as a
referece and open a Pull Request.

You may notice some "weird" newlines in translations -- that's the separator
for pluralforms_ in the templating engine.

.. __: https://github.com/posativ/isso/blob/master/isso/js/app/i18n/en.js
.. __: https://github.com/posativ/isso/blob/master/isso/js/app/i18n/
.. _pluralforms: http://docs.translatehouse.org/projects/localization-guide/en/latest/l10n/pluralforms.html?id=l10n/pluralforms

.. _contribute-docs:

Documentation
-------------

Documentation improvements are sorely needed. Anything that makes the
experience for a newcomer more pleasant is always welcome.
Please see the :doc:`documentation` page for more details.

.. _contribute-code:

Code contributions
------------------

You do not have to read this whole section; the maintainers will give you
feedback in the review process. But if you want to be a nice and helpful
person, you can make the lives of the maintainers a lot easier.

These guidelines are here to help your thought process and hopefully make you
aware of a few aspects you might not have thought about yet.

.. _contribute-checklist:

.. note:: **Submitting a change**

    1. Write **proper commit messages** (see next paragraph)
    2. If adding features: **Add or amend tests** to cover the changes
    3. Run all **test suites** (see :doc:`/docs/technical-docs/testing`) and make
       sure they pass
    4. If docs changes needed: Update the :doc:`documentation <documentation>`
       accordingly.
    5. If it's a user-facing feature or an important bugfix, add ``CHANGES.rst``
       entry
    6. Add yourself to ``CONTRIBUTORS.txt``, if you like

.. _contribute-commitmsg:

How to write good commit messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Mention the affected part in the title (e.g. ``setup.py``)
- Keep title under 50 characters if possible, at most 72
- Keep body under 80 characters of width
- Explain what the change does
- Link to related issues or references
- Ideally, how to verify that this commit does what it says

The `commento docs`_ have a more extensive explanation of good commits.

This is an example of a **good commit:**

.. code-block::

    js: Postbox: Use labels rather than placeholders

    Placeholders are is meant to be a hint (an example input)
    for the user about what to enter into the field, but
    shouldn't be used in lieu of a <label>.

    See following links for further justification:
    - https://www.tpgi.com/html5-accessibility-chops-the-placeholder-attribute/
    - https://www.nngroup.com/articles/form-design-placeholders/
    - https://www.maxability.co.in/2016/01/03/placeholder-attribute-and-why-it-is-not-accessible/

    This commit is a reland of
    https://github.com/posativ/isso/pull/356 with a fix for the
    placeholder-replacement code in `isso.js` as reported in
    https://github.com/posativ/isso/issues/524

...while this is a **bad commit:**

.. code-block::

    Fix classes

It does not tell the reviewer which part is affected, why it is necessary or
why this particular way of doing things was chosen.

.. _commento docs: https://docs.commento.io/contributing/development-guidelines.html

Considerations when submitting changes
--------------------------------------

The following sections will help you decide how to tackle larger architectural
issues and help avoid wasted efforts for changes that are unlikely to be
accepted.

Design philosophy / Zen of Isso
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Isso should not be a "move fast and break things" project.
- Be mindful of the users. They do not anxiously await a new release - they
  simply want their websites to work.
- Try to avoid breaking changes: People do not want to dig through changelogs
  to find out why suddenly their comment section is gone.

What kind of changes will be accepted?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As a rule, you want to make the life of the maintainers as easy as possible.
Removing cruft is good, as is improving tests or docs. Introducing new
features, possibly with new config options, should have good reasoning and is
harder to review.

What should I think about?

- Will everyone benefit from my contribution or is this just fixing my pet
  peeve/supporting my exotic use case?
- Will this add complexity? If many changes similar to mine are introduced, will
  this make the project more confusing and complex?
- Should this be done in a more generalized manner? As a hypothetical example,
  do not create a new toggle with ``is-submit-button-green`` or
  ``submit-button-color``, but rather create a mechanism by which the color of
  all buttons can be set.

If adding a new option/config:

- Is the option well-named? Can users already figure out what it does, without
  having to read the description?
- Is the option really necessary? Should the default behaviour be changed
  instead?
- Is the option well-documented? Is it clear what it does? Are the available
  choices well-documented?
- Is the option in the right config section?
- Backward compatibility

A config option is sort of a promise to users. They will be confused if it is
removed and their setup no longer works.

What is currently needed?
^^^^^^^^^^^^^^^^^^^^^^^^^

- **Improvements of test coverage** - really important for the project to move
  forward!
- Look at `open issues with label "needs-contributor"`__
- Look at `open issues with label "good-first-issue"`__
- Look at `open issues with label "needs-decision"`__ and chime in with your
  well thought-out opinion
- Look at `milestones`__ - the next release of Isso will be version 0.13, and
  you can help by looking for open issues and PRs that
  `contribute to 0.13 <https://github.com/posativ/isso/milestone/5>`_
- Nicer automated testing, via docker or GH actions, of most of the available
  setup options (fastcgi/proxy configs, docker, apachge/nginx, ...)

@posativ's wishlist:

- `Admin Web Interface <https://github.com/posativ/isso/issues/10>`_ –
  administration via email is cumbersome with a high amount of comments. A
  administration web interface should include the ability to:

  - Delete or activate comments matching a filter (e.g. name, email, ip address)
  - Close threads and remove threads completely

.. __: https://github.com/posativ/isso/labels/needs-contributor
.. __: https://github.com/posativ/isso/labels/good-first-issue
.. __: https://github.com/posativ/isso/labels/needs-decision
.. __: https://github.com/posativ/isso/milestones

Regarding fancy new CI tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Linters are fine, but please create sensible configs
- Nothing too "magic", AI-based
- Keep in mind that too many bots running will need constant updates and maintenance
- Nothing that compromises this project's integrity, by granting repo access to bots
- Nothing too "chatty" - it will just be ignored and increase the burden on
  maintainers even more

Complexity
^^^^^^^^^^

Isso started out as a fairly simple project, but it has grown over time.
It is built using many different technologies and moving parts

.. Try to avoid adding new dependencies to the project. Adding complexity makes it
.. exponentially harder to understand the breadth of components, makes it harder
.. to keep track of the growing list of external dependencies, and also means that
.. the maintainers will have to do even more work before merging your change - in
.. practice, they will probably not be able to find the time.

Below is a non-exhaustive list of tools, services, dependencies and
technologies Isso's contributors and maintainers need to at least peripherally
be aware of - that's a lot to demand of someone! Your aim should be to reduce
this complexity, not add to it.

.. hlist::
   :columns: 2

   * **Docs**

     -  apiDoc
     -  sphinx with reST syntax

   * **Python**

     -  Pallets project: werkzeug, jinja2, flask
     -  misaka (and changing config opts)
     -  bleach, html5lib
     -  Different python versions, OS versions
     -  setuptools, pip
     -  Python Package Index (PyPI) uploading

   * **Python testing**

     -  pytest (unit testing)
     -  coverage
     -  flake8

   * **Convenience tools**

     -  Docker
     -  Vagrant
     -  Ansible

   * **Javascript**

     -  Node.js
     -  npm
     -  package.json oddities
     -  webpack
     -  Jest
     -  puppeteer
     -  Browser compatibility and ES5/ES6 standards

   * **Development tools**

     -  make
     -  Github Actions

   * **Deployment options**

     -  ``isso run [opts]``
     -  Apache (``mod_wsgi``)
     -  Apache (``mod_fastcgi``)
     -  Apache (proxy)
     -  nginx (proxy)
     -  uwswgi
     -  gunicorn
     -  gevent

   * **Importers**

     -  Current disqus export format
     -  Current and past Wordpress export formats
