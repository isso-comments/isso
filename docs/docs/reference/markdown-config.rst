Configure how comments are rendered
===================================

You can use the :ref:`configure-markup` section in your configuration file to
influence how the `Markdown`_ syntax in comments is rendered and displayed
to the user.

Per Isso's defaults, commenters can use **standard Markdown syntax**, **minus
footnotes and tables**
(see :ref:`below <available-markdown-options>` on how to activate them).

.. _Markdown: https://daringfireball.net/projects/markdown/

Because users can enter untrusted, potentially **malicious text** into the
comment box, Isso applies some safety precautions so that the rendered comments
do not contain e.g. malware ``<script>`` tags or ``iframes``. You should not
blindly change these defaults to allow more elements without knowing what you
are doing.

Plain HTML in comments
----------------------

Per Isso's defaults, commenters can also enter plain HTML instead of or inside
of Markdown text.

To disallow user-entered plain HTML, add ``skip-html`` to ``[markup] flags``.

.. todo:: Maybe replace this list with a link to ``isso.conf``?

+-------------------------------------------+-----------------------------------+
| These HTML tags are allowed by default:   | These HTML *attributes* allowed   |
|                                           | by default:                       |
| ``<a>``, ``<blockquote>``, ``<br>``,      |                                   |
| ``<code>``, ``<del>``, ``<em>``,          | ``align`` (for tables) and        |
| ``<h1>``, ``<h2>``, ``<h3>``, ``<h4>``,   | ``href`` (for ``<a href="...">``) |
| ``<h5>``, ``<h6>``, ``<hr>``, ``<ins>``,  |                                   |
| ``<li>``, ``<ol>``, ``<p>``, ``<pre>``,   |                                   |
| ``<strong>``, ``<table>``, ``<tbody>``,   |                                   |
| ``<td>``, ``<th>``, ``<thead>``,          |                                   |
| ``<ul>``.                                 |                                   |
+-------------------------------------------+-----------------------------------+

Elements and attributes not in the allowed list will just be stripped.
``<foo bar=1>text</foo>`` will simply become ``text``.

.. note:: Keep in mind that removing an element from the allowed tags will not
   only disallow commenters from entering it as a plain HTML tag, but also
   remove formatting from any markdown that would generate the tag.

   An example: Allowed elements are ``['a', 'strong']``. Then ``Some *text*``
   would not be rendered in italics since the ``em`` element would be
   forbidden.

Line breaks
-----------

By default, Markdown requires two new lines to create a paragraph break.
E.g. this block:

.. code-block:: markdown

   This is a quite **long paragraph** that spans multiple lines,
   which is split over multiple lines in the Markdown source code.

   Thus, the width remains under about 80 characters and the writer does not
   have to scroll so far to the right.

will be rendered as:

    This is a quite **long paragraph** that spans multiple lines,
    which is split over multiple lines in the Markdown source code.

    Thus, the width remains under about 80 characters and the writer does not
    have to scroll so far to the right.

Set ``hard-wrap`` in ``[markup] flags`` to only require a single newline to
create a line break (``<br>``):

.. code-block:: markdown

   One line.
   Another line.

will then be rendered as:

   | One line.
   | Another line.


Defaults and available options
------------------------------

.. _available-markdown-options:

.. note:: Make sure to use e.g. ``fenced-code`` (with a ``-`` dash) instead of
   ``fenced_code`` (underline) to refer to extension names.

The following behavior is **enabled by default:**

.. role::  raw-html(raw)
    :format: html

+----------------------------------------------------------+-------------------+
| Explanation                                              | Extension name    |
+==========================================================+===================+
| Automatically convert ``http://`` links and email        | ``autolink``      |
| addresses into clickable links, even if commenters did   |                   |
| not format them using ``[text](http://link.site)``       |                   |
+----------------------------------------------------------+-------------------+
| Blocks that are surrounded by triple backticks (```````) | ``fenced-code``   |
| at the beginning and at the end are rendered as code     |                   |
| blocks, without needing to be indented.                  |                   |
+----------------------------------------------------------+-------------------+
| Text surrounded in two ``~`` gets a line through:        | ``strikethrough`` |
| ``Text ~~deleted~~``                                     |                   |
| :raw-html:`&rarr; Text <del>deleted</del>`               |                   |
+----------------------------------------------------------+-------------------+
| Text after the ``^`` character is rendered as            | ``superscript``   |
| "superscript": ``Intelligence^2`` :raw-html:`&rarr;`     |                   |
| Intelligence\ :sup:`2`.                                  |                   |
+----------------------------------------------------------+-------------------+

The following **additional options** are available:

+----------------------------------------------------------+---------------------------+
| Explanation                                              | Extension name            |
+==========================================================+===========================+
| Ignore indented code blocks                              | ``disable-indented-code`` |
+----------------------------------------------------------+---------------------------+
| Ignore inline LaTeX-style math blocks, such as           | ``math``                  |
| inline ``$equations$`` or display ``$$equations$$``,     |                           |
| allowing them to be processed separately with a          |                           |
| JavaScript library.                                      |                           |
| **Note:** This extension will *not* render equations     |                           |
| or any form of math, it just marks them to be ignored by |                           |
| the markdown parser. A library such as                   |                           |
| `MathJax <https://www.mathjax.org/>`_                    |                           |
| or `KaTeX <https://katex.org/>`_ is needed for that.     |                           |
+----------------------------------------------------------+---------------------------+
| Normally, everything between two ``_underscores_`` would | ``no-intra-emphasis``     |
| be rendered with *emphasis*. This option disables        |                           |
| parsing of underscores *within* words.                   |                           |
| ``A_good_day`` :raw-html:`&rarr;` A_good_day,            |                           |
| not A\ *good*\ day                                       |                           |
+----------------------------------------------------------+---------------------------+
| Parse markdown footnotes. Not recommended because        | ``footnotes``             |
| multiple footnotes by different commenters on the same   |                           |
| page could clash due to duplicate links to footnotes.    |                           |
+----------------------------------------------------------+---------------------------+
| Use two ``=`` signs like ``==this==`` to highlight text. | ``highlight``             |
+----------------------------------------------------------+---------------------------+
| Text inside quotes gets a special "quote" class.         | ``quote``                 |
| Perhaps useful for styling in CSS                        |                           |
+----------------------------------------------------------+---------------------------+
| Enable Markdown tables.                                  | ``tables``                |
| **Note:** The ``<tr>`` and all other ``<table>``-related |                           |
| tags need to be allowed under ``allowed-elements`` for   |                           |
| this to work. Also, a table cannot be surrounded by      |                           |
| anything other than blank lines to render properly.      |                           |
+----------------------------------------------------------+---------------------------+
| Instead of ``_underscore`` resulting in *emphasis*,      | ``underline``             |
| the resulting text will be... underlined.                |                           |
+----------------------------------------------------------+---------------------------+

.. todo:: ``no-intra-emphasis`` should be made default

.. seealso::
    The `flask-misaka docs <https://flask-misaka.readthedocs.io/en/latest/#options>`_
    also have a good explanation of what each extension options does.
