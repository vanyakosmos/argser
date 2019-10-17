# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import re
import sys

# sys.path.insert(0, os.path.abspath(os.pardir))
root = os.path.abspath(os.path.join(os.path.pardir, os.path.pardir))
module_root = os.path.abspath(os.path.join(os.path.pardir, os.path.pardir, 'argser'))
sys.path.insert(0, module_root)
# sys.path.insert(0, os.path.abspath(module_dir))

# -- Project information -----------------------------------------------------

project = 'argser'
copyright = '2019, Bachynin Ivan'
author = 'Bachynin Ivan'

# The full version, including alpha/beta/rc tags
with open(os.path.join(root, 'pyproject.toml'), 'r') as f:
    version = re.search(r'version\s+=\s+"(.*)"', f.read(), flags=re.MULTILINE).group(1)

# The full version, including alpha/beta/rc tags.
print('version', version)
release = version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'm2r',
    'sphinxcontrib.apidoc',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
pygments_style = 'friendly'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_context = {
    "display_github": True,
    "github_user": "vanyakosmos",
    "github_repo": "argser",
    "github_version": "master",
}

# -- Extensions --------------------------------------------------------------

apidoc_module_dir = module_root
apidoc_output_dir = 'modules'
apidoc_excluded_paths = [
    'consts.py',
    'utils.py',
    'logging.py',
]
apidoc_separate_modules = True
apidoc_toc_file = False
