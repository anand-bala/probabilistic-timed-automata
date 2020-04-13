import os
import sys
sys.path.insert(0, os.path.abspath(".."))

from better import better_theme_path
import pta

# -- Project information -----------------------------------------------------

project = "Probabilistic Timed Automata"
copyright = "2020, Anand Balakrishnan"
author = "Anand Balakrishnan"
version = pta.__version__.split('-')[0]
release = pta.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]

language = "en"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# Based on: https://github.com/Yelp/mrjob/blob/master/docs/conf.py

html_theme_path = [better_theme_path]
html_theme = "better"

html_context = {}
html_sidebars = {
    '**': ['localtoc.html', 'searchbox.html'],
}

html_title = F"{project} v{release} documentation"
html_short_title = "Home"

html_show_sourcelink = True
html_static_path = ["_static"]

# -- Extension configuration -------------------------------------------------

# Napoleon settings
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc configuration
autodoc_member_order = 'bysource'
# TODO: Update this when Sphinx 3.0 is released
autodoc_typehints = 'description'

# -- Options for todo extension ----------------------------------------------

todo_include_todos = True
