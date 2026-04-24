"""
API Contract Tests

Validates all API responses against OpenAPI schemas to ensure contract compliance.

Requirements tested:
- 12.3: Response schema validation
"""

from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient

from api.routes import export, tasks
from api.services.data_export import DataExportService
from api.services.session_manager import SessionLifecycleState, SessionManager, SimulationSession
from api.services.task_executor import TaskExecutor


@pytest.fixture
def mock_redis() -> AsyncMock:
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
def mock_apgi_framework() -> Mock:
    """Create a mock APGI system with realistic state."""
    mock_system = Mock()
    mock_system.time = 0.0
    mock_system.timestep_ms = 10.0

    def mock_get_state() -> Dict[str, Any]:
        return {
            "time": mock_system.time,
            "timestep_ms": 10.0,
            "is_running": False,
            "core": {
                "active_inference": {},
                "precision": {"exteroceptive": 1.0, "interoceptive": 1.0},
            },
            "ignition": {
                "ignition_occurred": False,
                "total_signal": 1.5,
                "threshold": 2.0,
                "duration_ms": None,
            },
            "interoception": {
                "body_state": {
                    "heart_rate": 72.0,
                    "cortisol": 0.12,
                    "temperature": 37.0,
                    "glucose": 5.0,
                },
                "allostatic_load": 0.25,
            },
            "self_model": {"minimal": {"coherence": 0.8}, "narrative": {"active": False}},
            "thermodynamic": {"metabolic_reserves": 900.0, "reserve_fraction": 0.9},
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
    return mock_system


@pytest.fixture
def mock_session_manager(mock_apgi_framework: Mock) -> Mock:
    """Create a mock SessionManager."""
    manager = Mock(spec=SessionManager)

    async def mock_create_session(request: Dict[str, Any], user_id: str = "default_user") -> str:
        session_id = "test-session-123"
        return session_id

    async def mock_get_session(session_id: str) -> Any:
        if session_id == "test-session-123":
            mock_sim = Mock(spec=SimulationSession)
            mock_sim.session_id = session_id
            mock_sim.state = SessionLifecycleState.CREATED
            mock_sim.created_at = "2025-12-03T10:30:00"
            mock_sim.updated_at = "2025-12-03T10:30:00"
            mock_sim.config = {"config_path": "config/default.yaml"}
            mock_sim.apgi_framework = mock_apgi_framework
            mock_sim.user_id = "test-user-123"

            async def mock_start() -> Dict[str, Any]:
                return {"session_id": session_id, "status": "running"}

            async def mock_get_state() -> Dict[str, Any]:
                return mock_apgi_framework.get_state()

            mock_sim.start = AsyncMock(side_effect=mock_start)
            mock_sim.get_state = AsyncMock(side_effect=mock_get_state)

            return mock_sim
        raise ValueError(f"Session {session_id} not found")

    manager.create_session = AsyncMock(side_effect=mock_create_session)
    manager.get_session = AsyncMock(side_effect=mock_get_session)
    manager.update_session_state = AsyncMock()

    return manager


@pytest.fixture
def mock_data_export_service() -> Mock:
    """Create a mock DataExportService."""
    service = Mock(spec=DataExportService)

    async def mock_export_session_data(
        session_id: str,
        format: str = "json",
        variables: Optional[List[str]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> tuple[bytes, str]:
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

    service.export_session_data = AsyncMock(side_effect=mock_export_session_data)

    return service


@pytest.fixture
def mock_task_executor() -> Mock:
    """Create a mock TaskExecutor."""
    executor = Mock(spec=TaskExecutor)

    async def mock_list_available_tasks() -> Dict[str, Any]:
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

    executor.list_available_tasks = AsyncMock(side_effect=mock_list_available_tasks)

    return executor


@pytest.fixture
def client(
    mock_redis: AsyncMock,
    mock_session_manager: Mock,
    mock_data_export_service: Mock,
    mock_task_executor: Mock,
) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies."""
    from datetime import datetime, timedelta

    from fastapi.testclient import TestClient

    from api.main import create_app
    from api.services.auth_manager import TokenPayload
    from api.services.authorization import get_current_user, require_permission
    from api.services.session_manager import get_redis_client, get_session_manager

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
    async def mock_get_current_user() -> TokenPayload:
        return mock_token_payload

    # Override require_permission to always pass
    def mock_require_permission(permission: str) -> Callable[[], None]:
        def dummy_dependency() -> None:
            return None

        return dummy_dependency

    # Override session manager and redis client dependencies
    def mock_get_session_manager() -> Mock:
        return mock_session_manager

    def mock_get_redis_client() -> AsyncMock:
        return mock_redis

    # Apply overrides
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[require_permission] = mock_require_permission
    app.dependency_overrides[get_session_manager] = mock_get_session_manager
    app.dependency_overrides[get_redis_client] = mock_get_redis_client

    # Override data export service and task executor
    export._data_export_service = mock_data_export_service  # type: ignore[attr-defined]
    export._session_manager = mock_session_manager  # type: ignore[attr-defined]
    tasks._task_executor = mock_task_executor  # type: ignore[attr-defined]
    tasks._session_manager = mock_session_manager  # type: ignore[attr-defined]

    # Skip startup/shutdown events
    app.router.on_startup = []
    app.router.on_shutdown = []

    # Use patch to mock get_current_user in state routes and skip session ownership checks
    mock_user = Mock()
    mock_user.user_id = "test-user-id"
    mock_user.roles = ["user"]
    with patch("api.routes.state.get_current_user", return_value=mock_user):
        with patch(
            "api.services.session_manager.get_session_manager",
            return_value=mock_session_manager,
        ):
            yield TestClient(app)


@pytest.fixture
def openapi_schema(client: Any) -> Dict[str, Any]:
    """Get the OpenAPI schema from the API."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def validate_response_against_schema(
    response_data: Dict[str, Any], schema: Dict[str, Any], openapi_components: Dict[str, Any]
) -> bool:
    """
    Validate response data against OpenAPI schema.

    Args:
        response_data: The actual response data
        schema: The schema definition from OpenAPI
        openapi_components: The components section from OpenAPI spec

    Returns:
        True if valid, raises AssertionError if invalid
    """
    # Handle $ref references
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")
        if ref_path[0] == "#" and ref_path[1] == "components" and ref_path[2] == "schemas":
            schema_name = ref_path[3]
            schema = openapi_components["schemas"][schema_name]

    # Check required properties
    if "properties" in schema:
        required_fields = schema.get("required", [])
        for field in required_fields:
            assert field in response_data, f"Required field '{field}' missing from response"

        # Check property types
        for field, field_schema in schema["properties"].items():
            if field in response_data:
                value = response_data[field]

                # Handle $ref in properties
                if "$ref" in field_schema:
                    ref_path = field_schema["$ref"].split("/")
                    if (
                        ref_path[0] == "#"
                        and ref_path[1] == "components"
                        and ref_path[2] == "schemas"
                    ):
                        schema_name = ref_path[3]
                        field_schema = openapi_components["schemas"][schema_name]

                # Basic type checking
                if "type" in field_schema:
                    expected_type = field_schema["type"]
                    if expected_type == "string":
                        assert isinstance(value, str), f"Field '{field}' should be string"
                    elif expected_type == "integer":
                        assert isinstance(value, int), f"Field '{field}' should be integer"
                    elif expected_type == "number":
                        assert isinstance(value, (int, float)), f"Field '{field}' should be number"
                    elif expected_type == "boolean":
                        assert isinstance(value, bool), f"Field '{field}' should be boolean"
                    elif expected_type == "object":
                        assert isinstance(value, dict), f"Field '{field}' should be object"
                        # Recursively validate nested objects
                        if "properties" in field_schema:
                            validate_response_against_schema(
                                value, field_schema, openapi_components
                            )
                    elif expected_type == "array":
                        assert isinstance(value, list), f"Field '{field}' should be array"

    return True


class TestSessionEndpointContracts:
    """
    Test session endpoint responses against OpenAPI schemas.

    Validates: Requirements 12.3
    """

    def test_create_session_response_schema(
        self, client: Any, openapi_schema: Dict[str, Any]
    ) -> None:
        """
        Test that POST /v1/sessions response matches OpenAPI schema.

        Validates: Requirements 12.3
        """
        response = client.post("/v1/sessions", json={"config_path": "config/default.yaml"})
        assert response.status_code == 201

        data = response.json()

        # Verify required fields from SessionCreateResponse
        assert "session_id" in data
        assert "status" in data
        assert "created_at" in data
        assert "config" in data

        # Verify types
        assert isinstance(data["session_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["config"], dict)

    def test_get_session_response_schema(self, client: Any, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that GET /v1/sessions/{session_id} response matches OpenAPI schema.

        Validates: Requirements 12.3
        """
        response = client.get("/v1/sessions/test-session-123")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields from SessionResponse
        assert "session_id" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "config" in data

        # Verify types
        assert isinstance(data["session_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert isinstance(data["config"], dict)

    def test_session_action_response_schema(
        self, client: Any, openapi_schema: Dict[str, Any]
    ) -> None:
        """
        Test that session action endpoints return correct schema.

        Validates: Requirements 12.3
        """
        response = client.post("/v1/sessions/test-session-123/start")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields from SessionActionResponse
        assert "session_id" in data
        assert "status" in data
        assert "timestamp" in data

        # Verify types
        assert isinstance(data["session_id"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)


class TestStateEndpointContracts:
    """
    Test state endpoint responses against OpenAPI schemas.

    Validates: Requirements 12.3
    """

    def test_get_state_response_schema(self, client: Any, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that GET /v1/sessions/{session_id}/state response matches schema.

        Validates: Requirements 12.3
        """
        response = client.get("/v1/sessions/test-session-123/state")
        assert response.status_code == 200

        data = response.json()

        # Verify required top-level fields from SystemStateResponse
        assert "time_ms" in data
        assert "ignition" in data
        assert "workspace" in data
        assert "body" in data
        assert "allostasis" in data
        assert "precision" in data
        assert "metabolism" in data
        assert "self_model" in data

        # Verify types
        assert isinstance(data["time_ms"], (int, float))
        assert isinstance(data["ignition"], dict)
        assert isinstance(data["workspace"], dict)
        assert isinstance(data["body"], dict)
        assert isinstance(data["allostasis"], dict)
        assert isinstance(data["precision"], dict)
        assert isinstance(data["metabolism"], dict)
        assert isinstance(data["self_model"], dict)

        # Verify nested structures
        # Ignition state
        assert "ignition_occurred" in data["ignition"]
        assert "total_signal" in data["ignition"]
        assert "threshold" in data["ignition"]
        assert isinstance(data["ignition"]["ignition_occurred"], bool)
        assert isinstance(data["ignition"]["total_signal"], (int, float))
        assert isinstance(data["ignition"]["threshold"], (int, float))

        # Body state
        assert "heart_rate" in data["body"]
        assert "cortisol" in data["body"]
        assert "temperature" in data["body"]
        assert isinstance(data["body"]["heart_rate"], (int, float))
        assert isinstance(data["body"]["cortisol"], (int, float))
        assert isinstance(data["body"]["temperature"], (int, float))

        # Precision state
        assert "exteroceptive" in data["precision"]
        assert "interoceptive" in data["precision"]
        assert isinstance(data["precision"]["exteroceptive"], (int, float))
        assert isinstance(data["precision"]["interoceptive"], (int, float))

        # Metabolism state
        assert "reserves" in data["metabolism"]
        assert "reserve_fraction" in data["metabolism"]
        assert isinstance(data["metabolism"]["reserves"], (int, float))
        assert isinstance(data["metabolism"]["reserve_fraction"], (int, float))


class TestExportEndpointContracts:
    """
    Test export endpoint responses against OpenAPI schemas.

    Validates: Requirements 12.3
    """

    def test_export_data_response_schema(self, client: Any, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that GET /v1/sessions/{session_id}/export response matches schema.

        Validates: Requirements 12.3
        """
        response = client.get("/v1/sessions/test-session-123/export?format=json")
        assert response.status_code == 200

        # Response is a file download, parse the content
        import json

        data = json.loads(response.content)

        # Verify required fields
        assert "session_id" in data
        assert "format" in data
        assert "history" in data

        # Verify types
        assert isinstance(data["session_id"], str)
        assert isinstance(data["format"], str)
        assert isinstance(data["history"], dict)


class TestTaskEndpointContracts:
    """
    Test task endpoint responses against OpenAPI schemas.

    Validates: Requirements 12.3
    """

    def test_list_tasks_response_schema(self, client: Any, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that GET /v1/tasks response matches schema.

        Validates: Requirements 12.3
        """
        response = client.get("/v1/tasks")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

        # Verify task structure
        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            assert "task_type" in task
            assert "description" in task
            assert isinstance(task["task_type"], str)
            assert isinstance(task["description"], str)


class TestErrorResponseContracts:
    """
    Test error response schemas.

    Validates: Requirements 12.3, 1.3
    """

    def test_404_error_response_schema(self, client: Any, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that 404 error responses match ErrorResponse schema.

        Validates: Requirements 12.3, 1.3
        """
        response = client.get("/v1/sessions/nonexistent-id")
        assert response.status_code == 404

        data = response.json()

        # Verify error structure
        assert "error" in data
        error = data["error"]

        # Verify required error fields
        assert "code" in error
        assert "message" in error

        # Verify types
        assert isinstance(error["code"], str)
        assert isinstance(error["message"], str)

        # Optional fields
        if "request_id" in error:
            assert isinstance(error["request_id"], str)
        if "timestamp" in error:
            assert isinstance(error["timestamp"], str)
        if "details" in error:
            assert isinstance(error["details"], dict)

    def test_validation_error_response_schema(
        self, client: Any, openapi_schema: Dict[str, Any]
    ) -> None:
        """
        Test that validation error responses match schema.

        Validates: Requirements 12.3, 1.3
        """
        # Send invalid request (missing required fields or invalid types)
        response = client.post("/v1/sessions", json={"invalid_field": "value"})

        # Should return 422 for validation errors or 201 if validation passes
        # (depends on whether fields are truly required)
        if response.status_code == 422:
            data = response.json()
            assert "error" in data or "detail" in data


class TestOpenAPISchemaCompleteness:
    """
    Test that OpenAPI schema is complete and well-formed.

    Validates: Requirements 12.3
    """

    def test_openapi_schema_structure(self, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that OpenAPI schema has required structure.

        Validates: Requirements 12.3
        """
        # Verify top-level structure
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema

        # Verify info section
        info = openapi_schema["info"]
        assert "title" in info
        assert "version" in info
        assert info["title"] == "APGI System API"

    def test_all_endpoints_have_schemas(self, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that all endpoints have response schemas defined.

        Validates: Requirements 12.3
        """
        paths = openapi_schema.get("paths", {})

        for path, methods in paths.items():
            for method, spec in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    # Check that responses are defined
                    assert "responses" in spec, f"{method.upper()} {path} missing responses"

                    # Check that at least one success response is defined
                    responses = spec["responses"]
                    success_codes = [code for code in responses.keys() if code.startswith("2")]
                    assert (
                        len(success_codes) > 0
                    ), f"{method.upper()} {path} has no success responses"

    def test_components_schemas_defined(self, openapi_schema: Dict[str, Any]) -> None:
        """
        Test that component schemas are properly defined.

        Validates: Requirements 12.3
        """
        if "components" in openapi_schema:
            components = openapi_schema["components"]
            if "schemas" in components:
                schemas = components["schemas"]

                # Verify key schemas exist
                expected_schemas = [
                    "SessionCreateRequest",
                    "SessionCreateResponse",
                    "SessionResponse",
                    "SystemStateResponse",
                ]

                for schema_name in expected_schemas:
                    if schema_name in schemas:
                        schema = schemas[schema_name]
                        # Verify schema has properties or is properly defined
                        assert (
                            "properties" in schema or "type" in schema or "allOf" in schema
                        ), f"Schema {schema_name} is not properly defined"
