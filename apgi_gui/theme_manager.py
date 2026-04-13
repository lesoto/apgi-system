"""
Shared Theme Utility for APGI GUI Applications

Provides consistent theming support across all GUI applications.
"""

import tkinter as tk
from typing import Any, Dict, Optional, cast, Union, List

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ThemeManager:
    """Manages color themes for GUI applications"""

    THEMES: Dict[str, Dict[str, Any]] = {
        "normal": {
            "bg": "white",
            "fg": "black",
            "canvas_bg": "white",
            "accent": "#2E86AB",
            "info": "#2E86AB",
            "success": "#48BF84",
            "warning": "#FF9F1C",
            "error": "#E63946",
            "notification_colors": {
                "high": "#FF4444",
                "medium": "#FFA500",
                "low": "#4444FF",
            },
            "battery_colors": {
                "high": "#48BF84",
                "medium": "#FF9F1C",
                "low": "#E63946",
            },
            "state_colors": {
                "idle": "#888888",
                "processing": "#2E86AB",
                "complete": "#48BF84",
                "error": "#E63946",
            },
        },
        "dark": {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "canvas_bg": "#2d2d2d",
            "accent": "#48BF84",
            "info": "#48BF84",
            "success": "#48BF84",
            "warning": "#FF9F1C",
            "error": "#E63946",
            "notification_colors": {
                "high": "#FF4444",
                "medium": "#FFA500",
                "low": "#4444FF",
            },
            "battery_colors": {
                "high": "#48BF84",
                "medium": "#FF9F1C",
                "low": "#E63946",
            },
            "state_colors": {
                "idle": "#888888",
                "processing": "#48BF84",
                "complete": "#48BF84",
                "error": "#E63946",
            },
        },
        "high_contrast": {
            "bg": "black",
            "fg": "white",
            "canvas_bg": "#000000",
            "accent": "#FFFF00",
            "info": "#FFFF00",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "error": "#FF0000",
            "notification_colors": {
                "high": "#FF0000",
                "medium": "#FFFF00",
                "low": "#FFFFFF",
            },
            "battery_colors": {
                "high": "#00FF00",
                "medium": "#FFFF00",
                "low": "#FF0000",
            },
            "state_colors": {
                "idle": "#FFFFFF",
                "processing": "#FFFF00",
                "complete": "#00FF00",
                "error": "#FF0000",
            },
        },
        "high_contrast_dark": {
            "bg": "#000000",
            "fg": "#FFFFFF",
            "canvas_bg": "#1a1a1a",
            "accent": "#00FFFF",
            "info": "#00FFFF",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "error": "#FF0000",
            "notification_colors": {
                "high": "#FF0000",
                "medium": "#FFFF00",
                "low": "#00FFFF",
            },
            "battery_colors": {
                "high": "#00FF00",
                "medium": "#FFFF00",
                "low": "#FF0000",
            },
            "state_colors": {
                "idle": "#666666",
                "processing": "#00FFFF",
                "complete": "#00FF00",
                "error": "#FF0000",
            },
        },
    }

    def __init__(self, initial_theme: str = "normal"):
        """Initialize theme manager

        Args:
            initial_theme: Starting theme name
        """
        self.current_theme = initial_theme
        self.high_contrast = False

    def get_theme_color(self, color_type: str) -> str:
        """Get a color from the current theme

        Args:
            color_type: Type of color (e.g., 'bg', 'fg', 'accent', 'info', 'success', 'warning', 'error')

        Returns:
            Color hex code
        """
        theme = self.THEMES[self.current_theme]
        return cast(str, theme.get(color_type, "black"))

    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme

        Args:
            theme_name: Name of theme to set

        Returns:
            True if successful, False if theme not found
        """
        if theme_name not in self.THEMES:
            return False

        self.current_theme = theme_name
        return True

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names

        Returns:
            List of theme names
        """
        return list(self.THEMES.keys())

    def apply_theme_to_widget(self, widget: tk.Misc, theme_name: Optional[str] = None) -> None:
        """Apply current theme to a widget

        Args:
            widget: Tkinter widget to theme
            theme_name: Optional theme name, uses current if not specified
        """
        theme = self.THEMES[theme_name or self.current_theme]

        # Apply background and foreground if widget supports it
        try:
            widget.configure(bg=theme["bg"], fg=theme["fg"])  # type: ignore
        except tk.TclError:
            # Widget doesn't support bg/fg configuration
            pass

    def apply_theme_to_canvas(
        self, canvas: Union[tk.Canvas, FigureCanvasTkAgg], theme_name: Optional[str] = None
    ) -> None:
        """Apply current theme to a canvas

        Args:
            canvas: Tkinter canvas widget or matplotlib FigureCanvasTkAgg
            theme_name: Optional theme name, uses current if not specified
        """
        theme = self.THEMES[theme_name or self.current_theme]

        try:
            # Check if this is a matplotlib FigureCanvasTkAgg
            if hasattr(canvas, "figure"):
                # For matplotlib canvases, set the figure's facecolor
                canvas.figure.set_facecolor(theme["canvas_bg"])
                if hasattr(canvas, "draw"):
                    canvas.draw()  # Redraw to apply the change
            else:
                # For Tkinter canvases, use config
                canvas.config(bg=cast(str, theme["canvas_bg"]))
        except tk.TclError:
            pass


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance

    Returns:
        ThemeManager instance
    """
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
