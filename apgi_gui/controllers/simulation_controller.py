"""
Simulation controller for the APGI GUI.
"""

import threading
import time
from typing import Any, Callable, Dict, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class SimulationController:
    """Controller for managing the APGI simulation thread and state."""

    def __init__(self, system: Any, callbacks: Dict[str, Callable]) -> None:
        """
        Initialize the simulation controller.

        Args:
            system: The APGISystem instance
            callbacks: Dictionary of callbacks for UI updates and data processing
        """
        self.system = system
        self.callbacks = callbacks

        self.is_running = False
        self.is_paused = False
        self.simulation_thread: Optional[threading.Thread] = None
        self.speed = 1.0

    def start(self) -> None:
        """Start the simulation thread."""
        if self.is_running:
            return

        if self.system is None:
            raise RuntimeError("APGI system is not initialized")

        self.is_running = True
        self.is_paused = False

        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()

    def pause(self) -> None:
        """Toggle pause state."""
        self.is_paused = not self.is_paused

    def stop(self) -> None:
        """Stop the simulation thread."""
        self.is_running = False
        self.is_paused = False

        # Wait for simulation thread to complete with timeout
        if self.simulation_thread is not None and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=2.0)
            if self.simulation_thread.is_alive():
                logger.warning("Simulation thread did not terminate within timeout")

    def reset(self) -> None:
        """Reset the simulation."""
        was_running = self.is_running
        if was_running:
            self.stop()

        if self.system:
            self.system.reset()
            if "on_reset" in self.callbacks:
                self.callbacks["on_reset"]()

    def set_speed(self, speed: float) -> None:
        """Set the simulation speed."""
        self.speed = speed

    def _simulation_loop(self) -> None:
        """Main simulation loop running in a background thread."""
        try:
            while self.is_running:
                if self.is_paused:
                    time.sleep(0.1)
                    continue

                # Run one step of the simulation
                start_time = time.time()

                # Check for custom input from UI
                extero_input = None
                if "get_custom_input" in self.callbacks:
                    extero_input = self.callbacks["get_custom_input"]()

                # Default to zero input if None
                if extero_input is None:
                    # Match sensory level nodes in default config (256)
                    extero_input = np.zeros(256)

                step_data = self.system.step(extero_input=extero_input)

                # Process data
                if "on_step" in self.callbacks:
                    self.callbacks["on_step"](step_data)

                # Control simulation speed
                elapsed = time.time() - start_time
                target_sleep = (0.1 / self.speed) - elapsed
                if target_sleep > 0:
                    time.sleep(target_sleep)

        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.is_running = False
            if "on_error" in self.callbacks:
                self.callbacks["on_error"]({"message": str(e)})
