project = 'nurses_2'
copyright = '2022, salt-die'
author = 'salt-die'

release = '0.9.3'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'numpydoc',
]

autosummary_generate = True

autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
    'undoc-members': True,
    'ignore-module-all': True,
}

html_theme = 'pydata_sphinx_theme'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
