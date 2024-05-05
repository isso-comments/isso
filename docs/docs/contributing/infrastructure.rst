Isso Project Infrastructure
===========================

Conceived initially as  Martin Zimmermann (`@posativ`_)'s nimble personal project,
Isso has grown to encompass a larger community of users and maintainers. With a
transition away from being controlled solely by Martin, the project
infrastructure is now largely community-owned.

This page documents the parts that make up the project and who is responsible
for them, in order for new or potential maintainers to get a better overview.

.. attention::

   We realize that many of our processes could use an overhaul and would
   benefit from much more automation. If you know how, please open a Pull
   Request or offer your help in an issue!

Website
-------

The project website used to be hosted at `posativ.org/isso`_, but now lives at
its own domain `isso-comments.de`_.

* The domain `isso-comments.de`_ is registered by `@ix5`_ through German registrar
  `netcup.de`_. Costs exactly 1.44€ each year so quite sustainable, but makes
  @ix5 a potential bus factor.
* Website content is served by GitHub Pages. The `sphinx-doc`_-built site is
  auto-deployed to `isso-comments.github.io`_ via a `GitHub Action`_ on every push
  to the Isso main repository. Requires appropriate ``A`` and ``CNAME`` records
  to GitHub's servers:

  .. code-block:: console

      $ dig www.isso-comments.de
      www.isso-comments.de.	300	IN	CNAME	isso-comments.github.io.
      isso-comments.github.io. 3600	IN	A	185.199.108.153
      isso-comments.github.io. 3600	IN	A	185.199.109.153
      isso-comments.github.io. 3600	IN	A	185.199.110.153
      isso-comments.github.io. 3600	IN	A	185.199.111.153

* The demo instance of the comment form (on the homepage) lives on `@ix5`_'s
  server at `comments.isso-comments.de`_ and consists of the latest ``isso``
  package from ``PyPI``, deployed via ``gunicorn``.
  The ansible role to set this up is available at `ansible-role-isso`_. The
  simple auto-reset feature to curtail vandalism is documented at
  `isso-demo-config`_.

.. _@posativ: https://github.com/posativ
.. _posativ.org/isso: https://posativ.org/isso
.. _isso-comments.de: https://isso-comments.de
.. _@ix5: https://github.com/ix5
.. _netcup.de: https://netcup.de
.. _sphinx-doc: https://www.sphinx-doc.org/
.. _isso-comments.github.io: https://github.com/isso-comments/isso-comments.github.io
.. _GitHub Action: https://github.com/isso-comments/isso/blob/master/.github/workflows/build-upload-docs.yml
.. _comments.isso-comments.de: https://comments.isso-comments.de
.. _ansible-role-isso: https://git.ix5.org/felix/ansible-role-isso
.. _isso-demo-config: https://github.com/isso-comments/isso-demo-config

Development
-----------

Development happens under the `isso-comments GitHub organisation`_, with the
main `isso-comments/isso`_ repository serving as the source for the Python
parts, Javascript client, website and documentation, API documentation as well
as CI/CD configuration.

The ``master`` branch has branch protections set up, requiring an approving
maintainer review before merging.

.. _isso-comments GitHub organisation: https://github.com/isso-comments
.. _isso-comments/isso: https://github.com/isso-comments/isso

Packaging
---------

Isso is released "officially" as an installable Python package on `PyPI`_
and as a docker image. Other distributors may package releases of Isso natively
for operating systems (e.g. for the Arch User repository or formerly Debian),
but support for these releases should be given by the packager.

.. _PyPI: https://pypi.org/project/isso/

PyPI (Python Package Index)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Release rights for the `isso PyPI`_ project are held by @jelmer, @posativ, @blatinier and @ix5.

.. _isso PyPI: https://pypi.org/project/isso/

Docker image
^^^^^^^^^^^^

The `ghcr.io/isso-comments/isso docker image`_ is rebuilt on every push to
``master``. Push rights for manually created tags (e.g. ``:release``) are
inherited from the main ``isso-comments/isso`` GitHub repository (toggle
``Inherit access from source repository`` turned on).

The `ghcr.io/isso-comments/isso-js-testbed`_ image for running ``Jest``- and
``puppet``-based unit and integration tests is rebuilt and pushed every week by
a GitHub Action.

.. _ghcr.io/isso-comments/isso docker image: https://github.com/isso-comments/isso/pkgs/container/isso
.. _ghcr.io/isso-comments/isso-js-testbed: https://github.com/orgs/isso-comments/packages/container/package/isso-js-testbed

Secrets
-------

There are some "`secrets`_" needed to make the auto-deploy feature for GitHub Pages work.

* The main ``isso-comments/isso`` repository holds a *private* key in the
  variable ``ACTIONS_DEPLOY_KEY`` (`link to action secrets`_).
* The deploy repository ``isso-comments/isso-comments.github.io`` for GitHub
  Pages is set up with a *public* deploy key (`link to deploy keys`_)
  corresponding to the action secrets private key, allowing actions running in
  the source repository to deploy code (the newly generated website) in this
  repository.

*(The direct links only work for maintainers with full repository access).*

The docker actions do not need to be outfitted with any special secrets since
the main repository is already set up as a source for "Actions access" with
write access (`link to package settings`_).

.. _link to action secrets: https://github.com/isso-comments/isso/settings/secrets/actions
.. _link to deploy keys: https://github.com/isso-comments/isso-comments.github.io/settings/keys
.. _secrets: https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
.. _link to package settings: https://github.com/orgs/isso-comments/packages/container/isso/settings

Social
------

There exists an IRC channel (``#isso``) on `Libera.chat`_ but it is seldomly
active and not used for coordination between maintainers. Most discussion
happens in public on GitHub Issues; for private communication among each other
regarding handover of project resources/keys (very rare) the maintainers have
so far used E-mail.

.. _Libera.chat: https://libera.chat/
