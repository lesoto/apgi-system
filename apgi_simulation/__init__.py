"""
APGI System: Allostatic Precision-Gated Ignition Framework

A computational model of consciousness integrating active inference,
predictive processing, and allostatic regulation.
"""

from apgi_simulation._version import __version__

from apgi_simulation.core.active_inference import ActiveInferenceEngine
from apgi_simulation.core.free_energy import FreeEnergyCalculator
from apgi_simulation.core.precision import PrecisionWeighting
from apgi_simulation.core.predictive_processing import HierarchicalPredictor

__all__ = [
    "ActiveInferenceEngine",
    "FreeEnergyCalculator",
    "HierarchicalPredictor",
    "PrecisionWeighting",
]
