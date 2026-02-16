"""
Test Health Check Endpoint

Tests for the comprehensive /v1/health endpoint that checks all dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from api.main import create_app
from api.services.health_check import HealthCheckService


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_health_service() -> Mock:
    """Create a mock health check service."""
    service = Mock(spec=HealthCheckService)
    return service


def test_health_endpoint_all_healthy(client: TestClient) -> None:
    """Test health endpoint when all components are healthy."""
    # Mock the health service to return healthy status
    with patch("api.routes.health.health_service") as mock_service:
        mock_service.perform_health_check = AsyncMock(
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

        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"
        assert data["checks"]["redis"]["status"] == "healthy"
        assert data["checks"]["celery"]["status"] == "healthy"


def test_health_endpoint_database_unhealthy(client: TestClient) -> None:
    """Test health endpoint when database is unhealthy."""
    with patch("api.routes.health.health_service") as mock_service:
        mock_service.perform_health_check = AsyncMock(
            return_value={
                "status": "unhealthy",
                "version": "1.0.0",
                "timestamp": "2025-12-03T10:30:00Z",
                "checks": {
                    "database": {
                        "status": "unhealthy",
                        "message": "Database connection failed: Connection refused",
                    },
                    "redis": {"status": "healthy", "message": "Redis connection successful"},
                    "celery": {"status": "healthy", "message": "1 Celery worker(s) active"},
                },
            }
        )

        response = client.get("/v1/health")
        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "unhealthy"


def test_health_endpoint_redis_unhealthy(client: TestClient) -> None:
    """Test health endpoint when Redis is unhealthy."""
    with patch("api.routes.health.health_service") as mock_service:
        mock_service.perform_health_check = AsyncMock(
            return_value={
                "status": "unhealthy",
                "version": "1.0.0",
                "timestamp": "2025-12-03T10:30:00Z",
                "checks": {
                    "database": {"status": "healthy", "message": "Database connection successful"},
                    "redis": {
                        "status": "unhealthy",
                        "message": "Redis connection failed: Connection refused",
                    },
                    "celery": {"status": "healthy", "message": "1 Celery worker(s) active"},
                },
            }
        )

        response = client.get("/v1/health")
        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["checks"]["redis"]["status"] == "unhealthy"


def test_health_endpoint_celery_unhealthy(client: TestClient) -> None:
    """Test health endpoint when Celery is unhealthy."""
    with patch("api.routes.health.health_service") as mock_service:
        mock_service.perform_health_check = AsyncMock(
            return_value={
                "status": "unhealthy",
                "version": "1.0.0",
                "timestamp": "2025-12-03T10:30:00Z",
                "checks": {
                    "database": {"status": "healthy", "message": "Database connection successful"},
                    "redis": {"status": "healthy", "message": "Redis connection successful"},
                    "celery": {"status": "unhealthy", "message": "No active Celery workers"},
                },
            }
        )

        response = client.get("/v1/health")
        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["checks"]["celery"]["status"] == "unhealthy"


def test_health_endpoint_service_not_initialized(client: TestClient) -> None:
    """Test health endpoint when service is not initialized."""
    with patch("api.routes.health.health_service", None):
        response = client.get("/v1/health")
        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert "error" in data
        assert "not initialized" in data["error"]


def test_health_service_check_database_success() -> None:
    """Test health service database check when successful."""
    service = HealthCheckService()

    with patch("api.services.health_check.get_db_context") as mock_db:
        mock_session = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = (1,)
        mock_session.execute.return_value = mock_result
        mock_db.return_value.__enter__.return_value = mock_session

        status, message = service.check_database()

        assert status == "healthy"
        assert "successful" in message.lower()


def test_health_service_check_database_failure() -> None:
    """Test health service database check when it fails."""
    service = HealthCheckService()

    with patch("api.services.health_check.get_db_context") as mock_db:
        mock_db.return_value.__enter__.side_effect = Exception("Connection refused")

        status, message = service.check_database()

        assert status == "unhealthy"
        assert "failed" in message.lower()


@pytest.mark.asyncio
async def test_health_service_check_redis_success() -> None:
    """Test health service Redis check when successful."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)

    service = HealthCheckService(redis_client=mock_redis)
    status, message = await service.check_redis()

    assert status == "healthy"
    assert "successful" in message.lower()


@pytest.mark.asyncio
async def test_health_service_check_redis_failure() -> None:
    """Test health service Redis check when it fails."""
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(side_effect=Exception("Connection refused"))

    service = HealthCheckService(redis_client=mock_redis)
    status, message = await service.check_redis()

    assert status == "unhealthy"
    assert "failed" in message.lower()


@pytest.mark.asyncio
async def test_health_service_check_redis_not_initialized() -> None:
    """Test health service Redis check when client is not initialized."""
    service = HealthCheckService(redis_client=None)
    status, message = await service.check_redis()

    assert status == "unhealthy"
    assert "not initialized" in message.lower()


def test_health_service_check_celery_success() -> None:
    """Test health service Celery check when successful."""
    mock_celery = Mock()
    mock_inspect = Mock()
    mock_inspect.active.return_value = {"worker1": []}
    mock_celery.control.inspect.return_value = mock_inspect

    service = HealthCheckService(celery_app=mock_celery)
    status, message = service.check_celery()

    assert status == "healthy"
    assert "active" in message.lower()


def test_health_service_check_celery_no_workers() -> None:
    """Test health service Celery check when no workers are active."""
    mock_celery = Mock()
    mock_inspect = Mock()
    mock_inspect.active.return_value = {}
    mock_celery.control.inspect.return_value = mock_inspect

    service = HealthCheckService(celery_app=mock_celery)
    status, message = service.check_celery()

    assert status == "unhealthy"
    assert "no active" in message.lower()


def test_health_service_check_celery_none_response() -> None:
    """Test health service Celery check when inspect returns None."""
    mock_celery = Mock()
    mock_inspect = Mock()
    mock_inspect.active.return_value = None
    mock_celery.control.inspect.return_value = mock_inspect

    service = HealthCheckService(celery_app=mock_celery)
    status, message = service.check_celery()

    assert status == "unhealthy"
    assert "no celery workers available" in message.lower()


def test_health_service_check_celery_failure() -> None:
    """Test health service Celery check when it fails."""
    mock_celery = Mock()
    mock_celery.control.inspect.side_effect = Exception("Connection error")

    service = HealthCheckService(celery_app=mock_celery)
    status, message = service.check_celery()

    assert status == "unhealthy"
    assert "failed" in message.lower()
