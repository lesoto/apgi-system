"""
Integration test to verify CORS headers are present in API responses.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


def test_cors_headers_present_on_root(client):
    """Test that CORS headers are present on root endpoint."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_headers_present_on_health(client):
    """Test that CORS headers are present on health endpoint."""
    response = client.get("/health", headers={"Origin": "http://localhost:8000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_cors_headers_present_on_version(client):
    """Test that CORS headers are present on version endpoint."""
    response = client.get("/v1/version", headers={"Origin": "http://localhost:3000"})

    # Verify CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_credentials_header_present(client):
    """Test that CORS credentials header is present."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})

    # Verify credentials header is present
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_headers_without_origin(client):
    """Test that API works without Origin header (non-browser clients)."""
    response = client.get("/health")

    # Response should still be successful
    assert response.status_code == 200

    # CORS headers may not be present without Origin header
    # This is expected behavior - CORS is only for browser requests
