"""
GUI Core Components

Core GUI components and utilities for the APGI system.
Provides modular components to break down the large monolithic GUI file.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
from typing import Any, Callable, Optional

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


class BaseFrame(ttk.Frame):
    """
    Base frame class with common functionality.
    """

    def __init__(self, parent: tk.Widget, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.setup_ui()
        self.setup_bindings()

    def setup_ui(self) -> None:
        """Setup UI components - override in subclasses."""
        pass

    def setup_bindings(self) -> None:
        """Setup event bindings - override in subclasses."""
        pass

    def show_error(self, title: str, message: str) -> None:
        """Show error message."""
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """Show info message."""
        messagebox.showinfo(title, message)


class ToolTip:
    """Consistent tooltip implementation for tkinter widgets"""

    def __init__(self, widget: tk.Widget, text: str = "") -> None:
        """Initialize tooltip

        Args:
            widget: The widget to attach tooltip to
            text: Tooltip text to display
        """
        self.widget = widget
        self.text = text
        self.tipwindow: Optional[tk.Toplevel] = None
        self.id: Optional[str] = None
        self._delay = 500

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)

    def on_enter(self, event: Optional[tk.Event] = None) -> None:
        """Show tooltip when mouse enters widget"""
        self.schedule()

    def on_leave(self, event: Optional[tk.Event] = None) -> None:
        """Hide tooltip when mouse leaves widget"""
        self.unschedule()
        self.hidetip()

    def schedule(self) -> None:
        """Schedule tooltip display"""
        self.unschedule()
        self.id = self.widget.after(self._delay, self.showtip)

    def unschedule(self) -> None:
        """Cancel scheduled tooltip display"""
        id = self.id
        self.id = None
        if id is not None:
            self.widget.after_cancel(id)

    def showtip(self) -> None:
        """Display the tooltip"""
        if self.tipwindow or not self.text:
            return
        bbox = self.widget.bbox("insert")  # type: ignore
        if bbox is None:
            return
        x, y, _, _ = bbox
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", 8, "normal"),
        )
        label.pack(padx=1, pady=1)

    def hidetip(self) -> None:
        """Hide the tooltip"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw is not None:
            tw.destroy()

    def update_text(self, new_text: str) -> None:
        """Update tooltip text"""
        self.text = new_text


