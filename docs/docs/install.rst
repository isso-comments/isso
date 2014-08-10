Installation
============

Isso is a web application written in Python. If pip and virtualenv mean
anything to you, continue with :ref:`install-from-pypi`. If you are running
Debian/Ubuntu or Gentoo, you can use :ref:`prebuilt-package`. If not, read the
next section carefully.

.. contents::
    :local:
    :depth: 1

Interludium: Python is not PHP
------------------------------

If you think hosting a web application written in Python is as easy as one
written in PHP, you are wrong. Unlike for PHP, many Linux distribution use
Python for internal tools. Your package manager already ships several python
libraries, but most likely not all required by Isso (or in an up-to-date
version – looking at you, Debian!).

That's why most Python developers use the `Python Package Index`_ to get their
dependencies. But the most important rule: never install *anything* from PyPi
as root. Not because of malicious software, but because you *will* break your
system.
``easy_install`` is one tool to mess up your system. Another package manager is
``pip``. If you ever searched for an issue with Python/pip and Stackoverflow is
suggesting your ``easy_install pip`` or ``pip install --upgrade pip`` (as root
of course!), you are doing it wrong. `Why you should not use Python's
easy_install carelessly on Debian`_ is worth the read.

Fortunately, Python has a way to install packages (both as root and as user)
without interfering with your globally installed packages: `virtualenv`. Use
this *always* if you are installing software unavailable in your favourite
package manager.

.. code-block:: sh

    # for Debian/Ubuntu
    ~> sudo apt-get install python-setuptools python-virtualenv

    # Fedora/Red Hat
    ~> sudo yum install python-setuptools python-virtualenv

The next steps should be done as regular user, not as root (although possible
but not recommended):

.. code-block:: sh

    ~> virtualenv /path/to/isso
    ~> source /path/to/isso/bin/activate

After calling `source`, you can now install packages from PyPi locally into this
virtual environment. If you don't like Isso anymore, you just `rm -rf` the
folder. Inside this virtual environment, you may also execute the example
commands from above to upgrade your Python Package Manager (although it barely
makes sense), it is completely independent from your global system.

With a virtualenv active, you may now continue to :ref:`install-from-pypi`!
Of course you may not need a virtualenv when you are running dedicated virtual
machines or a shared host (e.g. Uberspace.de).

.. _Python Package Index: https://pypi.python.org/pypi
.. _Why you should not use Python's easy_install carelessly on Debian:
   https://workaround.org/easy-install-debian

.. _install-from-pypi:

Install from PyPi
-----------------

Requirements
^^^^^^^^^^^^

- Python 2.6, 2.7 or 3.3+ (+ devel headers)
- SQLite 3.3.8 or later
- a working C compiler

For Debian/Ubuntu just `copy and paste
<http://thejh.net/misc/website-terminal-copy-paste>`_ to your terminal:

.. code-block:: sh

    ~> sudo apt-get install python-dev sqlite3 build-essential

Similar for Fedora (and derivates):

.. code-block:: sh

    ~> sudo yum install python-devel sqlite
    ~> sudo yum groupinstall “Development Tools”

Installation
^^^^^^^^^^^^

Install Isso with `pip <http://www.pip-installer.org/en/latest/>`_:

.. code-block:: sh

    ~> pip install isso

`Don't have pip? <https://twitter.com/gardaud/status/357638468572151808>`_

.. code-block:: sh

    ~> easy_install isso  # cross your fingers

For easier execution, you can symlink the executable to a location in your
:envvar:`PATH`.

.. code-block:: sh

    ~> ln -s /path/to/isso-venv/bin/isso /usr/local/bin/isso

Upgrade
^^^^^^^

To upgrade Isso, activate your virtual environment again, and run

.. code-block:: sh

    ~> source /path/to/isso/bin/activate  # optional
    ~> pip install --upgrade isso

.. _prebuilt-package:

Prebuilt Packages
-----------------

* Debian: https://packages.crapouillou.net/ – built from PyPi. Includes
  startup scripts and vhost configurations for Lighttpd, Apache and Nginx
  [`source <https://github.com/jgraichen/debian-isso>`__].
  `#729218 <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=729218>`_ is an
  ITP for Debian.

* Gentoo: http://eroen.eu/cgit/cgit.cgi/eroen-overlay/tree/www-apps/isso?h=isso
  – not yet available in Portage, but you can use the ebuild to build Isso.

* Arch Linux: https://aur.archlinux.org/packages/isso/
  – install with `yaourt isso`.

* Docker Image: https://registry.hub.docker.com/u/bl4n/isso/

Install from Source
-------------------

If you want to hack on Isso or track down issues, there's an alternate
way to set up Isso. It requires a lot more dependencies and effort:

- Python 2.6, 2.7 or 3.3+ (+ devel headers)
- Virtualenv
- SQLite 3.3.8 or later
- a working C compiler
- Node.js, `NPM <https://npmjs.org/>`__ and `Bower <http://bower.io/>`__

Get a fresh copy of Isso:

.. code-block:: sh

    ~> git clone https://github.com/posativ/isso.git
    ~> cd isso/

To create a virtual environment (recommended), run:

.. code-block:: sh

    ~> virtualenv .
    ~> source ./bin/activate

Install Isso and its dependencies:

.. code-block:: sh

    ~> python setup.py develop  # or `install`
    ~> isso run

Install JavaScript modules:

.. code-block:: sh

    ~> make init

Integration without previous optimization:

.. code-block:: html

    <script src="/js/config.js"></script>
    <script data-main="/js/embed" src="/js/components/requirejs/require.js"></script>

Optimization:

.. code-block:: sh

    ~> npm install -g requirejs uglifyjs jade
    ~> make js

.. _init-scripts:

Init scripts
------------

Init scripts to run Isso as a service (check your distribution's documentation
for your init-system; e.g. Debian uses SysVinit, Fedora uses SystemD) if you
don't use FastCGi or uWSGI:

-  SystemD: https://github.com/jgraichen/debian-isso/blob/master/debian/isso.service
-  SysVinit: https://github.com/jgraichen/debian-isso/blob/master/debian/isso.init
-  OpenBSD: https://gist.github.com/noqqe/7397719
-  Supervisor: https://github.com/posativ/isso/issues/47
