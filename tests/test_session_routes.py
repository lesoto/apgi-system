"""
Test Session API Routes

Integration tests for session management endpoints.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient

from api.main import create_app
from api.routes import sessions
from api.services.session_manager import SessionLifecycleState, SessionManager, SimulationSession


@pytest.fixture
def mock_redis() -> AsyncMock:
    mock_client = AsyncMock(spec=redis.Redis)
    mock_client.ping = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def mock_session_manager() -> Mock:
    manager = Mock(spec=SessionManager)

    # Mock create_session
    async def mock_create_session(request: Any, user_id: str = "default_user") -> str:
        return "test-session-id-123"

    manager.create_session = AsyncMock(side_effect=mock_create_session)

    # Mock get_session
    async def mock_get_session(session_id: str) -> Mock | None:
        if session_id == "test-session-id-123":
            mock_sim = Mock(spec=SimulationSession)
            mock_sim.session_id = session_id
            mock_sim.state = SessionLifecycleState.CREATED
            mock_sim.created_at = "2025-12-03T10:30:00"
            mock_sim.updated_at = "2025-12-03T10:30:00"
            mock_sim.config = {"config_path": "config/default.yaml"}

            # Mock session methods
            async def mock_start() -> dict[str, str]:
                mock_sim.state = SessionLifecycleState.RUNNING
                return {"session_id": session_id, "status": "running"}

            mock_sim.start = AsyncMock(side_effect=mock_start)

            async def mock_pause() -> dict[str, str]:
                mock_sim.state = SessionLifecycleState.PAUSED
                return {"session_id": session_id, "status": "paused"}

            mock_sim.pause = AsyncMock(side_effect=mock_pause)

            async def mock_stop() -> dict[str, str]:
                mock_sim.state = SessionLifecycleState.STOPPED
                return {"session_id": session_id, "status": "stopped"}

            mock_sim.stop = AsyncMock(side_effect=mock_stop)

            async def mock_reset() -> dict[str, str]:
                mock_sim.state = SessionLifecycleState.CREATED
                return {"session_id": session_id, "status": "created"}

            mock_sim.reset = AsyncMock(side_effect=mock_reset)

            return mock_sim
        else:
            raise ValueError(f"Session {session_id} not found")

    manager.get_session = AsyncMock(side_effect=mock_get_session)

    # Mock delete_session
    async def mock_delete_session(session_id: str) -> None:
        if session_id != "test-session-id-123":
            raise ValueError(f"Session {session_id} not found")

    manager.delete_session = AsyncMock(side_effect=mock_delete_session)

    # Mock update_session_state
    manager.update_session_state = AsyncMock()

    return manager


@pytest.fixture
def client(mock_redis: AsyncMock, mock_session_manager: Mock) -> TestClient:
    """Create a test client with mocked dependencies."""
    app = create_app()

    # Override the session manager dependency
    sessions._session_manager = mock_session_manager  # type: ignore[attr-defined]
    sessions._redis_client = mock_redis  # type: ignore[attr-defined]

    # Mock authentication dependencies
    from api.services import authorization as auth
    from api.services.auth_manager import TokenPayload

    # Create mock user with admin role
    from datetime import datetime

    mock_user = TokenPayload(  # type: ignore[call-arg]
        user_id="test-user-123",
        username="testuser",
        roles=["admin"],
        exp=datetime.fromtimestamp(9999999999),
    )

    # Override get_current_user to return mock user
    async def mock_get_current_user() -> TokenPayload:
        return mock_user

    # Override require_permission to pass through
    async def mock_require_permission(permission: auth.Permission) -> TokenPayload:
        return mock_user

    # Override verify_session_owner to pass through
    async def mock_verify_session_owner(session_id: str) -> None:
        pass

    # Apply overrides using FastAPI's dependency override
    app.dependency_overrides[auth.get_current_user] = mock_get_current_user
    app.dependency_overrides[auth.require_permission] = mock_require_permission
    app.dependency_overrides[auth.verify_session_owner] = mock_verify_session_owner
    app.dependency_overrides[sessions.get_session_manager] = lambda: mock_session_manager

    # Skip startup/shutdown events for testing
    app.router.on_startup = []
    app.router.on_shutdown = []

    return TestClient(app)


def test_create_session(client: Any) -> None:
    """Test creating a new session."""
    response = client.post(
        "/v1/sessions/", json={"config_path": "config/default.yaml", "description": "Test session"}
    )

    if response.status_code != 201:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "created"
    assert "created_at" in data
    assert "config" in data


def test_get_session(client: Any) -> None:
    """Test retrieving session details."""
    response = client.get("/v1/sessions/test-session-id-123/")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id-123"
    assert data["status"] == "created"
    assert "created_at" in data
    assert "updated_at" in data
    assert "config" in data


def test_get_session_not_found(client: Any) -> None:
    """Test retrieving non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/")

    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "SESSION_NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"].lower()


def test_start_session(client: Any) -> None:
    """Test starting a session."""
    response = client.post("/v1/sessions/test-session-id-123/start/")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id-123"
    assert data["status"] == "running"
    assert "timestamp" in data


def test_pause_session(client: TestClient) -> None:
    """Test pausing a session."""
    # First start the session
    client.post("/v1/sessions/test-session-id-123/start/")

    # Then pause it
    response = client.post("/v1/sessions/test-session-id-123/pause/")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id-123"
    assert data["status"] == "paused"
    assert "timestamp" in data


def test_stop_session(client: TestClient) -> None:
    """Test stopping a session."""
    response = client.post("/v1/sessions/test-session-id-123/stop/")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id-123"
    assert data["status"] == "stopped"
    assert "timestamp" in data


def test_reset_session(client: TestClient) -> None:
    """Test resetting a session."""
    response = client.post("/v1/sessions/test-session-id-123/reset/")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-id-123"
    assert data["status"] == "created"
    assert "timestamp" in data


def test_delete_session(client: TestClient) -> None:
    """Test deleting a session."""
    response = client.delete("/v1/sessions/test-session-id-123/")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_session_not_found(client: TestClient) -> None:
    """Test deleting non-existent session."""
    response = client.delete("/v1/sessions/nonexistent-id/")

    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "SESSION_NOT_FOUND"
    assert "does not exist" in error_data["error"]["message"].lower()


def test_session_lifecycle_workflow(client: TestClient) -> None:
    """Test complete session lifecycle."""
    # Create session
    create_response = client.post("/v1/sessions/", json={"config_path": "config/default.yaml"})
    assert create_response.status_code == 201
    session_id = create_response.json()["session_id"]

    # Get session details
    get_response = client.get(f"/v1/sessions/{session_id}/")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "created"

    # Start session
    start_response = client.post(f"/v1/sessions/{session_id}/start/")
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "running"

    # Pause session
    pause_response = client.post(f"/v1/sessions/{session_id}/pause/")
    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "paused"

    # Stop session
    stop_response = client.post(f"/v1/sessions/{session_id}/stop/")
    assert stop_response.status_code == 200
    assert stop_response.json()["status"] == "stopped"

    # Reset session
    reset_response = client.post(f"/v1/sessions/{session_id}/reset/")
    assert reset_response.status_code == 200
    assert reset_response.json()["status"] == "created"

    # Delete session
    delete_response = client.delete(f"/v1/sessions/{session_id}/")
    assert delete_response.status_code == 204
