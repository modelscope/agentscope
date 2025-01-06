# -*- coding: utf-8 -*-
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AgentScope Doc"
copyright = "2024, Alibaba"
author = "Alibaba Tongyi Lab"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_gallery.gen_gallery",
]

myst_enable_extensions = [
    "colon_fence",
]

sphinx_gallery_conf = {
    "download_all_examples": False,
    "examples_dirs": [
        "tutorial",
    ],
    "gallery_dirs": [
        "build_tutorial",
    ],
    "filename_pattern": "tutorial/.*\.py",
    "example_extensions": [".py"],
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

languages = ["en", "zh_CN"]
language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_css_files = [
    "css/gallery.css",
]

source_suffix = [".md", ".rst"]
