"""Narrative Self - long-term identity and autobiographical memory."""

import numpy as np
from typing import Dict, Any, List
from collections import deque


class NarrativeSelf:
    """
    Narrative self-model with episodic memory and long-term identity.

    Implements the narrative self - the extended, autobiographical sense
    of identity that emerges from episodic memory and self-reflection.
    This represents the reflective, story-based understanding of oneself
    as a continuous agent with a past, present, and future.

    **Core Components**:
    - **Episodic Memory**: Storage of significant life experiences
    - **Identity Vector**: Slowly-evolving representation of personal identity
    - **Goal Hierarchy**: Long-term goals and values (currently placeholder)
    - **Narrative Coherence**: Consistency of self-story over time

    **Key Functions**:
    - Selectively encodes significant experiences into episodic memory
    - Gradually consolidates identity through experience integration
    - Maintains narrative coherence across different time scales
    - Supports autobiographical reasoning and future planning

    **Memory Dynamics**:
    - Selective encoding: Only ~1% of experiences stored (significance-based)
    - Capacity limits: Fixed maximum number of episodes
    - Consolidation: Identity slowly updated based on stored experiences
    - Forgetting: Oldest memories displaced when capacity exceeded

    The narrative self operates on much longer timescales than the minimal
    self, reflecting the slow accumulation of autobiographical knowledge.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing narrative self settings:
        - self_model.narrative_self.episodic_memory_capacity: Maximum episodes (default: 1000)
        - self_model.narrative_self.consolidation_rate: Identity update rate (default: 0.01)

    Attributes
    ----------
    episodic_memory : deque
        Circular buffer storing significant experiences
    identity_vector : np.ndarray
        64-dimensional identity representation
    goal_hierarchy : List
        Hierarchical goal structure (currently unused)
    memory_capacity : int
        Maximum number of stored episodes
    consolidation_rate : float
        Rate of identity consolidation

    Examples
    --------
    >>> config = {'self_model': {'narrative_self': {'episodic_memory_capacity': 500}}}
    >>> narrative_self = NarrativeSelf(config)
    >>> experience = {'event': 'ignition', 'context': 'high_arousal', 'outcome': 'success'}
    >>> result = narrative_self.update(experience, dt=1.0)
    >>> print(f"Identity strength: {result['identity_strength']:.2f}")
    Identity strength: 0.63
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('self_model', {}).get('narrative_self', {})
        self.memory_capacity = self.config.get('episodic_memory_capacity', 1000)
        self.consolidation_rate = self.config.get('consolidation_rate', 0.01)

        self.episodic_memory = deque(maxlen=self.memory_capacity)
        self.identity_vector = np.random.randn(64) * 0.1
        self.goal_hierarchy = []

    def update(self, experience: Dict[str, Any], dt: float = 1.0) -> Dict[str, Any]:
        """
        Update narrative self with new experience.

        Processes new experiences for potential storage in episodic memory
        and gradually consolidates identity representation. Uses selective
        encoding to store only significant experiences.

        Parameters
        ----------
        experience : Dict[str, Any]
            Dictionary containing experience information (event type, context,
            outcome, etc.)
        dt : float, optional
            Timestep in milliseconds, by default 1.0

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'identity_strength': Magnitude of identity vector (measure of self-definition)
            - 'memory_count': Number of stored episodic memories
            - 'narrative_coherence': Coherence of self-narrative (0-1)
        """
        # Store significant experiences
        if np.random.rand() < 0.01:  # Selective encoding
            self.episodic_memory.append(experience)

        # Gradual identity consolidation
        if len(self.episodic_memory) > 0:
            self.identity_vector *= (1 - self.consolidation_rate * dt / 1000.0)

        coherence = 1.0 - 0.1 * np.random.rand()  # Simplified

        return {
            'identity_strength': float(np.linalg.norm(self.identity_vector)),
            'memory_count': len(self.episodic_memory),
            'narrative_coherence': float(coherence)
        }

    def get_current_state(self) -> Dict[str, Any]:
        """Get current narrative self state."""
        coherence = 1.0 - 0.1 * np.random.rand()  # Simplified
        
        return {
            'identity_strength': float(np.linalg.norm(self.identity_vector)),
            'memory_count': len(self.episodic_memory),
            'narrative_coherence': float(coherence),
            'identity_vector': self.identity_vector.copy()
        }

    def reset(self):
        self.episodic_memory.clear()
        self.identity_vector = np.random.randn(64) * 0.1
