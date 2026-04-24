"""
GUI Mediator for decoupling UI components from the application controller.

This mediator implements the Mediator pattern to reduce direct dependencies
between UI components and the core application logic.
"""

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class GUIMediator:
    """
    Mediator between GUI components and the APGI system.

    This class provides a centralized interface for UI components to interact
    with the simulation controller and system, decoupling the UI from the
    application logic.
    """

    def __init__(self, system: Any, simulation_controller: Any) -> None:
        """
        Initialize the GUI mediator.

        Args:
            system: The APGISystem instance
            simulation_controller: The SimulationController instance
        """
        self._system = system
        self._sim_controller = simulation_controller
        self._ui_callbacks: Dict[str, Callable] = {}
        self._data_buffers: Dict[str, list] = {
            "ignition": [],
            "surprise": [],
            "extero_precision": [],
            "intero_precision": [],
            "somatic_gain": [],
            "metabolic_reserves": [],
            "allostatic_load": [],
        }
        self._time_buffer: list = []
        self._max_buffer_points = 1000

    def register_callback(self, event_name: str, callback: Callable) -> None:
        """
        Register a UI callback for a specific event.

        Args:
            event_name: Name of the event (e.g., 'on_step', 'on_error')
            callback: Callback function to invoke
        """
        self._ui_callbacks[event_name] = callback

    def unregister_callback(self, event_name: str) -> None:
        """
        Unregister a UI callback.

        Args:
            event_name: Name of the event to unregister
        """
        self._ui_callbacks.pop(event_name, None)

    # Simulation Control Methods
    def start_simulation(self) -> bool:
        """
        Start the simulation.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._sim_controller.start()
            self._notify_ui("on_simulation_started", {})
            return True
        except Exception as e:
            logger.error(f"Failed to start simulation: {e}")
            self._notify_ui("on_error", {"message": str(e)})
            return False

    def pause_simulation(self) -> bool:
        """
        Pause/resume the simulation.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._sim_controller.pause()
            is_paused = self._sim_controller.is_paused
            self._notify_ui("on_simulation_paused", {"paused": is_paused})
            return True
        except Exception as e:
            logger.error(f"Failed to pause simulation: {e}")
            self._notify_ui("on_error", {"message": str(e)})
            return False

    def stop_simulation(self) -> bool:
        """
        Stop the simulation.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._sim_controller.stop()
            self._notify_ui("on_simulation_stopped", {})
            return True
        except Exception as e:
            logger.error(f"Failed to stop simulation: {e}")
            self._notify_ui("on_error", {"message": str(e)})
            return False

    def reset_simulation(self) -> bool:
        """
        Reset the simulation.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._sim_controller.reset()
            self._clear_buffers()
            self._notify_ui("on_simulation_reset", {})
            return True
        except Exception as e:
            logger.error(f"Failed to reset simulation: {e}")
            self._notify_ui("on_error", {"message": str(e)})
            return False

    def set_simulation_speed(self, speed: float) -> None:
        """
        Set the simulation speed.

        Args:
            speed: Speed multiplier (1.0 = normal speed)
        """
        self._sim_controller.set_speed(speed)

    # Data Access Methods
    def get_simulation_state(self) -> Dict[str, Any]:
        """
        Get the current simulation state.

        Returns:
            Dictionary containing simulation state information
        """
        return {
            "is_running": self._sim_controller.is_running,
            "is_paused": self._sim_controller.is_paused,
            "speed": self._sim_controller.speed,
            "current_time": self._time_buffer[-1] if self._time_buffer else 0.0,
        }

    def get_data_buffers(self) -> Dict[str, list]:
        """
        Get the current data buffers.

        Returns:
            Dictionary of data buffers
        """
        return {
            "time": self._time_buffer.copy(),
            **{key: buf.copy() for key, buf in self._data_buffers.items()},
        }

    def get_buffer_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the data buffers.

        Returns:
            Dictionary with buffer statistics
        """
        stats = {
            "buffer_size": len(self._time_buffer),
            "max_buffer_points": self._max_buffer_points,
            "buffer_utilization": len(self._time_buffer) / self._max_buffer_points,
        }

        if self._time_buffer:
            stats["time_range"] = {  # type: ignore[assignment]
                "min": min(self._time_buffer),
                "max": max(self._time_buffer),
                "duration": max(self._time_buffer) - min(self._time_buffer),
            }

        return stats

    # Parameter Modification Methods
    def set_system_parameter(self, param_name: str, value: Any) -> bool:
        """
        Set a system parameter.

        Args:
            param_name: Name of the parameter
            value: Value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            if hasattr(self._system, param_name):
                setattr(self._system, param_name, value)
                self._notify_ui("on_parameter_changed", {"param": param_name, "value": value})
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set parameter {param_name}: {e}")
            return False

    def get_system_parameter(self, param_name: str) -> Optional[Any]:
        """
        Get a system parameter.

        Args:
            param_name: Name of the parameter

        Returns:
            Parameter value or None if not found
        """
        try:
            return getattr(self._system, param_name, None)
        except Exception as e:
            logger.error(f"Failed to get parameter {param_name}: {e}")
            return None

    # Event Handling Methods (called by SimulationController)
    def on_simulation_step(self, step_data: Dict[str, Any]) -> None:
        """
        Handle simulation step data from the controller.

        Args:
            step_data: Dictionary containing step data
        """
        # Update buffers
        sim_time = step_data.get("time", 0.0)
        self._time_buffer.append(sim_time)

        mapping = {
            "ignition": "ignition_probability",
            "surprise": "surprise",
            "extero_precision": "extero_precision",
            "intero_precision": "intero_precision",
            "somatic_gain": "somatic_gain",
            "metabolic_reserves": "metabolic_reserves",
            "allostatic_load": "allostatic_load",
        }

        for key, data_key in mapping.items():
            val = step_data.get(data_key, 0.0)
            self._data_buffers[key].append(float(val))

        # Maintain buffer size
        if len(self._time_buffer) > self._max_buffer_points:
            self._time_buffer.pop(0)
            for buf in self._data_buffers.values():
                buf.pop(0)

        # Notify UI
        self._notify_ui("on_step", step_data)

    def on_simulation_error(self, error_msg: str) -> None:
        """
        Handle simulation error from the controller.

        Args:
            error_msg: Error message
        """
        logger.error(f"Simulation error: {error_msg}")
        self._notify_ui("on_error", {"message": error_msg})
        self._sim_controller.stop()

    def on_simulation_reset(self) -> None:
        """
        Handle simulation reset from the controller.
        """
        self._clear_buffers()
        self._notify_ui("on_simulation_reset", {})

    # Internal Methods
    def _notify_ui(self, event_name: str, data: Dict[str, Any]) -> None:
        """
        Notify registered UI callbacks of an event.

        Args:
            event_name: Name of the event
            data: Event data
        """
        if event_name in self._ui_callbacks:
            try:
                self._ui_callbacks[event_name](data)
            except Exception as e:
                logger.error(f"Error in UI callback for {event_name}: {e}")

    def _clear_buffers(self) -> None:
        """Clear all data buffers."""
        self._time_buffer.clear()
        for buf in self._data_buffers.values():
            buf.clear()

    # Properties
    @property
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return bool(self._sim_controller.is_running)

    @property
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return bool(self._sim_controller.is_paused)

    @property
    def system(self) -> Any:
        """Get the system instance."""
        return self._system

    @property
    def simulation_controller(self) -> Any:
        """Get the simulation controller instance."""
        return self._sim_controller
