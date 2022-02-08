Overview
========

Welcome to Isso's documentation. This documentation will help you get started
fast. If you run into any problems when using Isso, you can find the answer in
troubleshooting guide or you can ask me on IRC or GitHub.

Documentation overview:

.. toctree::
   :maxdepth: 1

   install
   quickstart
   troubleshooting

What's Isso?
------------

Isso is a lightweight commenting server similar to Disqus. It allows anonymous
comments, maintains identity and is simple to administrate. It uses JavaScript
and cross-origin ressource sharing for easy integration into (static) websites.

No, I meant "Isso"
------------------

Isso is an informal, german abbreviation for "Ich schrei sonst!", which can
roughly be translated to "I'm yelling otherwise". It usually ends the
discussion without any further arguments.

In germany, Isso `is also pokémon N° 360`__.

.. __: http://bulbapedia.bulbagarden.net/wiki/Wynaut_(Pok%C3%A9mon)

What's wrong with Disqus?
-------------------------

No anonymous comments (IP address, email and name recorded), hosted in the USA,
third-party. Just like IntenseDebate, livefrye etc. When you embed Disqus, they
can do anything with your readers (and probably mine Bitcoins, see the loading
times).

Isso is not the only open-source commenting server:

* `commento <https://commento.io/>`_, written in Go. Requires a
  `postgresql <https://www.postgresql.org/>`_ database.

* `Remark42 <https://remark42.com/docs/1.6/>`_, written in Go.

* `talkatv <https://github.com/talkatv/talkatv>`_, written in Python.
  Unfortunately, talkatv's (read "talkative") development stalled. Neither
  anonymous nor threaded comments.

* `Juvia <https://github.com/phusion/juvia>`_, written in Ruby (on Rails).
  No threaded comments, nice administration webinterface, but... yeah... Ruby.

* `Tildehash.com <http://www.tildehash.com/?article=why-im-reinventing-disqus>`_,
  written in PHP__ (compare to Python__). Did I forgot something?

* `Unobtrusive, self-hosted comments <http://stackoverflow.com/q/2053217>`_,
  discussion on StackOverflow.

.. __: http://www.cvedetails.com/vendor/74/PHP.html
.. __: http://www.cvedetails.com/vendor/10210/Python.html
