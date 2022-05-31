:orphan:

Community
=========

.. _contact:

Getting in contact
------------------

The main place of interaction for the Isso community is the
`GitHub issue tracker <https://github.com/posativ/isso/issues>`_.

A few people - including the lead developers and maintainers - frequent the
``#isso`` channel, which you can join via
`Matrix <https://matrix.to/#/#isso:libera.chat">`_ or via IRC on
`Libera.Chat <https://libera.chat/>`_

You may also ask questions or suggest improvements on
`GitHub Discussions <https://github.com/posativ/isso/discussions>`_.

.. _scripts-and-helpers:

Scripts & Helpers
-----------------

Some utility scripts have been developed by isso users.
They are stored in the `GitHub contrib/ directory
<https://github.com/posativ/isso/tree/master/contrib>`_ :

* `dump_comments.py` : dump isso comments as text, optionally with color
* `import_blogger.py` : comment importer from Blogger

.. _powered-by-isso:

Powered by Isso
---------------

A list of websites and people that use Isso can be found at
`the wiki at GitHub <https://github.com/posativ/isso/wiki/Powered-by-isso>`_.

Feel free to add your own project to the list!

.. _adjacent-projects:

Tutorials and articles about Isso
---------------------------------

*These articles also provide concrete examples of using Isso with blog engines
like Hugo, Ghost or Pelican.*

.. Notes to editors:
   - Remember to add last updated timestamp (mon/year) to each new/updated article
   - Only publicly keep most relevant articles/tutorials here, the rest can
     stay as commented-out ones to avoid duplicates (see list below)
   - Migration complete from https://github.com/posativ/isso/wiki/Tutorials,
     wiki page deleted

* `Add comments to a static blog with Isso <https://oktomus.com/posts/2020/add-comments-to-a-static-blog-with-isso/>`_ (1/2020)
* `Adding Isso Comments to Hugo <https://stiobhart.net/2017-02-24-isso-comments/>`_ (updated 11/2021)
* `Add comments to a static blog like Hugo or Jekyll with Isso <https://djangocas.dev/blog/hugo/isso-static-blog-comments-setup-and-internal/>`_ (2/2022)
* `Installing, configuring and integrating Isso into Confluence  <https://confluence.jaytaala.com/display/TKB/Installing%2C+configuring%2C+and+integrating+isso+%28commenting+web+app%29+into+Confluence>`_ (updated 2/2020)
* `Set up Isso comments on Google Cloud <https://paulness.com/setup-isso-commenting-on-google-compute-engine-vm-cloud/>`_ (4/2018)
* `Adding Isso comments to a Ghost blog on AWS Lightsail <https://dev.to/sometimescasey/adding-isso-comments-to-a-ghost-blog-on-aws-lightsail-5ea2>`_ (12/2020)
* `Deploying Isso Commenting System Under Nginx With Docker <https://linuxhandbook.com/deploy-isso-comment/>`_ (2/2022)
* `Inside The Isso Database <https://snorl.ax/posts/2019/06/10/inside-the-isso-database/>`_ (6/2019)

.. Articles that are not relevant/recent enough:
   * `Install The Newest Isso and Integrated It with CDN like CloudFlare <https://snorl.ax/posts/2016/07/12/start-to-use-isso/`_
   * `Bye, Bye Disqus - Say Hello to Isso <https://matthiasadler.info/blog/isso-comment-integration/>`_ (8/2017)
   * `OverIQ.com: Installing Isso <https://overiq.com/installing-isso/>`_ (7/2020)
   * `Isso Comments <https://www.hallada.net/2017/11/15/isso-comments.html>`_ (11/2017, updated 5/2019)
   * `HN Discussion about Isso <https://news.ycombinator.com/item?id=16219570>`_ (1/2018)
   * `How to add Isso comments to your site <https://therandombits.com/2018/12/how-to-add-isso-comments-to-your-site/>`_ (12/2018)
   * `Isso: simple self-hosted commenting system <https://blog.phusion.nl/2018/08/16/isso-simple-self-hosted-commenting-system/>`_ (8/2018)
   * `quintagroup: Isso short project description <https://quintagroup.com/cms/python/isso>`_ (not dated)
   * `Add comments to your blog with Isso <https://stanislas.blog/2018/02/add-comments-to-your-blog-with-isso/>`_ (2/2018)
   * `Create a Hugo Blog, along with Isso comment server <https://omicx.cc/posts/2021-04-16-create-a-hugo-blog/>`_ (4/2021)
   * `Isso comments system on Debian <https://skorotkiewicz.github.io/techlog/isso-comments-system-on-debian/>`_ (10/2018)
   * `Unborking my ISSO comments system and making it more resilient <https://www.lonecpluspluscoder.com/2021/11/27/fixed-isso-comments-and-made-more-resilient/>`_ (updated 11/2021)
   * `Setting up Isso for my Hugo static website <https://www.sailadastra.com/posts/isso_comments/>`_ (6/2018)
   * `Integrate Isso into Hugo <https://www.scisoft.de/posts/technology/190912-isso-hugo/>`_ (9/2019)
   * `Installing Isso on Uberspace <https://lab.uberspace.de/guide_isso/>`_ (4/2020) (needs to be re-worked!)

Isso-adjacent Projects
----------------------

* A Webmention receiver and publisher, has a plugin to integrate with Isso: `Bussator`_
* A plugin for `Grav CMS`_ to integrate isso comments: `grav-plugin-jscomments`_
* A `Pelican theme supporting isso comments <https://github.com/Lucas-C/pelican-mg>`_
* A `Sphinx extension to integrate isso comments <https://github.com/sphinx-notes/isso>`_
* `mihokookayami/isso Docker image <https://hub.docker.com/r/mihokookayami/isso>`_

.. _Grav cms: https://en.wikipedia.org/wiki/Grav_(CMS)
.. _grav-plugin-jscomments: https://github.com/Sommerregen/grav-plugin-jscomments>
.. _Bussator: https://gitlab.com/mardy/bussator

.. note::
   Feel free to **add your own project** that builds on top of or integrates
   Isso in some manner. That way, there will be more data points for
   maintainers to judge if they can afford to make (breaking) changes in Isso's
   internals.

Other options
-------------

Isso is not the only open-source commenting server. You can find an overview at
`lisakov.com: Open source comments <https://lisakov.com/projects/open-source-comments/>`_.

Some popular options are:

* `Commento <https://commento.io/>`_, written in Go. Requires a
  `PostgreSQL <https://www.postgresql.org/>`_ database.

* `Remark42 <https://remark42.com/>`_, written in Go.

* `Staticman <https://staticman.net/>`_, written in Node.js. Adds comments
  directly to repository of static sites.

* `schnack <https://schnack.cool/>`_, written in Node.js.


.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - Define and refine community standards
   - Link to more related projects

   Ideas:

   - `Ansible community page <https://docs.ansible.com/ansible/latest/community/>`_
