Server API
==========

.. note:: View the `Current API documentation`_ for **Isso 0.12.6** here, which
   is automatically generated. You can select previous versions from a dropdown
   on the upper right of the page.

    Using the API, you can:

   - Fetch comment threads
   - Post, edit and delete comments
   - Get information about the server
   - Like and dislike comments
   - **...and much more!**

The Isso API uses ``HTTP`` and ``JSON`` as primary communication protocol. The
API is extensively documented using an `apiDoc`_-compatible syntax in
`isso/views/comments.py`_.

.. _Current API documentation: /docs/api/
.. _apiDoc: https://apidocjs.com/
.. _isso/views/comments.py: https://github.com/posativ/isso/blob/master/isso/views/comments.py

Sections covered in this document:

.. contents::
    :local:

Generating API documentation
----------------------------

Install ``Node.js`` and ``npm``.

Run ``make apidoc-init apidoc`` and view the generated API documentation at
``apidoc/_output/`` (it produces a regular HTML file).

Live API testing
----------------

To test out calls to the API right from the browser, without having to
copy-&-paste ``curl`` commands, you can use ``apiDoc``'s live preview
functionality.

Set ``sampleUrl`` to e.g. ``localhost:8080`` in ``apidoc.json``:

.. code-block:: json
   :caption: apidoc.json

    {
      "name": "Isso API",
      "version": "0.13.0",
      "sampleUrl": "http://localhost:8080",
      "private": "true"
    }

Run ``make apidoc`` again and start your local
:ref:`test server <development-server>`

Go to ``apidoc/output`` and serve the generated API docs via
``python -m http.server`` [#f1]_, open ``http://localhost:8000`` in your browser
and use the "Send a sample request"

.. image:: /images/apidoc-sample-latest.png
   :scale: 75 %

.. [#f1] You must use a webserver to view the docs. Opening the local file
   straight from the browser will not work; the browser will refuse to execute
   any ``GET``/``POST`` calls because of security issues with local files.

Writing API documentation
-------------------------

Isso's API documentation is built using the `apiDoc`_ Javascript tool.

Inside `isso/views/comments.py`_, the view functions that are public endpoints
are annotated using ``@api`` syntax in code comments.

.. note:: The `apiDoc`_ "Getting started" guide should also help you get up to
   speed in making the API documentation of Isso even better!

A few points to consider:

- Use ``@apiVersion`` to annotate when an endpoint was first introduced or
  changed. This information will help to automatically create a viewable diff
  between Isso API versions.
- The current documentation for all endpoints should be good enough to
  copy-paste for your new or changed endpoint.
- Admin functionality is marked ``@apiPrivate``. To generate docs for private
  endpoints, set ``--private`` on the ``apidoc`` command line.
- Use ``@apiQuery`` for GET query URL-encoded parameters, ``@apiBody`` for POST
  data.
