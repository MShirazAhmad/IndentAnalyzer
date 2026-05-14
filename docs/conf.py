from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import __version__

project = 'IndentAnalyzer'
author = 'Nanoindentation Analysis Team'
release = __version__

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

myst_enable_extensions = [
    'amsmath',
    'colon_fence',
    'dollarmath',
]

myst_heading_anchors = 3
autosummary_generate = True
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'IndentAnalyzer documentation'
