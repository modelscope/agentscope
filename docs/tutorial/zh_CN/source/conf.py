# -*- coding: utf-8 -*-
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "AgentScope Doc"
copyright = "2025, Alibaba"
author = "Alibaba Tongyi Lab"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_gallery.gen_gallery",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
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

templates_path = ["../../_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

languages = ["en", "zh_CN"]
language = "zh_CN"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["../../_static"]

html_css_files = [
    "css/gallery.css",
]

html_js_files = [
    "language_switch.js",
]

source_suffix = [".md", ".rst"]


# -- Options for API documentation -------------------------------------------

autodoc_member_order = "groupwise"
add_module_names = False
python_display_short_literal_types = True


def skip_member(app, what, name, obj, skip, options):
    if name in []:
        return True

    return skip


def setup(app):
    ######
    # The following block is to avoid pure text build error
    from sphinx.writers.text import TextTranslator
    from docutils.nodes import Node

    # 1) Create a no-op "visit" method
    def visit_imgsgnode(self, node: Node):
        # Here you can decide what text you want to generate, if any
        # For now, do nothing (no output)
        pass

    # 2) Create a matching "depart" method
    def depart_imgsgnode(self, node: Node):
        pass

    # 3) Assign these to the TextTranslator so that Sphinx doesn't error
    TextTranslator.visit_imgsgnode = visit_imgsgnode
    TextTranslator.depart_imgsgnode = depart_imgsgnode
    ######

    app.connect("autodoc-skip-member", skip_member)
