Development & Testing
=====================

Before submitting a change, you need to verify that it does not inadvertently
break any existing functionality in Isso.

A test suite for the **Python server** part ensures that the most basic things
are not broken, but it can only catch as many errors as it is configured to be
aware of (this is called "test coverage"). For more information, see
:doc:`testing-server`.

The **Javascript client** code is covered by both unit tests and end-to-end
integration tests. The test coverage is very small at the moment - see
`this GitHub issue <https://github.com/posativ/isso/issues/754>`_.
For detailed instructions about running client tests, see
:doc:`testing-client`.

.. note::
   Improvements to Isso's test coverage and/or different testing strategies are
   always welcome! Please see the :doc:`/docs/contributing/index` page for
   further information.


Sections covered in this document:

.. contents::
    :local:


Development server
------------------

After you've set up Isso according to :ref:`install-from-source`, you will have
a development server available at ``localhost:8080``.

.. code-block:: bash

   $ virtualenv .venv
   $ source .venv/bin/activate
   (.venv) $ isso -c share/isso-dev.cfg run

From there, the page ``localhost:8080/demo`` will be available, from where you
can try out the embedded Isso widget yourself. For convenience, the development
version of the bundled client code is used (``embed.dev.js`` with source map).

This enables easier debugging - e.g. Firefox shows a ``webpack`` entry in the
"Debugger" tab and shows the actual line of source code in any console traces.

Using docker
------------

Testing via `docker <https://en.wikipedia.org/wiki/Docker_(software)>`_ is not
a requirement, but can make a few tests faster to set up, makes automation
easier and ensures a consistent testing environment across developer machines.

Isso ships with several ``Dockerfiles`` - the ones under the
`docker/ folder <https://github.com/posativ/isso/tree/master/docker>`_ are for
creating a container that can run the unit and integration tests.

Build images
^^^^^^^^^^^^

First, ensure all images are built:

.. code-block:: console

    # Prepare testbed image
    $ docker build -f docker/Dockerfile-js-testbed -t isso-js-testbed .

This will take some time as headless chromium needs to be downloaded, once
(~400Mb), as well as necessary libraries installed. Will be cached on subsequent
runs.

.. code-block:: console

    # Create production image
    $ docker build -f Dockerfile -t isso .

Start server
^^^^^^^^^^^^

Start up server part via ``docker compose``:

.. code-block:: bash

    $ docker compose up -d

Now you should have the Isso server part available at ``localhost:8080``.

Running tests
^^^^^^^^^^^^^

Run **unit tests:**

.. code-block:: bash
    :emphasize-lines: 4

    $ docker run \
        --mount type=bind,source=${PWD}/package.json,target=/src/package.json,readonly \
        --mount type=bind,source=${PWD}/isso/js/,target=/src/isso/js/,readonly \
        isso-js-testbed npm run test-unit

Run **integration tests:**

.. code-block:: bash
    :emphasize-lines: 4-6

    $ docker run \
        --mount type=bind,source=${PWD}/package.json,target=/src/package.json,readonly \
        --mount type=bind,source=${PWD}/isso/js/,target=/src/isso/js/,readonly \
        --env ISSO_ENDPOINT='http://isso-dev.local:8080' \
        --network container:isso-server \
        isso-js-testbed npm run test-integration

(The ``--network`` part ensures that the client container can see the server
part. This is *not* set automatically by docker since this container is
considered a transient one)

Finally, bring down the containers again

.. code-block:: bash

    $ docker compose down -v

(The ``-v`` flag removes the transient volumes again, ensuring each test run
can start afresh).

Testing strategies
------------------

Manual testing
^^^^^^^^^^^^^^

Here are a few ideas of how to manually test the client to reveal potentially
uncovered scenarios:

- Post a comment
- Post an answer to a comment
- Edit your comment
- Test the admin interface
- Delete a comment from admin, then try to delete from frontend
- Reply to a comment that you have deleted from the admin/as another user
- Use ``curl`` commands
- Clear your cookies
- Restore certain cookies
- Embed into a single-page application (SPA)
- Zoom inside your browser
- Play with the embed parameters (``data-isso-*``)
- Play with the server config
- Test whether the docker container still works

Performance testing
^^^^^^^^^^^^^^^^^^^

Find a way to have 100, 1,000, 10,000, 100k commments at once.

Then, test responsiveness, speed of insertion, the updating of all timestamps
every minute, and whatever else might be performance-related.

Here is an example to insert into the database (might be better optimized):

.. code-block:: bash

    for i in {1..1000}; do
      sqlite3 comments.db "INSERT INTO comments (tid, created, remote_addr, text, mode, voters) VALUES (1, 100, '127.0.0.1', 'hello', 1, 0);";
    done

Also set the comments to be loaded at once to ``infinity``:

.. code-block:: html

    <script data-isso-max-comments-top="inf" src="../js/embed.dev.js"></script>

Unconventional testing
^^^^^^^^^^^^^^^^^^^^^^

Be a chaos monkey! Think of unconventional ways of breaking Isso.


.. epigraph::

   A QA engineer walks into a bar. Orders a beer. Orders 0 beers. Orders
   99999999999 beers. Orders a lizard. Orders -1 beers. Orders a ueicbksjdhd.

   First real customer walks in and asks where the bathroom is. The bar bursts
   into flames, killing everyone.

   -- `brenankeller <https://twitter.com/brenankeller/status/1068615953989087232>`_

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - Explain the difference between unit and integration tests, maybe using cool
     analogies
   - Collect a few guides about testing philosophies and strategies

   ... and other things about testing in general that should be documented.
