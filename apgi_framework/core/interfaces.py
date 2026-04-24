"""
Stub module for subsystem interfaces.

This module provides type stubs for subsystem protocol interfaces
that are being migrated from the old apgi_simulation structure.
"""

from typing import Any, Dict

import numpy as np


class SubsystemProtocol:
    """Protocol for subsystem communication."""

    def __init__(self, name: str):
        """Initialize subsystem protocol.

        Parameters
        ----------
        name : str
            Name of the subsystem
        """
        self.name = name
        self.enabled = True

    def process(self, input_data: np.ndarray) -> np.ndarray:
        """Process input data.

        Parameters
        ----------
        input_data : np.ndarray
            Input data to process

        Returns
        -------
        np.ndarray
            Processed output
        """
        return input_data

    def get_state(self) -> Dict[str, Any]:
        """Get current subsystem state.

        Returns
        -------
        Dict[str, Any]
            State dictionary
        """
        return {"name": self.name, "enabled": self.enabled}

    def reset(self) -> None:
        """Reset subsystem state."""
        self.enabled = True
