"""Experimental tasks for APGI system validation."""

from apgi_system.experiments.tasks.attentional_blink import AttentionalBlinkTask
from apgi_system.experiments.tasks.change_blindness import ChangeBlindnessTask
from apgi_system.experiments.tasks.binocular_rivalry import BinocularRivalryTask
from apgi_system.experiments.tasks.masking_paradigm import MaskingParadigmTask
from apgi_system.experiments.tasks.iowa_gambling import IowaGamblingTask
from apgi_system.experiments.tasks.stroop_task import StroopTask
from apgi_system.experiments.tasks.nback_task import NBackTask

__all__ = [
    "AttentionalBlinkTask",
    "ChangeBlindnessTask",
    "BinocularRivalryTask",
    "MaskingParadigmTask",
    "IowaGamblingTask",
    "StroopTask",
    "NBackTask",
]
