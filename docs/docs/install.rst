Installation
============

Isso is a web application written in Python. If pip and virtualenv mean anything
to you, continue with :ref:`install-from-pypi`. If you are running
Debian/Ubuntu, Gentoo, Archlinux or Fedora, you can use
:ref:`prebuilt-package`. If not, read the next section carefully.

.. contents::
    :local:
    :depth: 1

.. _install-interludium:

Interludium: Python is not PHP
------------------------------

If you think hosting a web application written in Python is as easy as one
written in PHP, you are wrong. Unlike for PHP, many Linux distribution use
Python for internal tools. Your package manager already ships several python
libraries, but most likely not all required by Isso (or in an up-to-date
version – looking at you, Debian!).

That's why most Python developers use the `Python Package Index`_ to get their
dependencies. The most important rule to follow is to never install *anything* from PyPi
as root. Not because of malicious software, but because you *will* break your
system.
``easy_install`` is one tool to mess up your system. Another package manager is
``pip``. If you ever searched for an issue with Python/pip and Stackoverflow is
suggesting you ``easy_install pip`` or ``pip install --upgrade pip`` (as root
of course!), you are doing it wrong. `Why you should not use Python's
easy_install carelessly on Debian`_ is worth the read.

Fortunately, Python has a way to install packages (both as root and as user)
without interfering with your globally installed packages: `virtualenv`. Use
this *always* if you are installing software unavailable in your favourite
package manager.

.. code-block:: sh

    # for Debian/Ubuntu
    ~> sudo apt-get install python-setuptools python-virtualenv python-dev

    # Fedora/Red Hat
    ~> sudo yum install python-setuptools python-virtualenv python-devel

The next steps should be done as regular user, not as root (although possible
but not recommended):

.. code-block:: sh

    ~> virtualenv /opt/isso
    ~> source /opt/isso/bin/activate

After calling `source`, you can now install packages from PyPi locally into this
virtual environment. If you don't like Isso anymore, you just `rm -rf` the
folder. Inside this virtual environment, you may also execute the example
commands from above to upgrade your Python Package Manager (although it barely
makes sense), it is completely independent from your global system.

To use Isso installed in a virtual environment outside of the virtual
environment, you just need to add */opt/isso/bin* to your :envvar:`PATH` or
execute */opt/isso/bin/isso* directly. It will launch Isso from within the
virtual environment.

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

- Python 2.7 or 3.4+ (+ devel headers)
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

    ~> ln -s /opt/isso/bin/isso /usr/local/bin/isso

Upgrade
^^^^^^^

To upgrade Isso, activate your virtual environment again, and run

.. code-block:: sh

    ~> source /opt/isso/bin/activate  # optional
    ~> pip install --upgrade isso

.. _prebuilt-package:

Prebuilt Packages
-----------------

* Debian (since Buster): https://packages.debian.org/search?keywords=isso

* Gentoo: http://eroen.eu/cgit/cgit.cgi/eroen-overlay/tree/www-apps/isso?h=isso
  – not yet available in Portage, but you can use the ebuild to build Isso.

* Arch Linux: https://aur.archlinux.org/packages/isso/
  – install with `yaourt isso`.

* Fedora: https://copr.fedoraproject.org/coprs/jujens/isso/ — copr
  repository. Built from Pypi, includes a systemctl unit script.

Build a Docker image
--------------------

You can get a Docker image by running ``docker build . -t
isso``. Assuming you have your configuration in ``/opt/isso``, you can
use the following command to spawn the Docker container:

.. code-block:: sh

    ~> docker run -d --rm --name isso -p 127.0.0.1:8080:8080 -v /opt/isso:/config -v /opt/isso:/db isso

Then, you can use a reverse proxy to expose port 8080.

Install from Source
-------------------

If you want to hack on Isso or track down issues, there's an alternate
way to set up Isso. It requires a lot more dependencies and effort:

- Python 3.5+ (+ devel headers)
- Virtualenv
- SQLite 3.3.8 or later
- a working C compiler
- Node.js, `NPM <https://npmjs.org/>`__ and `Bower <http://bower.io/>`__ - *for frontend*
- `sassc <https://github.com/sass/sassc>`_ for compiling
  `.scss <https://sass-lang.com/>`_ - *for docs*

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

Integration without optimization:

.. code-block:: html

    <script src="/js/config.js"></script>
    <script data-main="/js/embed" src="/js/components/requirejs/require.js"></script>

Optimization - generate ``embed.(min|dev).js``:

.. code-block:: sh

    ~> make js

Generate docs:

.. code-block:: sh

    ~> make site

.. _init-scripts:

Init scripts
------------

Init scripts to run Isso as a service (check your distribution's documentation
for your init-system; e.g. Debian uses SysVinit, Fedora uses systemd) if you
don't use FastCGi or uWSGI:

-  systemd (Isso + Gunicorn): https://salsa.debian.org/jelmer/isso/-/blob/master/debian/isso.service
-  SysVinit (Isso + Gunicorn): https://salsa.debian.org/jelmer/isso/-/blob/master/debian/isso.init
-  OpenBSD: https://gist.github.com/noqqe/7397719
-  FreeBSD: https://gist.github.com/ckoepp/52f6f0262de04cee1b88ef4a441e276d
-  Supervisor: https://github.com/posativ/isso/issues/47

If you're writing your own init script, you can utilize ``start-stop-daemon``
to run Isso in the background (Isso runs in the foreground usually). Below you
will find a very basic SysVinit script which you can use for inspiration:

.. code-block:: sh

    #!/bin/sh
    ### BEGIN INIT INFO
    # Provides:          isso
    # Required-Start:    $local_fs $network
    # Default-Start:     2 3 4 5
    # Default-Stop:      0 1 6
    # Description:       lightweight Disqus alternative
    ### END INIT INFO

    EXEC=/opt/isso/bin/isso
    EXEC_OPTS="-c /etc/isso.cfg run"

    RUNAS=isso
    PIDFILE=/var/run/isso.pid

    start() {
      echo 'Starting service…' >&2
      start-stop-daemon --start --user "$RUNAS" --background --make-pidfile --pidfile $PIDFILE \
                        --exec $EXEC -- $EXEC_OPTS
    }

    stop() {
      echo 'Stopping service…' >&2
      start-stop-daemon --stop --user "$RUNAS" --pidfile $PIDFILE --exec $EXEC
    }

    case "$1" in
      start)
        start
        ;;
      stop)
        stop
        ;;
      restart)
        stop
        start
        ;;
      *)
        echo "Usage: $0 {start|stop|restart}"
    esac
