"""Core threshold module - redirects to engines.threshold_engine."""

from apgi_framework.engines.threshold_engine import ThresholdManager  # noqa: F401

__all__ = [
    "ThresholdManager",
]
