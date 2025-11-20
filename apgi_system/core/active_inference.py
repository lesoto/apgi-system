"""
Active Inference Engine

Implements the core active inference loop using variational message passing
and hierarchical Bayesian filtering.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from apgi_system.core.free_energy import FreeEnergyCalculator


@dataclass
class BeliefState:
    """Represents beliefs at a single hierarchical level."""
    mean: np.ndarray  # Posterior mean
    covariance: np.ndarray  # Posterior covariance
    precision: float  # Precision (inverse variance)
    prediction: np.ndarray  # Predicted observation/state
    prediction_error: np.ndarray  # Prediction error


class HierarchicalGaussianFilter:
    """
    Hierarchical Gaussian filtering for approximate Bayesian inference.

    Implements predictive coding with precision-weighted prediction errors
    propagating up the hierarchy and predictions propagating down.
    """

    def __init__(
        self,
        num_levels: int,
        state_dims: List[int],
        observation_dim: int,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize hierarchical filter.

        Args:
            num_levels: Number of hierarchical levels
            state_dims: Dimensionality at each level
            observation_dim: Dimensionality of observations
            config: Configuration dictionary
        """
        self.num_levels = num_levels
        self.state_dims = state_dims
        self.observation_dim = observation_dim
        self.config = config or {}

        # Initialize belief states
        self.beliefs: List[BeliefState] = []
        for dim in state_dims:
            self.beliefs.append(BeliefState(
                mean=np.zeros(dim),
                covariance=np.eye(dim),
                precision=1.0,
                prediction=np.zeros(dim),
                prediction_error=np.zeros(dim)
            ))

        # Learning parameters
        self.learning_rate = self.config.get('learning_rate', 0.01)

        # Precision dynamics
        self.precision_min = self.config.get('precision_range', [0.1, 10.0])[0]
        self.precision_max = self.config.get('precision_range', [0.1, 10.0])[1]

    def update(
        self,
        observation: np.ndarray,
        action: Optional[np.ndarray] = None,
        dt: float = 0.001
    ) -> Tuple[List[BeliefState], float]:
        """
        Update beliefs using variational message passing.

        Args:
            observation: Sensory observation
            action: Current action (optional)
            dt: Time step

        Returns:
            Updated belief states and total free energy
        """
        # Bottom-up pass: compute prediction errors
        self._bottom_up_pass(observation)

        # Top-down pass: update beliefs
        self._top_down_pass(dt)

        # Update precisions based on prediction error statistics
        self._update_precisions()

        # Compute total free energy
        total_fe = self._compute_total_free_energy(observation)

        return self.beliefs, total_fe

    def _bottom_up_pass(self, observation: np.ndarray):
        """
        Bottom-up pass: compute prediction errors at each level.

        Error propagates from sensory level upward.
        """
        # Level 0: sensory prediction error
        self.beliefs[0].prediction_error = observation - self.beliefs[0].prediction

        # Higher levels: state prediction errors
        for level in range(1, self.num_levels):
            # Prediction from level above
            higher_prediction = self._map_down(level, self.beliefs[level].mean)
            # Error is difference from current belief
            self.beliefs[level].prediction_error = \
                self.beliefs[level - 1].mean - higher_prediction

    def _top_down_pass(self, dt: float):
        """
        Top-down pass: update beliefs using precision-weighted errors.

        Beliefs are updated to minimize prediction errors.
        """
        # Update from top to bottom
        for level in range(self.num_levels - 1, -1, -1):
            # Precision-weighted error from below
            if level == 0:
                # Bottom level gets sensory prediction error
                error_below = self.beliefs[0].prediction_error
                precision_below = self.beliefs[0].precision
            else:
                error_below = self.beliefs[level - 1].prediction_error
                precision_below = self.beliefs[level - 1].precision

            # Precision-weighted error from above
            if level < self.num_levels - 1:
                error_above = self.beliefs[level + 1].prediction_error
                precision_above = self.beliefs[level + 1].precision
            else:
                # Top level has no error from above
                error_above = np.zeros_like(self.beliefs[level].mean)
                precision_above = 0.0

            # Update belief mean (gradient descent on free energy)
            # δμ = η * (Π_below * ε_below - Π_above * ε_above)
            update = self.learning_rate * (
                precision_below * error_below[:len(self.beliefs[level].mean)] -
                precision_above * error_above[:len(self.beliefs[level].mean)]
            )

            self.beliefs[level].mean += dt * update

            # Update prediction for next iteration
            self.beliefs[level].prediction = self._generate_prediction(level)

    def _update_precisions(self):
        """
        Update precision estimates based on prediction error statistics.

        Precision ∝ 1 / E[ε^2]
        """
        for level in range(self.num_levels):
            # Estimate variance from squared prediction errors
            error_variance = np.mean(self.beliefs[level].prediction_error ** 2) + 1e-6

            # Update precision (with smoothing)
            new_precision = 1.0 / error_variance
            self.beliefs[level].precision = 0.9 * self.beliefs[level].precision + \
                                           0.1 * new_precision

            # Clamp to valid range
            self.beliefs[level].precision = np.clip(
                self.beliefs[level].precision,
                self.precision_min,
                self.precision_max
            )

    def _generate_prediction(self, level: int) -> np.ndarray:
        """Generate prediction at a given level from belief above."""
        if level < self.num_levels - 1:
            return self._map_down(level + 1, self.beliefs[level + 1].mean)
        else:
            # Top level predicts itself (prior)
            return self.beliefs[level].mean

    def _map_down(self, from_level: int, state: np.ndarray) -> np.ndarray:
        """
        Map state representation down one level.

        Simple linear mapping for now. Can be made nonlinear.
        """
        target_dim = self.beliefs[from_level - 1].mean.shape[0]
        source_dim = state.shape[0]

        # Simple projection matrix (could be learned)
        if not hasattr(self, '_projection_matrices'):
            self._projection_matrices = {}

        key = (from_level, target_dim, source_dim)
        if key not in self._projection_matrices:
            # Initialize random projection matrix
            self._projection_matrices[key] = np.random.randn(target_dim, source_dim) * 0.1

        return self._projection_matrices[key] @ state

    def _compute_total_free_energy(self, observation: np.ndarray) -> float:
        """Compute total free energy across hierarchy."""
        total_fe = 0.0

        # Sensory level
        error = observation - self.beliefs[0].prediction
        total_fe += 0.5 * self.beliefs[0].precision * np.sum(error ** 2)

        # Higher levels
        for level in range(1, self.num_levels):
            error = self.beliefs[level].prediction_error
            total_fe += 0.5 * self.beliefs[level].precision * np.sum(error ** 2)

        return total_fe


