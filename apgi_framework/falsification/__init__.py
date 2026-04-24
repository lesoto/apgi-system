"""
APGI Framework Testing Module

This module implements the primary falsification testing framework for the APGI
(Interoceptive Predictive Integration) Framework, including consciousness assessment,
neural signature validation, and experimental control mechanisms.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

# Core test implementations
from .primary_falsification import FalsificationResult, PrimaryFalsificationTest
from .consciousness_assessment import (
    ConsciousnessAssessment,
    ConsciousnessAssessmentSimulator,
    ConsciousnessValidator,
)
from .consciousness_without_ignition import ConsciousnessWithoutIgnitionTest
from .threshold_insensitivity import ThresholdInsensitivityTest
from .soma_bias import SomaBiasTest
from .mock_engine import FalsificationEngine

# Other supporting modules
from .ai_acc_validation import AIACCValidator
from .edge_case_interpreter import EdgeCaseInterpreter, EdgeCaseType, FrameworkBoundary
from .experimental_control import ExperimentalControlValidator
from .result_interpretation import FalsificationInterpreter, ResultLogger

__all__ = [
    "ConsciousnessAssessment",
    "ConsciousnessAssessmentSimulator",
    "ConsciousnessValidator",
    "AIACCValidator",
    "ExperimentalControlValidator",
    "FalsificationInterpreter",
    "ResultLogger",
    "EdgeCaseInterpreter",
    "EdgeCaseType",
    "FrameworkBoundary",
    "ConsciousnessWithoutIgnitionTest",
    "ThresholdInsensitivityTest",
    "SomaBiasTest",
    "PrimaryFalsificationTest",
    "FalsificationResult",
    "FalsificationEngine",
]
