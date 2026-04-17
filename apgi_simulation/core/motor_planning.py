"""
Hierarchical Motor Planning Module

Implements policy generation and selection based on Expected Free Energy (EFE)
minimization.  A principled generative likelihood model ``p(o|s)`` is built
from deterministic orthonormal projections so that predicted observations
embed real information from the latent belief state, making the EFE signal
meaningful for goal-directed behaviour.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from apgi_simulation.core.free_energy import FreeEnergyCalculator
from apgi_simulation.types import ConfigDict, FloatArray

logger = logging.getLogger(__name__)


class GenerativeLikelihood:
    """
    Minimal generative likelihood model implementing ``p(o|s)``.

    Maps from the top-level latent state ``s ∈ ℝ^{d_s}`` to a probability
    distribution over observations ``o ∈ ℝ^{d_o}`` via:

    * **Transition**: ``s_{t+1} = tanh(B @ s_t + C @ a)``
    * **Observation**: ``ô_t = softmax(A @ s_t)``

    All three weight matrices ``A``, ``B``, ``C`` are initialised as
    orthonormal (or pseudo-orthonormal) projections via SVD with a fixed seed,
    guaranteeing:
    - Unity gain — no information amplification across the mapping.
    - Determinism — identical results for identical seeds/configurations.
    - Bounded outputs — combined with ``tanh`` nonlinearity.

    Parameters
    ----------
    state_dim : int
        Dimensionality of the top-level latent state.
    obs_dim : int
        Dimensionality of the observation / preference space.
    action_dim : int
        Dimensionality of the action vector.
    seed : int, optional
        Seed for deterministic weight initialisation.
    """

    def __init__(
        self,
        state_dim: int,
        obs_dim: int,
        action_dim: int,
        seed: int = 0,
    ) -> None:
        rng = np.random.default_rng(seed)

        # Orthonormal likelihood matrix A: (obs_dim, state_dim)
        raw_A = rng.standard_normal((obs_dim, state_dim))
        U_a, _, Vt_a = np.linalg.svd(raw_A, full_matrices=False)
        self.A: FloatArray = U_a @ Vt_a

        # Orthonormal transition matrix B: (state_dim, state_dim)
        raw_B = rng.standard_normal((state_dim, state_dim))
        U_b, _, Vt_b = np.linalg.svd(raw_B, full_matrices=False)
        self.B: FloatArray = U_b @ Vt_b

        # Pseudo-orthonormal action gain matrix C: (state_dim, action_dim)
        raw_C = rng.standard_normal((state_dim, action_dim))
        U_c, _, Vt_c = np.linalg.svd(raw_C, full_matrices=False)
        self.C: FloatArray = U_c @ Vt_c

        self.state_dim = state_dim
        self.obs_dim = obs_dim
        self.action_dim = action_dim

    def rollout(
        self,
        initial_state: FloatArray,
        action: FloatArray,
        horizon: int,
    ) -> Tuple[List[FloatArray], FloatArray]:
        """
        Roll-out latent states and predicted observations for a batch of actions.

        Parameters
        ----------
        initial_state : np.ndarray, shape (batch_size, state_dim)
            Current top-level belief means for each agent.
        action : np.ndarray, shape (batch_size, action_dim)
            Candidate action vectors for each agent.
        horizon : int
            Number of steps to simulate ahead.

        Returns
        -------
        predicted_states : list of np.ndarray
            Latent state sequence s_1, …, s_T (each element (batch_size, state_dim)).
        predicted_observations : np.ndarray, shape (batch_size, horizon, obs_dim)
            Probability distributions ô_1, …, ô_T.
        """
        batch_size = initial_state.shape[0]

        # Ensure action has correct dimension
        if action.ndim == 1:
            action = action.reshape(1, -1)

        # Pad or truncate action to match expected action_dim
        action_padded = np.zeros((batch_size, self.action_dim))
        cols = min(action.shape[1], self.action_dim)
        action_padded[:, :cols] = action[:, :cols]

        state = initial_state.copy()
        predicted_states: List[FloatArray] = []
        predicted_obs_list: List[FloatArray] = []

        # Vectorized transition part: (B, action_dim) @ (state_dim, action_dim).T -> (B, state_dim)
        C_a = (self.C @ action_padded.T).T

        for _ in range(horizon):
            # State transition: (state_dim, state_dim) @ (B, state_dim).T -> (state_dim, B) -> (B, state_dim)
            state = np.tanh((self.B @ state.T).T + C_a)
            predicted_states.append(state.copy())

            # Likelihood: softmax( (obs_dim, state_dim) @ (B, state_dim).T )
            logits = (self.A @ state.T).T
            logits -= logits.max(axis=1, keepdims=True)
            probs = np.exp(logits)
            probs /= probs.sum(axis=1, keepdims=True) + 1e-10
            predicted_obs_list.append(probs)

        if predicted_obs_list:
            # (H, B, D) -> (B, H, D)
            predicted_observations = np.transpose(np.stack(predicted_obs_list), (1, 0, 2))
        else:
            predicted_observations = np.empty((batch_size, 0, self.obs_dim), dtype=np.float64)

        return predicted_states, predicted_observations


class MotorPlanner:
    """
    Hierarchical Motor Planner for Active Inference.

    Generates and evaluates action policies (sequences of actions) by
    minimizing Expected Free Energy (G). Balances epistemic value
    (information gain / exploration) with pragmatic value (prior
    preferences / exploitation).

    The observation predictions used in EFE computation are produced by
    :class:`GenerativeLikelihood`, which maps latent belief states to
    structured probability distributions — replacing the previous
    noise-based placeholder that rendered EFE numerically uninformative.

    Parameters
    ----------
    config : dict
        Configuration dictionary.
    """

    def __init__(self, config: ConfigDict) -> None:
        """
        Initialize the Motor Planner.

        Parameters
        ----------
        config : dict
            System configuration.  Reads from:
            * ``active_inference.planning.horizon``  (default 3)
            * ``active_inference.planning.num_policies``  (default 10)
            * ``active_inference.planning.precision``  (default 1.0)
            * ``system.action_dim``  (default 10)
            * ``system.obs_dim``  (default equals ``action_dim``)
            * ``system.random_seed``  (default 0)
        """
        self.config = config
        self.fe_calc = FreeEnergyCalculator(config)

        planning_config = config.get("active_inference", {}).get("planning", {})
        self.horizon = planning_config.get("horizon", 3)
        self.num_policies = planning_config.get("num_policies", 10)
        self.gamma = planning_config.get("precision", 1.0)  # inverse temperature

        # Action and observation space dimensions
        self.action_dim = config.get("system", {}).get("action_dim", 10)
        self.obs_dim = config.get("system", {}).get("obs_dim", self.action_dim)

        # Seeded RNG for reproducible candidate action sampling
        seed = int(config.get("system", {}).get("random_seed", 0))
        self._rng = np.random.default_rng(seed)

        # Default uniform preferences (normalised when used)
        self.preferences: FloatArray = np.ones(self.obs_dim) / self.obs_dim

        # Generative model is lazily created on first plan() call so that we
        # know the top-level latent state dimension from the belief states.
        self._generative_model: Optional[GenerativeLikelihood] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_preferences(self, preferences: FloatArray) -> None:
        """
        Set prior preferences over observations/outcomes.

        Parameters
        ----------
        preferences : np.ndarray
            Target observation distribution (goal state).
            Must be non-negative; normalised internally.
        """
        self.preferences = preferences

    def plan(
        self, current_beliefs: List[Any], available_actions: Optional[List[FloatArray]] = None
    ) -> Tuple[FloatArray, Dict[str, Any]]:
        """
        Select the best actions for a batch of agents.

        Evaluates multiple candidates for ALL agents in parallel using
        broadcasting and vectorized rollouts.
        """
        top_belief = current_beliefs[-1]
        batch_size, state_dim = top_belief.mean.shape
        self._ensure_generative_model(state_dim)

        if available_actions is None:
            # Sample independent candidates for each agent: (num_policies, batch_size, action_dim)
            candidates = self._rng.standard_normal((self.num_policies, batch_size, self.action_dim))
        elif len(available_actions) == 0:
            # No available actions, return zero action
            return np.zeros((batch_size, self.action_dim), dtype=np.float64), {"efe_components": {}}
        else:
            # Assume available_actions is a list of num_policies arrays, each (batch_size, D)
            candidates = np.stack(available_actions)

        # Normalised preference distribution (proper probability distribution)
        pref = np.clip(self.preferences, 1e-10, None)
        pref = pref / (pref.sum() + 1e-10)

        best_actions = np.zeros((batch_size, self.action_dim))

        assert self._generative_model is not None

        # We evaluate each 'policy candidate index' across all agents
        # Index 0 evaluated for all agents, Index 1 for all agents...
        # This allows vectorizing the ROLLOUT.

        per_policy_batch_efes = []  # List of (batch_size,)

        num_candidates = candidates.shape[0]
        for p_idx in range(num_candidates):
            action_batch = candidates[p_idx]  # (batch_size, action_dim)

            # Vectorized rollout
            predicted_states, predicted_observations = self._generative_model.rollout(
                initial_state=top_belief.mean,
                action=action_batch,
                horizon=self.horizon,
            )

            # state_uncertainty: (batch_size, horizon, state_dim)
            # top_belief.precision: (batch_size,)
            prec = top_belief.precision.reshape(-1, 1, 1) + 1e-10
            state_uncertainty = np.ones((batch_size, self.horizon, state_dim)) / prec

            # Calculate EFE for each agent for this policy index
            # EFE computation might need vectorization too
            efes = []
            for b in range(batch_size):
                # We can vectorize this further if compute_expected_free_energy supports it
                efe, _ = self.fe_calc.compute_expected_free_energy(
                    policy=action_batch[b],
                    predicted_states=[s[b] for s in predicted_states],
                    predicted_observations=predicted_observations[b],
                    preferences=pref,
                    state_uncertainty=state_uncertainty[b],
                    horizon=self.horizon,
                )
                efes.append(efe)
            per_policy_batch_efes.append(np.array(efes))

        # (num_policies, batch_size)
        policy_efes_matrix = np.stack(per_policy_batch_efes)

        # Softmax over policies for each agent
        # min_efes: (batch_size,)
        min_efes = np.min(policy_efes_matrix, axis=0)
        shifted_efes = -self.gamma * (policy_efes_matrix - min_efes)
        probs = np.exp(shifted_efes)
        probs /= probs.sum(axis=0) + 1e-10  # (num_policies, batch_size)

        # Best action index for each agent
        best_indices = np.argmax(probs, axis=0)  # (batch_size,)

        for b in range(batch_size):
            best_actions[b] = candidates[best_indices[b], b]

        planning_info = {
            "best_indices": best_indices.tolist(),
            "avg_efe": float(np.mean(policy_efes_matrix)),
            "batch_size": batch_size,
        }

        # For backward compatibility if batch_size=1, return squeeze
        if batch_size == 1:
            return best_actions[0], planning_info
        return best_actions, planning_info

    def reset(self) -> None:
        """Reset planner state.  Generative model weights are retained."""
        pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_generative_model(self, state_dim: int) -> None:
        """
        Lazily create or replace the :class:`GenerativeLikelihood` when the
        top-level state dimension is first known or changes.

        Parameters
        ----------
        state_dim : int
            Dimensionality of the top-level latent belief state.
        """
        if self._generative_model is None or self._generative_model.state_dim != state_dim:
            seed = int(self.config.get("system", {}).get("random_seed", 0))
            self._generative_model = GenerativeLikelihood(
                state_dim=state_dim,
                obs_dim=self.obs_dim,
                action_dim=self.action_dim,
                seed=seed,
            )
            logger.debug(
                "GenerativeLikelihood initialised: state_dim=%d obs_dim=%d action_dim=%d",
                state_dim,
                self.obs_dim,
                self.action_dim,
            )
