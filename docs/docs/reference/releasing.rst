Releasing a new version
=======================

These instructions should mainly be useful to the maintainers, but you might
also be interested in case you'd like to create a fork or test out a new
pre-release.

Relevant files:

- ``MANIFEST.in``
- ``LICENSE``
- ``setup.py``
- ``setup.cfg``
- ``releaser.conf`` (for jelmer's ``releaser`` tool)

.. code-block:: dosini
   :caption: ``~/.pypirc``

   [pypi]
     username = __token__
     password = pypi-XXXXX

Creating wheels: `Wheels User Guide`_

Packaging: `packaging.python.org`_

.. _Wheels User Guide: https://wheel.readthedocs.io/en/stable/user_guide.html
.. _packaging.python.org: https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/

https://packaging.python.org/en/latest/tutorials/packaging-projects/

https://stackoverflow.com/questions/43377675/build-a-universal-wheel-from-setup-py
https://pythonwheels.com/

For wheels: ``pip install wheel`` or ``apt install python3-wheel``

* Run ``make test``
* Update version number in ``setup.py``, ``apidoc.json`` and ``CHANGES.rst``
* ``git commit -m "Preparing ${VERSION}" setup.py CHANGES.rst``
* ``git tag -as ${VERSION}``
* ``make init all``
* ``python3 setup.py sdist`` (Source distribution)
* ``twine upload --sign dist/isso-${VERSION}.tar.gz``
* ``python3 setup.py bdist_wheel`` (Wheel)
* ``twine upload --sign dist/isso-${VERSION}-py3-none-any.whl``
