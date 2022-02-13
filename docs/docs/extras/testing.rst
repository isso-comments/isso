Testing
-------

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
