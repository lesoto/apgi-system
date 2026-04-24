"""
Experimental tasks module for the APGI Framework.

This module contains various cognitive and experimental tasks
for testing the APGI falsification framework.
"""

from .attentional_blink import AttentionalBlinkTask, StimulusType
from .binocular_rivalry import BinocularRivalryTask
from .change_blindness import ChangeBlindnessTask, ChangeType
from .iowa_gambling import IowaGamblingTask, DeckType, DECK_SCHEDULES
from .masking_paradigm import MaskingParadigmTask, MaskType
from .nback import NBackTask, NBackLevel, StimulusType as NBackStimulusType
from .stroop import StroopTask, StimulusType as StroopStimulusType

__all__ = [
    "AttentionalBlinkTask",
    "StimulusType",
    "BinocularRivalryTask",
    "ChangeBlindnessTask",
    "ChangeType",
    "IowaGamblingTask",
    "DeckType",
    "DECK_SCHEDULES",
    "MaskingParadigmTask",
    "MaskType",
    "StroopTask",
    "StroopStimulusType",
    "NBackTask",
    "NBackLevel",
    "NBackStimulusType",
]
