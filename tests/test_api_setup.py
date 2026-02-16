"""
Test API Setup and Basic Functionality

Verifies that the API application is properly configured and can start.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


def test_app_creation() -> None:
    """Test that the FastAPI application can be created."""
    app = create_app()
    assert app is not None
    assert app.title == "APGI System API"
    assert app.version == "1.0.0"


def test_root_endpoint(client: TestClient) -> None:
    """Test the root endpoint returns basic API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "APGI System API"
    assert data["version"] == "1.0.0"
    assert "docs" in data
    assert "health" in data


def test_health_check_endpoint(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_openapi_schema(client: TestClient) -> None:
    """Test that OpenAPI schema is generated."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "APGI System API"


def test_docs_endpoint(client: TestClient) -> None:
    """Test that Swagger UI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_endpoint(client: TestClient) -> None:
    """Test that ReDoc documentation is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
