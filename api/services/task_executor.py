"""
Task Executor Service

Manages asynchronous execution of experimental tasks using Celery.
"""

import asyncio
import logging
from enum import Enum
from typing import Any, Dict, Optional

from celery.result import AsyncResult  # type: ignore

from api.celery_app import celery_app
from api.tasks.task_registry import TASK_REGISTRY, TaskType

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskExecutor:
    """
    Executes experimental tasks asynchronously using Celery.

    Manages task submission, status tracking, and result retrieval.
    """

    def __init__(self) -> None:
        """Initialize task executor."""
        self.celery = celery_app
        logger.info("TaskExecutor initialized")

    async def submit_task(
        self,
        session_id: str,
        task_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        webhook_url: Optional[str] = None,
    ) -> str:
        """
        Submit task for async execution.

        Args:
            session_id: Session identifier
            task_type: Type of experimental task
            parameters: Task-specific parameters
            webhook_url: Optional webhook URL for completion notification

        Returns:
            Task ID for tracking

        Raises:
            ValueError: If task_type is not recognized
        """
        # Validate task type
        try:
            task_enum = TaskType(task_type)
        except ValueError:
            raise ValueError(
                f"Unknown task type: {task_type}. "
                f"Available types: {[t.value for t in TaskType]}"
            )

        # Get Celery task name
        task_name = TASK_REGISTRY[task_enum]

        # Prepare parameters
        params = parameters or {}

        # Submit task in thread pool to avoid blocking
        def _submit_task() -> str:
            logger.info(f"Submitting {task_type} task for session {session_id}")
            result = self.celery.send_task(
                task_name, args=[session_id, params], task_id=None  # Let Celery generate ID
            )
            logger.info(f"Task submitted with ID: {result.id}")
            return str(result.id)

        task_id = await asyncio.to_thread(_submit_task)

        # Note: Task metadata storage is handled by the Celery task itself

        return task_id

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get current task status.

        Args:
            task_id: Task identifier

        Returns:
            Dict with status information including:
                - task_id: Task identifier
                - status: Current status (pending, running, completed, failed)
                - progress: Progress information if available
                - result: Task result if completed
                - error: Error message if failed
        """

        def _get_status() -> Dict[str, Any]:
            result = AsyncResult(task_id, app=self.celery)

            # Map Celery states to our TaskStatus
            state_mapping = {
                "PENDING": TaskStatus.PENDING,
                "STARTED": TaskStatus.RUNNING,
                "RETRY": TaskStatus.RUNNING,
                "SUCCESS": TaskStatus.COMPLETED,
                "FAILURE": TaskStatus.FAILED,
            }

            response = {
                "task_id": task_id,
                "status": state_mapping.get(result.state, TaskStatus.PENDING),
                "state": result.state,
            }

            # Add result or error information
            if result.successful():
                response["result"] = result.result
            elif result.failed():
                response["error"] = str(result.info)
            elif result.state == "STARTED":
                # Task is running, include any progress info
                response["info"] = result.info if result.info else {}

            return response

        return await asyncio.to_thread(_get_status)

    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve completed task results.

        Args:
            task_id: Task identifier

        Returns:
            Task results

        Raises:
            ValueError: If task is not completed or failed
        """

        def _get_result() -> Any:
            result = AsyncResult(task_id, app=self.celery)

            if not result.ready():
                raise ValueError(
                    f"Task {task_id} is not complete. " f"Current state: {result.state}"
                )

            if result.failed():
                raise ValueError(f"Task {task_id} failed: {result.info}")

            return result.result

        return await asyncio.to_thread(_get_result)

    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a running task.

        Args:
            task_id: Task identifier

        Returns:
            Dict with cancellation status
        """

        def _cancel_task() -> Dict[str, Any]:
            result = AsyncResult(task_id, app=self.celery)

            if result.state in ["PENDING", "STARTED", "RETRY"]:
                result.revoke(terminate=True)
                logger.info(f"Task {task_id} cancelled")
                return {
                    "task_id": task_id,
                    "status": "cancelled",
                    "message": "Task cancellation requested",
                }
            else:
                return {
                    "task_id": task_id,
                    "status": result.state,
                    "message": f"Task cannot be cancelled (state: {result.state})",
                }

        return await asyncio.to_thread(_cancel_task)

    async def list_available_tasks(self) -> Dict[str, Any]:
        """
        List all available experimental tasks with descriptions.

        Returns:
            Dict mapping task types to their descriptions and parameters
        """
        return {
            "tasks": [
                {
                    "task_type": TaskType.IOWA_GAMBLING.value,
                    "name": "Iowa Gambling Task",
                    "description": (
                        "Decision-making task with four decks of cards. "
                        "Tests learning from rewards and punishments."
                    ),
                    "parameters": {
                        "num_trials": {
                            "type": "integer",
                            "default": 100,
                            "description": "Number of card selections",
                        },
                        "initial_balance": {
                            "type": "integer",
                            "default": 2000,
                            "description": "Starting money amount",
                        },
                        "deck_stimulus_strength": {
                            "type": "float",
                            "default": 1.5,
                            "description": "Strength of deck visual stimuli",
                        },
                        "outcome_stimulus_strength": {
                            "type": "float",
                            "default": 2.0,
                            "description": "Strength of outcome stimuli",
                        },
                        "interoceptive_gain": {
                            "type": "float",
                            "default": 1.0,
                            "description": "Multiplier for interoceptive signals",
                        },
                        "deck_selection_strategy": {
                            "type": "string",
                            "default": "balanced",
                            "options": ["balanced", "random", "participant_choice"],
                            "description": "How trials are generated",
                        },
                    },
                },
                {
                    "task_type": TaskType.MASKING_PARADIGM.value,
                    "name": "Visual Masking Paradigm",
                    "description": (
                        "Tests temporal dynamics of conscious access. "
                        "Target followed by mask at varying SOAs."
                    ),
                    "parameters": {
                        "target_duration_ms": {
                            "type": "float",
                            "default": 50.0,
                            "description": "Target presentation duration (ms)",
                        },
                        "soas": {
                            "type": "array",
                            "default": [0, 17, 33, 50, 67, 83, 100, 150, 200, 300],
                            "description": "Stimulus onset asynchronies to test (ms)",
                        },
                        "mask_duration_ms": {
                            "type": "float",
                            "default": 100.0,
                            "description": "Mask presentation duration (ms)",
                        },
                        "num_trials_per_condition": {
                            "type": "integer",
                            "default": 20,
                            "description": "Number of trials per SOA",
                        },
                        "target_strength": {
                            "type": "float",
                            "default": 2.0,
                            "description": "Target stimulus strength",
                        },
                        "mask_strength": {
                            "type": "float",
                            "default": 3.0,
                            "description": "Mask stimulus strength",
                        },
                    },
                },
                {
                    "task_type": TaskType.ATTENTIONAL_BLINK.value,
                    "name": "Attentional Blink Task",
                    "description": (
                        "RSVP paradigm with two targets. "
                        "Tests temporal limits of conscious access."
                    ),
                    "parameters": {
                        "stream_length": {
                            "type": "integer",
                            "default": 15,
                            "description": "Number of items in RSVP stream",
                        },
                        "item_duration_ms": {
                            "type": "float",
                            "default": 100.0,
                            "description": "Duration of each item (ms)",
                        },
                        "num_trials_per_lag": {
                            "type": "integer",
                            "default": 20,
                            "description": "Number of trials per lag condition",
                        },
                        "lags": {
                            "type": "array",
                            "default": [1, 2, 3, 4, 8],
                            "description": "Lags to test (items between T1 and T2)",
                        },
                        "target_salience": {
                            "type": "float",
                            "default": 2.0,
                            "description": "Salience boost for targets",
                        },
                    },
                },
            ]
        }
