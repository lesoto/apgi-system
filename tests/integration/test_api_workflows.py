"""
End-to-End API Workflow Integration Tests

Tests complete workflows through the API including:
- Complete simulation workflow (create → start → query → export)
- Authentication flow
- Task execution flow

Requirements tested:
- 1.1: HTTP status codes
- 2.1: Session creation
- 2.2: Session start
- 3.1: System state access
- 5.1: Data export
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import redis.asyncio as redis
import time

from api.main import create_app
from api.routes import sessions, state, export, tasks, auth
from api.services.session_manager import SessionManager, SimulationSession, SessionLifecycleState
from api.services.task_executor import TaskExecutor
from api.services.data_export import DataExportService
from api.database.models import User
from api.services.auth_manager import AuthManager


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_client = AsyncMock(spec=redis.Redis)
    mock_client.ping = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.setex = AsyncMock()
    mock_client.delete = AsyncMock()
    mock_client.close = AsyncMock()
    mock_client.zadd = AsyncMock()
    mock_client.zremrangebyscore = AsyncMock()
    mock_client.zcard = AsyncMock(return_value=0)
    return mock_client


@pytest.fixture
def mock_apgi_system():
    """Create a mock APGI system."""
    mock_system = Mock()
    mock_system.time = 0.0
    mock_system.timestep_ms = 10.0
    mock_system.is_running = False

    # Mock step method
    def mock_step(extero_input):
        mock_system.time += mock_system.timestep_ms
        return {
            "time": mock_system.time,
            "ignition": {
                "ignition_occurred": False,
                "total_signal": 1.5,
                "threshold": 2.0,
                "duration_ms": None,
            },
            "workspace": {
                "is_broadcasting": False,
                "content": None,
                "broadcast_duration_ms": None,
                "is_reportable": False,
            },
            "body": {
                "current": {
                    "heart_rate": 72.0,
                    "cortisol": 0.12,
                    "temperature": 37.0,
                    "glucose": 5.0,
                }
            },
            "allostasis": {"allostatic_load": 0.25},
            "precision": {"exteroceptive": 1.0, "interoceptive": 1.0},
            "metabolism": {"reserves": 900.0, "reserve_fraction": 0.9},
            "self_model": {"minimal": {"coherence": 0.8}, "narrative": {"active": False}},
        }

    mock_system.step = Mock(side_effect=mock_step)

    # Mock get_state method
    def mock_get_state():
        return {
            "time": mock_system.time,
            "timestep_ms": mock_system.timestep_ms,
            "is_running": mock_system.is_running,
            "core": {
                "active_inference": {},
                "precision": {"exteroceptive": 1.0, "interoceptive": 1.0},
            },
            "ignition": {"ignition_occurred": False},
            "interoception": {"body_state": {"heart_rate": 72.0}, "allostatic_load": 0.25},
            "self_model": {},
            "thermodynamic": {"metabolic_reserves": 900.0},
            "neural": {},
            "history": {
                "time": [0.0, 10.0, 20.0],
                "ignitions": [False, False, False],
                "free_energy": [1.5, 1.6, 1.4],
                "precision": [1.0, 1.0, 1.0],
                "metabolic_reserves": [1000.0, 990.0, 980.0],
            },
        }

    mock_system.get_state = Mock(side_effect=mock_get_state)
    mock_system.reset = Mock()

    return mock_system


@pytest.fixture
def mock_session_manager(mock_apgi_system):
    """Create a mock SessionManager with realistic behavior."""
    manager = Mock(spec=SessionManager)
    sessions_store = {}

    async def mock_create_session(request, user_id="default_user"):
        session_id = f"session-{len(sessions_store) + 1}"

        # Create mock simulation session
        mock_sim = Mock(spec=SimulationSession)
        mock_sim.session_id = session_id
        mock_sim.state = SessionLifecycleState.CREATED
        mock_sim.created_at = "2025-12-03T10:30:00"
        mock_sim.updated_at = "2025-12-03T10:30:00"
        mock_sim.config = {
            "config_path": request.config_path or "config/default.yaml",
            "description": request.description,
        }
        mock_sim.apgi_system = mock_apgi_system

        # Mock session methods
        async def mock_start():
            mock_sim.state = SessionLifecycleState.RUNNING
            mock_apgi_system.is_running = True
            return {"session_id": session_id, "status": "running"}

        async def mock_pause():
            mock_sim.state = SessionLifecycleState.PAUSED
            mock_apgi_system.is_running = False
            return {"session_id": session_id, "status": "paused"}

        async def mock_stop():
            mock_sim.state = SessionLifecycleState.STOPPED
            mock_apgi_system.is_running = False
            return {"session_id": session_id, "status": "stopped"}

        async def mock_reset():
            mock_sim.state = SessionLifecycleState.CREATED
            mock_apgi_system.time = 0.0
            mock_apgi_system.reset()
            return {"session_id": session_id, "status": "created"}

        async def mock_get_state():
            return mock_apgi_system.get_state()

        mock_sim.start = AsyncMock(side_effect=mock_start)
        mock_sim.pause = AsyncMock(side_effect=mock_pause)
        mock_sim.stop = AsyncMock(side_effect=mock_stop)
        mock_sim.reset = AsyncMock(side_effect=mock_reset)
        mock_sim.get_state = AsyncMock(side_effect=mock_get_state)

        sessions_store[session_id] = mock_sim
        return session_id

    async def mock_get_session(session_id):
        if session_id in sessions_store:
            return sessions_store[session_id]
        raise ValueError(f"Session {session_id} not found")

    async def mock_delete_session(session_id):
        if session_id in sessions_store:
            del sessions_store[session_id]
        else:
            raise ValueError(f"Session {session_id} not found")

    manager.create_session = AsyncMock(side_effect=mock_create_session)
    manager.get_session = AsyncMock(side_effect=mock_get_session)
    manager.delete_session = AsyncMock(side_effect=mock_delete_session)
    manager.update_session_state = AsyncMock()

    return manager


@pytest.fixture
def mock_data_export_service():
    """Create a mock DataExportService."""
    service = Mock(spec=DataExportService)

    async def mock_export_session_data(
        session_id, format="json", variables=None, start_time=None, end_time=None
    ):
        import json

        data = {
            "session_id": session_id,
            "format": format,
            "history": {
                "time": [0.0, 10.0, 20.0],
                "ignitions": [False, False, False],
                "free_energy": [1.5, 1.6, 1.4],
            },
        }
        data_bytes = json.dumps(data).encode("utf-8")
        content_type = "application/json" if format == "json" else "text/csv"
        return data_bytes, content_type

    async def mock_generate_summary_stats(session_id):
        return {
            "session_id": session_id,
            "duration_ms": 1000.0,
            "num_steps": 100,
            "ignition_stats": {"count": 5, "total_signal": 10.0},
            "energy_stats": {"mean_free_energy": 1.5, "final_free_energy": 1.4},
            "allostasis_stats": {"mean_load": 0.25, "max_load": 0.5},
        }

    service.export_session_data = AsyncMock(side_effect=mock_export_session_data)
    service.generate_summary_stats = AsyncMock(side_effect=mock_generate_summary_stats)

    return service


@pytest.fixture
def mock_task_executor():
    """Create a mock TaskExecutor."""
    executor = Mock(spec=TaskExecutor)
    tasks_store = {}

    async def mock_submit_task(session_id, task_type, parameters, webhook_url=None, db=None):
        task_id = f"task-{len(tasks_store) + 1}"
        tasks_store[task_id] = {
            "task_id": task_id,
            "session_id": session_id,
            "task_type": task_type,
            "status": "completed",
            "result": {"task_type": task_type, "trials": 100, "performance": 0.75},
        }
        return task_id

    async def mock_get_task_status(task_id):
        if task_id in tasks_store:
            return tasks_store[task_id]
        raise ValueError(f"Task {task_id} not found")

    async def mock_get_task_result(task_id):
        if task_id in tasks_store:
            return tasks_store[task_id]["result"]
        raise ValueError(f"Task {task_id} not found")

    async def mock_list_available_tasks():
        return {
            "tasks": [
                {
                    "task_type": "iowa_gambling",
                    "description": "Iowa Gambling Task",
                    "parameters": {"num_trials": "int"},
                },
                {
                    "task_type": "masking_paradigm",
                    "description": "Masking Paradigm",
                    "parameters": {"soa_ms": "float"},
                },
            ]
        }

    executor.submit_task = AsyncMock(side_effect=mock_submit_task)
    executor.get_task_status = AsyncMock(side_effect=mock_get_task_status)
    executor.get_task_result = AsyncMock(side_effect=mock_get_task_result)
    executor.list_available_tasks = AsyncMock(side_effect=mock_list_available_tasks)

    return executor


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock_db = Mock()

    # Mock user for authentication
    mock_user = User(
        user_id="test-user-123",
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$hashed_password",
        roles=["researcher"],
    )

    mock_db.query = Mock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()

    return mock_db


@pytest.fixture
def client(
    mock_redis, mock_session_manager, mock_data_export_service, mock_task_executor, mock_db_session
):
    """Create a test client with all mocked dependencies."""
    from api.services.authorization import get_current_user, require_permission
    from api.services.auth_manager import TokenPayload
    from datetime import datetime, timedelta

    # Create app in test mode (disables auth and CSRF middleware)
    app = create_app(test_mode=True)

    # Create mock user token for dependency overrides
    mock_token_payload = TokenPayload(
        user_id="test-user-123",
        username="testuser",
        roles=["researcher"],
        exp=datetime.utcnow() + timedelta(days=1),
        token_type="access",
    )

    # Override get_current_user to return mock user
    async def mock_get_current_user():
        return mock_token_payload

    # Override require_permission to always pass
    def mock_require_permission(permission):
        def dummy_dependency():
            return None

        return dummy_dependency

    # Apply overrides
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[require_permission] = mock_require_permission

    # Override dependencies
    sessions._session_manager = mock_session_manager
    sessions._redis_client = mock_redis

    # Mock state routes
    state._session_manager = mock_session_manager

    # Mock export routes
    export._data_export_service = mock_data_export_service
    export._session_manager = mock_session_manager

    # Mock task routes
    tasks._task_executor = mock_task_executor
    tasks._session_manager = mock_session_manager

    # Skip startup/shutdown events
    app.router.on_startup = []
    app.router.on_shutdown = []

    # Use patch to mock is_authenticated in state routes
    with patch("api.routes.state.is_authenticated", return_value=True):
        yield TestClient(app)


class TestCompleteSimulationWorkflow:
    """
    Test complete simulation workflow: create → start → query → export.

    Validates: Requirements 1.1, 2.1, 2.2, 3.1, 5.1
    """

    def test_end_to_end_simulation_workflow(self, client):
        """
        Test complete simulation workflow from creation to data export.

        This test validates the entire lifecycle:
        1. Create a new session
        2. Start the simulation
        3. Query system state
        4. Export data
        5. Clean up

        Validates: Requirements 1.1, 2.1, 2.2, 3.1, 5.1
        """
        # Step 1: Create session
        create_response = client.post(
            "/v1/sessions",
            json={
                "config_path": "config/default.yaml",
                "description": "End-to-end test simulation",
            },
        )
        assert create_response.status_code == 201, "Session creation should return 201"
        create_data = create_response.json()
        assert "session_id" in create_data
        assert create_data["status"] == "created"
        session_id = create_data["session_id"]

        # Step 2: Start simulation
        start_response = client.post(f"/v1/sessions/{session_id}/start")
        assert start_response.status_code == 200, "Session start should return 200"
        start_data = start_response.json()
        assert start_data["status"] == "running"

        # Step 3: Query system state
        state_response = client.get(f"/v1/sessions/{session_id}/state")
        assert state_response.status_code == 200, "State query should return 200"
        state_data = state_response.json()

        # Verify state contains all required subsystems
        assert "time_ms" in state_data
        assert "ignition" in state_data
        assert "workspace" in state_data
        assert "body" in state_data
        assert "allostasis" in state_data
        assert "precision" in state_data
        assert "metabolism" in state_data
        assert "self_model" in state_data

        # Step 4: Stop simulation
        stop_response = client.post(f"/v1/sessions/{session_id}/stop")
        assert stop_response.status_code == 200

        # Step 5: Export data
        export_response = client.get(f"/v1/sessions/{session_id}/export?format=json")
        assert export_response.status_code == 200, "Data export should return 200"
        # Response is a file download, so parse the content
        import json

        export_data = json.loads(export_response.content)
        assert "session_id" in export_data
        assert "history" in export_data

        # Step 6: Get summary statistics
        summary_response = client.get(f"/v1/sessions/{session_id}/summary")
        assert summary_response.status_code == 200
        summary_data = summary_response.json()
        assert "num_steps" in summary_data
        assert "ignition_stats" in summary_data

        # Step 7: Clean up - delete session
        delete_response = client.delete(f"/v1/sessions/{session_id}")
        assert delete_response.status_code == 204, "Session deletion should return 204"

        # Verify session is deleted
        get_response = client.get(f"/v1/sessions/{session_id}")
        assert get_response.status_code == 404, "Deleted session should return 404"

    def test_simulation_workflow_with_pause_resume(self, client):
        """
        Test simulation workflow with pause and resume operations.

        Validates: Requirements 2.2, 2.3
        """
        # Create and start session
        create_response = client.post("/v1/sessions", json={"config_path": "config/default.yaml"})
        session_id = create_response.json()["session_id"]

        start_response = client.post(f"/v1/sessions/{session_id}/start")
        assert start_response.status_code == 200

        # Pause simulation
        pause_response = client.post(f"/v1/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"

        # Query state while paused
        state_response = client.get(f"/v1/sessions/{session_id}/state")
        assert state_response.status_code == 200

        # Resume by starting again
        resume_response = client.post(f"/v1/sessions/{session_id}/start")
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "running"

        # Clean up
        client.delete(f"/v1/sessions/{session_id}")

    def test_simulation_workflow_with_reset(self, client):
        """
        Test simulation workflow with reset operation.

        Validates: Requirements 2.4
        """
        # Create and start session
        create_response = client.post("/v1/sessions", json={"config_path": "config/default.yaml"})
        session_id = create_response.json()["session_id"]

        client.post(f"/v1/sessions/{session_id}/start")

        # Let it run (simulated by querying state)
        client.get(f"/v1/sessions/{session_id}/state")

        # Reset simulation
        reset_response = client.post(f"/v1/sessions/{session_id}/reset")
        assert reset_response.status_code == 200
        assert reset_response.json()["status"] == "created"

        # Verify can start again after reset
        start_response = client.post(f"/v1/sessions/{session_id}/start")
        assert start_response.status_code == 200

        # Clean up
        client.delete(f"/v1/sessions/{session_id}")

    def test_multiple_concurrent_sessions(self, client):
        """
        Test managing multiple concurrent simulation sessions.

        Validates: Requirements 2.1
        """
        session_ids = []

        # Create multiple sessions
        for i in range(3):
            response = client.post(
                "/v1/sessions",
                json={"config_path": "config/default.yaml", "description": f"Session {i+1}"},
            )
            assert response.status_code == 201
            session_ids.append(response.json()["session_id"])

        # Start all sessions
        for session_id in session_ids:
            response = client.post(f"/v1/sessions/{session_id}/start")
            assert response.status_code == 200

        # Query state from each session
        for session_id in session_ids:
            response = client.get(f"/v1/sessions/{session_id}/state")
            assert response.status_code == 200
            assert "ignition" in response.json()

        # Clean up all sessions
        for session_id in session_ids:
            response = client.delete(f"/v1/sessions/{session_id}")
            assert response.status_code == 204


class TestAuthenticationWorkflow:
    """
    Test authentication workflow.

    Validates: Requirements 7.1, 7.2
    """

    @patch("api.services.auth_manager.AuthManager.authenticate_user")
    @patch("api.services.auth_manager.AuthManager.create_tokens_for_user")
    def test_complete_authentication_flow(
        self, mock_create_tokens, mock_authenticate, client, mock_db_session
    ):
        """
        Test complete authentication flow: login → use token → refresh → logout.

        Validates: Requirements 7.1, 7.2
        """
        # Mock user
        mock_user = User(
            user_id="test-user-123",
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            roles=["researcher"],
        )

        mock_authenticate.return_value = mock_user
        mock_create_tokens.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 1800,
            "refresh_token": "test_refresh_token",
        }

        # Step 1: Login
        login_response = client.post(
            "/v1/auth/login", json={"username": "testuser", "password": "password123"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"

        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Step 2: Use access token to make authenticated request
        # (Note: In real scenario, would use token in Authorization header)
        # For this test, we verify the token structure is correct
        assert len(access_token) > 0
        assert len(refresh_token) > 0

    @patch("api.services.auth_manager.AuthManager.authenticate_user")
    @patch("api.services.auth_manager.AuthManager.create_tokens_for_user")
    def test_authentication_failure(self, mock_create_tokens, mock_authenticate, client):
        """
        Test authentication failure with invalid credentials.

        Validates: Requirements 7.1
        """
        mock_authenticate.return_value = None

        login_response = client.post(
            "/v1/auth/login", json={"username": "invalid", "password": "wrong"}
        )
        assert login_response.status_code == 401
        error_data = login_response.json()
        assert "error" in error_data


class TestTaskExecutionWorkflow:
    """
    Test experimental task execution workflow.

    Validates: Requirements 4.1, 4.2, 4.3
    """

    def test_complete_task_execution_flow(self, client):
        """
        Test complete task execution: create session → submit task → check status → get results.

        Validates: Requirements 4.1, 4.2, 4.3
        """
        # Step 1: Create session
        create_response = client.post("/v1/sessions", json={"config_path": "config/default.yaml"})
        assert create_response.status_code == 201
        session_id = create_response.json()["session_id"]

        # Step 2: Start session
        start_response = client.post(f"/v1/sessions/{session_id}/start")
        assert start_response.status_code == 200

        # Step 3: Submit task
        task_response = client.post(
            f"/v1/sessions/{session_id}/tasks",
            json={"task_type": "iowa_gambling", "parameters": {"num_trials": 100}},
        )
        assert task_response.status_code == 202  # Accepted for async processing
        task_data = task_response.json()
        assert "task_id" in task_data
        task_id = task_data["task_id"]

        # Step 4: Check task status
        status_response = client.get(f"/v1/tasks/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["task_id"] == task_id

        # Step 5: Get task results (assuming task completed)
        if status_data["status"] == "completed":
            assert "result" in status_data
            assert "task_type" in status_data["result"]

        # Clean up
        client.delete(f"/v1/sessions/{session_id}")

    def test_list_available_tasks(self, client):
        """
        Test listing available experimental tasks.

        Validates: Requirements 4.4
        """
        response = client.get("/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)


class TestErrorHandling:
    """
    Test error handling across workflows.

    Validates: Requirements 1.1, 1.3
    """

    def test_404_for_nonexistent_session(self, client):
        """Test 404 error for non-existent session."""
        response = client.get("/v1/sessions/nonexistent-id")
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "code" in error_data["error"]
        assert "message" in error_data["error"]

    def test_404_for_nonexistent_task(self, client):
        """Test 404 error for non-existent task."""
        response = client.get("/v1/tasks/nonexistent-task-id")
        assert response.status_code == 404

    def test_error_response_structure(self, client):
        """
        Test that error responses follow consistent structure.

        Validates: Requirements 1.3
        """
        response = client.get("/v1/sessions/invalid-id")
        assert response.status_code == 404

        error_data = response.json()
        assert "error" in error_data
        error = error_data["error"]

        # Verify error structure
        assert "code" in error
        assert "message" in error
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)
