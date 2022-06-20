from datetime import datetime

from nurses_2 import __version__

project = "nurses_2"
copyright = f"{datetime.now().year}, salt-die"
author = "salt-die"
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

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
