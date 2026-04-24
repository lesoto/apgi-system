"""
Prometheus Metrics Middleware

Provides Prometheus metrics for monitoring API performance and health.
"""

import time
from typing import Awaitable, Callable

import psutil
from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Import SLO tracker
from apgi_framework.performance.slo_tracker import (
    get_slo_tracker,
    record_endpoint_metric,
)

# Define Prometheus metrics

# Request counter by endpoint, method, and status
request_counter = Counter(
    "apgi_api_requests_total", "Total number of API requests", ["method", "endpoint", "status_code"]
)

# Request duration histogram with per-endpoint percentiles
request_duration = Histogram(
    "apgi_api_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# Per-endpoint percentile histograms
p50_latency = Gauge("apgi_api_latency_p50_ms", "P50 latency in milliseconds", ["endpoint"])
p95_latency = Gauge("apgi_api_latency_p95_ms", "P95 latency in milliseconds", ["endpoint"])
p99_latency = Gauge("apgi_api_latency_p99_ms", "P99 latency in milliseconds", ["endpoint"])

# Active sessions gauge
active_sessions = Gauge("apgi_api_active_sessions", "Number of active simulation sessions")

# Task queue length gauge
task_queue_length = Gauge("apgi_api_task_queue_length", "Number of pending async tasks")

# Error counter by type
error_counter = Counter(
    "apgi_api_errors_total", "Total number of errors", ["error_type", "endpoint"]
)

# Active requests gauge
active_requests = Gauge("apgi_api_active_requests", "Number of requests currently being processed")

# Memory usage gauge
memory_usage_bytes = Gauge("apgi_api_memory_usage_bytes", "Current memory usage in bytes")

# CPU usage gauge
cpu_usage_percent = Gauge("apgi_api_cpu_usage_percent", "Current CPU usage percentage")

# Response size histogram
response_size_bytes = Histogram(
    "apgi_api_response_size_bytes",
    "Response size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000),
)

# SLO Error Budgets
slo_error_budget_remaining = Gauge(
    "apgi_api_slo_error_budget_remaining_percent", "Remaining error budget for SLO", ["endpoint"]
)
slo_latency_budget_remaining = Gauge(
    "apgi_api_slo_latency_budget_remaining_percent",
    "Remaining latency budget for SLO",
    ["endpoint"],
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that collects Prometheus metrics for all HTTP requests.

    Tracks:
    - Request count by endpoint, method, and status
    - Request duration by endpoint and method
    - Active requests
    - Errors by type
    - Response sizes
    - System metrics (memory and CPU usage)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Skip metrics collection for the metrics endpoint itself
        if request.url.path == "/v1/metrics":
            return await call_next(request)

        # Normalize endpoint path (remove IDs for better aggregation)
        endpoint = self._normalize_endpoint(request.url.path)
        method = request.method

        # Increment active requests
        active_requests.inc()

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code

            request_counter.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

            request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            # Track response size
            if hasattr(response, "headers") and "content-length" in response.headers:
                response_size = int(response.headers["content-length"])
                response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

            # Track errors (4xx and 5xx)
            if status_code >= 400:
                error_type = "client_error" if status_code < 500 else "server_error"
                error_counter.labels(error_type=error_type, endpoint=endpoint).inc()

            # Update system metrics
            self._update_system_metrics()

            # Record to SLO tracker
            response_time_ms = duration * 1000
            record_endpoint_metric(
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                status_code=status_code,
                error=status_code >= 400,
            )

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time

            error_counter.labels(error_type=type(e).__name__, endpoint=endpoint).inc()

            request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            # Record error to SLO tracker
            record_endpoint_metric(
                endpoint=endpoint,
                response_time_ms=duration * 1000,
                status_code=500,
                error=True,
            )

            # Re-raise exception
            raise

        finally:
            # Decrement active requests
            active_requests.dec()

            # Update real SLO metrics from SLO tracker
            self._update_slo_metrics(endpoint)

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path by replacing IDs with placeholders.

        This helps aggregate metrics across similar endpoints.

        Args:
            path: Original request path

        Returns:
            Normalized path with ID placeholders
        """
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            # Replace UUIDs and numeric IDs with placeholders
            if self._looks_like_id(part):
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        return "/".join(normalized_parts)

    def _looks_like_id(self, part: str) -> bool:
        """
        Check if a path part looks like an ID.

        Args:
            part: Path component

        Returns:
            True if it looks like an ID
        """
        # Check for UUID pattern
        if len(part) == 36 and part.count("-") == 4:
            return True

        # Check for numeric ID
        if part.isdigit():
            return True

        # Check for task ID pattern (task_xxx)
        if part.startswith("task_"):
            return True

        return False

    def _update_system_metrics(self) -> None:
        """Update system-level metrics (memory and CPU usage)."""
        try:
            # Memory usage
            memory_info = psutil.virtual_memory()
            memory_usage_bytes.set(memory_info.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_usage_percent.set(cpu_percent)
        except Exception:
            # Silently fail if psutil is not available or other errors occur
            pass

    def _update_slo_metrics(self, endpoint: str) -> None:
        """Update SLO metrics from SLO tracker for real-time percentiles."""
        try:
            slo_tracker = get_slo_tracker()
            report = slo_tracker.get_slo_report(endpoint)

            if endpoint in report:
                ep_report = report[endpoint]
                if ep_report["status"] != "no_data":
                    # Update percentile gauges
                    p50_latency.labels(endpoint=endpoint).set(ep_report["p50"]["current"])
                    p95_latency.labels(endpoint=endpoint).set(ep_report["p95"]["current"])
                    p99_latency.labels(endpoint=endpoint).set(ep_report["p99"]["current"])

                    # Calculate remaining budgets
                    error_budget = ep_report["error_rate"]
                    latency_budget = ep_report["p95"]

                    # Set remaining budget percentages
                    slo_error_budget_remaining.labels(endpoint=endpoint).set(
                        (1.0 - error_budget["current"]) * 100
                    )
                    slo_latency_budget_remaining.labels(endpoint=endpoint).set(
                        max(0, 1.0 - (latency_budget["current"] / latency_budget["budget"])) * 100
                        if latency_budget["budget"] > 0
                        else 100.0
                    )
        except Exception:
            # Silently fail if SLO tracker not available
            pass


class MetricsCollector:
    """
    Helper class for updating application-specific metrics.
    """

    @staticmethod
    def set_active_sessions(count: int) -> None:
        """
        Update the active sessions gauge.

        Args:
            count: Number of active sessions
        """
        active_sessions.set(count)

    @staticmethod
    def set_task_queue_length(count: int) -> None:
        """
        Update the task queue length gauge.

        Args:
            count: Number of pending tasks
        """
        task_queue_length.set(count)

    @staticmethod
    def increment_error(error_type: str, endpoint: str) -> None:
        """
        Increment error counter.

        Args:
            error_type: Type of error
            endpoint: Endpoint where error occurred
        """
        error_counter.labels(error_type=error_type, endpoint=endpoint).inc()


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_response() -> Response:
    """
    Generate Prometheus metrics response.

    Returns:
        Response with Prometheus metrics in text format
    """
    from starlette.responses import Response

    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
