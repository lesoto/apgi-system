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
from api.middleware.authentication import (
    AuthenticationMiddleware,
    get_current_user_from_request,
    is_authenticated
)
from api.middleware.rate_limiting import (
    RateLimitingMiddleware
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
    "ResponseSchemaValidationMiddleware",
    "AuthenticationMiddleware",
    "get_current_user_from_request",
    "is_authenticated",
    "RateLimitingMiddleware"
]
