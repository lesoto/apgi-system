"""
Tests for API Data Models

Basic tests to verify Pydantic models and SQLAlchemy models work correctly.
"""

from datetime import datetime

import pytest

from api.models import (
    AllostaticState,
    BodyState,
    ErrorResponse,
    IgnitionState,
    MetabolicState,
    MinimalSelfState,
    NarrativeSelfState,
    PrecisionState,
    SelfModelState,
    SessionCreateRequest,
    SessionCreateResponse,
    SystemStateResponse,
    TaskExecuteRequest,
    TaskResult,
    TaskStatusEnum,
    WorkspaceState,
)


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_session_create_request_minimal(self) -> None:
        """Test SessionCreateRequest with minimal data."""
        request = SessionCreateRequest(
            config_path="config/default.yaml", custom_config=None, description=None
        )
        assert request.config_path == "config/default.yaml"
        assert request.custom_config is None
        assert request.description is None

    def test_session_create_request_full(self) -> None:
        """Test SessionCreateRequest with all fields."""
        request = SessionCreateRequest(
            config_path="config/default.yaml",
            custom_config={"timestep_ms": 10.0},
            description="Test session",
        )
        assert request.config_path == "config/default.yaml"
        assert request.custom_config == {"timestep_ms": 10.0}
        assert request.description == "Test session"

    def test_session_create_response(self) -> None:
        """Test SessionCreateResponse."""
        response = SessionCreateResponse(
            session_id="test-123",
            status="created",
            created_at=datetime.utcnow(),
            config={"timestep_ms": 10.0},
        )
        assert response.session_id == "test-123"
        assert response.status == "created"
        assert response.config == {"timestep_ms": 10.0}

    def test_system_state_response(self) -> None:
        """Test SystemStateResponse with nested models."""
        state = SystemStateResponse(
            time_ms=5000.0,
            ignition=IgnitionState(
                ignition_occurred=True, total_signal=2.5, threshold=2.0, duration_ms=350.0
            ),
            workspace=WorkspaceState(
                is_broadcasting=True, content="sensory", broadcast_duration_ms=350.0
            ),
            body=BodyState(heart_rate=75.0, cortisol=0.15, temperature=37.0),
            allostasis=AllostaticState(allostatic_load=0.3),
            precision=PrecisionState(exteroceptive=1.2, interoceptive=0.8),
            metabolism=MetabolicState(reserves=850.0, reserve_fraction=0.85),
            self_model=SelfModelState(
                minimal=MinimalSelfState(coherence=0.75), narrative=NarrativeSelfState(active=True)
            ),
        )

        assert state.time_ms == 5000.0
        assert state.ignition.ignition_occurred is True
        assert state.workspace.is_broadcasting is True
        assert state.body.heart_rate == 75.0
        assert state.allostasis.allostatic_load == 0.3
        assert state.precision.exteroceptive == 1.2
        assert state.metabolism.reserves == 850.0
        assert state.self_model.minimal.coherence == 0.75

    def test_task_execute_request(self) -> None:
        """Test TaskExecuteRequest."""
        request = TaskExecuteRequest(
            task_type="iowa_gambling", parameters={"num_trials": 100}, webhook_url=None
        )
        assert request.task_type == "iowa_gambling"
        assert request.parameters == {"num_trials": 100}
        assert request.webhook_url is None

    def test_task_result(self) -> None:
        """Test TaskResult."""
        result = TaskResult(
            task_id="task-123",
            status=TaskStatusEnum.COMPLETED,
            progress=100,
            result_data={"summary": {"score": 0.65}},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=None,
        )
        assert result.task_id == "task-123"
        assert result.status == TaskStatusEnum.COMPLETED
        assert result.progress == 100
        assert result.result_data == {"summary": {"score": 0.65}}

    def test_error_response(self) -> None:
        """Test ErrorResponse."""
        error = ErrorResponse(
            error={
                "code": "SESSION_NOT_FOUND",
                "message": "Session not found",
                "request_id": "req-123",
                "timestamp": "2025-12-03T10:30:00Z",
                "details": {"session_id": "abc123"},
            }
        )
        assert error.error["code"] == "SESSION_NOT_FOUND"
        assert error.error["message"] == "Session not found"

    def test_model_json_serialization(self) -> None:
        """Test that models can be serialized to JSON."""
        request = SessionCreateRequest(
            config_path="config/default.yaml", custom_config=None, description="Test"
        )
        json_data = request.model_dump_json()
        assert isinstance(json_data, str)
        assert "config/default.yaml" in json_data

    def test_model_validation_error(self) -> None:
        """Test that invalid data raises validation error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            # Missing required fields
            SystemStateResponse(time_ms=5000.0)  # type: ignore[call-arg]


class TestSQLAlchemyModels:
    """Test SQLAlchemy database models."""

    def test_user_model_structure(self) -> None:
        """Test User model structure."""
        # Import directly from models to avoid connection issues
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("models", "api/database/models.py")
        if spec is None or spec.loader is None:
            pytest.skip("Cannot load models module")
        models = importlib.util.module_from_spec(spec)
        sys.modules["models"] = models
        spec.loader.exec_module(models)

        User = models.User

        user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
            roles=["researcher"],
        )

        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.roles == ["researcher"]

    def test_session_model_structure(self) -> None:
        """Test Session model structure."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("models", "api/database/models.py")
        if spec is None or spec.loader is None:
            pytest.skip("Cannot load models module")
        models = importlib.util.module_from_spec(spec)
        sys.modules["models"] = models
        spec.loader.exec_module(models)

        Session = models.Session

        session = Session(
            session_id="session-123",
            user_id="user-123",
            config={"timestep_ms": 10.0},
            state="created",
        )

        assert session.session_id == "session-123"
        assert session.user_id == "user-123"
        assert session.config == {"timestep_ms": 10.0}
        assert session.state == "created"

    def test_task_model_structure(self) -> None:
        """Test Task model structure."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("models", "api/database/models.py")
        if spec is None or spec.loader is None:
            pytest.skip("Cannot load models module")
        models = importlib.util.module_from_spec(spec)
        sys.modules["models"] = models
        spec.loader.exec_module(models)

        Task = models.Task

        task = Task(
            task_id="task-123",
            session_id="session-123",
            task_type="iowa_gambling",
            parameters={"num_trials": 100},
            status="pending",
        )

        assert task.task_id == "task-123"
        assert task.session_id == "session-123"
        assert task.task_type == "iowa_gambling"
        assert task.status == "pending"

    def test_session_data_model_structure(self) -> None:
        """Test SessionData model structure."""
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location("models", "api/database/models.py")
        if spec is None or spec.loader is None:
            pytest.skip("Cannot load models module")
        models = importlib.util.module_from_spec(spec)
        sys.modules["models"] = models
        spec.loader.exec_module(models)

        SessionData = models.SessionData

        data = SessionData(
            session_id="session-123", time_ms=5000.0, data={"ignition": {"ignition_occurred": True}}
        )

        assert data.session_id == "session-123"
        assert data.time_ms == 5000.0
        assert data.data == {"ignition": {"ignition_occurred": True}}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
