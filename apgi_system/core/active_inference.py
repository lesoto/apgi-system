"""
Active Inference Engine

Implements the core active inference loop using variational message passing
and hierarchical Bayesian filtering.
"""

import logging
import threading
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Tuple, Union

import numpy as np

from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.core.motor_planning import MotorPlanner
from apgi_system.core.temporal_dynamics import TemporalDynamics
from apgi_system.types import ConfigDict, FloatArray
from apgi_system.validation import InputValidator

logger = logging.getLogger(__name__)


class MultiModalInputLayer:
    """
    Handles heterogeneous input streams and fuses them into a combined sensory representation.
    Supports Vision, NLP, and Audio modalities.
    """

    def __init__(self, config: ConfigDict) -> None:
        self.config = config.get("multi_modal", {})
        self.modalities = self.config.get("modalities", {"vision": 256, "nlp": 128, "audio": 64})
        self.combined_dim = sum(self.modalities.values())

        # Projection matrices to a shared sensory space if needed
        # For now, we simple concatenate or use a weighted fusion
        self.weights = self.config.get("fusion_weights", {k: 1.0 for k in self.modalities})

    def fuse(self, inputs: Dict[str, FloatArray]) -> FloatArray:
        """
        Fuse multiple modalities into a single vector.
        If a modality is missing, it's padded with zeros.
        """
        fused_parts = []
        for name, dim in self.modalities.items():
            if name in inputs:
                val = inputs[name]
                if val.shape[0] != dim:
                    # Reshape or pad if dimension mismatch
                    if val.size >= dim:
                        val = val[:dim]
                    else:
                        val = np.pad(val, (0, dim - val.size))
                fused_parts.append(val * self.weights.get(name, 1.0))
            else:
                fused_parts.append(np.zeros(dim))

        return np.concatenate(fused_parts)

    def get_combined_dim(self) -> int:
        return self.combined_dim


@dataclass
class BeliefState:
    """Represents beliefs at a single hierarchical level."""

    mean: FloatArray  # Posterior mean
    covariance: FloatArray  # Posterior covariance
    precision: float  # Precision (inverse variance)
    prediction: FloatArray  # Predicted observation/state
    prediction_error: FloatArray  # Prediction error


