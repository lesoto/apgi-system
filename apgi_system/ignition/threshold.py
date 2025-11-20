"""
Ignition Threshold Computation

Implements dynamic threshold for global ignition based on:
- Exteroceptive precision-weighted prediction errors
- Interoceptive precision-weighted errors with somatic markers
- Metabolic state and allostatic load
- Recent ignition history
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from collections import deque


class IgnitionThreshold:
    """
    Computes ignition signal and dynamic threshold.

    Ignition occurs when:
        S_t > θ_t

    Where:
        S_t = S_extero + S_intero
        S_extero = Π_e * |ε_e|
        S_intero = Π_i * M * |ε_i|

        M = somatic marker gain
        θ_t = dynamic threshold (context-dependent)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ignition threshold system.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        ignition_config = config.get('ignition', {})

        # Threshold parameters
        self.baseline_threshold = ignition_config.get('baseline_threshold', 2.0)
        self.threshold_range = ignition_config.get('threshold_range', [1.0, 5.0])
        self.sigmoid_alpha = ignition_config.get('sigmoid_alpha', 5.0)

        # Current state
        self.current_threshold = self.baseline_threshold
        self.current_signal = 0.0
        self.ignition_probability = 0.0

        # Components
        self.extero_signal = 0.0
        self.intero_signal = 0.0

        # Recent ignition history
        self.refractory_period_ms = ignition_config.get('refractory_period_ms', 200)
        self.recent_ignitions = deque(maxlen=100)
        self.last_ignition_time = -np.inf

        # Metabolic tracking
        self.metabolic_reserves = 1.0  # 0-1, starts full
        self.allostatic_load = 0.0     # 0-1, starts at zero

        # Signal history for analysis
        self.signal_history = deque(maxlen=1000)
        self.threshold_history = deque(maxlen=1000)

    def compute_ignition_signal(
        self,
        extero_error: np.ndarray,
        extero_precision: float,
        intero_error: np.ndarray,
        intero_precision: float,
        somatic_marker_gain: float = 1.0,
        current_time: float = 0.0
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Compute ignition signal and determine if ignition occurs.

        Args:
            extero_error: Exteroceptive prediction error
            extero_precision: Exteroceptive precision
            intero_error: Interoceptive prediction error
            intero_precision: Interoceptive precision
            somatic_marker_gain: Gain from somatic markers (0.5-2.0)
            current_time: Current simulation time (ms)

        Returns:
            ignition_occurred: Boolean indicating ignition
            components: Dictionary with signal components
        """
        # Exteroceptive component
        self.extero_signal = extero_precision * np.linalg.norm(extero_error)

        # Interoceptive component with somatic marker modulation
        self.intero_signal = intero_precision * somatic_marker_gain * \
                            np.linalg.norm(intero_error)

        # Total accumulated signal
        self.current_signal = self.extero_signal + self.intero_signal

        # Update dynamic threshold
        self._update_threshold(current_time)

        # Compute ignition probability (sigmoid function)
        diff = self.current_signal - self.current_threshold
        self.ignition_probability = self._sigmoid(self.sigmoid_alpha * diff)

        # Determine if ignition occurs
        ignition_occurred = False

        # Check refractory period
        if (current_time - self.last_ignition_time) >= self.refractory_period_ms:
            # Stochastic ignition based on probability
            if np.random.rand() < self.ignition_probability:
                ignition_occurred = True
                self.last_ignition_time = current_time
                self.recent_ignitions.append({
                    'time': current_time,
                    'signal': self.current_signal,
                    'threshold': self.current_threshold
                })

        # Record history
        self.signal_history.append(self.current_signal)
        self.threshold_history.append(self.current_threshold)

        components = {
            'total_signal': float(self.current_signal),
            'extero_signal': float(self.extero_signal),
            'intero_signal': float(self.intero_signal),
            'threshold': float(self.current_threshold),
            'ignition_probability': float(self.ignition_probability),
            'somatic_marker_gain': float(somatic_marker_gain),
            'ignition_occurred': ignition_occurred
        }

        return ignition_occurred, components

    def _update_threshold(self, current_time: float):
        """
        Update dynamic threshold based on context.

        Threshold increases when:
        - Metabolic reserves are low
        - Allostatic load is high
        - Recent ignitions are frequent

        Threshold decreases when:
        - Signal is survival-relevant (would need context info)
        - Resources are plentiful
        """
        # Base threshold
        theta = self.baseline_threshold

        # Metabolic modulation
        # Low reserves -> higher threshold (conserve energy)
        metabolic_factor = 1.0 + (1.0 - self.metabolic_reserves) * 0.5
        theta *= metabolic_factor

        # Allostatic load modulation
        # High load -> higher threshold (prevent overload)
        load_factor = 1.0 + self.allostatic_load * 0.3
        theta *= load_factor

        # Recent ignition frequency
        # Frequent ignitions -> higher threshold (habituation)
        recent_count = len([
            ign for ign in self.recent_ignitions
            if (current_time - ign['time']) < 1000.0  # Last second
        ])

        if recent_count > 3:
            frequency_factor = 1.0 + (recent_count - 3) * 0.1
            theta *= frequency_factor

        # Clamp to valid range
        theta = np.clip(theta, self.threshold_range[0], self.threshold_range[1])

        self.current_threshold = theta

    def _sigmoid(self, x: float) -> float:
        """Sigmoid function for smooth probability."""
        return 1.0 / (1.0 + np.exp(-x))

    def update_metabolic_state(self, reserves: float, allostatic_load: float):
        """
        Update metabolic state variables.

        Args:
            reserves: Metabolic reserves (0-1)
            allostatic_load: Allostatic load (0-1)
        """
        self.metabolic_reserves = np.clip(reserves, 0.0, 1.0)
        self.allostatic_load = np.clip(allostatic_load, 0.0, 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical summary of ignition dynamics."""
        if len(self.signal_history) == 0:
            return {
                'mean_signal': 0.0,
                'mean_threshold': self.baseline_threshold,
                'ignition_rate': 0.0,
                'recent_ignitions': 0
            }

        return {
            'mean_signal': float(np.mean(self.signal_history)),
            'std_signal': float(np.std(self.signal_history)),
            'mean_threshold': float(np.mean(self.threshold_history)),
            'std_threshold': float(np.std(self.threshold_history)),
            'ignition_rate': len(self.recent_ignitions) / max(len(self.signal_history), 1),
            'recent_ignitions': len(self.recent_ignitions),
            'current_probability': float(self.ignition_probability)
        }

    def reset(self):
        """Reset ignition state."""
        self.current_threshold = self.baseline_threshold
        self.current_signal = 0.0
        self.ignition_probability = 0.0
        self.extero_signal = 0.0
        self.intero_signal = 0.0
        self.recent_ignitions.clear()
        self.last_ignition_time = -np.inf
        self.metabolic_reserves = 1.0
        self.allostatic_load = 0.0
        self.signal_history.clear()
        self.threshold_history.clear()
