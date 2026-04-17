"""Core active inference and predictive processing modules."""

from apgi_system.core.active_inference import (
    ActiveInferenceAgent,
    ActiveInferenceEngine,
    VectorizedAgentPool,
)
from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.core.precision import PrecisionWeighting
from apgi_system.core.predictive_processing import HierarchicalPredictor
from apgi_system.core.vp15 import VP15Bounds, VP15Metrics, VP15ValidationProtocol

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
