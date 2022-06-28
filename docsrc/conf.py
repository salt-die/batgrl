from datetime import datetime

from nurses_2 import __version__

author = "salt-die"
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

html_sidebars = {
    "**": ["search-field", "sidebar-nav-bs"]
}

html_theme_options = {
    "show_prev_next": False,
    "left_sidebar_end": [],
    "page_sidebar_items": ["page-toc"],
    "footer_items": [],
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
