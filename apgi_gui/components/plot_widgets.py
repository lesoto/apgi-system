"""
Plotting widgets for the APGI GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class PlotWidget:
    """A reusable matplotlib plot widget for Tkinter."""

    def __init__(
        self, parent: tk.Widget, title: str, xlabel: str = "", ylabel: str = "", figsize=(5, 3)
    ) -> None:
        """
        Initialize the plot widget.

        Args:
            parent: Parent widget
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            figsize: Figure size
        """
        self.figure = Figure(figsize=figsize, dpi=100, tight_layout=True)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.lines: Dict[str, Any] = {}

    @property
    def fig(self):
        """Alias for figure (for compatibility)."""
        return self.figure

    def add_line(self, name: str, color: str = "blue", label: Optional[str] = None) -> None:
        """Add a data line to the plot."""
        (line,) = self.ax.plot([], [], color=color, label=label or name)
        self.lines[name] = line
        if label or name:
            self.ax.legend()

    def update_data(self, name: str, xdata: List[float], ydata: List[float]) -> None:
        """Update the data for a specific line."""
        if name in self.lines:
            self.lines[name].set_data(xdata, ydata)
            self._rescale()
            self.canvas.draw_idle()

    def _rescale(self) -> None:
        """Rescale the plot axes to fit the data."""
        self.ax.relim()
        self.ax.autoscale_view()


class MultiPlotWidget:
    """A widget containing multiple plots in a grid."""

    def __init__(self, parent: tk.Widget, rows: int, cols: int) -> None:
        """
        Initialize the multi-plot widget.

        Args:
            parent: Parent widget
            rows: Number of rows
            cols: Number of columns
        """
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.plots: Dict[str, PlotWidget] = {}
        self.rows = rows
        self.cols = cols

    @property
    def fig(self):
        """Get the figure from the first plot (for compatibility)."""
        if self.plots:
            return next(iter(self.plots.values())).figure
        return None

    @property
    def canvas(self):
        """Get the canvas from the first plot (for compatibility)."""
        if self.plots:
            return next(iter(self.plots.values())).canvas
        return None

    def add_plot(self, key: str, row: int, col: int, title: str, **kwargs) -> PlotWidget:
        """Add a plot to the grid."""
        plot_frame = ttk.Frame(self.frame)
        plot_frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
        self.frame.grid_rowconfigure(row, weight=1)
        self.frame.grid_columnconfigure(col, weight=1)

        plot = PlotWidget(plot_frame, title, **kwargs)
        self.plots[key] = plot
        return plot
