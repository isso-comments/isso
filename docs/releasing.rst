Releasing steps
===============

* Run ``python3 setup.py nosetests``, ``python2 setup.py nosetests``
* Update version number in ``setup.py`` and ``CHANGES.rst``
* ``git commit -m "Preparing ${VERSION}"``
* ``git tag -as ${VERSION}``
* ``make init all``
* ``./setup.py sdist``
* ``twine upload dist/isso-${VERSION}.tar.gz``
