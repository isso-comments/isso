Writing Documentation
=====================

- Sphinx
- How to write good docs

Help
----

Helpful links:

- `Cross-referencing with Sphinx <https://docs.readthedocs.io/en/stable/guides/cross-referencing-with-sphinx.html>`_

Debugging cross-references:

.. code-block:: sh

    python -m sphinx.ext.intersphinx docs/_build/html/objects.inv

Also make sure you have used ``:ref:`` or ``:doc``
correctly and not confused the two.
