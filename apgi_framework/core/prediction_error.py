"""Core prediction error module - redirects to engines.prediction_error_engine."""

from apgi_framework.engines.prediction_error_engine import (  # noqa: F401
    PredictionErrorProcessor,
)

__all__ = [
    "PredictionErrorProcessor",
]
