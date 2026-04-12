"""
Ignition Threshold Computation

Implements dynamic threshold for global ignition based on:
- Exteroceptive precision-weighted prediction errors
- Interoceptive precision-weighted errors with somatic markers
- Metabolic state and allostatic load
- Recent ignition history
"""

from collections import deque
from typing import Any, Dict, Tuple

import numpy as np

from ..types import ConfigDict, FloatArray
from ..validation import InputValidator


class IgnitionThreshold:
    """
    Computes ignition signal and dynamic threshold for conscious access.

    The IgnitionThreshold class implements the core mechanism for determining when
    information gains conscious access through global ignition. It combines precision-
    weighted prediction errors from exteroceptive and interoceptive channels, modulated
    by somatic markers and metabolic state, to compute an ignition signal that is
    compared against a dynamic threshold.

    Ignition occurs stochastically when:
        S_t > θ_t

    Where:
        S_t = S_extero + S_intero
        S_extero = Π_e * |ε_e|  (exteroceptive component)
        S_intero = Π_i * M * |ε_i|  (interoceptive component with somatic markers)

        Π_e, Π_i = precision weights (attention/confidence)
        ε_e, ε_i = prediction errors
        M = somatic marker gain (0.5-2.0)
        θ_t = dynamic threshold (context-dependent, 1.0-5.0)

    The threshold dynamically adjusts based on:
    - Metabolic reserves (low reserves → higher threshold to conserve energy)
    - Allostatic load (high stress → higher threshold to prevent overload)
    - Recent ignition frequency (habituation → higher threshold)

    Attributes
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing ignition parameters
    baseline_threshold : float
        Base threshold value (default: 2.0)
    threshold_range : List[float]
        Valid range for threshold [min, max] (default: [1.0, 5.0])
    sigmoid_alpha : float
        Steepness of sigmoid probability function (default: 5.0)
    current_threshold : float
        Current dynamic threshold value
    current_signal : float
        Current total ignition signal
    ignition_probability : float
        Current probability of ignition (0-1)
    extero_signal : float
        Exteroceptive component of signal
    intero_signal : float
        Interoceptive component of signal
    refractory_period_ms : float
        Minimum time between ignitions in milliseconds (default: 200)
    recent_ignitions : deque
        History of recent ignition events
    last_ignition_time : float
        Timestamp of most recent ignition
    metabolic_reserves : float
        Current metabolic reserves (0-1, starts at 1.0)
    allostatic_load : float
        Current allostatic load (0-1, starts at 0.0)
    signal_history : deque
        Historical record of signal values
    threshold_history : deque
        Historical record of threshold values

    Examples
    --------
    >>> config = {'ignition': {'baseline_threshold': 2.0, 'refractory_period_ms': 200}}
    >>> threshold = IgnitionThreshold(config)
    >>> extero_error = np.array([1.0, 2.0, 1.5])
    >>> intero_error = np.array([0.5, 0.3])
    >>> ignited, info = threshold.compute_ignition_signal(
    ...     extero_error=extero_error,
    ...     extero_precision=1.5,
    ...     intero_error=intero_error,
    ...     intero_precision=1.0,
    ...     somatic_marker_gain=1.2,
    ...     current_time=100.0
    ... )
    >>> print(f"Ignition occurred: {ignited}")
    >>> print(f"Signal: {info['total_signal']:.2f}, Threshold: {info['threshold']:.2f}")
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize ignition threshold system.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary with the following structure:
            - 'ignition': Dict containing:
                - 'baseline_threshold': float, optional (default: 2.0)
                    Base threshold value before dynamic modulation
                - 'threshold_range': List[float], optional (default: [1.0, 5.0])
                    Valid range [min, max] for threshold values
                - 'sigmoid_alpha': float, optional (default: 5.0)
                    Steepness parameter for sigmoid probability function
                - 'refractory_period_ms': float, optional (default: 200)
                    Minimum time between ignition events in milliseconds

        Notes
        -----
        The system initializes with full metabolic reserves (1.0) and zero
        allostatic load (0.0), representing a well-rested, unstressed state.
        """
        self.config = config
        ignition_config = config.get("ignition", {})

        # Threshold parameters
        self.baseline_threshold = ignition_config.get("baseline_threshold", 2.0)
        self.threshold_range = ignition_config.get("threshold_range", [1.0, 5.0])
        self.sigmoid_alpha = ignition_config.get("sigmoid_alpha", 5.0)

        # Current state
        self.current_threshold = self.baseline_threshold
        self.current_signal = 0.0
        self.ignition_probability = 0.0

        # Components
        self.extero_signal = 0.0
        self.intero_signal = 0.0

        # Recent ignition history
        self.refractory_period_ms = ignition_config.get("refractory_period_ms", 200)
        self.recent_ignitions: deque[Dict[str, float]] = deque(maxlen=100)
        self.last_ignition_time = -np.inf

        # Metabolic tracking
        self.metabolic_reserves = 1.0  # 0-1, starts full
        self.allostatic_load = 0.0  # 0-1, starts at zero

        # Signal history for analysis
        self.signal_history: deque[float] = deque(maxlen=1000)
        self.threshold_history: deque[float] = deque(maxlen=1000)

    def compute_ignition_signal(
        self,
        extero_error: FloatArray,
        extero_precision: float,
        intero_error: FloatArray,
        intero_precision: float,
        somatic_marker_gain: float = 1.0,
        current_time: float = 0.0,
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Compute ignition signal and determine if ignition occurs.

        This method computes the total ignition signal by combining precision-weighted
        prediction errors from exteroceptive and interoceptive channels. The interoceptive
        component is further modulated by somatic markers (learned emotional associations).
        The signal is compared against a dynamic threshold using a sigmoid function to
        determine ignition probability. Ignition occurs stochastically, respecting a
        refractory period to prevent excessive ignition frequency.

        Parameters
        ----------
        extero_error : np.ndarray
            Exteroceptive prediction error vector (external sensory errors).
            Shape: (n_extero_dims,), typically (256,) for visual input.
            Values typically in range [-10, 10].
        extero_precision : float
            Exteroceptive precision weight (confidence/attention).
            Higher values indicate more reliable/attended external signals.
            Typical range: [0.1, 3.0]. Must be positive.
        intero_error : np.ndarray
            Interoceptive prediction error vector (body state errors).
            Shape: (n_intero_dims,), typically (4,) for [heart_rate, cortisol, temp, glucose].
            Values typically in range [-5, 5].
        intero_precision : float
            Interoceptive precision weight (confidence in body signals).
            Higher values indicate more reliable interoceptive information.
            Typical range: [0.1, 2.0]. Must be positive.
        somatic_marker_gain : float, optional
            Gain from somatic markers (learned emotional associations), by default 1.0.
            Range: [0.5, 2.0]
            - < 1.0: Negative associations (aversive contexts)
            - = 1.0: Neutral (no learned association)
            - > 1.0: Positive associations (appetitive contexts)
        current_time : float, optional
            Current simulation time in milliseconds, by default 0.0.
            Used for refractory period enforcement and event logging.

        Returns
        -------
        ignition_occurred : bool
            Whether an ignition event occurred at this timestep.
            True if signal exceeded threshold (outside refractory period) and
            stochastic sampling succeeded.
        components : Dict[str, float]
            Dictionary containing signal components and diagnostics:
            - 'total_signal': Combined ignition signal (S_t)
            - 'extero_signal': Exteroceptive component (Π_e * |ε_e|)
            - 'intero_signal': Interoceptive component (Π_i * M * |ε_i|)
            - 'threshold': Current dynamic threshold (θ_t)
            - 'ignition_probability': Probability of ignition (0-1)
            - 'somatic_marker_gain': Applied somatic marker gain
            - 'ignition_occurred': Boolean (same as first return value)

        Notes
        -----
        The ignition signal is computed as:
            S_extero = Π_e * ||ε_e||
            S_intero = Π_i * M * ||ε_i||
            S_total = S_extero + S_intero

        The dynamic threshold θ_t is modulated by:
        - Metabolic reserves: θ *= (1 + 0.5 * (1 - reserves))
        - Allostatic load: θ *= (1 + 0.3 * load)
        - Recent ignition frequency: θ *= (1 + 0.1 * (count - 3)) if count > 3

        Ignition probability uses a sigmoid:
            P(ignition) = 1 / (1 + exp(-α * (S_t - θ_t)))
        where α is the sigmoid steepness parameter.

        The refractory period prevents ignition for a fixed duration after each
        ignition event, modeling neural recovery time.

        Examples
        --------
        >>> threshold = IgnitionThreshold(config)
        >>> extero_error = np.array([1.0, 2.0, 1.5])
        >>> intero_error = np.array([0.5, 0.3])
        >>> ignited, info = threshold.compute_ignition_signal(
        ...     extero_error=extero_error,
        ...     extero_precision=1.5,
        ...     intero_error=intero_error,
        ...     intero_precision=1.0,
        ...     somatic_marker_gain=1.2,
        ...     current_time=100.0
        ... )
        >>> if ignited:
        ...     print(f"Ignition! Signal: {info['total_signal']:.2f}")
        """
        # Input validation
        InputValidator.validate_array(extero_error, "extero_error")
        InputValidator.validate_scalar(extero_precision, "extero_precision", positive=True)
        InputValidator.validate_array(intero_error, "intero_error")
        InputValidator.validate_scalar(intero_precision, "intero_precision", positive=True)
        InputValidator.validate_scalar(
            somatic_marker_gain, "somatic_marker_gain", value_range=(0.5, 2.0)
        )
        InputValidator.validate_scalar(
            current_time, "current_time", value_range=(0.0, float("inf"))
        )

        # Exteroceptive component
        self.extero_signal = float(extero_precision * np.linalg.norm(extero_error))

        # Interoceptive component with somatic marker modulation
        self.intero_signal = float(
            intero_precision * somatic_marker_gain * np.linalg.norm(intero_error)
        )

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
                self.recent_ignitions.append(
                    {
                        "time": current_time,
                        "signal": self.current_signal,
                        "threshold": self.current_threshold,
                    }
                )

        # Record history
        self.signal_history.append(self.current_signal)
        self.threshold_history.append(self.current_threshold)

        components = {
            "total_signal": float(self.current_signal),
            "extero_signal": float(self.extero_signal),
            "intero_signal": float(self.intero_signal),
            "threshold": float(self.current_threshold),
            "ignition_probability": float(self.ignition_probability),
            "somatic_marker_gain": float(somatic_marker_gain),
            "ignition_occurred": ignition_occurred,
        }

        return ignition_occurred, components

    def _update_threshold(self, current_time: float) -> None:
        """
        Update dynamic threshold based on metabolic and contextual factors.

        The threshold dynamically adjusts to reflect the organism's current state
        and recent history. This implements adaptive gating that conserves energy
        when resources are low and prevents overload during high stress.

        Parameters
        ----------
        current_time : float
            Current simulation time in milliseconds.
            Used to compute recent ignition frequency.

        Notes
        -----
        Threshold modulation factors:

        1. Metabolic reserves (energy conservation):
           - Low reserves → higher threshold (conserve energy)
           - Factor: 1 + 0.5 * (1 - reserves)
           - Range: [1.0, 1.5] as reserves go from 1.0 to 0.0

        2. Allostatic load (stress protection):
           - High load → higher threshold (prevent overload)
           - Factor: 1 + 0.3 * load
           - Range: [1.0, 1.3] as load goes from 0.0 to 1.0

        3. Recent ignition frequency (habituation):
           - Frequent ignitions → higher threshold (adaptation)
           - Counts ignitions in last 1000ms
           - Factor: 1 + 0.1 * (count - 3) if count > 3
           - Implements habituation to repeated stimuli

        The final threshold is clamped to the valid range specified in configuration
        (default: [1.0, 5.0]) to prevent extreme values.
        """
        # Base threshold
        theta = self.baseline_threshold

        # Metabolic modulation
        # Low reserves -> higher threshold (conserve energy)
        m_scalar = self.config.get("ignition", {}).get("metabolic_scaling", 0.5)
        metabolic_factor = 1.0 + (1.0 - self.metabolic_reserves) * m_scalar
        theta *= metabolic_factor

        # Allostatic load modulation
        # High load -> higher threshold (prevent overload)
        l_scalar = self.config.get("ignition", {}).get("load_scaling", 0.3)
        load_factor = 1.0 + self.allostatic_load * l_scalar
        theta *= load_factor

        habituation_window_ms = self.config.get("ignition", {}).get("habituation_window_ms", 1000.0)
        recent_count = len(
            [
                ign
                for ign in self.recent_ignitions
                if (current_time - ign["time"]) < habituation_window_ms
            ]
        )

        habituation_threshold_count = self.config.get("ignition", {}).get(
            "habituation_threshold_count", 3
        )
        if recent_count > habituation_threshold_count:
            habituation_factor = self.config.get("ignition", {}).get("habituation_factor", 0.1)
            frequency_factor = (
                1.0 + (recent_count - habituation_threshold_count) * habituation_factor
            )
            theta *= frequency_factor

        # Clamp to valid range
        theta = np.clip(theta, self.threshold_range[0], self.threshold_range[1])

        self.current_threshold = theta

    def _sigmoid(self, x: float) -> float:
        """
        Sigmoid function for smooth probability computation.

        Parameters
        ----------
        x : float
            Input value (typically signal - threshold difference).

        Returns
        -------
        float
            Sigmoid output in range (0, 1).

        Notes
        -----
        Computes: σ(x) = 1 / (1 + exp(-x))
        """
        return 1.0 / (1.0 + np.exp(-x))

    def update_metabolic_state(self, reserves: float, allostatic_load: float) -> None:
        """
        Update metabolic state variables that modulate ignition threshold.

        This method allows external systems (metabolism, allostasis) to inform
        the ignition threshold about the organism's current physiological state.
        These values directly influence threshold computation.

        Parameters
        ----------
        reserves : float
            Current metabolic reserves (energy available for ignition).
            Range: [0.0, 1.0]
            - 1.0: Full reserves (well-fed, rested)
            - 0.5: Moderate reserves
            - 0.0: Depleted reserves (exhausted)
            Values are automatically clamped to valid range.
        allostatic_load : float
            Current allostatic load (cumulative stress/wear).
            Range: [0.0, 1.0]
            - 0.0: No stress (homeostatic balance)
            - 0.5: Moderate stress
            - 1.0: High stress (allostatic overload)
            Values are automatically clamped to valid range.

        Notes
        -----
        These values affect threshold computation in the next call to
        compute_ignition_signal(). Lower reserves and higher load both
        increase the threshold, making ignition less likely and conserving
        resources during challenging conditions.
        """
        self.metabolic_reserves = np.clip(reserves, 0.0, 1.0)
        self.allostatic_load = np.clip(allostatic_load, 0.0, 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistical summary of ignition dynamics.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing ignition statistics:
            - 'mean_signal': Mean ignition signal over history
            - 'std_signal': Standard deviation of signal
            - 'mean_threshold': Mean threshold over history
            - 'std_threshold': Standard deviation of threshold
            - 'ignition_rate': Proportion of timesteps with ignition
            - 'recent_ignitions': Count of recent ignition events
            - 'current_probability': Current ignition probability

        Notes
        -----
        Returns zeros/defaults if no history has been accumulated yet.
        Statistics are computed over the signal_history buffer (max 1000 samples).
        """
        if len(self.signal_history) == 0:
            return {
                "mean_signal": 0.0,
                "mean_threshold": self.baseline_threshold,
                "ignition_rate": 0.0,
                "recent_ignitions": 0,
            }

        return {
            "mean_signal": float(np.mean(self.signal_history)),
            "std_signal": float(np.std(self.signal_history)),
            "mean_threshold": float(np.mean(self.threshold_history)),
            "std_threshold": float(np.std(self.threshold_history)),
            "ignition_rate": len(self.recent_ignitions) / max(len(self.signal_history), 1),
            "recent_ignitions": len(self.recent_ignitions),
            "current_probability": float(self.ignition_probability),
        }

    def reset(self) -> None:
        """
        Reset ignition threshold system to initial state.

        Clears all history, resets counters, and restores default values.
        Useful for starting new simulation runs or experiments.

        Notes
        -----
        Resets:
        - Threshold to baseline value
        - All signal components to zero
        - Ignition history and timestamps
        - Metabolic reserves to 1.0 (full)
        - Allostatic load to 0.0 (no stress)
        - All history buffers
        """
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
