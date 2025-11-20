"""Minimal Self - moment-to-moment embodied self."""

import numpy as np
from typing import Dict, Any


class MinimalSelf:
    """Interoceptive-based minimal self representation."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('self_model', {}).get('minimal_self', {})
        self.update_rate_ms = self.config.get('update_rate_ms', 50)
        self.coherence_threshold = self.config.get('coherence_threshold', 0.7)

        self.body_schema = np.zeros(6)  # Body state representation
        self.temporal_continuity = 1.0
        self.sense_of_agency = 1.0
        self.update_counter = 0.0

    def update(self, body_state: np.ndarray, prediction_accuracy: float, dt: float = 1.0) -> Dict[str, Any]:
        self.update_counter += dt

        if self.update_counter >= self.update_rate_ms:
            self.update_counter = 0
            self.body_schema = 0.9 * self.body_schema + 0.1 * body_state
            self.sense_of_agency = 0.9 * self.sense_of_agency + 0.1 * prediction_accuracy

        self.temporal_continuity = prediction_accuracy

        coherence = min(self.sense_of_agency, self.temporal_continuity)
        depersonalization = coherence < self.config.get('depersonalization_threshold', 0.4)

        return {
            'body_schema': self.body_schema.copy(),
            'coherence': float(coherence),
            'agency': float(self.sense_of_agency),
            'continuity': float(self.temporal_continuity),
            'depersonalization': depersonalization
        }

    def reset(self):
        self.body_schema = np.zeros(6)
        self.temporal_continuity = 1.0
        self.sense_of_agency = 1.0
