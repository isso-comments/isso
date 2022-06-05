Testing the Server
==================

The server part of Isso is tested by the `pytest`_ tool. You should also
install the `coverage`_ module with the `pytest-cov`_ plugin to receive code
coverage statistics.

.. code-block:: console

    (.venv) $ pip install pytest pytest-cov coverage

Run Isso's standard server **test suite**:

.. code-block:: console

    (.venv) make test

You can also run tests independently via ``pytest [options] isso/tests/``.

.. note::
   Improvements to Isso's test coverage and/or different testing strategies are
   always welcome! Please see the :doc:`/docs/contributing/index` page for
   further information.

**Check Python code style** using ``flake8``:

.. code-block:: console

    (.venv) $ pip install flake8
    (.venv) $ make flakes

Generate and view server **test coverage**:

.. code-block:: console

    (.venv) $ make coverage

.. note::
   The Continuous Integration suite running via
   `GitHub Actions <https://github.com/posativ/isso/blob/master/.github/workflows/python-tests.yml>`_
   will throw an **error** if either the unit tests, the integration tests or
   the ``flake8`` tests fail or the code coverage falls **below 70%**.


DistributionNotFound error
--------------------------

Pytest needs your Isso package to be visible in its ``PATH`` to work, else it
will complain with:

.. code-block:: console

    pkg_resources.DistributionNotFound: The 'isso' distribution was not found and is required by the application

When running ``pytest`` directly, you need to be aware that it will prioritize
the packaged version of Isso in your ``site-packages``, not the one you have in
your current working directory.

That is why you should uninstall the ``pip`` package of Isso and set
``PYTHONPATH=.`` before running tests. The project ``Makefile`` already does
the latter for you.

Alternatively, use ``pip install -e .`` to install Isso as an "editable"
package (the package in ``site-packages`` will be a symlink to your current
development directory).

.. _pytest: https://docs.pytest.org/
.. _pytest-cov: https://github.com/pytest-dev/pytest-cov
.. _coverage: https://coverage.readthedocs.io/en/latest/

.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - Maybe some links to "how to write good python tests"

   ... and other things about server testing that should be documented.
