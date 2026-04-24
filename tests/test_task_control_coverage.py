"""
Comprehensive tests for apgi_framework.adaptive.task_control module.

Covers: TaskState, ResponseType, TimingEvent, ResponseData, PrecisionTimer,
ResponseCollector, TaskStateMachine, SessionConfiguration, SessionManager
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from apgi_framework.adaptive.task_control import (
    TaskState,
    ResponseType,
    TimingEvent,
    ResponseData,
    PrecisionTimer,
    ResponseCollector,
    SessionConfiguration,
    SessionManager,
    TaskStateMachine,
)

# --- Enums ---


class TestTaskState:
    def test_all_states(self):
        assert TaskState.IDLE.value == "idle"
        assert TaskState.INITIALIZING.value == "initializing"
        assert TaskState.READY.value == "ready"
        assert TaskState.RUNNING.value == "running"
        assert TaskState.PAUSED.value == "paused"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.ERROR.value == "error"


class TestResponseType:
    def test_all_types(self):
        assert ResponseType.DETECTION.value == "detection"
        assert ResponseType.CONFIDENCE.value == "confidence"
        assert ResponseType.FORCED_CHOICE.value == "forced_choice"
        assert ResponseType.SYNCHRONY_JUDGMENT.value == "synchrony_judgment"


# --- TimingEvent ---


class TestTimingEvent:
    def test_timing_error_no_actual_time(self):
        event = TimingEvent(
            event_id="test",
            event_type="stimulus",
            scheduled_time=datetime.now(),
        )
        assert event.get_timing_error_ms() is None

    def test_timing_error_calculation(self):
        scheduled = datetime(2026, 1, 1, 12, 0, 0)
        actual = datetime(2026, 1, 1, 12, 0, 0, 5000)  # 5ms later
        event = TimingEvent(
            event_id="test",
            event_type="stimulus",
            scheduled_time=scheduled,
            actual_time=actual,
        )
        error = event.get_timing_error_ms()
        assert error is not None
        assert abs(error - 5.0) < 0.1


# --- ResponseData ---


class TestResponseData:
    def test_to_dict(self):
        response = ResponseData(
            response_id="resp_1",
            response_type=ResponseType.DETECTION,
            response_time=datetime(2026, 1, 1, 12, 0, 0),
            reaction_time_ms=350.0,
            response_value=True,
            confidence=0.85,
        )
        d = response.to_dict()
        assert d["response_id"] == "resp_1"
        assert d["response_type"] == "detection"
        assert d["reaction_time_ms"] == 350.0
        assert d["confidence"] == 0.85
        assert d["valid"] is True

    def test_default_values(self):
        response = ResponseData(
            response_id="r1",
            response_type=ResponseType.FORCED_CHOICE,
            response_time=datetime.now(),
            reaction_time_ms=200.0,
            response_value="left",
        )
        assert response.confidence is None
        assert response.valid is True
        assert response.metadata == {}


# --- PrecisionTimer ---


class TestPrecisionTimer:
    def test_init(self):
        timer = PrecisionTimer("test_timer")
        assert timer.timer_id == "test_timer"
        assert timer.reference_time is None

    def test_start_session(self):
        timer = PrecisionTimer()
        timer.start_session()
        assert timer.reference_time is not None

    def test_get_current_time_ms_not_started(self):
        timer = PrecisionTimer()
        with pytest.raises(RuntimeError, match="Timer session not started"):
            timer.get_current_time_ms()

    def test_get_current_time_ms(self):
        timer = PrecisionTimer()
        timer.start_session()
        t = timer.get_current_time_ms()
        assert t >= 0

    def test_schedule_event_not_started(self):
        timer = PrecisionTimer()
        with pytest.raises(RuntimeError):
            timer.schedule_event("e1", "stimulus", 100.0)

    def test_schedule_event(self):
        timer = PrecisionTimer()
        timer.start_session()
        event = timer.schedule_event("e1", "stimulus", 100.0, {"key": "val"})
        assert event.event_id == "e1"
        assert event.event_type == "stimulus"
        assert event.metadata["key"] == "val"
        assert len(timer.timing_events) == 1

    def test_wait_until_not_started(self):
        timer = PrecisionTimer()
        with pytest.raises(RuntimeError):
            timer.wait_until(100.0)

    def test_wait_until(self):
        timer = PrecisionTimer()
        timer.start_session()
        error = timer.wait_until(1.0)  # Wait 1ms
        assert isinstance(error, float)

    def test_sleep_precise_short(self):
        timer = PrecisionTimer()
        error = timer.sleep_precise(1.0)  # 1ms
        assert isinstance(error, float)

    def test_sleep_precise_longer(self):
        timer = PrecisionTimer()
        error = timer.sleep_precise(5.0)  # 5ms
        assert isinstance(error, float)

    def test_mark_event_executed(self):
        timer = PrecisionTimer()
        timer.start_session()
        event = timer.schedule_event("e1", "stimulus", 10.0)
        timer.mark_event_executed(event)
        assert event.actual_time is not None

    def test_get_timing_statistics_empty(self):
        timer = PrecisionTimer()
        stats = timer.get_timing_statistics()
        assert stats["total_events"] == 0
        assert stats["mean_error_ms"] == 0.0

    def test_get_timing_statistics(self):
        timer = PrecisionTimer()
        timer.timing_errors = [0.1, -0.2, 0.15, -0.05]
        stats = timer.get_timing_statistics()
        assert stats["total_events"] == 4
        assert stats["max_error_ms"] == 0.15
        assert stats["min_error_ms"] == -0.2


# --- ResponseCollector ---


class TestResponseCollector:
    def test_init(self):
        rc = ResponseCollector("test_collector")
        assert rc.collector_id == "test_collector"
        assert rc.is_collecting is False

    def test_start_collection(self):
        rc = ResponseCollector()
        rc.start_collection(stimulus_onset_time=datetime.now(), response_window_ms=100.0)
        assert rc.is_collecting is True
        rc.stop_collection()

    def test_stop_collection(self):
        rc = ResponseCollector()
        rc.start_collection(stimulus_onset_time=datetime.now(), response_window_ms=50.0)
        rc.stop_collection()
        assert rc.is_collecting is False

    def test_wait_for_response_not_collecting(self):
        rc = ResponseCollector()
        result = rc.wait_for_response(timeout_ms=10)
        assert result is None

    def test_wait_for_response_timeout(self):
        rc = ResponseCollector()
        rc.start_collection(stimulus_onset_time=datetime.now(), response_window_ms=10.0)
        result = rc.wait_for_response(timeout_ms=10)
        assert result is None
        rc.stop_collection()

    def test_wait_for_response_with_response(self):
        rc = ResponseCollector()
        rc.start_collection(stimulus_onset_time=datetime.now(), response_window_ms=5000.0)
        rc.is_collecting = True

        # Put a response in the queue manually
        response = ResponseData(
            response_id="r1",
            response_type=ResponseType.DETECTION,
            response_time=datetime.now(),
            reaction_time_ms=300.0,
            response_value=True,
        )
        rc.response_queue.put(response)

        result = rc.wait_for_response(timeout_ms=1000)
        assert result is not None
        assert result.response_id == "r1"
        rc.stop_collection()


# --- TaskStateMachine ---


class TestTaskStateMachine:
    def test_init(self):
        sm = TaskStateMachine("test_sm")
        assert sm.current_state == TaskState.IDLE
        assert sm.previous_state is None
        assert sm.error_message is None

    def test_valid_transition(self):
        sm = TaskStateMachine()
        assert sm.transition_to(TaskState.INITIALIZING, "Start")
        assert sm.current_state == TaskState.INITIALIZING
        assert sm.previous_state == TaskState.IDLE

    def test_invalid_transition(self):
        sm = TaskStateMachine()
        assert not sm.transition_to(TaskState.RUNNING)
        assert sm.current_state == TaskState.IDLE

    def test_full_lifecycle(self):
        sm = TaskStateMachine()
        assert sm.transition_to(TaskState.INITIALIZING)
        assert sm.transition_to(TaskState.READY)
        assert sm.transition_to(TaskState.RUNNING)
        assert sm.transition_to(TaskState.COMPLETED)
        assert sm.transition_to(TaskState.IDLE)

    def test_pause_resume(self):
        sm = TaskStateMachine()
        sm.transition_to(TaskState.INITIALIZING)
        sm.transition_to(TaskState.READY)
        sm.transition_to(TaskState.RUNNING)
        assert sm.transition_to(TaskState.PAUSED)
        assert sm.transition_to(TaskState.RUNNING)

    def test_error_transition(self):
        sm = TaskStateMachine()
        sm.transition_to(TaskState.INITIALIZING)
        sm.set_error("Something went wrong")
        assert sm.current_state == TaskState.ERROR
        assert sm.error_message == "Something went wrong"

    def test_error_recovery(self):
        sm = TaskStateMachine()
        sm.transition_to(TaskState.INITIALIZING)
        sm.set_error("Error occurred")
        assert sm.transition_to(TaskState.IDLE)
        assert sm.error_message is None

    def test_add_state_callback(self):
        sm = TaskStateMachine()
        callback = MagicMock()
        sm.add_state_callback(TaskState.INITIALIZING, callback)
        sm.transition_to(TaskState.INITIALIZING)
        callback.assert_called_once_with(TaskState.INITIALIZING)

    def test_callback_error_handling(self):
        sm = TaskStateMachine()

        def bad_callback(state):
            raise ValueError("Callback error")

        sm.add_state_callback(TaskState.INITIALIZING, bad_callback)
        # Should not raise
        sm.transition_to(TaskState.INITIALIZING)

    def test_can_start_task(self):
        sm = TaskStateMachine()
        assert not sm.can_start_task()
        sm.transition_to(TaskState.INITIALIZING)
        sm.transition_to(TaskState.READY)
        assert sm.can_start_task()

    def test_can_pause_task(self):
        sm = TaskStateMachine()
        assert not sm.can_pause_task()
        sm.transition_to(TaskState.INITIALIZING)
        sm.transition_to(TaskState.READY)
        sm.transition_to(TaskState.RUNNING)
        assert sm.can_pause_task()

    def test_can_resume_task(self):
        sm = TaskStateMachine()
        assert not sm.can_resume_task()
        sm.transition_to(TaskState.INITIALIZING)
        sm.transition_to(TaskState.READY)
        sm.transition_to(TaskState.RUNNING)
        sm.transition_to(TaskState.PAUSED)
        assert sm.can_resume_task()

    def test_is_task_active(self):
        sm = TaskStateMachine()
        assert not sm.is_task_active()
        sm.transition_to(TaskState.INITIALIZING)
        sm.transition_to(TaskState.READY)
        sm.transition_to(TaskState.RUNNING)
        assert sm.is_task_active()

    def test_get_state_duration(self):
        sm = TaskStateMachine()
        assert sm.get_state_duration() is None
        sm.transition_to(TaskState.INITIALIZING)
        duration = sm.get_state_duration()
        assert duration is not None
        assert duration >= 0

    def test_get_state_summary(self):
        sm = TaskStateMachine()
        summary = sm.get_state_summary()
        assert summary["current_state"] == "idle"
        assert summary["previous_state"] is None


# --- SessionConfiguration ---


class TestSessionConfiguration:
    def test_default_config(self):
        config = SessionConfiguration(
            session_id="s1",
            participant_id="p1",
        )
        assert config.protocol_version == "1.0.0"
        assert config.tasks_to_run == ["detection", "heartbeat", "oddball"]
        assert config.task_order == "fixed"

    def test_validate_valid(self):
        config = SessionConfiguration(session_id="s1", participant_id="p1")
        assert config.validate() is True

    def test_validate_invalid_session_id(self):
        config = SessionConfiguration(session_id="", participant_id="p1")
        assert config.validate() is False

    def test_validate_invalid_participant_id(self):
        config = SessionConfiguration(session_id="s1", participant_id="")
        assert config.validate() is False

    def test_validate_invalid_tasks(self):
        config = SessionConfiguration(
            session_id="s1",
            participant_id="p1",
            tasks_to_run=[],
        )
        assert config.validate() is False

    def test_validate_invalid_duration(self):
        config = SessionConfiguration(
            session_id="s1",
            participant_id="p1",
            max_session_duration_min=0,
        )
        assert config.validate() is False


# --- SessionManager ---


class TestSessionManager:
    def setup_method(self):
        self.manager = SessionManager("test_manager")
        self.config = SessionConfiguration(
            session_id="s1",
            participant_id="p1",
            inter_task_interval_s=0,  # No wait for tests
            backup_interval_min=0,
        )

    def test_init(self):
        assert self.manager.manager_id == "test_manager"
        assert self.manager.current_session is None
        assert self.manager.current_task_index == 0

    def test_configure_session(self):
        result = self.manager.configure_session(self.config)
        assert result is True
        assert self.manager.current_session == self.config
        assert self.manager.session_data["session_id"] == "s1"

    def test_configure_session_invalid(self):
        bad_config = SessionConfiguration(session_id="", participant_id="p1")
        result = self.manager.configure_session(bad_config)
        assert result is False

    def test_start_session_without_config(self):
        result = self.manager.start_session()
        assert result is False

    @patch.object(SessionManager, "_start_data_backup")
    def test_start_session(self, mock_backup):
        self.manager.configure_session(self.config)
        result = self.manager.start_session()
        assert result is True
        assert self.manager.state_machine.current_state == TaskState.READY

    @patch.object(SessionManager, "_start_data_backup")
    def test_run_next_task_no_session(self, mock_backup):
        result = self.manager.run_next_task()
        assert result is None

    @patch.object(SessionManager, "_start_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_run_next_task(self, mock_save, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        task = self.manager.run_next_task()
        assert task == "detection"
        assert self.manager.state_machine.current_state == TaskState.RUNNING

    @patch.object(SessionManager, "_start_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_complete_current_task(self, mock_save, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        self.manager.run_next_task()
        result = self.manager.complete_current_task()
        assert result is True
        assert "detection" in self.manager.completed_tasks

    def test_complete_task_without_session(self):
        result = self.manager.complete_current_task()
        assert result is False

    @patch.object(SessionManager, "_start_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_pause_resume_session(self, mock_save, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        self.manager.run_next_task()
        assert self.manager.pause_session() is True
        assert self.manager.state_machine.current_state == TaskState.PAUSED
        assert self.manager.resume_session() is True
        assert self.manager.state_machine.current_state == TaskState.RUNNING

    @patch.object(SessionManager, "_start_data_backup")
    @patch.object(SessionManager, "_stop_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_abort_session(self, mock_save, mock_stop, mock_start):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        self.manager.run_next_task()
        result = self.manager.abort_session("Test abort")
        assert result is True
        assert self.manager.session_data.get("aborted") is True

    @patch.object(SessionManager, "_start_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_add_trial_data(self, mock_save, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        self.manager.run_next_task()
        trial = {"trial_number": 1, "response": True}
        self.manager.add_trial_data("detection", trial)
        assert len(self.manager.session_data["tasks"]["detection"]["trials"]) == 1

    @patch.object(SessionManager, "_start_data_backup")
    def test_add_event(self, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        self.manager.add_event("marker", {"label": "start"})
        assert len(self.manager.session_data["events"]) == 1

    def test_get_session_progress_no_session(self):
        progress = self.manager.get_session_progress()
        assert "error" in progress

    @patch.object(SessionManager, "_start_data_backup")
    def test_get_session_progress(self, mock_backup):
        self.manager.configure_session(self.config)
        self.manager.start_session()
        progress = self.manager.get_session_progress()
        assert progress["session_id"] == "s1"
        assert progress["total_tasks"] == 3
        assert progress["completed_tasks"] == 0
        assert progress["progress_percent"] == 0

    @patch.object(SessionManager, "_stop_data_backup")
    @patch.object(SessionManager, "_save_session_data")
    def test_cleanup(self, mock_save, mock_stop):
        self.manager.configure_session(self.config)
        self.manager.cleanup()
        mock_stop.assert_called()
