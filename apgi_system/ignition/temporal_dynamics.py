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
from ..types import ConfigDict


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
    Orchestrates multi-timescale ignition dynamics across pre-, peri-, and post-ignition phases.

    The IgnitionTimeline class implements the complete temporal dynamics of conscious
    access, from initial context processing through ignition to post-ignition integration.
    It tracks the progression through distinct neural processing stages with realistic
    timing based on neuroscience evidence.

    This implements the temporal cascade model of consciousness, where conscious access
    emerges through a sequence of neural events spanning approximately 1 second from
    stimulus onset to full integration.

    Timeline Phases
    ---------------
    
    **Phase 1: Pre-ignition (-500 to 0 ms)**
    Preparatory processing before threshold crossing:
    - Context recognition (frontal cortex, immediate)
    - Hierarchical predictive pre-activation (0-100ms)
    - Precision modulation by ACC (50-150ms)
    - Somatic marker retrieval (50-100ms latency)
    - Thalamocortical gating preparation (300ms+)
    
    **Phase 2: Ignition Event (0 to +500 ms)**
    Rapid global ignition and broadcasting:
    - Threshold crossing detection (0ms)
    - Frontoparietal network recruitment (<50ms)
    - Recurrent amplification with gamma (50-400ms)
    - Global workspace broadcasting (100-400ms)
    - State maintenance (entire phase)
    
    **Phase 3: Post-ignition (+500 ms onwards)**
    Integration and learning:
    - Reportability interface activation (immediate)
    - Motor planning for report (100-300ms)
    - Working memory encoding (200-500ms)
    - Somatic marker updating/learning (500-1000ms)

    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary
    pre_ignition_duration : float
        Duration of pre-ignition phase (default: 500ms)
    ignition_duration : float
        Duration of ignition event phase (default: 500ms)
    current_phase : TimelinePhase
        Current phase (PRE_IGNITION, IGNITION_EVENT, or POST_IGNITION)
    phase_time : float
        Time spent in current phase (milliseconds)
    total_time : float
        Total simulation time (milliseconds)
    events : List[TimelineEvent]
        Chronological log of timeline events
    max_events : int
        Maximum events to store (default: 1000)
    
    Phase-specific state flags:
    - Pre-ignition: context_recognized, predictions_activated, precision_modulated,
                    somatic_marker_retrieved, thalamus_gated
    - Ignition: threshold_crossed, frontoparietal_recruited, amplification_active,
                broadcasting
    - Post-ignition: reportability_active, motor_planned, memory_encoded,
                     markers_updated

    Examples
    --------
    >>> config = {}
    >>> timeline = IgnitionTimeline(config)
    >>> 
    >>> # Update timeline without ignition (pre-ignition processing)
    >>> for _ in range(100):
    ...     state = timeline.update(ignition_signal=False, dt=1.0)
    >>> print(f"Phase: {state['phase']}")  # "pre_ignition"
    >>> 
    >>> # Trigger ignition
    >>> state = timeline.update(ignition_signal=True, dt=1.0)
    >>> print(f"Phase: {state['phase']}")  # "ignition_event"
    >>> print(f"Ignition active: {state['ignition_active']}")
    >>> 
    >>> # Continue through ignition and post-ignition
    >>> for _ in range(1000):
    ...     state = timeline.update(ignition_signal=False, dt=1.0)
    >>> print(f"Reportable: {state['reportable']}")
    >>> 
    >>> # Check recent events
    >>> print(f"Recent events: {len(state['recent_events'])}")
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize ignition timeline orchestrator.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary. Currently uses default timing parameters,
            but can be extended to include:
            - 'pre_ignition_duration': float (default: 500ms)
            - 'ignition_duration': float (default: 500ms)
            - 'max_events': int (default: 1000)

        Notes
        -----
        The timeline initializes in PRE_IGNITION phase with all state flags
        set to False. Events are logged as processing stages complete.
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
        Update timeline state and process phase-specific dynamics.

        This method advances the timeline through its phases, triggering appropriate
        neural processing events at each stage. It should be called at each simulation
        timestep.

        Parameters
        ----------
        ignition_signal : bool
            Whether ignition threshold was crossed at this timestep.
            When True during PRE_IGNITION phase, triggers transition to IGNITION_EVENT.
        context_info : Optional[Dict[str, Any]], optional
            Contextual information for pre-ignition processing, by default None.
            Can include:
            - 'context_id': Identifier for current context
            - 'predictions': Pre-activated predictions
            - 'markers': Retrieved somatic markers
            Used for logging and debugging.
        dt : float, optional
            Timestep duration in milliseconds, by default 1.0.
            Used for timing phase transitions and event scheduling.

        Returns
        -------
        Dict[str, Any]
            Timeline state information containing:
            - 'phase': Current phase name (str)
            - 'phase_time': Time in current phase (float, ms)
            - 'total_time': Total simulation time (float, ms)
            - 'pre_ignition_complete': Whether all pre-ignition stages done (bool)
            - 'ignition_active': Whether currently in active ignition (bool)
            - 'reportable': Whether content is reportable/conscious (bool)
            - 'recent_events': List of recent timeline events (List[Dict])
                Each event contains: 'time', 'type', 'phase'

        Notes
        -----
        Phase Processing:

        **PRE_IGNITION Phase:**
        - Processes preparatory stages with realistic timing
        - Context recognition: immediate (0ms)
        - Predictive activation: 50ms
        - Precision modulation: 100ms
        - Somatic marker retrieval: 150ms
        - Thalamic gating: 300ms
        - Transitions to IGNITION_EVENT when ignition_signal=True

        **IGNITION_EVENT Phase:**
        - Processes rapid ignition cascade
        - Threshold crossing: immediate (0ms)
        - Frontoparietal recruitment: 20ms
        - Recurrent amplification: 50ms
        - Global broadcast: 100ms
        - Transitions to POST_IGNITION after ignition_duration (500ms)

        **POST_IGNITION Phase:**
        - Processes integration and learning
        - Reportability: immediate (0ms)
        - Motor planning: 200ms
        - Memory encoding: 400ms
        - Marker updating: 700ms
        - Transitions back to PRE_IGNITION after 1000ms

        All events are logged to the events list for analysis and debugging.

        Examples
        --------
        >>> timeline = IgnitionTimeline(config)
        >>> 
        >>> # Pre-ignition processing
        >>> context = {'context_id': 'visual_scene_1'}
        >>> state = timeline.update(
        ...     ignition_signal=False,
        ...     context_info=context,
        ...     dt=1.0
        ... )
        >>> print(f"Pre-ignition complete: {state['pre_ignition_complete']}")
        >>> 
        >>> # Trigger ignition
        >>> state = timeline.update(ignition_signal=True, dt=1.0)
        >>> print(f"Phase: {state['phase']}")  # "ignition_event"
        >>> 
        >>> # Check recent events
        >>> for event in state['recent_events']:
        ...     print(f"{event['time']:.0f}ms: {event['type']}")
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

    def _process_pre_ignition(self, context_info: Optional[Dict[str, Any]], dt: float) -> None:
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

    def _process_ignition_event(self, dt: float) -> None:
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

    def _process_post_ignition(self, dt: float) -> None:
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

    def _transition_to_ignition(self) -> None:
        """Transition from pre-ignition to ignition event."""
        self.current_phase = TimelinePhase.IGNITION_EVENT
        self.phase_time = 0.0
        self._log_event("phase_transition", {"to": "ignition_event"})

        # Reset ignition flags
        self.threshold_crossed = False
        self.frontoparietal_recruited = False
        self.amplification_active = False
        self.broadcasting = False

    def _transition_to_post_ignition(self) -> None:
        """Transition from ignition event to post-ignition."""
        self.current_phase = TimelinePhase.POST_IGNITION
        self.phase_time = 0.0
        self._log_event("phase_transition", {"to": "post_ignition"})

        # Reset post-ignition flags
        self.reportability_active = False
        self.motor_planned = False
        self.memory_encoded = False
        self.markers_updated = False

    def _transition_to_pre_ignition(self) -> None:
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

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
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
        """
        Get timeline events within a specified time range.

        Parameters
        ----------
        start_time : float
            Start of time range in milliseconds (inclusive).
        end_time : float
            End of time range in milliseconds (inclusive).

        Returns
        -------
        List[TimelineEvent]
            List of events that occurred within the specified time range.
            Each TimelineEvent contains:
            - time: float (event timestamp)
            - phase: TimelinePhase (phase when event occurred)
            - event_type: str (type of event)
            - data: Dict (event-specific data)

        Examples
        --------
        >>> timeline = IgnitionTimeline(config)
        >>> # ... run simulation ...
        >>> events = timeline.get_events_in_range(100.0, 500.0)
        >>> for event in events:
        ...     print(f"{event.time:.0f}ms: {event.event_type}")
        """
        return [
            event for event in self.events
            if start_time <= event.time <= end_time
        ]

    def reset(self) -> None:
        """
        Reset timeline to initial state.

        Clears all events, resets phase to PRE_IGNITION, and resets all state flags.
        Useful for starting new simulation runs or experiments.

        Notes
        -----
        Resets:
        - Phase to PRE_IGNITION
        - Phase time to 0
        - Total time to 0
        - All events (cleared)
        - All phase-specific state flags to False
        """
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
