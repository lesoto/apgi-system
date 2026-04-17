"""Core active inference and predictive processing modules."""

from apgi_simulation.core.active_inference import (
    ActiveInferenceAgent,
    ActiveInferenceEngine,
    VectorizedAgentPool,
)
from apgi_simulation.core.free_energy import FreeEnergyCalculator
from apgi_simulation.core.precision import PrecisionWeighting
from apgi_simulation.core.predictive_processing import HierarchicalPredictor
from apgi_simulation.core.vp15 import VP15Bounds, VP15Metrics, VP15ValidationProtocol

__all__ = [
    "ActiveInferenceAgent",
    "ActiveInferenceEngine",
    "FreeEnergyCalculator",
    "HierarchicalPredictor",
    "PrecisionWeighting",
    "VectorizedAgentPool",
    "VP15Bounds",
    "VP15Metrics",
    "VP15ValidationProtocol",
]
