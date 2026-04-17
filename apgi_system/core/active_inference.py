"""
Active Inference Engine

Implements the core active inference loop using variational message passing
and hierarchical Bayesian filtering.

Performance notes
-----------------
* ``ActiveInferenceEngine.step()`` remains synchronous for backward
  compatibility.
* ``ActiveInferenceEngine.async_step()`` is the coroutine variant that
  offloads the heavy HGF ``filter.update()`` call via
  ``asyncio.to_thread`` so the event loop stays responsive.
* ``vectorized_batch_step()`` runs a *single* HGF instance whose batch
  dimension equals the agent count, achieving NumPy-vectorized multi-agent
  simulation without spawning extra threads.
"""

import asyncio
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple, Union

import numpy as np

from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.core.motor_planning import MotorPlanner
from apgi_system.core.temporal_dynamics import TemporalDynamics
from apgi_system.types import ConfigDict, FloatArray
from apgi_system.validation import InputValidator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Multi-agent vectorised simulation
# ---------------------------------------------------------------------------


@dataclass
class ActiveInferenceAgent:
    """
    Lightweight descriptor for a single agent inside a vectorised batch.

    A batch of ``N`` agents shares *one* ``HierarchicalGaussianFilter``
    whose batch dimension is ``N``.  Each ``ActiveInferenceAgent`` records
    per-agent metadata and provides a view of its slice of the shared
    belief state.

    Parameters
    ----------
    agent_id : int
        Zero-based index into the batch dimension.
    config : dict
        Agent-specific configuration overrides (merged on top of the engine
        config at construction time).
    """

    agent_id: int
    config: Dict[str, Any] = field(default_factory=dict)
    # Accumulated free-energy trace for post-hoc analysis
    free_energy_history: List[float] = field(default_factory=list)

    def record_step(self, free_energy: float) -> None:
        """Append the per-agent free energy from the current step."""
        self.free_energy_history.append(free_energy)

    def reset(self) -> None:
        """Clear accumulated history."""
        self.free_energy_history.clear()


