"""Core precision module - redirects to engines.precision_engine."""

from apgi_framework.engines.precision_engine import (
    PrecisionCalculator,
    PrecisionWeighting,
)  # noqa: F401

__all__ = [
    "PrecisionCalculator",
    "PrecisionWeighting",
]
