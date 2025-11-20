"""Entropy production and thermodynamic tracking."""

import numpy as np
from typing import Dict, Any


class EntropyTracker:
    """Tracks entropy production and distance from equilibrium."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('thermodynamic', {})
        self.landauer_constant = self.config.get('landauer_constant', 1.0)

        self.total_entropy = 0.0
        self.bits_erased = 0.0

    def update(self, num_spikes: int = 0, ignition: bool = False, dt: float = 1.0) -> Dict[str, Any]:
        # Entropy from spikes (information processing)
        self.bits_erased += num_spikes
        spike_entropy = num_spikes * self.landauer_constant

        # Entropy from ignition (state transitions)
        ignition_entropy = 10.0 if ignition else 0.0

        self.total_entropy += spike_entropy + ignition_entropy

        return {
            'total_entropy': float(self.total_entropy),
            'bits_erased': float(self.bits_erased),
            'landauer_cost': float(self.bits_erased * self.landauer_constant)
        }

    def reset(self):
        self.total_entropy = 0.0
        self.bits_erased = 0.0
