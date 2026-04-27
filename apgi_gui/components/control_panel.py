"""
Control panel component for the APGI GUI.
"""

import datetime
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Any, Callable, Dict, Union, cast


class ControlPanel:
    """Control panel component for the APGI GUI."""

    def __init__(
        self,
        parent: tk.Widget,
        callbacks: Dict[str, Union[Callable, tk.Variable, Dict[str, tk.Variable]]],
    ) -> None:
        """
        Initialize the control panel.

        Args:
            parent: Parent widget
            callbacks: Dictionary of callback functions and variables
        """
        self.parent = parent
        self.callbacks = callbacks

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self._create_simulation_controls()
        self._create_system_status()
        self._create_parameter_adjustments()
        self._create_event_log()

    def _create_simulation_controls(self) -> None:
        control_frame = ttk.LabelFrame(self.frame, text="Simulation Control", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        start_callback = self.callbacks.get("start_simulation")
        cmd = (
            cast(Callable[[], Any], start_callback) if callable(start_callback) else (lambda: None)
        )
        self.start_btn = ttk.Button(btn_frame, text="▶ Start", command=cmd, width=10)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        pause_callback = self.callbacks.get("pause_simulation")
        cmd = (
            cast(Callable[[], Any], pause_callback) if callable(pause_callback) else (lambda: None)
        )
        self.pause_btn = ttk.Button(
            btn_frame,
            text="⏸ Pause",
            command=cmd,
            width=10,
            state=tk.DISABLED,
        )
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        stop_callback = self.callbacks.get("stop_simulation")
        cmd = cast(Callable[[], Any], stop_callback) if callable(stop_callback) else (lambda: None)
        self.stop_btn = ttk.Button(
            btn_frame,
            text="⏹ Stop",
            command=cmd,
            width=10,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        reset_callback = self.callbacks.get("reset_simulation")
        cmd = (
            cast(Callable[[], Any], reset_callback) if callable(reset_callback) else (lambda: None)
        )
        self.reset_btn = ttk.Button(btn_frame, text="↻ Reset", command=cmd, width=10)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)

        speed_var = self.callbacks.get("speed_var")
        if isinstance(speed_var, (tk.DoubleVar, tk.IntVar)):
            speed_scale = ttk.Scale(
                speed_frame, from_=0.1, to=10.0, orient=tk.HORIZONTAL, variable=speed_var
            )
            speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            self.speed_label = ttk.Label(speed_frame, text=f"{speed_var.get():.1f}x")
            self.speed_label.pack(side=tk.LEFT)

            speed_var.trace_add(
                "write", lambda *args: self.speed_label.config(text=f"{speed_var.get():.1f}x")
            )
        else:
            # Fallback if no speed_var provided
            speed_scale = ttk.Scale(speed_frame, from_=0.1, to=10.0, orient=tk.HORIZONTAL)
            speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            self.speed_label = ttk.Label(speed_frame, text="1.0x")
            self.speed_label.pack(side=tk.LEFT)

    def _create_system_status(self) -> None:
        status_frame = ttk.LabelFrame(self.frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_labels = {}
        status_items = [
            ("Time", "0.00 s"),
            ("Ignition Events", "0"),
            ("Workspace", "Idle"),
            ("Metabolic Reserves", "100.0%"),
            ("Allostatic Load", "0.0%"),
        ]

        for label, initial in status_items:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{label}:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
            self.status_labels[label] = ttk.Label(frame, text=initial, font=("Arial", 9))
            self.status_labels[label].pack(side=tk.RIGHT)

    def _create_parameter_adjustments(self) -> None:
        param_frame = ttk.LabelFrame(self.frame, text="Quick Parameters", padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        canvas = tk.Canvas(param_frame, height=300)
        scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        param_vars_data = self.callbacks.get("param_vars", {})
        self.param_vars: Dict[str, tk.Variable] = (
            param_vars_data if isinstance(param_vars_data, dict) else {}
        )
        self.param_labels = {}

        parameters = [
            ("Ignition Threshold", "baseline_threshold", 1.0, 5.0, 2.0),
            ("Extero Precision", "extero_precision", 0.1, 10.0, 1.0),
            ("Intero Precision", "intero_precision", 0.1, 10.0, 0.8),
            ("Arousal Level", "arousal", 0.0, 1.0, 0.0),
            ("Stress Level", "stress", 0.0, 1.0, 0.0),
            ("Activity Level", "activity", 0.0, 1.0, 0.0),
            ("Learning Rate", "learning_rate", 0.001, 0.1, 0.01),
            ("Attention Gain", "attention_gain", 0.5, 3.0, 1.0),
        ]

        for label, key, min_val, max_val, default in parameters:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=3)

            ttk.Label(frame, text=label, width=18).pack(side=tk.LEFT)

            var = self.param_vars.get(key)
            if var is None or not isinstance(var, (tk.DoubleVar, tk.IntVar)):
                var = tk.DoubleVar(value=default)
                self.param_vars[key] = var

            scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var)  # type: ignore[arg-type]
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            val_label = ttk.Label(frame, text=f"{var.get():.2f}", width=6)
            val_label.pack(side=tk.LEFT)
            self.param_labels[key] = val_label

            var.trace_add(
                "write", lambda *args, v=var, lbl=val_label: lbl.config(text=f"{v.get():.2f}")
            )

    def _create_event_log(self) -> None:
        log_frame = ttk.LabelFrame(self.frame, text="Event Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=8, width=40, font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def update_status(self, metrics: Dict[str, str]) -> None:
        """Update the system status labels."""
        for label, value in metrics.items():
            if label in self.status_labels:
                self.status_labels[label].config(text=value)

    def log_event(self, message: str) -> None:
        """Add a message to the event log."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
