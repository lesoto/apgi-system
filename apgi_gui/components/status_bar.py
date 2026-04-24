"""
Status bar component for the APGI GUI.
"""

import tkinter as tk
from tkinter import ttk


class StatusBar:
    """Status bar component for the APGI GUI."""

    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the status bar.

        Args:
            parent: Parent widget
        """
        self.frame = ttk.Frame(parent)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.fps_label = ttk.Label(self.frame, text="FPS: 0", relief=tk.SUNKEN, width=10)
        self.fps_label.pack(side=tk.RIGHT)

        self.memory_label = ttk.Label(self.frame, text="MEM: 0 MB", relief=tk.SUNKEN, width=15)
        self.memory_label.pack(side=tk.RIGHT)

        self.time_label = ttk.Label(self.frame, text="Time: 0.0s", relief=tk.SUNKEN, width=15)
        self.time_label.pack(side=tk.RIGHT)

    def set_status(self, text: str) -> None:
        """Set the status text."""
        self.status_label.config(text=text)

    def update_metrics(self, fps: float, memory_mb: float, sim_time: float) -> None:
        """Update the metrics displayed in the status bar."""
        self.fps_label.config(text=f"FPS: {fps:.1f}")
        self.memory_label.config(text=f"MEM: {memory_mb:.1f} MB")
        self.time_label.config(text=f"Time: {sim_time:.1f}s")
