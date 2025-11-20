"""Coherence maintenance between minimal and narrative self."""

import numpy as np
from typing import Dict, Any


class CoherenceMaintenance:
    """Maintains unity between minimal and narrative self."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.coherence_score = 1.0

    def update(self, minimal_info: Dict[str, Any], narrative_info: Dict[str, Any]) -> Dict[str, Any]:
        # Check consistency
        minimal_coherence = minimal_info.get('coherence', 1.0)
        narrative_coherence = narrative_info.get('narrative_coherence', 1.0)

        self.coherence_score = 0.6 * minimal_coherence + 0.4 * narrative_coherence

        return {
            'overall_coherence': float(self.coherence_score),
            'phenomenal_unity': self.coherence_score > 0.7
        }

    def reset(self):
        self.coherence_score = 1.0
