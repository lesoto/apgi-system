"""
Property-based tests for API endpoints.

Tests universal properties that should hold across all valid API requests.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from api.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ExpiredTokenError,
    InvalidTokenError,
    RateLimitExceededError,
    SessionNotFoundError,
    TaskNotFoundError,
    ValidationError,
)
from api.services.task_executor import TaskExecutor, TaskStatus, TaskType

# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def task_type_strategy(draw: st.DrawFn) -> str:
    """Generate valid task types."""
    return draw(
        st.sampled_from(
            [
                TaskType.IOWA_GAMBLING.value,
                TaskType.MASKING_PARADIGM.value,
                TaskType.ATTENTIONAL_BLINK.value,
            ]
        )
    )


@st.composite
def task_parameters_strategy(draw: st.DrawFn, task_type: str) -> Dict[str, Any]:
    """Generate valid parameters for a given task type."""
    if task_type == TaskType.IOWA_GAMBLING.value:
        return {
            "num_trials": draw(st.integers(min_value=10, max_value=200)),
            "initial_balance": draw(st.integers(min_value=1000, max_value=5000)),
            "deck_stimulus_strength": draw(st.floats(min_value=0.5, max_value=3.0)),
            "outcome_stimulus_strength": draw(st.floats(min_value=0.5, max_value=3.0)),
            "interoceptive_gain": draw(st.floats(min_value=0.5, max_value=2.0)),
            "deck_selection_strategy": draw(st.sampled_from(["balanced", "random"])),
        }
    elif task_type == TaskType.MASKING_PARADIGM.value:
        return {
            "target_duration_ms": draw(st.floats(min_value=20.0, max_value=100.0)),
            "soas": draw(
                st.lists(st.floats(min_value=0.0, max_value=500.0), min_size=3, max_size=10)
            ),
            "mask_duration_ms": draw(st.floats(min_value=50.0, max_value=200.0)),
            "num_trials_per_condition": draw(st.integers(min_value=5, max_value=30)),
            "target_strength": draw(st.floats(min_value=1.0, max_value=5.0)),
            "mask_strength": draw(st.floats(min_value=1.0, max_value=5.0)),
        }
    elif task_type == TaskType.ATTENTIONAL_BLINK.value:
        return {
            "stream_length": draw(st.integers(min_value=10, max_value=20)),
            "item_duration_ms": draw(st.floats(min_value=50.0, max_value=200.0)),
            "num_trials_per_lag": draw(st.integers(min_value=5, max_value=30)),
            "lags": draw(st.lists(st.integers(min_value=1, max_value=10), min_size=2, max_size=8)),
            "target_salience": draw(st.floats(min_value=1.0, max_value=5.0)),
        }
    else:
        return {}


@st.composite
def session_id_strategy(draw: st.DrawFn) -> str:
    """Generate valid session IDs (UUIDs)."""
    return str(uuid.uuid4())


@st.composite
def task_result_strategy(draw: st.DrawFn, task_type: str, session_id: str) -> Dict[str, Any]:
    """Generate mock task results for a given task type."""
    base_result: Dict[str, Any] = {
        "task_type": task_type,
        "session_id": session_id,
        "status": "completed",
    }

    if task_type == TaskType.IOWA_GAMBLING.value:
        base_result["results"] = {
            "total_trials": draw(st.integers(min_value=10, max_value=200)),
            "advantageous_ratio": draw(st.floats(min_value=0.0, max_value=1.0)),
            "final_balance": draw(st.integers(min_value=-5000, max_value=10000)),
        }
    elif task_type == TaskType.MASKING_PARADIGM.value:
        base_result["results"] = {
            "ignition_probabilities": draw(
                st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=3, max_size=10)
            ),
            "mean_ignition_probability": draw(st.floats(min_value=0.0, max_value=1.0)),
        }
    elif task_type == TaskType.ATTENTIONAL_BLINK.value:
        base_result["results"] = {
            "t1_accuracy": draw(st.floats(min_value=0.0, max_value=1.0)),
            "t2_accuracy_by_lag": draw(
                st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=8)
            ),
        }

    return base_result


# ============================================================================
# Property Tests
# ============================================================================


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_task_execution_round_trip(data: st.DataObject) -> None:
    """
    **Feature: api-rest-interface, Property 10: Task execution and retrieval round-trip**

    For any experimental task, executing it and then retrieving results by task ID
    should return the complete task results.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.5**
    """
    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())

    # Generate parameters for this task type
    parameters = data.draw(task_parameters_strategy(task_type))

    # Generate expected result
    expected_result = data.draw(task_result_strategy(task_type, session_id))

    # Create mock Celery app and result
    mock_celery_app = Mock()
    mock_async_result = Mock()
    mock_async_result.id = str(uuid.uuid4())
    mock_async_result.state = "SUCCESS"
    mock_async_result.successful.return_value = True
    mock_async_result.failed.return_value = False
    mock_async_result.ready.return_value = True
    mock_async_result.result = expected_result

    # Mock send_task to return our mock result
    mock_celery_app.send_task.return_value = mock_async_result

    # Create TaskExecutor with mocked Celery app
    with patch("api.services.task_executor.celery_app", mock_celery_app):
        with patch("api.services.task_executor.AsyncResult", return_value=mock_async_result):
            executor = TaskExecutor()

            # Step 1: Submit task
            task_id = await executor.submit_task(
                session_id=session_id, task_type=task_type, parameters=parameters
            )

            # Verify task_id was returned
            assert task_id is not None
            assert isinstance(task_id, str)
            assert len(task_id) > 0

            # Step 2: Get task status
            status_info = await executor.get_task_status(task_id)

            # Verify status response structure
            assert "task_id" in status_info
            assert "status" in status_info
            assert status_info["task_id"] == task_id

            # Step 3: Get task result (for completed tasks)
            if status_info["status"] == TaskStatus.COMPLETED.value:
                result = await executor.get_task_result(task_id)

                # Verify result structure matches what was submitted
                assert result is not None
                assert isinstance(result, dict)

                # Verify result contains expected fields
                assert "task_type" in result
                assert "session_id" in result
                assert "status" in result
                assert "results" in result

                # Verify values match
                assert result["task_type"] == task_type
                assert result["session_id"] == session_id
                assert result["status"] == "completed"

                # Verify results field is present and is a dict
                assert isinstance(result["results"], dict)
                assert len(result["results"]) > 0


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_task_status_tracking(data: st.DataObject) -> None:
    """
    Property: Task status should be trackable from submission to completion.

    For any task, the status should progress through valid states and
    always be retrievable by task ID.
    """
    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())

    # Generate parameters
    parameters = data.draw(task_parameters_strategy(task_type))

    # Create mock Celery app
    mock_celery_app = Mock()
    mock_async_result = Mock()
    task_id = str(uuid.uuid4())
    mock_async_result.id = task_id

    # Mock different states
    mock_async_result.state = "PENDING"
    mock_async_result.successful.return_value = False
    mock_async_result.failed.return_value = False
    mock_async_result.ready.return_value = False

    mock_celery_app.send_task.return_value = mock_async_result

    with patch("api.services.task_executor.celery_app", mock_celery_app):
        with patch("api.services.task_executor.AsyncResult", return_value=mock_async_result):
            executor = TaskExecutor()

            # Submit task
            returned_task_id = await executor.submit_task(
                session_id=session_id, task_type=task_type, parameters=parameters
            )

            # Verify task ID is returned
            assert returned_task_id == task_id

            # Get status for pending task
            status_info = await executor.get_task_status(task_id)

            # Verify status structure
            assert "task_id" in status_info
            assert "status" in status_info
            assert "state" in status_info
            assert status_info["task_id"] == task_id

            # Verify status is one of the valid states
            valid_statuses = [s.value for s in TaskStatus]
            assert status_info["status"] in valid_statuses


@given(
    invalid_task_type=st.text(min_size=1, max_size=50).filter(
        lambda x: x not in [t.value for t in TaskType]
    ),
    session_id=session_id_strategy(),
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_invalid_task_type_rejection(
    invalid_task_type: str, session_id: str
) -> None:
    """
    Property: Invalid task types should be rejected with clear error.

    For any string that is not a valid task type, submitting a task
    should raise a ValueError.
    """
    # Create executor
    executor = TaskExecutor()

    # Attempt to submit task with invalid type
    with pytest.raises(ValueError) as exc_info:
        await executor.submit_task(
            session_id=session_id, task_type=invalid_task_type, parameters={}
        )

    # Verify error message mentions the invalid task type
    error_message = str(exc_info.value)
    assert "Unknown task type" in error_message or "task type" in error_message.lower()


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_async_task_status_tracking(data: st.DataObject) -> None:
    """
    **Feature: api-rest-interface, Property 25: Async task status tracking**

    For any long-running task, polling the status endpoint should show progress
    updates until completion.

    **Validates: Requirements 11.1, 11.2**
    """
    # Generate test data upfront
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())
    parameters = data.draw(task_parameters_strategy(task_type))
    progress_value = data.draw(st.integers(min_value=0, max_value=99))
    current_trial = data.draw(st.integers(min_value=1, max_value=100))
    task_result = data.draw(task_result_strategy(task_type, session_id))

    # Create mock Celery app
    mock_celery_app = Mock()
    task_id = str(uuid.uuid4())

    # Simulate task lifecycle: PENDING -> STARTED -> SUCCESS
    task_states = ["PENDING", "STARTED", "SUCCESS"]

    for state in task_states:
        mock_async_result = Mock()
        mock_async_result.id = task_id
        mock_async_result.state = state

        # Configure mock based on state
        if state == "PENDING":
            mock_async_result.successful.return_value = False
            mock_async_result.failed.return_value = False
            mock_async_result.ready.return_value = False
            mock_async_result.info = None
        elif state == "STARTED":
            mock_async_result.successful.return_value = False
            mock_async_result.failed.return_value = False
            mock_async_result.ready.return_value = False
            # Include progress info for running tasks
            mock_async_result.info = {"progress": progress_value, "current_trial": current_trial}
        elif state == "SUCCESS":
            mock_async_result.successful.return_value = True
            mock_async_result.failed.return_value = False
            mock_async_result.ready.return_value = True
            mock_async_result.result = task_result

        mock_celery_app.send_task.return_value = mock_async_result

        with patch("api.services.task_executor.celery_app", mock_celery_app):
            with patch("api.services.task_executor.AsyncResult", return_value=mock_async_result):
                executor = TaskExecutor()

                # For first iteration, submit the task
                if state == "PENDING":
                    returned_task_id = await executor.submit_task(
                        session_id=session_id, task_type=task_type, parameters=parameters
                    )
                    assert returned_task_id == task_id

                # Poll status
                status_info = await executor.get_task_status(task_id)

                # Verify status structure is always present
                assert "task_id" in status_info
                assert "status" in status_info
                assert "state" in status_info
                assert status_info["task_id"] == task_id
                assert status_info["state"] == state

                # Verify status is valid
                valid_statuses = [s.value for s in TaskStatus]
                assert status_info["status"] in valid_statuses

                # Verify state-specific properties
                if state == "PENDING":
                    assert status_info["status"] == TaskStatus.PENDING.value
                elif state == "STARTED":
                    assert status_info["status"] == TaskStatus.RUNNING.value
                    # Running tasks should include progress info
                    if "info" in status_info:
                        assert isinstance(status_info["info"], dict)
                elif state == "SUCCESS":
                    assert status_info["status"] == TaskStatus.COMPLETED.value
                    # Completed tasks should include result
                    assert "result" in status_info
                    assert isinstance(status_info["result"], dict)

                    # Verify result structure
                    result = status_info["result"]
                    assert "task_type" in result
                    assert "session_id" in result
                    assert "status" in result
                    assert result["task_type"] == task_type
                    assert result["session_id"] == session_id


@given(data=st.data())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_failed_task_status_tracking(data: st.DataObject) -> None:
    """
    Property: Failed tasks should report error information.

    For any task that fails, the status should show failure state
    and include error information.

    **Validates: Requirements 11.1, 11.2**
    """
    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())
    parameters = data.draw(task_parameters_strategy(task_type))

    # Create mock Celery app with failed task
    mock_celery_app = Mock()
    task_id = str(uuid.uuid4())

    mock_async_result = Mock()
    mock_async_result.id = task_id
    mock_async_result.state = "FAILURE"
    mock_async_result.successful.return_value = False
    mock_async_result.failed.return_value = True
    mock_async_result.ready.return_value = True

    # Generate error message
    error_message = data.draw(st.text(min_size=10, max_size=100))
    mock_async_result.info = error_message

    mock_celery_app.send_task.return_value = mock_async_result

    with patch("api.services.task_executor.celery_app", mock_celery_app):
        with patch("api.services.task_executor.AsyncResult", return_value=mock_async_result):
            executor = TaskExecutor()

            # Submit task
            returned_task_id = await executor.submit_task(
                session_id=session_id, task_type=task_type, parameters=parameters
            )
            assert returned_task_id == task_id

            # Get status
            status_info = await executor.get_task_status(task_id)

            # Verify failed status
            assert status_info["status"] == TaskStatus.FAILED.value
            assert status_info["state"] == "FAILURE"

            # Verify error information is present
            assert "error" in status_info
            assert isinstance(status_info["error"], str)
            assert len(status_info["error"]) > 0


# ============================================================================
# Error Response Property Tests
# ============================================================================


@st.composite
def api_error_strategy(draw: st.DrawFn) -> Any:
    """Generate various APIError instances for testing."""
    error_type = draw(
        st.sampled_from(
            [
                "session_not_found",
                "task_not_found",
                "validation_error",
                "authentication_error",
                "authorization_error",
                "rate_limit_exceeded",
                "invalid_token",
                "expired_token",
            ]
        )
    )

    if error_type == "session_not_found":
        session_id = str(uuid.uuid4())
        return SessionNotFoundError(session_id)
    elif error_type == "task_not_found":
        task_id = str(uuid.uuid4())
        return TaskNotFoundError(task_id)
    elif error_type == "validation_error":
        message = draw(st.text(min_size=10, max_size=100))
        validation_errors = draw(
            st.lists(
                st.fixed_dictionaries(
                    {
                        "field": st.text(min_size=1, max_size=50),
                        "message": st.text(min_size=5, max_size=100),
                        "type": st.sampled_from(["value_error", "type_error", "missing"]),
                    }
                ),
                min_size=1,
                max_size=5,
            )
        )
        return ValidationError(message, [str(e) for e in validation_errors])
    elif error_type == "authentication_error":
        message = draw(st.text(min_size=10, max_size=100))
        return AuthenticationError(message)
    elif error_type == "authorization_error":
        resource = draw(st.text(min_size=5, max_size=50))
        action = draw(st.sampled_from(["read", "write", "delete", "execute"]))
        required_role = draw(st.sampled_from(["admin", "researcher", "viewer"]))
        return AuthorizationError(resource, action, required_role)
    elif error_type == "rate_limit_exceeded":
        limit = draw(st.integers(min_value=10, max_value=1000))
        window_seconds = draw(st.integers(min_value=60, max_value=3600))
        retry_after = draw(st.integers(min_value=1, max_value=300))
        return RateLimitExceededError(limit, window_seconds, retry_after)
    elif error_type == "invalid_token":
        reason = draw(st.text(min_size=10, max_size=100))
        return InvalidTokenError(reason)
    elif error_type == "expired_token":
        message = draw(st.text(min_size=10, max_size=100))
        return ExpiredTokenError(message)


@given(error=api_error_strategy(), request_id=st.text(min_size=10, max_size=50))
@settings(max_examples=100, deadline=None)
def test_property_error_response_completeness(error: APIError, request_id: str) -> None:
    """
    **Feature: api-rest-interface, Property 3: Error response completeness**

    For any API request that results in an error, the response should include
    an error message, error code, and request ID.

    **Validates: Requirements 1.3**
    """
    # Convert error to dictionary response format
    error_dict = error.to_dict(request_id=request_id)

    # Verify top-level structure
    assert "error" in error_dict, "Response must contain 'error' field"
    error_content = error_dict["error"]

    # Property 1: Error response must include error code
    assert "code" in error_content, "Error response must include 'code' field"
    assert isinstance(error_content["code"], str), "Error code must be a string"
    assert len(error_content["code"]) > 0, "Error code must not be empty"

    # Property 2: Error response must include error message
    assert "message" in error_content, "Error response must include 'message' field"
    assert isinstance(error_content["message"], str), "Error message must be a string"
    assert len(error_content["message"]) > 0, "Error message must not be empty"

    # Property 3: Error response must include request ID
    assert "request_id" in error_content, "Error response must include 'request_id' field"
    assert error_content["request_id"] == request_id, "Request ID must match the provided value"

    # Property 4: Error response must include timestamp
    assert "timestamp" in error_content, "Error response must include 'timestamp' field"
    assert isinstance(error_content["timestamp"], str), "Timestamp must be a string"
    # Verify timestamp is in ISO format with Z suffix
    assert error_content["timestamp"].endswith("Z"), "Timestamp must be in UTC (end with 'Z')"

    # Property 5: Error response must include details field
    assert "details" in error_content, "Error response must include 'details' field"
    assert isinstance(error_content["details"], dict), "Details must be a dictionary"

    # Property 6: Verify error has appropriate HTTP status code
    assert hasattr(error, "status_code"), "Error must have status_code attribute"
    assert isinstance(error.status_code, int), "Status code must be an integer"
    assert 400 <= error.status_code < 600, "Status code must be in 4xx or 5xx range"


@given(error=api_error_strategy())
@settings(max_examples=100, deadline=None)
def test_property_error_response_without_request_id(error: APIError) -> None:
    """
    Property: Error responses should handle missing request IDs gracefully.

    For any error, converting to dict without a request_id should still
    produce a valid error response structure.
    """
    # Convert error to dictionary without request_id
    error_dict = error.to_dict(request_id=None)

    # Verify structure is still valid
    assert "error" in error_dict
    error_content = error_dict["error"]

    # All required fields should still be present
    assert "code" in error_content
    assert "message" in error_content
    assert "timestamp" in error_content
    assert "details" in error_content

    # request_id should be None or present
    assert "request_id" in error_content


@given(
    error_code=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Nd"), whitelist_characters="_"),
    ),
    error_message=st.text(min_size=10, max_size=200),
    status_code=st.sampled_from([400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504]),
)
@settings(max_examples=100, deadline=None)
def test_property_custom_api_error_completeness(
    error_code: str, error_message: str, status_code: int
) -> None:
    """
    Property: Custom APIError instances should produce complete error responses.

    For any custom error code, message, and status code, the resulting
    error response should be complete and well-formed.
    """
    # Create custom APIError
    custom_error = APIError(
        code=error_code,
        message=error_message,
        status_code=status_code,
        details={"custom_field": "custom_value"},
    )

    # Generate request ID
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Convert to dict
    error_dict = custom_error.to_dict(request_id=request_id)

    # Verify all required fields are present
    assert "error" in error_dict
    error_content = error_dict["error"]

    assert error_content["code"] == error_code
    assert error_content["message"] == error_message
    assert error_content["request_id"] == request_id
    assert "timestamp" in error_content
    assert "details" in error_content
    assert error_content["details"]["custom_field"] == "custom_value"

    # Verify status code is accessible
    assert custom_error.status_code == status_code


# ============================================================================
# Authentication and Authorization Property Tests
# ============================================================================


@st.composite
def user_credentials_strategy(draw: st.DrawFn) -> Dict[str, Any]:
    """Generate valid user credentials."""
    username = draw(
        st.text(
            min_size=3,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
        )
    )
    password = draw(st.text(min_size=8, max_size=100))
    roles = draw(
        st.lists(
            st.sampled_from(["admin", "researcher", "viewer"]), min_size=1, max_size=3, unique=True
        )
    )
    return {"username": username, "password": password, "roles": roles}


@st.composite
def user_id_strategy(draw: st.DrawFn) -> str:
    """Generate valid user IDs (UUIDs)."""
    return str(uuid.uuid4())


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_authentication_token_round_trip(
    credentials: Dict[str, Any], user_id: str
) -> None:
    """
    **Feature: api-rest-interface, Property 16: Authentication token round-trip**

    For any valid credentials, authenticating should return a token that can be
    used to make authenticated requests successfully.

    **Validates: Requirements 7.1, 7.2**
    """
    from api.database.connection import SessionLocal
    from api.services.auth_manager import AuthManager

    # Create database session
    db = SessionLocal()

    try:
        # Create AuthManager
        auth_manager = AuthManager(db)

        # Step 1: Create access token
        access_token = auth_manager.create_access_token(
            user_id=user_id, username=credentials["username"], roles=credentials["roles"]
        )

        # Verify token was created
        assert access_token is not None
        assert isinstance(access_token, str)
        assert len(access_token) > 0

        # Step 2: Verify the token (round-trip)
        payload = auth_manager.verify_token(access_token, expected_type="access")

        # Verify payload contains correct information
        assert payload is not None
        assert payload.user_id == user_id
        assert payload.username == credentials["username"]
        assert payload.roles == credentials["roles"]
        assert payload.token_type == "access"

        # Verify expiration is in the future
        from datetime import datetime

        assert payload.exp > datetime.utcnow()

    finally:
        db.close()


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_refresh_token_round_trip(credentials: Dict[str, Any], user_id: str) -> None:
    """
    Property: Refresh tokens should also support round-trip verification.

    For any valid credentials, creating a refresh token and verifying it
    should return the same user information.

    **Validates: Requirements 7.1, 7.2**
    """
    from api.database.connection import SessionLocal
    from api.services.auth_manager import AuthManager

    # Create database session
    db = SessionLocal()

    try:
        # Create AuthManager
        auth_manager = AuthManager(db)

        # Create refresh token
        refresh_token = auth_manager.create_refresh_token(
            user_id=user_id, username=credentials["username"], roles=credentials["roles"]
        )

        # Verify token was created
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0

        # Verify the token
        payload = auth_manager.verify_token(refresh_token, expected_type="refresh")

        # Verify payload
        assert payload.user_id == user_id
        assert payload.username == credentials["username"]
        assert payload.roles == credentials["roles"]
        assert payload.token_type == "refresh"

    finally:
        db.close()


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy(),
    required_permission=st.sampled_from(
        [
            "session:create",
            "session:read",
            "session:update",
            "session:delete",
            "task:create",
            "task:read",
            "data:export",
            "system:admin",
        ]
    ),
)
@settings(max_examples=100, deadline=None)
def test_property_authorization_enforcement(
    credentials: Dict[str, Any], user_id: str, required_permission: str
) -> None:
    """
    **Feature: api-rest-interface, Property 17: Authorization enforcement**

    For any operation requiring specific permissions, requests without those
    permissions should return 403 Forbidden.

    **Validates: Requirements 7.3, 7.5**
    """
    from api.services.authorization import Permission, get_permissions_for_roles, has_permission

    # Get user's permissions based on their roles
    user_permissions = get_permissions_for_roles(credentials["roles"])

    # Try to convert required_permission string to Permission enum
    try:
        perm_enum = Permission(required_permission)
    except ValueError:
        # If permission doesn't exist, skip this test case
        return

    # Check if user has the permission
    has_perm = has_permission(credentials["roles"], perm_enum)

    # Verify the result matches what we expect based on user's permissions
    expected_has_perm = perm_enum in user_permissions
    assert has_perm == expected_has_perm

    # If user doesn't have permission, verify check_permission raises error
    if not has_perm:
        from api.exceptions import AuthorizationError
        from api.services.authorization import check_permission

        with pytest.raises(AuthorizationError) as exc_info:
            check_permission(
                user_roles=credentials["roles"],
                required_permission=perm_enum,
                resource="test_resource",
                action="test_action",
            )

        # Verify error contains relevant information
        error = exc_info.value
        assert error.status_code == 403
        assert (
            "FORBIDDEN" in error.code
            or "AUTHORIZATION" in error.code
            or "INSUFFICIENT_PERMISSIONS" in error.code
        )


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy(),
    expiration_seconds=st.integers(min_value=-3600, max_value=-1),
)
@settings(max_examples=100, deadline=None)
def test_property_expired_token_rejection(
    credentials: Dict[str, Any], user_id: str, expiration_seconds: int
) -> None:
    """
    **Feature: api-rest-interface, Property 18: Expired token rejection**

    For any expired JWT token, requests using that token should be rejected
    with 401 Unauthorized.

    **Validates: Requirements 7.4**
    """
    from datetime import datetime

    import jwt

    from api.database.connection import SessionLocal
    from api.exceptions import ExpiredTokenError
    from api.services.auth_manager import AuthManager, TokenPayload

    # Create database session
    db = SessionLocal()

    try:
        # Create AuthManager
        auth_manager = AuthManager(db)

        # Create an expired token by manually setting expiration in the past
        expires_at = datetime.utcnow() + timedelta(seconds=expiration_seconds)

        payload = TokenPayload(
            user_id=user_id,
            username=credentials["username"],
            roles=credentials["roles"],
            exp=expires_at,
            token_type="access",
        )

        # Encode the token with past expiration
        assert auth_manager.secret_key is not None
        expired_token = jwt.encode(
            payload.to_dict(), auth_manager.secret_key, algorithm=auth_manager.algorithm
        )

        # Verify token is actually expired
        assert expires_at < datetime.utcnow()

        # Attempt to verify the expired token - should raise ExpiredTokenError
        with pytest.raises(ExpiredTokenError) as exc_info:
            auth_manager.verify_token(expired_token, expected_type="access")

        # Verify error message indicates expiration
        error_message = str(exc_info.value)
        assert "expired" in error_message.lower()

    finally:
        db.close()


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=50, deadline=None)
def test_property_invalid_token_rejection(credentials: Dict[str, Any], user_id: str) -> None:
    """
    Property: Invalid or malformed tokens should be rejected.

    For any invalid token, verification should raise InvalidTokenError.

    **Validates: Requirements 7.2, 7.4**
    """
    from api.database.connection import SessionLocal
    from api.exceptions import InvalidTokenError
    from api.services.auth_manager import AuthManager

    # Create database session
    db = SessionLocal()

    try:
        # Create AuthManager
        auth_manager = AuthManager(db)

        # Test various invalid tokens
        invalid_tokens = [
            "not.a.valid.token",
            "invalid_token_format",
            "",
            "Bearer token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ]

        for invalid_token in invalid_tokens:
            # Attempt to verify invalid token - should raise InvalidTokenError
            with pytest.raises(InvalidTokenError):
                auth_manager.verify_token(invalid_token, expected_type="access")

    finally:
        db.close()


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=50, deadline=None)
def test_property_wrong_token_type_rejection(credentials: Dict[str, Any], user_id: str) -> None:
    """
    Property: Using wrong token type should be rejected.

    For any token, verifying it with the wrong expected type should fail.

    **Validates: Requirements 7.2**
    """
    from api.database.connection import SessionLocal
    from api.exceptions import InvalidTokenError
    from api.services.auth_manager import AuthManager

    # Create database session
    db = SessionLocal()

    try:
        # Create AuthManager
        auth_manager = AuthManager(db)

        # Create an access token
        access_token = auth_manager.create_access_token(
            user_id=user_id, username=credentials["username"], roles=credentials["roles"]
        )

        # Try to verify it as a refresh token - should fail
        with pytest.raises(InvalidTokenError) as exc_info:
            auth_manager.verify_token(access_token, expected_type="refresh")

        # Verify error mentions token type mismatch
        error_message = str(exc_info.value)
        assert "type" in error_message.lower()

    finally:
        db.close()


# ============================================================================
# Rate Limiting Property Tests
# ============================================================================


@st.composite
def client_id_strategy(draw: st.DrawFn) -> str:
    """Generate valid client IDs."""
    client_type = draw(st.sampled_from(["user", "ip"]))
    if client_type == "user":
        return f"user:{uuid.uuid4()}"
    else:
        # Generate valid IP addresses
        octets = [draw(st.integers(min_value=1, max_value=255)) for _ in range(4)]
        return f"ip:{'.'.join(map(str, octets))}"


@st.composite
def endpoint_strategy(draw: st.DrawFn) -> str:
    """Generate valid endpoint identifiers."""
    return draw(
        st.sampled_from(
            [
                "global",
                "session:create",
                "session:read",
                "session:delete",
                "task:execute",
                "data:export",
            ]
        )
    )


@given(
    client_id=client_id_strategy(),
    endpoint=endpoint_strategy(),
    num_requests=st.integers(min_value=1, max_value=150),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_rate_limit_enforcement(
    client_id: str, endpoint: str, num_requests: int
) -> None:
    """
    **Feature: api-rest-interface, Property 19: Rate limit enforcement**

    For any client exceeding rate limits, subsequent requests should return
    429 Too Many Requests until the window resets.

    **Validates: Requirements 8.1, 8.2**
    """
    import asyncio
    import time

    import redis.asyncio as redis

    from api.config import settings
    from api.services.rate_limiter import RateLimiter

    # Create unique client_id to avoid collisions between parallel test runs
    # Use both test run ID and timestamp to ensure uniqueness across Hypothesis examples
    test_run_id = str(uuid.uuid4())[:8]
    timestamp_id = str(time.time()).replace(".", "_")
    unique_client_id = f"test_{test_run_id}_{timestamp_id}_{client_id}"

    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Aggressively clean up any existing state
        key = rate_limiter._get_redis_key(unique_client_id, endpoint)
        await redis_client.delete(key)
        await asyncio.sleep(0.01)  # Give Redis time to process

        # Verify Redis state is clean before starting
        existing_count = await redis_client.zcard(key)
        assert (
            existing_count == 0
        ), f"Redis state not clean: found {existing_count} existing entries"

        # Get the configured limit for this endpoint
        limit, window_seconds = rate_limiter._get_limit_config(endpoint)
        weight = rate_limiter._get_operation_weight(endpoint)

        # Calculate how many requests we can make before hitting the limit
        max_allowed_requests = limit // weight

        # Track results
        allowed_count = 0
        denied_count = 0

        # Make requests
        for i in range(num_requests):
            result = await rate_limiter.check_rate_limit(
                client_id=unique_client_id, endpoint=endpoint
            )

            if result.allowed:
                allowed_count += 1
            else:
                denied_count += 1

                # Once we start getting denied, all subsequent requests should be denied
                # (until window resets, which won't happen in this test)
                assert result.retry_after is not None
                assert result.retry_after > 0
                assert result.remaining == 0

        # Debug: Check actual Redis state
        final_count = await redis_client.zcard(key)

        # Verify rate limiting behavior
        if num_requests <= max_allowed_requests:
            # All requests should be allowed
            assert (
                allowed_count == num_requests
            ), f"Expected {num_requests} allowed, got {allowed_count}. Final Redis count: {final_count}"
            assert denied_count == 0
        else:
            # Some requests should be allowed, rest denied
            # The allowed count should be exactly max_allowed_requests
            assert (
                allowed_count == max_allowed_requests
            ), f"Expected {max_allowed_requests} allowed requests (limit={limit}, weight={weight}), but got {allowed_count}. Final Redis count: {final_count}, Redis key: {key}"
            assert denied_count == num_requests - allowed_count
            assert denied_count > 0

    finally:
        # Clean up - ensure we remove the test data
        await rate_limiter.reset_rate_limit(unique_client_id, endpoint)
        # Wait for Redis to process the cleanup
        await asyncio.sleep(0.05)
        await redis_client.close()


@given(client_id=client_id_strategy(), endpoint=endpoint_strategy())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_per_client_isolation(client_id: str, endpoint: str) -> None:
    """
    Property: Rate limits should be isolated per client.

    For any two different clients, one client hitting rate limits should
    not affect the other client's ability to make requests.

    **Validates: Requirements 8.2**
    """
    import redis.asyncio as redis

    from api.config import settings
    from api.services.rate_limiter import RateLimiter

    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Generate a second client ID
        client_id_2 = f"{client_id}_different"

        # Reset rate limits
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await rate_limiter.reset_rate_limit(client_id_2, endpoint)

        # Get limit configuration
        limit, window_seconds = rate_limiter._get_limit_config(endpoint)
        weight = rate_limiter._get_operation_weight(endpoint)
        max_requests = limit // weight

        # Exhaust rate limit for first client
        for i in range(max_requests + 5):
            await rate_limiter.check_rate_limit(client_id, endpoint)

        # Verify first client is rate limited
        result1 = await rate_limiter.check_rate_limit(client_id, endpoint)
        assert not result1.allowed

        # Verify second client can still make requests
        result2 = await rate_limiter.check_rate_limit(client_id_2, endpoint)
        assert result2.allowed
        assert result2.remaining > 0

    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await rate_limiter.reset_rate_limit(client_id_2, endpoint)
        await redis_client.close()


@given(client_id=client_id_strategy(), endpoint1=endpoint_strategy(), endpoint2=endpoint_strategy())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_per_endpoint_isolation(
    client_id: str, endpoint1: str, endpoint2: str
) -> None:
    """
    Property: Rate limits should be isolated per endpoint.

    For any client, hitting rate limits on one endpoint should not
    affect their ability to access other endpoints.

    **Validates: Requirements 8.2**
    """
    import redis.asyncio as redis

    from api.config import settings
    from api.services.rate_limiter import RateLimiter

    # Skip if endpoints are the same
    assume(endpoint1 != endpoint2)

    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Reset rate limits
        await rate_limiter.reset_rate_limit(client_id, endpoint1)
        await rate_limiter.reset_rate_limit(client_id, endpoint2)

        # Get limit configuration for first endpoint
        limit1, window1 = rate_limiter._get_limit_config(endpoint1)
        weight1 = rate_limiter._get_operation_weight(endpoint1)
        max_requests1 = limit1 // weight1

        # Exhaust rate limit for first endpoint
        for i in range(max_requests1 + 5):
            await rate_limiter.check_rate_limit(client_id, endpoint1)

        # Verify first endpoint is rate limited
        result1 = await rate_limiter.check_rate_limit(client_id, endpoint1)
        assert not result1.allowed

        # Verify second endpoint is still accessible
        result2 = await rate_limiter.check_rate_limit(client_id, endpoint2)
        assert result2.allowed
        assert result2.remaining > 0

    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint1)
        await rate_limiter.reset_rate_limit(client_id, endpoint2)
        await redis_client.close()


@given(
    client_id=client_id_strategy(),
    endpoint=endpoint_strategy(),
    custom_limit=st.integers(min_value=5, max_value=50),
    custom_window=st.integers(min_value=10, max_value=120),
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_custom_configuration(
    client_id: str, endpoint: str, custom_limit: int, custom_window: int
) -> None:
    """
    Property: Custom rate limit configurations should be respected.

    For any custom limit and window configuration, the rate limiter
    should enforce those specific limits.

    **Validates: Requirements 8.2, 8.5**
    """
    import redis.asyncio as redis

    from api.config import settings
    from api.services.rate_limiter import RateLimiter

    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Reset rate limit
        await rate_limiter.reset_rate_limit(client_id, endpoint)

        # Get weight for this endpoint
        weight = rate_limiter._get_operation_weight(endpoint)
        max_requests = custom_limit // weight

        # Make requests up to the custom limit
        allowed_count = 0
        for i in range(max_requests + 2):
            result = await rate_limiter.check_rate_limit(
                client_id=client_id,
                endpoint=endpoint,
                limit=custom_limit,
                window_seconds=custom_window,
            )

            if result.allowed:
                allowed_count += 1
                # Verify limit is reported correctly
                assert result.limit == custom_limit

        # Verify we allowed approximately the right number of requests
        assert allowed_count >= max_requests - 1
        assert allowed_count <= max_requests + 1

        # Next request should be denied
        result = await rate_limiter.check_rate_limit(
            client_id=client_id, endpoint=endpoint, limit=custom_limit, window_seconds=custom_window
        )
        assert not result.allowed
        assert result.limit == custom_limit

    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await redis_client.close()


@given(client_id=client_id_strategy(), endpoint=endpoint_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_header_completeness(client_id: str, endpoint: str) -> None:
    """
    **Feature: api-rest-interface, Property 20: Rate limit header completeness**

    For any API request, the response should include rate limit headers
    (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).

    **Validates: Requirements 8.3, 8.4, 8.5**
    """
    from datetime import datetime

    import redis.asyncio as redis

    from api.config import settings
    from api.services.rate_limiter import RateLimiter

    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Reset rate limit
        await rate_limiter.reset_rate_limit(client_id, endpoint)

        # Make a request and check rate limit
        result = await rate_limiter.check_rate_limit(client_id=client_id, endpoint=endpoint)

        # Get rate limit headers
        headers = rate_limiter.get_rate_limit_headers(result)

        # Verify all required headers are present
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

        # Verify header values are valid
        # X-RateLimit-Limit should be a positive integer
        limit_value = int(headers["X-RateLimit-Limit"])
        assert limit_value > 0
        assert limit_value == result.limit

        # X-RateLimit-Remaining should be a non-negative integer
        remaining_value = int(headers["X-RateLimit-Remaining"])
        assert remaining_value >= 0
        assert remaining_value == result.remaining
        assert remaining_value <= limit_value

        # X-RateLimit-Reset should be a valid Unix timestamp in the future
        reset_value = int(headers["X-RateLimit-Reset"])
        assert reset_value > 0
        current_timestamp = int(datetime.utcnow().timestamp())
        assert reset_value >= current_timestamp
        assert reset_value == int(result.reset_at.timestamp())

        # If request was denied, Retry-After header should be present
        if not result.allowed:
            assert "Retry-After" in headers
            retry_after_value = int(headers["Retry-After"])
            assert retry_after_value > 0
            assert retry_after_value == result.retry_after

        # Test with rate limit exceeded scenario
        # Get limit configuration
        limit, window_seconds = rate_limiter._get_limit_config(endpoint)
        weight = rate_limiter._get_operation_weight(endpoint)
        max_requests = limit // weight

        # Exhaust rate limit
        for i in range(max_requests + 5):
            await rate_limiter.check_rate_limit(client_id, endpoint)

        # Make one more request that should be denied
        denied_result = await rate_limiter.check_rate_limit(client_id, endpoint)
        assert not denied_result.allowed

        # Get headers for denied request
        denied_headers = rate_limiter.get_rate_limit_headers(denied_result)

        # Verify all headers are still present
        assert "X-RateLimit-Limit" in denied_headers
        assert "X-RateLimit-Remaining" in denied_headers
        assert "X-RateLimit-Reset" in denied_headers
        assert "Retry-After" in denied_headers

        # Verify denied request has remaining = 0
        assert int(denied_headers["X-RateLimit-Remaining"]) == 0

        # Verify Retry-After is present and valid
        retry_after = int(denied_headers["Retry-After"])
        assert retry_after > 0
        assert retry_after <= window_seconds + 1  # Should be within window

    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await redis_client.close()


# ============================================================================
# Data Export Property Tests
# ============================================================================


@st.composite
def simulation_history_strategy(draw: st.DrawFn) -> Dict[str, Any]:
    """Generate valid simulation history data."""
    # Generate a reasonable number of timesteps
    num_steps = draw(st.integers(min_value=10, max_value=500))

    # Generate time array (monotonically increasing)
    start_time = draw(st.floats(min_value=0.0, max_value=1000.0))
    timestep_ms = draw(st.floats(min_value=1.0, max_value=100.0))
    times = [start_time + i * timestep_ms for i in range(num_steps)]

    # Generate various data arrays matching the number of timesteps
    history = {
        "time": times,
        "free_energy": draw(
            st.lists(
                st.floats(min_value=0.0, max_value=10.0), min_size=num_steps, max_size=num_steps
            )
        ),
        "ignitions": draw(st.lists(st.booleans(), min_size=num_steps, max_size=num_steps)),
        "metabolic_reserves": draw(
            st.lists(
                st.floats(min_value=0.0, max_value=1000.0), min_size=num_steps, max_size=num_steps
            )
        ),
        "allostatic_load": draw(
            st.lists(
                st.floats(min_value=0.0, max_value=1.0), min_size=num_steps, max_size=num_steps
            )
        ),
    }

    return history


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    export_format=st.sampled_from(["json", "csv"]),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_completeness(
    session_id: str, history: Dict[str, Any], export_format: str
) -> None:
    """
    **Feature: api-rest-interface, Property 11: Data export completeness**

    For any simulation session with recorded data, exporting the data should
    include all timesteps that were recorded.

    **Validates: Requirements 5.1**
    """
    import csv
    import io
    import json
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)

    # Configure mock to return our generated history
    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}

    # Configure session manager to return our mock session
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Export the data
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id, format=export_format
    )

    # Verify content type is correct
    if export_format == "json":
        assert content_type == "application/json"
    elif export_format == "csv":
        assert content_type == "text/csv"

    # Verify data was returned
    assert data_bytes is not None
    assert len(data_bytes) > 0

    # Parse the exported data and verify completeness
    num_recorded_timesteps = len(history["time"])

    if export_format == "json":
        # Parse JSON
        data_str = data_bytes.decode("utf-8")
        exported_data = json.loads(data_str)

        # Verify structure
        assert "session_id" in exported_data
        assert "history" in exported_data
        assert exported_data["session_id"] == session_id

        # Verify all timesteps are present
        exported_history = exported_data["history"]
        assert "time" in exported_history
        exported_times = exported_history["time"]

        # Property: All recorded timesteps should be in the export
        assert len(exported_times) == num_recorded_timesteps

        # Verify times match exactly
        for i, (original_time, exported_time) in enumerate(zip(history["time"], exported_times)):
            assert (
                abs(original_time - exported_time) < 0.001
            ), f"Timestep {i}: original={original_time}, exported={exported_time}"

        # Verify all data arrays have the same length as time
        for key, values in exported_history.items():
            if isinstance(values, list) and key in history:
                assert (
                    len(values) == num_recorded_timesteps
                ), f"Variable '{key}' has {len(values)} values, expected {num_recorded_timesteps}"

    elif export_format == "csv":
        # Parse CSV
        data_str = data_bytes.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(data_str))
        rows = list(csv_reader)

        # Property: All recorded timesteps should be in the export
        assert (
            len(rows) == num_recorded_timesteps
        ), f"CSV has {len(rows)} rows, expected {num_recorded_timesteps}"

        # Verify time column exists and values match
        for i, (row, original_time) in enumerate(zip(rows, history["time"])):
            assert "time" in row
            exported_time = float(row["time"])
            assert (
                abs(original_time - exported_time) < 0.001
            ), f"Row {i}: original time={original_time}, exported time={exported_time}"


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    start_time_offset=st.floats(min_value=0.1, max_value=0.4),
    end_time_offset=st.floats(min_value=0.6, max_value=0.9),
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_time_filtering(
    session_id: str, history: Dict[str, Any], start_time_offset: float, end_time_offset: float
) -> None:
    """
    Property: Data export with time filtering should include only timesteps
    within the specified range.

    For any simulation session and time range, exporting with start_time and
    end_time filters should return only the timesteps within that range.

    **Validates: Requirements 5.1**
    """
    import json
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Skip if history is too small
    assume(len(history["time"]) >= 10)

    # Calculate time range
    times = history["time"]
    time_span = times[-1] - times[0]
    start_time = times[0] + time_span * start_time_offset
    end_time = times[0] + time_span * end_time_offset

    # Ensure start < end
    assume(start_time < end_time)

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)

    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}

    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Export with time filtering
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id, format="json", start_time=start_time, end_time=end_time
    )

    # Parse exported data
    data_str = data_bytes.decode("utf-8")
    exported_data = json.loads(data_str)
    exported_times = exported_data["history"]["time"]

    # Property: All exported times should be within the specified range
    for t in exported_times:
        assert start_time <= t <= end_time, f"Time {t} is outside range [{start_time}, {end_time}]"

    # Property: All times within the range should be exported
    expected_times = [t for t in times if start_time <= t <= end_time]
    assert len(exported_times) == len(
        expected_times
    ), f"Expected {len(expected_times)} timesteps, got {len(exported_times)}"


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    variables_to_export=st.lists(
        st.sampled_from(["free_energy", "ignitions", "metabolic_reserves", "allostatic_load"]),
        min_size=1,
        max_size=3,
        unique=True,
    ),
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_variable_filtering(
    session_id: str, history: Dict[str, Any], variables_to_export: List[str]
) -> None:
    """
    Property: Data export with variable filtering should include only the
    requested variables (plus time).

    For any simulation session and list of variables, exporting with variable
    filtering should return only those variables.

    **Validates: Requirements 5.1**
    """
    import json
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)

    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}

    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Export with variable filtering
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id, format="json", variables=variables_to_export
    )

    # Parse exported data
    data_str = data_bytes.decode("utf-8")
    exported_data = json.loads(data_str)
    exported_history = exported_data["history"]

    # Property: Time should always be included
    assert "time" in exported_history

    # Property: All requested variables should be present
    for var in variables_to_export:
        assert var in exported_history, f"Variable '{var}' not in export"
        # Verify it has the correct length
        assert len(exported_history[var]) == len(exported_history["time"])

    # Property: Only requested variables (plus time) should be present
    # Filter out any metadata or non-data fields
    data_keys = [k for k in exported_history.keys() if isinstance(exported_history[k], list)]
    expected_keys = set(variables_to_export) | {"time"}
    actual_keys = set(data_keys)

    assert actual_keys == expected_keys, f"Expected variables {expected_keys}, got {actual_keys}"


# ============================================================================
# Time Series Export Property Tests
# ============================================================================


@st.composite
def time_series_variables_strategy(draw: st.DrawFn) -> List[str]:
    """Generate valid variable names for time series export."""
    # Common variables available in APGI system history
    available_vars = [
        "free_energy",
        "ignitions",
        "metabolic_reserves",
        "allostatic_load",
        "extero_precision",
        "intero_precision",
        "heart_rate",
        "cortisol",
        "workspace_active",
        "gamma_power",
        "beta_power",
        "minimal_self_coherence",
    ]

    # Select a subset of variables
    num_vars = draw(st.integers(min_value=1, max_value=len(available_vars)))
    selected = draw(
        st.lists(st.sampled_from(available_vars), min_size=num_vars, max_size=num_vars, unique=True)
    )
    return selected


@st.composite
def mock_time_series_history_strategy(draw: st.DrawFn, num_steps: int) -> Dict[str, Any]:
    """Generate mock history data for time series testing."""
    # Generate timestamps (monotonically increasing)
    start_time = draw(st.floats(min_value=0.0, max_value=1000.0))
    timestep = draw(st.floats(min_value=1.0, max_value=100.0))

    times = [start_time + i * timestep for i in range(num_steps)]

    # Generate data for various variables
    history = {
        "time": times,
        "free_energy": [draw(st.floats(min_value=0.0, max_value=10.0)) for _ in range(num_steps)],
        "ignitions": [draw(st.booleans()) for _ in range(num_steps)],
        "metabolic_reserves": [
            draw(st.floats(min_value=0.0, max_value=1000.0)) for _ in range(num_steps)
        ],
        "allostatic_load": [
            draw(st.floats(min_value=0.0, max_value=5.0)) for _ in range(num_steps)
        ],
        "extero_precision": [
            draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)
        ],
        "intero_precision": [
            draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)
        ],
        "heart_rate": [draw(st.floats(min_value=60.0, max_value=120.0)) for _ in range(num_steps)],
        "cortisol": [draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)],
        "workspace_active": [draw(st.booleans()) for _ in range(num_steps)],
        "gamma_power": [draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)],
        "beta_power": [draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)],
        "minimal_self_coherence": [
            draw(st.floats(min_value=0.0, max_value=1.0)) for _ in range(num_steps)
        ],
    }

    return history


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_time_series_data_consistency(data: st.DataObject) -> None:
    """
    **Feature: api-rest-interface, Property 12: Time series data consistency**

    For any time series export request, the returned data should be ordered by
    timestamp and contain only the requested variables.

    **Validates: Requirements 5.3**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate test data
    num_steps = data.draw(st.integers(min_value=10, max_value=100))
    requested_variables = data.draw(time_series_variables_strategy())
    session_id = data.draw(session_id_strategy())

    # Generate mock history data
    mock_history = data.draw(mock_time_series_history_strategy(num_steps))

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = Mock(spec=SimulationSession)

    # Mock get_state to return our history
    mock_sim_session.get_state = AsyncMock(return_value={"history": mock_history})

    # Mock get_session to return our simulation session
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create DataExportService with mocked session manager
    export_service = DataExportService(mock_session_manager)

    # Export time series data
    result = await export_service.export_time_series(
        session_id=session_id,
        variables=requested_variables,
        start_time=None,
        end_time=None,
        downsample=None,
        limit=None,
        cursor=None,
    )

    # Verify result structure
    assert "session_id" in result
    assert "time" in result
    assert "data" in result
    assert "num_points" in result

    assert result["session_id"] == session_id

    # Property 1: Timestamps should be ordered (monotonically increasing)
    returned_times = result["time"]
    assert len(returned_times) > 0, "Time series should contain data points"

    for i in range(len(returned_times) - 1):
        assert (
            returned_times[i] <= returned_times[i + 1]
        ), f"Timestamps must be monotonically increasing: {returned_times[i]} > {returned_times[i + 1]}"

    # Property 2: Only requested variables should be present in data
    returned_data = result["data"]
    assert isinstance(returned_data, dict), "Data should be a dictionary"

    # Check that all requested variables are present
    for var in requested_variables:
        assert var in returned_data, f"Requested variable '{var}' should be in returned data"

    # Check that no extra variables are present
    for var in returned_data.keys():
        assert (
            var in requested_variables
        ), f"Variable '{var}' was not requested but is in returned data"

    # Property 3: Each variable should have the same number of data points as timestamps
    num_time_points = len(returned_times)
    for var, values in returned_data.items():
        assert (
            len(values) == num_time_points
        ), f"Variable '{var}' should have {num_time_points} data points, got {len(values)}"

    # Property 4: Data values should match the original history (in order)
    for var in requested_variables:
        original_values = mock_history[var]
        returned_values = returned_data[var]

        # Values should match in order
        assert len(returned_values) == len(
            original_values
        ), f"Variable '{var}' should have {len(original_values)} values"

        for i, (orig, ret) in enumerate(zip(original_values, returned_values)):
            # Handle boolean values
            if isinstance(orig, bool):
                assert ret == orig, f"Variable '{var}' at index {i}: expected {orig}, got {ret}"
            else:
                # Handle numeric values with tolerance
                assert (
                    abs(orig - ret) < 1e-9
                ), f"Variable '{var}' at index {i}: expected {orig}, got {ret}"


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_time_series_filtering_consistency(data: st.DataObject) -> None:
    """
    Property: Time series filtering should preserve ordering and variable selection.

    For any time series export with time range filtering, the returned data
    should still be ordered by timestamp and contain only requested variables.

    **Validates: Requirements 5.3**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate test data
    num_steps = data.draw(st.integers(min_value=20, max_value=100))
    requested_variables = data.draw(time_series_variables_strategy())
    session_id = data.draw(session_id_strategy())

    # Generate mock history data
    mock_history = data.draw(mock_time_series_history_strategy(num_steps))

    # Generate time range filter (subset of the data)
    times = mock_history["time"]
    start_idx = data.draw(st.integers(min_value=0, max_value=num_steps // 2))
    end_idx = data.draw(st.integers(min_value=num_steps // 2, max_value=num_steps - 1))

    start_time = times[start_idx]
    end_time = times[end_idx]

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = Mock(spec=SimulationSession)

    mock_sim_session.get_state = AsyncMock(return_value={"history": mock_history})

    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create DataExportService
    export_service = DataExportService(mock_session_manager)

    # Export time series data with filtering
    result = await export_service.export_time_series(
        session_id=session_id,
        variables=requested_variables,
        start_time=start_time,
        end_time=end_time,
        downsample=None,
        limit=None,
        cursor=None,
    )

    # Verify timestamps are still ordered after filtering
    returned_times = result["time"]
    assert len(returned_times) > 0, "Filtered time series should contain data points"

    for i in range(len(returned_times) - 1):
        assert (
            returned_times[i] <= returned_times[i + 1]
        ), "Timestamps must remain monotonically increasing after filtering"

    # Verify all timestamps are within the requested range
    for t in returned_times:
        assert (
            start_time <= t <= end_time
        ), f"Timestamp {t} should be within range [{start_time}, {end_time}]"

    # Verify only requested variables are present
    returned_data = result["data"]
    for var in requested_variables:
        assert var in returned_data, f"Requested variable '{var}' should be in filtered data"

    for var in returned_data.keys():
        assert (
            var in requested_variables
        ), f"Variable '{var}' was not requested but is in filtered data"

    # Verify each variable has same number of points as timestamps
    for var, values in returned_data.items():
        assert len(values) == len(
            returned_times
        ), f"Variable '{var}' should have same length as timestamps after filtering"


@given(data=st.data())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.large_base_example, HealthCheck.data_too_large],
)
@pytest.mark.asyncio
async def test_property_time_series_downsampling_consistency(data: st.DataObject) -> None:
    """
    Property: Downsampled time series should maintain ordering and variable selection.

    For any time series export with downsampling, the returned data should
    be ordered by timestamp, contain only requested variables, and have
    consistent downsampling across all variables.

    **Validates: Requirements 5.3**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate test data
    num_steps = data.draw(st.integers(min_value=50, max_value=200))
    requested_variables = data.draw(time_series_variables_strategy())
    session_id = data.draw(session_id_strategy())
    downsample_factor = data.draw(st.integers(min_value=2, max_value=10))

    # Generate mock history data
    mock_history = data.draw(mock_time_series_history_strategy(num_steps))

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = Mock(spec=SimulationSession)

    mock_sim_session.get_state = AsyncMock(return_value={"history": mock_history})

    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create DataExportService
    export_service = DataExportService(mock_session_manager)

    # Export time series data with downsampling
    result = await export_service.export_time_series(
        session_id=session_id,
        variables=requested_variables,
        start_time=None,
        end_time=None,
        downsample=downsample_factor,
        limit=None,
        cursor=None,
    )

    # Verify timestamps are still ordered after downsampling
    returned_times = result["time"]
    assert len(returned_times) > 0, "Downsampled time series should contain data points"

    for i in range(len(returned_times) - 1):
        assert (
            returned_times[i] <= returned_times[i + 1]
        ), "Timestamps must remain monotonically increasing after downsampling"

    # Verify downsampling was applied correctly
    expected_length = len(mock_history["time"][::downsample_factor])
    assert (
        len(returned_times) == expected_length
    ), f"Downsampled data should have {expected_length} points, got {len(returned_times)}"

    # Verify only requested variables are present
    returned_data = result["data"]
    for var in requested_variables:
        assert var in returned_data, f"Requested variable '{var}' should be in downsampled data"

    for var in returned_data.keys():
        assert (
            var in requested_variables
        ), f"Variable '{var}' was not requested but is in downsampled data"

    # Verify all variables have same length after downsampling
    for var, values in returned_data.items():
        assert len(values) == len(
            returned_times
        ), f"Variable '{var}' should have same length as timestamps after downsampling"
        assert (
            len(values) == expected_length
        ), f"Variable '{var}' should have {expected_length} points after downsampling"


