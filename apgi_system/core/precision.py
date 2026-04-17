"""
Precision Weighting Module

Implements dynamic precision modulation for attention, uncertainty,
and neuromodulator effects.
"""

from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, Optional, Union

import numpy as np

from apgi_system.types import ConfigDict, FloatArray


class NeuromodulatorType(Enum):
    """Types of neuromodulators affecting precision."""

    NOREPINEPHRINE = "norepinephrine"  # Increases precision
    ACETYLCHOLINE = "acetylcholine"  # Volatility sensitivity
    DOPAMINE = "dopamine"  # Prediction error signaling
    SEROTONIN = "serotonin"  # Prior confidence


class PrecisionWeighting:
    """
    Manages precision (inverse variance) across hierarchical levels
    and different processing streams.

    Precision controls the gain on prediction errors, determining how much
    influence they have on belief updating and action selection. High precision
    amplifies errors (high confidence in sensory data), while low precision
    attenuates them (high uncertainty).

    Precision is dynamically modulated by multiple factors:
    - Attention: Voluntary and involuntary attentional allocation
    - Uncertainty: Estimated reliability of predictions
    - Context: Task demands and environmental conditions
    - Neuromodulators: Norepinephrine, acetylcholine, dopamine, serotonin
    - Resources: Fatigue and cognitive load

    This implements the precision-weighting mechanism central to predictive
    coding and active inference, providing a computational account of attention
    and uncertainty.

    Attributes
    ----------
    extero_precision : float
        Current exteroceptive precision
    intero_precision : float
        Current interoceptive precision
    extero_baseline : float
        Baseline exteroceptive precision
    intero_baseline : float
        Baseline interoceptive precision
    neuromodulators : Dict[NeuromodulatorType, float]
        Current neuromodulator levels (0-1 normalized)
    attention_focus : str or None
        Currently attended stream ('extero', 'intero', or None)
    attention_gain : float
        Current attention gain multiplier
    fatigue_level : float
        Current fatigue level (0=fresh, 1=exhausted)
    cognitive_load : float
        Current cognitive load (0-1)
    extero_uncertainty : float
        Estimated exteroceptive uncertainty
    intero_uncertainty : float
        Estimated interoceptive uncertainty

    Notes
    -----
    Precision is inversely related to variance:
    Π = 1 / σ²

    In predictive coding, precision-weighted prediction errors drive learning:
    Δμ ∝ Π * ε

    This provides a principled mechanism for attention: attending to a stream
    increases its precision, amplifying its influence on inference.

    References
    ----------
    .. [1] Feldman, H., & Friston, K. J. (2010). Attention, uncertainty, and
           free-energy. Frontiers in human neuroscience, 4, 215.

    Examples
    --------
    >>> config = load_config('config/default.yaml')
    >>> precision = PrecisionWeighting(config)
    >>> precisions = precision.update(
    ...     extero_error_variance=2.5,
    ...     intero_error_variance=1.0,
    ...     attention_target='extero'
    ... )
    >>> print(f"Extero precision: {precisions['exteroceptive']:.2f}")
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize precision weighting system.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing:
            - 'precision': Precision parameters including baselines and ranges
            - 'active_inference': Active inference parameters

        Examples
        --------
        >>> config = {
        ...     'precision': {
        ...         'exteroceptive_baseline': 1.0,
        ...         'interoceptive_baseline': 0.8,
        ...         'attention_gain_range': [0.5, 3.0],
        ...         'volatility_sensitivity': 0.1
        ...     }
        ... }
        >>> precision = PrecisionWeighting(config)
        """
        self.config = config
        precision_config = config.get("precision", {})

        # Batch support
        self.batch_size = config.get("active_inference", {}).get("batch_size", 1)

        # Baseline precisions (B,)
        self.extero_baseline = np.full(
            self.batch_size, precision_config.get("exteroceptive_baseline", 1.0)
        )
        self.intero_baseline = np.full(
            self.batch_size, precision_config.get("interoceptive_baseline", 0.8)
        )

        # Current precisions (B,)
        self.extero_precision = self.extero_baseline.copy()
        self.intero_precision = self.intero_baseline.copy()

        # Precision parameters
        self.gain_range = precision_config.get("attention_gain_range", [0.5, 3.0])
        self.volatility_sensitivity = precision_config.get("volatility_sensitivity", 0.1)

        # Neuromodulator levels (B, 4) - mapped to dictionary of (B,) for internal use
        self.neuromodulators = {
            NeuromodulatorType.NOREPINEPHRINE: np.full(self.batch_size, 0.5),
            NeuromodulatorType.ACETYLCHOLINE: np.full(self.batch_size, 0.5),
            NeuromodulatorType.DOPAMINE: np.full(self.batch_size, 0.5),
            NeuromodulatorType.SEROTONIN: np.full(self.batch_size, 0.5),
        }

        # Neuromodulator effects from config
        nm_effects = precision_config.get("neuromodulator_effects", {})
        self.nm_gain = {
            NeuromodulatorType.NOREPINEPHRINE: nm_effects.get("norepinephrine", 1.5),
            NeuromodulatorType.ACETYLCHOLINE: nm_effects.get("acetylcholine", 1.2),
            NeuromodulatorType.DOPAMINE: 1.0,
            NeuromodulatorType.SEROTONIN: 1.0,
        }

        # Attention state
        self.attention_focus = np.array([None] * self.batch_size)
        self.attention_gain = np.ones(self.batch_size)

        # Resource tracking
        self.fatigue_level = np.zeros(self.batch_size)
        self.cognitive_load = np.zeros(self.batch_size)

        # Uncertainty tracking (B,)
        self.extero_uncertainty = np.ones(self.batch_size)
        self.intero_uncertainty = np.ones(self.batch_size)

        # Volatility tracking
        self.extero_volatility: Union[float, np.ndarray] = 0.0
        self.intero_volatility: Union[float, np.ndarray] = 0.0
        self.volatility_window: Deque[Dict[str, np.ndarray]] = deque(maxlen=10)

    def update(
        self,
        extero_error_variance: Optional[Union[float, FloatArray]] = None,
        intero_error_variance: Optional[Union[float, FloatArray]] = None,
        attention_target: Optional[FloatArray] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Update precision estimates for batch.

        Raises
        ------
        TypeError
            If error variances are not numeric
        ValueError
            If error variances are negative, NaN, or Inf, or if attention_target
            is not 'extero', 'intero', or None

        Notes
        -----
        Precision update follows:
        Π = baseline / (uncertainty + ε)

        where uncertainty is estimated from error variance with exponential smoothing.

        Multiple modulatory factors are applied multiplicatively:
        Π_final = Π_base * attention * neuromod * resources * context

        Examples
        --------
        >>> precision = PrecisionWeighting(config)
        >>> precisions = precision.update(
        ...     extero_error_variance=2.0,
        ...     intero_error_variance=1.5,
        ...     attention_target='extero',
        ...     context={'threat_level': 0.7}
        ... )
        >>> print(f"Extero: {precisions['exteroceptive']:.2f}")
        """
        # Ensure variants are arrays (B,)
        if extero_error_variance is not None:
            if not isinstance(extero_error_variance, np.ndarray):
                extero_error_variance = np.full(self.batch_size, float(extero_error_variance))
            elif extero_error_variance.shape == ():
                extero_error_variance = np.full(self.batch_size, float(extero_error_variance))

        if intero_error_variance is not None:
            if not isinstance(intero_error_variance, np.ndarray):
                intero_error_variance = np.full(self.batch_size, float(intero_error_variance))
            elif intero_error_variance.shape == ():
                intero_error_variance = np.full(self.batch_size, float(intero_error_variance))
        # Validate inputs - check array elements are valid
        if extero_error_variance is not None:
            if np.any(np.isnan(extero_error_variance)) or np.any(np.isinf(extero_error_variance)):
                raise ValueError("extero_error_variance contains NaN or Inf values")
            if np.any(extero_error_variance < 0):
                raise ValueError(
                    f"extero_error_variance must be non-negative, got min {np.min(extero_error_variance)}"
                )

        if intero_error_variance is not None:
            if np.any(np.isnan(intero_error_variance)) or np.any(np.isinf(intero_error_variance)):
                raise ValueError("intero_error_variance contains NaN or Inf values")
            if np.any(intero_error_variance < 0):
                raise ValueError(
                    f"intero_error_variance must be non-negative, got min {np.min(intero_error_variance)}"
                )

        if attention_target is not None:
            if attention_target not in ["extero", "intero"]:
                raise ValueError(
                    f"attention_target must be 'extero' or 'intero', got {attention_target}"
                )

        # Update uncertainty estimates from error variance
        if extero_error_variance is not None:
            self._update_uncertainty("extero", extero_error_variance)

        if intero_error_variance is not None:
            self._update_uncertainty("intero", intero_error_variance)

        # Update volatility
        self._update_volatility()

        # Apply attention modulation
        if attention_target is not None:
            self._apply_attention(attention_target)

        # Apply neuromodulator effects
        self._apply_neuromodulators()

        # Apply resource constraints
        self._apply_resource_constraints()

        # Context-dependent modulation
        if context is not None:
            self._apply_context_modulation(context)

        # Clamp to valid ranges
        self._clamp_precisions()

        return {
            "exteroceptive": self.extero_precision.copy(),
            "interoceptive": self.intero_precision.copy(),
            "attention_gain": self.attention_gain.copy(),
            "fatigue_penalty": self.fatigue_level.copy(),
        }

    def _update_uncertainty(self, stream: str, error_variance: np.ndarray) -> None:
        """Update uncertainty estimate from prediction error variance (B,)."""
        alpha = 0.1
        if stream == "extero":
            self.extero_uncertainty = (1 - alpha) * self.extero_uncertainty + alpha * error_variance
            self.extero_precision = self.extero_baseline / (self.extero_uncertainty + 1e-6)
        else:
            self.intero_uncertainty = (1 - alpha) * self.intero_uncertainty + alpha * error_variance
            self.intero_precision = self.intero_baseline / (self.intero_uncertainty + 1e-6)

    def _update_volatility(self) -> None:
        """
        Update volatility estimates.

        """
        self.volatility_window.append(
            {
                "extero_uncertainty": self.extero_uncertainty,
                "intero_uncertainty": self.intero_uncertainty,
            }
        )

        # Compute volatility as variance of uncertainty
        if len(self.volatility_window) > 2:
            extero_unc = [w["extero_uncertainty"] for w in self.volatility_window]
            intero_unc = [w["intero_uncertainty"] for w in self.volatility_window]

            self.extero_volatility = np.var(extero_unc) if len(extero_unc) > 1 else 0.0
            self.intero_volatility = np.var(intero_unc) if len(intero_unc) > 1 else 0.0

    def _apply_attention(self, target: Any) -> None:
        """Apply attention modulation (B,)."""
        if not isinstance(target, np.ndarray):
            target = np.array([target] * self.batch_size)

        self.attention_focus = target

        # Vectorized attention mask
        extero_mask = target == "extero"
        intero_mask = target == "intero"

        high_gain = self.gain_range[1]

        self.extero_precision[extero_mask] *= high_gain
        self.intero_precision[extero_mask] *= 0.5

        self.intero_precision[intero_mask] *= high_gain
        self.extero_precision[intero_mask] *= 0.5

        self.attention_gain[:] = 1.0
        self.attention_gain[extero_mask | intero_mask] = high_gain

    def _apply_neuromodulators(self) -> None:
        """
        Apply neuromodulator effects on precision.

        - Norepinephrine: Increases precision (arousal)
        - Acetylcholine: Modulates based on volatility
        """
        # Norepinephrine effect
        ne_level = self.neuromodulators[NeuromodulatorType.NOREPINEPHRINE]
        ne_gain = 1.0 + (self.nm_gain[NeuromodulatorType.NOREPINEPHRINE] - 1.0) * ne_level

        self.extero_precision *= ne_gain
        self.intero_precision *= ne_gain

        # Acetylcholine effect (volatility-dependent)
        ach_level = self.neuromodulators[NeuromodulatorType.ACETYLCHOLINE]

        # High ACh in volatile environments increases learning rate (reduces precision of priors)
        volatility_factor = (self.extero_volatility + self.intero_volatility) / 2
        ach_modulation = 1.0 - ach_level * volatility_factor * self.volatility_sensitivity

        self.extero_precision *= max(0.5, ach_modulation)
        self.intero_precision *= max(0.5, ach_modulation)

    def _apply_resource_constraints(self) -> None:
        """
        Apply fatigue and cognitive load effects.

        Fatigue reduces precision (increased noise).
        """
        # Fatigue penalty (1 = no fatigue, 0 = exhausted)
        fatigue_factor = 1.0 - 0.5 * self.fatigue_level

        self.extero_precision *= fatigue_factor
        self.intero_precision *= fatigue_factor

        # High cognitive load slightly reduces precision
        load_factor = 1.0 - 0.2 * self.cognitive_load
        self.extero_precision *= load_factor
        self.intero_precision *= load_factor

    def _apply_context_modulation(self, context: Dict[str, Any]) -> None:
        """
        Apply context-dependent precision modulation.

        Different contexts may prioritize different streams.
        """
        # Example: threat context increases interoceptive precision
        if context.get("threat_level", 0) > 0.5:
            self.intero_precision *= 1.5

        # Example: task context increases exteroceptive precision
        if context.get("task_demand", 0) > 0.5:
            self.extero_precision *= 1.3

    def _clamp_precisions(self) -> None:
        """Clamp precisions to valid range."""
        precision_range = self.config.get("active_inference", {}).get(
            "precision_range", [0.1, 10.0]
        )

        self.extero_precision = np.clip(
            self.extero_precision, precision_range[0], precision_range[1]
        )

        self.intero_precision = np.clip(
            self.intero_precision, precision_range[0], precision_range[1]
        )

    def set_neuromodulator(self, modulator: NeuromodulatorType, level: float) -> None:
        """
        Set neuromodulator level.

        Parameters
        ----------
        modulator : NeuromodulatorType
            Type of neuromodulator (NOREPINEPHRINE, ACETYLCHOLINE, DOPAMINE, SEROTONIN)
        level : float
            Neuromodulator level (0-1, automatically clamped)

        Notes
        -----
        Neuromodulator effects on precision:
        - Norepinephrine: Increases precision (arousal, alertness)
        - Acetylcholine: Modulates based on volatility (learning rate)
        - Dopamine: Signals prediction errors (not directly affecting precision)
        - Serotonin: Affects prior confidence

        Examples
        --------
        >>> precision = PrecisionWeighting(config)
        >>> precision.set_neuromodulator(NeuromodulatorType.NOREPINEPHRINE, 0.8)
        >>> precisions = precision.update()
        """
        self.neuromodulators[modulator] = np.clip(level, 0.0, 1.0)

    def set_fatigue(self, level: float) -> None:
        """
        Set fatigue level.

        Parameters
        ----------
        level : float
            Fatigue level (0=fresh, 1=exhausted, automatically clamped)

        Notes
        -----
        Fatigue reduces precision, modeling decreased sensory reliability
        and increased noise with exhaustion.
        """
        self.fatigue_level = np.clip(level, 0.0, 1.0)

    def set_cognitive_load(self, load: float) -> None:
        """
        Set cognitive load level.

        Parameters
        ----------
        load : float
            Cognitive load (0=minimal, 1=maximal, automatically clamped)

        Notes
        -----
        High cognitive load reduces precision, modeling resource limitations
        under demanding task conditions.
        """
        self.cognitive_load = np.clip(load, 0.0, 1.0)

    def get_precision_matrix(self, stream: str, dimension: int) -> FloatArray:
        """
        Get precision matrix for a processing stream.

        Constructs a diagonal precision matrix for use in free energy
        calculations and belief updates.

        Parameters
        ----------
        stream : str
            Processing stream: 'extero' or 'intero'
        dimension : int
            Dimensionality of the matrix

        Returns
        -------
        precision_matrix : np.ndarray
            Diagonal precision matrix of shape (dimension, dimension)

        Notes
        -----
        Returns Π * I where Π is the scalar precision and I is identity.
        For more complex models, this could return non-diagonal matrices
        encoding correlations.

        Examples
        --------
        >>> precision = PrecisionWeighting(config)
        >>> precision.update(extero_error_variance=2.0)
        >>> P = precision.get_precision_matrix('extero', 256)
        >>> print(P.shape)  # (256, 256)
        """
        if stream == "extero":
            precision = self.extero_precision
        else:
            precision = self.intero_precision

        return precision * np.eye(dimension)

    def reset(self) -> None:
        """Reset precision system for all agents."""
        self.extero_precision = self.extero_baseline.copy()
        self.intero_precision = self.intero_baseline.copy()
        self.attention_focus = np.array([None] * self.batch_size)
        self.attention_gain.fill(1.0)
        self.fatigue_level.fill(0.0)
        self.cognitive_load.fill(0.0)

        for modulator in self.neuromodulators:
            self.neuromodulators[modulator].fill(0.5)