class ControlPanel(BaseFrame):
    """
    Control panel for simulation management.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
    ) -> None:
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_reset = on_reset
        super().__init__(parent)

    def setup_ui(self) -> None:
        """Setup control panel UI."""
        # Title
        title_label = ttk.Label(self, text="Simulation Control", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Control buttons frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=10)

        # Start button
        self.start_button = ttk.Button(
            buttons_frame, text="▶ Start", command=self.on_start_clicked, style="Success.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        # Stop button
        self.stop_button = ttk.Button(
            buttons_frame,
            text="⏸ Stop",
            command=self.on_stop_clicked,
            style="Danger.TButton",
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Reset button
        self.reset_button = ttk.Button(
            buttons_frame, text="↺ Reset", command=self.on_reset_clicked, style="Warning.TButton"
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        # Status indicator
        self.status_label = ttk.Label(buttons_frame, text="● Stopped", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=(20, 0))

    def setup_bindings(self) -> None:
        """Setup keyboard shortcuts."""
        self.bind("<Control-s>", lambda e: self.on_start_clicked())
        self.bind("<Control-t>", lambda e: self.on_stop_clicked())
        self.bind("<Control-r>", lambda e: self.on_reset_clicked())

    def on_start_clicked(self) -> None:
        """Handle start button click."""
        if self.on_start is not None:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="● Running", foreground="green")
            self.on_start()

    def on_stop_clicked(self) -> None:
        """Handle stop button click."""
        if self.on_stop is not None:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="● Stopped", foreground="red")
            self.on_stop()

    def on_reset_clicked(self) -> None:
        """Handle reset button click."""
        if self.on_reset is not None:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="● Stopped", foreground="red")
            self.on_reset()


class ParameterPanel(BaseFrame):
    """
    Panel for configuring simulation parameters.
    """

    def __init__(self, parent: tk.Widget, config: Optional[dict[str, Any]] = None) -> None:
        self.parameter_config: dict[str, Any] = config if config is not None else {}
        self.parameters: dict[str, tk.DoubleVar] = {}
        super().__init__(parent)

    def setup_ui(self) -> None:
        """Setup parameter panel UI."""
        # Title
        title_label = ttk.Label(self, text="Parameters", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Scrollable frame for parameters
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add parameter controls
        self._add_parameter_controls(scrollable_frame)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")

        self.canvas = canvas
        self.scrollable_frame = scrollable_frame

    def _add_parameter_controls(self, parent: tk.Widget) -> None:
        """Add parameter input controls."""
        parameters = [
            ("Timestep (ms)", "timestep_ms", 1.0, 0.1, 100.0),
            ("Learning Rate", "learning_rate", 0.1, 0.0, 1.0),
            ("Precision", "precision", 1.0, 0.01, 100.0),
            ("Threshold", "threshold", 1.0, 0.1, 10.0),
            ("Duration (s)", "duration", 60, 1, 3600),
        ]

        for i, (label, key, default, min_val, max_val) in enumerate(parameters):
            # Parameter frame
            param_frame = ttk.Frame(parent)
            param_frame.pack(fill=tk.X, pady=5, padx=10)

            # Label
            ttk.Label(param_frame, text=label, width=20, anchor=tk.W).pack(side=tk.LEFT)

            # Variable
            var = tk.DoubleVar(value=self.parameter_config.get(key, default))
            self.parameters[key] = var

            # Entry with validation
            entry = ttk.Entry(param_frame, textvariable=var, width=15)
            entry.pack(side=tk.LEFT, padx=(10, 0))

            # Add validation
            entry.bind(
                "<FocusOut>",
                lambda e, k=key, v=var, mn=min_val, mx=max_val: self._validate_parameter(  # type: ignore
                    e, k, v, mn, mx
                ),
            )

    def _validate_parameter(
        self, event: tk.Event, key: str, var: tk.DoubleVar, min_val: float, max_val: float
    ) -> None:
        """Validate parameter value."""
        try:
            value = var.get()
            if value < min_val:
                var.set(min_val)
            elif value > max_val:
                var.set(max_val)
        except Exception:
            pass  # Keep current value if invalid

    def get_parameters(self) -> dict[str, Any]:
        """Get current parameter values."""
        return {key: var.get() for key, var in self.parameters.items()}


class VisualizationPanel(BaseFrame):
    """
    Panel for real-time visualization.
    """

    def __init__(self, parent: tk.Widget) -> None:
        self.figures: dict[str, Any] = {}
        self.canvases: dict[str, Any] = {}
        super().__init__(parent)

    def setup_ui(self) -> None:
        """Setup visualization panel UI."""
        # Title
        title_label = ttk.Label(self, text="Visualization", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # Create notebook for multiple plots
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Add plot tabs
        self._create_ignition_plot()
        self._create_energy_plot()
        self._create_activity_plot()

    def _create_ignition_plot(self) -> None:
        """Create ignition events plot."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ignition Events")

        # Create matplotlib figure
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("Ignition Events Over Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Ignition Strength")
        ax.grid(True, alpha=0.3)

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, frame)  # type: ignore
        canvas.draw()  # type: ignore
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # type: ignore

        self.figures["ignition"] = fig
        self.canvases["ignition"] = canvas

    def _create_energy_plot(self) -> None:
        """Create energy consumption plot."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Energy")

        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("System Energy")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Energy Level")
        ax.grid(True, alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, frame)  # type: ignore
        canvas.draw()  # type: ignore
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # type: ignore

        self.figures["energy"] = fig
        self.canvases["energy"] = canvas

    def _create_activity_plot(self) -> None:
        """Create neural activity plot."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Neural Activity")

        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("Neural Activity")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Activity Level")
        ax.grid(True, alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, frame)  # type: ignore
        canvas.draw()  # type: ignore
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # type: ignore

        self.figures["activity"] = fig
        self.canvases["activity"] = canvas

    def update_plot(self, plot_name: str, x_data: list[float], y_data: list[float]) -> None:
        """Update specific plot with new data."""
        if plot_name in self.figures:
            fig = self.figures[plot_name]
            ax = fig.axes[0]

            ax.clear()
            ax.plot(x_data, y_data, "b-", linewidth=1)
            ax.grid(True, alpha=0.3)

            # Restore labels
            if plot_name == "ignition":
                ax.set_title("Ignition Events Over Time")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Ignition Strength")
            elif plot_name == "energy":
                ax.set_title("System Energy")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Energy Level")
            elif plot_name == "activity":
                ax.set_title("Neural Activity")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Activity Level")

            if plot_name in self.canvases:
                self.canvases[plot_name].draw()


class StatusBar(BaseFrame):
    """
    Status bar for displaying system information.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)

    def setup_ui(self) -> None:
        """Setup status bar UI."""
        self.configure(relief=tk.SUNKEN, borderwidth=1)

        # Status message
        self.status_label = ttk.Label(self, text="Ready", anchor=tk.W, relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=1)

        # Separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Time display
        self.time_label = ttk.Label(self, text="", anchor=tk.E, relief=tk.SUNKEN, width=20)
        self.time_label.pack(side=tk.LEFT, padx=2, pady=1)

        self._update_time()

    def _update_time(self) -> None:
        """Update time display."""
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.after(1000, self._update_time)

    def set_status(self, message: str) -> None:
        """Update status message."""
        self.status_label.config(text=message)


class MenuBar:
    """
    Application menu bar.
    """

    def __init__(
        self,
        parent: tk.Misc,
        on_new: Optional[Callable[[], object]] = None,
        on_open: Optional[Callable[[], object]] = None,
        on_save: Optional[Callable[[], object]] = None,
        on_exit: Optional[Callable[[], object]] = None,
    ) -> None:
        self.parent = parent
        self.on_new = on_new
        self.on_open = on_open
        self.on_save = on_save
        self.on_exit = on_exit
        self.create_menu()

    def create_menu(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.parent)

        # Only configure menu if parent is a Tk instance (root window)
        if isinstance(self.parent, tk.Tk):
            self.parent.configure(menu=menubar)
        else:
            # If parent is not Tk, store it for manual handling
            self.menubar = menubar

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(
            label="New", command=self.on_new or (lambda: None), accelerator="Ctrl+N"
        )
        file_menu.add_command(
            label="Open", command=self.on_open or (lambda: None), accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Save", command=self.on_save or (lambda: None), accelerator="Ctrl+S"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", command=self.on_exit or (lambda: None), accelerator="Ctrl+Q"
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)

        help_menu.add_command(label="About", command=self.show_about)

    def show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About APGI System",
            "APGI Consciousness Modeling Framework\n"
            "Version 1.0.0\n\n"
            "A comprehensive system for modeling consciousness\n"
            "using active inference and precision-gated ignition.",
        )
