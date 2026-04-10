"""
Unit tests for API exception handlers.

Validates that various system exceptions are correctly caught and
transformed into standardized JSON error responses.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from api.exception_handlers import (
    unhandled_exception_handler,
    validation_error_handler,
    circuit_breaker_handler,
    http_exception_handler,
    api_error_handler,
)
from api.exceptions import APIError
from api.exceptions import (
    InvalidTokenError,
    AuthorizationError,
    SessionNotFoundError,
)
from utils.circuit_breaker_utils import CircuitBreakerOpenException


class CustomUnhandledError(Exception):
    """Custom exception for testing unhandled error handler."""

    pass


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with registered exception handlers."""
    app = FastAPI()

    # Register handlers - type ignore needed due to FastAPI's flexible handler signature
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(CircuitBreakerOpenException, circuit_breaker_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(APIError, api_error_handler)  # type: ignore[arg-type]

    # Add test routes
    @app.get("/trigger-500")
    async def trigger_500() -> None:
        raise CustomUnhandledError("Unexpected server error")

    # Register handler for custom exception (FastAPI doesn't route base Exception in tests)
    app.add_exception_handler(CustomUnhandledError, unhandled_exception_handler)

    @app.get("/trigger-validation")
    async def trigger_validation() -> None:
        # Manually raise RequestValidationError to simulate Pydantic failure
        raise RequestValidationError(errors=[])

    @app.get("/trigger-circuit-breaker")
    async def trigger_circuit_breaker() -> None:
        raise CircuitBreakerOpenException("Service unavailable due to circuit breaker")

    @app.get("/trigger-404")
    async def trigger_404() -> None:
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.get("/trigger-auth-error")
    async def trigger_auth_error() -> None:
        raise InvalidTokenError("Token is invalid")

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide a TestClient for the test app."""
    return TestClient(app)


@pytest.mark.unit
def test_unhandled_exception_handler(client: TestClient) -> None:
    """Test that generic exceptions return a 500 status code."""
    response = client.get("/trigger-500")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected error occurred. Please try again later."


@pytest.mark.unit
def test_circuit_breaker_handler(client: TestClient) -> None:
    """Test that CircuitBreakerException returns a 503 status code."""
    response = client.get("/trigger-circuit-breaker")
    assert response.status_code == 503
    data = response.json()
    assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "Circuit breaker" in data["error"]["message"]


@pytest.mark.unit
def test_http_exception_handler(client: TestClient) -> None:
    """Test that HTTPException returns its specified status code."""
    response = client.get("/trigger-404")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Resource not found"


@pytest.mark.unit
def test_validation_exception_handler(client: TestClient) -> None:
    """Test that RequestValidationError returns a 422 status code with details."""
    # We can also trigger this by sending invalid JSON to a POST route
    # But here we use our manual trigger
    response = client.get("/trigger-validation")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.unit
def test_custom_exception_mapping(app: FastAPI, client: TestClient) -> None:
    """Test that domain-specific exceptions are mapped to correct status codes."""

    @app.get("/trigger-not-found")
    async def trigger_custom_not_found() -> None:
        raise SessionNotFoundError("test-session-id")

    response = client.get("/trigger-not-found")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "SESSION_NOT_FOUND"

    @app.get("/trigger-forbidden")
    async def trigger_custom_forbidden() -> None:
        raise AuthorizationError("sessions", "delete", "admin")

    response = client.get("/trigger-forbidden")
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
