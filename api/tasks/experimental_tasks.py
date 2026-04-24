"""
Experimental Task Celery Tasks

Celery tasks for executing experimental paradigms (Iowa Gambling, Masking, Attentional Blink).
"""

import logging
from datetime import datetime
from typing import Any, Dict

import yaml
from celery import Task  # type: ignore

from apgi_framework.experiments.tasks.attentional_blink import AttentionalBlinkTask
from apgi_framework.experiments.tasks.binocular_rivalry import BinocularRivalryTask
from apgi_framework.experiments.tasks.change_blindness import ChangeBlindnessTask
from apgi_framework.experiments.tasks.iowa_gambling import IowaGamblingTask
from apgi_framework.experiments.tasks.masking_paradigm import MaskingParadigmTask
from apgi_framework.platform_utils import get_resource_path
from apgi_framework.system import APGISystem
from api.celery_app import celery_app
from api.database.connection import get_db
from api.database.models import Task as TaskModel
from api.services.webhook_manager import WebhookManager

logger = logging.getLogger(__name__)


async def trigger_webhook_on_completion(task_id: str, result: Dict[str, Any]) -> None:
    """
    Trigger webhook delivery when task completes.

    Args:
        task_id: Celery task ID
        result: Task result data
    """
    try:
        # Get database session
        db = next(get_db())

        # Find task record
        task_record = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()

        if not task_record:
            logger.warning(f"Task record not found for task {task_id}")
            return

        # Update task status in database
        task_record.status = result.get("status", "completed")
        task_record.completed_at = datetime.utcnow()  # type: ignore[assignment]
        task_record.result_data = result  # type: ignore[assignment]

        if result.get("status") == "failed":
            task_record.error_message = result.get("error")  # type: ignore[assignment]

        db.commit()

        # Check if webhook URL is configured
        if task_record.webhook_url:
            logger.info(f"Triggering webhook for task {task_id} to {task_record.webhook_url}")

            # Create webhook payload
            payload = {
                "task_id": task_id,
                "session_id": task_record.session_id,
                "task_type": task_record.task_type,
                "status": result.get("status", "completed"),
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "result": result,
            }

            # Load webhook config
            config_path = get_resource_path("config/default.yaml")
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            webhook_config = config.get("webhook", {})

            # Create webhook delivery
            webhook_manager = WebhookManager(webhook_config=webhook_config)
            delivery_id = await webhook_manager.create_webhook_delivery(
                db=db, task_id=task_id, webhook_url=task_record.webhook_url, payload=payload  # type: ignore[arg-type]
            )

            # Attempt immediate delivery
            await webhook_manager.deliver_webhook(db, delivery_id)
            await webhook_manager.close()

            logger.info(f"Webhook delivery {delivery_id} created for task {task_id}")
        else:
            logger.debug(f"No webhook URL configured for task {task_id}")

        db.close()

    except Exception as e:
        logger.error(f"Failed to trigger webhook for task {task_id}: {e}", exc_info=True)


class APGITask(Task):  # type: ignore[misc]
    """Base task class with APGI system initialization."""

    _apgi_simulation = None

    @property
    def apgi_simulation(self) -> APGISystem:
        """Lazy initialization of APGI system."""
        if self._apgi_simulation is None:
            # Use platform-aware resource path resolution
            self._apgi_simulation = APGISystem(
                config_path=str(get_resource_path("config/default.yaml"))
            )
        return self._apgi_simulation


