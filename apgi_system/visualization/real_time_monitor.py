"""Real-time monitoring dashboard for APGI system."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from collections import deque


class RealTimeMonitor:
    """
    Real-time visualization dashboard for APGI system dynamics.

    Provides live monitoring and visualization of key APGI system metrics
    during simulation. The monitor displays multiple synchronized time series
    to reveal the temporal dynamics of consciousness-related processes.

    **Visualization Panels**:
    - **Ignition Events**: Scatter plot showing when global ignition occurs
    - **Free Energy**: Time series of prediction error magnitude
    - **Precision Dynamics**: Evolution of attention/precision weights
    - **Energy Reserves**: Metabolic budget and depletion status

    **Key Features**:
    - Real-time updating during simulation
    - Configurable time window for display
    - Automatic axis scaling and formatting
    - Event detection and highlighting
    - Export capabilities for analysis

    **Use Cases**:
    - Monitoring system behavior during experiments
    - Debugging parameter settings and dynamics
    - Visualizing consciousness-related phenomena
    - Recording system trajectories for analysis
    - Educational demonstration of APGI principles

    The monitor uses matplotlib for rendering and maintains circular buffers
    for efficient memory usage during long simulations.

    Parameters
    ----------
    window_size : int, optional
        Number of timepoints to display in the visualization window, by default 1000

    Attributes
    ----------
    window_size : int
        Maximum number of timepoints displayed
    time_buffer: deque[float]
        Circular buffer storing timestamps
    ignition_buffer : deque[int]
        Buffer storing ignition event indicators (0/1)
    fe_buffer : deque[float]
        Buffer storing free energy / prediction error values
    precision_buffer : deque[float]
        Buffer storing precision weight values
    energy_buffer : deque[float]
        Buffer storing energy reserve levels
    fig : matplotlib.figure.Figure
        Main figure object
    axes : List[matplotlib.axes.Axes]
        List of subplot axes
    lines : List[matplotlib.lines.Line2D]
        Line plot objects for each metric
    ignition_scatter : matplotlib.collections.PathCollection
        Scatter plot for ignition events

    Examples
    --------
    >>> monitor = RealTimeMonitor(window_size=500)
    >>> # During simulation loop:
    >>> state = apgi_system.step(observation)
    >>> monitor.update(state)
    >>> monitor.render()  # Update display
    >>> # After simulation:
    >>> monitor.save('simulation_results.png')
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize monitor.

        Args:
            window_size: Number of timepoints to display
        """
        self.window_size = window_size

        # Data buffers
        self.time_buffer: deque[float] = deque(maxlen=window_size)
        self.ignition_buffer: deque[int] = deque(maxlen=window_size)
        self.fe_buffer: deque[float] = deque(maxlen=window_size)
        self.precision_buffer: deque[float] = deque(maxlen=window_size)
        self.energy_buffer: deque[float] = deque(maxlen=window_size)

        # Setup figure
        self.fig, self.axes = plt.subplots(4, 1, figsize=(12, 10))
        self.fig.suptitle("APGI System Real-Time Monitor")

        # Configure axes
        self.axes[0].set_ylabel("Ignition")
        self.axes[1].set_ylabel("Free Energy")
        self.axes[2].set_ylabel("Precision")
        self.axes[3].set_ylabel("Energy Reserves")
        self.axes[3].set_xlabel("Time (ms)")

        # Initialize line plots
        self.lines = []
        for ax in self.axes:
            (line,) = ax.plot([], [], "b-")
            self.lines.append(line)

        # Ignition events as scatter
        self.ignition_scatter = self.axes[0].scatter([], [], c="red", s=50, alpha=0.6)

    def update(self, state: Dict[str, Any]) -> None:
        """
        Update monitor buffers with new system state.

        Extracts relevant metrics from the system state and adds them to
        the circular buffers for visualization. The buffers automatically
        maintain the configured window size.

        Parameters
        ----------
        state : Dict[str, Any]
            Current APGI system state dictionary containing:
            - 'time': Current simulation time
            - 'ignition': Dict with 'ignition_occurred' and 'total_signal'
            - 'precision': Dict with 'exteroceptive' precision value
            - 'metabolism': Dict with 'reserves' energy level
        """
        self.time_buffer.append(state["time"])

        # Extract metrics
        ignition = 1 if state["ignition"]["ignition_occurred"] else 0
        self.ignition_buffer.append(ignition)

        # Free energy (might not be directly available, use placeholder)
        self.fe_buffer.append(state["ignition"]["total_signal"])

        self.precision_buffer.append(state["precision"]["exteroceptive"])
        self.energy_buffer.append(state["metabolism"]["reserves"])

    def render(self) -> None:
        """
        Render current visualization state.

        Updates all plot elements with current buffer contents and refreshes
        the display. Automatically scales axes and handles ignition event
        highlighting.

        The rendering process:
        1. Updates ignition scatter plot with event times
        2. Updates line plots for all continuous metrics
        3. Automatically scales axes based on data ranges
        4. Refreshes the display with minimal delay

        This method should be called after each update() to maintain
        real-time visualization.
        """
        if len(self.time_buffer) == 0:
            return

        time_data = np.array(self.time_buffer)

        # Update ignition events
        ignitions = np.array(self.ignition_buffer)
        ignition_times = time_data[ignitions > 0]
        ignition_values = ignitions[ignitions > 0]

        self.ignition_scatter.set_offsets(np.column_stack([ignition_times, ignition_values]))
        self.axes[0].set_xlim(time_data[0], time_data[-1])
        self.axes[0].set_ylim(-0.1, 1.1)

        # Update line plots
        data_buffers = [
            self.ignition_buffer,
            self.fe_buffer,
            self.precision_buffer,
            self.energy_buffer,
        ]

        for i, (line, data) in enumerate(zip(self.lines, data_buffers)):
            data_array = np.array(data)
            line.set_data(time_data, data_array)

            self.axes[i].set_xlim(time_data[0], time_data[-1])

            if len(data_array) > 0:
                data_min, data_max = data_array.min(), data_array.max()
                margin = (data_max - data_min) * 0.1 or 1.0
                self.axes[i].set_ylim(data_min - margin, data_max + margin)

        plt.tight_layout()
        plt.draw()
        plt.pause(0.001)

    def show(self) -> None:
        """Display monitor window."""
        plt.show()

    def save(self, filename: str = "apgi_monitor.png") -> None:
        """
        Save current visualization to file.

        Exports the current state of the monitor to an image file for
        documentation, analysis, or presentation purposes.

        Parameters
        ----------
        filename : str, optional
            Output filename with extension, by default 'apgi_monitor.png'.
            Supported formats: PNG, PDF, SVG, EPS (determined by extension)

        Examples
        --------
        >>> monitor.save('experiment_1_results.png')
        >>> monitor.save('high_res_figure.pdf')
        """
        self.fig.savefig(filename, dpi=150, bbox_inches="tight")
        print(f"Monitor saved to {filename}")
