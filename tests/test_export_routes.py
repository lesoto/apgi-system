"""
Test Data Export API Routes

Integration tests for data export endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Generator
from unittest.mock import AsyncMock, Mock

import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient

import api.services.authorization as auth
from api.main import create_app
from api.routes import export, sessions
from api.services.auth_manager import TokenPayload
from api.services.authorization import get_current_user, require_permission
from api.services.data_export import DataExportService
from api.services.session_manager import SessionLifecycleState, SessionManager, SimulationSession


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
    """Create a mock SessionManager with test data."""
    manager = Mock(spec=SessionManager)

    # Mock get_session
    async def mock_get_session(session_id: str) -> Mock:
        if session_id == "test-session-id-123":
            mock_sim = Mock(spec=SimulationSession)
            mock_sim.session_id = session_id
            mock_sim.state = SessionLifecycleState.RUNNING

            # Mock get_state with history data
            async def mock_get_state() -> Dict[str, Any]:
                return {
                    "time": 5000.0,
                    "history": {
                        "time": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0],
                        "ignitions": [False, True, False, True, False, False],
                        "free_energy": [1.5, 1.8, 1.6, 2.0, 1.7, 1.9],
                        "metabolic_reserves": [1000.0, 980.0, 960.0, 940.0, 920.0, 900.0],
                        "allostatic_load": [0.2, 0.3, 0.25, 0.35, 0.28, 0.32],
                    },
                    "ignition": {"ignition_occurred": False},
                    "workspace": {"is_broadcasting": False},
                    "body": {"heart_rate": 70.0, "cortisol": 0.1, "temperature": 37.0},
                }

            mock_sim.get_state = AsyncMock(side_effect=mock_get_state)

            return mock_sim
        else:
            raise ValueError(f"Session {session_id} not found")

    manager.get_session = AsyncMock(side_effect=mock_get_session)

    return manager


@pytest.fixture
def client(mock_redis: AsyncMock, mock_session_manager: Mock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies."""
    app = create_app(test_mode=True)

    # Create mock user for auth bypass
    mock_user = TokenPayload(
        user_id="test-user-123",
        username="testuser",
        roles=["admin"],
        exp=datetime.fromtimestamp(9999999999),
    )

    async def mock_get_current_user() -> TokenPayload:
        return mock_user

    # Override require_permission to pass through
    async def mock_require_permission(permission: auth.Permission) -> TokenPayload:
        return mock_user

    # Apply overrides
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[require_permission] = mock_require_permission

    # Override the session manager dependency
    sessions._session_manager = mock_session_manager  # type: ignore[attr-defined]
    sessions._redis_client = mock_redis  # type: ignore[attr-defined]

    # Initialize export service with mock session manager
    export._data_export_service = DataExportService(mock_session_manager)

    # Skip startup/shutdown events for testing
    app.router.on_startup = []
    app.router.on_shutdown = []

    yield TestClient(app)


