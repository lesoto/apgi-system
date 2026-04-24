from abc import ABC, abstractmethod
from typing import Any, Dict


class SubsystemProtocol(ABC):
    """Abstract base class for subsystem communication."""

    def __init__(self, name: str):
        """Initialize subsystem protocol.

        Parameters
        ----------
        name : str
            Name of the subsystem
        """
        self.name = name
        self.enabled = True

    @abstractmethod
    def step(self, dt: float, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single timestep of the subsystem.

        Parameters
        ----------
        dt : float
            Timestep duration in ms
        inputs : Dict[str, Any]
            Input data for the subsystem

        Returns
        -------
        Dict[str, Any]
            Subsystem output and state updates
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current subsystem state.

        Returns
        -------
        Dict[str, Any]
            State dictionary
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset subsystem state."""
        pass
