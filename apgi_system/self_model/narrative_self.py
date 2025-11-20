"""Narrative Self - long-term identity and autobiographical memory."""

import numpy as np
from typing import Dict, Any, List
from collections import deque


class NarrativeSelf:
    """Long-timescale self-model with episodic memory."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('self_model', {}).get('narrative_self', {})
        self.memory_capacity = self.config.get('episodic_memory_capacity', 1000)
        self.consolidation_rate = self.config.get('consolidation_rate', 0.01)

        self.episodic_memory = deque(maxlen=self.memory_capacity)
        self.identity_vector = np.random.randn(64) * 0.1
        self.goal_hierarchy = []

    def update(self, experience: Dict[str, Any], dt: float = 1.0) -> Dict[str, Any]:
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

    def reset(self):
        self.episodic_memory.clear()
        self.identity_vector = np.random.randn(64) * 0.1
