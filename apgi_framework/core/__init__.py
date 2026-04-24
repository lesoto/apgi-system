"""
Core mathematical framework for the APGI Framework.

This module contains the fundamental mathematical implementations including
the APGI ignition threshold equation, precision calculations, and prediction
error processing.
"""

from .data_models import (
    APGIParameters,
    ConsciousnessAssessment,
    ExperimentalTrial,
    FalsificationResult,
    NeuralSignatures,
    PharmacologicalCondition,
    StatisticalSummary,
)
from ..engines import PredictiveIgnitionNetwork, SomaticAgent

# Import engines from the engines module (consolidated)
from apgi_framework.engines import (
    APGIEquation,
    PrecisionCalculator,
    PrecisionWeighting,
    PredictionErrorProcessor,
    SomaticMarkerEngine,
    ContextType,
    ThresholdManager,
    ThresholdAdaptationType,
)

from apgi_framework.core.active_inference import (
    ActiveInferenceAgent,
    ActiveInferenceEngine,
    HierarchicalGaussianFilter,
)
from apgi_framework.core.free_energy import FreeEnergyCalculator
from apgi_framework.core.predictive_processing import HierarchicalPredictor
from apgi_framework.core.vp15 import VP15ValidationProtocol

__all__ = [
    "APGIEquation",
    "PrecisionCalculator",
    "PredictionErrorProcessor",
    "SomaticMarkerEngine",
    "ContextType",
    "ThresholdManager",
    "ThresholdAdaptationType",
    "SomaticAgent",
    "PredictiveIgnitionNetwork",
    "APGIParameters",
    "NeuralSignatures",
    "ConsciousnessAssessment",
    "ExperimentalTrial",
    "FalsificationResult",
    "StatisticalSummary",
    "PharmacologicalCondition",
]
