"""
Active Inference Engine

Implements the core active inference loop using variational message passing
and hierarchical Bayesian filtering.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
from collections import deque
import threading

from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.validation import InputValidator
from apgi_system.types import FloatArray, ConfigDict


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

        # Precision dynamics
        self.precision_min = self.config.get("precision_range", [0.1, 10.0])[0]
        self.precision_max = self.config.get("precision_range", [0.1, 10.0])[1]

        # Projection matrix cache with LRU eviction
        self._projection_cache_max_size = self.config.get("projection_cache_size", 100)
        self._projection_cache = {}
        self._cache_access_order = deque()  # Track access order for LRU (O(1) operations)
        self._cache_lock = threading.Lock()  # Thread safety for cache access

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
        self._update_precisions()

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
            # Prediction from level above
            higher_prediction = self._map_down(level, self.beliefs[level].mean)
            # Error is difference from current belief
            self.beliefs[level].prediction_error = self.beliefs[level - 1].mean - higher_prediction

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
                raise ValueError(
                    f"Shape mismatch at level {level}: "
                    f"belief mean shape {belief_shape} vs error_below shape {error_below.shape}"
                )
            if error_above.shape != belief_shape:
                raise ValueError(
                    f"Shape mismatch at level {level}: "
                    f"belief mean shape {belief_shape} vs error_above shape {error_above.shape}"
                )

            update = self.learning_rate * (
                precision_below * error_below - precision_above * error_above
            )

            self.beliefs[level].mean += dt * update

            # Update prediction for next iteration
            self.beliefs[level].prediction = self._generate_prediction(level)

    def _update_precisions(self) -> None:
        """
        Update precision estimates based on prediction error statistics.

        Precision is inversely proportional to prediction error variance,
        implementing adaptive gain control. High precision amplifies prediction
        errors, while low precision attenuates them.

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
            self.beliefs[level].precision = (
                0.9 * self.beliefs[level].precision + 0.1 * new_precision
            )

            # Clamp to valid range
            self.beliefs[level].precision = np.clip(
                self.beliefs[level].precision, self.precision_min, self.precision_max
            )

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
    ) -> np.ndarray:
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
                # Same dimension: use identity with small noise
                projection_matrix = (
                    np.eye(target_dim) + np.random.randn(target_dim, source_dim) * 0.01
                )
            else:
                # Different dimensions: use truncated normal initialization
                projection_matrix = np.random.randn(target_dim, source_dim) * 0.1
                # Ensure finite values
                projection_matrix = np.nan_to_num(
                    projection_matrix, nan=0.0, posinf=1.0, neginf=-1.0
                )
                # Add small identity component for stability
                min_dim = min(target_dim, source_dim)
                projection_matrix[:min_dim, :min_dim] += np.eye(min_dim) * 0.1

            # Add to cache
            self._projection_cache[key] = projection_matrix
            self._cache_access_order.append(key)

            # Evict oldest if cache is full
            if len(self._projection_cache) > self._projection_cache_max_size:
                oldest_key = self._cache_access_order.popleft()  # O(1) operation with deque
                del self._projection_cache[oldest_key]

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
        """
        target_dim = self.beliefs[from_level - 1].mean.shape[0]
        source_dim = state.shape[0]

        # Get projection matrix from cache
        projection_matrix = self._get_projection_matrix(from_level, target_dim, source_dim)

        # Ensure numerical stability
        projection_matrix = np.nan_to_num(projection_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
        state = np.nan_to_num(state, nan=0.0, posinf=1.0, neginf=-1.0)

        result = projection_matrix @ state
        return np.nan_to_num(result, nan=0.0, posinf=1.0, neginf=-1.0)

    def _project_up(self, from_level: int, state: FloatArray) -> FloatArray:
        """
        Map state representation up one level in the hierarchy.

        Args:
            from_level: Source level (lower in hierarchy)
            state: State vector to map up

        Returns:
            Mapped state vector at higher level
        """
        if from_level >= self.num_levels - 1:
            # Already at top level
            return state

        target_dim = self.beliefs[from_level + 1].mean.shape[0]
        source_dim = state.shape[0]

        # Get projection matrix from cache
        projection_matrix = self._get_projection_matrix(from_level + 1, target_dim, source_dim)

        # Ensure numerical stability with enhanced checks
        projection_matrix = np.nan_to_num(projection_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
        state = np.nan_to_num(state, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Gradient clipping to prevent overflow
        projection_matrix = np.clip(projection_matrix, -100, 100)
        state = np.clip(state, -100, 100)
        
        # Check for divide by zero conditions
        if np.any(np.abs(projection_matrix) < 1e-10):
            projection_matrix = np.where(np.abs(projection_matrix) < 1e-10, 
                                   np.sign(projection_matrix) * 1e-10, projection_matrix)

        result = projection_matrix @ state
        
        # Final result stabilization
        result = np.nan_to_num(result, nan=0.0, posinf=1.0, neginf=-1.0)
        result = np.clip(result, -1000, 1000)  # Prevent extreme values
        
        return result

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

        # Policy evaluation
        self.num_policies = config.get("num_policies", 10)
        self.planning_horizon = config.get("planning_horizon", 3)

        # State tracking
        self.time = 0.0
        self.timestep = config.get("system", {}).get("timestep_ms", 1.0) / 1000.0

    def step(
        self, observation: FloatArray, available_actions: Optional[List[FloatArray]] = None
    ) -> Tuple[FloatArray, Dict[str, Any]]:
        """
        Execute single step of active inference loop.

        Performs the complete perception-action cycle:
        1. Perceptual inference: Update beliefs to explain observation
        2. Policy evaluation: Simulate outcomes of available actions
        3. Action selection: Choose action minimizing expected free energy

        Parameters
        ----------
        observation : np.ndarray
            Current sensory observation vector of shape (observation_dim,)
        available_actions : List[np.ndarray], optional
            List of available action vectors. If None or empty, returns null action.

        Returns
        -------
        selected_action : np.ndarray
            Chosen action vector that minimizes expected free energy
        info : Dict[str, Any]
            Diagnostic information containing:
            - 'time': Current simulation time
            - 'free_energy': Variational free energy
            - 'beliefs': Current belief states at all levels
            - 'efe_components': Expected free energy breakdown
            - 'precisions': Precision values at each level
            - 'prediction_errors': Prediction errors at each level

        Notes
        -----
        The action selection implements:
        π* = argmin_π G(π)

        where G(π) is the expected free energy under policy π, balancing
        epistemic value (information gain) and pragmatic value (goal achievement).

        Examples
        --------
        >>> engine = ActiveInferenceEngine(config)
        >>> obs = np.random.randn(256)
        >>> actions = [np.array([0.0]), np.array([1.0]), np.array([-1.0])]
        >>> action, info = engine.step(obs, actions)
        >>> print(f"Selected action: {action}, FE: {info['free_energy']:.2f}")
        """
        # Update perceptual inference
        beliefs, free_energy = self.filter.update(observation, dt=self.timestep)

        # Select action if actions available
        if available_actions is not None and len(available_actions) > 0:
            action, efe_components = self._select_action(beliefs, available_actions)
        else:
            action = np.zeros(1)  # Null action
            efe_components = {}

        # Increment time
        self.time += self.timestep

        # Compile diagnostics
        info = {
            "time": self.time,
            "free_energy": free_energy,
            "beliefs": beliefs,
            "efe_components": efe_components,
            "precisions": [b.precision for b in beliefs],
            "prediction_errors": [b.prediction_error for b in beliefs],
        }

        return action, info

    def _select_action(
        self, beliefs: List[BeliefState], available_actions: List[FloatArray]
    ) -> Tuple[FloatArray, Dict[str, float]]:
        """
        Select action by minimizing expected free energy.

        Evaluates each available action by simulating its expected outcomes
        and computing the expected free energy. Selects the action with
        lowest expected free energy, balancing exploration and exploitation.

        Parameters
        ----------
        beliefs : List[BeliefState]
            Current belief states at all hierarchical levels
        available_actions : List[np.ndarray]
            List of candidate action vectors to evaluate

        Returns
        -------
        best_action : np.ndarray
            Action with minimum expected free energy
        best_components : Dict[str, float]
            Expected free energy components for selected action:
            - 'epistemic_value': Expected information gain
            - 'pragmatic_value': Expected cost/divergence from preferences
            - 'exploration_drive': Magnitude of exploration motivation
            - 'exploitation_drive': Magnitude of exploitation motivation

        Notes
        -----
        Expected free energy decomposes as:
        G(π) = Epistemic Value + Pragmatic Value
             = -E[Information Gain] + E[KL(p(o|π)||p*(o))]

        Lower epistemic value → more exploration
        Lower pragmatic value → better goal achievement
        """
        best_action = available_actions[0]
        best_efe = float("inf")
        best_components = {}

        for action in available_actions:
            # Simulate future under this action (simplified)
            predicted_states = self._simulate_future(beliefs, action)
            # Treat predicted states as predicted observations
            predicted_observations = np.stack(predicted_states)

            # Preferences (could be learned or specified)
            preferences = np.ones_like(predicted_observations[0]) / len(predicted_observations[0])

            # Uncertainty
            level_uncertainties = [
                float(np.mean(np.diag(b.covariance))) if b.covariance.size > 0 else 0.0
                for b in beliefs
            ]

            if not level_uncertainties:
                level_uncertainties = [0.0]

            if self.planning_horizon > 0:
                repeats = max(
                    1,
                    (self.planning_horizon + len(level_uncertainties) - 1)
                    // len(level_uncertainties),
                )
                state_uncertainty = np.tile(level_uncertainties, repeats)[: self.planning_horizon]
            else:
                state_uncertainty = np.array(level_uncertainties)

            # Compute expected free energy
            efe, components = self.fe_calc.compute_expected_free_energy(
                policy=action,
                predicted_states=predicted_states,
                predicted_observations=predicted_observations,
                preferences=preferences,
                state_uncertainty=state_uncertainty,
                horizon=self.planning_horizon,
            )

            if efe < best_efe:
                best_efe = efe
                best_action = action
                best_components = components

        return best_action, best_components

    def _simulate_future(
        self, beliefs: List[BeliefState], action: FloatArray, horizon: Optional[int] = None
    ) -> List[FloatArray]:
        """
        Simulate future states under a policy.

        Uses a forward model to predict how states will evolve under a given
        action sequence. This enables prospective planning and policy evaluation.

        Parameters
        ----------
        beliefs : List[BeliefState]
            Current belief states
        action : np.ndarray
            Action to simulate
        horizon : int, optional
            Number of steps to simulate ahead. If None, uses planning_horizon.

        Returns
        -------
        future_states : List[np.ndarray]
            Predicted state sequence of length horizon

        Notes
        -----
        Current implementation uses simplified linear dynamics:
        s_{t+1} = s_t + α * a + η

        where α is action gain and η is process noise.
        Can be extended to learned nonlinear forward models.
        """
        if horizon is None:
            horizon = self.planning_horizon

        future_states = []
        current_state = beliefs[0].mean.copy()

        for _ in range(horizon):
            # Simple dynamics: s_{t+1} = s_t + action + noise
            # Pad action to match state dimensionality
            action_padded = np.zeros_like(current_state)
            action_padded[: len(action)] = action
            current_state = current_state + 0.1 * action_padded
            future_states.append(current_state.copy())

        return future_states

    def reset(self) -> None:
        """
        Reset the engine to initial state.

        Reinitializes all belief states, clears history, and resets time to zero.
        Useful for starting new simulation runs or experimental trials.

        Notes
        -----
        After reset, all beliefs return to prior distributions with zero mean
        and identity covariance.
        """
        for belief in self.filter.beliefs:
            belief.mean = np.zeros_like(belief.mean)
            belief.covariance = np.eye(len(belief.mean))
            belief.precision = 1.0
            belief.prediction = np.zeros_like(belief.prediction)
            belief.prediction_error = np.zeros_like(belief.prediction_error)

        self.time = 0.0
