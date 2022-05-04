Writing Documentation
=====================

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - How to install & run Sphinx (note that latest sphinx from pip is needed by theme)
   - How Sphinx works, what its philosphy is
   - Small reST intro, also link to the
     `reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
   - How to write good documentation, maybe link to a few guides and example sites
   - More syntax standards, and also correct wrong usage across the docs

   ... and other things about documentation that should be documented.

Introduction
------------

The documentation for Isso is written using the `Sphinx`__ documentation
project in a markup language called ``reStructuredText`` (``reST``). The
documentation files have have ``.rst`` as a file extension.

``reST`` works a bit like Markdown, but has some differences. Here's an
example:

.. code-block:: rst

    One asterisk: *text* for emphasis (italics),
    Two asterisks: **text** for strong emphasis (boldface), and
    Backquotes: ``text`` for code samples.

.. __: https://www.sphinx-doc.org/en/master/

Building the docs
-----------------

You will need to have the latest version of the ``Sphinx`` documentation generator installed
`from PyPi <https://pypi.org/project/Sphinx/>`_.

.. warning:: Please avoid using the version installed by your operating system
   since it may be severely outdated and throw errors with Isso's theme. Isso's
   docs need at least version 4.5.0.

Install via pip:

.. code-block:: bash

   $ virtualenv .venv && $ source .venv/bin/activate
   (.venv) $ pip install sphinx
   (.venv) $ sphinx-build --version
   ~> sphinx-build 4.5.0

Build the docs:

.. code-block:: bash

   (.venv) $ make site

The stylesheets of the theme are written in a CSS-like language called
`sass <https://sass-lang.com/guide>`_ and have the ``.scss`` file extension.

If you have made any changes to the stylesheets, you need to install the
`sassc`__ program and then re-generate the CSS file at
``docs/_static/css/site.css``:

.. code-block:: bash

   apt install sassc
   make css

.. __: https://github.com/sass/sassc

How to write reST
-----------------
First and foremost, see the
`reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_.

**Links:**

.. code-block:: rst

    Use `Link text <https://domain.invalid/>`_ for **inline web links**.

    This is a paragraph that contains `a link`_ using **references**.

    .. _a link: https://domain.invalid/

**Referencing other sections:** (see `:ref:`__)

.. code-block:: rst

    .. _my-reference-label:

    Section to cross-reference
    --------------------------

    This is the text of the section.

    It refers to the section itself, see :ref:`my-reference-label`.

.. __: https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#ref-role

**Referencing other documents:** (see `:doc:`__)

.. code-block:: rst

    See also :doc:`/contributing` or :doc:`the news page </news>`

.. __: https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#cross-referencing-documents

**Code blocks:**

Use ``.. code-block:: <language>`` and indent the code by one level:

.. code-block:: rst

   .. code-block:: bash

        sudo apt install python3 python3-pip python3-virtualenv
        virtualenv .venv
        source .venv/bin/activate
        (.venv) $ python [cmd]

Syntax standards
----------------

- Use at most three levels of headlines:
  ``===`` for page title, ``---`` for section headings (h3), ``^^^`` for
  sub-headings (h4).
- Use ``$ /usr/bin/command`` to refer to shell commands and use
  ``code-block:: bash`` over ``sh``
- Use ``(.venv) $ python [cmd]`` for things that need to be run inside a
  virtual environment and be consistent
  (see `Sphinx: Narrative Documentation`__)
- Use ``/path/to/isso/<thing>`` to refer to items inside Isso's main directory
  and use ``comments.db`` as the name for the database
- Admonitions should only be: ``note``, ``tip``, ``warning``, ``attention``,
  (maybe also ``error``?). See `docutils: Admonitions`__.
- Try to keep line length under 80 characters, but don't worry when going over
  that limit when using links or code blocks

.. __: https://www.sphinx-doc.org/en/master/tutorial/narrative-documentation.html
.. __: https://docutils.sourceforge.io/docs/ref/rst/directives.html#admonitions

Inspiration
-----------

The following documentation pages should serve as good examples. They are from
related projects that also offer commenting functionality.

- `Commento Documentation <https://docs.commento.io/>`_
- `Remark42 Documentation <https://remark42.com/docs/getting-started/installation/>`_
- `Schnack Documentation <https://schnack.cool/>`_

Help
----

Helpful links:

- `Cross-referencing with Sphinx <https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html>`_

Debugging cross-references:

.. code-block:: sh

    python -m sphinx.ext.intersphinx docs/_build/html/objects.inv

Also make sure you have used ``:ref:`` or ``:doc``
correctly and not confused the two.
