##################
Testing the Server
##################

The server part of Isso is tested by the `pytest`_ tool. You should also
install the `coverage`_ module with the `pytest-cov`_ plugin to receive code
coverage statistics.

.. code-block:: bash

    $ pip install pytest pytest-cov coverage

Run Isso's standard server **test suite**:

.. code-block:: bash

    make tests

You can also run tests independently via ``pytest [options] isso/``.

.. note::
   Improvements to Isso's test coverage and/or different testing strategies are
   always welcome! Please see the :doc:`/docs/contributing/index` page for
   further information.

Generate and view server **test coverage**:

.. code-block:: bash

    make coverage

.. note::
   The Continuous Integration suite running via
   `GitHub Actions <https://github.com/posativ/isso/blob/master/.github/workflows/python-tests.yml>`_
   will throw an **error** if the code coverage falls **below 70%**.


DistributionNotFound error
--------------------------

Pytest needs your Isso package to be installed as a site package to work, else it
will complain with:

.. code-block:: sh

    pkg_resources.DistributionNotFound: The 'isso' distribution was not found and is required by the application

When running Isso via ``pytest``, you need to be aware that it will use the
packaged version of Isso in your ``site-packages``, not the one you have in
your current working directory.

Use ``pip install -e .`` to install Isso as an "editable" package (the package
in ``site-packages`` will be a symlink to your current development directory).

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
