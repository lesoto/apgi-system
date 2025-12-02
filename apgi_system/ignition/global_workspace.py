"""
Global Workspace Implementation

Implements global broadcasting mechanism based on Global Workspace Theory.
When ignition occurs, information is broadcast to all subscriber systems.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from ..validation import InputValidator


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
    Global workspace for conscious broadcasting based on Global Workspace Theory.

    The GlobalWorkspace class implements the core mechanism for conscious access
    through global broadcasting. When ignition occurs, competing contents vie for
    access to the workspace. The winner undergoes recurrent amplification and is
    broadcast to all subscriber systems, making it globally available and reportable.

    This implements Baars' Global Workspace Theory and Dehaene's Global Neuronal
    Workspace model, where consciousness arises from widespread information sharing
    across brain systems.

    Key Mechanisms
    --------------
    1. Competition for Access (Winner-Take-All):
       - Multiple contents compete based on priority and salience
       - Only one content gains access at a time
       - Competition resolves in ~50ms

    2. Recurrent Amplification (100-400ms):
       - Winner undergoes positive feedback amplification
       - Strengthens representation through recurrent processing
       - Corresponds to gamma-band synchronization

    3. Global Broadcasting:
       - Amplified content broadcast to all subscribers
       - Makes information globally available
       - Enables cross-domain integration

    4. State Maintenance:
       - Content maintained for ~1 second
       - Enables working memory and reportability
       - Gradual fade-out after maintenance period

    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary
    amplification_duration_ms : float
        Duration of recurrent amplification phase (default: 300ms)
    maintenance_duration_ms : float
        Duration of state maintenance phase (default: 1000ms)
    fade_duration_ms : float
        Duration of gradual fade-out (default: 200ms)
    state : WorkspaceState
        Current workspace state (IDLE, IGNITING, BROADCASTING, MAINTAINING, FADING)
    current_content : Optional[BroadcastContent]
        Currently broadcast content (None if idle)
    state_time : float
        Time spent in current state (milliseconds)
    competing_contents : List[BroadcastContent]
        Contents competing for workspace access
    amplification_gain : float
        Gain factor for recurrent amplification (default: 2.0)
    recurrent_strength : float
        Strength of recurrent connections (default: 0.8)
    subscribers : List[Callable]
        Systems subscribed to workspace broadcasts
    broadcast_history : List[BroadcastContent]
        History of broadcast contents

    Examples
    --------
    >>> config = {'ignition': {'amplification_duration_ms': 300}}
    >>> workspace = GlobalWorkspace(config)
    >>> 
    >>> # Subscribe a system to broadcasts
    >>> def my_subscriber(content):
    ...     print(f"Received broadcast: {content.source}")
    >>> workspace.subscribe(my_subscriber)
    >>> 
    >>> # Update workspace with ignition
    >>> candidate = np.random.randn(256)
    >>> state = workspace.update(
    ...     ignition_occurred=True,
    ...     candidate_content=candidate,
    ...     source="visual_cortex",
    ...     priority=1.5,
    ...     dt=1.0
    ... )
    >>> print(f"Workspace state: {state['state']}")
    >>> print(f"Is reportable: {state['is_reportable']}")
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize global workspace system.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary with the following structure:
            - 'ignition': Dict containing:
                - 'amplification_duration_ms': float, optional (default: 300)
                    Duration of recurrent amplification phase in milliseconds.
                    Typical range: [200, 500]ms

        Notes
        -----
        The workspace initializes in IDLE state with no content. Subscribers
        can be added via the subscribe() method to receive broadcasts.
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
        Update global workspace state and process broadcasts.

        This method implements the workspace state machine, handling competition,
        amplification, broadcasting, maintenance, and fade-out. It should be called
        at each simulation timestep.

        Parameters
        ----------
        ignition_occurred : bool
            Whether an ignition event was triggered at this timestep.
            When True (and workspace is IDLE), initiates competition for access.
        candidate_content : Optional[np.ndarray], optional
            Content vector competing for workspace access, by default None.
            Typically a neural representation (e.g., 256-dimensional vector).
            If provided, added to competition pool.
        source : str, optional
            Source identifier for the content (e.g., "visual_cortex", "prefrontal"),
            by default "unknown". Used for tracking and debugging.
        priority : float, optional
            Priority/salience of the content, by default 1.0.
            Higher values increase likelihood of winning competition.
            Typical range: [0.5, 2.0]
        dt : float, optional
            Timestep duration in milliseconds, by default 1.0.
            Used for timing state transitions.

        Returns
        -------
        Dict[str, Any]
            Workspace state information containing:
            - 'state': Current state name (str)
            - 'state_time': Time in current state (float, ms)
            - 'is_broadcasting': Whether actively broadcasting (bool)
            - 'is_reportable': Whether content is reportable/conscious (bool)
            - 'num_competitors': Number of contents in competition (int)
            - 'broadcast_content': Dict with content info (if broadcasting):
                - 'shape': Content array shape
                - 'magnitude': L2 norm of content
                - 'source': Source identifier
                - 'priority': Priority value

        Notes
        -----
        State Machine:
        1. IDLE: Waiting for ignition
           - Transition: ignition_occurred → IGNITING
        
        2. IGNITING: Competition phase (~50ms)
           - Select winner from competing contents
           - Transition: after 50ms → BROADCASTING
        
        3. BROADCASTING: Recurrent amplification (300-500ms)
           - Amplify content through positive feedback
           - Broadcast to all subscribers
           - Transition: after amplification_duration_ms → MAINTAINING
        
        4. MAINTAINING: Sustained state (~1000ms)
           - Maintain content for working memory
           - Continue broadcasting
           - Transition: after maintenance_duration_ms → FADING
        
        5. FADING: Gradual fade-out (~200ms)
           - Reduce content magnitude gradually
           - Transition: after fade_duration_ms → IDLE

        Content is reportable (conscious) during BROADCASTING and MAINTAINING states.

        Examples
        --------
        >>> workspace = GlobalWorkspace(config)
        >>> content = np.random.randn(256)
        >>> 
        >>> # First update: add candidate
        >>> state = workspace.update(
        ...     ignition_occurred=False,
        ...     candidate_content=content,
        ...     source="visual",
        ...     priority=1.2
        ... )
        >>> 
        >>> # Second update: trigger ignition
        >>> state = workspace.update(ignition_occurred=True, dt=1.0)
        >>> print(f"State: {state['state']}")  # "igniting"
        >>> 
        >>> # Continue updating to progress through states
        >>> for _ in range(100):
        ...     state = workspace.update(ignition_occurred=False, dt=1.0)
        >>> print(f"Reportable: {state['is_reportable']}")
        """
        # Input validation
        if not isinstance(ignition_occurred, bool):
            raise TypeError(f"ignition_occurred must be bool, got {type(ignition_occurred)}")
        
        if candidate_content is not None:
            InputValidator.validate_array(candidate_content, "candidate_content")
        
        if not isinstance(source, str):
            raise TypeError(f"source must be str, got {type(source)}")
        
        InputValidator.validate_scalar(priority, "priority", positive=True)
        InputValidator.validate_scalar(dt, "dt", positive=True)
        
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
        Subscribe a system to receive workspace broadcasts.

        Subscribers are called with broadcast content during BROADCASTING and
        MAINTAINING states. This enables global information sharing across
        brain systems.

        Parameters
        ----------
        callback : Callable
            Function to call with broadcast content.
            Signature: callback(content: BroadcastContent) -> None
            The callback receives a BroadcastContent object containing:
            - content: np.ndarray (the broadcast representation)
            - ignition_time: float (when ignition occurred)
            - source: str (content source)
            - priority: float (content priority)
            - metadata: Dict (additional information)

        Notes
        -----
        Subscriber errors are caught and logged to prevent one failing
        subscriber from disrupting the entire broadcast mechanism.

        Examples
        --------
        >>> workspace = GlobalWorkspace(config)
        >>> 
        >>> def motor_system_subscriber(content):
        ...     print(f"Motor system received: {content.source}")
        ...     # Use content for motor planning
        >>> 
        >>> def memory_system_subscriber(content):
        ...     print(f"Memory encoding: {content.content.shape}")
        ...     # Encode content to working memory
        >>> 
        >>> workspace.subscribe(motor_system_subscriber)
        >>> workspace.subscribe(memory_system_subscriber)
        """
        self.subscribers.append(callback)

    def get_current_broadcast(self) -> Optional[np.ndarray]:
        """
        Get currently broadcast content.

        Returns
        -------
        Optional[np.ndarray]
            Copy of current broadcast content if in BROADCASTING or MAINTAINING state,
            None otherwise. Returns a copy to prevent external modification.

        Notes
        -----
        This provides read-only access to the current conscious content.
        Content is only available during active broadcasting states.
        """
        if self.current_content is not None and \
           self.state in [WorkspaceState.BROADCASTING, WorkspaceState.MAINTAINING]:
            return self.current_content.content.copy()
        return None

    def is_reportable(self) -> bool:
        """
        Check if current content is reportable (conscious).

        Returns
        -------
        bool
            True if content is currently reportable (conscious), False otherwise.

        Notes
        -----
        Content is reportable during BROADCASTING and MAINTAINING states,
        corresponding to the period when information is globally available
        and can be verbally reported or used for decision-making.

        This implements the reportability criterion for consciousness:
        information is conscious if it can be reported and used flexibly
        across cognitive domains.
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
        """
        Reset workspace to initial state.

        Clears all content, resets state to IDLE, and removes all subscribers.
        Useful for starting new simulation runs or experiments.

        Notes
        -----
        Resets:
        - State to IDLE
        - Current content to None
        - State time to 0
        - Competition pool (cleared)
        - All subscribers (removed)
        """
        self.state = WorkspaceState.IDLE
        self.current_content = None
        self.state_time = 0.0
        self.competing_contents.clear()
        self.subscribers.clear()
