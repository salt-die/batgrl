"""Sphinx documentation builder configuration."""

from datetime import datetime

from batgrl import __version__

project = "batgrl"
author = "salt-die"
today = f"{datetime.now():%B %d, %Y}"
copyright = f"{datetime.now().year}, {author}"
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "numpydoc",
]

autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": True,
    "inherited-members": True,
    "ignore-module-all": True,
}
html_theme = "pydata_sphinx_theme"
html_sidebars = {"**": ["search-field", "sidebar-nav-bs"]}
html_theme_options = {
    "footer_start": ["copyright"],
    "github_url": "https://github.com/salt-die/batgrl",
    "navigation_with_keys": False,
    "show_prev_next": False,
}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
numpydoc_show_inherited_class_members = {"figfont.FullLayout": False}
