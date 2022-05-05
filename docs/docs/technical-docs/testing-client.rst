##################
Testing the Client
##################

The Javascript client part of Isso is tested by the
`Jest testing framework <https://jestjs.io/>`_.

.. note::
   Improvements to Isso's test coverage and/or different testing strategies are
   always welcome! Please see the :doc:`/docs/contributing/index` page for
   further information.

Sections covered in this document:

.. contents::
    :local:

Unit tests
----------

The unit tests that cover the frontend client ensure that the individual
components are working fine in isolation.

Install the needed ``Jest``-related packages
(listed as ``optionalDependencies`` in ``package.json``):

.. code-block:: bash

   $ npm install

Then run the unit tests:

.. code-block:: bash

   $ npm run tests-unit

You should receive output that looks similar to the following:

.. code-block:: bash

   > test-unit
   > jest --config isso/js/jest-unit.config.js isso/js/tests/unit/

   PASS  isso/js/tests/unit/isso.test.js
   PASS  isso/js/tests/unit/config.test.js
   PASS  isso/js/tests/unit/utils.test.js

   Test Suites: 3 passed, 3 total
   Tests:       3 passed, 3 total
   Snapshots:   1 passed, 1 total
   Time:        0.907 s, estimated 1 s
   Ran all test suites matching /isso\/js\/tests\/unit\//i.

If you receive an error saying ``1 snapshot failed`` see
:ref:`Updating snapshots <updating-snapshots>`


End-to-End Integration tests
----------------------------

For the end-to-end integration tests, the Python server part needs to be up and
running - this part of the test suite pretends to be a real user sitting in
front of a keyboard.

The tests are run using the `puppeteer`__ browser automation tool. It runs a
real Chromium browser in the background and can be instrumented to allow
simulation of user interaction.

.. __: https://puppeteer.github.io/puppeteer/

First, ensure all the client files are built and that the server part is ready
to be run. Refer to :ref:`install-from-source` for details. Here's the
important part:

.. code-block:: bash

   $ make init
   $ make js

Start the server:

.. code-block:: bash

   $ virtualenv .venv
   $ source .venv/bin/activate
   (.venv) $ isso -c share/isso-dev.cfg run

Install the necessary ``puppeteer``-related Javascript packages:

.. code-block:: bash

   $ npm install --no-save jest jest-puppeteer puppeteer

.. note::
   This will take some time as a headless ``chromium`` browser needs to be
   downloaded, which requires about 400Mb of space.

Then run the integration tests:

.. code-block:: bash

   $ npm run tests-integration

You should receive output that looks similar to the following:

.. code-block:: bash

    > test-integration
    > jest --config isso/js/jest-integration.config.js isso/js/tests/integration/

    PASS  isso/js/tests/integration/puppet.test.js
     ✓ window.Isso functions should be idempotent (87 ms)
     ✓ should have correct ISSO_ENDPOINT on page (26 ms)
     ✓ should display "Isso Demo" text on page (34 ms)
     ✓ should fill Postbox with valid data and receive 201 reply (319 ms)

    Test Suites: 1 passed, 1 total
    Tests:       4 passed, 4 total
    Snapshots:   0 total
    Time:        0.752 s, estimated 21 s
    Ran all test suites matching /isso\/js\/tests\/integration\//i.


Skip downloading Chromium
^^^^^^^^^^^^^^^^^^^^^^^^^

The downloaded browser will be saved to ``node_modules/puppeteer/.local-chromium/``.
You can set ``PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true`` in your environment to
skip downloading the bundled browser and instead use the locally installed
version of Chrome/Chromium via e.g. ``PUPPETEER_EXECUTABLE_PATH=$(which chromium)``.

For further information, see `puppeteer docs: Environment variables`__.

.. __: https://github.com/puppeteer/puppeteer/blob/main/docs/api.md#environment-variables

Testing standards
-----------------

A good starting point are the `MailChimp standards`__

You may use ``ES6`` syntax in tests (the restriction for ``ES5`` syntax is only
for the production client code which needs to run on as many browsers as
possible).

Try not to introduce any race conditions - especially the asynchronous code is
very tricky to get right.

The current test suite was written largely by one of the main project leads,
who happens to know very little about testing (or even Javascript in general).
Feel free to suggest improvements and change this!

.. __: https://mailchimp.com/developer/open-commerce/docs/testing-requirements/>

.. _updating-snapshots:

Updating snapshots
^^^^^^^^^^^^^^^^^^

The ``Jest`` tests make use of `snapshots <https://jestjs.io/docs/snapshot-testing>`_. Say you want to ensure that the Postbox ``<textarea>`` always looks like this:

.. code-block:: html

   <div class="isso-textarea-wrapper">
     <div class="isso-textarea isso-placeholder">
         Type Comment Here (at least 3 chars)</div>
     <div class="isso-preview">[...]</div>
   </div>

You *could* write this as:

.. code-block:: javascript

   let expected_html = '<div class="isso-textarea-wrapper> [...]';
   expect($(".isso-textarea-wrapper").innerHTML.toBe(expected_html);

But then your resulting test files would quickly grow quite messy, especially
for large components where the ``expected_html`` block would span whole pages.
That is why ``Jest`` offers to check in those expected blocks as ``snapshots``,
which will saved into e.g. ``isso/js/tests/unit/__snapshots__/*.snap``

.. code-block:: javascript

   expect($(".isso-textarea-wrapper").innerHTML).toMatchSnapshot();

If you have created a commit which changes the HTML that is generated on the
client side (and you're sure it is correct) or written a new test case that
uses snapshots, check in or update the snapshot file by running
``npm run test-unit -- -u``. You should see something like the following:

.. code-block:: text

   npx jest --config isso/js/jest-unit.config.js isso/js/tests/unit/ -u
   PASS  isso/js/tests/unit/isso.test.js
   › 1 snapshot updated.

Make a new commit for the changes to the snapshot - here's an example:

.. code-block:: text

   isso: tests/unit: Update isso.js snapshot

   Prepending `isso-` to the element classes causes a change in
   the generated HTML and necessitates an update of the
   snapshot.

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   Unit tests:

   - Jest, how to write good tests (link to
     `MailChimp standards <https://mailchimp.com/developer/open-commerce/docs/testing-requirements/>`_)
   - How to update and check in snapshots

   Integration tests:

   - How Puppeteer works
   - How to take advantage of ``jest-puppeteer`` special ``expect`` functions

   Running client tests in general:

   - Ways of running tests inside and outside of docker containers
   - Link to the GitHub actions that run on every Pull Request

   ... and other things about client testing that should be documented.
