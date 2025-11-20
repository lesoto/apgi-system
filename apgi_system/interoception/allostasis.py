"""
Allostatic Regulation

Maintains homeostatic set points and manages allostatic load.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AllostaticSetPoint:
    """Set point for a physiological variable."""
    name: str
    target: float
    acceptable_range: Tuple[float, float]
    current_deviation: float = 0.0
    load_contribution: float = 0.0


class AllostaticRegulator:
    """
    Manages allostatic regulation and cumulative load.

    Allostasis: Achieving stability through change
    - Maintains homeostatic set points
    - Computes deviation from optimal states
    - Tracks cumulative allostatic load
    - Generates regulatory signals
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize allostatic regulator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        intero_config = config.get('interoception', {})
        ranges_config = intero_config.get('allostatic_ranges', {})

        # Define set points for key variables
        self.set_points = [
            AllostaticSetPoint(
                name='heart_rate',
                target=70.0,
                acceptable_range=(65, 75)
            ),
            AllostaticSetPoint(
                name='temperature',
                target=37.0,
                acceptable_range=(36.8, 37.2)
            ),
            AllostaticSetPoint(
                name='glucose',
                target=5.0,
                acceptable_range=(4.5, 5.5)
            ),
            AllostaticSetPoint(
                name='cortisol',
                target=10.0,
                acceptable_range=(8, 12)
            )
        ]

        # Allostatic load tracking
        self.total_load = 0.0
        self.load_decay_rate = 0.001  # per ms
        self.load_accumulation_rate = 0.01

        # Regulation parameters
        self.tight_range_factor = ranges_config.get('tight', 0.1)
        self.moderate_range_factor = ranges_config.get('moderate', 0.2)
        self.wide_range_factor = ranges_config.get('wide', 0.3)

    def update(
        self,
        body_state: Dict[str, float],
        dt: float = 1.0
    ) -> Dict[str, Any]:
        """
        Update allostatic regulation.

        Args:
            body_state: Current physiological state
            dt: Timestep in ms

        Returns:
            Regulation signals and load metrics
        """
        regulation_signals = {}
        total_deviation = 0.0

        # Check each set point
        for set_point in self.set_points:
            if set_point.name in body_state:
                current_value = body_state[set_point.name]

                # Compute deviation from target
                deviation = current_value - set_point.target
                set_point.current_deviation = deviation

                # Check if within acceptable range
                in_range = (set_point.acceptable_range[0] <=
                           current_value <=
                           set_point.acceptable_range[1])

                if not in_range:
                    # Compute load contribution
                    # Larger deviations contribute more to load
                    range_width = (set_point.acceptable_range[1] -
                                 set_point.acceptable_range[0])

                    normalized_deviation = abs(deviation) / range_width
                    set_point.load_contribution = normalized_deviation

                    # Accumulate total load
                    self.total_load += self.load_accumulation_rate * \
                                      normalized_deviation * dt / 1000.0
                else:
                    set_point.load_contribution = 0.0

                # Generate regulatory signal (proportional to deviation)
                regulation_signals[set_point.name] = -0.1 * deviation

                total_deviation += abs(deviation)

        # Decay load over time
        self.total_load *= (1.0 - self.load_decay_rate * dt / 1000.0)
        self.total_load = max(0.0, self.total_load)

        # Clamp load to [0, 1]
        self.total_load = min(1.0, self.total_load)

        return {
            'regulation_signals': regulation_signals,
            'allostatic_load': float(self.total_load),
            'total_deviation': float(total_deviation),
            'set_points_status': self._get_set_points_status(),
            'homeostatic_stability': self._compute_stability()
        }

    def _get_set_points_status(self) -> List[Dict[str, Any]]:
        """Get status of all set points."""
        status = []
        for sp in self.set_points:
            status.append({
                'name': sp.name,
                'target': sp.target,
                'deviation': sp.current_deviation,
                'load_contribution': sp.load_contribution,
                'in_range': abs(sp.current_deviation) < \
                           (sp.acceptable_range[1] - sp.acceptable_range[0]) / 2
            })
        return status

    def _compute_stability(self) -> float:
        """
        Compute overall homeostatic stability (0-1).

        Higher = more stable (all variables near set points).
        """
        total_normalized_deviation = 0.0

        for sp in self.set_points:
            range_width = sp.acceptable_range[1] - sp.acceptable_range[0]
            normalized_dev = abs(sp.current_deviation) / range_width
            total_normalized_deviation += normalized_dev

        # Average across set points
        avg_deviation = total_normalized_deviation / len(self.set_points)

        # Convert to stability (1 - deviation)
        stability = max(0.0, 1.0 - avg_deviation)

        return float(stability)

    def get_allostatic_load(self) -> float:
        """Get current allostatic load."""
        return self.total_load

    def trigger_stressor(self, intensity: float = 0.5):
        """
        Simulate a stressor event.

        Args:
            intensity: Stressor intensity (0-1)
        """
        self.total_load += intensity * 0.2
        self.total_load = min(1.0, self.total_load)

    def reset(self):
        """Reset to baseline."""
        self.total_load = 0.0
        for sp in self.set_points:
            sp.current_deviation = 0.0
            sp.load_contribution = 0.0
