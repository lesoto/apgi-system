"""
Hierarchical Predictive Processing

Implements predictive coding with separate exteroceptive and interoceptive
prediction error channels.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from collections import deque

from apgi_system.validation import InputValidator
from apgi_system.types import FloatArray, ConfigDict


class PredictionErrorChannel:
    """
    Single prediction error channel with temporal accumulation.

    Maintains a sliding window of prediction errors for temporal integration,
    enabling the system to accumulate evidence over time. This is crucial for
    detecting sustained deviations from predictions that may trigger conscious
    access (ignition events).

    Attributes
    ----------
    name : str
        Channel identifier (e.g., 'exteroceptive', 'interoceptive')
    dimension : int
        Dimensionality of prediction error vectors
    window_size : int
        Number of time steps in sliding window
    error_buffer : deque
        Circular buffer storing recent prediction errors
    current_error : np.ndarray
        Most recent prediction error
    accumulated_error : float
        Sum of squared errors over window
    precision : float
        Current precision weight

    Notes
    -----
    The sliding window enables temporal integration:
    - Short windows (~50ms): Sensitive to transient changes
    - Long windows (~200ms): Sensitive to sustained deviations
    
    Accumulated error provides a scalar measure of prediction failure
    over the integration window.

    Examples
    --------
    >>> channel = PredictionErrorChannel('extero', dimension=256, window_size_ms=100)
    >>> obs = np.random.randn(256)
    >>> pred = np.random.randn(256)
    >>> error = channel.update(obs, pred, precision=1.5)
    >>> signal = channel.get_accumulated_signal()
    """

    def __init__(
        self,
        name: str,
        dimension: int,
        window_size_ms: float = 100.0,
        timestep_ms: float = 1.0
    ) -> None:
        """
        Initialize prediction error channel.

        Parameters
        ----------
        name : str
            Channel name (e.g., 'exteroceptive', 'interoceptive')
        dimension : int
            Dimensionality of prediction error vectors
        window_size_ms : float, default=100.0
            Sliding window duration in milliseconds
        timestep_ms : float, default=1.0
            Time step duration in milliseconds

        Examples
        --------
        >>> channel = PredictionErrorChannel(
        ...     name='exteroceptive',
        ...     dimension=256,
        ...     window_size_ms=100.0,
        ...     timestep_ms=1.0
        ... )
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
        observation: FloatArray,
        prediction: FloatArray,
        precision: float = 1.0
    ) -> FloatArray:
        """
        Update prediction error with new observation.

        Computes prediction error, adds it to the sliding window buffer,
        and updates accumulated error statistics.

        Parameters
        ----------
        observation : np.ndarray
            Observed signal vector
        prediction : np.ndarray
            Predicted signal vector
        precision : float, default=1.0
            Precision weight (inverse variance)

        Returns
        -------
        current_error : np.ndarray
            Computed prediction error (observation - prediction)

        Notes
        -----
        Prediction error: ε = o - μ̂
        
        The error is added to a circular buffer, automatically discarding
        the oldest error when the buffer is full.

        Examples
        --------
        >>> channel = PredictionErrorChannel('extero', 256)
        >>> obs = np.random.randn(256)
        >>> pred = np.zeros(256)
        >>> error = channel.update(obs, pred, precision=1.5)
        >>> print(f"Error magnitude: {np.linalg.norm(error):.3f}")
        """
        self.current_error = observation - prediction
        self.precision = precision

        # Add to sliding window
        self.error_buffer.append(self.current_error.copy())

        # Update accumulated error
        self._update_accumulated_error()

        return self.current_error

    def _update_accumulated_error(self) -> None:
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

        Computes the precision-weighted magnitude of accumulated prediction
        errors, providing a scalar measure of prediction failure.

        Returns
        -------
        signal : float
            Precision-weighted signal: S = Π * √(Σ ε²)

        Notes
        -----
        This signal is used for ignition threshold computation. High signal
        indicates sustained prediction errors that may warrant conscious access.
        """
        return self.precision * np.sqrt(self.accumulated_error)

    def get_statistics(self) -> Dict[str, float]:
        """
        Get statistical summary of prediction errors.

        Returns
        -------
        stats : Dict[str, float]
            Dictionary containing:
            - 'mean_error': Mean absolute error
            - 'std_error': Standard deviation of errors
            - 'max_error': Maximum absolute error
            - 'accumulated': Sum of squared errors
            - 'current_magnitude': L2 norm of current error

        Notes
        -----
        Statistics are computed over the sliding window, providing
        a temporal summary of prediction performance.
        """
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

    def reset(self) -> None:
        """
        Reset channel to initial state.

        Clears error buffer and resets all accumulated statistics.
        """
        self.error_buffer.clear()
        self.current_error = np.zeros(self.dimension)
        self.accumulated_error = 0.0


class HierarchicalPredictor:
    """
    Hierarchical predictive processing with multiple levels and timescales.

    Implements a multi-level predictive coding architecture where each level:
    - Receives input from the level below
    - Generates predictions for the level below
    - Computes prediction errors
    - Operates at a characteristic timescale (faster at lower levels)

    The predictor maintains separate channels for exteroceptive (external sensory)
    and interoceptive (internal body state) prediction errors, enabling the system
    to process both external and internal information streams.

    Attributes
    ----------
    num_levels : int
        Number of hierarchical levels
    levels : List[Dict]
        Level configurations containing state, predictions, errors, and timescales
    exteroceptive_channel : PredictionErrorChannel
        Channel for external sensory prediction errors
    interoceptive_channel : PredictionErrorChannel
        Channel for internal body state prediction errors
    learning_rates : List[float]
        Learning rates for each level (decreasing with level)
    intero_prediction : np.ndarray
        Current interoceptive prediction (6D body state vector)

    Notes
    -----
    The hierarchical structure implements temporal abstraction:
    - Lower levels update rapidly (1-10ms) for fast sensory processing
    - Higher levels update slowly (100-1000ms) for abstract representations
    
    This multi-timescale architecture enables efficient processing of both
    fast-changing sensory details and slow-changing contextual information.

    References
    ----------
    .. [1] Rao, R. P., & Ballard, D. H. (1999). Predictive coding in the visual cortex:
           a functional interpretation of some extra-classical receptive-field effects.
           Nature neuroscience, 2(1), 79-87.

    Examples
    --------
    >>> config = load_config('config/default.yaml')
    >>> predictor = HierarchicalPredictor(config)
    >>> extero_input = np.random.randn(256)
    >>> intero_input = np.random.randn(6)
    >>> results = predictor.predict(extero_input, intero_input, dt_ms=1.0)
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize hierarchical predictor.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing:
            - 'hierarchy': Hierarchical structure with num_levels and level_configs
            - 'predictive_processing': Prediction parameters
            - 'system': System parameters including timestep_ms

        Raises
        ------
        KeyError
            If required configuration keys are missing
        ValueError
            If level configurations are invalid

        Examples
        --------
        >>> config = {
        ...     'hierarchy': {
        ...         'num_levels': 4,
        ...         'level_configs': [
        ...             {'name': 'sensory', 'nodes': 256, 'timescale_ms': 1},
        ...             {'name': 'perceptual', 'nodes': 128, 'timescale_ms': 10},
        ...             {'name': 'conceptual', 'nodes': 64, 'timescale_ms': 100},
        ...             {'name': 'abstract', 'nodes': 32, 'timescale_ms': 500}
        ...         ]
        ...     },
        ...     'system': {'timestep_ms': 1.0}
        ... }
        >>> predictor = HierarchicalPredictor(config)
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

        # Interoceptive dimension is 6 (body state vector size)
        # heart_rate, respiration, temperature, glucose, cortisol, blood_pressure
        self.interoceptive_channel = PredictionErrorChannel(
            name='interoceptive',
            dimension=6,  # Body state vector size
            window_size_ms=window_size,
            timestep_ms=timestep_ms
        )

        # Learning rates per level
        self.learning_rates = [0.01 / (i + 1) for i in range(self.num_levels)]

        # Interoceptive prediction (separate from hierarchical levels)
        self.intero_prediction = np.zeros(6)

    def predict(
        self,
        extero_input: Optional[FloatArray] = None,
        intero_input: Optional[FloatArray] = None,
        dt_ms: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate predictions and compute prediction errors.

        Processes both exteroceptive and interoceptive input streams,
        computing prediction errors and updating hierarchical representations.
        Each level generates predictions for the level below and computes
        errors based on bottom-up input.

        Parameters
        ----------
        extero_input : np.ndarray, optional
            Exteroceptive (external sensory) input vector
        intero_input : np.ndarray, optional
            Interoceptive (body state) input vector of shape (6,)
            Expected order: [heart_rate, respiration, temperature, 
                           glucose, cortisol, blood_pressure]
        dt_ms : float, default=1.0
            Time step in milliseconds

        Returns
        -------
        results : Dict[str, Any]
            Dictionary containing:
            - 'exteroceptive': Dict with 'error' and 'stats'
            - 'interoceptive': Dict with 'error' and 'stats'
            - 'hierarchical_errors': List of errors at each level

        Raises
        ------
        TypeError
            If inputs are not numpy arrays
        ValueError
            If input shapes don't match expected dimensions, contain NaN/Inf,
            or dt_ms is not positive

        Notes
        -----
        Prediction errors are computed as:
        ε = observation - prediction
        
        These errors drive learning and belief updating throughout the hierarchy.

        Examples
        --------
        >>> predictor = HierarchicalPredictor(config)
        >>> extero = np.random.randn(256)
        >>> intero = np.array([70, 15, 37.0, 5.0, 10, 120])  # Body state
        >>> results = predictor.predict(extero, intero, dt_ms=1.0)
        >>> print(f"Extero error: {results['exteroceptive']['stats']['mean_error']:.3f}")
        """
        # Validate inputs
        if extero_input is not None:
            InputValidator.validate_array(
                extero_input,
                "extero_input",
                expected_shape=(self.levels[0]['nodes'],)
            )
        
        if intero_input is not None:
            InputValidator.validate_array(
                intero_input,
                "intero_input",
                expected_shape=(6,)
            )
        
        InputValidator.validate_scalar(
            dt_ms,
            "dt_ms",
            positive=True,
            value_range=(0.001, 1000.0)
        )
        
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
                prediction=self.intero_prediction,  # 6-dimensional body prediction
                precision=self.levels[0]['precision']
            )
            results['interoceptive'] = {
                'error': intero_error,
                'stats': self.interoceptive_channel.get_statistics()
            }

            # Update interoceptive prediction (simple running average)
            self.intero_prediction = 0.9 * self.intero_prediction + 0.1 * intero_input

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

    def _update_hierarchy(self, dt_ms: float) -> None:
        """
        Update hierarchical levels with different timescales.

        Each level updates at its characteristic timescale, with lower levels
        updating more frequently than higher levels. This implements temporal
        abstraction in the hierarchy.

        Parameters
        ----------
        dt_ms : float
            Time step in milliseconds

        Notes
        -----
        Update occurs when: update_counter >= update_interval
        
        This ensures each level operates at its natural timescale:
        - Sensory level: ~1ms (fast sensory processing)
        - Perceptual level: ~10ms (perceptual grouping)
        - Conceptual level: ~100ms (object recognition)
        - Abstract level: ~500ms (contextual understanding)
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

    def _map_down(self, state: FloatArray, target_dim: int) -> FloatArray:
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

    def _map_up(self, state: FloatArray, target_dim: int) -> FloatArray:
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
        """
        Get current prediction errors across all channels.

        Returns
        -------
        errors : Dict[str, float]
            Dictionary containing:
            - 'exteroceptive_signal': Precision-weighted extero signal
            - 'interoceptive_signal': Precision-weighted intero signal
            - 'exteroceptive_stats': Statistical summary of extero errors
            - 'interoceptive_stats': Statistical summary of intero errors

        Notes
        -----
        The precision-weighted signal is computed as:
        S = Π * √(Σ ε²)
        
        where Π is precision and ε are prediction errors over a sliding window.
        """
        return {
            'exteroceptive_signal': self.exteroceptive_channel.get_accumulated_signal(),
            'interoceptive_signal': self.interoceptive_channel.get_accumulated_signal(),
            'exteroceptive_stats': self.exteroceptive_channel.get_statistics(),
            'interoceptive_stats': self.interoceptive_channel.get_statistics()
        }

    def reset(self) -> None:
        """
        Reset all hierarchical levels and prediction error channels.

        Clears all state, predictions, errors, and temporal buffers.
        Useful for starting new simulation runs or experimental trials.
        """
        for level in self.levels:
            level['state'] = np.zeros(level['nodes'])
            level['prediction'] = np.zeros(level['nodes'])
            level['error'] = np.zeros(level['nodes'])
            level['update_counter'] = 0

        self.exteroceptive_channel.reset()
        self.interoceptive_channel.reset()
        self.intero_prediction = np.zeros(6)
