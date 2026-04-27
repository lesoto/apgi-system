"""Core precision module - redirects to engines.precision_engine."""

from apgi_framework.engines.precision_engine import (  # noqa: F401
    PrecisionCalculator,
    PrecisionWeighting,
)

__all__ = [
    "PrecisionCalculator",
    "PrecisionWeighting",
]
