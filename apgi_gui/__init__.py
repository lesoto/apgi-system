"""
APGI System GUI Package

This package provides a comprehensive GUI for the Allostatic Precision-Gated Ignition System.
The main GUI class is APGIGui, which can be imported and used directly.
"""

# Import the main GUI class directly from the module file
import sys
import os

# Add the parent directory to the path to allow direct import
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the GUI class
from apgi_gui import APGIGui, main

# Create alias for backward compatibility
run_gui = main

__version__ = "0.1.0"
__all__ = ["APGIGui", "run_gui", "main"]
