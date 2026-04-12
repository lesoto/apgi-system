"""
Integration test to verify CORS headers are present in API responses.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from api.routes import health
from api.services.auth_manager import TokenPayload
from api.services.authorization import get_current_user


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    app = create_app(test_mode=True)

    # Mock health service
    mock_health_service = AsyncMock()
    mock_health_service.perform_health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2025-12-03T10:30:00Z",
            "checks": {
                "database": {"status": "healthy", "message": "Database connection successful"},
                "redis": {"status": "healthy", "message": "Redis connection successful"},
                "celery": {"status": "healthy", "message": "1 Celery worker(s) active"},
            },
        }
    )
    health.health_service = mock_health_service

    # Create mock user for auth bypass
    mock_user = TokenPayload(
        user_id="test-user-123",
        username="testuser",
        roles=["admin"],
        exp=datetime.fromtimestamp(9999999999),
    )

    async def mock_get_current_user() -> TokenPayload:
        return mock_user

    # Override get_current_user dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user

    return TestClient(app)


def test_cors_headers_present_on_root(client: TestClient) -> None:
    """Test that CORS headers are present on root endpoint."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_headers_present_on_health(client: TestClient) -> None:
    """Test that CORS headers are present on health endpoint."""
    response = client.get("/v1/health", headers={"Origin": "http://localhost:8000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_cors_headers_present_on_version(client: TestClient) -> None:
    """Test that CORS headers are present on version endpoint."""
    response = client.get("/v1/version", headers={"Origin": "http://localhost:3000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_credentials_header_present(client: TestClient) -> None:
    """Test that CORS credentials header is present."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})

    # Verify credentials header is present
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_headers_without_origin(client: TestClient) -> None:
    """Test that API works without Origin header (non-browser clients)."""
    response = client.get("/v1/health")

    # Response should still be successful
    assert response.status_code == 200

    # CORS headers may not be present without Origin header
    # This is expected behavior - CORS is only for browser requests
