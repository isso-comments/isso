Troubleshooting
===============

For uberspace users
-------------------
Some uberspace users experienced problems with isso and they solved their
issue by adding `DirectoryIndex disabled` as the first line in the `.htaccess`
file for the domain the isso server is running on.

pkg_ressources.DistributionNotFound
-----------------------------------

This is usually caused by messing up the system's Python with newer packages
from PyPi (e.g. by executing `easy_install --upgrade pip` as root) and is not
related to Isso at all.

Install Isso in a virtual environment as described in
:ref:`install-interludium`. Alternatively, you can use `pip install --user`
to install Isso into the user's home.

UnicodeDecodeError: 'ascii' codec can't decode byte 0xff
--------------------------------------------------------

Likely an issue with your environment, check you set your preferred file
encoding either in :envvar:`LANG`, :envvar:`LANGUAGE`, :envvar:`LC_ALL` or
:envvar:`LC_CTYPE`:

.. code-block:: text

    $ env LANG=C.UTF-8 isso [-h] [--version] ...

If none of the mentioned variables is set, the interaction with Isso will
likely fail (unable to print non-ascii characters to stdout/err, unable to
parse configuration file with non-ascii characters and to forth).

The web console shows 404 Not Found responses
---------------------------------------------

That's fine. Isso returns "404 Not Found" to indicate "No comments".
