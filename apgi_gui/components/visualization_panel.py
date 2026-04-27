"""
Visualization panel component for the APGI GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from .plot_widgets import MultiPlotWidget


class VisualizationPanel:
    """Visualization panel component with multiple tabs."""

    def __init__(self, parent: tk.Widget) -> None:
        """
        Initialize the visualization panel.

        Args:
            parent: Parent widget
        """
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tabs: Dict[str, ttk.Frame] = {}
        self.plots: Dict[str, MultiPlotWidget] = {}

        self._create_neural_tab()
        self._create_interoception_tab()
        self._create_metrics_tab()

    def _create_neural_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Neural Activity")
        self.tabs["neural"] = tab

        multi_plot = MultiPlotWidget(tab, rows=2, cols=1)
        self.plots["neural"] = multi_plot

        multi_plot.add_plot("ignition", 0, 0, "Ignition Probability", ylabel="Probability")
        multi_plot.plots["ignition"].add_line("prob", color="red")

        multi_plot.add_plot("surprise", 1, 0, "Precision-Weighted Surprise", ylabel="Surprise")
        multi_plot.plots["surprise"].add_line("val", color="blue")

    def _create_interoception_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Interoception")
        self.tabs["intero"] = tab

        multi_plot = MultiPlotWidget(tab, rows=2, cols=1)
        self.plots["intero"] = multi_plot

        multi_plot.add_plot("precision", 0, 0, "Interoceptive Precision", ylabel="Precision")
        multi_plot.plots["precision"].add_line("val", color="green")

        multi_plot.add_plot("somatic", 1, 0, "Somatic Marker Gain", ylabel="Gain")
        multi_plot.plots["somatic"].add_line("val", color="orange")

    def _create_metrics_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="System Metrics")
        self.tabs["metrics"] = tab

        multi_plot = MultiPlotWidget(tab, rows=2, cols=1)
        self.plots["metrics"] = multi_plot

        multi_plot.add_plot("energy", 0, 0, "Metabolic Reserves", ylabel="Percent")
        multi_plot.plots["energy"].add_line("reserves", color="blue")

        multi_plot.add_plot("load", 1, 0, "Allostatic Load", ylabel="Percent")
        multi_plot.plots["load"].add_line("load", color="purple")

    def update_plots(self, data: Dict[str, List[float]], time_data: List[float]) -> None:
        """Update all plots with new data."""
        # Neural tab
        if "ignition" in data:
            self.plots["neural"].plots["ignition"].update_data("prob", time_data, data["ignition"])
        if "surprise" in data:
            self.plots["neural"].plots["surprise"].update_data("val", time_data, data["surprise"])

        # Intero tab
        if "intero_precision" in data:
            self.plots["intero"].plots["precision"].update_data(
                "val", time_data, data["intero_precision"]
            )
        if "somatic_gain" in data:
            self.plots["intero"].plots["somatic"].update_data(
                "val", time_data, data["somatic_gain"]
            )

        # Metrics tab
        if "metabolic_reserves" in data:
            self.plots["metrics"].plots["energy"].update_data(
                "reserves", time_data, data["metabolic_reserves"]
            )
        if "allostatic_load" in data:
            self.plots["metrics"].plots["load"].update_data(
                "load", time_data, data["allostatic_load"]
            )
