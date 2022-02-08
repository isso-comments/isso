Releasing steps
===============

* Run ``python3 setup.py nosetests``
* Update version number in ``setup.py`` and ``CHANGES.rst``
* ``git commit -m "Preparing ${VERSION}" setup.py CHANGES.rst``
* ``git tag -as ${VERSION}``
* ``make init all``
* ``python3 setup.py sdist``
* ``twine upload --sign dist/isso-${VERSION}.tar.gz``
