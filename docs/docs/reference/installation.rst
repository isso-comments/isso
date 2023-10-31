Installation
============

Isso is a web application written in Python. If pip and virtualenv mean anything
to you, continue with :ref:`install-from-pypi`. If you are running
Debian/Ubuntu or Arch Linux, you can use :ref:`prebuilt-package`. If not, read
the next section carefully.

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
system. ``pip`` is one tool to mess up your system.
If you ever searched for an issue with Python/pip and Stackoverflow is
suggesting you ``pip install --upgrade pip`` (as root
of course!), you are doing it wrong. `Why you should not use Python's
easy_install carelessly on Debian`_ is worth the read.

Fortunately, Python has a way to install packages (both as root and as user)
without interfering with your globally installed packages: ``virtualenv``. Use
this *always* if you are installing software unavailable in your favourite
package manager.

.. code-block:: console

    # for Debian/Ubuntu
    $ sudo apt-get install python3-setuptools python3-virtualenv python3-dev

    # Fedora/Red Hat
    $ sudo yum install python3-setuptools python3-virtualenv python3-devel

The next steps should be done as regular user, not as root (although possible
but not recommended):

.. code-block:: console

    $ virtualenv /opt/isso
    $ source /opt/isso/bin/activate

.. note::
   This guide will refer to commands that need to run inside an activated
   ``virtualenv`` with the ``(.venv) $`` prefix.

After calling ``source``, you can now install packages from PyPi locally into this
virtual environment. If you don't like Isso anymore, you just ``rm -rf`` the
folder. Inside this virtual environment, you may also execute the example
commands from above to upgrade your Python Package Manager (although it barely
makes sense), it is completely independent from your global system.

To use Isso installed in a virtual environment outside of the virtual
environment, you just need to add ``/opt/isso/bin`` to your :envvar:`PATH` or
execute ``/opt/isso/bin/isso`` directly. It will launch Isso from within the
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

- Python 3.8+ (+ devel headers)
- SQLite 3.3.8 or later
- a working C compiler

For Debian/Ubuntu just `copy and paste
<http://thejh.net/misc/website-terminal-copy-paste>`_ to your terminal:

.. code-block:: console

    $ sudo apt-get install python3-dev sqlite3 build-essential

Similar for Fedora (and derivates):

.. code-block:: console

    $ sudo yum install python3-devel sqlite
    $ sudo yum groupinstall “Development Tools”

Installation
^^^^^^^^^^^^

Install Isso with `pip <http://www.pip-installer.org/en/latest/>`_, using the
``virtualenv`` set up before:

.. code-block:: console

    $ source /opt/isso/bin/activate
    (.venv) $ pip install isso

For easier execution, you can symlink the executable to a location in your
:envvar:`PATH`.

.. code-block:: console

    $ ln -s /opt/isso/bin/isso /usr/local/bin/isso

Upgrade
^^^^^^^

To upgrade Isso, activate your virtual environment again, and run

.. code-block:: console

    $ source /opt/isso/bin/activate  # optional
    (.venv) $ pip install --upgrade isso

.. _prebuilt-package:

Prebuilt Packages
-----------------

* Debian (since Buster): https://packages.debian.org/search?keywords=isso

* Arch Linux: https://aur.archlinux.org/packages/isso/

.. _using-docker:

Using Docker
------------

Assuming you have your configuration in ``/var/lib/isso``, with
``dbpath=/db/comments.db`` and ``host`` set properly in ``isso.cfg``, you have
two options for running a Docker container:

a) Official Docker image
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    $ docker pull ghcr.io/isso-comments/isso:latest
    $ docker run -d --rm --name isso -p 127.0.0.1:8080:8080 \
        -v /var/lib/isso:/config -v /var/lib/isso:/db \
        ghcr.io/isso-comments/isso:latest

b) Build a Docker image yourself
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can build a Docker image by running ``make docker``, which will be tagged
as ``isso:latest``.

.. code-block:: console

    $ mkdir -p config/ db/
    $ cp contrib/isso.sample.cfg config/isso.cfg
    # Set 'dbpath' to '/db/comments.db' and adjust 'host'
    $ docker run -d --rm --name isso -p 127.0.0.1:8080:8080 \
        -v $PWD/config:/config -v $PWD/db:/db \
        isso:latest

Then, you can use a reverse proxy to expose port 8080.

.. _install-from-source:

Install from Source
-------------------

If you want to hack on Isso or track down issues, there's an alternate
way to set up Isso. It requires a lot more dependencies and effort:

- Python 3.8+ (+ devel headers)
- Virtualenv
- SQLite 3.3.8 or later
- a working C compiler (e.g. the ``gcc`` package)
- Node.js, `NPM <https://npmjs.org/>`__ - *required for frontend*

Get a fresh copy of Isso:

.. code-block:: console

    $ git clone https://github.com/posativ/isso.git
    $ cd isso/

To create a virtual environment (recommended), run:

.. code-block:: console

    $ virtualenv .venv
    $ source .venv/bin/activate

Install JavaScript modules using ``npm``:

.. code-block:: console

    $ make init

Build JavaScript frontend code:

.. code-block:: console

    $ make js

Install Isso and its dependencies:

.. code-block:: console

    (.venv) $ python setup.py develop  # or `pip install -e .`
    (.venv) $ isso -c /path/to/isso.cfg run

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