@celery_app.task(
    bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_iowa_gambling_task"
)
def execute_iowa_gambling_task(
    self: APGITask, session_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Iowa Gambling Task.

    Args:
        session_id: Session identifier
        parameters: Task parameters including:
            - num_trials: Number of trials (default: 100)
            - initial_balance: Starting balance (default: 2000)
            - deck_stimulus_strength: Deck visual strength (default: 1.5)
            - outcome_stimulus_strength: Outcome strength (default: 2.0)
            - interoceptive_gain: Interoceptive signal multiplier (default: 1.0)
            - deck_selection_strategy: 'balanced', 'random', or 'participant_choice' (default: 'balanced')

    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Iowa Gambling Task for session {session_id}")

    result = None
    try:
        # Extract parameters with defaults
        num_trials = parameters.get("num_trials", 100)
        starting_balance = parameters.get("initial_balance", 2000)
        num_decks = parameters.get("num_decks", 4)

        # Create task instance
        task = IowaGamblingTask(
            num_decks=num_decks,
            starting_balance=starting_balance,
            num_trials=num_trials,
        )

        # Run all trials
        results = task.run_all_trials(self.apgi_simulation)

        logger.info(f"Iowa Gambling Task completed for session {session_id}")

        result = {
            "task_type": "iowa_gambling",
            "session_id": session_id,
            "status": "completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Iowa Gambling Task failed for session {session_id}: {e}", exc_info=True)
        result = {
            "task_type": "iowa_gambling",
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
        }

    # Trigger webhook on completion (async)
    import asyncio

    try:
        asyncio.run(trigger_webhook_on_completion(self.request.id, result))
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}", exc_info=True)

    return result


@celery_app.task(
    bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_masking_paradigm_task"
)
def execute_masking_paradigm_task(
    self: APGITask, session_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Masking Paradigm Task.

    Args:
        session_id: Session identifier
        parameters: Task parameters including:
            - target_duration_ms: Target presentation duration (default: 50.0)
            - soas: List of SOAs to test in ms (default: [0, 17, 33, 50, 67, 83, 100, 150, 200, 300])
            - mask_duration_ms: Mask presentation duration (default: 100.0)
            - num_trials_per_condition: Trials per SOA (default: 20)

    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Masking Paradigm Task for session {session_id}")

    result = None
    try:
        # Extract parameters with defaults
        target_duration_ms = parameters.get("target_duration_ms", 50.0)
        soas = parameters.get("soas", [0, 17, 33, 50, 67, 83, 100, 150, 200, 300])
        mask_duration_ms = parameters.get("mask_duration_ms", 100.0)
        num_trials_per_condition = parameters.get("num_trials_per_condition", 20)

        # Create task instance
        task = MaskingParadigmTask(
            target_duration_ms=target_duration_ms,
            soas=soas,
            mask_duration_ms=mask_duration_ms,
            num_trials_per_condition=num_trials_per_condition,
        )

        # Run all trials
        results = task.run_all_trials(self.apgi_simulation)

        logger.info(f"Masking Paradigm Task completed for session {session_id}")

        result = {
            "task_type": "masking_paradigm",
            "session_id": session_id,
            "status": "completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Masking Paradigm Task failed for session {session_id}: {e}", exc_info=True)
        result = {
            "task_type": "masking_paradigm",
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
        }

    # Trigger webhook on completion (async)
    import asyncio

    try:
        asyncio.run(trigger_webhook_on_completion(self.request.id, result))
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}", exc_info=True)

    return result


