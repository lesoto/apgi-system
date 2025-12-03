"""
API Middleware

Custom middleware for request processing, authentication, rate limiting, etc.
"""

from api.middleware.logging import (
    RequestLoggingMiddleware,
    StructuredLogger,
    ErrorLoggingHandler,
    error_logger,
    configure_structured_logging
)
from api.middleware.metrics import (
    PrometheusMetricsMiddleware,
    MetricsCollector,
    metrics_collector
)
from api.middleware.alerting import (
    AlertManager,
    AlertSeverity,
    alert_manager,
    configure_alerting
)
from api.middleware.schema_validation import (
    ResponseSchemaValidationMiddleware
)

__all__ = [
    "RequestLoggingMiddleware",
    "StructuredLogger",
    "ErrorLoggingHandler",
    "error_logger",
    "configure_structured_logging",
    "PrometheusMetricsMiddleware",
    "MetricsCollector",
    "metrics_collector",
    "AlertManager",
    "AlertSeverity",
    "alert_manager",
    "configure_alerting",
    "ResponseSchemaValidationMiddleware"
]
