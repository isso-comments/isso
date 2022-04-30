Writing Documentation
=====================

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - How to run Sphinx
   - How Sphinx works, what its philosphy is
   - Small reST intro, also link to the
     `reStructuredText Primer <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html>`_
   - How to write good documentation, maybe link to a few guides and example sites

   ... and other things about documentation that should be documented.

Help
----

Helpful links:

- `Cross-referencing with Sphinx <https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html>`_

Debugging cross-references:

.. code-block:: sh

    python -m sphinx.ext.intersphinx docs/_build/html/objects.inv

Also make sure you have used ``:ref:`` or ``:doc``
correctly and not confused the two.
