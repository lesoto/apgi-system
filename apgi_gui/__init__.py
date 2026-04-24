"""
APGI System GUI Package

This package provides a comprehensive GUI for the Allostatic Precision-Gated Ignition System.
"""

__version__ = "0.1.0"

# Lazy imports to avoid RuntimeWarning when running as __main__
__all__ = ["APGIGui", "run_gui", "main"]


def __getattr__(name: str):
    """Lazy import to avoid circular import issues when running as __main__."""
    if name in ("APGIGui", "main", "run_gui"):
        from apgi_gui.main import APGIGui, main

        if name == "APGIGui":
            return APGIGui
        if name == "main":
            return main
        if name == "run_gui":
            return main
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