class VectorizedAgentPool:
    """
    Manages a pool of ``ActiveInferenceAgent`` objects that share a single
    ``HierarchicalGaussianFilter`` batch.

    NumPy broadcasting across the batch dimension means that all ``N``
    agents are updated simultaneously in O(N·D²) instead of sequentially
    in O(N·T·D²), where T is the number of sequential steps.

    Parameters
    ----------
    engine : ActiveInferenceEngine
        The shared engine.  Its ``filter.batch_size`` must equal ``num_agents``.
    num_agents : int
        Number of agents to run in parallel.
    agent_configs : list of dict, optional
        Per-agent configuration overrides.  Defaults to empty dicts.

    Examples
    --------
    >>> engine = ActiveInferenceEngine({**config, "system": {**config["system"], "batch_size": 64}})
    >>> pool = VectorizedAgentPool(engine, num_agents=64)
    >>> observations = np.random.randn(64, 256)
    >>> results = pool.step(observations)
    >>> print(f"Stepped {len(results)} agents, mean FE = {np.mean([r['free_energy'] for r in results]):.3f}")
    """

    def __init__(
        self,
        engine: "ActiveInferenceEngine",
        num_agents: int,
        agent_configs: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if engine.batch_size != num_agents:
            raise ValueError(
                f"Engine batch_size ({engine.batch_size}) must equal num_agents ({num_agents}). "
                f"Set config['system']['batch_size'] = {num_agents} before constructing the engine."
            )
        self.engine = engine
        self.num_agents = num_agents
        _cfgs = agent_configs or [{} for _ in range(num_agents)]
        self.agents: List[ActiveInferenceAgent] = [
            ActiveInferenceAgent(agent_id=i, config=_cfgs[i]) for i in range(num_agents)
        ]

    def step(
        self,
        observations: FloatArray,
        available_actions: Optional[List[List[FloatArray]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute one vectorised step for all agents.

        Parameters
        ----------
        observations : np.ndarray, shape (N, D)
            One observation row per agent.
        available_actions : list of list, optional
            Per-agent action sets.  If ``None``, the engine's motor planner
            operates with no external constraints.

        Returns
        -------
        list of dict
            Per-agent info dicts containing ``free_energy``, ``action``, and
            ``agent_id``.
        """
        if observations.ndim != 2 or observations.shape[0] != self.num_agents:
            raise ValueError(
                f"observations must have shape ({self.num_agents}, D), " f"got {observations.shape}"
            )

        # Single vectorised HGF pass covers all agents simultaneously
        # action / info are still computed per-agent by reusing the batch beliefs
        action, info = self.engine.step(observations)

        results: List[Dict[str, Any]] = []
        beliefs = info["beliefs"]

        for i, agent in enumerate(self.agents):
            # Per-agent free energy: extract the i-th row contribution
            # We compute it from the per-level precision-weighted errors
            agent_fe = 0.0
            for belief in beliefs:
                if belief.prediction_error.ndim == 2:
                    err = belief.prediction_error[i]
                    prec = (
                        belief.precision[i]
                        if belief.precision.ndim > 0
                        else float(belief.precision)
                    )
                else:
                    err = belief.prediction_error
                    prec = float(belief.precision)
                agent_fe += float(0.5 * prec * np.sum(err**2))

            agent.record_step(agent_fe)

            results.append(
                {
                    "agent_id": i,
                    "free_energy": agent_fe,
                    "action": action,
                    "belief_means": [b.mean[i] if b.mean.ndim == 2 else b.mean for b in beliefs],
                }
            )

        return results

    async def async_step(
        self,
        observations: FloatArray,
    ) -> List[Dict[str, Any]]:
        """
        Async wrapper around :meth:`step` – offloads computation to a
        thread so the event loop remains unblocked.
        """
        return await asyncio.to_thread(self.step, observations)

    def reset(self) -> None:
        """Reset engine and all agent histories."""
        self.engine.reset()
        for agent in self.agents:
            agent.reset()


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
        Fuse multiple modalities into a single matrix (B, D).
        If a modality is missing, it's padded with zeros.
        """
        fused_parts = []
        batch_size = next(iter(inputs.values())).shape[0] if inputs else 1

        for name, dim in self.modalities.items():
            if name in inputs:
                val = inputs[name]
                if val.ndim == 1:
                    val = val.reshape(1, -1)

                if val.shape[1] != dim:
                    # Reshape or pad if dimension mismatch
                    if val.shape[1] >= dim:
                        val = val[:, :dim]
                    else:
                        val = np.pad(val, ((0, 0), (0, dim - val.shape[1])))
                fused_parts.append(val * self.weights.get(name, 1.0))
            else:
                fused_parts.append(np.zeros((batch_size, dim)))

        return np.concatenate(fused_parts, axis=1)

    def get_combined_dim(self) -> int:
        return self.combined_dim


@dataclass
class BeliefState:
    """Represents beliefs at a single hierarchical level for one or more agents."""

    mean: FloatArray  # Posterior mean (B, D)
    covariance: FloatArray  # Posterior covariance (B, D, D)
    precision: FloatArray  # Precision (inverse variance) (B, 1) or (B,)
    prediction: FloatArray  # Predicted observation/state (B, D)
    prediction_error: FloatArray  # Prediction error (B, D)


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
        batch_size: int = 1,
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
        batch_size : int, default=1
            Number of independent agents to simulate in parallel
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
        ...     batch_size=100,
        ...     config={'learning_rate': 0.01}
        ... )
        >>> beliefs, fe = filter.update(observation=np.random.randn(100, 256))
        """
        self.num_levels = num_levels
        self.state_dims = state_dims
        self.observation_dim = observation_dim
        self.batch_size = batch_size
        self.config = config or {}

        # Initialize belief states with batch dimension
        self.beliefs: List[BeliefState] = []
        for dim in state_dims:
            self.beliefs.append(
                BeliefState(
                    mean=np.zeros((batch_size, dim)),
                    covariance=np.tile(np.eye(dim), (batch_size, 1, 1)),
                    precision=np.ones(batch_size),
                    prediction=np.zeros((batch_size, dim)),
                    prediction_error=np.zeros((batch_size, dim)),
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
        """Reset beliefs for all agents to initial state."""
        for belief in self.beliefs:
            belief.mean.fill(0.0)
            dim = belief.mean.shape[1]
            belief.covariance = np.tile(np.eye(dim), (self.batch_size, 1, 1))
            belief.precision.fill(1.0)
            belief.prediction.fill(0.0)
            belief.prediction_error.fill(0.0)

    def _layer_norm(self, x: FloatArray, eps: float = 1e-6) -> FloatArray:
        """Apply optimized layer normalization across the feature dimension."""
        # Use variance for one-pass calculation efficiency if in 2D/3D
        if x.ndim == 1:
            mu = x.mean()
            # ddof=0 for consistency with nn.LayerNorm
            var = x.var()
            return (x - mu) / np.sqrt(var + eps)

        # Normalize over feature dimension (last) for batch processing
        mu = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return (x - mu) / np.sqrt(var + eps)

    def _variational_dropout(self, x: FloatArray, p: float = 0.1) -> FloatArray:
        """Apply variational dropout for regularization."""
        mask = np.random.binomial(1, 1 - p, size=x.shape)
        return x * mask / (1 - p)

    def update(self, observation: FloatArray, dt: float = 0.001) -> Tuple[List[BeliefState], float]:
        """
        Update beliefs using vectorized variational message passing.

        Runs inference for the entire batch of agents simultaneously.

        Parameters
        ----------
        observation : np.ndarray
            Sensory observation matrix of shape (batch_size, observation_dim)
        dt : float, default=0.001
            Time step for belief integration in seconds

        Returns
        -------
        beliefs : List[BeliefState]
            Updated belief states for all agents
        free_energy : float
            Total variational free energy (averaged across batch)

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
        if observation.ndim == 1:
            observation = observation.reshape(1, -1)

        InputValidator.validate_array(
            observation, "observation", expected_shape=(self.batch_size, self.observation_dim)
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

            current_belief_dim = self.beliefs[level].mean.shape[1]
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
            else:
                # Project error from level below to current level's dimension
                error_below_raw = self.beliefs[level - 1].prediction_error
                target_dim = self.beliefs[level].mean.shape[1]
                source_dim = error_below_raw.shape[1]

                if target_dim != source_dim:
                    error_below = self._project_up(level - 1, error_below_raw)
                else:
                    error_below = error_below_raw

            # Precision-weighted error from above
            if level < self.num_levels - 1:
                # Project error from level above to current level's dimension
                error_above_raw = self.beliefs[level + 1].prediction_error
                target_dim = self.beliefs[level].mean.shape[1]
                source_dim = error_above_raw.shape[1]

                if target_dim != source_dim:
                    error_above = self._map_down(level + 1, error_above_raw)
                else:
                    error_above = error_above_raw
            else:
                # Top level has no error from above
                error_above = np.zeros_like(self.beliefs[level].mean)

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

            # Vectorized precision weighting: (B, D) * (B, 1) or (B,) broadcasted
            # We ensure precision has shape (B, 1) for clean broadcasting
            p_below = self.beliefs[level == 0 and 0 or level - 1].precision.reshape(-1, 1)
            p_above = (
                self.beliefs[level + 1].precision.reshape(-1, 1)
                if level < self.num_levels - 1
                else 0.0
            )

            update = self.learning_rate * (p_below * error_below - p_above * error_above)

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
            # Estimate variance from squared prediction errors for each agent: (B, D) -> (B,)
            error_variance = np.mean(self.beliefs[level].prediction_error ** 2, axis=1) + 1e-6

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
            # old: (B,), new_precision: (B,)
            self.beliefs[level].precision = (1 - alpha) * old + alpha * new_precision

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

                    # Compute gradient: average outer product across batch
                    # (B, D_target, 1) @ (B, 1, D_source) -> (B, D_target, D_source) -> Mean over B
                    gradient = np.mean(
                        np.einsum("bi,bj->bij", error, below_state),
                        axis=0,
                    )

                    # Scale learning rate by timestep
                    effective_lr = self.projection_learning_rate * dt * 1000.0

                    # Update projection matrix
                    self._projection_cache[key] = projection_matrix - effective_lr * gradient

                    # Re-orthogonalize to maintain numerical stability
                    updated_matrix = self._projection_cache[key]
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

                # Robustness check: avoid numerical instability from SVD edge cases
                if not np.all(np.isfinite(projection_matrix)):
                    projection_matrix = np.random.standard_normal((target_dim, source_dim))
                    q, _ = np.linalg.qr(projection_matrix.T)
                    projection_matrix = q.T[:target_dim, :source_dim]

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
        target_dim = self.beliefs[from_level - 1].mean.shape[1]
        source_dim = state.shape[1]

        # Get projection matrix from cache (already orthonormal — do NOT normalise it)
        projection_matrix = self._get_projection_matrix(from_level, target_dim, source_dim)

        # Normalise the input state vector only
        state = self._layer_norm(state)

        # Thread-safe matrix multiplication using the shared instance-level lock
        try:
            with self._cache_lock:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    # Vectorized matmul: (D_target, D_source) @ (B, D_source).T -> (D_target, B) -> (B, D_target)
                    result = (projection_matrix @ state.T).T
        except (FloatingPointError, ValueError):
            logger.warning("_map_down: matmul failed at level %d; returning zeros.", from_level)
            result = np.zeros((self.batch_size, target_dim))

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

        target_dim = self.beliefs[from_level + 1].mean.shape[1]
        source_dim = state.shape[1]

        # Get projection matrix from cache (already orthonormal — do NOT normalise it)
        projection_matrix = self._get_projection_matrix(from_level + 1, target_dim, source_dim)

        # Normalise and regularise the input state vector only
        state = self._variational_dropout(self._layer_norm(state), p=0.05)

        # Thread-safe matrix multiplication using the shared instance-level lock
        try:
            with self._cache_lock:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    # Vectorized matmul: (B, D_target)
                    result = (projection_matrix @ state.T).T
        except (FloatingPointError, ValueError):
            logger.warning("_project_up: matmul failed at level %d; returning zeros.", from_level)
            result = np.zeros((self.batch_size, target_dim))

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
        # Total FE averaged across batch
        total_fe = 0.0

        # Sensory level - error: (B, D)
        error = observation - self.beliefs[0].prediction
        # Compute mean squared error weighted by precision for each agent
        fe_batch = 0.5 * self.beliefs[0].precision * np.sum(error**2, axis=1)
        total_fe += np.mean(fe_batch)

        # Higher levels
        for level in range(1, self.num_levels):
            error = self.beliefs[level].prediction_error
            fe_batch = 0.5 * self.beliefs[level].precision * np.sum(error**2, axis=1)
            total_fe += np.mean(fe_batch)

        return float(total_fe)


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
        self.batch_size = config.get("system", {}).get("batch_size", 1)

        state_dims = [lc["nodes"] for lc in level_configs]
        observation_dim = state_dims[0]  # Sensory level

        # Initialize hierarchical filter
        self.filter = HierarchicalGaussianFilter(
            num_levels=num_levels,
            state_dims=state_dims,
            observation_dim=observation_dim,
            batch_size=self.batch_size,
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
        Execute single synchronous step of active inference loop.

        Supports multi-modal input and temporal orchestration.
        For non-blocking behaviour in an async event loop use
        :meth:`async_step` instead.

        Parameters
        ----------
        observation : np.ndarray or dict
            Sensory input – either a vector (batch_size, D) or a dict of
            modality arrays passed to the multi-modal fusion layer.
        available_actions : list of np.ndarray, optional
            Candidate action vectors evaluated by the motor planner.

        Returns
        -------
        action : np.ndarray
            Selected motor command.
        info : dict
            Diagnostic payload: ``free_energy``, ``beliefs``, ``planning``,
            ``temporal``, ``precisions``, ``prediction_errors``.
        """
        # 1. Update temporal dynamics
        temporal_info = self.temporal_dynamics.update(self.timestep)

        # 2. Multi-modal fusion
        if isinstance(observation, dict):
            fused_observation = self.input_layer.fuse(observation)
        else:
            fused_observation = observation
            if fused_observation.ndim == 1:
                fused_observation = fused_observation.reshape(1, -1)

        # Project observation to match filter's expected dimension if needed
        obs_dim = fused_observation.shape[1]
        expected_dim = self.filter.observation_dim
        if obs_dim != expected_dim:
            if obs_dim > expected_dim:
                fused_observation = fused_observation[:, :expected_dim]
            else:
                padded = np.zeros((fused_observation.shape[0], expected_dim))
                padded[:, :obs_dim] = fused_observation
                fused_observation = padded

        # 3. Apply phase-dependent gain modulation (Alpha/Gamma PAC)
        gain = self.temporal_dynamics.get_gain_modulation("alpha")
        fused_observation = fused_observation * gain  # avoid in-place to keep gradient-safe

        # 4. Perceptual inference (heavy compute – HGF matrix ops)
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

    async def async_step(
        self,
        observation: Union[FloatArray, Dict[str, FloatArray]],
        available_actions: Optional[List[FloatArray]] = None,
    ) -> Tuple[FloatArray, Dict[str, Any]]:
        """
        Non-blocking coroutine variant of :meth:`step`.

        Offloads the heavy HGF ``filter.update()`` to a worker thread via
        ``asyncio.to_thread``.  The event loop remains responsive during
        the matrix multiplications.

        All other logic (temporal dynamics, gain modulation, motor planning)
        runs synchronously on the calling coroutine because it is cheap
        relative to the HGF computation.

        Parameters
        ----------
        observation : np.ndarray or dict
            Same semantics as :meth:`step`.
        available_actions : list of np.ndarray, optional
            Same semantics as :meth:`step`.

        Returns
        -------
        action : np.ndarray
        info : dict
        """
        # 1. Temporal dynamics (fast – keeps on the event loop coroutine)
        temporal_info = self.temporal_dynamics.update(self.timestep)

        # 2. Multi-modal fusion (cheap)
        if isinstance(observation, dict):
            fused_observation = self.input_layer.fuse(observation)
        else:
            fused_observation = observation
            if fused_observation.ndim == 1:
                fused_observation = fused_observation.reshape(1, -1)

        # 3. Gain modulation
        gain = self.temporal_dynamics.get_gain_modulation("alpha")
        fused_observation = fused_observation * gain

        # 4. Heavy HGF inference – run in thread so event loop stays alive
        beliefs, free_energy = await asyncio.to_thread(
            self.filter.update, fused_observation, self.timestep
        )

        # 5. Motor planning (fast)
        action, planning_info = self.motor_planner.plan(beliefs, available_actions)

        self.time += self.timestep

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

    # ------------------------------------------------------------------
    # Vectorised multi-agent helper
    # ------------------------------------------------------------------

    def vectorized_batch_step(
        self,
        observations: FloatArray,
        available_actions: Optional[List[FloatArray]] = None,
    ) -> Tuple[FloatArray, Dict[str, Any]]:
        """
        Run one active-inference step for a *batch* of agents.

        Requires ``observations.shape == (batch_size, observation_dim)``.
        All agents share the same HGF, so the computation cost is
        O(batch_size · D²) – identical to :meth:`step` when
        ``batch_size == 1``.  This makes it dramatically more efficient
        than looping over individual :meth:`step` calls.

        Parameters
        ----------
        observations : np.ndarray, shape (batch_size, observation_dim)
            One observation per agent.
        available_actions : list of np.ndarray, optional
            Shared or per-batch action candidates.

        Returns
        -------
        actions : np.ndarray, shape (batch_size, action_dim)
            One action per agent (broadcast from the scalar planner).
        info : dict
            Batch-level diagnostics. Per-agent free energies available
            under ``info['per_agent_free_energy']``.

        Raises
        ------
        ValueError
            If ``observations`` batch dimension does not match engine
            ``batch_size``.
        """
        B = observations.shape[0] if observations.ndim > 1 else 1
        if B != self.batch_size:
            raise ValueError(
                f"vectorized_batch_step: observations batch dim {B} != "
                f"engine batch_size {self.batch_size}."
            )

        action, info = self.step(observations, available_actions)

        # Compute per-agent free energy from the shared belief state
        beliefs = info["beliefs"]
        per_agent_fe = np.zeros(B)
        for belief in beliefs:
            if belief.prediction_error.ndim == 2:
                err_sq = np.sum(belief.prediction_error**2, axis=1)  # (B,)
                prec = (
                    belief.precision
                    if belief.precision.ndim > 0
                    else np.full(B, float(belief.precision))
                )
                per_agent_fe += 0.5 * prec * err_sq
            else:
                per_agent_fe += (
                    0.5 * float(belief.precision) * float(np.sum(belief.prediction_error**2))
                )

        info["per_agent_free_energy"] = per_agent_fe

        # Broadcast single action to all agents if needed
        if action.ndim == 1:
            actions = np.tile(action, (B, 1))
        else:
            actions = action

        return actions, info

    def reset(self) -> None:
        """Reset the engine and its components."""
        self.filter.reset_beliefs()
        self.motor_planner.reset()
        self.temporal_dynamics.reset()
        self.time = 0.0
