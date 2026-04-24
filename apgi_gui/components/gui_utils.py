"""
General GUI utilities for APGI applications.
"""

import tkinter as tk
from typing import Any, Callable, Dict, List, Optional


class Tooltip:
    """A tooltip that appears when hovering over a widget."""

    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window: Optional[tk.Toplevel] = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event: Optional[tk.Event] = None) -> None:
        if self.tooltip_window or not self.text:
            return

        # Get cursor position for tooltip
        if hasattr(self.widget, "winfo_pointerxy"):
            x, y = self.widget.winfo_pointerxy()
        else:
            x, y = self.widget.winfo_rootx() + 25, self.widget.winfo_rooty() + 25

        x += 25
        y += 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#FFFFE1",
            relief="solid",
            borderwidth=1,
            font=("tahoma", 8, "normal"),
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event: Optional[tk.Event] = None) -> None:
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class KeyboardManager:
    """Manages keyboard shortcuts for the application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.shortcuts: Dict[str, Callable] = {}

    def bind_shortcut(self, sequence: str, callback: Callable, description: str = "") -> None:
        """Bind a keyboard sequence to a callback.

        Args:
            sequence: The keyboard sequence (e.g., "F9", "<Control-s>")
            callback: The function to call when the shortcut is triggered
            description: Optional description of what the shortcut does (for documentation)
        """
        self.shortcuts[sequence] = callback
        self.root.bind(sequence, lambda e: callback())

    def unbind_shortcut(self, sequence: str) -> None:
        """Unbind a keyboard sequence."""
        if sequence in self.shortcuts:
            del self.shortcuts[sequence]
            self.root.unbind(sequence)


class UndoRedoManager:
    """Manages undo and redo operations."""

    def __init__(self, max_history: int = 50):
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_history = max_history

    def push_state(self, state: Dict[str, Any]) -> None:
        """Push a new state onto the undo stack."""
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform undo and return the previous state."""
        if not self.undo_stack:
            return None
        self.redo_stack.append(current_state)
        return self.undo_stack.pop()

    def redo(self, current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform redo and return the next state."""
        if not self.redo_stack:
            return None
        self.undo_stack.append(current_state)
        return self.redo_stack.pop()

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
