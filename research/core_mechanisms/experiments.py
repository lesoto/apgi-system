"""
Core mechanisms experiments for APGI Framework.

This module contains experimental paradigms for core consciousness mechanisms.
"""

from typing import Any, Dict, List


class CoreMechanismExperiment:
    """Base class for core mechanism experiments."""

    def __init__(self, name: str):
        self.name = name
        self.parameters: Dict[str, Any] = {}

    def run(self, **kwargs) -> Dict[str, Any]:
        """Run the experiment."""
        return {"status": "completed", "experiment": self.name}


# Available experiments
AVAILABLE_EXPERIMENTS = {
    "basic_awareness": CoreMechanismExperiment("Basic Awareness"),
    "threshold_detection": CoreMechanismExperiment("Threshold Detection"),
    "somatic_integration": CoreMechanismExperiment("Somatic Integration"),
}


def get_experiment(name: str) -> CoreMechanismExperiment:
    """Get an experiment by name."""
    return AVAILABLE_EXPERIMENTS.get(name, CoreMechanismExperiment("Unknown"))


def list_experiments() -> List[str]:
    """List available experiments."""
    return list(AVAILABLE_EXPERIMENTS.keys())
