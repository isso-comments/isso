Installation
------------

Requirements:

-  Python 2.6, 2.7 or 3.3 (+ devel headers)
-  a working C compiler

Install Isso with `pip <http://www.pip-installer.org/en/latest/>`_:

.. code-block:: sh

    ~> pip install isso

`Dont't have pip <https://twitter.com/gardaud/status/357638468572151808>`_?

.. code-block:: sh

    ~> easy_install isso  # cross your fingers

Init scripts to run Isso as a service (check your distribution's documentation
for your init-system; e.g. Debian uses SysVinit, Fedora uses SystemD):

-  SystemD: https://github.com/jgraichen/debian-isso/blob/master/debian/isso.service
-  SysVinit: https://github.com/jgraichen/debian-isso/blob/master/debian/isso.init
-  OpenBSD: https://gist.github.com/noqqe/7397719
-  Supervisor: https://github.com/posativ/isso/issues/47
