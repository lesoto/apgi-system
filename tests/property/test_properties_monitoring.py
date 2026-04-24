"""
Property-based tests for logging and monitoring functionality.

Tests universal properties for request logging, error logging, and metrics.
"""

import json
from datetime import datetime
from typing import Any, Callable
from unittest.mock import Mock, patch

import pytest
from fastapi import Request
from hypothesis import given, settings
from hypothesis import strategies as st

from api.middleware.logging import ErrorLoggingHandler, StructuredLogger
from api.middleware.metrics import error_counter, request_counter, request_duration

# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def http_method_strategy(draw: Callable[[Any], Any]) -> str:
    """Generate valid HTTP methods."""
    return draw(st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH"]))


@st.composite
def http_path_strategy(draw: Callable[[Any], Any]) -> str:
    """Generate valid HTTP paths."""
    paths = [
        "/v1/sessions",
        "/v1/sessions/{id}",
        "/v1/sessions/{id}/start",
        "/v1/sessions/{id}/state",
        "/v1/tasks",
        "/v1/tasks/{id}",
        "/v1/health",
        "/v1/metrics",
    ]
    return draw(st.sampled_from(paths))


@st.composite
def http_status_code_strategy(draw: Callable[[Any], Any]) -> int:
    """Generate valid HTTP status codes."""
    return draw(st.sampled_from([200, 201, 400, 401, 403, 404, 422, 429, 500, 502, 503]))


@st.composite
def client_id_strategy(draw: Callable[[Any], Any]) -> str:
    """Generate client identifiers (IP addresses)."""
    return draw(st.from_regex(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", fullmatch=True))


@st.composite
def duration_ms_strategy(draw: Callable[[Any], Any]) -> float:
    """Generate request durations in milliseconds."""
    return draw(st.floats(min_value=0.1, max_value=10000.0))


@st.composite
def error_type_strategy(draw: Callable[[Any], Any]) -> str:
    """Generate error type names."""
    error_types: list[str] = [
        "ValueError",
        "KeyError",
        "TypeError",
        "RuntimeError",
        "SessionNotFoundError",
        "ValidationError",
    ]
    result: str = draw(st.sampled_from(error_types))
    return result


# ============================================================================
# Property Tests
# ============================================================================


@given(
    message=st.text(min_size=1, max_size=200),
    method=http_method_strategy(),
    path=http_path_strategy(),
    status_code=http_status_code_strategy(),
    duration_ms=duration_ms_strategy(),
    client_id=client_id_strategy(),
)
@settings(max_examples=100)
def test_property_request_logging_completeness(
    message: str, method: str, path: str, status_code: int, duration_ms: float, client_id: str
) -> None:
    """
    **Feature: api-rest-interface, Property 22: Request logging completeness**

    For any processed request, the log entry should include method, path,
    status code, duration, and client identifier.

    Validates: Requirements 10.1
    """
    # Create structured logger
    logger = StructuredLogger("test.requests")

    # Capture log output
    with patch("logging.Logger.info") as mock_log:
        # Log a request
        logger.info(
            message,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            client_id=client_id,
        )

        # Verify log was called
        assert mock_log.called

        # Get the logged message
        log_message = mock_log.call_args[0][0]

        # Parse JSON log entry
        log_entry = json.loads(log_message)

        # Verify all required fields are present
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry
        assert "message" in log_entry
        assert "method" in log_entry
        assert "path" in log_entry
        assert "status_code" in log_entry
        assert "duration_ms" in log_entry
        assert "client_id" in log_entry

        # Verify field values match
        assert log_entry["method"] == method
        assert log_entry["path"] == path
        assert log_entry["status_code"] == status_code
        assert log_entry["duration_ms"] == duration_ms
        assert log_entry["client_id"] == client_id
        assert log_entry["level"] == "INFO"

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(log_entry["timestamp"].replace("Z", "+00:00"))


@given(
    error_type=error_type_strategy(),
    error_message=st.text(min_size=1, max_size=200),
    method=http_method_strategy(),
    path=http_path_strategy(),
    client_id=client_id_strategy(),
)
@settings(max_examples=100)
def test_property_error_logging_completeness(
    error_type: str, error_message: str, method: str, path: str, client_id: str
) -> None:
    """
    **Feature: api-rest-interface, Property 23: Error logging completeness**

    For any error that occurs, the log entry should include stack trace,
    request context, and a unique error ID.

    Validates: Requirements 10.2
    """
    # Create error logging handler
    error_logger = ErrorLoggingHandler()

    # Create a mock exception
    try:
        # Dynamically create exception of the specified type
        exception_class = type(error_type, (Exception,), {})
        raise exception_class(error_message)
    except Exception as exc:
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.method = method
        mock_request.url.path = path
        mock_request.client.host = client_id
        mock_request.state.request_id = "test_req_123"

        # Capture log output
        with patch("api.middleware.logging.StructuredLogger.error") as mock_log:
            # Log the error
            error_logger.log_error(exc, request=mock_request, error_code="TEST_ERROR")

            # Verify log was called
            assert mock_log.called

            # Get the logged kwargs
            log_kwargs = mock_log.call_args[1]

            # Verify all required fields are present
            assert "error_type" in log_kwargs
            assert "error_message" in log_kwargs
            assert "stack_trace" in log_kwargs
            assert "request_id" in log_kwargs
            assert "method" in log_kwargs
            assert "path" in log_kwargs
            assert "client_id" in log_kwargs
            assert "error_code" in log_kwargs

            # Verify field values
            assert log_kwargs["error_type"] == error_type
            assert log_kwargs["error_message"] == error_message
            assert log_kwargs["method"] == method
            assert log_kwargs["path"] == path
            assert log_kwargs["client_id"] == client_id
            assert log_kwargs["error_code"] == "TEST_ERROR"

            # Verify stack trace is present and non-empty
            assert len(log_kwargs["stack_trace"]) > 0
            assert "Traceback" in log_kwargs["stack_trace"]


@given(
    method=http_method_strategy(),
    endpoint=http_path_strategy(),
    status_code=http_status_code_strategy(),
)
@settings(max_examples=100)
def test_property_metrics_exposure(method: str, endpoint: str, status_code: int) -> None:
    """
    **Feature: api-rest-interface, Property 24: Metrics exposure**

    For any running API instance, the metrics endpoint should expose
    request rate, error rate, and response time percentiles.

    Validates: Requirements 10.3
    """
    # Record a request in metrics
    request_counter.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    # Record duration
    request_duration.labels(method=method, endpoint=endpoint).observe(0.123)

    # If it's an error, record error metric
    if status_code >= 400:
        error_type = "client_error" if status_code < 500 else "server_error"
        error_counter.labels(error_type=error_type, endpoint=endpoint).inc()

    # Generate metrics output
    from prometheus_client import generate_latest

    metrics_output = generate_latest().decode("utf-8")

    # Verify metrics are present in output
    # Check for request counter metric
    assert "apgi_api_requests_total" in metrics_output

    # Check for request duration metric (histogram includes multiple metrics)
    assert "apgi_api_request_duration_seconds" in metrics_output

    # Check for error counter if applicable
    if status_code >= 400:
        assert "apgi_api_errors_total" in metrics_output

    # Verify metric has labels
    # The metric line should include method, endpoint, and status_code labels
    # Labels can appear in any order, so check for each individually
    assert f'method="{method}"' in metrics_output
    assert f'endpoint="{endpoint}"' in metrics_output
    assert f'status_code="{status_code}"' in metrics_output

    # Verify histogram buckets are present (for percentiles)
    assert "apgi_api_request_duration_seconds_bucket" in metrics_output
    assert "apgi_api_request_duration_seconds_sum" in metrics_output
    assert "apgi_api_request_duration_seconds_count" in metrics_output


# ============================================================================
# Additional validation tests
# ============================================================================


@given(log_level=st.sampled_from(["INFO", "WARNING", "ERROR", "DEBUG"]))
@settings(max_examples=20)
def test_structured_logger_json_format(log_level: str) -> None:
    """
    Verify that structured logger always outputs valid JSON.
    """
    logger = StructuredLogger("test.logger")

    with patch("logging.Logger." + log_level.lower()) as mock_log:
        # Log a message
        getattr(logger, log_level.lower())("Test message", field1="value1", field2=123, field3=True)

        # Get logged message
        log_message = mock_log.call_args[0][0]

        # Verify it's valid JSON
        log_entry = json.loads(log_message)

        # Verify structure
        assert isinstance(log_entry, dict)
        assert log_entry["level"] == log_level
        assert log_entry["message"] == "Test message"
        assert log_entry["field1"] == "value1"
        assert log_entry["field2"] == 123
        assert log_entry["field3"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