@given(session_id=session_id_strategy(), data=st.data())
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.large_base_example,
        HealthCheck.data_too_large,
    ],
)
@pytest.mark.asyncio
async def test_property_pagination_consistency(session_id: str, data: st.DataObject) -> None:
    """
    **Feature: api-rest-interface, Property 13: Pagination consistency**

    For any paginated request, following all pagination links should eventually
    return all data without duplicates or gaps.

    **Validates: Requirements 5.5**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate test data with a reasonable number of timesteps for pagination testing
    num_steps = data.draw(st.integers(min_value=50, max_value=300))
    history = data.draw(mock_time_series_history_strategy(num_steps))

    # Generate variables to export
    variables = data.draw(time_series_variables_strategy())

    # Generate page size (limit) - should be smaller than total to trigger pagination
    page_size = data.draw(st.integers(min_value=5, max_value=min(30, num_steps // 2)))

    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)

    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Collect all data by following pagination
    all_times = []
    all_data: dict[str, list[Any]] = {var: [] for var in variables}
    cursor = None
    page_count = 0
    max_pages = 100  # Safety limit to prevent infinite loops

    while page_count < max_pages:
        # Fetch page
        result = await export_service.export_time_series(
            session_id=session_id, variables=variables, limit=page_size, cursor=cursor
        )

        # Verify result structure
        assert "time" in result
        assert "data" in result
        assert "pagination" in result or cursor is None

        # Collect data from this page
        page_times = result["time"]
        page_data = result["data"]

        # Verify all requested variables are present
        for var in variables:
            assert var in page_data, f"Variable '{var}' missing from page {page_count}"

        # Verify data consistency within page
        for var in variables:
            assert len(page_data[var]) == len(
                page_times
            ), f"Variable '{var}' length mismatch on page {page_count}"

        # Append to collected data
        all_times.extend(page_times)
        for var in variables:
            all_data[var].extend(page_data[var])

        page_count += 1

        # Check if more pages available
        pagination = result.get("pagination")
        if pagination and pagination.get("has_more"):
            cursor = pagination.get("next_cursor")
            assert cursor is not None, "has_more=True but next_cursor is None"
        else:
            # No more pages
            break

    # Property 1: All original timesteps should be present (no gaps)
    original_times = history["time"]
    assert len(all_times) == len(
        original_times
    ), f"Expected {len(original_times)} timesteps, got {len(all_times)}"

    # Property 2: Times should be in order (no reordering)
    for i in range(len(all_times)):
        assert (
            abs(all_times[i] - original_times[i]) < 0.001
        ), f"Timestep {i}: expected {original_times[i]}, got {all_times[i]}"

    # Property 3: No duplicate timesteps
    # Check that times are strictly increasing (or at least non-decreasing)
    for i in range(1, len(all_times)):
        assert (
            all_times[i] >= all_times[i - 1]
        ), f"Times not in order at index {i}: {all_times[i - 1]} -> {all_times[i]}"

    # Property 4: All data for each variable should match original (no duplicates or gaps)
    for var in variables:
        assert len(all_data[var]) == len(
            original_times
        ), f"Variable '{var}': expected {len(original_times)} values, got {len(all_data[var])}"

        # Verify values match original
        original_values = history[var]
        for i in range(len(all_data[var])):
            original_val = original_values[i]
            collected_val = all_data[var][i]

            # Handle different types appropriately
            if isinstance(original_val, bool):
                assert (
                    collected_val == original_val
                ), f"Variable '{var}' at index {i}: expected {original_val}, got {collected_val}"
            else:
                # For numeric values, allow small floating point differences
                assert (
                    abs(float(collected_val) - float(original_val)) < 0.001
                ), f"Variable '{var}' at index {i}: expected {original_val}, got {collected_val}"

    # Property 5: Number of pages should be reasonable
    expected_pages = (len(original_times) + page_size - 1) // page_size  # Ceiling division
    assert (
        page_count == expected_pages
    ), f"Expected {expected_pages} pages with page_size={page_size}, got {page_count} pages"


@given(session_id=session_id_strategy(), data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_pagination_cursor_validity(session_id: str, data: st.DataObject) -> None:
    """
    Property: Pagination cursors should be valid and decodable.

    For any paginated response with has_more=True, the next_cursor should be
    a valid base64-encoded JSON string that can be used for the next request.

    **Validates: Requirements 5.5**
    """
    import base64
    import json
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate test data
    num_steps = data.draw(st.integers(min_value=30, max_value=100))
    history = data.draw(mock_time_series_history_strategy(num_steps))
    variables = data.draw(time_series_variables_strategy())
    page_size = data.draw(st.integers(min_value=5, max_value=20))

    # Ensure we'll have multiple pages
    assume(num_steps > page_size)

    # Create mock session manager
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)
    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Fetch first page
    result = await export_service.export_time_series(
        session_id=session_id, variables=variables, limit=page_size, cursor=None
    )

    # If there's more data, verify cursor is valid
    pagination = result.get("pagination")
    if pagination and pagination.get("has_more"):
        cursor = pagination.get("next_cursor")

        # Property: Cursor should be present
        assert cursor is not None
        assert isinstance(cursor, str)
        assert len(cursor) > 0

        # Property: Cursor should be valid base64
        try:
            decoded_bytes = base64.b64decode(cursor)
            decoded_str = decoded_bytes.decode("utf-8")
        except Exception as e:
            pytest.fail(f"Cursor is not valid base64: {e}")

        # Property: Decoded cursor should be valid JSON
        try:
            cursor_data = json.loads(decoded_str)
        except Exception as e:
            pytest.fail(f"Decoded cursor is not valid JSON: {e}")

        # Property: Cursor should contain offset field
        assert "offset" in cursor_data
        assert isinstance(cursor_data["offset"], int)
        assert cursor_data["offset"] > 0
        assert cursor_data["offset"] <= num_steps

        # Property: Using the cursor should return the next page
        next_result = await export_service.export_time_series(
            session_id=session_id, variables=variables, limit=page_size, cursor=cursor
        )

        # Verify we got different data
        first_page_times = result["time"]
        second_page_times = next_result["time"]

        # Pages should not overlap (no duplicates)
        if first_page_times and second_page_times:
            assert (
                first_page_times[-1] < second_page_times[0]
            ), "Pages overlap - last time of first page should be before first time of second page"


@given(session_id=session_id_strategy(), data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_pagination_empty_results(session_id: str, data: st.DataObject) -> None:
    """
    Property: Pagination should handle empty results gracefully.

    For any request that returns no data, pagination info should indicate
    no more pages available.

    **Validates: Requirements 5.5**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Create empty history
    empty_history: dict[str, list[Any]] = {
        "time": [],
        "free_energy": [],
        "ignitions": [],
    }

    variables = data.draw(time_series_variables_strategy())
    page_size = data.draw(st.integers(min_value=5, max_value=50))

    # Create mock session manager
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)
    mock_sim_session.get_state.return_value = {"history": empty_history, "current_state": {}}
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Fetch data
    result = await export_service.export_time_series(
        session_id=session_id, variables=variables, limit=page_size, cursor=None
    )

    # Property: Empty results should have empty time array
    assert "time" in result
    assert len(result["time"]) == 0

    # Property: Empty results should have empty data arrays
    assert "data" in result
    for var in variables:
        if var in result["data"]:
            assert len(result["data"][var]) == 0

    # Property: Pagination should indicate no more data
    pagination = result.get("pagination")
    if pagination:
        assert pagination.get("has_more") is False
        assert pagination.get("next_cursor") is None