@celery_app.task(
    bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_attentional_blink_task"
)
def execute_attentional_blink_task(
    self: APGITask, session_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Attentional Blink Task.

    Args:
        session_id: Session identifier
        parameters: Task parameters including:
            - stream_length: Number of items in RSVP stream (default: 15)
            - stimulus_duration_ms: Duration of each item (default: 100.0)
            - isi_ms: Inter-stimulus interval (default: 200.0)
            - num_trials_per_lag: Trials per lag condition (default: 20)
            - lags: List of lags to test (default: [1, 2, 3, 4, 8])

    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Attentional Blink Task for session {session_id}")

    result = None
    try:
        # Extract parameters with defaults
        stream_length = parameters.get("stream_length", 15)
        stimulus_duration_ms = parameters.get("stimulus_duration_ms", 100.0)
        isi_ms = parameters.get("isi_ms", 200.0)
        num_trials_per_lag = parameters.get("num_trials_per_lag", 20)
        lags = parameters.get("lags", [1, 2, 3, 4, 8])

        # Create task instance
        task = AttentionalBlinkTask(
            stimulus_duration_ms=stimulus_duration_ms,
            isi_ms=isi_ms,
            lags=lags,
            num_trials_per_lag=num_trials_per_lag,
            stream_length=stream_length,
        )

        # Run all trials
        results = task.run_all_trials(self.apgi_simulation)

        logger.info(f"Attentional Blink Task completed for session {session_id}")

        result = {
            "task_type": "attentional_blink",
            "session_id": session_id,
            "status": "completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Attentional Blink Task failed for session {session_id}: {e}", exc_info=True)
        result = {
            "task_type": "attentional_blink",
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
        }

    # Trigger webhook on completion (async)
    import asyncio

    try:
        asyncio.run(trigger_webhook_on_completion(self.request.id, result))
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}", exc_info=True)

    return result


@celery_app.task(
    bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_change_blindness_task"
)
def execute_change_blindness_task(
    self: APGITask, session_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Change Blindness Task.

    Args:
        session_id: Session identifier
        parameters: Task parameters

    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Change Blindness Task for session {session_id}")

    result = None
    try:
        # Extract parameters with defaults
        change_magnitude = parameters.get("change_magnitude", 0.3)
        num_trials = parameters.get("num_trials", 50)

        # Create task instance
        task = ChangeBlindnessTask(
            change_magnitudes=[change_magnitude],
            num_trials_per_condition=num_trials,
        )

        # Run all trials
        results = task.run_all_trials(self.apgi_simulation)

        logger.info(f"Change Blindness Task completed for session {session_id}")

        result = {
            "task_type": "change_blindness",
            "session_id": session_id,
            "status": "completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Change Blindness Task failed for session {session_id}: {e}", exc_info=True)
        result = {
            "task_type": "change_blindness",
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
        }

    # Trigger webhook on completion (async)
    import asyncio

    try:
        asyncio.run(trigger_webhook_on_completion(self.request.id, result))
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}", exc_info=True)

    return result


# N-Back and Stroop tasks are not yet implemented in apgi_framework
# @celery_app.task(bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_nback_task")
# def execute_nback_task(...) -> Dict[str, Any]:
#     """Execute N-Back Task."""
#     pass

# @celery_app.task(bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_stroop_task")
# def execute_stroop_task(...) -> Dict[str, Any]:
#     """Execute Stroop Task."""
#     pass


@celery_app.task(
    bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_binocular_rivalry_task"
)
def execute_binocular_rivalry_task(
    self: APGITask, session_id: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute Binocular Rivalry Task.

    Args:
        session_id: Session identifier
        parameters: Task parameters

    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Binocular Rivalry Task for session {session_id}")

    result = None
    try:
        # Extract parameters with defaults
        duration_seconds = parameters.get("duration_seconds", 60.0)

        # Create task instance
        task = BinocularRivalryTask(
            trial_duration_ms=duration_seconds * 1000,  # Convert to ms
            num_trials=1,
        )

        # Run all trials
        results = task.run_all_trials(self.apgi_simulation)

        logger.info(f"Binocular Rivalry Task completed for session {session_id}")

        result = {
            "task_type": "binocular_rivalry",
            "session_id": session_id,
            "status": "completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Binocular Rivalry Task failed for session {session_id}: {e}", exc_info=True)
        result = {
            "task_type": "binocular_rivalry",
            "session_id": session_id,
            "status": "failed",
            "error": str(e),
        }

    # Trigger webhook on completion (async)
    import asyncio

    try:
        asyncio.run(trigger_webhook_on_completion(self.request.id, result))
    except Exception as e:
        logger.error(f"Failed to trigger webhook: {e}", exc_info=True)

    return result
