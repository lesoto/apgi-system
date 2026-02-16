"""
APGI System GUI Package

This package provides a comprehensive GUI for the Allostatic Precision-Gated Ignition System.
The main GUI class is APGIGui, which can be imported and used directly.
"""

# Import the main GUI class directly from the module file
import sys
import os
import importlib.util

# Add the parent directory to the path to allow direct import
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location(
    "apgi_gui_module", os.path.join(parent_dir, "apgi_gui.py")
)
if spec is None:
    raise ImportError("Could not load apgi_gui.py")

apgi_gui_module = importlib.util.module_from_spec(spec)
if spec.loader is None:
    raise ImportError("Could not load apgi_gui.py loader")

spec.loader.exec_module(apgi_gui_module)

# Extract the classes and functions
APGIGui = apgi_gui_module.APGIGui
main = apgi_gui_module.main

# Create alias for backward compatibility
run_gui = main

__version__ = "0.1.0"
__all__ = ["APGIGui", "run_gui", "main"]
