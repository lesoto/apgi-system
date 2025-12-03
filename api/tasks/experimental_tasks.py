"""
Experimental Task Celery Tasks

Celery tasks for executing experimental paradigms (Iowa Gambling, Masking, Attentional Blink).
"""

import logging
from typing import Dict, Any
from celery import Task

from api.celery_app import celery_app
from apgi_system.system import APGISystem
from apgi_system.experiments.tasks.iowa_gambling import IowaGamblingTask
from apgi_system.experiments.tasks.masking_paradigm import MaskingParadigmTask
from apgi_system.experiments.tasks.attentional_blink import AttentionalBlinkTask


logger = logging.getLogger(__name__)


class APGITask(Task):
    """Base task class with APGI system initialization."""
    
    _apgi_system = None
    
    @property
    def apgi_system(self):
        """Lazy initialization of APGI system."""
        if self._apgi_system is None:
            self._apgi_system = APGISystem(config_path="config/default.yaml")
        return self._apgi_system


@celery_app.task(bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_iowa_gambling_task")
def execute_iowa_gambling_task(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
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
    
    try:
        # Extract parameters with defaults
        num_trials = parameters.get("num_trials", 100)
        initial_balance = parameters.get("initial_balance", 2000)
        deck_stimulus_strength = parameters.get("deck_stimulus_strength", 1.5)
        outcome_stimulus_strength = parameters.get("outcome_stimulus_strength", 2.0)
        interoceptive_gain = parameters.get("interoceptive_gain", 1.0)
        deck_selection_strategy = parameters.get("deck_selection_strategy", "balanced")
        
        # Create task instance
        task = IowaGamblingTask(
            num_trials=num_trials,
            initial_balance=initial_balance,
            deck_stimulus_strength=deck_stimulus_strength,
            outcome_stimulus_strength=outcome_stimulus_strength,
            interoceptive_gain=interoceptive_gain,
            deck_selection_strategy=deck_selection_strategy
        )
        
        # Run all trials
        results = task.run_all_trials(self.apgi_system)
        
        logger.info(f"Iowa Gambling Task completed for session {session_id}")
        
        return {
            "task_type": "iowa_gambling",
            "session_id": session_id,
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Iowa Gambling Task failed for session {session_id}: {e}", exc_info=True)
        return {
            "task_type": "iowa_gambling",
            "session_id": session_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_masking_paradigm_task")
def execute_masking_paradigm_task(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Masking Paradigm Task.
    
    Args:
        session_id: Session identifier
        parameters: Task parameters including:
            - target_duration_ms: Target presentation duration (default: 50.0)
            - soas: List of SOAs to test in ms (default: [0, 17, 33, 50, 67, 83, 100, 150, 200, 300])
            - mask_duration_ms: Mask presentation duration (default: 100.0)
            - num_trials_per_condition: Trials per SOA (default: 20)
            - target_strength: Target stimulus strength (default: 2.0)
            - mask_strength: Mask stimulus strength (default: 3.0)
    
    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Masking Paradigm Task for session {session_id}")
    
    try:
        # Extract parameters with defaults
        target_duration_ms = parameters.get("target_duration_ms", 50.0)
        soas = parameters.get("soas", [0, 17, 33, 50, 67, 83, 100, 150, 200, 300])
        mask_duration_ms = parameters.get("mask_duration_ms", 100.0)
        num_trials_per_condition = parameters.get("num_trials_per_condition", 20)
        target_strength = parameters.get("target_strength", 2.0)
        mask_strength = parameters.get("mask_strength", 3.0)
        
        # Create task instance
        task = MaskingParadigmTask(
            target_duration_ms=target_duration_ms,
            soas=soas,
            mask_duration_ms=mask_duration_ms,
            num_trials_per_condition=num_trials_per_condition,
            target_strength=target_strength,
            mask_strength=mask_strength
        )
        
        # Run all trials
        results = task.run_all_trials(self.apgi_system)
        
        logger.info(f"Masking Paradigm Task completed for session {session_id}")
        
        return {
            "task_type": "masking_paradigm",
            "session_id": session_id,
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Masking Paradigm Task failed for session {session_id}: {e}", exc_info=True)
        return {
            "task_type": "masking_paradigm",
            "session_id": session_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(bind=True, base=APGITask, name="api.tasks.experimental_tasks.execute_attentional_blink_task")
def execute_attentional_blink_task(self, session_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Attentional Blink Task.
    
    Args:
        session_id: Session identifier
        parameters: Task parameters including:
            - stream_length: Number of items in RSVP stream (default: 15)
            - item_duration_ms: Duration of each item (default: 100.0)
            - num_trials_per_lag: Trials per lag condition (default: 20)
            - lags: List of lags to test (default: [1, 2, 3, 4, 8])
            - target_salience: Target salience boost (default: 2.0)
    
    Returns:
        Dict with task results and analysis
    """
    logger.info(f"Starting Attentional Blink Task for session {session_id}")
    
    try:
        # Extract parameters with defaults
        stream_length = parameters.get("stream_length", 15)
        item_duration_ms = parameters.get("item_duration_ms", 100.0)
        num_trials_per_lag = parameters.get("num_trials_per_lag", 20)
        lags = parameters.get("lags", [1, 2, 3, 4, 8])
        target_salience = parameters.get("target_salience", 2.0)
        
        # Create task instance
        task = AttentionalBlinkTask(
            stream_length=stream_length,
            item_duration_ms=item_duration_ms,
            num_trials_per_lag=num_trials_per_lag,
            lags=lags,
            target_salience=target_salience
        )
        
        # Run all trials
        results = task.run_all_trials(self.apgi_system)
        
        logger.info(f"Attentional Blink Task completed for session {session_id}")
        
        return {
            "task_type": "attentional_blink",
            "session_id": session_id,
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Attentional Blink Task failed for session {session_id}: {e}", exc_info=True)
        return {
            "task_type": "attentional_blink",
            "session_id": session_id,
            "status": "failed",
            "error": str(e)
        }
