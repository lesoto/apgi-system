"""
Integration tests for task execution routes.

Tests the task API endpoints for submitting and monitoring experimental tasks.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

import api.services.authorization as auth
from api.main import create_app
from api.routes.tasks import init_task_routes
from api.services.auth_manager import TokenPayload
from api.services.authorization import get_current_user, require_permission
from api.services.task_executor import TaskExecutor


@pytest.fixture
def app() -> Any:
    """Create test FastAPI application."""
    # Create app in test mode (disables auth and CSRF middleware)
    app = create_app(test_mode=True)

    # Initialize task routes
    init_task_routes()

    # Create mock user with admin role to pass permission checks
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

    return app


@pytest.fixture
def client(app: Any) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_task_executor() -> Mock:
    """Create mock TaskExecutor."""
    executor = Mock(spec=TaskExecutor)

    # Mock async methods
    executor.submit_task = AsyncMock(return_value="test_task_id_123")
    executor.get_task_status = AsyncMock(
        return_value={"task_id": "test_task_id_123", "status": "pending", "state": "PENDING"}
    )
    executor.get_task_result = AsyncMock(
        return_value={
            "task_type": "iowa_gambling",
            "session_id": "test_session",
            "status": "completed",
            "results": {"total_trials": 100},
        }
    )
    executor.cancel_task = AsyncMock(
        return_value={
            "task_id": "test_task_id_123",
            "status": "cancelled",
            "message": "Task cancellation requested",
        }
    )
    executor.list_available_tasks = AsyncMock(
        return_value={
            "tasks": [
                {
                    "task_type": "iowa_gambling",
                    "name": "Iowa Gambling Task",
                    "description": "Decision-making task",
                    "parameters": {},
                }
            ]
        }
    )

    return executor


class TestTaskRoutes:
    """Test task execution routes."""

    def test_list_tasks(self, client: TestClient, mock_task_executor: Mock) -> None:
        """Test GET /v1/tasks endpoint."""
        with patch("api.routes.tasks._task_executor", mock_task_executor):
            response = client.get("/v1/tasks")

            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) > 0
            assert data["tasks"][0]["task_type"] == "iowa_gambling"

    def test_submit_task(self, client: TestClient, mock_task_executor: Mock) -> None:
        """Test POST /v1/sessions/{session_id}/tasks endpoint."""
        with patch("api.routes.tasks._task_executor", mock_task_executor):
            response = client.post(
                "/v1/sessions/test_session/tasks",
                json={"task_type": "iowa_gambling", "parameters": {"num_trials": 50}},
            )

            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["session_id"] == "test_session"
            assert data["task_type"] == "iowa_gambling"
            assert data["status"] == "pending"
            assert "status_url" in data

    def test_get_task_status(self, client: TestClient, mock_task_executor: Mock) -> None:
        """Test GET /v1/tasks/{task_id} endpoint."""
        with patch("api.routes.tasks._task_executor", mock_task_executor):
            response = client.get("/v1/tasks/test_task_id_123")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["status"] == "pending"

    def test_cancel_task(self, client: TestClient, mock_task_executor: Mock) -> None:
        """Test DELETE /v1/tasks/{task_id} endpoint."""
        with patch("api.routes.tasks._task_executor", mock_task_executor):
            response = client.delete("/v1/tasks/test_task_id_123")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["status"] == "cancelled"


class TestTaskExecutorUnit:
    """Unit tests for TaskExecutor class."""

    def test_task_executor_initialization(self) -> None:
        """Test TaskExecutor initializes correctly."""
        executor = TaskExecutor()
        assert executor.celery is not None

    @pytest.mark.asyncio
    async def test_list_available_tasks(self) -> None:
        """Test listing available tasks."""
        executor = TaskExecutor()
        tasks = await executor.list_available_tasks()

        assert "tasks" in tasks
        assert len(tasks["tasks"]) == 3  # Iowa Gambling, Masking, Attentional Blink

        task_types = [t["task_type"] for t in tasks["tasks"]]
        assert "iowa_gambling" in task_types
        assert "masking_paradigm" in task_types
        assert "attentional_blink" in task_types

    @pytest.mark.asyncio
    async def test_submit_task_invalid_type(self) -> None:
        """Test submitting task with invalid type raises error."""
        executor = TaskExecutor()

        with pytest.raises(ValueError, match="Unknown task type"):
            await executor.submit_task(
                session_id="test_session", task_type="invalid_task", parameters={}
            )


class TestTaskSchemas:
    """Test task-related Pydantic schemas."""

    def test_task_submit_request_schema(self) -> None:
        """Test TaskSubmitRequest schema."""
        from api.models.schemas import TaskSubmitRequest

        request = TaskSubmitRequest(
            task_type="iowa_gambling", parameters={"num_trials": 100}, webhook_url=None
        )

        assert request.task_type == "iowa_gambling"
        assert request.parameters is not None and request.parameters["num_trials"] == 100

    def test_task_submit_response_schema(self) -> None:
        """Test TaskSubmitResponse schema."""
        from api.models.schemas import TaskSubmitResponse

        response = TaskSubmitResponse(
            task_id="task_123",
            session_id="session_456",
            task_type="iowa_gambling",
            status="pending",
            status_url="/v1/tasks/task_123",
        )

        assert response.task_id == "task_123"
        assert response.session_id == "session_456"
        assert response.status == "pending"

    def test_task_status_response_schema(self) -> None:
        """Test TaskStatusResponse schema."""
        from api.models.schemas import TaskStatusResponse

        response = TaskStatusResponse(
            task_id="task_123",
            status="completed",
            state="SUCCESS",
            result={"total_trials": 100},
            error=None,
            info=None,
        )

        assert response.task_id == "task_123"
        assert response.status == "completed"
        assert response.result is not None and response.result["total_trials"] == 100
