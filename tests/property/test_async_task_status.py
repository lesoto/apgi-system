"""
Property-based test for async task status tracking.

Tests that task status can be tracked from submission to completion.
"""

import uuid
from typing import Any
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from api.services.task_executor import TaskExecutor, TaskStatus, TaskType


# Strategies for generating test data
@st.composite
def task_type_strategy(draw: Any) -> Any:
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
def task_parameters_strategy(draw: Any, task_type: str) -> Any:
    """Generate valid parameters for a given task type."""
    if task_type == TaskType.IOWA_GAMBLING.value:
        return {
            "num_trials": draw(st.integers(min_value=10, max_value=200)),
        }
    elif task_type == TaskType.MASKING_PARADIGM.value:
        return {
            "target_duration_ms": draw(st.floats(min_value=20.0, max_value=100.0)),
        }
    elif task_type == TaskType.ATTENTIONAL_BLINK.value:
        return {
            "stream_length": draw(st.integers(min_value=10, max_value=20)),
        }
    else:
        return {}


@st.composite
def session_id_strategy(draw: Any) -> Any:
    """Generate valid session IDs (UUIDs)."""
    return str(uuid.uuid4())


@st.composite
def task_result_strategy(draw: Any, task_type: str, session_id: str) -> Any:
    """Generate mock task results for a given task type."""
    return {
        "task_type": task_type,
        "session_id": session_id,
        "status": "completed",
        "results": {"test": "data"},
    }


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
