"""
Property-based tests for API endpoints.

Tests universal properties that should hold across all valid API requests.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, AsyncMock, patch
import uuid

from api.services.task_executor import TaskExecutor, TaskType, TaskStatus


# ============================================================================
# Strategies for generating test data
# ============================================================================


@st.composite
def task_type_strategy(draw):
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
def task_parameters_strategy(draw, task_type):
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
def session_id_strategy(draw):
    """Generate valid session IDs (UUIDs)."""
    return str(uuid.uuid4())


@st.composite
def task_result_strategy(draw, task_type, session_id):
    """Generate mock task results for a given task type."""
    base_result = {"task_type": task_type, "session_id": session_id, "status": "completed"}

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
async def test_property_task_execution_round_trip(data):
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
async def test_property_task_status_tracking(data):
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
async def test_property_invalid_task_type_rejection(invalid_task_type, session_id):
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
async def test_property_async_task_status_tracking(data):
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
async def test_property_failed_task_status_tracking(data):
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


@given(data=st.data())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_async_task_status_tracking(data):
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


# ============================================================================
# Authentication and Authorization Property Tests
# ============================================================================


@st.composite
def user_credentials_strategy(draw):
    """Generate valid user credentials."""
    username = draw(st.text(min_size=3, max_size=50, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'
    )))
    password = draw(st.text(min_size=8, max_size=100))
    roles = draw(st.lists(
        st.sampled_from(['admin', 'researcher', 'viewer']),
        min_size=1,
        max_size=3,
        unique=True
    ))
    return {
        'username': username,
        'password': password,
        'roles': roles
    }


@st.composite
def user_id_strategy(draw):
    """Generate valid user IDs (UUIDs)."""
    return str(uuid.uuid4())


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_authentication_token_round_trip(credentials, user_id):
    """
    **Feature: api-rest-interface, Property 16: Authentication token round-trip**

    For any valid credentials, authenticating should return a token that can be
    used to make authenticated requests successfully.

    **Validates: Requirements 7.1, 7.2**
    """
    from api.services.auth_manager import AuthManager
    from api.database.connection import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create AuthManager
        auth_manager = AuthManager(db)
        
        # Step 1: Create access token
        access_token = auth_manager.create_access_token(
            user_id=user_id,
            username=credentials['username'],
            roles=credentials['roles']
        )
        
        # Verify token was created
        assert access_token is not None
        assert isinstance(access_token, str)
        assert len(access_token) > 0
        
        # Step 2: Verify the token (round-trip)
        payload = auth_manager.verify_token(access_token, expected_type='access')
        
        # Verify payload contains correct information
        assert payload is not None
        assert payload.user_id == user_id
        assert payload.username == credentials['username']
        assert payload.roles == credentials['roles']
        assert payload.token_type == 'access'
        
        # Verify expiration is in the future
        from datetime import datetime
        assert payload.exp > datetime.utcnow()
        
    finally:
        db.close()


@given(credentials=user_credentials_strategy(), user_id=user_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_refresh_token_round_trip(credentials, user_id):
    """
    Property: Refresh tokens should also support round-trip verification.

    For any valid credentials, creating a refresh token and verifying it
    should return the same user information.

    **Validates: Requirements 7.1, 7.2**
    """
    from api.services.auth_manager import AuthManager
    from api.database.connection import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create AuthManager
        auth_manager = AuthManager(db)
        
        # Create refresh token
        refresh_token = auth_manager.create_refresh_token(
            user_id=user_id,
            username=credentials['username'],
            roles=credentials['roles']
        )
        
        # Verify token was created
        assert refresh_token is not None
        assert isinstance(refresh_token, str)
        assert len(refresh_token) > 0
        
        # Verify the token
        payload = auth_manager.verify_token(refresh_token, expected_type='refresh')
        
        # Verify payload
        assert payload.user_id == user_id
        assert payload.username == credentials['username']
        assert payload.roles == credentials['roles']
        assert payload.token_type == 'refresh'
        
    finally:
        db.close()


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy(),
    required_permission=st.sampled_from([
        'session:create', 'session:read', 'session:update', 'session:delete',
        'task:create', 'task:read', 'data:export', 'system:admin'
    ])
)
@settings(max_examples=100, deadline=None)
def test_property_authorization_enforcement(credentials, user_id, required_permission):
    """
    **Feature: api-rest-interface, Property 17: Authorization enforcement**

    For any operation requiring specific permissions, requests without those
    permissions should return 403 Forbidden.

    **Validates: Requirements 7.3, 7.5**
    """
    from api.services.authorization import (
        has_permission, Permission, get_permissions_for_roles
    )
    
    # Get user's permissions based on their roles
    user_permissions = get_permissions_for_roles(credentials['roles'])
    
    # Try to convert required_permission string to Permission enum
    try:
        perm_enum = Permission(required_permission)
    except ValueError:
        # If permission doesn't exist, skip this test case
        return
    
    # Check if user has the permission
    has_perm = has_permission(credentials['roles'], perm_enum)
    
    # Verify the result matches what we expect based on user's permissions
    expected_has_perm = perm_enum in user_permissions
    assert has_perm == expected_has_perm
    
    # If user doesn't have permission, verify check_permission raises error
    if not has_perm:
        from api.services.authorization import check_permission
        from api.exceptions import AuthorizationError
        
        with pytest.raises(AuthorizationError) as exc_info:
            check_permission(
                user_roles=credentials['roles'],
                required_permission=perm_enum,
                resource='test_resource',
                action='test_action'
            )
        
        # Verify error contains relevant information
        error = exc_info.value
        assert error.status_code == 403
        assert 'FORBIDDEN' in error.code or 'AUTHORIZATION' in error.code or 'INSUFFICIENT_PERMISSIONS' in error.code


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy(),
    expiration_seconds=st.integers(min_value=-3600, max_value=-1)
)
@settings(max_examples=100, deadline=None)
def test_property_expired_token_rejection(credentials, user_id, expiration_seconds):
    """
    **Feature: api-rest-interface, Property 18: Expired token rejection**

    For any expired JWT token, requests using that token should be rejected
    with 401 Unauthorized.

    **Validates: Requirements 7.4**
    """
    from api.services.auth_manager import AuthManager, TokenPayload
    from api.exceptions import ExpiredTokenError
    from api.database.connection import SessionLocal
    from datetime import datetime, timedelta
    import jwt
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create AuthManager
        auth_manager = AuthManager(db)
        
        # Create an expired token by manually setting expiration in the past
        expires_at = datetime.utcnow() + timedelta(seconds=expiration_seconds)
        
        payload = TokenPayload(
            user_id=user_id,
            username=credentials['username'],
            roles=credentials['roles'],
            exp=expires_at,
            token_type='access'
        )
        
        # Encode the token with past expiration
        expired_token = jwt.encode(
            payload.to_dict(),
            auth_manager.secret_key,
            algorithm=auth_manager.algorithm
        )
        
        # Verify token is actually expired
        assert expires_at < datetime.utcnow()
        
        # Attempt to verify the expired token - should raise ExpiredTokenError
        with pytest.raises(ExpiredTokenError) as exc_info:
            auth_manager.verify_token(expired_token, expected_type='access')
        
        # Verify error message indicates expiration
        error_message = str(exc_info.value)
        assert 'expired' in error_message.lower()
        
    finally:
        db.close()


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_invalid_token_rejection(credentials, user_id):
    """
    Property: Invalid or malformed tokens should be rejected.

    For any invalid token, verification should raise InvalidTokenError.

    **Validates: Requirements 7.2, 7.4**
    """
    from api.services.auth_manager import AuthManager
    from api.exceptions import InvalidTokenError
    from api.database.connection import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create AuthManager
        auth_manager = AuthManager(db)
        
        # Test various invalid tokens
        invalid_tokens = [
            'not.a.valid.token',
            'invalid_token_format',
            '',
            'Bearer token',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature'
        ]
        
        for invalid_token in invalid_tokens:
            # Attempt to verify invalid token - should raise InvalidTokenError
            with pytest.raises(InvalidTokenError):
                auth_manager.verify_token(invalid_token, expected_type='access')
        
    finally:
        db.close()


@given(
    credentials=user_credentials_strategy(),
    user_id=user_id_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_wrong_token_type_rejection(credentials, user_id):
    """
    Property: Using wrong token type should be rejected.

    For any token, verifying it with the wrong expected type should fail.

    **Validates: Requirements 7.2**
    """
    from api.services.auth_manager import AuthManager
    from api.exceptions import InvalidTokenError
    from api.database.connection import SessionLocal
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create AuthManager
        auth_manager = AuthManager(db)
        
        # Create an access token
        access_token = auth_manager.create_access_token(
            user_id=user_id,
            username=credentials['username'],
            roles=credentials['roles']
        )
        
        # Try to verify it as a refresh token - should fail
        with pytest.raises(InvalidTokenError) as exc_info:
            auth_manager.verify_token(access_token, expected_type='refresh')
        
        # Verify error mentions token type mismatch
        error_message = str(exc_info.value)
        assert 'type' in error_message.lower()
        
    finally:
        db.close()



# ============================================================================
# Rate Limiting Property Tests
# ============================================================================


@st.composite
def client_id_strategy(draw):
    """Generate valid client IDs."""
    client_type = draw(st.sampled_from(['user', 'ip']))
    if client_type == 'user':
        return f"user:{uuid.uuid4()}"
    else:
        # Generate valid IP addresses
        octets = [draw(st.integers(min_value=1, max_value=255)) for _ in range(4)]
        return f"ip:{'.'.join(map(str, octets))}"


@st.composite
def endpoint_strategy(draw):
    """Generate valid endpoint identifiers."""
    return draw(st.sampled_from([
        'global',
        'session:create',
        'session:read',
        'session:delete',
        'task:execute',
        'data:export'
    ]))


@given(
    client_id=client_id_strategy(),
    endpoint=endpoint_strategy(),
    num_requests=st.integers(min_value=1, max_value=150)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_enforcement(client_id, endpoint, num_requests):
    """
    **Feature: api-rest-interface, Property 19: Rate limit enforcement**

    For any client exceeding rate limits, subsequent requests should return
    429 Too Many Requests until the window resets.

    **Validates: Requirements 8.1, 8.2**
    """
    from api.services.rate_limiter import RateLimiter
    import redis.asyncio as redis
    from api.config import settings
    
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)
        
        # Reset any existing rate limits for this client/endpoint
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        
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
                client_id=client_id,
                endpoint=endpoint
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
        
        # Verify rate limiting behavior
        if num_requests <= max_allowed_requests:
            # All requests should be allowed
            assert allowed_count == num_requests
            assert denied_count == 0
        else:
            # Some requests should be allowed, rest denied
            assert allowed_count <= max_allowed_requests
            assert denied_count == num_requests - allowed_count
            assert denied_count > 0
            
            # Verify we allowed approximately the right number
            # (may be slightly less due to weight)
            assert allowed_count >= max_allowed_requests - 1
            assert allowed_count <= max_allowed_requests + 1
        
    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await redis_client.close()


@given(
    client_id=client_id_strategy(),
    endpoint=endpoint_strategy()
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_per_client_isolation(client_id, endpoint):
    """
    Property: Rate limits should be isolated per client.

    For any two different clients, one client hitting rate limits should
    not affect the other client's ability to make requests.

    **Validates: Requirements 8.2**
    """
    from api.services.rate_limiter import RateLimiter
    import redis.asyncio as redis
    from api.config import settings
    
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
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


@given(
    client_id=client_id_strategy(),
    endpoint1=endpoint_strategy(),
    endpoint2=endpoint_strategy()
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_per_endpoint_isolation(client_id, endpoint1, endpoint2):
    """
    Property: Rate limits should be isolated per endpoint.

    For any client, hitting rate limits on one endpoint should not
    affect their ability to access other endpoints.

    **Validates: Requirements 8.2**
    """
    from api.services.rate_limiter import RateLimiter
    import redis.asyncio as redis
    from api.config import settings
    
    # Skip if endpoints are the same
    assume(endpoint1 != endpoint2)
    
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
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
    custom_window=st.integers(min_value=10, max_value=120)
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_custom_configuration(
    client_id, endpoint, custom_limit, custom_window
):
    """
    Property: Custom rate limit configurations should be respected.

    For any custom limit and window configuration, the rate limiter
    should enforce those specific limits.

    **Validates: Requirements 8.2, 8.5**
    """
    from api.services.rate_limiter import RateLimiter
    import redis.asyncio as redis
    from api.config import settings
    
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
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
                window_seconds=custom_window
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
            client_id=client_id,
            endpoint=endpoint,
            limit=custom_limit,
            window_seconds=custom_window
        )
        assert not result.allowed
        assert result.limit == custom_limit
        
    finally:
        # Clean up
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        await redis_client.close()


@given(
    client_id=client_id_strategy(),
    endpoint=endpoint_strategy()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_rate_limit_header_completeness(client_id, endpoint):
    """
    **Feature: api-rest-interface, Property 20: Rate limit header completeness**

    For any API request, the response should include rate limit headers
    (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).

    **Validates: Requirements 8.3, 8.4, 8.5**
    """
    from api.services.rate_limiter import RateLimiter
    import redis.asyncio as redis
    from api.config import settings
    from datetime import datetime
    
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)
        
        # Reset rate limit
        await rate_limiter.reset_rate_limit(client_id, endpoint)
        
        # Make a request and check rate limit
        result = await rate_limiter.check_rate_limit(
            client_id=client_id,
            endpoint=endpoint
        )
        
        # Get rate limit headers
        headers = rate_limiter.get_rate_limit_headers(result)
        
        # Verify all required headers are present
        assert 'X-RateLimit-Limit' in headers
        assert 'X-RateLimit-Remaining' in headers
        assert 'X-RateLimit-Reset' in headers
        
        # Verify header values are valid
        # X-RateLimit-Limit should be a positive integer
        limit_value = int(headers['X-RateLimit-Limit'])
        assert limit_value > 0
        assert limit_value == result.limit
        
        # X-RateLimit-Remaining should be a non-negative integer
        remaining_value = int(headers['X-RateLimit-Remaining'])
        assert remaining_value >= 0
        assert remaining_value == result.remaining
        assert remaining_value <= limit_value
        
        # X-RateLimit-Reset should be a valid Unix timestamp in the future
        reset_value = int(headers['X-RateLimit-Reset'])
        assert reset_value > 0
        current_timestamp = int(datetime.utcnow().timestamp())
        assert reset_value >= current_timestamp
        assert reset_value == int(result.reset_at.timestamp())
        
        # If request was denied, Retry-After header should be present
        if not result.allowed:
            assert 'Retry-After' in headers
            retry_after_value = int(headers['Retry-After'])
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
        assert 'X-RateLimit-Limit' in denied_headers
        assert 'X-RateLimit-Remaining' in denied_headers
        assert 'X-RateLimit-Reset' in denied_headers
        assert 'Retry-After' in denied_headers
        
        # Verify denied request has remaining = 0
        assert int(denied_headers['X-RateLimit-Remaining']) == 0
        
        # Verify Retry-After is present and valid
        retry_after = int(denied_headers['Retry-After'])
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
def simulation_history_strategy(draw):
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
        "free_energy": draw(st.lists(
            st.floats(min_value=0.0, max_value=10.0),
            min_size=num_steps,
            max_size=num_steps
        )),
        "ignitions": draw(st.lists(
            st.booleans(),
            min_size=num_steps,
            max_size=num_steps
        )),
        "metabolic_reserves": draw(st.lists(
            st.floats(min_value=0.0, max_value=1000.0),
            min_size=num_steps,
            max_size=num_steps
        )),
        "allostatic_load": draw(st.lists(
            st.floats(min_value=0.0, max_value=1.0),
            min_size=num_steps,
            max_size=num_steps
        ))
    }
    
    return history


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    export_format=st.sampled_from(['json', 'csv'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_completeness(session_id, history, export_format):
    """
    **Feature: api-rest-interface, Property 11: Data export completeness**

    For any simulation session with recorded data, exporting the data should
    include all timesteps that were recorded.

    **Validates: Requirements 5.1**
    """
    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession
    from unittest.mock import AsyncMock, Mock
    import json
    import csv
    import io
    
    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)
    
    # Configure mock to return our generated history
    mock_sim_session.get_state.return_value = {
        "history": history,
        "current_state": {}
    }
    
    # Configure session manager to return our mock session
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)
    
    # Create data export service
    export_service = DataExportService(mock_session_manager)
    
    # Export the data
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id,
        format=export_format
    )
    
    # Verify content type is correct
    if export_format == 'json':
        assert content_type == "application/json"
    elif export_format == 'csv':
        assert content_type == "text/csv"
    
    # Verify data was returned
    assert data_bytes is not None
    assert len(data_bytes) > 0
    
    # Parse the exported data and verify completeness
    num_recorded_timesteps = len(history["time"])
    
    if export_format == 'json':
        # Parse JSON
        data_str = data_bytes.decode('utf-8')
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
            assert abs(original_time - exported_time) < 0.001, \
                f"Timestep {i}: original={original_time}, exported={exported_time}"
        
        # Verify all data arrays have the same length as time
        for key, values in exported_history.items():
            if isinstance(values, list) and key in history:
                assert len(values) == num_recorded_timesteps, \
                    f"Variable '{key}' has {len(values)} values, expected {num_recorded_timesteps}"
    
    elif export_format == 'csv':
        # Parse CSV
        data_str = data_bytes.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(data_str))
        rows = list(csv_reader)
        
        # Property: All recorded timesteps should be in the export
        assert len(rows) == num_recorded_timesteps, \
            f"CSV has {len(rows)} rows, expected {num_recorded_timesteps}"
        
        # Verify time column exists and values match
        for i, (row, original_time) in enumerate(zip(rows, history["time"])):
            assert "time" in row
            exported_time = float(row["time"])
            assert abs(original_time - exported_time) < 0.001, \
                f"Row {i}: original time={original_time}, exported time={exported_time}"


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    start_time_offset=st.floats(min_value=0.1, max_value=0.4),
    end_time_offset=st.floats(min_value=0.6, max_value=0.9)
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_time_filtering(
    session_id, history, start_time_offset, end_time_offset
):
    """
    Property: Data export with time filtering should include only timesteps
    within the specified range.

    For any simulation session and time range, exporting with start_time and
    end_time filters should return only the timesteps within that range.

    **Validates: Requirements 5.1**
    """
    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession
    from unittest.mock import AsyncMock, Mock
    import json
    
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
    
    mock_sim_session.get_state.return_value = {
        "history": history,
        "current_state": {}
    }
    
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)
    
    # Create data export service
    export_service = DataExportService(mock_session_manager)
    
    # Export with time filtering
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id,
        format='json',
        start_time=start_time,
        end_time=end_time
    )
    
    # Parse exported data
    data_str = data_bytes.decode('utf-8')
    exported_data = json.loads(data_str)
    exported_times = exported_data["history"]["time"]
    
    # Property: All exported times should be within the specified range
    for t in exported_times:
        assert start_time <= t <= end_time, \
            f"Time {t} is outside range [{start_time}, {end_time}]"
    
    # Property: All times within the range should be exported
    expected_times = [t for t in times if start_time <= t <= end_time]
    assert len(exported_times) == len(expected_times), \
        f"Expected {len(expected_times)} timesteps, got {len(exported_times)}"


@given(
    session_id=session_id_strategy(),
    history=simulation_history_strategy(),
    variables_to_export=st.lists(
        st.sampled_from(['free_energy', 'ignitions', 'metabolic_reserves', 'allostatic_load']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_property_data_export_variable_filtering(
    session_id, history, variables_to_export
):
    """
    Property: Data export with variable filtering should include only the
    requested variables (plus time).

    For any simulation session and list of variables, exporting with variable
    filtering should return only those variables.

    **Validates: Requirements 5.1**
    """
    from api.services.data_export import DataExportService
    from api.services.session_manager import SessionManager, SimulationSession
    from unittest.mock import AsyncMock, Mock
    import json
    
    # Create mock session manager and simulation session
    mock_session_manager = Mock(spec=SessionManager)
    mock_sim_session = AsyncMock(spec=SimulationSession)
    
    mock_sim_session.get_state.return_value = {
        "history": history,
        "current_state": {}
    }
    
    mock_session_manager.get_session = AsyncMock(return_value=mock_sim_session)
    
    # Create data export service
    export_service = DataExportService(mock_session_manager)
    
    # Export with variable filtering
    data_bytes, content_type = await export_service.export_session_data(
        session_id=session_id,
        format='json',
        variables=variables_to_export
    )
    
    # Parse exported data
    data_str = data_bytes.decode('utf-8')
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
    
    assert actual_keys == expected_keys, \
        f"Expected variables {expected_keys}, got {actual_keys}"
