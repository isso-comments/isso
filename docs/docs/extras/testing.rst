Testing
-------

Isso is tested by the `nose`_ tool. You should also install the `coverage`_
module to receive code coverage statistics.

.. code-block:: sh

    $ pip install nose coverage

Nose needs your Isso package to be installed as a site package to work, else it
will complain with:

.. code-block:: sh

    pkg_resources.DistributionNotFound: The 'isso' distribution was not found and is required by the application

When running Isso via ``nosetests``, you need to be aware that it will use the
packaged version of Isso in your ``site-packages``, not the one you have in
your current working directory.

Use ``pip install -e .`` to install Isso as an "editable" package (the package
in ``site-packages`` will be a symlink to your current development directory).

You can run tests independently via ``nosetests [options] isso/`` or use Isso's
standard test suite via ``make tests coverage``.

.. _nose: https://nose.readthedocs.io/en/latest/
.. _coverage: https://coverage.readthedocs.io/en/latest/
