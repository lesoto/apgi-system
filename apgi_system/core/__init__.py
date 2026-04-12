"""Core active inference and predictive processing modules."""

from apgi_system.core.active_inference import ActiveInferenceEngine
from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.core.precision import PrecisionWeighting
from apgi_system.core.predictive_processing import HierarchicalPredictor

__all__ = [
    "ActiveInferenceEngine",
    "FreeEnergyCalculator",
    "HierarchicalPredictor",
    "PrecisionWeighting",
]
