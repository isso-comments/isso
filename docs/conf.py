# -*- coding: utf-8 -*-
#
# Isso documentation build configuration file, created by
# sphinx-quickstart on Thu Nov 21 11:28:01 2013.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys
import io
import re
import pkg_resources

from os.path import dirname, join
# Make `_theme` custom sphinx theme available
sys.path.insert(0, join(dirname(__file__), "_theme/"))
# Make `sphinx_reredirects` extension available
sys.path.insert(0, join(dirname(__file__), "_extensions/"))

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.todo',
    'sphinx_reredirects',
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# These patterns also affect html_static_path and html_extra_path
exclude_patterns = [
    "releasing.rst",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# # The master toctree document.
master_doc = 'docs/toc'
# The document name of the “root” document, that is, the document that contains
# the root toctree directive. Default is 'index'.
# (Changed in version 4.0: Renamed root_doc from master_doc.)
root_doc = 'docs/toc'

# General information about the project.
project = 'Isso'
copyright = '2012-2024, Martin Zimmermann & contributors'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The reST default role (used for this markup: `text`) to use for all
# documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
# See https://pygments.org/styles/
pygments_style = 'abap'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
#keep_warnings = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = '_theme'
html_translator_class = "remove_heading.IssoTranslator"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "collapse_navigation": False,
    "logo_only": True,
    "navigation_depth": 1,
    #"includehidden": False,
    #"titles_only": True,
}

# If true, the text around the keyword is shown as summary of each search result.
# Default is True.
html_show_search_summary = True

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ["."]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/isso.svg"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
#html_extra_path = []

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    'docs/**': ['sidebar-docs.html'],
    'index': [],
    'news': [],
    'community': [],
    'search': [],
}

# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = {"index": "index.html"}

# If false, no module index is generated.
html_domain_indices = False

# If false, no index is generated.
html_use_index = False

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'Issodoc'

html_context = {
  'display_github': True,
  'github_user': 'posativ',
  'github_repo': 'isso',
  'github_version': 'master/docs/',
}

# -- Extension configuration -------------------------------------------------

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
# See https://sphinx-doc.org/en/master/usage/extensions/todo.html
todo_include_todos = False

# -- Options for reredirects extension ----------------------------------------------
redirects = {
    "contribute/":                        "/docs/contributing/",
    "docs/install/":                      "/docs/reference/installation/",
    "docs/quickstart/":                   "/docs/guides/quickstart/",
    "docs/troubleshooting/":              "/docs/guides/troubleshooting/",
    "docs/setup/sub-uri/":                "/docs/reference/multi-site-sub-uri/#sub-uri",
    "docs/setup/multiple-sites/":         "/docs/reference/multi-site-sub-uri/#multiple-sites",
    "docs/configuration/server/":         "/docs/reference/server-config/",
    "docs/configuration/client/":         "/docs/reference/client-config/",
    "docs/extras/deployment/":            "/docs/reference/deployment/",
    "docs/extras/advanced-integration/":  "/docs/guides/advanced-integration/",
    "docs/extras/advanced-migration/":    "/docs/guides/tips-and-tricks/#advanced-migration",
    "docs/extras/testing/":               "/docs/technical-docs/testing/",
    "docs/extras/api/":                   "/docs/reference/server-api/",
    "docs/extras/contribs/":              "/community/",
}
