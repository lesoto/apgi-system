"""
Integration tests for task execution routes.

Tests the task API endpoints for submitting and monitoring experimental tasks.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from api.main import create_app
from api.services.task_executor import TaskExecutor, TaskType, TaskStatus


@pytest.fixture
def app():
    """Create test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_task_executor():
    """Create mock TaskExecutor."""
    executor = Mock(spec=TaskExecutor)
    
    # Mock async methods
    executor.submit_task = AsyncMock(return_value="test_task_id_123")
    executor.get_task_status = AsyncMock(return_value={
        "task_id": "test_task_id_123",
        "status": "pending",
        "state": "PENDING"
    })
    executor.get_task_result = AsyncMock(return_value={
        "task_type": "iowa_gambling",
        "session_id": "test_session",
        "status": "completed",
        "results": {"total_trials": 100}
    })
    executor.cancel_task = AsyncMock(return_value={
        "task_id": "test_task_id_123",
        "status": "cancelled",
        "message": "Task cancellation requested"
    })
    executor.list_available_tasks = Mock(return_value={
        "tasks": [
            {
                "task_type": "iowa_gambling",
                "name": "Iowa Gambling Task",
                "description": "Decision-making task",
                "parameters": {}
            }
        ]
    })
    
    return executor


class TestTaskRoutes:
    """Test task execution routes."""
    
    def test_list_tasks(self, client, mock_task_executor):
        """Test GET /v1/tasks endpoint."""
        with patch('api.routes.tasks._task_executor', mock_task_executor):
            response = client.get("/v1/tasks")
            
            assert response.status_code == 200
            data = response.json()
            assert "tasks" in data
            assert len(data["tasks"]) > 0
            assert data["tasks"][0]["task_type"] == "iowa_gambling"
    
    def test_submit_task(self, client, mock_task_executor):
        """Test POST /v1/sessions/{session_id}/tasks endpoint."""
        with patch('api.routes.tasks._task_executor', mock_task_executor):
            response = client.post(
                "/v1/sessions/test_session/tasks",
                json={
                    "task_type": "iowa_gambling",
                    "parameters": {"num_trials": 50}
                }
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["session_id"] == "test_session"
            assert data["task_type"] == "iowa_gambling"
            assert data["status"] == "pending"
            assert "status_url" in data
    
    def test_get_task_status(self, client, mock_task_executor):
        """Test GET /v1/tasks/{task_id} endpoint."""
        with patch('api.routes.tasks._task_executor', mock_task_executor):
            response = client.get("/v1/tasks/test_task_id_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["status"] == "pending"
    
    def test_cancel_task(self, client, mock_task_executor):
        """Test DELETE /v1/tasks/{task_id} endpoint."""
        with patch('api.routes.tasks._task_executor', mock_task_executor):
            response = client.delete("/v1/tasks/test_task_id_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "test_task_id_123"
            assert data["status"] == "cancelled"


class TestTaskExecutorUnit:
    """Unit tests for TaskExecutor class."""
    
    def test_task_executor_initialization(self):
        """Test TaskExecutor initializes correctly."""
        executor = TaskExecutor()
        assert executor.celery is not None
    
    def test_list_available_tasks(self):
        """Test listing available tasks."""
        executor = TaskExecutor()
        tasks = executor.list_available_tasks()
        
        assert "tasks" in tasks
        assert len(tasks["tasks"]) == 3  # Iowa Gambling, Masking, Attentional Blink
        
        task_types = [t["task_type"] for t in tasks["tasks"]]
        assert "iowa_gambling" in task_types
        assert "masking_paradigm" in task_types
        assert "attentional_blink" in task_types
    
    @pytest.mark.asyncio
    async def test_submit_task_invalid_type(self):
        """Test submitting task with invalid type raises error."""
        executor = TaskExecutor()
        
        with pytest.raises(ValueError, match="Unknown task type"):
            await executor.submit_task(
                session_id="test_session",
                task_type="invalid_task",
                parameters={}
            )


class TestTaskSchemas:
    """Test task-related Pydantic schemas."""
    
    def test_task_submit_request_schema(self):
        """Test TaskSubmitRequest schema."""
        from api.models.schemas import TaskSubmitRequest
        
        request = TaskSubmitRequest(
            task_type="iowa_gambling",
            parameters={"num_trials": 100}
        )
        
        assert request.task_type == "iowa_gambling"
        assert request.parameters["num_trials"] == 100
    
    def test_task_submit_response_schema(self):
        """Test TaskSubmitResponse schema."""
        from api.models.schemas import TaskSubmitResponse
        
        response = TaskSubmitResponse(
            task_id="task_123",
            session_id="session_456",
            task_type="iowa_gambling",
            status="pending",
            status_url="/v1/tasks/task_123"
        )
        
        assert response.task_id == "task_123"
        assert response.session_id == "session_456"
        assert response.status == "pending"
    
    def test_task_status_response_schema(self):
        """Test TaskStatusResponse schema."""
        from api.models.schemas import TaskStatusResponse
        
        response = TaskStatusResponse(
            task_id="task_123",
            status="completed",
            state="SUCCESS",
            result={"total_trials": 100}
        )
        
        assert response.task_id == "task_123"
        assert response.status == "completed"
        assert response.result["total_trials"] == 100