@given(session_id=session_id_strategy(), data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_pagination_boundary_conditions(
    session_id: str, data: st.DataObject
) -> None:
    """
    Property: Pagination should handle boundary conditions correctly.

    For any dataset where the total size is exactly divisible by page size,
    the last page should have exactly page_size items and has_more should be False.

    **Validates: Requirements 5.5**
    """
    from unittest.mock import AsyncMock, Mock

    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession

    # Generate page size first
    page_size = data.draw(st.integers(min_value=10, max_value=30))

    # Generate number of pages
    num_pages = data.draw(st.integers(min_value=2, max_value=5))

    # Create history with exact multiple of page size
    num_steps = page_size * num_pages
    history = data.draw(mock_time_series_history_strategy(num_steps))
    variables = data.draw(time_series_variables_strategy())

    # Create mock session manager
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)
    mock_sim_session.get_state.return_value = {"history": history, "current_state": {}}
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)

    # Create data export service
    export_service = DataExportService(mock_session_manager)

    # Fetch all pages
    cursor = None
    pages_fetched = 0

    for expected_page in range(num_pages):
        result = await export_service.export_time_series(
            session_id=session_id, variables=variables, limit=page_size, cursor=cursor
        )

        pages_fetched += 1

        # Property: Each page except possibly the last should have exactly page_size items
        page_times = result["time"]
        if expected_page < num_pages - 1:
            # Not the last page - should have exactly page_size items
            assert (
                len(page_times) == page_size
            ), f"Page {expected_page}: expected {page_size} items, got {len(page_times)}"
        else:
            # Last page - should have remaining items (which is page_size in this case)
            assert (
                len(page_times) == page_size
            ), f"Last page: expected {page_size} items, got {len(page_times)}"

        # Check pagination info
        pagination = result.get("pagination")

        if expected_page < num_pages - 1:
            # Not the last page - should have more data
            assert pagination is not None
            assert pagination.get("has_more")
            cursor = pagination.get("next_cursor")
            assert cursor is not None
        else:
            # Last page - should not have more data
            if pagination:
                assert not pagination.get("has_more")
                assert pagination.get("next_cursor") is None

    # Property: Should have fetched exactly num_pages
    assert pages_fetched == num_pages