class HierarchicalGaussianFilter:
    """
    Hierarchical Gaussian filtering for approximate Bayesian inference.

    Implements predictive coding with precision-weighted prediction errors
    propagating up the hierarchy and predictions propagating down. This filter
    performs variational message passing to minimize free energy across multiple
    hierarchical levels, each operating at different timescales.

    The filter maintains belief states at each level, consisting of posterior
    means, covariances, and precision estimates. Prediction errors flow bottom-up
    while predictions flow top-down, implementing the core predictive coding
    architecture.

    Attributes
    ----------
    num_levels : int
        Number of hierarchical levels in the filter
    state_dims : List[int]
        Dimensionality of state representations at each level
    observation_dim : int
        Dimensionality of sensory observations
    beliefs : List[BeliefState]
        Current belief states at each hierarchical level
    learning_rate : float
        Learning rate for belief updates
    precision_min : float
        Minimum allowed precision value
    precision_max : float
        Maximum allowed precision value

    Notes
    -----
    The hierarchical structure implements the following dynamics:
    - Bottom-up: Prediction errors propagate upward, weighted by precision
    - Top-down: Predictions propagate downward from higher levels
    - Precision: Dynamically updated based on prediction error statistics

    References
    ----------
    .. [1] Friston, K. (2010). The free-energy principle: a unified brain theory?
           Nature Reviews Neuroscience, 11(2), 127-138.
    """

    def __init__(
        self,
        num_levels: int,
        state_dims: List[int],
        observation_dim: int,
        config: Optional[ConfigDict] = None,
    ) -> None:
        """
        Initialize hierarchical Gaussian filter.

        Parameters
        ----------
        num_levels : int
            Number of hierarchical levels (typically 3-5)
        state_dims : List[int]
            Dimensionality at each level, from bottom (sensory) to top (abstract)
        observation_dim : int
            Dimensionality of sensory observations
        config : Dict[str, Any], optional
            Configuration dictionary containing:
            - 'learning_rate': Learning rate for belief updates (default: 0.01)
            - 'precision_range': [min, max] precision values (default: [0.1, 10.0])

        Examples
        --------
        >>> filter = HierarchicalGaussianFilter(
        ...     num_levels=3,
        ...     state_dims=[256, 128, 64],
        ...     observation_dim=256,
        ...     config={'learning_rate': 0.01}
        ... )
        >>> beliefs, fe = filter.update(observation=np.random.randn(256))
        """
        self.num_levels = num_levels
        self.state_dims = state_dims
        self.observation_dim = observation_dim
        self.config = config or {}

        # Initialize belief states
        self.beliefs: List[BeliefState] = []
        for dim in state_dims:
            self.beliefs.append(
                BeliefState(
                    mean=np.zeros(dim),
                    covariance=np.eye(dim),
                    precision=1.0,
                    prediction=np.zeros(dim),
                    prediction_error=np.zeros(dim),
                )
            )

        # Learning parameters
        self.learning_rate = self.config.get("learning_rate", 0.01)
        self.projection_learning_rate = self.config.get("projection_learning_rate", 0.001)

        # Precision dynamics
        self.precision_min = self.config.get("precision_range", [0.1, 10.0])[0]
        self.precision_max = self.config.get("precision_range", [0.1, 10.0])[1]

        # Projection matrix cache with LRU eviction
        self._projection_cache_max_size = self.config.get("projection_cache_size", 100)
        self._projection_cache: Dict[Tuple[int, int, int], np.ndarray] = {}
        self._cache_access_order: Deque[Tuple[int, int, int]] = deque()
        self._cache_lock = threading.Lock()  # Thread safety for cache access

    def reset_beliefs(self) -> None:
        """Reset beliefs to initial state."""
        for belief in self.beliefs:
            belief.mean = np.zeros_like(belief.mean)
            belief.covariance = np.eye(len(belief.mean))
            belief.precision = 1.0
            belief.prediction = np.zeros_like(belief.prediction)
            belief.prediction_error = np.zeros_like(belief.prediction_error)

    def _layer_norm(self, x: FloatArray, eps: float = 1e-6) -> FloatArray:
        """Apply layer normalization to stabilize hidden states."""
        mu = np.mean(x)
        sigma = np.std(x)
        return (x - mu) / (sigma + eps)

    def _variational_dropout(self, x: FloatArray, p: float = 0.1) -> FloatArray:
        """Apply variational dropout for regularization."""
        mask = np.random.binomial(1, 1 - p, size=x.shape)
        return x * mask / (1 - p)

    def update(self, observation: FloatArray, dt: float = 0.001) -> Tuple[List[BeliefState], float]:
        """
        Update beliefs using variational message passing.

        Performs a complete cycle of hierarchical inference:
        1. Bottom-up pass: Compute prediction errors at each level
        2. Top-down pass: Update beliefs to minimize prediction errors
        3. Precision update: Adjust precision based on error statistics
        4. Free energy computation: Calculate total variational free energy

        Parameters
        ----------
        observation : np.ndarray
            Sensory observation vector of shape (observation_dim,)
        dt : float, default=0.001
            Time step for belief integration in seconds

        Returns
        -------
        beliefs : List[BeliefState]
            Updated belief states at each hierarchical level
        free_energy : float
            Total variational free energy across all levels

        Raises
        ------
        ValueError
            If observation shape doesn't match expected dimensions, contains NaN/Inf,
            or dt is not positive

        Notes
        -----
        The update implements gradient descent on variational free energy:
        δμ = η * (Π_below * ε_below - Π_above * ε_above)

        where μ is the belief mean, η is learning rate, Π is precision,
        and ε is prediction error.

        Examples
        --------
        >>> filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)
        >>> obs = np.random.randn(256)
        >>> beliefs, fe = filter.update(obs, dt=0.001)
        >>> print(f"Free energy: {fe:.2f}")
        """
        # Validate inputs
        InputValidator.validate_array(
            observation, "observation", expected_shape=(self.observation_dim,)
        )

        InputValidator.validate_scalar(dt, "dt", positive=True, value_range=(1e-6, 1.0))

        # Bottom-up pass: compute prediction errors
        self._bottom_up_pass(observation)

        # Top-down pass: update beliefs
        self._top_down_pass(dt)

        # Update precisions based on prediction error statistics
        self._update_precisions(dt)

        # Update projection matrices (generative model learning)
        self._update_projection_matrices(dt)

        # Compute total free energy
        total_fe = self._compute_total_free_energy(observation)

        return self.beliefs, total_fe

    def _bottom_up_pass(self, observation: FloatArray) -> None:
        """
        Bottom-up pass: compute prediction errors at each level.

        Computes prediction errors by comparing observations/states with
        predictions from the level above. Errors propagate from the sensory
        level upward through the hierarchy.

        Parameters
        ----------
        observation : np.ndarray
            Sensory observation at the bottom level

        Notes
        -----
        At level 0 (sensory): ε₀ = o - μ̂₀
        At level i > 0: εᵢ = μᵢ₋₁ - g(μᵢ)

        where g() is the generative mapping from level i to i-1
        """
        # Level 0: sensory prediction error
        self.beliefs[0].prediction_error = observation - self.beliefs[0].prediction

        # Higher levels: state prediction errors
        for level in range(1, self.num_levels):
            # At each level, compute error: εᵢ = projected(μᵢ₋₁) - projected(g(μᵢ))
            # where both terms are projected to the current level's dimension

            current_belief_dim = self.beliefs[level].mean.shape[0]
            below_belief = self.beliefs[level - 1].mean

            # Project level below's belief to current level's dimension
            if below_belief.shape[0] != current_belief_dim:
                below_belief_projected = self._project_up(level - 1, below_belief)
            else:
                below_belief_projected = below_belief

            # Map current level's prediction down to level below, then project back up
            # This gives us the prediction at current level's dimension
            higher_prediction_down = self._map_down(level, self.beliefs[level].mean)
            if higher_prediction_down.shape[0] != current_belief_dim:
                higher_prediction = self._project_up(level - 1, higher_prediction_down)
            else:
                higher_prediction = higher_prediction_down

            # Error is difference at current level's dimension
            self.beliefs[level].prediction_error = below_belief_projected - higher_prediction

    def _top_down_pass(self, dt: float) -> None:
        """
        Top-down pass: update beliefs using precision-weighted errors.

        Updates belief means at each level by performing gradient descent on
        free energy. Beliefs are adjusted to minimize precision-weighted
        prediction errors from both above and below.

        Parameters
        ----------
        dt : float
            Time step for integration

        Notes
        -----
        The update rule implements:
        dμᵢ/dt = η * (Πᵢ₋₁ * εᵢ₋₁ - Πᵢ₊₁ * εᵢ₊₁)

        This balances errors from the level below (bottom-up) with
        errors from the level above (top-down).
        """
        # Update from top to bottom
        for level in range(self.num_levels - 1, -1, -1):
            # Precision-weighted error from below
            if level == 0:
                # Bottom level gets sensory prediction error
                error_below = self.beliefs[0].prediction_error
                precision_below = self.beliefs[0].precision
            else:
                # Project error from level below to current level's dimension
                error_below_raw = self.beliefs[level - 1].prediction_error
                target_dim = self.beliefs[level].mean.shape[0]
                source_dim = error_below_raw.shape[0]

                if target_dim != source_dim:
                    error_below = self._project_up(level - 1, error_below_raw)
                else:
                    error_below = error_below_raw

                precision_below = self.beliefs[level - 1].precision

            # Precision-weighted error from above
            if level < self.num_levels - 1:
                # Project error from level above to current level's dimension
                error_above_raw = self.beliefs[level + 1].prediction_error
                target_dim = self.beliefs[level].mean.shape[0]
                source_dim = error_above_raw.shape[0]

                if target_dim != source_dim:
                    error_above = self._map_down(level + 1, error_above_raw)
                else:
                    error_above = error_above_raw

                precision_above = self.beliefs[level + 1].precision
            else:
                # Top level has no error from above
                error_above = np.zeros_like(self.beliefs[level].mean)
                precision_above = 0.0

            # Update belief mean (gradient descent on free energy)
            # δμ = η * (Π_below * ε_below - Π_above * ε_above)

            # Validate array shapes before computation
            belief_shape = self.beliefs[level].mean.shape
            if error_below.shape != belief_shape:
                import logging

                if error_below.size == np.prod(belief_shape):
                    # Recoverable: same number of elements, reshape cleanly
                    error_below = error_below.reshape(belief_shape)
                    logging.debug(
                        f"Reshaped error_below at level {level}: {error_below.shape} → {belief_shape}"
                    )
                else:
                    # Unrecoverable: raise so the caller knows gradient flow is broken
                    raise ValueError(
                        f"Irrecoverable shape mismatch at level {level}: "
                        f"belief {belief_shape}, error {error_below.shape}. "
                        f"Check projection matrix dimensions."
                    )
            if error_above.shape != belief_shape:
                import logging

                if error_above.size == np.prod(belief_shape):
                    # Recoverable: same number of elements, reshape cleanly
                    error_above = error_above.reshape(belief_shape)
                    logging.debug(
                        f"Reshaped error_above at level {level}: {error_above.shape} → {belief_shape}"
                    )
                else:
                    # Unrecoverable: raise so the caller knows gradient flow is broken
                    raise ValueError(
                        f"Irrecoverable shape mismatch at level {level}: "
                        f"belief {belief_shape}, error_above {error_above.shape}. "
                        f"Check projection matrix dimensions."
                    )

            update = self.learning_rate * (
                precision_below * error_below - precision_above * error_above
            )

            # Apply layer normalization and dropout to the update vector to ensure stability
            update = self._variational_dropout(self._layer_norm(update), p=0.01)

            self.beliefs[level].mean += dt * update

            # Update prediction for next iteration
            self.beliefs[level].prediction = self._generate_prediction(level)

    def _update_precisions(self, dt: float) -> None:
        """
        Update precision estimates based on prediction error statistics.

        Precision is inversely proportional to prediction error variance,
        implementing adaptive gain control. High precision amplifies prediction
        errors, while low precision attenuates them.

        Parameters
        ----------
        dt : float
            Time step for precision update smoothing

        Notes
        -----
        Precision update: Π = 1 / (E[ε²] + ε_small)

        Uses exponential smoothing: Π_new = 0.9 * Π_old + 0.1 * Π_estimated

        Precision is clamped to [precision_min, precision_max] for stability.
        """
        for level in range(self.num_levels):
            # Estimate variance from squared prediction errors
            error_variance = np.mean(self.beliefs[level].prediction_error ** 2) + 1e-6

            # Update precision (with smoothing)
            new_precision = 1.0 / error_variance
            old = self.beliefs[level].precision
            try:
                dt_ms = dt * 1000.0
            except NameError:
                dt_ms = 1.0

            # Timescale-matched smoothing: faster levels update more quickly
            level_configs = (
                self.config.get("hierarchy", {}).get("level_configs", [])
                if hasattr(self, "config")
                else []
            )
            default_timescale = self.config.get("default_timescale_ms", 50.0)
            level_timescale_ms = default_timescale
            if level < len(level_configs):
                level_timescale_ms = level_configs[level].get("timescale_ms", default_timescale)

            alpha = min(0.5, dt_ms / level_timescale_ms)  # dt-normalized learning rate
            self.beliefs[level].precision = float((1 - alpha) * old + alpha * new_precision)

            # Clamp to valid range
            self.beliefs[level].precision = np.clip(
                self.beliefs[level].precision, self.precision_min, self.precision_max
            )

    def _update_projection_matrices(self, dt: float) -> None:
        """
        Update projection matrices using gradient descent on prediction errors.

        Implements generative model learning by adapting the projection matrices
        that map between hierarchical levels. This enables the system to learn
        the structure of the environment and improve predictions over time.

        Parameters
        ----------
        dt : float
            Time step for learning rate scaling

        Notes
        -----
        Uses Hebbian-style learning rule:
        ΔW = η * ε * x^T

        where η is learning rate, ε is prediction error, and x is the input state.
        This implements predictive coding-style learning where the generative
        model adapts to minimize prediction errors.
        """
        with self._cache_lock:
            # Update projection matrices for each level
            for level in range(1, self.num_levels):
                # Get prediction error at this level
                error = self.beliefs[level].prediction_error

                # Get the state from level below (input to projection)
                below_state = self.beliefs[level - 1].mean

                # Get the projection matrix key for this level
                target_dim = self.beliefs[level].mean.shape[0]
                source_dim = below_state.shape[0]
                key = (level, target_dim, source_dim)

                # Only update if matrix exists in cache
                if key in self._projection_cache:
                    projection_matrix = self._projection_cache[key]

                    # Compute gradient: outer product of error and input
                    # This is a Hebbian-style update rule
                    gradient = np.outer(error, below_state)

                    # Scale learning rate by timestep
                    effective_lr = self.projection_learning_rate * dt * 1000.0

                    # Update projection matrix
                    self._projection_cache[key] = projection_matrix - effective_lr * gradient

                    # Re-orthogonalize to maintain numerical stability
                    updated_matrix = self._projection_cache[key]
                    if updated_matrix.shape[0] <= updated_matrix.shape[1]:
                        U, S, Vt = np.linalg.svd(updated_matrix, full_matrices=False)
                        self._projection_cache[key] = U @ Vt
                    else:
                        U, S, Vt = np.linalg.svd(updated_matrix, full_matrices=False)
                        self._projection_cache[key] = U @ Vt

    def _generate_prediction(self, level: int) -> FloatArray:
        """
        Generate prediction at a given level from belief above.

        Parameters
        ----------
        level : int
            Level index for which to generate prediction

        Returns
        -------
        prediction : np.ndarray
            Predicted state at the specified level

        Notes
        -----
        Top level predicts itself (prior), lower levels receive predictions
        from the level above via generative mapping.
        """
        if level < self.num_levels - 1:
            return self._map_down(level + 1, self.beliefs[level + 1].mean)
        else:
            # Top level predicts itself (prior)
            return self.beliefs[level].mean

    def _get_projection_matrix(
        self, from_level: int, target_dim: int, source_dim: int
    ) -> np.ndarray[Any, Any]:
        """
        Get projection matrix with LRU cache management.

        Args:
            from_level: Source level (higher in hierarchy)
            target_dim: Target dimension
            source_dim: Source dimension

        Returns:
            Projection matrix
        """
        key = (from_level, target_dim, source_dim)

        with self._cache_lock:
            # Check if matrix exists in cache
            if key in self._projection_cache:
                # Move to end (most recently used)
                self._cache_access_order.remove(key)
                self._cache_access_order.append(key)
                return self._projection_cache[key]

            # Create new projection matrix with proper initialization
            # Use orthogonal initialization for better numerical stability
            if target_dim == source_dim:
                # Same dimension: deterministic identity (no noise — preserves exact information)
                projection_matrix = np.eye(target_dim)
            else:
                # Deterministic orthonormal projection via SVD — preserves information geometry
                rng = np.random.default_rng(seed=hash((source_dim, target_dim)) % 2**32)
                raw = rng.standard_normal((target_dim, source_dim))
                U, S, Vt = np.linalg.svd(raw, full_matrices=False)
                # Use pure orthonormal matrix via SVD (singular values = 1)
                # This ensures unity gain across layers, preventing numerical explosion
                projection_matrix = U @ Vt

            # Add to cache
            self._projection_cache[key] = projection_matrix
            self._cache_access_order.append(key)

            # Evict oldest if cache is full
            if len(self._projection_cache) > self._projection_cache_max_size:
                oldest_key = self._cache_access_order.popleft()  # O(1) operation with deque
                del self._projection_cache[oldest_key]
                import logging

                logging.debug(
                    f"Cache eviction: removed key {oldest_key}, cache size now {len(self._projection_cache)}"
                )

            return projection_matrix

    def _map_down(self, from_level: int, state: FloatArray) -> FloatArray:
        """
        Map state representation down one level in the hierarchy.

        Implements the generative mapping g: μᵢ → μ̂ᵢ₋₁ that projects
        higher-level representations to lower-level predictions.

        Parameters
        ----------
        from_level : int
            Source level (higher in hierarchy)

        Notes
        -----
        Only the **input state vector** is layer-normalised before the
        multiplication.  The projection matrix must *not* be normalised
        because that would destroy the orthonormality property established
        by the deterministic SVD initialisation (``_get_projection_matrix``).
        The shared ``_cache_lock`` is used for thread-safe matrix access
        instead of a locally-created ``Lock`` (which provides no exclusion).
        """
        target_dim = self.beliefs[from_level - 1].mean.shape[0]
        source_dim = state.shape[0]

        # Get projection matrix from cache (already orthonormal — do NOT normalise it)
        projection_matrix = self._get_projection_matrix(from_level, target_dim, source_dim)

        # Normalise the input state vector only
        state = self._layer_norm(state)

        # Thread-safe matrix multiplication using the shared instance-level lock
        try:
            with self._cache_lock:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    result = projection_matrix @ state
        except (FloatingPointError, ValueError):
            logger.warning("_map_down: matmul failed at level %d; returning zeros.", from_level)
            result = np.zeros(target_dim)

        return self._layer_norm(result)

    def _project_up(self, from_level: int, state: FloatArray) -> FloatArray:
        """
        Map state representation up one level in the hierarchy.

        Parameters
        ----------
        from_level : int
            Source level (lower in hierarchy)
        state : np.ndarray
            State vector to map up

        Returns
        -------
        np.ndarray
            Mapped state vector at higher level

        Notes
        -----
        Only the **input state vector** is layer-normalised and dropout-regularised
        before the multiplication.  The projection matrix must *not* be normalised
        for the same reason as ``_map_down``.  Thread-safety relies on the shared
        ``_cache_lock`` rather than a locally-created ``Lock``.
        """
        if from_level >= self.num_levels - 1:
            # Already at top level
            return state

        target_dim = self.beliefs[from_level + 1].mean.shape[0]
        source_dim = state.shape[0]

        # Get projection matrix from cache (already orthonormal — do NOT normalise it)
        projection_matrix = self._get_projection_matrix(from_level + 1, target_dim, source_dim)

        # Normalise and regularise the input state vector only
        state = self._variational_dropout(self._layer_norm(state), p=0.05)

        # Thread-safe matrix multiplication using the shared instance-level lock
        try:
            with self._cache_lock:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    result = projection_matrix @ state
        except (FloatingPointError, ValueError):
            logger.warning("_project_up: matmul failed at level %d; returning zeros.", from_level)
            result = np.zeros(target_dim)

        return self._layer_norm(result)

    def _compute_total_free_energy(self, observation: FloatArray) -> float:
        """
        Compute total variational free energy across hierarchy.

        Free energy is the sum of precision-weighted squared prediction errors
        at all levels, providing a scalar measure of model fit.

        Parameters
        ----------
        observation : np.ndarray
            Current sensory observation

        Returns
        -------
        free_energy : float
            Total free energy F = Σᵢ (0.5 * Πᵢ * ||εᵢ||²)

        Notes
        -----
        Lower free energy indicates better model fit. The system performs
        gradient descent on free energy to improve its internal model.
        """
        total_fe = 0.0

        # Sensory level
        error = observation - self.beliefs[0].prediction
        total_fe += 0.5 * self.beliefs[0].precision * np.sum(error**2)

        # Higher levels
        for level in range(1, self.num_levels):
            error = self.beliefs[level].prediction_error
            total_fe += 0.5 * self.beliefs[level].precision * np.sum(error**2)

        return total_fe


