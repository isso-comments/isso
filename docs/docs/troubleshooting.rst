Troubleshooting
===============

For uberspace users
-------------------
Some uberspace users experienced problems with isso and they solved their
issues by adding `DirectoryIndex disabled` as the first line in the `.htaccess`
file for the domain the isso server is running on.

pkg_ressources.DistributionNotFound
-----------------------------------

This is usually caused by messing up the system's Python with newer packages
from PyPi (e.g. by executing `easy_install --upgrade pip` as root) and is not
related to Isso at all.

Install Isso in a virtual environment as described in
:ref:`install-interludium`. Alternatively, you can use `pip install --user`
to install Isso into the user's home.

Why isn't markdown in my comments rendering as I expect?
--------------------------------------------------------

Please configure Isso's markup parser to your requirements as described in
:ref:`configure-markup`. As of version 0.12.2, Isso uses misaka 2.0 to render
markdown. Misaka 2.0 uses ``dashed-case`` instead of ``snake_case`` for
options, you might have to update your config.

UnicodeDecodeError: 'ascii' codec can't decode byte 0xff
--------------------------------------------------------

Likely an issue with your environment, check you set your preferred file
encoding either in :envvar:`LANG`, :envvar:`LANGUAGE`, :envvar:`LC_ALL` or
:envvar:`LC_CTYPE`:

.. code-block:: text

    $ env LANG=C.UTF-8 isso [-h] [--version] ...

If none of the mentioned variables are set, the interaction with Isso will
likely fail (unable to print non-ascii characters to stdout/err, unable to
parse configuration file with non-ascii characters and so forth).

The web console shows 404 Not Found responses
---------------------------------------------

Isso returned "404 Not Found" to indicate "No comments" in versions prior to
0.12.3. This behaviour was changed in
`a pull request <https://github.com/posativ/isso/pull/565>`_ to return a code
of "200" with an empty array.
