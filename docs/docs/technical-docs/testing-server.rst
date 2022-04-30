##################
Testing the Server
##################

Isso is tested by the `pytest`_ tool. You should also install the `coverage`_
module with the `pytest-cov`_ plugin to receive code coverage statistics.

.. code-block:: sh

    $ pip install pytest pytest-cov coverage

Pytest needs your Isso package to be installed as a site package to work, else it
will complain with:

.. code-block:: sh

    pkg_resources.DistributionNotFound: The 'isso' distribution was not found and is required by the application

When running Isso via ``pytest``, you need to be aware that it will use the
packaged version of Isso in your ``site-packages``, not the one you have in
your current working directory.

Use ``pip install -e .`` to install Isso as an "editable" package (the package
in ``site-packages`` will be a symlink to your current development directory).

You can run tests independently via ``pytest [options] isso/`` or use Isso's
standard test suite via ``make tests coverage``.

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

   - Unit tests: unittest, pytest, coverage
   - Maybe some links to "how to write good python tests"

   ... and other things about server testing that should be documented.
