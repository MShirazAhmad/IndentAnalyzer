#!/usr/bin/env python3
"""
Nanoindentation Analysis Source Package
ISO 14577-4:2016 compliant nanoindentation analysis system
"""

__version__ = "2.1.0"
__author__ = "Nanoindentation Analysis Team"
__description__ = "ISO 14577-4:2016 compliant nanoindentation analysis"

# Package structure
from . import core
from . import analysis
from . import calibration
from . import gui

__all__ = [
    'core',
    'analysis', 
    'calibration',
    'gui'
]