def test_export_session_data_json(client: TestClient) -> None:
    """Test exporting session data as JSON."""
    response = client.get(
        "/v1/sessions/test-session-id-123/export",
        params={"format": "json"},
        headers={"Authorization": "Bearer fake_token"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers.get("content-disposition", "")

    # Verify JSON structure
    data = response.json()
    assert "session_id" in data
    assert "exported_at" in data
    assert "history" in data
    assert "time" in data["history"]


def test_export_session_data_csv(client: TestClient) -> None:
    """Test exporting session data as CSV."""
    response = client.get("/v1/sessions/test-session-id-123/export", params={"format": "csv"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers.get("content-disposition", "")

    # Verify CSV has header
    content = response.text
    assert "time" in content
    assert "free_energy" in content or "ignitions" in content


def test_export_with_variable_filter(client: TestClient) -> None:
    """Test exporting with variable filtering."""
    response = client.get(
        "/v1/sessions/test-session-id-123/export",
        params={"format": "json", "variables": "time,free_energy"},
    )

    assert response.status_code == 200
    data = response.json()
    history = data["history"]

    # Should include time and free_energy
    assert "time" in history
    assert "free_energy" in history


def test_export_with_time_filter(client: TestClient) -> None:
    """Test exporting with time range filtering."""
    response = client.get(
        "/v1/sessions/test-session-id-123/export",
        params={"format": "json", "start_time": 10.0, "end_time": 40.0},
    )

    assert response.status_code == 200
    data = response.json()
    history = data["history"]

    # Verify time filtering worked
    times = history.get("time", [])
    if times:
        assert all(t >= 10.0 for t in times)
        assert all(t <= 40.0 for t in times)


def test_export_session_not_found(client: TestClient) -> None:
    """Test exporting non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/export", params={"format": "json"})

    assert response.status_code == 404
    # Error response may not have 'detail' key, just check status code


def test_get_summary_statistics(client: TestClient) -> None:
    """Test retrieving summary statistics."""
    response = client.get("/v1/sessions/test-session-id-123/summary")

    assert response.status_code == 200
    data = response.json()

    # Verify summary structure
    assert "session_id" in data
    assert "duration_ms" in data
    assert "num_steps" in data
    assert "ignition_stats" in data
    assert "energy_stats" in data
    assert "allostasis_stats" in data

    # Verify ignition stats
    ignition_stats = data["ignition_stats"]
    assert "total_events" in ignition_stats
    assert "frequency_hz" in ignition_stats


def test_get_time_series_data(client: TestClient) -> None:
    """Test retrieving time series data."""
    response = client.get(
        "/v1/sessions/test-session-id-123/timeseries",
        params={"variables": "free_energy,metabolic_reserves"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify time series structure
    assert "session_id" in data
    assert "time" in data
    assert "data" in data
    assert "num_points" in data

    # Verify requested variables are present
    assert "free_energy" in data["data"]
    assert "metabolic_reserves" in data["data"]


def test_get_time_series_with_pagination(client: TestClient) -> None:
    """Test time series with pagination."""
    response = client.get(
        "/v1/sessions/test-session-id-123/timeseries",
        params={"variables": "free_energy", "limit": 3},
    )

    assert response.status_code == 200
    data = response.json()

    # Should have pagination info
    assert "pagination" in data
    assert data["num_points"] <= 3

    # Check if more data available
    pagination = data["pagination"]
    if pagination:
        assert "has_more" in pagination
        assert "next_cursor" in pagination


def test_get_time_series_with_downsampling(client: TestClient) -> None:
    """Test time series with downsampling."""
    response = client.get(
        "/v1/sessions/test-session-id-123/timeseries",
        params={"variables": "free_energy", "downsample": 2},
    )

    assert response.status_code == 200
    data = response.json()

    # Downsampling should reduce number of points
    assert data["num_points"] <= 3  # Original has 6 points, downsample by 2 = 3


def test_get_event_analysis(client: TestClient) -> None:
    """Test retrieving event analysis."""
    response = client.get(
        "/v1/sessions/test-session-id-123/events", params={"event_type": "ignition"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify event analysis structure
    assert "session_id" in data
    assert "event_type" in data
    assert "total_events" in data
    assert "duration_distribution" in data
    assert "trigger_patterns" in data


def test_get_event_analysis_session_not_found(client: TestClient) -> None:
    """Test event analysis for non-existent session."""
    response = client.get("/v1/sessions/nonexistent-id/events", params={"event_type": "ignition"})

    assert response.status_code == 404
    # Error response may not have 'detail' key, just check status code


def test_complete_export_workflow(client: TestClient) -> None:
    """Test complete data export workflow."""
    session_id = "test-session-id-123"

    # 1. Get summary statistics
    summary_response = client.get(f"/v1/sessions/{session_id}/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["num_steps"] > 0

    # 2. Get time series data
    timeseries_response = client.get(
        f"/v1/sessions/{session_id}/timeseries",
        params={"variables": "free_energy,metabolic_reserves"},
    )
    assert timeseries_response.status_code == 200
    timeseries = timeseries_response.json()
    assert len(timeseries["time"]) > 0

    # 3. Get event analysis
    events_response = client.get(
        f"/v1/sessions/{session_id}/events", params={"event_type": "ignition"}
    )
    assert events_response.status_code == 200
    events = events_response.json()
    assert "total_events" in events

    # 4. Export complete data
    export_response = client.get(f"/v1/sessions/{session_id}/export", params={"format": "json"})
    assert export_response.status_code == 200
    export_data = export_response.json()
    assert "history" in export_data
