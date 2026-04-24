"""
API Middleware

Custom middleware for request processing, authentication, rate limiting, etc.
"""

from api.middleware.alerting import AlertManager, AlertSeverity, alert_manager, configure_alerting
from api.middleware.authentication import (
    AuthenticationMiddleware,
    get_current_user_from_request,
    is_authenticated,
)
from api.middleware.logging import (
    ErrorLoggingHandler,
    RequestLoggingMiddleware,
    StructuredLogger,
    configure_structured_logging,
    error_logger,
)
from api.middleware.metrics import MetricsCollector, PrometheusMetricsMiddleware, metrics_collector
from api.middleware.rate_limiting import RateLimitingMiddleware
from api.middleware.request_deduplication import (
    RequestDeduplicationMiddleware,
    deduplication_manager,
)
from api.middleware.schema_validation import ResponseSchemaValidationMiddleware
from api.middleware.serialization import OptimizedSerializationMiddleware, serialization_manager

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
    "ResponseSchemaValidationMiddleware",
    "AuthenticationMiddleware",
    "get_current_user_from_request",
    "is_authenticated",
    "RateLimitingMiddleware",
    "RequestDeduplicationMiddleware",
    "deduplication_manager",
    "OptimizedSerializationMiddleware",
    "serialization_manager",
]