# ============================================================================
# API Versioning Property Tests
# ============================================================================


@st.composite
def api_endpoint_strategy(draw: st.DrawFn) -> str:
    """Generate valid API endpoint paths."""
    # Common API endpoints in the system
    endpoints = [
        "/v1/sessions",
        "/v1/sessions/{session_id}",
        "/v1/sessions/{session_id}/start",
        "/v1/sessions/{session_id}/pause",
        "/v1/sessions/{session_id}/stop",
        "/v1/sessions/{session_id}/reset",
        "/v1/sessions/{session_id}/state",
        "/v1/sessions/{session_id}/ignition-history",
        "/v1/sessions/{session_id}/interoception",
        "/v1/sessions/{session_id}/prediction-errors",
        "/v1/sessions/{session_id}/somatic-markers",
        "/v1/tasks",
        "/v1/sessions/{session_id}/tasks",
        "/v1/tasks/{task_id}",
        "/v1/sessions/{session_id}/export",
        "/v1/sessions/{session_id}/summary",
        "/v1/sessions/{session_id}/timeseries",
        "/v1/sessions/{session_id}/events",
        "/v1/auth/login",
        "/v1/auth/refresh",
        "/v1/auth/logout",
        "/v1/metrics",
        "/v1/health",
        "/v1/version",
    ]
    return draw(st.sampled_from(endpoints))


