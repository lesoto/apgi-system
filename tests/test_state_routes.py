"""
Test State Access API Routes

Integration tests for state access endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
import redis.asyncio as redis
from typing import Dict, Any

from api.main import create_app
from api.routes import sessions
from api.services.session_manager import SessionManager, SimulationSession, SessionLifecycleState


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    mock_client = AsyncMock(spec=redis.Redis)
    mock_client.ping = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.close = AsyncMock()
    return mock_client


@pytest.fixture
def mock_session_manager() -> Mock:
    """Create a mock SessionManager with state access support."""
    manager = Mock(spec=SessionManager)

    # Mock get_session with state data
    async def mock_get_session(session_id: str) -> Mock:
        if session_id == "test-session-id-123":
            mock_sim = Mock(spec=SimulationSession)
            mock_sim.session_id = session_id
            mock_sim.state = SessionLifecycleState.RUNNING
            mock_sim.created_at = "2025-12-03T10:30:00"
            mock_sim.updated_at = "2025-12-03T10:31:00"
            mock_sim.config = {"config_path": "config/default.yaml"}

            # Mock get_state method with comprehensive state data
            async def mock_get_state() -> Dict[str, Any]:
                return {
                    "time": 5000.0,
                    "ignition": {
                        "ignition_occurred": True,
                        "total_signal": 2.5,
                        "threshold": 2.0,
                        "duration_ms": 350.0,
                    },
                    "workspace": {
                        "is_broadcasting": True,
                        "content": "sensory",
                        "broadcast_duration_ms": 350.0,
                    },
                    "body": {"heart_rate": 75.0, "cortisol": 0.15, "temperature": 37.0},
                    "allostasis": {"allostatic_load": 0.3},
                    "precision": {"exteroceptive": 1.2, "interoceptive": 0.8},
                    "metabolism": {"reserves": 850.0, "reserve_fraction": 0.85},
                    "self_model": {"minimal": {"coherence": 0.75}, "narrative": {"active": True}},
                    "prediction": {
                        "errors": {"level_0": [0.1, 0.2, 0.15], "level_1": [0.05, 0.08]},
                        "exteroceptive_stats": {"mean_error": 0.15, "std_error": 0.05},
                        "interoceptive_stats": {"mean_error": 0.10, "std_error": 0.03},
                    },
                    "interoception": {
                        "somatic_markers": {
                            "num_markers": 15,
                            "total_retrievals": 100,
                            "successful_retrievals": 85,
                            "retrieval_rate": 0.85,
                            "markers": [
                                {
                                    "context_hash": "abc123",
                                    "action_hash": "def456",
                                    "gain": 0.75,
                                    "timestamp": 1000.0,
                                }
                            ],
                        }
                    },
                    "history": {
                        "time": [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
                        "ignitions": [0, 1, 0, 1, 1],
                        "free_energy": [1.5, 1.8, 1.6, 1.9, 1.7],
                        "precision": [1.0, 1.2, 1.1, 1.3, 1.2],
                        "metabolic_reserves": [1000.0, 950.0, 900.0, 875.0, 850.0],
                    },
                }

            mock_sim.get_state = AsyncMock(side_effect=mock_get_state)

            return mock_sim
        else:
            raise ValueError(f"Session {session_id} not found")

    manager.get_session = AsyncMock(side_effect=mock_get_session)

    return manager


@pytest.fixture
def client(mock_redis, mock_session_manager) -> TestClient:
    """Create a test client with mocked dependencies."""
    app = create_app()

    # Override the session manager dependency
    sessions._session_manager = mock_session_manager
    sessions._redis_client = mock_redis

    # Skip startup/shutdown events for testing
    app.router.on_startup = []
    app.router.on_shutdown = []

    return TestClient(app)


def test_get_system_state(client: TestClient) -> None:
    """Test retrieving complete system state."""
    response = client.get("/v1/sessions/test-session-id-123/state")

    assert response.status_code == 200
    data = response.json()

    # Verify all required state components are present
    assert "time_ms" in data
    assert data["time_ms"] == 5000.0

    assert "ignition" in data
    assert data["ignition"]["ignition_occurred"] is True
    assert data["ignition"]["total_signal"] == 2.5
    assert data["ignition"]["threshold"] == 2.0
    assert data["ignition"]["duration_ms"] == 350.0

    assert "workspace" in data
    assert data["workspace"]["is_broadcasting"] is True
    assert data["workspace"]["content"] == "sensory"

    assert "body" in data
    assert data["body"]["heart_rate"] == 75.0
    assert data["body"]["cortisol"] == 0.15
    assert data["body"]["temperature"] == 37.0

    assert "allostasis" in data
    assert data["allostasis"]["allostatic_load"] == 0.3

    assert "precision" in data
    assert data["precision"]["exteroceptive"] == 1.2
    assert data["precision"]["interoceptive"] == 0.8

    assert "metabolism" in data
    assert data["metabolism"]["reserves"] == 850.0
    assert data["metabolism"]["reserve_fraction"] == 0.85

    assert "self_model" in data
    assert data["self_model"]["minimal"]["coherence"] == 0.75
    assert data["self_model"]["narrative"]["active"] is True


def test_get_system_state_not_found(client: TestClient) -> None:
    """Test retrieving state for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/state")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_ignition_history(client: TestClient) -> None:
    """Test retrieving ignition event history."""
    response = client.get("/v1/sessions/test-session-id-123/ignition-history")

    assert response.status_code == 200
    data = response.json()

    assert "events" in data
    assert isinstance(data["events"], list)

    # Should have 3 ignition events (indices 1, 3, 4 from history)
    assert len(data["events"]) == 3

    # Verify event structure
    for event in data["events"]:
        assert "time_ms" in event
        assert "duration_ms" in event
        assert "trigger_signal" in event
        assert "threshold" in event


