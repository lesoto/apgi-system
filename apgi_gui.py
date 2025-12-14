"""
APGI System - Comprehensive GUI Application

Full-featured Tkinter GUI for the Allostatic Precision-Gated Ignition System.
Provides complete control and visualization of all subsystems.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import yaml
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import deque
import threading
import time

from apgi_system.system import APGISystem
from apgi_system.platform_utils import (
    get_resource_path, 
    get_data_dir,
    load_resource_with_fallback,
    safe_write_file,
    check_required_libraries
)
import logging

# Configure logging for GUI
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apgi_gui.log'),
        logging.StreamHandler()
    ]
)


class APGIGui:
    """Main GUI application for APGI System."""

    def __init__(self, root):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("APGIConsciousness Modeling Framework")
        self.root.geometry("1720x1200")

        # System state
        self.apgi_system = None
        self.is_running = False
        self.is_paused = False
        self.simulation_thread = None
        self.config_path = get_resource_path("config/default.yaml")

        # Data buffers for plotting
        self.buffer_size = 1000
        self.time_buffer = deque(maxlen=self.buffer_size)
        self.data_buffers = {
            'ignition': deque(maxlen=self.buffer_size),
            'free_energy': deque(maxlen=self.buffer_size),
            'extero_precision': deque(maxlen=self.buffer_size),
            'intero_precision': deque(maxlen=self.buffer_size),
            'metabolic_reserves': deque(maxlen=self.buffer_size),
            'allostatic_load': deque(maxlen=self.buffer_size),
            'heart_rate': deque(maxlen=self.buffer_size),
            'cortisol': deque(maxlen=self.buffer_size),
            'workspace_active': deque(maxlen=self.buffer_size),
            'gamma_power': deque(maxlen=self.buffer_size),
            'beta_power': deque(maxlen=self.buffer_size),
            'somatic_markers': deque(maxlen=self.buffer_size),
            'minimal_self_coherence': deque(maxlen=self.buffer_size),
        }

        # Logging
        self.log_data = []
        self.auto_save = False

        # Build GUI
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # Initialize system
        self._initialize_system()

        # Start update loop
        self._update_displays()

    def _create_menu_bar(self):
        """Create comprehensive menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self._new_session, accelerator="Ctrl+N")
        file_menu.add_command(label="Load Configuration...", command=self._load_config, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Configuration...", command=self._save_config, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export Data...", command=self._export_data, accelerator="Ctrl+E")
        file_menu.add_command(label="Export Plot...", command=self._export_plot)
        file_menu.add_separator()
        file_menu.add_checkbutton(label="Auto-save Data", variable=tk.BooleanVar(value=False),
                                   command=self._toggle_auto_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._exit_app, accelerator="Ctrl+Q")

        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="System Parameters...", command=self._edit_parameters)
        edit_menu.add_command(label="Precision Settings...", command=self._edit_precision)
        edit_menu.add_command(label="Ignition Threshold...", command=self._edit_threshold)
        edit_menu.add_separator()
        edit_menu.add_command(label="Reset to Defaults", command=self._reset_defaults)

        # Simulation Menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        sim_menu.add_command(label="Start", command=self._start_simulation, accelerator="F5")
        sim_menu.add_command(label="Pause/Resume", command=self._pause_simulation, accelerator="F6")
        sim_menu.add_command(label="Stop", command=self._stop_simulation, accelerator="F7")
        sim_menu.add_command(label="Reset", command=self._reset_simulation, accelerator="F8")
        sim_menu.add_separator()
        sim_menu.add_command(label="Run Preset Task...", command=self._run_preset_task)

        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Control Panel", variable=tk.BooleanVar(value=True))
        view_menu.add_checkbutton(label="Neural Activity", variable=tk.BooleanVar(value=True))
        view_menu.add_checkbutton(label="Interoception", variable=tk.BooleanVar(value=True))
        view_menu.add_checkbutton(label="System Metrics", variable=tk.BooleanVar(value=True))
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-")
        view_menu.add_command(label="Fit to Window", accelerator="Ctrl+0")

        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Trigger Ignition Event", command=self._trigger_ignition)
        tools_menu.add_command(label="Induce Stressor", command=self._induce_stressor)
        tools_menu.add_command(label="Modulate Precision...", command=self._modulate_precision)
        tools_menu.add_separator()
        tools_menu.add_command(label="Inject Sensory Input...", command=self._inject_input)
        tools_menu.add_command(label="Set Body State...", command=self._set_body_state)
        tools_menu.add_separator()
        tools_menu.add_command(label="System Diagnostics", command=self._show_diagnostics)

        # Analysis Menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Ignition Statistics", command=self._show_ignition_stats)
        analysis_menu.add_command(label="Energy Budget Report", command=self._show_energy_report)
        analysis_menu.add_command(label="Somatic Marker Analysis", command=self._analyze_markers)
        analysis_menu.add_command(label="Self-Model Coherence", command=self._analyze_coherence)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Generate Report...", command=self._generate_report)

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About APGI System", command=self._show_about)

        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self._new_session())
        self.root.bind('<Control-o>', lambda e: self._load_config())
        self.root.bind('<Control-s>', lambda e: self._save_config())
        self.root.bind('<Control-e>', lambda e: self._export_data())
        self.root.bind('<Control-q>', lambda e: self._exit_app())
        self.root.bind('<F5>', lambda e: self._start_simulation())
        self.root.bind('<F6>', lambda e: self._pause_simulation())
        self.root.bind('<F7>', lambda e: self._stop_simulation())
        self.root.bind('<F8>', lambda e: self._reset_simulation())

    def _create_main_layout(self):
        """Create main application layout."""
        # Create main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Controls
        left_panel = ttk.Frame(main_paned, width=350)
        main_paned.add(left_panel, weight=0)

        # Right panel - Visualizations (tabbed)
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=1)

        # Build left panel
        self._create_control_panel(left_panel)

        # Build right panel with tabs
        self._create_visualization_panel(right_panel)

    def _create_control_panel(self, parent):
        """Create control panel."""
        # Simulation Controls
        control_frame = ttk.LabelFrame(parent, text="Simulation Control", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(btn_frame, text="▶ Start", command=self._start_simulation, width=10)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.pause_btn = ttk.Button(btn_frame, text="⏸ Pause", command=self._pause_simulation, width=10, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop", command=self._stop_simulation, width=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.reset_btn = ttk.Button(btn_frame, text="↻ Reset", command=self._reset_simulation, width=10)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=10.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT)
        self.speed_var.trace_add('write', lambda *args: self.speed_label.config(text=f"{self.speed_var.get():.1f}x"))

        # System Status
        status_frame = ttk.LabelFrame(parent, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_labels = {}
        status_items = [
            ('Time', '0.00 s'),
            ('Ignition Events', '0'),
            ('Workspace', 'Idle'),
            ('Metabolic Reserves', '100.0%'),
            ('Allostatic Load', '0.0%'),
        ]

        for label, initial in status_items:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{label}:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            self.status_labels[label] = ttk.Label(frame, text=initial, font=('Arial', 9))
            self.status_labels[label].pack(side=tk.RIGHT)

        # Parameter Adjustments
        param_frame = ttk.LabelFrame(parent, text="Quick Parameters", padding=10)
        param_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollable parameter list
        canvas = tk.Canvas(param_frame, height=300)
        scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add parameter controls
        self.param_vars = {}
        parameters = [
            ('Ignition Threshold', 'baseline_threshold', 1.0, 5.0, 2.0),
            ('Extero Precision', 'extero_precision', 0.1, 10.0, 1.0),
            ('Intero Precision', 'intero_precision', 0.1, 10.0, 0.8),
            ('Arousal Level', 'arousal', 0.0, 1.0, 0.0),
            ('Stress Level', 'stress', 0.0, 1.0, 0.0),
            ('Activity Level', 'activity', 0.0, 1.0, 0.0),
            ('Learning Rate', 'learning_rate', 0.001, 0.1, 0.01),
            ('Attention Gain', 'attention_gain', 0.5, 3.0, 1.0),
        ]

        for i, (label, key, min_val, max_val, default) in enumerate(parameters):
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=3)

            ttk.Label(frame, text=label, width=18).pack(side=tk.LEFT)

            var = tk.DoubleVar(value=default)
            self.param_vars[key] = var

            scale = ttk.Scale(frame, from_=min_val, to=max_val, variable=var, orient=tk.HORIZONTAL)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            val_label = ttk.Label(frame, text=f"{default:.2f}", width=6)
            val_label.pack(side=tk.LEFT)

            var.trace_add('write', lambda *args, v=var, l=val_label: l.config(text=f"{v.get():.2f}"))

        # Event Log
        log_frame = ttk.LabelFrame(parent, text="Event Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=40, font=('Courier', 8))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self._log_event("APGI System initialized")

    def _create_visualization_panel(self, parent):
        """Create tabbed visualization panel."""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Neural Activity & Ignition
        neural_tab = ttk.Frame(notebook)
        notebook.add(neural_tab, text="Neural Activity")
        self._create_neural_plots(neural_tab)

        # Tab 2: Interoception & Body State
        intero_tab = ttk.Frame(notebook)
        notebook.add(intero_tab, text="Interoception")
        self._create_intero_plots(intero_tab)

        # Tab 3: System Metrics
        metrics_tab = ttk.Frame(notebook)
        notebook.add(metrics_tab, text="System Metrics")
        self._create_metrics_plots(metrics_tab)

        # Tab 4: Self-Model & Coherence
        self_tab = ttk.Frame(notebook)
        notebook.add(self_tab, text="Self-Model")
        self._create_self_plots(self_tab)

        # Tab 5: Oscillations & Spectral
        osc_tab = ttk.Frame(notebook)
        notebook.add(osc_tab, text="Oscillations")
        self._create_osc_plots(osc_tab)

        # Tab 6: 3D State Space (advanced)
        state_tab = ttk.Frame(notebook)
        notebook.add(state_tab, text="State Space")
        self._create_state_space(state_tab)

    def _create_neural_plots(self, parent):
        """Create neural activity visualization."""
        fig = Figure(figsize=(10, 8))

        self.neural_axes = {
            'ignition': fig.add_subplot(4, 1, 1),
            'workspace': fig.add_subplot(4, 1, 2),
            'precision': fig.add_subplot(4, 1, 3),
            'free_energy': fig.add_subplot(4, 1, 4),
        }

        # Configure axes
        self.neural_axes['ignition'].set_ylabel('Ignition Events')
        self.neural_axes['ignition'].set_ylim(-0.1, 1.1)

        self.neural_axes['workspace'].set_ylabel('Workspace Activity')
        self.neural_axes['precision'].set_ylabel('Precision')
        self.neural_axes['free_energy'].set_ylabel('Free Energy')
        self.neural_axes['free_energy'].set_xlabel('Time (s)')

        # Initialize line plots
        self.neural_lines = {}
        self.neural_lines['ignition'] = self.neural_axes['ignition'].scatter([], [], c='red', s=50, alpha=0.6)
        self.neural_lines['workspace'], = self.neural_axes['workspace'].plot([], [], 'b-', linewidth=2)
        self.neural_lines['extero_precision'], = self.neural_axes['precision'].plot([], [], 'g-', label='Extero', linewidth=2)
        self.neural_lines['intero_precision'], = self.neural_axes['precision'].plot([], [], 'r-', label='Intero', linewidth=2)
        self.neural_lines['free_energy'], = self.neural_axes['free_energy'].plot([], [], 'purple', linewidth=2)

        self.neural_axes['precision'].legend(loc='upper right')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.neural_canvas = canvas

    def _create_intero_plots(self, parent):
        """Create interoception visualization."""
        fig = Figure(figsize=(10, 8))

        self.intero_axes = {
            'heart_rate': fig.add_subplot(4, 1, 1),
            'cortisol': fig.add_subplot(4, 1, 2),
            'allostatic_load': fig.add_subplot(4, 1, 3),
            'metabolic': fig.add_subplot(4, 1, 4),
        }

        self.intero_axes['heart_rate'].set_ylabel('Heart Rate (bpm)')
        self.intero_axes['cortisol'].set_ylabel('Cortisol (μg/dL)')
        self.intero_axes['allostatic_load'].set_ylabel('Allostatic Load')
        self.intero_axes['metabolic'].set_ylabel('Metabolic Reserves')
        self.intero_axes['metabolic'].set_xlabel('Time (s)')

        self.intero_lines = {}
        self.intero_lines['heart_rate'], = self.intero_axes['heart_rate'].plot([], [], 'r-', linewidth=2)
        self.intero_lines['cortisol'], = self.intero_axes['cortisol'].plot([], [], 'orange', linewidth=2)
        self.intero_lines['allostatic_load'], = self.intero_axes['allostatic_load'].plot([], [], 'darkred', linewidth=2)
        self.intero_lines['metabolic'], = self.intero_axes['metabolic'].plot([], [], 'green', linewidth=2)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.intero_canvas = canvas

    def _create_metrics_plots(self, parent):
        """Create system metrics visualization."""
        fig = Figure(figsize=(10, 8))

        self.metrics_axes = {
            'somatic': fig.add_subplot(3, 1, 1),
            'gamma': fig.add_subplot(3, 1, 2),
            'beta': fig.add_subplot(3, 1, 3),
        }

        self.metrics_axes['somatic'].set_ylabel('Somatic Markers')
        self.metrics_axes['gamma'].set_ylabel('Gamma Power')
        self.metrics_axes['beta'].set_ylabel('Beta Power')
        self.metrics_axes['beta'].set_xlabel('Time (s)')

        self.metrics_lines = {}
        self.metrics_lines['somatic'], = self.metrics_axes['somatic'].plot([], [], 'purple', linewidth=2)
        self.metrics_lines['gamma'], = self.metrics_axes['gamma'].plot([], [], 'darkgreen', linewidth=2)
        self.metrics_lines['beta'], = self.metrics_axes['beta'].plot([], [], 'blue', linewidth=2)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.metrics_canvas = canvas

    def _create_self_plots(self, parent):
        """Create self-model visualization."""
        fig = Figure(figsize=(10, 8))

        ax = fig.add_subplot(1, 1, 1)
        ax.set_ylabel('Coherence')
        ax.set_xlabel('Time (s)')
        ax.set_ylim(0, 1.1)

        self.coherence_line, = ax.plot([], [], 'b-', linewidth=2, label='Minimal Self')
        ax.axhline(y=0.7, color='g', linestyle='--', label='Normal Threshold')
        ax.axhline(y=0.4, color='r', linestyle='--', label='Depersonalization')
        ax.legend()

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.self_canvas = canvas
        self.self_ax = ax

    def _create_osc_plots(self, parent):
        """Create oscillation visualization."""
        fig = Figure(figsize=(10, 8))

        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)

        ax1.set_ylabel('Oscillation Signal')
        ax1.set_xlabel('Time (s)')
        ax2.set_ylabel('Power')
        ax2.set_xlabel('Frequency Band')

        self.osc_signal_line, = ax1.plot([], [], 'b-', linewidth=1)

        # Bar plot for power spectrum
        self.osc_bars = None
        self.osc_ax1 = ax1
        self.osc_ax2 = ax2

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.osc_canvas = canvas

    def _create_state_space(self, parent):
        """Create 3D state space visualization."""
        from mpl_toolkits.mplot3d import Axes3D

        fig = Figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        ax.set_xlabel('Free Energy')
        ax.set_ylabel('Precision')
        ax.set_zlabel('Allostatic Load')
        ax.set_title('3D State Space Trajectory')

        self.state_scatter = ax.scatter([], [], [], c='b', marker='o', s=20, alpha=0.6)
        self.state_ax = ax

        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, parent)
        toolbar.update()

        self.state_canvas = canvas

    def _create_status_bar(self):
        """Create status bar."""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_text = ttk.Label(status_bar, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.fps_label = ttk.Label(status_bar, text="0 FPS", relief=tk.SUNKEN, width=10)
        self.fps_label.pack(side=tk.RIGHT)

    # System Control Methods

    def _initialize_system(self):
        """Initialize APGI system."""
        try:
            self.apgi_system = APGISystem(config_path=str(self.config_path))
            self._log_event("System initialized successfully")
            self._update_status("System ready")
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize system:\n{str(e)}")
            self._log_event(f"ERROR: {str(e)}")

    def _start_simulation(self):
        """Start simulation."""
        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False

        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

        self._log_event("Simulation started")
        self._update_status("Running simulation...")

        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()

    def _pause_simulation(self):
        """Pause/resume simulation."""
        self.is_paused = not self.is_paused

        if self.is_paused:
            self.pause_btn.config(text="▶ Resume")
            self._log_event("Simulation paused")
            self._update_status("Paused")
        else:
            self.pause_btn.config(text="⏸ Pause")
            self._log_event("Simulation resumed")
            self._update_status("Running simulation...")

    def _stop_simulation(self):
        """Stop simulation."""
        self.is_running = False
        self.is_paused = False

        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏸ Pause")
        self.stop_btn.config(state=tk.DISABLED)

        self._log_event("Simulation stopped")
        self._update_status("Stopped")

    def _reset_simulation(self):
        """Reset simulation."""
        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        if self.apgi_system:
            self.apgi_system.reset()

        # Clear buffers
        for buffer in self.data_buffers.values():
            buffer.clear()
        self.time_buffer.clear()

        self._log_event("System reset")
        self._update_status("System reset")

        # Update displays
        self._update_plots()

    def _simulation_loop(self):
        """Main simulation loop (runs in separate thread)."""
        last_time = time.time()
        frame_count = 0
        fps_update_interval = 1.0

        while self.is_running:
            if not self.is_paused:
                try:
                    # Generate input
                    current_time = self.apgi_system.time / 1000.0  # Convert to seconds
                    extero_input = self._generate_input(current_time)

                    # Apply parameter adjustments
                    self._apply_parameters()

                    # Step simulation
                    state = self.apgi_system.step(extero_input)

                    # Record data
                    self._record_state(state)

                    # Auto-save if enabled
                    if self.auto_save and len(self.log_data) % 1000 == 0:
                        self._auto_save_data()

                    frame_count += 1

                except Exception as e:
                    self._log_event(f"ERROR: {str(e)}")
                    self.is_running = False

            # FPS calculation
            current = time.time()
            if current - last_time >= fps_update_interval:
                fps = frame_count / (current - last_time)
                self.root.after(0, lambda: self.fps_label.config(text=f"{fps:.1f} FPS"))
                frame_count = 0
                last_time = current

            # Control simulation speed
            time.sleep(0.001 / self.speed_var.get())

    def _generate_input(self, t):
        """Generate sensory input."""
        # Sinusoidal with noise
        base = np.sin(2 * np.pi * t / 5.0) * np.ones(256)
        noise = np.random.randn(256) * 0.2
        return base + noise

    def _apply_parameters(self):
        """Apply parameter adjustments to system."""
        if not self.apgi_system:
            return

        try:
            # Apply body state modulations
            self.apgi_system.body_model.set_arousal(self.param_vars['arousal'].get())
            self.apgi_system.body_model.set_stress(self.param_vars['stress'].get())
            self.apgi_system.body_model.set_activity(self.param_vars['activity'].get())

            # Apply precision
            self.apgi_system.precision.extero_baseline = self.param_vars['extero_precision'].get()
            self.apgi_system.precision.intero_baseline = self.param_vars['intero_precision'].get()

            # Apply threshold
            self.apgi_system.ignition_threshold.baseline_threshold = self.param_vars['baseline_threshold'].get()

        except Exception as e:
            pass  # Silently ignore parameter application errors

    def _record_state(self, state):
        """Record state data."""
        current_time = state['time'] / 1000.0  # Convert to seconds

        self.time_buffer.append(current_time)

        # Extract and record metrics
        self.data_buffers['ignition'].append(1 if state['ignition']['ignition_occurred'] else 0)
        self.data_buffers['free_energy'].append(state['ignition']['total_signal'])
        self.data_buffers['extero_precision'].append(state['precision']['exteroceptive'])
        self.data_buffers['intero_precision'].append(state['precision']['interoceptive'])
        self.data_buffers['metabolic_reserves'].append(state['metabolism']['reserves'])
        self.data_buffers['allostatic_load'].append(state['allostasis']['allostatic_load'])
        self.data_buffers['heart_rate'].append(state['body']['current']['heart_rate'])
        self.data_buffers['cortisol'].append(state['body']['current']['cortisol'])
        self.data_buffers['workspace_active'].append(1 if state['workspace']['is_broadcasting'] else 0)
        self.data_buffers['gamma_power'].append(state['oscillations']['band_powers'].get('gamma', 0))
        self.data_buffers['beta_power'].append(state['oscillations']['band_powers'].get('beta', 0))
        self.data_buffers['minimal_self_coherence'].append(state['self_model']['minimal']['coherence'])

        # Count somatic markers
        if hasattr(self.apgi_system.somatic_markers, 'markers'):
            self.data_buffers['somatic_markers'].append(len(self.apgi_system.somatic_markers.markers))
        else:
            self.data_buffers['somatic_markers'].append(0)

        # Log data for export
        self.log_data.append({
            'time': current_time,
            **{k: v[-1] for k, v in self.data_buffers.items()}
        })

    def _update_displays(self):
        """Update all displays (called periodically)."""
        if self.is_running and not self.is_paused:
            self._update_status_labels()
            self._update_plots()

        # Schedule next update
        self.root.after(100, self._update_displays)  # Update every 100ms

    def _update_status_labels(self):
        """Update status labels."""
        if not self.apgi_system:
            return

        try:
            summary = self.apgi_system.get_state_summary()

            self.status_labels['Time'].config(text=f"{summary['time_ms'] / 1000.0:.2f} s")

            stats = summary['ignition_stats']
            self.status_labels['Ignition Events'].config(text=str(stats['recent_ignitions']))

            workspace = 'Broadcasting' if summary['workspace_state'] == 'broadcasting' else 'Idle'
            self.status_labels['Workspace'].config(text=workspace)

            reserves = summary['metabolic_reserves']
            self.status_labels['Metabolic Reserves'].config(text=f"{reserves:.1f}%")

            load = summary['allostatic_load'] * 100
            self.status_labels['Allostatic Load'].config(text=f"{load:.1f}%")

        except Exception as e:
            pass  # Silently ignore update errors

    def _update_plots(self):
        """Update all plot canvases."""
        if len(self.time_buffer) < 2:
            return

        try:
            time_data = np.array(self.time_buffer)

            # Update neural plots
            self._update_neural_plots(time_data)

            # Update interoception plots
            self._update_intero_plots(time_data)

            # Update metrics plots
            self._update_metrics_plots(time_data)

            # Update self-model plot
            self._update_self_plot(time_data)

            # Update oscillation plots
            self._update_osc_plots(time_data)

            # Update 3D state space
            self._update_state_space()

        except Exception as e:
            pass  # Silently ignore plot update errors

    def _update_neural_plots(self, time_data):
        """Update neural activity plots."""
        # Ignition events (scatter plot)
        ignitions = np.array(self.data_buffers['ignition'])
        ignition_times = time_data[ignitions > 0]
        ignition_values = ignitions[ignitions > 0]

        if len(ignition_times) > 0:
            self.neural_lines['ignition'].set_offsets(np.column_stack([ignition_times, ignition_values]))

        # Workspace activity
        workspace = np.array(self.data_buffers['workspace_active'])
        self.neural_lines['workspace'].set_data(time_data, workspace)

        # Precision
        extero_prec = np.array(self.data_buffers['extero_precision'])
        intero_prec = np.array(self.data_buffers['intero_precision'])
        self.neural_lines['extero_precision'].set_data(time_data, extero_prec)
        self.neural_lines['intero_precision'].set_data(time_data, intero_prec)

        # Free energy
        fe = np.array(self.data_buffers['free_energy'])
        self.neural_lines['free_energy'].set_data(time_data, fe)

        # Update axis limits
        for key, ax in self.neural_axes.items():
            if key != 'ignition':
                ax.set_xlim(time_data[0], time_data[-1])
                ax.relim()
                ax.autoscale_view(scalex=False, scaley=True)

        self.neural_axes['ignition'].set_xlim(time_data[0], time_data[-1])

        self.neural_canvas.draw_idle()

    def _update_intero_plots(self, time_data):
        """Update interoception plots."""
        hr = np.array(self.data_buffers['heart_rate'])
        cortisol = np.array(self.data_buffers['cortisol'])
        load = np.array(self.data_buffers['allostatic_load'])
        metabolic = np.array(self.data_buffers['metabolic_reserves'])

        self.intero_lines['heart_rate'].set_data(time_data, hr)
        self.intero_lines['cortisol'].set_data(time_data, cortisol)
        self.intero_lines['allostatic_load'].set_data(time_data, load)
        self.intero_lines['metabolic'].set_data(time_data, metabolic)

        for ax in self.intero_axes.values():
            ax.set_xlim(time_data[0], time_data[-1])
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

        self.intero_canvas.draw_idle()

    def _update_metrics_plots(self, time_data):
        """Update system metrics plots."""
        somatic = np.array(self.data_buffers['somatic_markers'])
        gamma = np.array(self.data_buffers['gamma_power'])
        beta = np.array(self.data_buffers['beta_power'])

        self.metrics_lines['somatic'].set_data(time_data, somatic)
        self.metrics_lines['gamma'].set_data(time_data, gamma)
        self.metrics_lines['beta'].set_data(time_data, beta)

        for ax in self.metrics_axes.values():
            ax.set_xlim(time_data[0], time_data[-1])
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

        self.metrics_canvas.draw_idle()

    def _update_self_plot(self, time_data):
        """Update self-model plot."""
        coherence = np.array(self.data_buffers['minimal_self_coherence'])
        self.coherence_line.set_data(time_data, coherence)

        self.self_ax.set_xlim(time_data[0], time_data[-1])

        self.self_canvas.draw_idle()

    def _update_osc_plots(self, time_data):
        """Update oscillation plots."""
        # For oscillation signal, show recent window
        window_size = min(500, len(time_data))
        recent_time = time_data[-window_size:]

        # Generate sample oscillation (would come from system in full implementation)
        sample_osc = np.sin(2 * np.pi * 20 * recent_time) + 0.5 * np.sin(2 * np.pi * 40 * recent_time)
        self.osc_signal_line.set_data(recent_time, sample_osc)

        self.osc_ax1.set_xlim(recent_time[0], recent_time[-1])
        self.osc_ax1.set_ylim(-2, 2)

        # Power spectrum
        if self.osc_bars is None:
            bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
            powers = [0.5, 0.7, 1.0, 0.8, 0.6]  # Would come from system
            self.osc_bars = self.osc_ax2.bar(bands, powers)
            self.osc_ax2.set_ylim(0, 1.5)
        else:
            # Update bar heights
            gamma_power = self.data_buffers['gamma_power'][-1] if self.data_buffers['gamma_power'] else 0.6
            beta_power = self.data_buffers['beta_power'][-1] if self.data_buffers['beta_power'] else 0.8

            powers = [0.5, 0.7, 1.0, beta_power, gamma_power]
            for bar, power in zip(self.osc_bars, powers):
                bar.set_height(power)

        self.osc_canvas.draw_idle()

    def _update_state_space(self):
        """Update 3D state space plot."""
        if len(self.time_buffer) < 10:
            return

        # Get recent trajectory
        fe = np.array(self.data_buffers['free_energy'])
        prec = np.array(self.data_buffers['extero_precision'])
        load = np.array(self.data_buffers['allostatic_load'])

        # Color by time
        colors = np.linspace(0, 1, len(fe))

        self.state_scatter._offsets3d = (fe, prec, load)

        self.state_ax.set_xlim(fe.min(), fe.max())
        self.state_ax.set_ylim(prec.min(), prec.max())
        self.state_ax.set_zlim(0, 1)

        self.state_canvas.draw_idle()

    # Menu Command Methods

    def _new_session(self):
        """Start new session."""
        if messagebox.askyesno("New Session", "Start a new session? Current data will be lost."):
            self._reset_simulation()
            self.log_data = []
            self._log_event("New session started")

    def _load_config(self):
        """Load configuration file."""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = yaml.safe_load(f)
                self.config_path = Path(filename)
                self._initialize_system()
                self._log_event(f"Configuration loaded: {filename}")
                messagebox.showinfo("Success", "Configuration loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration:\n{str(e)}")

    def _save_config(self):
        """Save configuration file."""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Create config from current parameters
                config = {
                    'parameters': {k: v.get() for k, v in self.param_vars.items()}
                }
                with open(filename, 'w') as f:
                    yaml.dump(config, f)
                self._log_event(f"Configuration saved: {filename}")
                messagebox.showinfo("Success", "Configuration saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")

    def _export_data(self):
        """Export simulation data."""
        if not self.log_data:
            messagebox.showwarning("No Data", "No simulation data to export")
            return

        # Use platform-appropriate data directory as initial directory
        initial_dir = get_data_dir()
        initial_dir.mkdir(parents=True, exist_ok=True)
        
        filename = filedialog.asksaveasfilename(
            title="Export Data",
            initialdir=str(initial_dir),
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(self.log_data, f, indent=2)
                else:
                    # CSV export
                    with open(filename, 'w', newline='') as f:
                        if self.log_data:
                            writer = csv.DictWriter(f, fieldnames=self.log_data[0].keys())
                            writer.writeheader()
                            writer.writerows(self.log_data)

                self._log_event(f"Data exported: {filename}")
                messagebox.showinfo("Success", f"Data exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")

    def _export_plot(self):
        """Export current plot."""
        filename = filedialog.asksaveasfilename(
            title="Export Plot",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.neural_canvas.figure.savefig(filename, dpi=300, bbox_inches='tight')
                self._log_event(f"Plot exported: {filename}")
                messagebox.showinfo("Success", f"Plot saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export plot:\n{str(e)}")

    def _toggle_auto_save(self):
        """Toggle auto-save feature."""
        self.auto_save = not self.auto_save
        status = "enabled" if self.auto_save else "disabled"
        self._log_event(f"Auto-save {status}")

    def _auto_save_data(self):
        """Auto-save data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        filename = data_dir / f"apgi_autosave_{timestamp}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.log_data, f)
        except Exception as e:
            self._log_event(f"Auto-save failed: {str(e)}")

    def _exit_app(self):
        """Exit application."""
        if self.is_running:
            if not messagebox.askyesno("Exit", "Simulation is running. Exit anyway?"):
                return

        self.root.quit()
        self.root.destroy()

    def _edit_parameters(self):
        """Open parameter editor dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit System Parameters")
        dialog.geometry("500x600")

        ttk.Label(dialog, text="System Parameters", font=('Arial', 14, 'bold')).pack(pady=10)

        # Add parameter editors here
        ttk.Label(dialog, text="Advanced parameter editing coming soon...").pack(pady=20)

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

    def _edit_precision(self):
        """Edit precision settings."""
        messagebox.showinfo("Precision Settings", "Use Quick Parameters panel to adjust precision")

    def _edit_threshold(self):
        """Edit ignition threshold."""
        messagebox.showinfo("Threshold Settings", "Use Quick Parameters panel to adjust threshold")

    def _reset_defaults(self):
        """Reset all parameters to defaults."""
        if messagebox.askyesno("Reset", "Reset all parameters to default values?"):
            # Reset parameter sliders
            for key, var in self.param_vars.items():
                # Set to default values (simplified)
                if key == 'baseline_threshold':
                    var.set(2.0)
                elif key in ['extero_precision', 'intero_precision']:
                    var.set(1.0)
                else:
                    var.set(0.0)

            self._log_event("Parameters reset to defaults")

    def _run_preset_task(self):
        """Run preset experimental task."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Run Preset Task")
        dialog.geometry("500x400")

        ttk.Label(dialog, text="Select Preset Task:", font=('Arial', 12, 'bold')).pack(pady=10)

        tasks = [
            "Attentional Blink",
            "Change Blindness",
            "Binocular Rivalry",
            "Iowa Gambling Task",
            "Masking Paradigm"
        ]

        listbox = tk.Listbox(dialog, height=len(tasks))
        for task in tasks:
            listbox.insert(tk.END, task)
        listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Task configuration frame
        config_frame = ttk.LabelFrame(dialog, text="Task Configuration", padding=10)
        config_frame.pack(pady=5, padx=20, fill=tk.BOTH)

        ttk.Label(config_frame, text="Trials per condition:").grid(row=0, column=0, sticky=tk.W)
        trials_var = tk.IntVar(value=20)
        ttk.Spinbox(config_frame, from_=5, to=100, textvariable=trials_var, width=10).grid(row=0, column=1)

        def run_selected():
            selection = listbox.curselection()
            if selection:
                task_name = tasks[selection[0]]

                if task_name == "Attentional Blink":
                    dialog.destroy()
                    self._run_attentional_blink_task(num_trials=trials_var.get())
                elif task_name == "Change Blindness":
                    dialog.destroy()
                    self._run_change_blindness_task(num_trials=trials_var.get())
                elif task_name == "Binocular Rivalry":
                    dialog.destroy()
                    self._run_binocular_rivalry_task(num_trials=trials_var.get())
                elif task_name == "Iowa Gambling Task":
                    dialog.destroy()
                    self._run_iowa_gambling_task(num_trials=trials_var.get())
                elif task_name == "Masking Paradigm":
                    dialog.destroy()
                    self._run_masking_paradigm_task(trials_per_condition=trials_var.get())
                else:
                    self._log_event(f"Task not yet implemented: {task_name}")
                    messagebox.showinfo("Coming Soon",
                                      f"{task_name} implementation coming soon!\n\n"
                                      "Currently available:\n- Attentional Blink\n- Change Blindness\n- Binocular Rivalry\n- Iowa Gambling Task")

        ttk.Button(dialog, text="Run Task", command=run_selected).pack(pady=5)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=5)

    def _run_attentional_blink_task(self, num_trials: int = 20):
        """Run the Attentional Blink experimental task."""
        if not self.apgi_system:
            messagebox.showerror("Error", "System not initialized")
            return

        # Stop current simulation if running
        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        self._log_event("Starting Attentional Blink task...")
        self._update_status("Running Attentional Blink task...")

        # Import and create task
        try:
            from apgi_system.experiments.tasks import AttentionalBlinkTask

            # Create task with specified parameters
            task = AttentionalBlinkTask(
                stream_length=15,
                item_duration_ms=100.0,
                num_trials_per_lag=num_trials,
                lags=[1, 2, 3, 4, 8],
                target_salience=2.0
            )

            # Create progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Running Attentional Blink Task")
            progress_dialog.geometry("400x200")

            ttk.Label(progress_dialog, text="Running trials...",
                     font=('Arial', 12, 'bold')).pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, length=300,
                                          mode='determinate', variable=progress_var)
            progress_bar.pack(pady=10)

            status_label = ttk.Label(progress_dialog, text="Trial 0 of 0")
            status_label.pack(pady=5)

            # Results text area
            results_text = scrolledtext.ScrolledText(progress_dialog, height=6, width=50)
            results_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

            # Run task in separate thread
            def run_task_thread():
                total_trials = len(task.trials)

                for trial_idx, trial in enumerate(task.trials):
                    # Update progress
                    progress = (trial_idx / total_trials) * 100
                    self.root.after(0, lambda p=progress, i=trial_idx, t=total_trials: (
                        progress_var.set(p),
                        status_label.config(text=f"Trial {i+1} of {t}") if status_label.winfo_exists() else None
                    ))

                    # Run trial
                    result = task.run_trial(self.apgi_system, trial)

                    # Log result
                    if trial_idx % 10 == 0:
                        msg = f"Trial {trial_idx}: Lag {result.lag}, T1: {result.t1_detected}, T2: {result.t2_detected}\n"
                        self.root.after(0, lambda m=msg: results_text.insert(tk.END, m))
                        self.root.after(0, lambda: results_text.see(tk.END))

                # Task complete
                self.root.after(0, lambda: progress_var.set(100))
                self.root.after(0, lambda: status_label.config(text="Analysis complete!"))

                # Analyze results
                analysis = task.analyze_results()

                # Display summary
                summary = f"\n{'='*50}\nRESULTS:\n{'='*50}\n"
                summary += f"Total Trials: {analysis['total_trials']}\n"
                summary += f"Overall T1 Accuracy: {analysis['overall_t1_accuracy']:.1%}\n"
                summary += f"Overall T2 Accuracy: {analysis['overall_t2_accuracy']:.1%}\n"
                summary += f"Overall Blink Rate: {analysis['overall_blink_rate']:.1%}\n"
                summary += f"Peak Blink at Lag {analysis['max_blink_lag']}: {analysis['max_blink_rate']:.1%}\n\n"

                summary += "By Lag:\n"
                for lag in sorted(analysis['lag_analysis'].keys()):
                    lag_data = analysis['lag_analysis'][lag]
                    summary += f"  Lag {lag}: T2|T1={lag_data['t2_given_t1_accuracy']:.1%}, Blink={lag_data['blink_rate']:.1%}\n"

                self.root.after(0, lambda s=summary: results_text.insert(tk.END, s))
                self.root.after(0, lambda: results_text.see(tk.END))

                # Save results
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"attentional_blink_results_{timestamp}.json"
                task.save_results(filename)

                self.root.after(0, lambda: self._log_event(f"Task complete. Results saved to {filename}"))

                # Add close button
                def close_and_show_results():
                    progress_dialog.destroy()
                    task.print_results(analysis)
                    messagebox.showinfo("Task Complete",
                                      f"Attentional Blink task completed!\n\n"
                                      f"T1 Accuracy: {analysis['overall_t1_accuracy']:.1%}\n"
                                      f"T2 Accuracy: {analysis['overall_t2_accuracy']:.1%}\n"
                                      f"Blink Rate: {analysis['overall_blink_rate']:.1%}\n\n"
                                      f"Results saved to:\n{filename}")

                self.root.after(0, lambda: ttk.Button(progress_dialog, text="Close",
                                                      command=close_and_show_results).pack(pady=5))

            # Start task thread
            import threading
            task_thread = threading.Thread(target=run_task_thread, daemon=True)
            task_thread.start()

        except Exception as e:
            self._log_event(f"ERROR running task: {str(e)}")
            messagebox.showerror("Task Error", f"Failed to run task:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _run_change_blindness_task(self, num_trials: int = 10):
        """Run the Change Blindness experimental task."""
        if not self.apgi_system:
            messagebox.showerror("Error", "System not initialized")
            return

        # Stop current simulation if running
        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        self._log_event("Starting Change Blindness task...")
        self._update_status("Running Change Blindness task...")

        # Import and create task
        try:
            from apgi_system.experiments.tasks import ChangeBlindnessTask

            # Create task with specified parameters
            task = ChangeBlindnessTask(
                presentation_duration_ms=240.0,
                blank_duration_ms=80.0,
                max_alternations=20,
                num_trials_per_condition=num_trials,
                change_magnitudes=[0.3, 0.5, 0.8]
            )

            # Create progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Running Change Blindness Task")
            progress_dialog.geometry("400x200")

            ttk.Label(progress_dialog, text="Running trials...",
                     font=('Arial', 12, 'bold')).pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, length=300,
                                          mode='determinate', variable=progress_var)
            progress_bar.pack(pady=10)

            status_label = ttk.Label(progress_dialog, text="Trial 0 of 0")
            status_label.pack(pady=5)

            # Results text area
            results_text = scrolledtext.ScrolledText(progress_dialog, height=6, width=50)
            results_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

            # Run task in separate thread
            def run_task_thread():
                total_trials = len(task.trials)

                for trial_idx, trial in enumerate(task.trials):
                    # Update progress
                    progress = (trial_idx / total_trials) * 100
                    self.root.after(0, lambda p=progress, i=trial_idx, t=total_trials: (
                        progress_var.set(p),
                        status_label.config(text=f"Trial {i+1} of {t}") if status_label.winfo_exists() else None
                    ))

                    # Run trial
                    result = task.run_trial(self.apgi_system, trial)

                    # Log result
                    if trial_idx % 10 == 0:
                        detected_str = "Yes" if result.change_detected else "No"
                        msg = f"Trial {trial_idx}: {result.change_type.value}, Detected: {detected_str}\n"
                        self.root.after(0, lambda m=msg: results_text.insert(tk.END, m))
                        self.root.after(0, lambda: results_text.see(tk.END))

                # Task complete
                self.root.after(0, lambda: progress_var.set(100))
                self.root.after(0, lambda: status_label.config(text="Analysis complete!"))

                # Analyze results
                analysis = task.analyze_results()

                # Display summary
                summary = f"\n{'='*50}\nRESULTS:\n{'='*50}\n"
                summary += f"Total Trials: {analysis['total_trials']}\n"
                summary += f"Detection Rate: {analysis['overall_detection_rate']:.1%}\n"
                summary += f"Blindness Rate: {analysis['overall_blindness_rate']:.1%}\n"
                summary += f"Avg Alternations: {analysis['overall_avg_alternations']:.1f}\n"
                summary += f"Avg Time to Detection: {analysis['overall_avg_time_ms']:.0f} ms\n\n"

                summary += "By Change Type:\n"
                for change_type, data in analysis['by_change_type'].items():
                    summary += f"  {change_type}: {data['detection_rate']:.1%}\n"

                summary += "\nBy Magnitude:\n"
                for magnitude in sorted(analysis['by_magnitude'].keys()):
                    data = analysis['by_magnitude'][magnitude]
                    summary += f"  {magnitude:.1f}: {data['detection_rate']:.1%}\n"

                self.root.after(0, lambda s=summary: results_text.insert(tk.END, s))
                self.root.after(0, lambda: results_text.see(tk.END))

                # Save results
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"change_blindness_results_{timestamp}.json"
                task.save_results(filename)

                self.root.after(0, lambda: self._log_event(f"Task complete. Results saved to {filename}"))

                # Add close button
                def close_and_show_results():
                    progress_dialog.destroy()
                    task.print_results(analysis)
                    messagebox.showinfo("Task Complete",
                                      f"Change Blindness task completed!\n\n"
                                      f"Detection Rate: {analysis['overall_detection_rate']:.1%}\n"
                                      f"Blindness Rate: {analysis['overall_blindness_rate']:.1%}\n"
                                      f"Avg Alternations: {analysis['overall_avg_alternations']:.1f}\n\n"
                                      f"Results saved to:\n{filename}")

                self.root.after(0, lambda: ttk.Button(progress_dialog, text="Close",
                                                      command=close_and_show_results).pack(pady=5))

            # Start task thread
            import threading
            task_thread = threading.Thread(target=run_task_thread, daemon=True)
            task_thread.start()

        except Exception as e:
            self._log_event(f"ERROR running task: {str(e)}")
            messagebox.showerror("Task Error", f"Failed to run task:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _run_binocular_rivalry_task(self, num_trials: int = 10):
        """Run the Binocular Rivalry experimental task."""
        if not self.apgi_system:
            messagebox.showerror("Error", "System not initialized")
            return

        # Stop current simulation if running
        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        self._log_event("Starting Binocular Rivalry task...")
        self._update_status("Running Binocular Rivalry task...")

        # Import and create task
        try:
            from apgi_system.experiments.tasks import BinocularRivalryTask

            # Create task with specified parameters
            task = BinocularRivalryTask(
                trial_duration_ms=30000.0,  # 30 seconds per trial
                num_trials=num_trials,
                strength_ratios=[(1.0, 1.0), (1.0, 0.8), (1.2, 1.0)],
                sampling_interval_ms=100.0
            )

            # Create progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Running Binocular Rivalry Task")
            progress_dialog.geometry("400x200")

            ttk.Label(progress_dialog, text="Running trials...",
                     font=('Arial', 12, 'bold')).pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, length=300,
                                          mode='determinate', variable=progress_var)
            progress_bar.pack(pady=10)

            status_label = ttk.Label(progress_dialog, text="Trial 0 of 0")
            status_label.pack(pady=5)

            # Results text area
            results_text = scrolledtext.ScrolledText(progress_dialog, height=6, width=50)
            results_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

            # Run task in separate thread
            def run_task_thread():
                total_trials = len(task.trials)

                for trial_idx, trial in enumerate(task.trials):
                    # Update progress
                    progress = (trial_idx / total_trials) * 100
                    self.root.after(0, lambda p=progress, i=trial_idx, t=total_trials: (
                        progress_var.set(p),
                        status_label.config(text=f"Trial {i+1} of {t}") if status_label.winfo_exists() else None
                    ))

                    # Run trial
                    result = task.run_trial(self.apgi_system, trial)

                    # Log result
                    if trial_idx % 5 == 0:
                        msg = (f"Trial {trial_idx}: {result.num_alternations} alternations, "
                               f"Pattern A dominance: {result.pattern_a_dominance_ratio:.1%}\n")
                        self.root.after(0, lambda m=msg: results_text.insert(tk.END, m))
                        self.root.after(0, lambda: results_text.see(tk.END))

                # Task complete
                self.root.after(0, lambda: progress_var.set(100))
                self.root.after(0, lambda: status_label.config(text="Analysis complete!"))

                # Analyze results
                analysis = task.analyze_results()

                # Display summary
                summary = f"\n{'='*50}\nRESULTS:\n{'='*50}\n"
                summary += f"Total Trials: {analysis['total_trials']}\n"
                summary += f"Avg Dominance Duration: {analysis['avg_dominance_duration_ms']:.0f} ms\n"
                summary += f"Avg Alternation Rate: {analysis['avg_alternation_rate']:.2f} per second\n"
                summary += f"Pattern A Dominance: {analysis['avg_pattern_a_dominance_ratio']:.1%}\n"
                summary += f"Total Alternations: {analysis['total_alternations']}\n\n"

                summary += "By Strength Ratio:\n"
                for ratio_key in sorted(analysis['by_strength_ratio'].keys()):
                    data = analysis['by_strength_ratio'][ratio_key]
                    summary += (f"  {ratio_key}: Dom={data['avg_dominance_duration_ms']:.0f}ms, "
                               f"Alt={data['avg_alternation_rate']:.2f}/s\n")

                self.root.after(0, lambda s=summary: results_text.insert(tk.END, s))
                self.root.after(0, lambda: results_text.see(tk.END))

                # Save results
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"binocular_rivalry_results_{timestamp}.json"
                task.save_results(filename)

                self.root.after(0, lambda: self._log_event(f"Task complete. Results saved to {filename}"))

                # Add close button
                def close_and_show_results():
                    progress_dialog.destroy()
                    task.print_results(analysis)
                    messagebox.showinfo("Task Complete",
                                      f"Binocular Rivalry task completed!\n\n"
                                      f"Avg Dominance Duration: {analysis['avg_dominance_duration_ms']:.0f} ms\n"
                                      f"Alternation Rate: {analysis['avg_alternation_rate']:.2f} per second\n"
                                      f"Total Alternations: {analysis['total_alternations']}\n\n"
                                      f"Results saved to:\n{filename}")

                self.root.after(0, lambda: ttk.Button(progress_dialog, text="Close",
                                                      command=close_and_show_results).pack(pady=5))

            # Start task thread
            import threading
            task_thread = threading.Thread(target=run_task_thread, daemon=True)
            task_thread.start()

        except Exception as e:
            self._log_event(f"ERROR running task: {str(e)}")
            messagebox.showerror("Task Error", f"Failed to run task:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _run_masking_paradigm_task(self, trials_per_condition: int = 20):
        """Run the Masking Paradigm experimental task."""
        if not self.apgi_system:
            messagebox.showerror("Error", "System not initialized")
            return

        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        self._log_event("Starting Masking Paradigm task...")
        self._update_status("Running Masking Paradigm task...")

        try:
            from apgi_system.experiments.tasks import MaskingParadigmTask

            task = MaskingParadigmTask(num_trials_per_condition=trials_per_condition)

            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Running Masking Paradigm Task")
            progress_dialog.geometry("420x240")

            ttk.Label(progress_dialog, text="Running trials...",
                     font=('Arial', 12, 'bold')).pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, length=320,
                                           mode='determinate', variable=progress_var)
            progress_bar.pack(pady=10)

            status_label = ttk.Label(progress_dialog, text="Trial 0 of 0")
            status_label.pack(pady=5)

            results_text = scrolledtext.ScrolledText(progress_dialog, height=6, width=60)
            results_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

            def run_task_thread():
                total_trials = len(task.trials)

                for trial_idx, trial in enumerate(task.trials):
                    progress = (trial_idx / total_trials) * 100 if total_trials else 0
                    self.root.after(0, lambda p=progress, i=trial_idx, t=total_trials: (
                        progress_var.set(p),
                        status_label.config(text=f"Trial {i+1} of {t}") if status_label.winfo_exists() else None
                    ))

                    result = task.run_trial(self.apgi_system, trial)

                    if trial_idx % 10 == 0:
                        detected = "Yes" if result.target_detected else "No"
                        msg = (f"Trial {trial_idx}: SOA {result.soa_ms}ms, Detected: {detected}, "
                               f"Ignitions: {result.ignition_count}\n")
                        self.root.after(0, lambda m=msg: results_text.insert(tk.END, m))
                        self.root.after(0, lambda: results_text.see(tk.END))

                self.root.after(0, lambda: progress_var.set(100))
                self.root.after(0, lambda: status_label.config(text="Analysis complete!"))

                analysis = task.analyze_results()

                summary = f"\n{'='*50}\nRESULTS:\n{'='*50}\n"
                summary += f"Total Trials: {analysis['total_trials']}\n"
                summary += f"Overall Detection Rate: {analysis['overall_detection_rate']:.1%}\n"
                summary += f"Overall Suppression Rate: {analysis['overall_suppression_rate']:.1%}\n"
                summary += f"Masking Effect: {analysis['masking_effect']:.1%}\n\n"
                summary += "By SOA:\n"
                for soa in sorted(analysis['by_soa'].keys()):
                    data = analysis['by_soa'][soa]
                    summary += (f"  {soa:.0f}ms: Det={data['detection_rate']:.1%}, "
                                f"Supp={data['suppression_rate']:.1%}, "
                                f"Avg Strength={data['avg_ignition_strength']:.2f}\n")

                self.root.after(0, lambda s=summary: results_text.insert(tk.END, s))
                self.root.after(0, lambda: results_text.see(tk.END))

                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"masking_paradigm_results_{timestamp}.json"
                task.save_results(filename)

                self.root.after(0, lambda: self._log_event(f"Task complete. Results saved to {filename}"))

                def close_and_show_results():
                    progress_dialog.destroy()
                    task.print_results(analysis)
                    messagebox.showinfo("Task Complete",
                                        f"Masking Paradigm task completed!\n\n"
                                        f"Detection Rate: {analysis['overall_detection_rate']:.1%}\n"
                                        f"Suppression Rate: {analysis['overall_suppression_rate']:.1%}\n\n"
                                        f"Results saved to:\n{filename}")

                self.root.after(0, lambda: ttk.Button(progress_dialog, text="Close",
                                                      command=close_and_show_results).pack(pady=5))

            threading.Thread(target=run_task_thread, daemon=True).start()

        except Exception as e:
            self._log_event(f"ERROR running task: {str(e)}")
            messagebox.showerror("Task Error", f"Failed to run task:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _run_iowa_gambling_task(self, num_trials: int = 100):
        """Run the Iowa Gambling Task experimental task."""
        if not self.apgi_system:
            messagebox.showerror("Error", "System not initialized")
            return

        # Stop current simulation if running
        was_running = self.is_running
        if was_running:
            self._stop_simulation()

        self._log_event("Starting Iowa Gambling Task...")
        self._update_status("Running Iowa Gambling Task...")

        # Import and create task
        try:
            from apgi_system.experiments.tasks import IowaGamblingTask

            # Create task with specified parameters
            task = IowaGamblingTask(
                num_trials=num_trials,
                initial_balance=2000,
                deck_stimulus_strength=1.5,
                outcome_stimulus_strength=2.0,
                interoceptive_gain=1.0,
                deck_selection_strategy='balanced'
            )

            # Create progress dialog
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Running Iowa Gambling Task")
            progress_dialog.geometry("500x250")

            ttk.Label(progress_dialog, text="Running trials...",
                     font=('Arial', 12, 'bold')).pack(pady=10)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, length=400,
                                          mode='determinate', variable=progress_var)
            progress_bar.pack(pady=10)

            status_label = ttk.Label(progress_dialog, text="Trial 0 of 0")
            status_label.pack(pady=5)

            # Results text area
            results_text = scrolledtext.ScrolledText(progress_dialog, height=8, width=60)
            results_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

            # Run task in separate thread
            def run_task_thread():
                total_trials = len(task.trials)

                for trial_idx, trial in enumerate(task.trials):
                    # Update progress
                    progress = (trial_idx / total_trials) * 100
                    self.root.after(0, lambda p=progress, i=trial_idx, t=total_trials: (
                        progress_var.set(p),
                        status_label.config(text=f"Trial {i+1} of {t}") if status_label.winfo_exists() else None
                    ))

                    # Run trial
                    result = task.run_trial(self.apgi_system, trial)

                    # Log result
                    if trial_idx % 10 == 0:
                        deck = result.deck_choice.value
                        net = result.net_outcome
                        balance = result.running_total
                        msg = f"Trial {trial_idx}: Deck {deck}, Net: ${net:+d}, Balance: ${balance}\n"
                        self.root.after(0, lambda m=msg: results_text.insert(tk.END, m))
                        self.root.after(0, lambda: results_text.see(tk.END))

                # Task complete
                self.root.after(0, lambda: progress_var.set(100))
                self.root.after(0, lambda: status_label.config(text="Analysis complete!"))

                # Analyze results
                analysis = task.analyze_results()

                # Display summary
                summary = f"\n{'='*50}\nRESULTS:\n{'='*50}\n"
                summary += f"Total Trials: {analysis['total_trials']}\n"
                summary += f"Final Balance: ${analysis['final_balance']}\n"
                summary += f"Total Earnings: ${analysis['total_earnings']}\n"
                summary += f"Good Deck Choices: {analysis['good_deck_choices']} ({analysis['advantageous_ratio']:.1%})\n"
                summary += f"Bad Deck Choices: {analysis['bad_deck_choices']}\n"
                summary += f"Net Score: {analysis['net_score']}\n\n"

                summary += "Deck Selections:\n"
                for deck in ['A', 'B', 'C', 'D']:
                    deck_data = analysis['by_deck'][deck]
                    deck_type = 'Bad' if deck in ['A', 'B'] else 'Good'
                    summary += f"  Deck {deck} ({deck_type}): {deck_data['selections']} ({deck_data['selection_percentage']:.1f}%)\n"

                self.root.after(0, lambda s=summary: results_text.insert(tk.END, s))
                self.root.after(0, lambda: results_text.see(tk.END))

                # Save results
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"iowa_gambling_results_{timestamp}.json"
                task.save_results(filename)

                self.root.after(0, lambda: self._log_event(f"Task complete. Results saved to {filename}"))

                # Add close button
                def close_and_show_results():
                    progress_dialog.destroy()
                    task.print_results(analysis)
                    messagebox.showinfo("Task Complete",
                                      f"Iowa Gambling Task completed!\n\n"
                                      f"Total Earnings: ${analysis['total_earnings']}\n"
                                      f"Good Deck Choices: {analysis['advantageous_ratio']:.1%}\n"
                                      f"Net Score: {analysis['net_score']}\n\n"
                                      f"Results saved to:\n{filename}")

                self.root.after(0, lambda: ttk.Button(progress_dialog, text="Close",
                                                      command=close_and_show_results).pack(pady=5))

            import threading
            task_thread = threading.Thread(target=run_task_thread, daemon=True)
            task_thread.start()

        except Exception as e:
            self._log_event(f"ERROR running task: {str(e)}")
            messagebox.showerror("Task Error", f"Failed to run task:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _trigger_ignition(self):
        """Manually trigger ignition event."""
        if self.apgi_system:
            # Force high arousal to trigger ignition
            self.param_vars['arousal'].set(0.9)
            self.param_vars['stress'].set(0.8)
            self._log_event("Manual ignition trigger activated")

    def _induce_stressor(self):
        """Induce stressor event."""
        if self.apgi_system:
            self.apgi_system.allostasis.trigger_stressor(intensity=0.5)
            self._log_event("Stressor induced (intensity: 0.5)")

    def _modulate_precision(self):
        """Open precision modulation dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Modulate Precision")
        dialog.geometry("400x200")

        ttk.Label(dialog, text="Precision Modulation", font=('Arial', 12, 'bold')).pack(pady=10)

        frame = ttk.Frame(dialog)
        frame.pack(pady=10)

        ttk.Label(frame, text="Modulation Factor:").pack()
        factor_var = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.1, to=3.0, variable=factor_var, orient=tk.HORIZONTAL).pack()

        def apply():
            factor = factor_var.get()
            self.param_vars['extero_precision'].set(self.param_vars['extero_precision'].get() * factor)
            self.param_vars['intero_precision'].set(self.param_vars['intero_precision'].get() * factor)
            self._log_event(f"Precision modulated by factor: {factor:.2f}")
            dialog.destroy()

        ttk.Button(dialog, text="Apply", command=apply).pack(pady=10)

    def _inject_input(self):
        """Inject custom sensory input."""
        messagebox.showinfo("Input Injection", "Custom input injection feature coming soon...")

    def _set_body_state(self):
        """Set body state manually."""
        messagebox.showinfo("Body State", "Use Activity, Arousal, and Stress sliders in control panel")

    def _show_diagnostics(self):
        """Show system diagnostics."""
        if not self.apgi_system:
            messagebox.showwarning("No System", "System not initialized")
            return

        summary = self.apgi_system.get_state_summary()

        diag_text = f"""APGI System Diagnostics

Time: {summary['time_ms'] / 1000.0:.2f} seconds

Ignition Statistics:
- Recent Events: {summary['ignition_stats']['recent_ignitions']}
- Mean Signal: {summary['ignition_stats'].get('mean_signal', 0):.3f}
- Mean Threshold: {summary['ignition_stats'].get('mean_threshold', 0):.3f}

Workspace State: {summary['workspace_state']}

Metabolic State:
- Reserves: {summary['metabolic_reserves']:.1f}
- Allostatic Load: {summary['allostatic_load'] * 100:.1f}%

Somatic Markers:
- Count: {summary['somatic_markers']['num_markers']}
- Retrieval Success Rate: {summary['somatic_markers'].get('retrieval_success_rate', 0) * 100:.1f}%
"""

        messagebox.showinfo("System Diagnostics", diag_text)

    def _show_ignition_stats(self):
        """Show detailed ignition statistics."""
        if not self.apgi_system:
            return

        stats = self.apgi_system.ignition_threshold.get_statistics()

        text = f"""Ignition Statistics

Mean Signal: {stats['mean_signal']:.3f}
Std Signal: {stats.get('std_signal', 0):.3f}
Mean Threshold: {stats['mean_threshold']:.3f}
Std Threshold: {stats.get('std_threshold', 0):.3f}

Recent Ignitions: {stats['recent_ignitions']}
Ignition Rate: {stats['ignition_rate']:.3f}
Current Probability: {stats['current_probability']:.3f}
"""

        messagebox.showinfo("Ignition Statistics", text)

    def _show_energy_report(self):
        """Show energy budget report."""
        if not self.apgi_system:
            return

        text = f"""Energy Budget Report

Current Reserves: {self.apgi_system.metabolism.current_reserves:.1f}
Total Consumed: {self.apgi_system.metabolism.total_consumed:.1f}

Baseline Rate: {self.apgi_system.metabolism.baseline_rate:.1f}/s
Ignition Cost: {self.apgi_system.metabolism.ignition_cost:.1f} per event

Reserve Fraction: {self.apgi_system.metabolism.current_reserves / self.apgi_system.metabolism.total_budget * 100:.1f}%
"""

        messagebox.showinfo("Energy Budget", text)

    def _analyze_markers(self):
        """Analyze somatic markers."""
        if not self.apgi_system:
            return

        stats = self.apgi_system.somatic_markers.get_statistics()

        text = f"""Somatic Marker Analysis

Total Markers: {stats['num_markers']}
Capacity Used: {stats.get('capacity_used', 0) * 100:.1f}%

Total Retrievals: {stats.get('total_retrievals', 0)}
Successful Retrievals: {stats.get('successful_retrievals', 0)}
Success Rate: {stats.get('retrieval_success_rate', 0) * 100:.1f}%

Average Strength: {stats.get('avg_strength', 0):.3f}
Average Outcome: {stats.get('avg_outcome', 0):.3f}
"""

        messagebox.showinfo("Somatic Marker Analysis", text)

    def _analyze_coherence(self):
        """Analyze self-model coherence."""
        messagebox.showinfo("Self-Model Coherence", "Check the Self-Model tab for coherence visualization")

    def _generate_report(self):
        """Generate comprehensive report."""
        filename = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("APGI System Comprehensive Report\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    if self.apgi_system:
                        summary = self.apgi_system.get_state_summary()
                        f.write(f"Simulation Time: {summary['time_ms'] / 1000.0:.2f} seconds\n")
                        f.write(f"Ignition Events: {summary['ignition_stats']['recent_ignitions']}\n")
                        f.write(f"Metabolic Reserves: {summary['metabolic_reserves']:.1f}\n")
                        f.write(f"Allostatic Load: {summary['allostatic_load'] * 100:.1f}%\n")

                    f.write("\n" + "=" * 50 + "\n")
                    f.write("Event Log:\n")
                    f.write(self.log_text.get(1.0, tk.END))

                self._log_event(f"Report saved: {filename}")
                messagebox.showinfo("Success", f"Report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report:\n{str(e)}")

    def _show_docs(self):
        """Show documentation."""
        doc_text = """APGI System Documentation

The Allostatic Precision-Gated Ignition (APGI) framework is a computational
model of consciousness integrating:

- Active Inference
- Predictive Processing
- Allostatic Regulation
- Global Workspace Theory
- Somatic Marker Hypothesis

Key Features:
- Multi-scale neural dynamics
- Precision-weighted prediction errors
- Dynamic ignition thresholds
- Metabolic constraints
- Self-model maintenance

For detailed documentation, see README.md in the project directory.
"""

        dialog = tk.Toplevel(self.root)
        dialog.title("Documentation")
        dialog.geometry("600x400")

        text_widget = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, doc_text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)

    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        shortcuts = """Keyboard Shortcuts

Ctrl+N  - New Session
Ctrl+O  - Load Configuration
Ctrl+S  - Save Configuration
Ctrl+E  - Export Data
Ctrl+Q  - Exit

F5      - Start Simulation
F6      - Pause/Resume
F7      - Stop Simulation
F8      - Reset System
"""

        messagebox.showinfo("Keyboard Shortcuts", shortcuts)

    def _show_about(self):
        """Show about dialog."""
        about_text = """APGI System v0.1.0

Allostatic Precision-Gated Ignition Framework

A computational model of consciousness based on:
- Active Inference (Free Energy Principle)
- Predictive Processing
- Global Workspace Theory
- Allostatic Regulation
- Somatic Markers

Developed using Python, NumPy, Matplotlib, and Tkinter

For more information, visit the project repository.
"""

        messagebox.showinfo("About APGI System", about_text)

    # Helper Methods

    def _log_event(self, message):
        """Log event to event log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)

    def _update_status(self, message):
        """Update status bar message."""
        self.status_text.config(text=message)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = APGIGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