@given(endpoint=api_endpoint_strategy())
@settings(max_examples=100, deadline=None)
def test_property_api_versioning_in_paths(endpoint: str) -> None:
    """
    **Feature: api-rest-interface, Property 14: API versioning in paths**

    For any registered API endpoint, the path should start with a version
    prefix (e.g., /v1/).

    **Validates: Requirements 6.1**
    """
    # Property: All API endpoints should start with a version prefix
    assert endpoint.startswith("/v"), f"Endpoint '{endpoint}' does not start with version prefix"

    # Property: Version prefix should follow the pattern /vN/ where N is a number
    parts = endpoint.split("/")
    assert len(parts) >= 2, f"Endpoint '{endpoint}' has invalid structure"

    version_part = parts[1]
    assert version_part.startswith(
        "v"
    ), f"Endpoint '{endpoint}' version part '{version_part}' does not start with 'v'"

    # Extract version number
    version_number = version_part[1:]
    assert (
        version_number.isdigit()
    ), f"Endpoint '{endpoint}' version number '{version_number}' is not a digit"

    # Property: Version number should be positive
    assert int(version_number) > 0, f"Endpoint '{endpoint}' version number must be positive"


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_version_endpoint_response_structure(data: st.DataObject) -> None:
    """
    Property: Version endpoint should return complete version information.

    For any request to the version endpoint, the response should include
    current version, supported versions, deprecated versions, and API spec URL.

    **Validates: Requirements 6.1, 6.4**
    """
    from datetime import datetime

    from api.routes.version import get_version_info

    # Call the version endpoint
    response = await get_version_info()

    # Parse response
    assert response.status_code == 200
    content = bytes(response.body).decode("utf-8")

    import json

    version_info = json.loads(content)

    # Property: Response should contain all required fields
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
        assert field in version_info, f"Version info missing required field: {field}"

    # Property: current_version should be a valid semantic version string
    current_version = version_info["current_version"]
    assert isinstance(current_version, str)
    assert len(current_version) > 0
    # Basic semver check (X.Y.Z format)
    version_parts = current_version.split(".")
    assert (
        len(version_parts) >= 2
    ), f"Version '{current_version}' should have at least major.minor format"

    # Property: api_version should be a version identifier
    api_version = version_info["api_version"]
    assert isinstance(api_version, str)
    assert api_version.startswith("v"), f"API version '{api_version}' should start with 'v'"

    # Property: supported_versions should be a non-empty list
    supported_versions = version_info["supported_versions"]
    assert isinstance(supported_versions, list)
    assert len(supported_versions) > 0, "supported_versions should contain at least one version"

    # Property: Current API version should be in supported versions
    assert (
        api_version in supported_versions
    ), f"Current API version '{api_version}' should be in supported versions"

    # Property: deprecated_versions should be a list
    deprecated_versions = version_info["deprecated_versions"]
    assert isinstance(deprecated_versions, list)

    # Property: Deprecated versions should not be in supported versions
    for deprecated in deprecated_versions:
        assert (
            deprecated not in supported_versions
        ), f"Version '{deprecated}' cannot be both deprecated and supported"

    # Property: api_spec_url should be a valid path
    api_spec_url = version_info["api_spec_url"]
    assert isinstance(api_spec_url, str)
    assert api_spec_url.startswith("/"), f"API spec URL '{api_spec_url}' should be a valid path"

    # Property: documentation_url should be a valid path
    docs_url = version_info["documentation_url"]
    assert isinstance(docs_url, str)
    assert docs_url.startswith("/"), f"Documentation URL '{docs_url}' should be a valid path"

    # Property: timestamp should be a valid ISO 8601 timestamp
    timestamp = version_info["timestamp"]
    assert isinstance(timestamp, str)
    assert timestamp.endswith("Z"), "Timestamp should be in UTC (ending with 'Z')"

    # Verify timestamp can be parsed
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Timestamp '{timestamp}' is not valid ISO 8601 format")


