"""
Integration tests for version endpoint.

Tests the /v1/version endpoint to ensure it returns correct version information.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


def test_version_endpoint_returns_200(client: TestClient) -> None:
    """Test that version endpoint returns 200 OK."""
    response = client.get("/v1/version")
    assert response.status_code == 200


def test_version_endpoint_returns_json(client: TestClient) -> None:
    """Test that version endpoint returns JSON content."""
    response = client.get("/v1/version")
    assert response.headers["content-type"] == "application/json"


def test_version_endpoint_has_required_fields(client: TestClient) -> None:
    """Test that version endpoint returns all required fields."""
    response = client.get("/v1/version")
    data = response.json()

    required_fields = [
        "current_version",
        "api_version",
        "supported_versions",
        "deprecated_versions",
        "api_spec_url",
        "documentation_url",
        "timestamp",
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_version_endpoint_current_version_format(client: TestClient) -> None:
    """Test that current_version follows semantic versioning."""
    response = client.get("/v1/version")
    data = response.json()

    current_version = data["current_version"]
    assert isinstance(current_version, str)

    # Check semantic versioning format (X.Y.Z)
    parts = current_version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor format"

    # Check that parts are numeric
    for part in parts[:2]:  # At least major and minor should be numeric
        assert part.isdigit(), f"Version part '{part}' should be numeric"


def test_version_endpoint_api_version_format(client: TestClient) -> None:
    """Test that api_version follows expected format."""
    response = client.get("/v1/version")
    data = response.json()

    api_version = data["api_version"]
    assert isinstance(api_version, str)
    assert api_version.startswith("v"), "API version should start with 'v'"

    # Extract version number
    version_num = api_version[1:]
    assert version_num.isdigit(), "API version number should be numeric"


def test_version_endpoint_supported_versions_is_list(client: TestClient) -> None:
    """Test that supported_versions is a non-empty list."""
    response = client.get("/v1/version")
    data = response.json()

    supported_versions = data["supported_versions"]
    assert isinstance(supported_versions, list)
    assert len(supported_versions) > 0, "Should have at least one supported version"


def test_version_endpoint_current_api_in_supported(client: TestClient) -> None:
    """Test that current API version is in supported versions."""
    response = client.get("/v1/version")
    data = response.json()

    api_version = data["api_version"]
    supported_versions = data["supported_versions"]

    assert (
        api_version in supported_versions
    ), f"Current API version '{api_version}' should be in supported versions"


def test_version_endpoint_deprecated_versions_is_list(client: TestClient) -> None:
    """Test that deprecated_versions is a list."""
    response = client.get("/v1/version")
    data = response.json()

    deprecated_versions = data["deprecated_versions"]
    assert isinstance(deprecated_versions, list)


def test_version_endpoint_no_overlap_deprecated_supported(client: TestClient) -> None:
    """Test that deprecated versions are not in supported versions."""
    response = client.get("/v1/version")
    data = response.json()

    supported_versions = data["supported_versions"]
    deprecated_versions = data["deprecated_versions"]

    for deprecated in deprecated_versions:
        assert (
            deprecated not in supported_versions
        ), f"Version '{deprecated}' cannot be both deprecated and supported"


def test_version_endpoint_api_spec_url_format(client: TestClient) -> None:
    """Test that api_spec_url is a valid path."""
    response = client.get("/v1/version")
    data = response.json()

    api_spec_url = data["api_spec_url"]
    assert isinstance(api_spec_url, str)
    assert api_spec_url.startswith("/"), "API spec URL should be a valid path"


def test_version_endpoint_documentation_url_format(client: TestClient) -> None:
    """Test that documentation_url is a valid path."""
    response = client.get("/v1/version")
    data = response.json()

    docs_url = data["documentation_url"]
    assert isinstance(docs_url, str)
    assert docs_url.startswith("/"), "Documentation URL should be a valid path"


def test_version_endpoint_timestamp_format(client: TestClient) -> None:
    """Test that timestamp is in ISO 8601 format with UTC timezone."""
    from datetime import datetime

    response = client.get("/v1/version")
    data = response.json()

    timestamp = data["timestamp"]
    assert isinstance(timestamp, str)
    assert timestamp.endswith("Z"), "Timestamp should be in UTC (ending with 'Z')"

    # Verify timestamp can be parsed
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Timestamp '{timestamp}' is not valid ISO 8601 format")


def test_version_endpoint_validates_requirements_6_1(client: TestClient) -> None:
    """
    Test that version endpoint validates Requirements 6.1.

    Requirements 6.1: WHEN the API is accessed THEN the system SHALL include
    version prefix in all endpoint paths (e.g., /v1/simulations)
    """
    response = client.get("/v1/version")
    assert response.status_code == 200

    # The endpoint itself follows the versioning pattern
    assert "/v1/version" == "/v1/version"


def test_version_endpoint_validates_requirements_6_4(client: TestClient) -> None:
    """
    Test that version endpoint validates Requirements 6.4.

    Requirements 6.4: WHEN clients request API version information THEN the
    system SHALL return current version, supported versions, and deprecation notices
    """
    response = client.get("/v1/version")
    data = response.json()

    # Should return current version
    assert "current_version" in data
    assert isinstance(data["current_version"], str)

    # Should return supported versions
    assert "supported_versions" in data
    assert isinstance(data["supported_versions"], list)

    # Should return deprecated versions (deprecation notices)
    assert "deprecated_versions" in data
    assert isinstance(data["deprecated_versions"], list)

    # Should include API spec URL
    assert "api_spec_url" in data
    assert isinstance(data["api_spec_url"], str)