class ActiveInferenceEngine:
    """
    Main active inference engine coordinating perception and action.

    Implements the complete active inference loop, integrating perceptual
    inference (minimizing variational free energy) with action selection
    (minimizing expected free energy). The engine maintains hierarchical
    beliefs about the world and selects actions that balance exploration
    (epistemic value) and exploitation (pragmatic value).

    The engine coordinates three key processes:
    1. Perceptual inference: Update beliefs to explain observations
    2. Policy evaluation: Assess expected outcomes of different actions
    3. Action selection: Choose actions that minimize expected free energy

    Attributes
    ----------
    filter : HierarchicalGaussianFilter
        Hierarchical Gaussian filter for perceptual inference
    fe_calc : FreeEnergyCalculator
        Calculator for free energy and expected free energy
    num_policies : int
        Number of policies to evaluate during action selection
    planning_horizon : int
        Number of time steps to simulate ahead
    time : float
        Current simulation time in seconds
    timestep : float
        Time step duration in seconds

    Notes
    -----
    Active inference unifies perception and action under a single principle:
    minimize (expected) free energy. This implements the free energy principle
    for autonomous agents.

    References
    ----------
    .. [1] Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., & Pezzulo, G. (2017).
           Active inference: a process theory. Neural computation, 29(1), 1-49.

    Examples
    --------
    >>> config = load_config('config/default.yaml')
    >>> engine = ActiveInferenceEngine(config)
    >>> observation = np.random.randn(256)
    >>> action, info = engine.step(observation)
    >>> print(f"Free energy: {info['free_energy']:.2f}")
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize active inference engine.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing:
            - 'hierarchy': Hierarchical structure configuration
            - 'active_inference': Active inference parameters
            - 'num_policies': Number of policies to evaluate (default: 10)
            - 'planning_horizon': Planning horizon in steps (default: 3)
            - 'system': System-level parameters including timestep

        Raises
        ------
        KeyError
            If required configuration keys are missing
        ValueError
            If configuration values are invalid

        Examples
        --------
        >>> config = {
        ...     'hierarchy': {
        ...         'num_levels': 4,
        ...         'level_configs': [
        ...             {'nodes': 256, 'name': 'sensory'},
        ...             {'nodes': 128, 'name': 'perceptual'},
        ...             {'nodes': 64, 'name': 'conceptual'},
        ...             {'nodes': 32, 'name': 'abstract'}
        ...         ]
        ...     },
        ...     'system': {'timestep_ms': 1.0}
        ... }
        >>> engine = ActiveInferenceEngine(config)
        """
        self.config = config

        # Extract hierarchy configuration
        hierarchy_config = config.get("hierarchy", {})
        num_levels = hierarchy_config.get("num_levels", 4)
        level_configs = hierarchy_config.get("level_configs", [])

        state_dims = [lc["nodes"] for lc in level_configs]
        observation_dim = state_dims[0]  # Sensory level

        # Initialize hierarchical filter
        self.filter = HierarchicalGaussianFilter(
            num_levels=num_levels,
            state_dims=state_dims,
            observation_dim=observation_dim,
            config=config.get("active_inference", {}),
        )

        # Initialize free energy calculator
        self.fe_calc = FreeEnergyCalculator(config)

        # Initialize Multi-Modal Layer
        self.input_layer = MultiModalInputLayer(config)

        # Initialize Motor Planner
        self.motor_planner = MotorPlanner(config)

        # Initialize Temporal Dynamics with seeded RNG for full reproducibility
        _engine_seed = config.get("system", {}).get("random_seed", None)
        self.temporal_dynamics = TemporalDynamics(config, rng=np.random.default_rng(_engine_seed))

        # Planning parameters
        planning_config = config.get("active_inference", {}).get("planning", {})
        self.planning_horizon = planning_config.get("horizon", 3)
        self.num_policies = planning_config.get("num_policies", 10)

        # State tracking

        self.time = 0.0
        self.timestep = config.get("system", {}).get("timestep_ms", 1.0) / 1000.0

    def step(
        self,
        observation: Union[FloatArray, Dict[str, FloatArray]],
        available_actions: Optional[List[FloatArray]] = None,
    ) -> Tuple[FloatArray, Dict[str, Any]]:
        """
        Execute single step of active inference loop.
        Supports multi-modal input and temporal orchestration.
        """
        # 1. Update temporal dynamics
        temporal_info = self.temporal_dynamics.update(self.timestep)

        # 2. Multi-modal fusion
        if isinstance(observation, dict):
            fused_observation = self.input_layer.fuse(observation)
        else:
            fused_observation = observation

        # 3. Apply phase-dependent gain modulation (Alpha/Gamma PAC)
        gain = self.temporal_dynamics.get_gain_modulation("alpha")
        fused_observation *= gain

        # 4. Perceptual inference: Update beliefs
        beliefs, free_energy = self.filter.update(fused_observation, dt=self.timestep)

        # 5. Hierarchical Motor Planning: Select action minimizing G
        action, planning_info = self.motor_planner.plan(beliefs, available_actions)

        # Increment time
        self.time += self.timestep

        # Compile diagnostics
        info = {
            "time": self.time,
            "free_energy": free_energy,
            "beliefs": beliefs,
            "planning": planning_info,
            "temporal": temporal_info,
            "precisions": [b.precision for b in beliefs],
            "prediction_errors": [b.prediction_error for b in beliefs],
        }

        return action, info

    def reset(self) -> None:
        """Reset the engine and its components."""
        self.filter.reset_beliefs()
        self.motor_planner.reset()
        self.temporal_dynamics.reset()
        self.time = 0.0
