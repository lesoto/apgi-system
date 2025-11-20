"""
Ignition Timeline Implementation

Orchestrates the complete ignition timeline:
- Pre-ignition (-500 to 0 ms)
- Ignition event (0 to +500 ms)
- Post-ignition (+500 ms onwards)
"""

import numpy as np
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class TimelinePhase(Enum):
    """Phases of the ignition timeline."""
    PRE_IGNITION = "pre_ignition"
    IGNITION_EVENT = "ignition_event"
    POST_IGNITION = "post_ignition"


@dataclass
class TimelineEvent:
    """Event in the ignition timeline."""
    time: float
    phase: TimelinePhase
    event_type: str
    data: Dict[str, Any]


class IgnitionTimeline:
    """
    Orchestrates multi-timescale ignition dynamics.

    Timeline:
    -500 to 0 ms: Pre-ignition processing
        - Context recognition
        - Predictive pre-activation
        - Precision modulation
        - Somatic marker retrieval
        - Thalamocortical preparation

    0 to +500 ms: Ignition event
        - Threshold crossing
        - Frontoparietal recruitment
        - Recurrent amplification
        - Global broadcast
        - State maintenance

    +500 ms onwards: Post-ignition
        - Reportability
        - Motor planning
        - Working memory encoding
        - Somatic marker updating
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ignition timeline.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Timeline parameters
        self.pre_ignition_duration = 500.0  # ms
        self.ignition_duration = 500.0      # ms

        # Current state
        self.current_phase = TimelinePhase.PRE_IGNITION
        self.phase_time = 0.0  # Time in current phase
        self.total_time = 0.0  # Total simulation time

        # Event tracking
        self.events: List[TimelineEvent] = []
        self.max_events = 1000

        # Pre-ignition state
        self.context_recognized = False
        self.predictions_activated = False
        self.precision_modulated = False
        self.somatic_marker_retrieved = False
        self.thalamus_gated = False

        # Ignition state
        self.threshold_crossed = False
        self.frontoparietal_recruited = False
        self.amplification_active = False
        self.broadcasting = False

        # Post-ignition state
        self.reportability_active = False
        self.motor_planned = False
        self.memory_encoded = False
        self.markers_updated = False

    def update(
        self,
        ignition_signal: bool,
        context_info: Optional[Dict[str, Any]] = None,
        dt: float = 1.0
    ) -> Dict[str, Any]:
        """
        Update timeline state.

        Args:
            ignition_signal: Whether ignition threshold crossed
            context_info: Contextual information
            dt: Timestep in ms

        Returns:
            Timeline state and events
        """
        self.phase_time += dt
        self.total_time += dt

        # Pre-ignition phase
        if self.current_phase == TimelinePhase.PRE_IGNITION:
            self._process_pre_ignition(context_info, dt)

            # Transition to ignition if signal occurs
            if ignition_signal:
                self._transition_to_ignition()

        # Ignition event phase
        elif self.current_phase == TimelinePhase.IGNITION_EVENT:
            self._process_ignition_event(dt)

            # Transition to post-ignition after duration
            if self.phase_time >= self.ignition_duration:
                self._transition_to_post_ignition()

        # Post-ignition phase
        elif self.current_phase == TimelinePhase.POST_IGNITION:
            self._process_post_ignition(dt)

            # Can return to pre-ignition when complete
            if self.phase_time >= 1000.0:  # 1 second post-ignition
                self._transition_to_pre_ignition()

        return self._get_timeline_state()

    def _process_pre_ignition(self, context_info: Optional[Dict[str, Any]], dt: float):
        """
        Process pre-ignition phase (-500 to 0 ms).

        Activities:
        - Context recognition (frontal cortex)
        - Hierarchical predictive pre-activation
        - Precision modulation (ACC)
        - Somatic marker retrieval (50-100ms latency)
        - Thalamocortical gating preparation
        """
        # Context recognition (immediate)
        if not self.context_recognized and self.phase_time >= 0:
            self.context_recognized = True
            self._log_event("context_recognition", {"context": context_info})

        # Predictive cascades (early, 0-100ms)
        if not self.predictions_activated and self.phase_time >= 50:
            self.predictions_activated = True
            self._log_event("predictive_activation", {})

        # Precision modulation (ACC, 50-150ms)
        if not self.precision_modulated and self.phase_time >= 100:
            self.precision_modulated = True
            self._log_event("precision_modulation", {})

        # Somatic marker retrieval (50-100ms latency)
        if not self.somatic_marker_retrieved and self.phase_time >= 150:
            self.somatic_marker_retrieved = True
            self._log_event("somatic_marker_retrieval", {})

        # Thalamocortical gating preparation (late pre-ignition)
        if not self.thalamus_gated and self.phase_time >= 300:
            self.thalamus_gated = True
            self._log_event("thalamic_gating", {})

    def _process_ignition_event(self, dt: float):
        """
        Process ignition event phase (0 to +500 ms).

        Activities:
        - Threshold crossing detection
        - Rapid frontoparietal recruitment (< 50ms)
        - Recurrent amplification with gamma
        - Global broadcast
        - State maintenance
        """
        # Threshold crossing (immediate)
        if not self.threshold_crossed:
            self.threshold_crossed = True
            self._log_event("threshold_crossing", {"time": 0})

        # Frontoparietal recruitment (rapid, < 50ms)
        if not self.frontoparietal_recruited and self.phase_time >= 20:
            self.frontoparietal_recruited = True
            self._log_event("frontoparietal_recruitment", {})

        # Recurrent amplification (50-400ms)
        if not self.amplification_active and self.phase_time >= 50:
            self.amplification_active = True
            self._log_event("recurrent_amplification_start", {})

        # Global broadcast (100-400ms)
        if not self.broadcasting and self.phase_time >= 100:
            self.broadcasting = True
            self._log_event("global_broadcast_start", {})

    def _process_post_ignition(self, dt: float):
        """
        Process post-ignition phase (+500 ms onwards).

        Activities:
        - Reportability interface activation
        - Motor planning for report
        - Working memory encoding
        - Somatic marker updating
        """
        # Reportability (immediate upon entry)
        if not self.reportability_active and self.phase_time >= 0:
            self.reportability_active = True
            self._log_event("reportability_activated", {})

        # Motor planning (100-300ms)
        if not self.motor_planned and self.phase_time >= 200:
            self.motor_planned = True
            self._log_event("motor_planning", {})

        # Working memory encoding (200-500ms)
        if not self.memory_encoded and self.phase_time >= 400:
            self.memory_encoded = True
            self._log_event("memory_encoding", {})

        # Somatic marker updating (learning, 500-1000ms)
        if not self.markers_updated and self.phase_time >= 700:
            self.markers_updated = True
            self._log_event("somatic_marker_update", {})

    def _transition_to_ignition(self):
        """Transition from pre-ignition to ignition event."""
        self.current_phase = TimelinePhase.IGNITION_EVENT
        self.phase_time = 0.0
        self._log_event("phase_transition", {"to": "ignition_event"})

        # Reset ignition flags
        self.threshold_crossed = False
        self.frontoparietal_recruited = False
        self.amplification_active = False
        self.broadcasting = False

    def _transition_to_post_ignition(self):
        """Transition from ignition event to post-ignition."""
        self.current_phase = TimelinePhase.POST_IGNITION
        self.phase_time = 0.0
        self._log_event("phase_transition", {"to": "post_ignition"})

        # Reset post-ignition flags
        self.reportability_active = False
        self.motor_planned = False
        self.memory_encoded = False
        self.markers_updated = False

    def _transition_to_pre_ignition(self):
        """Transition back to pre-ignition (ready for next event)."""
        self.current_phase = TimelinePhase.PRE_IGNITION
        self.phase_time = 0.0
        self._log_event("phase_transition", {"to": "pre_ignition"})

        # Reset pre-ignition flags
        self.context_recognized = False
        self.predictions_activated = False
        self.precision_modulated = False
        self.somatic_marker_retrieved = False
        self.thalamus_gated = False

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a timeline event."""
        event = TimelineEvent(
            time=self.total_time,
            phase=self.current_phase,
            event_type=event_type,
            data=data
        )
        self.events.append(event)

        # Limit history
        if len(self.events) > self.max_events:
            self.events.pop(0)

    def _get_timeline_state(self) -> Dict[str, Any]:
        """Get current timeline state."""
        return {
            'phase': self.current_phase.value,
            'phase_time': float(self.phase_time),
            'total_time': float(self.total_time),
            'pre_ignition_complete': (
                self.context_recognized and
                self.predictions_activated and
                self.precision_modulated and
                self.somatic_marker_retrieved and
                self.thalamus_gated
            ),
            'ignition_active': (
                self.current_phase == TimelinePhase.IGNITION_EVENT and
                self.broadcasting
            ),
            'reportable': self.reportability_active,
            'recent_events': [
                {'time': e.time, 'type': e.event_type, 'phase': e.phase.value}
                for e in self.events[-10:]  # Last 10 events
            ]
        }

    def get_events_in_range(
        self,
        start_time: float,
        end_time: float
    ) -> List[TimelineEvent]:
        """Get events within a time range."""
        return [
            event for event in self.events
            if start_time <= event.time <= end_time
        ]

    def reset(self):
        """Reset timeline to initial state."""
        self.current_phase = TimelinePhase.PRE_IGNITION
        self.phase_time = 0.0
        self.total_time = 0.0
        self.events.clear()

        # Reset all flags
        self.context_recognized = False
        self.predictions_activated = False
        self.precision_modulated = False
        self.somatic_marker_retrieved = False
        self.thalamus_gated = False
        self.threshold_crossed = False
        self.frontoparietal_recruited = False
        self.amplification_active = False
        self.broadcasting = False
        self.reportability_active = False
        self.motor_planned = False
        self.memory_encoded = False
        self.markers_updated = False
