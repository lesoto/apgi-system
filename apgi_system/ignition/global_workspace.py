"""
Global Workspace Implementation

Implements global broadcasting mechanism based on Global Workspace Theory.
When ignition occurs, information is broadcast to all subscriber systems.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum


class WorkspaceState(Enum):
    """States of the global workspace."""
    IDLE = "idle"
    IGNITING = "igniting"
    BROADCASTING = "broadcasting"
    MAINTAINING = "maintaining"
    FADING = "fading"


@dataclass
class BroadcastContent:
    """Content being broadcast in the global workspace."""
    content: np.ndarray
    ignition_time: float
    source: str
    priority: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class GlobalWorkspace:
    """
    Global workspace for conscious broadcasting.

    Implements:
    - Competition for access (winner-take-all)
    - Recurrent amplification (100-400ms)
    - Sustained state maintenance
    - Gradual fade-out
    - Reportability interface
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize global workspace.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        ignition_config = config.get('ignition', {})

        # Workspace parameters
        self.amplification_duration_ms = ignition_config.get(
            'amplification_duration_ms', 300
        )
        self.maintenance_duration_ms = 1000.0  # How long to maintain after amp
        self.fade_duration_ms = 200.0  # Gradual fade

        # State
        self.state = WorkspaceState.IDLE
        self.current_content: Optional[BroadcastContent] = None
        self.state_time = 0.0  # Time in current state

        # Competition
        self.competing_contents: List[BroadcastContent] = []

        # Amplification dynamics
        self.amplification_gain = 2.0
        self.recurrent_strength = 0.8

        # Subscribers (other systems that receive broadcasts)
        self.subscribers: List[Callable] = []

        # Broadcast history
        self.broadcast_history: List[BroadcastContent] = []
        self.max_history = 100

    def update(
        self,
        ignition_occurred: bool,
        candidate_content: Optional[np.ndarray] = None,
        source: str = "unknown",
        priority: float = 1.0,
        dt: float = 1.0
    ) -> Dict[str, Any]:
        """
        Update global workspace.

        Args:
            ignition_occurred: Whether ignition signal was triggered
            candidate_content: Content competing for access
            source: Source of the content
            priority: Priority level
            dt: Timestep in ms

        Returns:
            Workspace state information
        """
        # Add candidate to competition if provided
        if candidate_content is not None:
            self.competing_contents.append(BroadcastContent(
                content=candidate_content.copy(),
                ignition_time=self.state_time,
                source=source,
                priority=priority
            ))

        # State machine
        if self.state == WorkspaceState.IDLE:
            if ignition_occurred and len(self.competing_contents) > 0:
                self._transition_to_igniting()

        elif self.state == WorkspaceState.IGNITING:
            self.state_time += dt

            # Select winner from competition
            if self.state_time >= 50.0:  # 50ms for competition resolution
                self._select_winner()
                self._transition_to_broadcasting()

        elif self.state == WorkspaceState.BROADCASTING:
            self.state_time += dt

            # Recurrent amplification
            if self.current_content is not None:
                self._amplify_content()

            if self.state_time >= self.amplification_duration_ms:
                self._transition_to_maintaining()

        elif self.state == WorkspaceState.MAINTAINING:
            self.state_time += dt

            if self.state_time >= self.maintenance_duration_ms:
                self._transition_to_fading()

        elif self.state == WorkspaceState.FADING:
            self.state_time += dt

            # Gradual reduction
            if self.current_content is not None:
                fade_factor = 1.0 - (self.state_time / self.fade_duration_ms)
                self.current_content.content *= max(0, fade_factor)

            if self.state_time >= self.fade_duration_ms:
                self._transition_to_idle()

        # Broadcast to subscribers
        if self.state in [WorkspaceState.BROADCASTING, WorkspaceState.MAINTAINING]:
            self._broadcast_to_subscribers()

        return self._get_state_info()

    def _transition_to_igniting(self):
        """Transition to igniting state."""
        self.state = WorkspaceState.IGNITING
        self.state_time = 0.0

    def _transition_to_broadcasting(self):
        """Transition to broadcasting state."""
        self.state = WorkspaceState.BROADCASTING
        self.state_time = 0.0

    def _transition_to_maintaining(self):
        """Transition to maintaining state."""
        self.state = WorkspaceState.MAINTAINING
        self.state_time = 0.0

    def _transition_to_fading(self):
        """Transition to fading state."""
        self.state = WorkspaceState.FADING
        self.state_time = 0.0

    def _transition_to_idle(self):
        """Transition to idle state."""
        self.state = WorkspaceState.IDLE
        self.state_time = 0.0
        self.current_content = None
        self.competing_contents.clear()

    def _select_winner(self):
        """
        Select winner from competing contents.

        Uses priority and salience to determine winner.
        """
        if len(self.competing_contents) == 0:
            return

        # Compute scores (priority + random noise for tie-breaking)
        scores = [
            content.priority + 0.1 * np.random.rand()
            for content in self.competing_contents
        ]

        # Winner takes all
        winner_idx = np.argmax(scores)
        self.current_content = self.competing_contents[winner_idx]

        # Clear competition
        self.competing_contents.clear()

    def _amplify_content(self):
        """
        Apply recurrent amplification to current content.

        Strengthens the representation through positive feedback.
        """
        if self.current_content is None:
            return

        # Recurrent amplification (increases magnitude)
        amplification = 1.0 + (self.amplification_gain - 1.0) * \
                       (self.state_time / self.amplification_duration_ms)

        self.current_content.content *= amplification

        # Add noise for realism
        noise = np.random.randn(*self.current_content.content.shape) * 0.01
        self.current_content.content += noise

    def _broadcast_to_subscribers(self):
        """Broadcast current content to all subscribers."""
        if self.current_content is None:
            return

        for subscriber in self.subscribers:
            try:
                subscriber(self.current_content)
            except Exception as e:
                # Don't let subscriber errors crash the workspace
                print(f"Subscriber error: {e}")

    def subscribe(self, callback: Callable):
        """
        Subscribe to workspace broadcasts.

        Args:
            callback: Function to call with broadcast content
        """
        self.subscribers.append(callback)

    def get_current_broadcast(self) -> Optional[np.ndarray]:
        """Get currently broadcast content."""
        if self.current_content is not None and \
           self.state in [WorkspaceState.BROADCASTING, WorkspaceState.MAINTAINING]:
            return self.current_content.content.copy()
        return None

    def is_reportable(self) -> bool:
        """
        Check if current content is reportable (conscious).

        Content is reportable during broadcasting and maintaining phases.
        """
        return self.state in [WorkspaceState.BROADCASTING, WorkspaceState.MAINTAINING]

    def _get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        info = {
            'state': self.state.value,
            'state_time': float(self.state_time),
            'is_broadcasting': self.state in [
                WorkspaceState.BROADCASTING,
                WorkspaceState.MAINTAINING
            ],
            'is_reportable': self.is_reportable(),
            'num_competitors': len(self.competing_contents)
        }

        if self.current_content is not None:
            info['broadcast_content'] = {
                'shape': self.current_content.content.shape,
                'magnitude': float(np.linalg.norm(self.current_content.content)),
                'source': self.current_content.source,
                'priority': float(self.current_content.priority)
            }

        return info

    def reset(self):
        """Reset workspace to initial state."""
        self.state = WorkspaceState.IDLE
        self.current_content = None
        self.state_time = 0.0
        self.competing_contents.clear()
        self.subscribers.clear()
