Migration from Misaka to Mistune
================================

Introduction
------------

Misaka was the rendering engine for converting Markdown to HTML in previous
versions of Isso. It is being replaced by Mistune. The Markdown syntax and
options between these engines is differing and this is to document the
differences.

See :doc:`Server Configuration <../reference/server-config>` how to set
Mistune as the new rendering engine.

For Misaka, plugins are configured with the ``options`` setting. Misaka
actually refers to plugins as extensions. The ``options`` setting must be
in section ``[markup.misaka]`` in the server configuration file ``isso.cfg``.

For Mistune, plugins are configured with the ``plugins`` setting. The ``plugins``
setting must be in section ``[markup.mistune]`` in the server configuration file
``isso.cfg``.

Syntax differences
------------------

HTML elements
^^^^^^^^^^^^^

Misaka allows HTML expressions like ``<em>Hi</em>`` in Markdown. This expression
will be rendered to HTML as is: ``<em>Hi</em>``. Mistune takes a stricter approach
and replaces any HTML element with rendered text like this: ``&lt;em&gt;Hi&lt;/em&gt;``.

Strong and emphasis
^^^^^^^^^^^^^^^^^^^

Misaka interprets asterisks like this:

1. \*\*word\*\*: Strong **word**
2. \*word\*: Emphasized *word*
3. \*\*word1\*\*\*word2\*: Strong **word1** and emphasized *word2*

Mistune is the same on the first two points but does not interpret asterisks inside words:

3. \*\*word1\*\*\*word2\*: Renders as \*\*word1\*\*\*word2\*

If you want to have the same rendered result with Mistune, use underscores for emphasis:

3. \*\*word1\*\*\_word2\_: Strong **word1** and emphasized *word2*

Plugins
-------

Fenced-code
^^^^^^^^^^^

Mistune always renders fenced code. The behavior is not configurable and no
fenced-code plugin exists for Mistune.

Superscript
^^^^^^^^^^^

This plugin exists in both engines with the same name ``superscript``. The
Markdown syntax is different however.

Misaka: ``^(superscripted_text)``

Mistune: ``^superscripted_text^``