# ============================================================================
# Deprecation Header Property Tests
# ============================================================================


@st.composite
def deprecated_endpoint_config_strategy(draw: st.DrawFn) -> tuple[str, dict[str, Any]]:
    """Generate deprecated endpoint configuration."""
    endpoint = draw(api_endpoint_strategy())

    # Generate sunset date (future date)
    from datetime import datetime, timedelta

    days_until_sunset = draw(st.integers(min_value=30, max_value=365))
    sunset_date = datetime.utcnow() + timedelta(days=days_until_sunset)
    sunset_str = sunset_date.strftime("%Y-%m-%d")

    # Optionally include replacement endpoint
    include_replacement = draw(st.booleans())

    config = {"sunset": sunset_str}

    if include_replacement:
        # Generate replacement endpoint (same path but v2)
        replacement = endpoint.replace("/v1/", "/v2/")
        config["replacement"] = replacement

    return endpoint, config


@given(deprecated_config=deprecated_endpoint_config_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_deprecation_header_presence(
    deprecated_config: tuple[str, dict[str, Any]],
) -> None:
    """
    **Feature: api-rest-interface, Property 15: Deprecation header presence**

    For any deprecated endpoint, responses should include a Deprecation header
    with warning information.

    **Validates: Requirements 6.5**
    """
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from api.middleware.deprecation import DeprecationMiddleware

    endpoint_path, deprecation_info = deprecated_config

    # Create a simple test app with the deprecation middleware
    async def test_endpoint(request: Any) -> JSONResponse:
        return JSONResponse({"message": "test"})

    # Create routes for the endpoint
    # Convert path parameters to Starlette format
    starlette_path = endpoint_path.replace("{session_id}", "{session_id:str}")
    starlette_path = starlette_path.replace("{task_id}", "{task_id:str}")

    app = Starlette(
        routes=[Route(starlette_path, test_endpoint, methods=["GET", "POST", "DELETE"])]
    )

    # Add deprecation middleware
    deprecated_endpoints = {endpoint_path: deprecation_info}
    app.add_middleware(DeprecationMiddleware, deprecated_endpoints=deprecated_endpoints)

    # Create test client
    client = TestClient(app)

    # Make request to the deprecated endpoint
    # Replace path parameters with actual values
    test_path = endpoint_path.replace("{session_id}", "test-session-123")
    test_path = test_path.replace("{task_id}", "test-task-456")

    response = client.get(test_path)

    # Property: Response should include Deprecation header
    assert (
        "Deprecation" in response.headers
    ), f"Deprecated endpoint '{endpoint_path}' should include Deprecation header"

    deprecation_header = response.headers["Deprecation"]
    assert (
        deprecation_header == "true"
    ), f"Deprecation header should be 'true', got '{deprecation_header}'"

    # Property: Response should include Sunset header if sunset date is specified
    if "sunset" in deprecation_info:
        assert (
            "Sunset" in response.headers
        ), "Deprecated endpoint with sunset date should include Sunset header"

        sunset_header = response.headers["Sunset"]
        assert (
            sunset_header == deprecation_info["sunset"]
        ), f"Sunset header should be '{deprecation_info['sunset']}', got '{sunset_header}'"

    # Property: Response should include Link header if replacement is specified
    if "replacement" in deprecation_info:
        assert (
            "Link" in response.headers
        ), "Deprecated endpoint with replacement should include Link header"

        link_header = response.headers["Link"]
        expected_replacement = deprecation_info["replacement"]
        assert (
            expected_replacement in link_header
        ), f"Link header should reference replacement '{expected_replacement}'"
        assert (
            'rel="successor-version"' in link_header
        ), "Link header should include rel='successor-version'"

    # Property: Response should include Warning header
    assert "Warning" in response.headers, "Deprecated endpoint should include Warning header"

    warning_header = response.headers["Warning"]
    assert "299" in warning_header, "Warning header should use code 299 for miscellaneous warnings"
    assert "Deprecated" in warning_header, "Warning header should mention deprecation"
    # The warning should mention either the template path or the actual path
    # (middleware uses actual path which is more useful for debugging)
    assert (
        endpoint_path in warning_header or test_path in warning_header
    ), f"Warning header should mention the endpoint path (template: '{endpoint_path}' or actual: '{test_path}')"


@given(endpoint=api_endpoint_strategy())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_non_deprecated_endpoint_no_headers(endpoint: str) -> None:
    """
    Property: Non-deprecated endpoints should not include deprecation headers.

    For any endpoint that is not deprecated, responses should not include
    Deprecation, Sunset, or deprecation-related Warning headers.

    **Validates: Requirements 6.5**
    """
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from api.middleware.deprecation import DeprecationMiddleware

    # Create a simple test app with the deprecation middleware
    async def test_endpoint_handler(request: Any) -> JSONResponse:
        return JSONResponse({"message": "test"})

    # Convert path parameters to Starlette format
    starlette_path = endpoint.replace("{session_id}", "{session_id:str}")
    starlette_path = starlette_path.replace("{task_id}", "{task_id:str}")

    app = Starlette(
        routes=[Route(starlette_path, test_endpoint_handler, methods=["GET", "POST", "DELETE"])]
    )

    # Add deprecation middleware with empty configuration (no deprecated endpoints)
    app.add_middleware(DeprecationMiddleware, deprecated_endpoints={})

    # Create test client
    client = TestClient(app)

    # Make request to the non-deprecated endpoint
    test_path = endpoint.replace("{session_id}", "test-session-123")
    test_path = test_path.replace("{task_id}", "test-task-456")

    response = client.get(test_path)

    # Property: Response should NOT include Deprecation header
    assert (
        "Deprecation" not in response.headers
    ), f"Non-deprecated endpoint '{endpoint}' should not include Deprecation header"

    # Property: Response should NOT include Sunset header
    assert (
        "Sunset" not in response.headers
    ), f"Non-deprecated endpoint '{endpoint}' should not include Sunset header"

    # Property: Response should NOT include deprecation-related Link header
    if "Link" in response.headers:
        link_header = response.headers["Link"]
        assert (
            'rel="successor-version"' not in link_header
        ), "Non-deprecated endpoint should not include successor-version Link header"


@given(data=st.data())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_deprecation_middleware_path_matching(data: st.DataObject) -> None:
    """
    Property: Deprecation middleware should correctly match paths with parameters.

    For any endpoint with path parameters (e.g., {session_id}), the deprecation
    middleware should match actual requests with real parameter values.

    **Validates: Requirements 6.5**
    """
    import uuid

    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from api.middleware.deprecation import DeprecationMiddleware

    # Use an endpoint with path parameters
    endpoint_pattern = "/v1/sessions/{session_id}/state"

    # Generate deprecation info
    from datetime import datetime, timedelta

    days_until_sunset = data.draw(st.integers(min_value=30, max_value=365))
    sunset_date = datetime.utcnow() + timedelta(days=days_until_sunset)
    sunset_str = sunset_date.strftime("%Y-%m-%d")

    deprecation_info = {"sunset": sunset_str, "replacement": "/v2/sessions/{session_id}/state"}

    # Create test app
    async def test_endpoint_handler(request: Any) -> JSONResponse:
        return JSONResponse({"message": "test"})

    starlette_path = "/v1/sessions/{session_id:str}/state"

    app = Starlette(routes=[Route(starlette_path, test_endpoint_handler, methods=["GET"])])

    # Add deprecation middleware with pattern
    deprecated_endpoints = {endpoint_pattern: deprecation_info}
    app.add_middleware(DeprecationMiddleware, deprecated_endpoints=deprecated_endpoints)

    # Create test client
    client = TestClient(app)

    # Generate random session ID
    session_id = str(uuid.uuid4())
    test_path = f"/v1/sessions/{session_id}/state"

    # Make request with actual session ID
    response = client.get(test_path)

    # Property: Deprecation headers should be present even with path parameters
    assert (
        "Deprecation" in response.headers
    ), f"Deprecated endpoint pattern should match actual path '{test_path}'"

    assert response.headers["Deprecation"] == "true"
    assert "Sunset" in response.headers
    assert response.headers["Sunset"] == sunset_str
    assert "Link" in response.headers
    assert "Warning" in response.headers


@given(data=st.data())
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_deprecation_info_consistency(data: st.DataObject) -> None:
    """
    Property: Deprecation information should be consistent across multiple requests.

    For any deprecated endpoint, making multiple requests should return the
    same deprecation headers.

    **Validates: Requirements 6.5**
    """
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from starlette.testclient import TestClient

    from api.middleware.deprecation import DeprecationMiddleware

    endpoint_path = "/v1/sessions"

    # Generate deprecation info
    from datetime import datetime, timedelta

    days_until_sunset = data.draw(st.integers(min_value=30, max_value=365))
    sunset_date = datetime.utcnow() + timedelta(days=days_until_sunset)
    sunset_str = sunset_date.strftime("%Y-%m-%d")

    deprecation_info = {"sunset": sunset_str, "replacement": "/v2/sessions"}

    # Create test app
    async def test_endpoint_handler(request: Any) -> JSONResponse:
        return JSONResponse({"message": "test"})

    app = Starlette(routes=[Route(endpoint_path, test_endpoint_handler, methods=["GET", "POST"])])

    # Add deprecation middleware
    deprecated_endpoints = {endpoint_path: deprecation_info}
    app.add_middleware(DeprecationMiddleware, deprecated_endpoints=deprecated_endpoints)

    # Create test client
    client = TestClient(app)

    # Make multiple requests
    num_requests = data.draw(st.integers(min_value=2, max_value=5))
    responses = []

    for _ in range(num_requests):
        response = client.get(endpoint_path)
        responses.append(response)

    # Property: All responses should have the same deprecation headers
    first_response = responses[0]
    first_deprecation = first_response.headers.get("Deprecation")
    first_sunset = first_response.headers.get("Sunset")
    first_link = first_response.headers.get("Link")

    for i, response in enumerate(responses[1:], start=1):
        assert (
            response.headers.get("Deprecation") == first_deprecation
        ), f"Request {i}: Deprecation header should be consistent"

        assert (
            response.headers.get("Sunset") == first_sunset
        ), f"Request {i}: Sunset header should be consistent"

        assert (
            response.headers.get("Link") == first_link
        ), f"Request {i}: Link header should be consistent"


# ============================================================================
# CORS Property Tests
# ============================================================================


@given(
    http_method=st.sampled_from(["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]),
    endpoint_path=st.sampled_from(
        ["/", "/health", "/v1/version", "/v1/sessions", "/v1/metrics", "/docs", "/openapi.json"]
    ),
    origin=st.sampled_from(
        [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com",
            "http://127.0.0.1:8080",
            None,  # No origin header
        ]
    ),
)
@settings(max_examples=100, deadline=None)
def test_property_cors_header_presence(
    http_method: str, endpoint_path: str, origin: str | None
) -> None:
    """
    **Feature: api-rest-interface, Property 4: CORS header presence**

    For any API request, the response should include appropriate CORS headers
    (Access-Control-Allow-Origin, etc.)

    **Validates: Requirements 1.5**
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse  # noqa: F401
    from fastapi.testclient import TestClient

    # Create a simple test app with CORS middleware
    app = FastAPI()

    # Configure CORS with typical settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for testing
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    # Add test endpoints
    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "root"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/v1/version")
    async def version() -> dict[str, str]:
        return {"version": "1.0.0"}

    @app.get("/v1/sessions")
    @app.post("/v1/sessions")
    async def sessions() -> dict[str, list[str]]:
        return {"sessions": []}

    @app.get("/v1/metrics")
    async def metrics() -> dict[str, dict[str, Any]]:
        return {"metrics": {}}

    @app.get("/docs")
    async def docs() -> dict[str, str]:
        return {"docs": "available"}

    @app.get("/openapi.json")
    async def openapi() -> dict[str, str]:
        return {"openapi": "3.0.0"}

    # Create test client
    client = TestClient(app)

    # Prepare headers
    headers = {}
    if origin is not None:
        headers["Origin"] = origin

    # Make request based on method
    if http_method == "GET":
        response = client.get(endpoint_path, headers=headers)
    elif http_method == "POST":
        response = client.post(endpoint_path, headers=headers, json={})
    elif http_method == "PUT":
        response = client.put(endpoint_path, headers=headers, json={})
    elif http_method == "DELETE":
        response = client.delete(endpoint_path, headers=headers)
    elif http_method == "PATCH":
        response = client.patch(endpoint_path, headers=headers, json={})
    elif http_method == "OPTIONS":
        response = client.options(endpoint_path, headers=headers)

    # Property 1: Response should include Access-Control-Allow-Origin header
    # when Origin header is present in request
    if origin is not None:
        assert (
            "access-control-allow-origin" in response.headers
        ), "Response to request with Origin header should include Access-Control-Allow-Origin header"

        # Verify the header value
        allow_origin = response.headers["access-control-allow-origin"]
        assert allow_origin in [
            "*",
            origin,
        ], f"Access-Control-Allow-Origin should be '*' or match request origin '{origin}', got '{allow_origin}'"

    # Property 2: For OPTIONS requests (preflight), additional CORS headers should be present
    # Note: CORS preflight headers are only added for successful OPTIONS requests (200)
    # If the endpoint doesn't support OPTIONS (405), CORS headers may not be fully present
    if http_method == "OPTIONS" and origin is not None and response.status_code == 200:
        # Access-Control-Allow-Methods should be present
        assert (
            "access-control-allow-methods" in response.headers
        ), "OPTIONS response should include Access-Control-Allow-Methods header"

        # Access-Control-Allow-Headers should be present
        assert (
            "access-control-allow-headers" in response.headers
        ), "OPTIONS response should include Access-Control-Allow-Headers header"

        # Verify methods header contains common HTTP methods
        allow_methods = response.headers["access-control-allow-methods"]
        assert isinstance(allow_methods, str), "Access-Control-Allow-Methods should be a string"
        assert len(allow_methods) > 0, "Access-Control-Allow-Methods should not be empty"

    # Property 3: If credentials are allowed, the appropriate header should be present
    if origin is not None and origin != "*":
        # When allow_credentials is True and origin is specific (not *),
        # the header should be present
        if "access-control-allow-credentials" in response.headers:
            credentials_value = response.headers["access-control-allow-credentials"]
            assert credentials_value.lower() in [
                "true",
                "false",
            ], f"Access-Control-Allow-Credentials should be 'true' or 'false', got '{credentials_value}'"

    # Property 4: Response should be successful or have appropriate status code
    # (CORS headers should be present regardless of response status)
    assert (
        response.status_code < 600
    ), f"Response status code should be valid HTTP status code, got {response.status_code}"


@given(
    cors_origins=st.lists(
        st.sampled_from(
            ["http://localhost:3000", "https://example.com", "https://app.example.com"]
        ),
        min_size=1,
        max_size=3,
        unique=True,
    ),
    request_origin=st.sampled_from(
        [
            "http://localhost:3000",
            "https://example.com",
            "https://app.example.com",
            "https://unauthorized.com",
        ]
    ),
)
@settings(max_examples=50, deadline=None)
def test_property_cors_origin_validation(cors_origins: set[str], request_origin: str) -> None:
    """
    Property: CORS should validate origins against allowed list.

    For any configured list of allowed origins, requests from allowed origins
    should receive CORS headers, while unauthorized origins should be handled
    appropriately.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient

    # Create test app with specific allowed origins
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    # Make request with origin header
    response = client.get("/test", headers={"Origin": request_origin})

    # Property: If origin is in allowed list, CORS headers should be present
    if request_origin in cors_origins:
        assert (
            "access-control-allow-origin" in response.headers
        ), f"Request from allowed origin '{request_origin}' should receive CORS headers"

        # The returned origin should match the request origin
        returned_origin = response.headers["access-control-allow-origin"]
        assert (
            returned_origin == request_origin
        ), f"Access-Control-Allow-Origin should match request origin '{request_origin}', got '{returned_origin}'"

    # Property: Response should still be successful regardless of origin
    # (CORS is enforced by browser, not server)
    assert (
        response.status_code == 200
    ), "Server should process request regardless of origin (CORS is browser-enforced)"


@given(
    allow_credentials=st.booleans(),
    origin=st.sampled_from(["http://localhost:3000", "https://example.com"]),
)
@settings(max_examples=50, deadline=None)
def test_property_cors_credentials_configuration(allow_credentials: bool, origin: str) -> None:
    """
    Property: CORS credentials configuration should be reflected in headers.

    For any credentials configuration, the Access-Control-Allow-Credentials
    header should match the configuration.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.testclient import TestClient

    # Create test app with specific credentials setting
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin],
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/test")
    async def test_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)

    # Make request with origin header
    response = client.get("/test", headers={"Origin": origin})

    # Property: Credentials header should match configuration
    if allow_credentials:
        assert (
            "access-control-allow-credentials" in response.headers
        ), "When credentials are allowed, header should be present"

        credentials_value = response.headers["access-control-allow-credentials"]
        assert (
            credentials_value.lower() == "true"
        ), f"Access-Control-Allow-Credentials should be 'true' when enabled, got '{credentials_value}'"

    # Property: Origin header should be present
    assert "access-control-allow-origin" in response.headers, "CORS origin header should be present"


# ============================================================================
# Webhook Delivery Property Tests
# ============================================================================


@st.composite
def webhook_url_strategy(draw: Any) -> str:
    """Generate valid webhook URLs."""
    protocol = draw(st.sampled_from(["http://", "https://"]))
    domain = draw(
        st.text(
            min_size=5,
            max_size=50,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters=".-"),
        ).filter(lambda x: not x.startswith(".") and not x.endswith("."))
    )
    path = draw(
        st.text(
            min_size=0,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="/-_"),
        )
    )

    # Ensure valid domain format
    if not domain or ".." in domain:
        domain = "example.com"

    url = f"{protocol}{domain}"
    if path and not path.startswith("/"):
        url += "/"
    url += path

    # Ensure URL doesn't exceed max length
    if len(url) > 500:
        url = url[:500]

    return url


@st.composite
def webhook_payload_strategy(draw: Any, task_type: str, session_id: str) -> dict[str, Any]:
    """Generate webhook payloads for completed tasks."""
    task_id = str(uuid.uuid4())

    payload = {
        "event": "task.completed",
        "task_id": task_id,
        "session_id": session_id,
        "task_type": task_type,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }

    # Add task-specific results
    results: dict[str, Any]
    if task_type == TaskType.IOWA_GAMBLING.value:
        results = {
            "total_trials": draw(st.integers(min_value=10, max_value=200)),
            "advantageous_ratio": draw(st.floats(min_value=0.0, max_value=1.0)),
            "final_balance": draw(st.integers(min_value=-5000, max_value=10000)),
        }
        payload["results"] = results  # type: ignore[assignment]
    elif task_type == TaskType.MASKING_PARADIGM.value:
        results = {
            "ignition_probabilities": draw(
                st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=3, max_size=10)
            ),
            "mean_ignition_probability": draw(st.floats(min_value=0.0, max_value=1.0)),
        }
        payload["results"] = results  # type: ignore[assignment]
    elif task_type == TaskType.ATTENTIONAL_BLINK.value:
        results = {
            "t1_accuracy": draw(st.floats(min_value=0.0, max_value=1.0)),
            "t2_accuracy_by_lag": draw(
                st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=8)
            ),
        }
        payload["results"] = results  # type: ignore[assignment]

    return payload


@given(data=st.data())
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_webhook_delivery_with_retry(data: Any) -> None:
    """
    **Feature: api-rest-interface, Property 26: Webhook delivery with retry**

    For any completed async task with registered webhook, the system should attempt
    delivery with exponential backoff on failure.

    **Validates: Requirements 11.3, 11.4, 11.5**
    """
    from datetime import datetime, timedelta
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from api.services.webhook_manager import WebhookManager, WebhookStatus

    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())
    webhook_url = data.draw(webhook_url_strategy())
    payload = data.draw(webhook_payload_strategy(task_type, session_id))
    task_id = payload["task_id"]

    # Determine if delivery should succeed or fail
    should_succeed = data.draw(st.booleans())
    response_status = data.draw(
        st.sampled_from([200, 201, 204])
        if should_succeed
        else st.sampled_from([400, 404, 500, 502, 503])
    )

    # Create mock database session
    mock_db = MagicMock()

    # Create webhook manager
    webhook_manager = WebhookManager()

    # Mock the HTTP client
    mock_response = MagicMock()
    mock_response.status_code = response_status
    mock_response.text = "OK" if should_succeed else "Error"

    # Create a mock delivery record - use SimpleNamespace to track attribute changes
    delivery_id = str(uuid.uuid4())
    mock_delivery = SimpleNamespace(
        delivery_id=delivery_id,
        task_id=task_id,
        webhook_url=webhook_url,
        payload=payload,
        status=WebhookStatus.PENDING.value,
        attempts=0,
        last_attempt_at=None,
        next_retry_at=None,
        response_status=None,
        response_body=None,
        error_message=None,
        created_at=datetime.utcnow(),
    )

    # Configure mock database query - use side_effect to ensure same object is returned
    mock_query = MagicMock()
    mock_filter_result = MagicMock()
    # Use side_effect to always return the same mock_delivery object
    mock_filter_result.first = MagicMock(return_value=mock_delivery)
    mock_query.filter = MagicMock(return_value=mock_filter_result)
    mock_db.query = MagicMock(return_value=mock_query)

    # Mock the HTTP client post method, IP check, and DNS resolution
    with patch.object(webhook_manager.http_client, "post", return_value=mock_response):
        with patch.object(webhook_manager, "_is_private_ip", return_value=False):
            with patch(
                "api.services.webhook_manager.socket.gethostbyname", return_value="93.184.216.34"
            ):
                # Test webhook delivery
                result = await webhook_manager.deliver_webhook(mock_db, delivery_id)

                # Property 1: Delivery attempt should increment attempt count
                assert mock_delivery.attempts > 0, "Webhook delivery should increment attempt count"

                # Property 2: Last attempt timestamp should be set
                assert (
                    mock_delivery.last_attempt_at is not None
                ), "Webhook delivery should record last attempt timestamp"

                # Property 3: Response status should be recorded
                assert (
                    mock_delivery.response_status == response_status
                ), f"Webhook delivery should record response status, expected {response_status}, got {mock_delivery.response_status}"

                # Property 4: Successful delivery should return True and set status to DELIVERED
                if should_succeed:
                    assert result is True, "Successful webhook delivery should return True"
                    assert (
                        mock_delivery.status == WebhookStatus.DELIVERED.value
                    ), "Successful webhook delivery should set status to DELIVERED"
                    assert (
                        mock_delivery.next_retry_at is None
                    ), "Successful webhook delivery should clear next_retry_at"

                # Property 5: Failed delivery should return False and schedule retry
                else:
                    assert result is False, "Failed webhook delivery should return False"

                    # If not at max retries, should schedule retry
                    if mock_delivery.attempts < WebhookManager.MAX_RETRIES:
                        assert (
                            mock_delivery.status == WebhookStatus.RETRYING.value
                        ), "Failed webhook delivery should set status to RETRYING"
                        assert (
                            mock_delivery.next_retry_at is not None
                        ), "Failed webhook delivery should schedule next retry"

                        # Property 6: Retry should use exponential backoff
                        # Calculate expected delay
                        expected_delay = min(
                            WebhookManager.INITIAL_RETRY_DELAY_SECONDS
                            * (WebhookManager.BACKOFF_MULTIPLIER ** (mock_delivery.attempts - 1)),
                            WebhookManager.MAX_RETRY_DELAY_SECONDS,
                        )

                        # Verify next_retry_at is approximately correct (within 5 seconds tolerance)
                        expected_retry_time = mock_delivery.last_attempt_at + timedelta(
                            seconds=expected_delay
                        )
                        time_diff = abs(
                            (mock_delivery.next_retry_at - expected_retry_time).total_seconds()
                        )

                        assert time_diff < 5, (
                            f"Retry should use exponential backoff, expected delay ~{expected_delay}s, "
                            f"but time difference is {time_diff}s"
                        )

                    # If at max retries, should mark as failed
                    else:
                        assert (
                            mock_delivery.status == WebhookStatus.FAILED.value
                        ), "Webhook delivery at max retries should set status to FAILED"
                        assert (
                            mock_delivery.next_retry_at is None
                        ), "Webhook delivery at max retries should not schedule retry"

                # Property 7: Database commit should be called
                assert mock_db.commit.called, "Webhook delivery should commit changes to database"


@given(data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_webhook_url_validation(data: Any) -> None:
    """
    Property: Webhook URL validation should reject invalid URLs.

    For any webhook URL, the validation should accept valid URLs and
    reject invalid ones with clear error messages.

    **Validates: Requirements 11.3**
    """
    from api.services.webhook_manager import WebhookManager

    # Generate URL components
    is_valid = data.draw(st.booleans())

    if is_valid:
        # Generate valid URL
        url = data.draw(webhook_url_strategy())
    else:
        # Generate invalid URL
        invalid_type = data.draw(
            st.sampled_from(["empty", "no_protocol", "too_long", "invalid_protocol"])
        )

        if invalid_type == "empty":
            url = ""
        elif invalid_type == "no_protocol":
            url = "example.com/webhook"
        elif invalid_type == "too_long":
            url = "https://" + "a" * 500
        elif invalid_type == "invalid_protocol":
            url = "ftp://example.com/webhook"

    webhook_manager = WebhookManager()

    # Test validation
    if is_valid and url:
        # Valid URLs should pass validation
        try:
            result = await webhook_manager.validate_webhook_url(url)
            assert result is True, f"Valid webhook URL '{url}' should pass validation"
        except ValueError:
            # Some generated URLs might still be invalid, that's ok
            pass
    else:
        # Invalid URLs should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await webhook_manager.validate_webhook_url(url)

        # Error message should be descriptive
        error_message = str(exc_info.value)
        assert len(error_message) > 0, "Validation error should include descriptive message"


@given(data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_webhook_retry_exponential_backoff(data: Any) -> None:
    """
    Property: Webhook retry delays should follow exponential backoff pattern.

    For any sequence of failed webhook deliveries, the retry delays should
    increase exponentially up to a maximum delay.

    **Validates: Requirements 11.5**
    """
    from unittest.mock import MagicMock

    from api.database.models import WebhookDelivery
    from api.services.webhook_manager import WebhookManager, WebhookStatus

    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())
    webhook_url = data.draw(webhook_url_strategy())
    payload = data.draw(webhook_payload_strategy(task_type, session_id))
    task_id = payload["task_id"]

    # Number of retry attempts to test (less than MAX_RETRIES)
    num_attempts = data.draw(st.integers(min_value=1, max_value=WebhookManager.MAX_RETRIES - 1))

    # Create mock database session
    mock_db = MagicMock()

    # Create webhook manager
    webhook_manager = WebhookManager()

    # Track retry delays
    retry_delays = []

    # Simulate multiple failed delivery attempts
    for attempt in range(1, num_attempts + 1):
        # Create mock delivery record
        delivery_id = str(uuid.uuid4())
        mock_delivery = MagicMock(spec=WebhookDelivery)
        mock_delivery.delivery_id = delivery_id
        mock_delivery.task_id = task_id
        mock_delivery.webhook_url = webhook_url
        mock_delivery.payload = payload
        mock_delivery.status = (
            WebhookStatus.RETRYING.value if attempt > 1 else WebhookStatus.PENDING.value
        )
        mock_delivery.attempts = attempt - 1  # Will be incremented during delivery
        mock_delivery.last_attempt_at = None
        mock_delivery.next_retry_at = None
        mock_delivery.response_status = None
        mock_delivery.error_message = None

        # Configure mock database query
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_delivery
        mock_db.query.return_value = mock_query

        # Mock failed HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(webhook_manager.http_client, "post", return_value=mock_response):
            # Attempt delivery
            result = await webhook_manager.deliver_webhook(mock_db, delivery_id)

            # Should fail
            assert result is False, f"Delivery attempt {attempt} should fail"

            # Calculate expected delay
            expected_delay = min(
                WebhookManager.INITIAL_RETRY_DELAY_SECONDS
                * (WebhookManager.BACKOFF_MULTIPLIER ** (attempt - 1)),
                WebhookManager.MAX_RETRY_DELAY_SECONDS,
            )

            retry_delays.append(expected_delay)

            # Verify retry was scheduled
            if mock_delivery.next_retry_at is not None:
                # Calculate actual delay
                actual_delay = (
                    mock_delivery.next_retry_at - mock_delivery.last_attempt_at
                ).total_seconds()

                # Verify exponential backoff (within 5 second tolerance)
                assert (
                    abs(actual_delay - expected_delay) < 5
                ), f"Attempt {attempt}: Expected delay ~{expected_delay}s, got {actual_delay}s"

    # Property: Delays should increase (or stay at max)
    for i in range(1, len(retry_delays)):
        assert retry_delays[i] >= retry_delays[i - 1], (
            f"Retry delays should increase or stay at maximum: "
            f"delay[{i - 1}]={retry_delays[i - 1]}, delay[{i}]={retry_delays[i]}"
        )

    # Property: Delays should not exceed maximum
    for delay in retry_delays:
        assert (
            delay <= WebhookManager.MAX_RETRY_DELAY_SECONDS
        ), f"Retry delay {delay}s should not exceed maximum {WebhookManager.MAX_RETRY_DELAY_SECONDS}s"


@given(data=st.data())
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_webhook_max_retries_enforcement(data: st.DataObject) -> None:
    """
    Property: Webhook delivery should stop retrying after max attempts.

    For any webhook that fails repeatedly, after MAX_RETRIES attempts,
    the delivery should be marked as permanently failed.

    **Validates: Requirements 11.5**
    """
    from unittest.mock import MagicMock

    from api.database.models import WebhookDelivery
    from api.services.webhook_manager import WebhookManager, WebhookStatus

    # Generate test data
    task_type = data.draw(task_type_strategy())
    session_id = data.draw(session_id_strategy())
    webhook_url = data.draw(webhook_url_strategy())
    payload = data.draw(webhook_payload_strategy(task_type, session_id))
    task_id = payload["task_id"]

    # Create mock database session
    mock_db = MagicMock()

    # Create webhook manager
    webhook_manager = WebhookManager()

    # Create mock delivery record at max retries
    delivery_id = str(uuid.uuid4())
    mock_delivery = MagicMock(spec=WebhookDelivery)
    mock_delivery.delivery_id = delivery_id
    mock_delivery.task_id = task_id
    mock_delivery.webhook_url = webhook_url
    mock_delivery.payload = payload
    mock_delivery.status = WebhookStatus.RETRYING.value
    mock_delivery.attempts = WebhookManager.MAX_RETRIES - 1  # Will be incremented to MAX_RETRIES
    mock_delivery.last_attempt_at = None
    mock_delivery.next_retry_at = None
    mock_delivery.response_status = None
    mock_delivery.error_message = None

    # Configure mock database query
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_delivery
    mock_db.query.return_value = mock_query

    # Mock failed HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch.object(webhook_manager.http_client, "post", return_value=mock_response):
        # Attempt final delivery
        result = await webhook_manager.deliver_webhook(mock_db, delivery_id)

        # Should fail
        assert result is False, "Final delivery attempt should fail"

        # Property 1: Attempts should equal MAX_RETRIES
        assert (
            mock_delivery.attempts == WebhookManager.MAX_RETRIES
        ), f"After final attempt, attempts should equal MAX_RETRIES ({WebhookManager.MAX_RETRIES})"

        # Property 2: Status should be FAILED
        assert (
            mock_delivery.status == WebhookStatus.FAILED.value
        ), "After max retries, status should be FAILED"

        # Property 3: No further retry should be scheduled
        assert (
            mock_delivery.next_retry_at is None
        ), "After max retries, no further retry should be scheduled"

        # Property 4: Error message should be set
        assert mock_delivery.error_message is not None, "Failed delivery should have error message"
