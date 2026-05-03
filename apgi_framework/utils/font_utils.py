"""Font utilities for cross-platform font compatibility."""

import tkinter as tk
from typing import List, Tuple


def get_system_fonts() -> List[str]:
    """Get list of available system fonts."""
    try:
        # Try to get fonts from tkinter
        root = tk.Tk()
        root.withdraw()  # Hide the window

        families = list(root.tk.call("font", "families"))
        root.destroy()
        return families
    except Exception:
        # Fallback to common font families
        return [
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Courier New",
            "Verdana",
            "Tahoma",
        ]


def get_font_fallback(primary: str, *fallbacks: str) -> str:
    """Get best available font.

    Args:
        primary: Primary font choice
        *fallbacks: Fallback fonts in order of preference

    Returns:
        Single font name that's available
    """
    system_fonts = get_system_fonts()

    # Check primary font first
    if primary in system_fonts:
        return primary

    # Check fallbacks
    for fallback in fallbacks:
        if fallback in system_fonts:
            return fallback

    # Return generic family as last resort
    return "Arial"  # Most widely available


# Cache for font families
_FONT_FAMILIES = None


def get_font_families() -> dict:
    """Get standard font families with lazy initialization."""
    global _FONT_FAMILIES
    if _FONT_FAMILIES is None:
        _FONT_FAMILIES = {
            "sans-serif": get_font_fallback(
                "Arial", "Helvetica", "Verdana", "Tahoma", "sans-serif"
            ),
            "serif": get_font_fallback("Times New Roman", "Times", "Georgia", "serif"),
            "monospace": get_font_fallback("Courier New", "Courier", "Consolas", "monospace"),
        }
    return _FONT_FAMILIES


def get_font(size: int, weight: str = "normal", family: str = "sans-serif") -> Tuple[str, int, str]:
    """Get font tuple with size and weight.

    Args:
        size: Font size
        weight: Font weight ("normal", "bold")
        family: Font family ("sans-serif", "serif", "monospace")

    Returns:
        Font tuple for tkinter/CustomTkinter
    """
    font_name = get_font_families().get(family, "Arial")

    if weight == "bold":
        return (font_name, size, "bold")
    else:
        return (font_name, size, "normal")
