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

google_analytics_account = os.getenv('GOOGLE_ANALYTICS_ACCOUNT', None)

html_theme_options = {
    'nav_title': 'GAME (Goals And Motivation Engine)',
    'color_primary': 'blue',
    'color_accent': 'light-blue',
    'repo_url': 'https://github.com/fvergaracl/GAME',
    'google_analytics_account': google_analytics_account,
    'repo_name': 'GAME',
    'repo_type': 'github',
    'globaltoc_depth': 3,
    # If False, expand all TOC entries
    'globaltoc_collapse': True,
    # If True, show hidden TOC entries
    'globaltoc_includehidden': True,
}


html_sidebars = {
    '**': [
        'globaltoc.html',
        'localtoc.html',
        'searchbox.html',
    ]
}
