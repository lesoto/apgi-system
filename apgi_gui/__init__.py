"""
APGI System GUI Package

This package provides a comprehensive GUI for the Allostatic Precision-Gated Ignition System.
The main GUI class is APGIGui, which can be imported and used directly.
"""

from ..apgi_gui import APGIGui, main

# Create alias for backward compatibility
run_gui = main

__version__ = "0.1.0"
__all__ = ["APGIGui", "run_gui", "main"]
