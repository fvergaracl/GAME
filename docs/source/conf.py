import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'GAME'
copyright = '2024, fvergaracl'
author = 'fvergaracl'
release = 'v1.1.003'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = []

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_material'
html_static_path = ['_static']

html_theme_options = {
    'color_primary': 'blue',
    'color_accent': 'light-blue',
    'repo_url': 'https://github.com/fvergaracl/GAME',
    'repo_name': 'GAME',
}
