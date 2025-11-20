"""Real-time monitoring dashboard for APGI system."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from typing import Dict, Any, List
from collections import deque


class RealTimeMonitor:
    """
    Real-time visualization of APGI system state.

    Displays:
    - Ignition events
    - Prediction errors
    - Precision dynamics
    - Energy budget
    - Oscillations
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize monitor.

        Args:
            window_size: Number of timepoints to display
        """
        self.window_size = window_size

        # Data buffers
        self.time_buffer = deque(maxlen=window_size)
        self.ignition_buffer = deque(maxlen=window_size)
        self.fe_buffer = deque(maxlen=window_size)
        self.precision_buffer = deque(maxlen=window_size)
        self.energy_buffer = deque(maxlen=window_size)

        # Setup figure
        self.fig, self.axes = plt.subplots(4, 1, figsize=(12, 10))
        self.fig.suptitle('APGI System Real-Time Monitor')

        # Configure axes
        self.axes[0].set_ylabel('Ignition')
        self.axes[1].set_ylabel('Free Energy')
        self.axes[2].set_ylabel('Precision')
        self.axes[3].set_ylabel('Energy Reserves')
        self.axes[3].set_xlabel('Time (ms)')

        # Initialize line plots
        self.lines = []
        for ax in self.axes:
            line, = ax.plot([], [], 'b-')
            self.lines.append(line)

        # Ignition events as scatter
        self.ignition_scatter = self.axes[0].scatter([], [], c='red', s=50, alpha=0.6)

    def update(self, state: Dict[str, Any]):
        """
        Update monitor with new state.

        Args:
            state: Current system state
        """
        self.time_buffer.append(state['time'])

        # Extract metrics
        ignition = 1 if state['ignition']['ignition_occurred'] else 0
        self.ignition_buffer.append(ignition)

        # Free energy (might not be directly available, use placeholder)
        self.fe_buffer.append(state['ignition']['total_signal'])

        self.precision_buffer.append(state['precision']['exteroceptive'])
        self.energy_buffer.append(state['metabolism']['reserves'])

    def render(self):
        """Render current state."""
        if len(self.time_buffer) == 0:
            return

        time_data = np.array(self.time_buffer)

        # Update ignition events
        ignitions = np.array(self.ignition_buffer)
        ignition_times = time_data[ignitions > 0]
        ignition_values = ignitions[ignitions > 0]

        self.ignition_scatter.set_offsets(
            np.column_stack([ignition_times, ignition_values])
        )
        self.axes[0].set_xlim(time_data[0], time_data[-1])
        self.axes[0].set_ylim(-0.1, 1.1)

        # Update line plots
        data_buffers = [
            self.ignition_buffer,
            self.fe_buffer,
            self.precision_buffer,
            self.energy_buffer
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

    def show(self):
        """Display monitor window."""
        plt.show()

    def save(self, filename: str = 'apgi_monitor.png'):
        """Save current view to file."""
        self.fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Monitor saved to {filename}")
