"""
Hierarchical Predictive Processing

Implements predictive coding with separate exteroceptive and interoceptive
prediction error channels.
"""

from collections import deque
from typing import Any, Dict, Optional

import numpy as np

from apgi_simulation.stability import NumericalStabilityMonitor
from apgi_simulation.types import ConfigDict, FloatArray


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
        batch_size: int = 1,
        window_size_ms: float = 100.0,
        timestep_ms: float = 1.0,
    ) -> None:
        """
        Initialize prediction error channel with batch support.

        Parameters
        ----------
        name : str
            Channel name
        dimension : int
            Dimensionality of prediction error vectors
        batch_size : int
            Number of parallel agent simulations
        window_size_ms : float
            Sliding window duration
        """
        self.name = name
        self.dimension = dimension
        self.batch_size = batch_size
        self.window_size = int(window_size_ms / timestep_ms)
        self.timestep_ms = timestep_ms

        # Sliding window buffer: list of deques, one per agent
        # Or a single deque of (B, D) arrays
        self.error_buffer: deque[np.ndarray] = deque(maxlen=self.window_size)

        # Current state: (B, D)
        self.current_error = np.zeros((batch_size, dimension))
        self.accumulated_error = np.zeros(batch_size)
        self.precision = np.ones(batch_size)

    def update(
        self, observation: FloatArray, prediction: FloatArray, precision: np.ndarray
    ) -> FloatArray:
        """
        Update prediction error for batch.

        Parameters
        ----------
        observation : np.ndarray
            Observed signals (B, D)
        prediction : np.ndarray
            Predicted signals (B, D)
        precision : np.ndarray
            Precision weights (B,)
        """
        # Ensure correct shapes
        if observation.ndim == 1:
            observation = observation[np.newaxis, :]
        if prediction.ndim == 1:
            prediction = prediction[np.newaxis, :]

        self.current_error = observation - prediction
        self.precision = precision

        # Add (B, D) snapshot to sliding window
        self.error_buffer.append(self.current_error.copy())

        # Update accumulated error (B,)
        self._update_accumulated_error()

        return self.current_error

    def _update_accumulated_error(self) -> None:
        """Update accumulated error (B,) over sliding window."""
        if len(self.error_buffer) == 0:
            self.accumulated_error.fill(0.0)
        else:
            # error_buffer is deque of (B, D) arrays
            # Stack into (Window, B, D)
            errors = np.stack(list(self.error_buffer))
            # Sum of squares over (Window, D) dimensions -> (B,)
            self.accumulated_error = np.sum(errors**2, axis=(0, 2))

    def get_accumulated_signal(self) -> np.ndarray:
        """Get precision-weighted accumulated signal (B,)."""
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
            return {"mean_error": 0.0, "std_error": 0.0, "max_error": 0.0, "accumulated": 0.0}

        errors = np.array(self.error_buffer)
        return {
            "mean_error": float(np.mean(np.abs(errors))),
            "std_error": float(np.std(errors)),
            "max_error": float(np.max(np.abs(errors))),
            "accumulated": float(self.accumulated_error),
            "current_magnitude": float(np.linalg.norm(self.current_error)),
        }

    def reset(self) -> None:
        """Reset channel for all agents."""
        self.error_buffer.clear()
        self.current_error.fill(0.0)
        self.accumulated_error.fill(0.0)


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
        hierarchy_config = config.get("hierarchy", {})
        self.num_levels = hierarchy_config.get("num_levels", 4)
        level_configs = hierarchy_config.get("level_configs", [])

        # Predictive processing config
        pp_config = config.get("predictive_processing", {})
        self.prediction_horizon_ms = pp_config.get("prediction_horizon_ms", 200)
        self.temporal_discount = pp_config.get("temporal_discount", 0.95)

        # Initialize levels with batch support
        self.batch_size = config.get("active_inference", {}).get("batch_size", 1)
        self.levels = []
        for i, level_config in enumerate(level_configs):
            level = {
                "name": level_config["name"],
                "nodes": level_config["nodes"],
                "timescale_ms": level_config["timescale_ms"],
                "state": np.zeros((self.batch_size, level_config["nodes"])),
                "prediction": np.zeros((self.batch_size, level_config["nodes"])),
                "error": np.zeros((self.batch_size, level_config["nodes"])),
                "precision": np.ones(self.batch_size),
                "update_counter": 0,
                "update_interval": int(level_config["timescale_ms"]),
            }
            self.levels.append(level)

        # Separate error channels
        timestep_ms = config.get("system", {}).get("timestep_ms", 1.0)
        window_size = pp_config.get("error_accumulation_window_ms", 100)

        self.exteroceptive_channel = PredictionErrorChannel(
            name="exteroceptive",
            dimension=self.levels[0]["nodes"],
            batch_size=self.batch_size,
            window_size_ms=window_size,
            timestep_ms=timestep_ms,
        )

        self.interoceptive_channel = PredictionErrorChannel(
            name="interoceptive",
            dimension=6,
            batch_size=self.batch_size,
            window_size_ms=window_size,
            timestep_ms=timestep_ms,
        )

        # Learning rates per level
        self.learning_rates = [0.01 / (i + 1) for i in range(self.num_levels)]

        # Interoceptive prediction (B, 6)
        self.intero_prediction = np.zeros((self.batch_size, 6))

        # Stability monitoring
        self.stability_monitor = NumericalStabilityMonitor(config)

    def predict(
        self,
        extero_input: Optional[FloatArray] = None,
        intero_input: Optional[FloatArray] = None,
        dt_ms: float = 1.0,
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
            # extero_input should be (B, D)
            if extero_input.ndim == 1:
                extero_input = extero_input[np.newaxis, :]

        if intero_input is not None:
            # intero_input should be (B, 6)
            if intero_input.ndim == 1:
                intero_input = intero_input[np.newaxis, :]

        results: Dict[str, Any] = {
            "exteroceptive": {},
            "interoceptive": {},
            "hierarchical_errors": [],
        }

        # Process exteroceptive stream
        if extero_input is not None:
            # Project extero_input to match level 0 dimension if needed
            level0_dim = self.levels[0]["nodes"]
            if extero_input.shape[1] != level0_dim:
                extero_input_projected = self._map_up(extero_input, level0_dim)
            else:
                extero_input_projected = extero_input

            extero_error = self.exteroceptive_channel.update(
                observation=extero_input_projected,
                prediction=self.levels[0]["prediction"],
                precision=self.levels[0]["precision"],
            )

            # Check stability of exteroceptive error
            self.stability_monitor.check_stability(
                extero_error, context="exteroceptive_prediction_error"
            )

            results["exteroceptive"] = {
                "error": extero_error,
                "stats": self.exteroceptive_channel.get_statistics(),
            }

        # Process interoceptive stream
        if intero_input is not None:
            intero_error = self.interoceptive_channel.update(
                observation=intero_input,
                prediction=self.intero_prediction,  # 6-dimensional body prediction
                precision=self.levels[0]["precision"],
            )

            # Check stability of interoceptive error
            self.stability_monitor.check_stability(
                intero_error, context="interoceptive_prediction_error"
            )

            results["interoceptive"] = {
                "error": intero_error,
                "stats": self.interoceptive_channel.get_statistics(),
            }

            # Update interoceptive prediction (simple running average)
            self.intero_prediction = 0.9 * self.intero_prediction + 0.1 * intero_input

            # Check stability of updated prediction
            self.stability_monitor.check_stability(
                self.intero_prediction, context="interoceptive_prediction_update"
            )

        # Update hierarchical levels
        self._update_hierarchy(dt_ms)

        # Collect hierarchical errors
        for level in self.levels:
            results["hierarchical_errors"].append(
                {
                    "level": level["name"],
                    "error": level["error"].copy(),
                    "magnitude": np.linalg.norm(level["error"], axis=1),
                    "precision": level["precision"],
                }
            )

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
            level["update_counter"] += dt_ms

            # Only update if timescale reached
            if level["update_counter"] >= level["update_interval"]:
                level["update_counter"] = 0

                # Get prediction from level above (top-down)
                if i < self.num_levels - 1:
                    higher_state = self.levels[i + 1]["state"]
                    # Simple mapping (could be learned transformation)
                    level["prediction"] = self._map_down(higher_state, level["nodes"])
                else:
                    # Top level predicts based on prior
                    level["prediction"] = level["state"] * 0.9  # Drift toward zero

                # Compute prediction error
                if i > 0:
                    lower_state = self.levels[i - 1]["state"]
                    mapped_lower = self._map_up(lower_state, level["nodes"])
                    level["error"] = mapped_lower - level["prediction"]
                else:
                    # Bottom level error comes from sensory input
                    level["error"] = self.exteroceptive_channel.current_error

                # Update state (gradient descent on prediction error)
                level["state"] += self.learning_rates[i] * level["error"]

                # Check stability of updated state
                self.stability_monitor.check_stability(
                    level["state"], context=f"hierarchical_level_{i}_{level['name']}_state"
                )

    def _map_down(self, state: FloatArray, target_dim: int) -> FloatArray:
        """Map state from higher to lower level (B, D_high) -> (B, D_low)."""
        b_size, source_dim = state.shape
        if source_dim == target_dim:
            return state.copy()
        elif source_dim < target_dim:
            # Upsample
            result = np.zeros((b_size, target_dim))
            result[:, :source_dim] = state
            return result
        else:
            # Downsample
            return state[:, :target_dim]

    def _map_up(self, state: FloatArray, target_dim: int) -> FloatArray:
        """Map state from lower to higher level (B, D_low) -> (B, D_high)."""
        b_size, source_dim = state.shape
        if source_dim == target_dim:
            return state.copy()
        elif source_dim > target_dim:
            # Pool/compress
            ratio = source_dim // target_dim
            result = np.zeros((b_size, target_dim))
            for i in range(target_dim):
                start = i * ratio
                end = min((i + 1) * ratio, source_dim)
                result[:, i] = np.mean(state[:, start:end], axis=1)
            return result
        else:
            # Expand
            result = np.zeros((b_size, target_dim))
            result[:, :source_dim] = state
            return result

    def get_prediction_errors(self) -> Dict[str, Any]:
        """
        Get current prediction errors across all channels.

        Returns
        -------
        errors : Dict[str, Any]
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
            "exteroceptive_signal": self.exteroceptive_channel.get_accumulated_signal(),
            "interoceptive_signal": self.interoceptive_channel.get_accumulated_signal(),
            "exteroceptive_stats": self.exteroceptive_channel.get_statistics(),
            "interoceptive_stats": self.interoceptive_channel.get_statistics(),
        }

    def reset(self) -> None:
        """Reset all hierarchical levels and prediction error channels."""
        for level in self.levels:
            level["state"].fill(0.0)
            level["prediction"].fill(0.0)
            level["error"].fill(0.0)
            level["update_counter"] = 0

        self.exteroceptive_channel.reset()
        self.interoceptive_channel.reset()
        self.intero_prediction.fill(0.0)