def test_get_ignition_history_with_time_filter(client: TestClient) -> None:
    """Test retrieving ignition history with time filters."""
    response = client.get(
        "/v1/sessions/test-session-id-123/ignition-history",
        params={"start_time": 2500.0, "end_time": 4500.0},
    )

    assert response.status_code == 200
    data = response.json()

    # Should only include events within time range
    assert "events" in data
    for event in data["events"]:
        assert 2500.0 <= event["time_ms"] <= 4500.0


def test_get_ignition_history_with_limit(client: TestClient) -> None:
    """Test retrieving ignition history with limit."""
    response = client.get("/v1/sessions/test-session-id-123/ignition-history", params={"limit": 2})

    assert response.status_code == 200
    data = response.json()

    # Should respect limit
    assert len(data["events"]) <= 2

    # Should include pagination info if more data available
    if data.get("pagination"):
        assert "next_cursor" in data["pagination"]
        assert "has_more" in data["pagination"]


def test_get_ignition_history_not_found(client: TestClient) -> None:
    """Test retrieving ignition history for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/ignition-history")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_interoceptive_state(client: TestClient) -> None:
    """Test retrieving interoceptive body state."""
    response = client.get("/v1/sessions/test-session-id-123/interoception")

    assert response.status_code == 200
    data = response.json()

    # Verify body state components
    assert "heart_rate" in data
    assert data["heart_rate"] == 75.0

    assert "cortisol" in data
    assert data["cortisol"] == 0.15

    assert "temperature" in data
    assert data["temperature"] == 37.0


def test_get_interoceptive_state_not_found(client: TestClient) -> None:
    """Test retrieving interoceptive state for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/interoception")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_prediction_errors(client: TestClient) -> None:
    """Test retrieving prediction errors."""
    response = client.get("/v1/sessions/test-session-id-123/prediction-errors")

    assert response.status_code == 200
    data = response.json()

    # Verify prediction error structure
    assert "session_id" in data
    assert data["session_id"] == "test-session-id-123"

    assert "time_ms" in data
    assert data["time_ms"] == 5000.0

    assert "prediction_errors" in data
    assert "exteroceptive_stats" in data
    assert "interoceptive_stats" in data

    # Verify stats structure
    assert "mean_error" in data["exteroceptive_stats"]
    assert "std_error" in data["exteroceptive_stats"]


def test_get_prediction_errors_not_found(client: TestClient) -> None:
    """Test retrieving prediction errors for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/prediction-errors")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_somatic_markers(client: TestClient) -> None:
    """Test retrieving somatic markers."""
    response = client.get("/v1/sessions/test-session-id-123/somatic-markers")

    assert response.status_code == 200
    data = response.json()

    # Verify somatic marker structure
    assert "session_id" in data
    assert data["session_id"] == "test-session-id-123"

    assert "time_ms" in data
    assert data["time_ms"] == 5000.0

    assert "num_markers" in data
    assert data["num_markers"] == 15

    assert "total_retrievals" in data
    assert data["total_retrievals"] == 100

    assert "successful_retrievals" in data
    assert data["successful_retrievals"] == 85

    assert "retrieval_rate" in data
    assert data["retrieval_rate"] == 0.85

    assert "markers" in data
    assert isinstance(data["markers"], list)


def test_get_somatic_markers_not_found(client: TestClient) -> None:
    """Test retrieving somatic markers for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/somatic-markers")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_state_endpoints_require_valid_session(client: TestClient) -> None:
    """Test that all state endpoints require a valid session."""
    endpoints = [
        "/v1/sessions/invalid-id/state",
        "/v1/sessions/invalid-id/ignition-history",
        "/v1/sessions/invalid-id/interoception",
        "/v1/sessions/invalid-id/prediction-errors",
        "/v1/sessions/invalid-id/somatic-markers",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404, f"Endpoint {endpoint} should return 404"
