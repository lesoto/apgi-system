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

from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.types import ConfigDict, FloatArray

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
    ) -> Tuple[List[FloatArray], np.ndarray]:
        """
        Roll-out latent states and predicted observations for one action.

        Parameters
        ----------
        initial_state : np.ndarray, shape (state_dim,)
            Current top-level belief mean ``μ_top``.
        action : np.ndarray, shape (action_dim,) or smaller
            Candidate action vector.  Padded / truncated to ``action_dim``
            automatically.
        horizon : int
            Number of steps to simulate ahead.

        Returns
        -------
        predicted_states : list of np.ndarray
            Latent state sequence ``s_1, …, s_T`` (length ``horizon``).
        predicted_observations : np.ndarray, shape (horizon, obs_dim)
            Probability distributions ``ô_1, …, ô_T`` from softmax
            ``A @ s_t``.

        Notes
        -----
        Transition:  ``s_{t+1} = tanh(B @ s_t + C @ a)``
        Observation: ``ô_t     = softmax(A @ s_t)``

        The ``tanh`` nonlinearity bounds latent states to ``[-1, 1]``
        preventing unbounded growth over long horizons.
        Softmax ensures predicted observations form a valid distribution.
        """
        # Pad or truncate action to match expected action_dim
        action_padded = np.zeros(self.action_dim)
        action_padded[: min(len(action), self.action_dim)] = action[: self.action_dim]

        state = initial_state.copy()
        predicted_states: List[FloatArray] = []
        predicted_obs_list: List[FloatArray] = []

        C_a = self.C @ action_padded  # precompute; constant across steps

        for _ in range(horizon):
            # State transition: stable tanh dynamics
            state = np.tanh(self.B @ state + C_a)
            predicted_states.append(state.copy())

            # Likelihood: softmax(A @ s_t)
            logits = self.A @ state
            logits -= logits.max()  # numerical stability before exp
            probs = np.exp(logits)
            probs /= probs.sum() + 1e-10
            predicted_obs_list.append(probs)

        # Guard: np.stack raises on an empty sequence; return shaped empty array instead.
        if predicted_obs_list:
            predicted_observations = np.stack(predicted_obs_list)  # (horizon, obs_dim)
        else:
            predicted_observations = np.empty((0, self.obs_dim), dtype=np.float64)
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
        Select the best action by evaluating policies over a temporal horizon.

        Candidate actions are evaluated by rolling out predicted states and
        observations through the generative model ``p(o|s)``, then computing
        EFE for each candidate.  The action with the lowest EFE is selected
        via a precision-weighted softmax ``p(π) ∝ exp(−γ·G(π))``.

        Parameters
        ----------
        current_beliefs : list of BeliefState
            Belief states at all hierarchical levels (bottom → top).
        available_actions : list of np.ndarray, optional
            Candidate actions.  If *None*, ``num_policies`` actions are
            sampled from a standard normal via the seeded internal RNG.

        Returns
        -------
        best_action : np.ndarray
        planning_info : dict
            Keys: ``best_idx``, ``policy_probs``, ``policy_efes``,
            ``selected_efe``, ``components``.
        """
        top_belief = current_beliefs[-1]
        state_dim = top_belief.mean.shape[0]
        self._ensure_generative_model(state_dim)

        if available_actions is None:
            # Reproducible candidate action sampling via seeded RNG
            available_actions = [
                self._rng.standard_normal(self.action_dim) for _ in range(self.num_policies)
            ]

        # Normalised preference distribution (proper probability distribution)
        pref = np.clip(self.preferences, 1e-10, None)
        pref = pref / (pref.sum() + 1e-10)

        policy_efes: List[float] = []
        policy_info: List[Dict[str, float]] = []

        assert self._generative_model is not None  # guaranteed by _ensure_generative_model

        for action in available_actions:
            # ── Generative rollout via p(s|s,a) and p(o|s) ─────────────────
            predicted_states, predicted_observations = self._generative_model.rollout(
                initial_state=top_belief.mean,
                action=action,
                horizon=self.horizon,
            )

            # State uncertainty: reciprocal of belief precision
            # (higher precision → lower per-element uncertainty)
            per_step_uncertainty = np.ones(state_dim) / (top_belief.precision + 1e-10)
            state_uncertainty = np.stack([per_step_uncertainty] * self.horizon)

            # ── Expected Free Energy ─────────────────────────────────────────
            efe, components = self.fe_calc.compute_expected_free_energy(
                policy=action,
                predicted_states=predicted_states,
                predicted_observations=predicted_observations,
                preferences=pref,
                state_uncertainty=state_uncertainty,
                horizon=self.horizon,
            )

            policy_efes.append(efe)
            policy_info.append(components)

        # ── Precision-weighted softmax over negative EFE ─────────────────────
        policy_efes_arr = np.array(policy_efes)
        shifted_efes = -self.gamma * (policy_efes_arr - policy_efes_arr.min())
        probs = np.exp(shifted_efes)
        probs /= probs.sum()

        best_idx = int(np.argmax(probs))
        best_action = available_actions[best_idx]

        planning_info: Dict[str, Any] = {
            "best_idx": best_idx,
            "policy_probs": probs.tolist(),
            "policy_efes": policy_efes_arr.tolist(),
            "selected_efe": float(policy_efes_arr[best_idx]),
            "components": policy_info[best_idx],
        }

        return best_action, planning_info

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
