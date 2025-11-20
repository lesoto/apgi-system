"""
Hierarchical Predictive Processing

Implements predictive coding with separate exteroceptive and interoceptive
prediction error channels.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from collections import deque


class PredictionErrorChannel:
    """
    Single prediction error channel with temporal accumulation.

    Maintains sliding window of prediction errors for temporal integration.
    """

    def __init__(
        self,
        name: str,
        dimension: int,
        window_size_ms: float = 100.0,
        timestep_ms: float = 1.0
    ):
        """
        Initialize prediction error channel.

        Args:
            name: Channel name (e.g., 'exteroceptive', 'interoceptive')
            dimension: Dimensionality of prediction errors
            window_size_ms: Sliding window size in milliseconds
            timestep_ms: Timestep in milliseconds
        """
        self.name = name
        self.dimension = dimension
        self.window_size = int(window_size_ms / timestep_ms)
        self.timestep_ms = timestep_ms

        # Sliding window buffer
        self.error_buffer = deque(maxlen=self.window_size)

        # Current state
        self.current_error = np.zeros(dimension)
        self.accumulated_error = 0.0
        self.precision = 1.0

    def update(
        self,
        observation: np.ndarray,
        prediction: np.ndarray,
        precision: float = 1.0
    ) -> np.ndarray:
        """
        Update prediction error.

        Args:
            observation: Observed signal
            prediction: Predicted signal
            precision: Precision weight

        Returns:
            Current prediction error
        """
        self.current_error = observation - prediction
        self.precision = precision

        # Add to sliding window
        self.error_buffer.append(self.current_error.copy())

        # Update accumulated error
        self._update_accumulated_error()

        return self.current_error

    def _update_accumulated_error(self):
        """Update accumulated error over sliding window."""
        if len(self.error_buffer) == 0:
            self.accumulated_error = 0.0
        else:
            # Sum of squared errors over window
            errors = np.array(self.error_buffer)
            self.accumulated_error = np.sum(errors ** 2)

    def get_accumulated_signal(self) -> float:
        """
        Get precision-weighted accumulated signal.

        S = Π * |ε|
        """
        return self.precision * np.sqrt(self.accumulated_error)

    def get_statistics(self) -> Dict[str, float]:
        """Get statistical summary of errors."""
        if len(self.error_buffer) == 0:
            return {
                'mean_error': 0.0,
                'std_error': 0.0,
                'max_error': 0.0,
                'accumulated': 0.0
            }

        errors = np.array(self.error_buffer)
        return {
            'mean_error': float(np.mean(np.abs(errors))),
            'std_error': float(np.std(errors)),
            'max_error': float(np.max(np.abs(errors))),
            'accumulated': float(self.accumulated_error),
            'current_magnitude': float(np.linalg.norm(self.current_error))
        }

    def reset(self):
        """Reset channel state."""
        self.error_buffer.clear()
        self.current_error = np.zeros(self.dimension)
        self.accumulated_error = 0.0


class HierarchicalPredictor:
    """
    Hierarchical predictive processing with multiple levels and timescales.

    Each level:
    - Receives input from level below
    - Generates predictions for level below
    - Computes prediction errors
    - Operates at different timescale
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize hierarchical predictor.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Extract hierarchy configuration
        hierarchy_config = config.get('hierarchy', {})
        self.num_levels = hierarchy_config.get('num_levels', 4)
        level_configs = hierarchy_config.get('level_configs', [])

        # Predictive processing config
        pp_config = config.get('predictive_processing', {})
        self.prediction_horizon_ms = pp_config.get('prediction_horizon_ms', 200)
        self.temporal_discount = pp_config.get('temporal_discount', 0.95)

        # Initialize levels
        self.levels = []
        for i, level_config in enumerate(level_configs):
            level = {
                'name': level_config['name'],
                'nodes': level_config['nodes'],
                'timescale_ms': level_config['timescale_ms'],
                'state': np.zeros(level_config['nodes']),
                'prediction': np.zeros(level_config['nodes']),
                'error': np.zeros(level_config['nodes']),
                'precision': 1.0,
                'update_counter': 0,
                'update_interval': int(level_config['timescale_ms'])
            }
            self.levels.append(level)

        # Separate error channels
        timestep_ms = config.get('system', {}).get('timestep_ms', 1.0)
        window_size = pp_config.get('error_accumulation_window_ms', 100)

        self.exteroceptive_channel = PredictionErrorChannel(
            name='exteroceptive',
            dimension=self.levels[0]['nodes'],
            window_size_ms=window_size,
            timestep_ms=timestep_ms
        )

        self.interoceptive_channel = PredictionErrorChannel(
            name='interoceptive',
            dimension=self.levels[0]['nodes'],  # Same for now
            window_size_ms=window_size,
            timestep_ms=timestep_ms
        )

        # Learning rates per level
        self.learning_rates = [0.01 / (i + 1) for i in range(self.num_levels)]

    def predict(
        self,
        extero_input: Optional[np.ndarray] = None,
        intero_input: Optional[np.ndarray] = None,
        dt_ms: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate predictions and compute errors.

        Args:
            extero_input: Exteroceptive input (sensory)
            intero_input: Interoceptive input (body state)
            dt_ms: Time step in milliseconds

        Returns:
            Dictionary with predictions and errors
        """
        results = {
            'exteroceptive': {},
            'interoceptive': {},
            'hierarchical_errors': []
        }

        # Process exteroceptive stream
        if extero_input is not None:
            extero_error = self.exteroceptive_channel.update(
                observation=extero_input,
                prediction=self.levels[0]['prediction'],
                precision=self.levels[0]['precision']
            )
            results['exteroceptive'] = {
                'error': extero_error,
                'stats': self.exteroceptive_channel.get_statistics()
            }

        # Process interoceptive stream
        if intero_input is not None:
            intero_error = self.interoceptive_channel.update(
                observation=intero_input,
                prediction=self.levels[0]['prediction'],  # Simplified
                precision=self.levels[0]['precision']
            )
            results['interoceptive'] = {
                'error': intero_error,
                'stats': self.interoceptive_channel.get_statistics()
            }

        # Update hierarchical levels
        self._update_hierarchy(dt_ms)

        # Collect hierarchical errors
        for level in self.levels:
            results['hierarchical_errors'].append({
                'level': level['name'],
                'error': level['error'].copy(),
                'magnitude': float(np.linalg.norm(level['error'])),
                'precision': level['precision']
            })

        return results

    def _update_hierarchy(self, dt_ms: float):
        """
        Update hierarchical levels with different timescales.

        Lower levels update faster than higher levels.
        """
        for i, level in enumerate(self.levels):
            level['update_counter'] += dt_ms

            # Only update if timescale reached
            if level['update_counter'] >= level['update_interval']:
                level['update_counter'] = 0

                # Get prediction from level above (top-down)
                if i < self.num_levels - 1:
                    higher_state = self.levels[i + 1]['state']
                    # Simple mapping (could be learned transformation)
                    level['prediction'] = self._map_down(higher_state, level['nodes'])
                else:
                    # Top level predicts based on prior
                    level['prediction'] = level['state'] * 0.9  # Drift toward zero

                # Compute prediction error
                if i > 0:
                    lower_state = self.levels[i - 1]['state']
                    mapped_lower = self._map_up(lower_state, level['nodes'])
                    level['error'] = mapped_lower - level['prediction']
                else:
                    # Bottom level error comes from sensory input
                    level['error'] = self.exteroceptive_channel.current_error

                # Update state (gradient descent on prediction error)
                level['state'] += self.learning_rates[i] * level['error']

    def _map_down(self, state: np.ndarray, target_dim: int) -> np.ndarray:
        """Map state from higher to lower level."""
        if len(state) == target_dim:
            return state.copy()
        elif len(state) < target_dim:
            # Upsample
            result = np.zeros(target_dim)
            result[:len(state)] = state
            return result
        else:
            # Downsample
            return state[:target_dim]

    def _map_up(self, state: np.ndarray, target_dim: int) -> np.ndarray:
        """Map state from lower to higher level."""
        if len(state) == target_dim:
            return state.copy()
        elif len(state) > target_dim:
            # Pool/compress
            ratio = len(state) // target_dim
            result = np.zeros(target_dim)
            for i in range(target_dim):
                start = i * ratio
                end = min((i + 1) * ratio, len(state))
                result[i] = np.mean(state[start:end])
            return result
        else:
            # Expand
            result = np.zeros(target_dim)
            result[:len(state)] = state
            return result

    def get_prediction_errors(self) -> Dict[str, float]:
        """Get current prediction errors across channels."""
        return {
            'exteroceptive_signal': self.exteroceptive_channel.get_accumulated_signal(),
            'interoceptive_signal': self.interoceptive_channel.get_accumulated_signal(),
            'exteroceptive_stats': self.exteroceptive_channel.get_statistics(),
            'interoceptive_stats': self.interoceptive_channel.get_statistics()
        }

    def reset(self):
        """Reset all levels and channels."""
        for level in self.levels:
            level['state'] = np.zeros(level['nodes'])
            level['prediction'] = np.zeros(level['nodes'])
            level['error'] = np.zeros(level['nodes'])
            level['update_counter'] = 0

        self.exteroceptive_channel.reset()
        self.interoceptive_channel.reset()
