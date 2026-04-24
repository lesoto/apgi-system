"""
Menu bar component for the APGI GUI.
"""

import tkinter as tk
from typing import Callable, Dict, Any

# Type alias for callback functions
Callback = Callable[..., Any]


class MenuBar:
    """Menu bar component for the APGI GUI."""

    def __init__(self, root: tk.Tk, callbacks: Dict[str, Callable]) -> None:
        """
        Initialize the menu bar.

        Args:
            root: Root window
            callbacks: Dictionary of callback functions for menu items
        """
        self.root = root
        self.callbacks = callbacks
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.modifier_key = (
            "Command" if self.root.tk.call("tk", "windowingsystem") == "aqua" else "Ctrl"
        )

        self._create_file_menu()
        self._create_edit_menu()
        self._create_simulation_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_analysis_menu()
        self._create_help_menu()

    def _create_file_menu(self) -> None:
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(
            label="New Session",
            command=self.callbacks.get("new_session") or (lambda: None),  # type: ignore[arg-type]
            accelerator=f"{self.modifier_key}+N",
        )
        file_menu.add_command(
            label="Load Configuration...",
            command=self.callbacks.get("load_config") or (lambda: None),  # type: ignore[arg-type]
            accelerator=f"{self.modifier_key}+O",
        )
        file_menu.add_command(
            label="Save Configuration...",
            command=self.callbacks.get("save_config") or (lambda: None),  # type: ignore[arg-type]
            accelerator=f"{self.modifier_key}+S",
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Export Data...",
            command=self.callbacks.get("export_data") or (lambda: None),  # type: ignore[arg-type]
            accelerator=f"{self.modifier_key}+E",
        )
        file_menu.add_command(
            label="Export Plot...",
            command=self.callbacks.get("export_plot") or (lambda: None),  # type: ignore[arg-type]
        )
        file_menu.add_separator()

        if "auto_save_var" in self.callbacks:
            file_menu.add_checkbutton(
                label="Auto-save Data",
                variable=self.callbacks["auto_save_var"],  # type: ignore[arg-type]
                command=self.callbacks.get("toggle_auto_save") or (lambda: None),  # type: ignore[arg-type]
            )

        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            command=self.callbacks.get("confirm_exit") or (lambda: None),  # type: ignore[arg-type]
            accelerator=f"{self.modifier_key}+Q",
        )

    def _create_edit_menu(self) -> None:
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(
            label="System Parameters...",
            command=self.callbacks.get("edit_parameters") or (lambda: None),  # type: ignore[arg-type]
        )
        edit_menu.add_command(
            label="Precision Settings...",
            command=self.callbacks.get("edit_precision") or (lambda: None),  # type: ignore[arg-type]
        )
        edit_menu.add_command(
            label="Ignition Threshold...",
            command=self.callbacks.get("edit_threshold") or (lambda: None),  # type: ignore[arg-type]
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Reset to Defaults",
            command=self.callbacks.get("reset_defaults") or (lambda: None),  # type: ignore[arg-type]
        )

    def _create_simulation_menu(self) -> None:
        sim_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(
            label="Start",
            command=self.callbacks.get("start_simulation") or (lambda: None),  # type: ignore[arg-type]
            accelerator="F5",
        )
        sim_menu.add_command(
            label="Pause/Resume",
            command=self.callbacks.get("pause_simulation") or (lambda: None),  # type: ignore[arg-type]
            accelerator="F6",
        )
        sim_menu.add_command(
            label="Stop",
            command=self.callbacks.get("stop_simulation") or (lambda: None),  # type: ignore[arg-type]
            accelerator="F7",
        )
        sim_menu.add_command(
            label="Reset",
            command=self.callbacks.get("reset_simulation") or (lambda: None),  # type: ignore[arg-type]
            accelerator="F8",
        )
        sim_menu.add_separator()
        sim_menu.add_command(
            label="Run Preset Task...",
            command=self.callbacks.get("run_preset_task") or (lambda: None),  # type: ignore[arg-type]
        )

    def _create_view_menu(self) -> None:
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=view_menu)

        if "view_vars" in self.callbacks:
            view_vars: Dict[str, tk.Variable] = self.callbacks["view_vars"]  # type: ignore[assignment]
            view_menu.add_checkbutton(
                label="Control Panel",
                variable=view_vars.get("control_panel"),  # type: ignore[arg-type]
                command=self.callbacks.get("toggle_control_panel") or (lambda: None),  # type: ignore[arg-type]
            )
            view_menu.add_checkbutton(
                label="Neural Activity",
                variable=view_vars.get("neural_activity"),  # type: ignore[arg-type]
                command=self.callbacks.get("toggle_neural_activity") or (lambda: None),  # type: ignore[arg-type]
            )
            view_menu.add_checkbutton(
                label="Interoception",
                variable=view_vars.get("interoception"),  # type: ignore[arg-type]
                command=self.callbacks.get("toggle_interoception") or (lambda: None),  # type: ignore[arg-type]
            )
            view_menu.add_checkbutton(
                label="System Metrics",
                variable=view_vars.get("system_metrics"),  # type: ignore[arg-type]
                command=self.callbacks.get("toggle_system_metrics") or (lambda: None),  # type: ignore[arg-type]
            )

        view_menu.add_separator()
        view_menu.add_command(
            label="Zoom In",
            accelerator=f"{self.modifier_key}++",
            command=self.callbacks.get("zoom_in") or (lambda: None),  # type: ignore[arg-type]
        )
        view_menu.add_command(
            label="Zoom Out",
            accelerator=f"{self.modifier_key}+-",
            command=self.callbacks.get("zoom_out") or (lambda: None),  # type: ignore[arg-type]
        )
        view_menu.add_command(
            label="Fit to Window",
            accelerator=f"{self.modifier_key}+0",
            command=self.callbacks.get("zoom_fit") or (lambda: None),  # type: ignore[arg-type]
        )

    def _create_tools_menu(self) -> None:
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(
            label="Trigger Ignition Event",
            command=self.callbacks.get("trigger_ignition") or (lambda: None),  # type: ignore[arg-type]
        )
        tools_menu.add_command(
            label="Induce Stressor",
            command=self.callbacks.get("induce_stressor") or (lambda: None),  # type: ignore[arg-type]
        )
        tools_menu.add_command(
            label="Modulate Precision...",
            command=self.callbacks.get("modulate_precision") or (lambda: None),  # type: ignore[arg-type]
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Inject Sensory Input...",
            command=self.callbacks.get("inject_input") or (lambda: None),  # type: ignore[arg-type]
        )
        tools_menu.add_command(
            label="Set Body State...",
            command=self.callbacks.get("set_body_state") or (lambda: None),  # type: ignore[arg-type]
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="System Diagnostics",
            command=self.callbacks.get("show_diagnostics") or (lambda: None),  # type: ignore[arg-type]
        )

    def _create_analysis_menu(self) -> None:
        analysis_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(
            label="Ignition Statistics",
            command=self.callbacks.get("show_ignition_stats") or (lambda: None),  # type: ignore[arg-type]
        )
        analysis_menu.add_command(
            label="Energy Budget Report",
            command=self.callbacks.get("show_energy_report") or (lambda: None),  # type: ignore[arg-type]
        )
        analysis_menu.add_command(
            label="Somatic Marker Analysis",
            command=self.callbacks.get("analyze_markers") or (lambda: None),  # type: ignore[arg-type]
        )
        analysis_menu.add_command(
            label="Self-Model Coherence",
            command=self.callbacks.get("analyze_coherence") or (lambda: None),  # type: ignore[arg-type]
        )
        analysis_menu.add_separator()
        analysis_menu.add_command(
            label="Statistical Analysis...",
            command=self.callbacks.get("show_statistical_analysis") or (lambda: None),  # type: ignore[arg-type]
        )
        analysis_menu.add_separator()
        analysis_menu.add_command(
            label="Generate Report...",
            command=self.callbacks.get("generate_report") or (lambda: None),  # type: ignore[arg-type]
        )

    def _create_help_menu(self) -> None:
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="Documentation",
            command=self.callbacks.get("show_docs") or (lambda: None),  # type: ignore[arg-type]
        )
        help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self.callbacks.get("show_shortcuts") or (lambda: None),  # type: ignore[arg-type]
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="About APGI System",
            command=self.callbacks.get("show_about") or (lambda: None),  # type: ignore[arg-type]
        )
