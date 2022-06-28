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

html_theme_options = {
  "show_prev_next": False,
}

html_show_sphinx = False

html_show_sourcelink = True

html_sidebars = {
    "**": ["globaltoc.html", "sourcelink.html", "searchbox.html"],
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
