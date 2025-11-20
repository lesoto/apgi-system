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

    Functions:
    - Learn associations: (context, action) -> body_outcome
    - Retrieve markers when similar contexts encountered
    - Modulate interoceptive gain based on marker valence
    - Bias action selection toward positive outcomes
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize somatic marker system.

        Args:
            config: Configuration dictionary
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

        Args:
            context: Context pattern (state representation)
            action: Action pattern
            body_outcome: Valence of body state outcome (-1 to +1)
            current_time: Current simulation time
        """
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

        Args:
            context: Current context
            action: Proposed action

        Returns:
            gain_modulation: Gain factor (0.5-2.0)
            marker_found: Whether a marker was retrieved
        """
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

        Uses cosine similarity for pattern matching.
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
        """Compute cosine similarity between two vectors."""
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

        Args:
            dt: Timestep in ms
        """
        for marker in self.markers:
            # Decay strength of infrequently accessed markers
            marker.strength *= (1.0 - self.decay_rate * dt / 1000.0)
            marker.strength = max(0.0, marker.strength)

        # Remove very weak markers
        self.markers = [m for m in self.markers if m.strength > 0.1]

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
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

        Strengthens frequently accessed markers, weakens others.
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
        """Clear all markers."""
        self.markers.clear()
        self.last_retrieved_marker = None
        self.total_retrievals = 0
        self.successful_retrievals = 0
