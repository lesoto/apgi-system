"""
Somatic Marker System

Implements Damasio's somatic marker hypothesis:
Learns associations between contexts/actions and body states,
then uses these to bias decision-making.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from apgi_system.validation import InputValidator


@dataclass
class SomaticMarker:
    """
    A somatic marker: association between situation and body response.

    Stores: (context_pattern, action_pattern) -> body_outcome
    """
    context_pattern: np.ndarray
    action_pattern: np.ndarray
    body_outcome: float  # Valence: positive = good, negative = bad
    strength: float = 1.0  # Association strength
    access_count: int = 0
    last_update_time: float = 0.0


class SomaticMarkerSystem:
    """
    Stores and retrieves somatic markers for decision guidance.

    Implements Damasio's somatic marker hypothesis: the brain learns
    associations between situations/actions and their bodily outcomes
    (positive or negative), then uses these learned associations to bias
    future decision-making. When a similar situation is encountered, the
    retrieved marker modulates interoceptive gain to guide behavior.

    The system performs four key functions:
    1. **Learning**: Store associations (context, action) -> body_outcome
    2. **Retrieval**: Find markers matching current context-action pairs
    3. **Gain Modulation**: Convert marker valence to interoceptive gain
    4. **Decision Biasing**: Bias action selection toward positive outcomes

    Markers are stored with:
    - Context pattern: State representation when marker was learned
    - Action pattern: Action taken in that context
    - Body outcome: Valence of resulting body state (-1 to +1)
    - Strength: Association strength (0-1), decays if unused
    - Access count: Number of times retrieved

    Retrieval uses cosine similarity for pattern matching. When a marker
    is retrieved, its body outcome is converted to a gain modulation factor:
    - Positive outcome (good) -> increase gain (enhance interoceptive signal)
    - Negative outcome (bad) -> decrease gain (suppress interoceptive signal)

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing:
        - somatic_markers.capacity: Maximum number of markers (default: 10000)
        - somatic_markers.learning_rate: Learning rate for updates (default: 0.05)
        - somatic_markers.decay_rate: Decay rate for unused markers (default: 0.001)
        - somatic_markers.retrieval_threshold: Minimum strength for retrieval (default: 0.3)
        - somatic_markers.gain_modulation_range: [min, max] gain values (default: [0.5, 2.0])

    Attributes
    ----------
    markers : List[SomaticMarker]
        Stored somatic markers
    capacity : int
        Maximum number of markers to store
    learning_rate : float
        Rate at which marker outcomes are updated
    decay_rate : float
        Rate at which unused markers decay
    retrieval_threshold : float
        Minimum strength required for successful retrieval
    gain_range : List[float]
        [min, max] range for gain modulation
    total_retrievals : int
        Total number of retrieval attempts
    successful_retrievals : int
        Number of successful retrievals

    Examples
    --------
    >>> config = {'somatic_markers': {'capacity': 1000}}
    >>> sm_system = SomaticMarkerSystem(config)
    >>> context = np.random.randn(10)
    >>> action = np.random.randn(5)
    >>> sm_system.learn(context, action, body_outcome=0.8, current_time=100.0)
    >>> gain, found = sm_system.retrieve(context, action)
    >>> print(f"Gain: {gain}, Found: {found}")
    Gain: 1.65, Found: True
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize somatic marker system with configuration.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing somatic marker settings
        """
        self.config = config
        marker_config = config.get('somatic_markers', {})

        # System parameters
        self.capacity = marker_config.get('capacity', 10000)
        self.learning_rate = marker_config.get('learning_rate', 0.05)
        self.decay_rate = marker_config.get('decay_rate', 0.001)
        self.retrieval_threshold = marker_config.get('retrieval_threshold', 0.3)
        self.gain_range = marker_config.get('gain_modulation_range', [0.5, 2.0])

        # Storage
        self.markers: List[SomaticMarker] = []

        # Retrieval cache
        self.last_retrieved_marker: Optional[SomaticMarker] = None

        # Statistics
        self.total_retrievals = 0
        self.successful_retrievals = 0

    def learn(
        self,
        context: np.ndarray,
        action: np.ndarray,
        body_outcome: float,
        current_time: float = 0.0
    ):
        """
        Learn or update a somatic marker.

        If a similar marker already exists (based on cosine similarity of
        context and action patterns), updates its body outcome using the
        learning rate. Otherwise, creates a new marker (or replaces the
        weakest marker if at capacity).

        The body outcome is updated using exponential moving average:
        new_outcome = (1 - lr) * old_outcome + lr * observed_outcome

        Parameters
        ----------
        context : np.ndarray
            Context pattern (state representation) when outcome occurred
        action : np.ndarray
            Action pattern that was taken
        body_outcome : float
            Valence of resulting body state, in range [-1, 1]:
            - +1: Very positive outcome (good body state)
            - 0: Neutral outcome
            - -1: Very negative outcome (bad body state)
        current_time : float, optional
            Current simulation time in milliseconds, by default 0.0

        Examples
        --------
        >>> sm_system = SomaticMarkerSystem(config)
        >>> context = np.array([1.0, 0.5, -0.3])
        >>> action = np.array([0.8, -0.2])
        >>> sm_system.learn(context, action, body_outcome=0.7, current_time=100.0)
        >>> print(len(sm_system.markers))
        1
        """
        # Validate inputs
        InputValidator.validate_array(context, "context")
        InputValidator.validate_array(action, "action")
        InputValidator.validate_scalar(
            body_outcome,
            "body_outcome",
            value_range=(-1.0, 1.0)
        )
        InputValidator.validate_scalar(
            current_time,
            "current_time",
            value_range=(0.0, 1e10)
        )
        
        # Check if similar marker exists
        existing_marker = self._find_similar_marker(context, action)

        if existing_marker is not None:
            # Update existing marker
            existing_marker.body_outcome = (
                (1 - self.learning_rate) * existing_marker.body_outcome +
                self.learning_rate * body_outcome
            )
            existing_marker.strength = min(1.0, existing_marker.strength + 0.1)
            existing_marker.last_update_time = current_time

        else:
            # Create new marker
            if len(self.markers) < self.capacity:
                marker = SomaticMarker(
                    context_pattern=context.copy(),
                    action_pattern=action.copy(),
                    body_outcome=body_outcome,
                    strength=0.5,  # Start with moderate strength
                    last_update_time=current_time
                )
                self.markers.append(marker)
            else:
                # Replace weakest marker
                weakest_idx = np.argmin([m.strength for m in self.markers])
                self.markers[weakest_idx] = SomaticMarker(
                    context_pattern=context.copy(),
                    action_pattern=action.copy(),
                    body_outcome=body_outcome,
                    strength=0.5,
                    last_update_time=current_time
                )

    def retrieve(
        self,
        context: np.ndarray,
        action: np.ndarray
    ) -> Tuple[float, bool]:
        """
        Retrieve somatic marker for a context-action pair.

        Searches for a marker matching the given context-action pair using
        cosine similarity. If a sufficiently strong marker is found, converts
        its body outcome to a gain modulation factor:

        - Positive outcome -> gain > 1.0 (enhance interoceptive signal)
        - Neutral outcome -> gain = 1.0 (no modulation)
        - Negative outcome -> gain < 1.0 (suppress interoceptive signal)

        The gain is computed as:
        normalized_outcome = (body_outcome + 1) / 2  # Map [-1,1] to [0,1]
        gain = min_gain + normalized_outcome * (max_gain - min_gain)

        Parameters
        ----------
        context : np.ndarray
            Current context pattern
        action : np.ndarray
            Proposed action pattern

        Returns
        -------
        gain_modulation : float
            Gain factor in range [0.5, 2.0] (configurable):
            - Values > 1.0 enhance interoceptive precision
            - Values < 1.0 suppress interoceptive precision
            - 1.0 returned if no marker found (neutral)
        marker_found : bool
            True if a matching marker was retrieved, False otherwise

        Examples
        --------
        >>> sm_system = SomaticMarkerSystem(config)
        >>> context = np.array([1.0, 0.5])
        >>> action = np.array([0.8])
        >>> sm_system.learn(context, action, body_outcome=0.6, current_time=0.0)
        >>> gain, found = sm_system.retrieve(context, action)
        >>> print(f"Gain: {gain:.2f}, Found: {found}")
        Gain: 1.45, Found: True
        """
        # Validate inputs
        InputValidator.validate_array(context, "context")
        InputValidator.validate_array(action, "action")
        
        self.total_retrievals += 1

        # Find matching marker
        marker = self._find_similar_marker(context, action)

        if marker is not None and marker.strength > self.retrieval_threshold:
            # Successful retrieval
            self.successful_retrievals += 1
            marker.access_count += 1
            self.last_retrieved_marker = marker

            # Convert body outcome to gain modulation
            # Positive outcome -> increase gain (enhance interoceptive precision)
            # Negative outcome -> decrease gain (suppress interoceptive signal)
            normalized_outcome = (marker.body_outcome + 1.0) / 2.0  # Map [-1,1] to [0,1]
            gain = self.gain_range[0] + normalized_outcome * (
                self.gain_range[1] - self.gain_range[0]
            )

            return float(gain), True

        else:
            # No marker found - neutral gain
            self.last_retrieved_marker = None
            return 1.0, False

    def _find_similar_marker(
        self,
        context: np.ndarray,
        action: np.ndarray,
        similarity_threshold: float = 0.8
    ) -> Optional[SomaticMarker]:
        """
        Find marker similar to given context-action pair.

        Uses cosine similarity for pattern matching. Computes combined
        similarity as weighted average: 0.7 * context_sim + 0.3 * action_sim
        (context weighted more heavily than action).

        Parameters
        ----------
        context : np.ndarray
            Context pattern to match
        action : np.ndarray
            Action pattern to match
        similarity_threshold : float, optional
            Minimum similarity required for match, by default 0.8

        Returns
        -------
        Optional[SomaticMarker]
            Best matching marker if similarity exceeds threshold, None otherwise
        """
        if len(self.markers) == 0:
            return None

        best_similarity = 0.0
        best_marker = None

        for marker in self.markers:
            # Compute similarity
            context_sim = self._cosine_similarity(context, marker.context_pattern)
            action_sim = self._cosine_similarity(action, marker.action_pattern)

            # Combined similarity (weighted average)
            combined_sim = 0.7 * context_sim + 0.3 * action_sim

            if combined_sim > best_similarity and combined_sim > similarity_threshold:
                best_similarity = combined_sim
                best_marker = marker

        return best_marker

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Handles vectors of different lengths by truncating to the shorter
        length. Returns 0.0 if either vector has zero norm.

        Parameters
        ----------
        a : np.ndarray
            First vector
        b : np.ndarray
            Second vector

        Returns
        -------
        float
            Cosine similarity in range [-1, 1], where:
            - 1.0 = identical direction
            - 0.0 = orthogonal
            - -1.0 = opposite direction
        """
        # Handle different sizes
        min_len = min(len(a), len(b))
        a_trunc = a[:min_len]
        b_trunc = b[:min_len]

        norm_a = np.linalg.norm(a_trunc)
        norm_b = np.linalg.norm(b_trunc)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.dot(a_trunc, b_trunc) / (norm_a * norm_b))

    def decay_markers(self, dt: float):
        """
        Apply decay to unused markers.

        Reduces the strength of all markers proportionally to time elapsed.
        Markers with very low strength (< 0.1) are removed from storage.
        This implements forgetting of rarely-used associations.

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        for marker in self.markers:
            # Decay strength of infrequently accessed markers
            marker.strength *= (1.0 - self.decay_rate * dt / 1000.0)
            marker.strength = max(0.0, marker.strength)

        # Remove very weak markers
        self.markers = [m for m in self.markers if m.strength > 0.1]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get system statistics.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'num_markers': Number of stored markers
            - 'capacity_used': Fraction of capacity used (0-1)
            - 'total_retrievals': Total retrieval attempts
            - 'successful_retrievals': Number of successful retrievals
            - 'retrieval_success_rate': Fraction of successful retrievals
            - 'avg_strength': Average marker strength
            - 'avg_outcome': Average body outcome across markers
        """
        if len(self.markers) == 0:
            return {
                'num_markers': 0,
                'retrieval_success_rate': 0.0,
                'avg_strength': 0.0
            }

        return {
            'num_markers': len(self.markers),
            'capacity_used': len(self.markers) / self.capacity,
            'total_retrievals': self.total_retrievals,
            'successful_retrievals': self.successful_retrievals,
            'retrieval_success_rate': (
                self.successful_retrievals / max(1, self.total_retrievals)
            ),
            'avg_strength': float(np.mean([m.strength for m in self.markers])),
            'avg_outcome': float(np.mean([m.body_outcome for m in self.markers]))
        }

    def consolidate(self):
        """
        Consolidate markers (simulate sleep/offline processing).

        Simulates memory consolidation during sleep or offline periods:
        - Strengthens frequently accessed markers (access_count > 5)
        - Weakens rarely accessed markers
        - Resets access counts

        This implements the principle that important associations (frequently
        retrieved) are strengthened during consolidation, while unimportant
        associations decay.
        """
        for marker in self.markers:
            if marker.access_count > 5:
                # Strengthen frequently used markers
                marker.strength = min(1.0, marker.strength + 0.1)
            else:
                # Weaken rarely used markers
                marker.strength *= 0.9

            # Reset access count
            marker.access_count = 0

    def reset(self):
        """
        Clear all markers and reset statistics.

        Removes all stored markers and resets retrieval statistics to zero.
        """
        self.markers.clear()
        self.last_retrieved_marker = None
        self.total_retrievals = 0
        self.successful_retrievals = 0