class ActiveInferenceEngine:
    """
    Main active inference engine coordinating perception and action.

    Integrates:
    - Hierarchical Gaussian filtering for perception
    - Expected free energy minimization for action selection
    - Precision weighting for attention and uncertainty
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize active inference engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Extract hierarchy configuration
        hierarchy_config = config.get('hierarchy', {})
        num_levels = hierarchy_config.get('num_levels', 4)
        level_configs = hierarchy_config.get('level_configs', [])

        state_dims = [lc['nodes'] for lc in level_configs]
        observation_dim = state_dims[0]  # Sensory level

        # Initialize hierarchical filter
        self.filter = HierarchicalGaussianFilter(
            num_levels=num_levels,
            state_dims=state_dims,
            observation_dim=observation_dim,
            config=config.get('active_inference', {})
        )

        # Initialize free energy calculator
        self.fe_calc = FreeEnergyCalculator(config)

        # Policy evaluation
        self.num_policies = config.get('num_policies', 10)
        self.planning_horizon = config.get('planning_horizon', 3)

        # State tracking
        self.time = 0.0
        self.timestep = config.get('system', {}).get('timestep_ms', 1.0) / 1000.0

    def step(
        self,
        observation: np.ndarray,
        available_actions: Optional[List[np.ndarray]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Single step of active inference.

        1. Update beliefs (perception)
        2. Evaluate policies (planning)
        3. Select action (decision)

        Args:
            observation: Current sensory input
            available_actions: List of possible actions

        Returns:
            selected_action: Chosen action
            info: Dictionary with diagnostics
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
            'time': self.time,
            'free_energy': free_energy,
            'beliefs': beliefs,
            'efe_components': efe_components,
            'precisions': [b.precision for b in beliefs],
            'prediction_errors': [b.prediction_error for b in beliefs]
        }

        return action, info

    def _select_action(
        self,
        beliefs: List[BeliefState],
        available_actions: List[np.ndarray]
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Select action by minimizing expected free energy.

        Args:
            beliefs: Current belief states
            available_actions: Available actions

        Returns:
            Best action and EFE components
        """
        best_action = available_actions[0]
        best_efe = float('inf')
        best_components = {}

        for action in available_actions:
            # Simulate future under this action (simplified)
            predicted_states = self._simulate_future(beliefs, action)
            predicted_obs = predicted_states[0]  # Simplified

            # Preferences (could be learned or specified)
            preferences = np.ones_like(predicted_obs) / len(predicted_obs)

            # Uncertainty
            state_uncertainty = np.array([b.covariance.diagonal()
                                         for b in beliefs])

            # Compute expected free energy
            efe, components = self.fe_calc.compute_expected_free_energy(
                policy=action,
                predicted_states=predicted_states,
                predicted_observations=np.array([predicted_obs]),
                preferences=preferences,
                state_uncertainty=state_uncertainty,
                horizon=self.planning_horizon
            )

            if efe < best_efe:
                best_efe = efe
                best_action = action
                best_components = components

        return best_action, best_components

    def _simulate_future(
        self,
        beliefs: List[BeliefState],
        action: np.ndarray,
        horizon: Optional[int] = None
    ) -> List[np.ndarray]:
        """
        Simulate future states under a policy.

        Simplified forward model for now.
        """
        if horizon is None:
            horizon = self.planning_horizon

        future_states = []
        current_state = beliefs[0].mean.copy()

        for _ in range(horizon):
            # Simple dynamics: s_{t+1} = s_t + action + noise
            # Pad action to match state dimensionality
            action_padded = np.zeros_like(current_state)
            action_padded[:len(action)] = action
            current_state = current_state + 0.1 * action_padded
            future_states.append(current_state.copy())

        return future_states

    def reset(self):
        """Reset the engine to initial state."""
        for belief in self.filter.beliefs:
            belief.mean = np.zeros_like(belief.mean)
            belief.covariance = np.eye(len(belief.mean))
            belief.precision = 1.0
            belief.prediction = np.zeros_like(belief.prediction)
            belief.prediction_error = np.zeros_like(belief.prediction_error)

        self.time = 0.0
