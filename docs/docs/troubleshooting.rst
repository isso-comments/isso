Troubleshooting
===============

pkg_ressources.DistributionNotFound
-----------------------------------

This is usually caused by messing up the system's Python with newer packages
from PyPi (e.g. by executing `easy_install --upgrade pip` as root) and is not
related to Isso at all.

Install Isso in a virtual environment as described in
:ref:`install-interludium`. Alternatively, you can use `pip install --user`
to install Isso into the user's home.

The web console shows 404 Not Found responses
---------------------------------------------

That's fine. Isso returns "404 Not Found" to indicate "No comments".
