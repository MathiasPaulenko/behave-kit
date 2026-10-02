"""Sphinx configuration for behave-kit documentation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("..").resolve()))

import behave_kit  # noqa: E402

project = "behave-kit"
author = "Mathias Paulenko"
copyright = "2026, Mathias Paulenko"  # noqa: A001
release = behave_kit.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path: list[str] = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path: list[str] = []

autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
