"""
Unit tests for MotorPlanner and GenerativeLikelihood.

Covers:
- GenerativeLikelihood: orthonormality of A, B, C; rollout shape/validity
- MotorPlanner: reproducibility, preference normalisation, EFE differentiation,
  plan() output contract, lazy generative model creation, reset()
"""

import math
from typing import List
from unittest.mock import MagicMock

import numpy as np
import pytest

from apgi_simulation.core.motor_planning import GenerativeLikelihood, MotorPlanner

# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG: dict = {
    "system": {
        "random_seed": 0,
        "action_dim": 6,
        "obs_dim": 6,
        "timestep_ms": 1.0,
    },
    "active_inference": {
        "learning_rate": 0.01,
        "precision_init": 1.0,
        "precision_range": [0.1, 10.0],
        "free_energy_threshold": 100.0,
        "planning": {
            "horizon": 3,
            "num_policies": 5,
            "precision": 1.0,
        },
    },
    "free_energy": {
        "eps": 1e-10,
        "temperature": 1.0,
        "precision_min": 1e-6,
        "precision_max": 1e6,
        "regularization_eps": 1e-6,
        "condition_number_threshold": 1e12,
    },
}


def _make_belief(mean: np.ndarray, precision: float = 1.0) -> MagicMock:
    """Return a lightweight BeliefState-like mock."""
    b = MagicMock()
    b.mean = mean.copy()
    b.precision = precision
    b.covariance = np.eye(len(mean))
    return b


def _make_beliefs(dims: List[int], precision: float = 1.0) -> List[MagicMock]:
    """Create a list of mocked belief states for a hierarchy."""
    return [_make_belief(np.zeros(d), precision) for d in dims]


# ---------------------------------------------------------------------------
# GenerativeLikelihood tests
# ---------------------------------------------------------------------------


class TestGenerativeLikelihood:
    """Tests focused on the internal generative model."""

    STATE_DIM = 8
    OBS_DIM = 6
    ACTION_DIM = 4

    @pytest.fixture
    def gl(self) -> GenerativeLikelihood:
        return GenerativeLikelihood(
            state_dim=self.STATE_DIM,
            obs_dim=self.OBS_DIM,
            action_dim=self.ACTION_DIM,
            seed=42,
        )

    # ── Weight matrix properties ────────────────────────────────────────────

    def test_A_shape(self, gl: GenerativeLikelihood) -> None:
        assert gl.A.shape == (self.OBS_DIM, self.STATE_DIM)

    def test_B_shape(self, gl: GenerativeLikelihood) -> None:
        assert gl.B.shape == (self.STATE_DIM, self.STATE_DIM)

    def test_C_shape(self, gl: GenerativeLikelihood) -> None:
        assert gl.C.shape == (self.STATE_DIM, self.ACTION_DIM)

    def test_A_rows_are_orthonormal(self, gl: GenerativeLikelihood) -> None:
        """A must be (pseudo-)orthonormal: A @ Aᵀ ≈ I_{obs_dim}."""
        product = gl.A @ gl.A.T
        np.testing.assert_allclose(
            product,
            np.eye(self.OBS_DIM),
            atol=1e-10,
            err_msg="A @ A.T is not identity — likelihood matrix lost orthonormality",
        )

    def test_B_is_orthogonal(self, gl: GenerativeLikelihood) -> None:
        """B must be orthogonal: B @ Bᵀ ≈ I_{state_dim}."""
        product = gl.B @ gl.B.T
        np.testing.assert_allclose(
            product,
            np.eye(self.STATE_DIM),
            atol=1e-10,
            err_msg="B @ B.T is not identity — transition matrix is not orthogonal",
        )

    def test_deterministic_with_same_seed(self) -> None:
        gl1 = GenerativeLikelihood(8, 6, 4, seed=7)
        gl2 = GenerativeLikelihood(8, 6, 4, seed=7)
        np.testing.assert_array_equal(gl1.A, gl2.A)
        np.testing.assert_array_equal(gl1.B, gl2.B)
        np.testing.assert_array_equal(gl1.C, gl2.C)

    def test_different_seeds_produce_different_matrices(self) -> None:
        gl1 = GenerativeLikelihood(8, 6, 4, seed=1)
        gl2 = GenerativeLikelihood(8, 6, 4, seed=2)
        assert not np.allclose(gl1.A, gl2.A), "Different seeds produced identical A"

    # ── rollout() ───────────────────────────────────────────────────────────

    def test_rollout_state_count(self, gl: GenerativeLikelihood) -> None:
        s0 = np.zeros(self.STATE_DIM)
        a = np.zeros(self.ACTION_DIM)
        states, obs = gl.rollout(s0, a, horizon=3)
        assert len(states) == 3

    def test_rollout_obs_shape(self, gl: GenerativeLikelihood) -> None:
        s0 = np.zeros(self.STATE_DIM)
        a = np.zeros(self.ACTION_DIM)
        _, obs = gl.rollout(s0, a, horizon=4)
        assert obs.shape == (4, self.OBS_DIM)

    def test_rollout_observations_are_probability_distributions(
        self, gl: GenerativeLikelihood
    ) -> None:
        """Each observation row must sum to 1 and be non-negative (softmax output)."""
        rng = np.random.default_rng(0)
        s0 = rng.standard_normal(self.STATE_DIM)
        a = rng.standard_normal(self.ACTION_DIM)
        _, obs = gl.rollout(s0, a, horizon=5)
        for t in range(5):
            assert np.all(obs[t] >= 0), f"Timestep {t}: negative probability"
            assert obs[t].sum() == pytest.approx(
                1.0, abs=1e-8
            ), f"Timestep {t}: obs does not sum to 1 (got {obs[t].sum():.6f})"

    def test_rollout_states_bounded_by_tanh(self, gl: GenerativeLikelihood) -> None:
        """All state values must lie in (-1, 1) after the tanh nonlinearity."""
        rng = np.random.default_rng(42)
        s0 = rng.standard_normal(self.STATE_DIM) * 10  # large initial state
        a = rng.standard_normal(self.ACTION_DIM) * 10
        states, _ = gl.rollout(s0, a, horizon=10)
        for t, s in enumerate(states):
            assert np.all(
                np.abs(s) <= 1.0 + 1e-10
            ), f"Timestep {t}: state escapes tanh bounds ({np.abs(s).max():.4f})"

    def test_rollout_action_padding(self, gl: GenerativeLikelihood) -> None:
        """Short action vector should be zero-padded without error."""
        s0 = np.zeros(self.STATE_DIM)
        a_short = np.ones(2)  # shorter than action_dim=4
        states, obs = gl.rollout(s0, a_short, horizon=2)
        assert len(states) == 2

    def test_rollout_deterministic(self, gl: GenerativeLikelihood) -> None:
        s0 = np.ones(self.STATE_DIM) * 0.5
        a = np.ones(self.ACTION_DIM) * 0.1
        states1, obs1 = gl.rollout(s0, a, horizon=3)
        states2, obs2 = gl.rollout(s0, a, horizon=3)
        for t in range(3):
            np.testing.assert_array_equal(states1[t], states2[t])
        np.testing.assert_array_equal(obs1, obs2)

    def test_zero_horizon_rollout(self, gl: GenerativeLikelihood) -> None:
        s0 = np.zeros(self.STATE_DIM)
        a = np.zeros(self.ACTION_DIM)
        states, obs = gl.rollout(s0, a, horizon=0)
        assert states == []
        assert obs.shape == (0, self.OBS_DIM)


# ---------------------------------------------------------------------------
# MotorPlanner tests
# ---------------------------------------------------------------------------


class TestMotorPlanner:
    """Tests for the MotorPlanner public API and internal behaviour."""

    @pytest.fixture
    def planner(self) -> MotorPlanner:
        return MotorPlanner(BASE_CONFIG)

    @pytest.fixture
    def beliefs(self) -> List[MagicMock]:
        # 4-level hierarchy matching the default config
        return _make_beliefs([32, 16, 8, 4])

    # ── Initialisation ──────────────────────────────────────────────────────

    def test_horizon_read_from_config(self, planner: MotorPlanner) -> None:
        assert planner.horizon == 3

    def test_num_policies_read_from_config(self, planner: MotorPlanner) -> None:
        assert planner.num_policies == 5

    def test_action_dim_read_from_config(self, planner: MotorPlanner) -> None:
        assert planner.action_dim == 6

    def test_obs_dim_read_from_config(self, planner: MotorPlanner) -> None:
        assert planner.obs_dim == 6

    def test_generative_model_starts_as_none(self, planner: MotorPlanner) -> None:
        assert planner._generative_model is None

    # ── plan() output contract ──────────────────────────────────────────────

    def test_plan_returns_action_and_info(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        action, info = planner.plan(beliefs)
        assert isinstance(action, np.ndarray)
        assert isinstance(info, dict)

    def test_plan_action_has_correct_shape(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        action, _ = planner.plan(beliefs)
        assert action.shape == (planner.action_dim,)

    def test_plan_info_keys(self, planner: MotorPlanner, beliefs: List[MagicMock]) -> None:
        _, info = planner.plan(beliefs)
        expected = {"best_idx", "policy_probs", "policy_efes", "selected_efe", "components"}
        assert set(info.keys()) == expected

    def test_plan_policy_probs_sum_to_one(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        _, info = planner.plan(beliefs)
        total = sum(info["policy_probs"])
        assert total == pytest.approx(1.0, abs=1e-7)

    def test_plan_best_idx_in_range(self, planner: MotorPlanner, beliefs: List[MagicMock]) -> None:
        _, info = planner.plan(beliefs)
        assert 0 <= info["best_idx"] < planner.num_policies

    def test_plan_selected_efe_matches_best_idx(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        _, info = planner.plan(beliefs)
        assert info["selected_efe"] == pytest.approx(info["policy_efes"][info["best_idx"]])

    def test_plan_all_efe_are_finite(self, planner: MotorPlanner, beliefs: List[MagicMock]) -> None:
        _, info = planner.plan(beliefs)
        for efe in info["policy_efes"]:
            assert math.isfinite(efe), f"Non-finite EFE value: {efe}"

    # ── Generative model lazy creation ─────────────────────────────────────

    def test_generative_model_created_on_first_plan(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        assert planner._generative_model is None
        planner.plan(beliefs)
        assert planner._generative_model is not None

    def test_generative_model_state_dim_matches_top_belief(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        planner.plan(beliefs)
        assert planner._generative_model is not None
        assert planner._generative_model.state_dim == beliefs[-1].mean.shape[0]

    def test_generative_model_recreated_on_dim_change(self, planner: MotorPlanner) -> None:
        beliefs_small = _make_beliefs([4, 4])
        planner.plan(beliefs_small)
        model_first = planner._generative_model

        beliefs_large = _make_beliefs([8, 8])
        planner.plan(beliefs_large)
        model_second = planner._generative_model

        assert (
            model_first is not model_second
        ), "Generative model was not recreated after top-level dim change"

    # ── Observations are NOT pure noise ────────────────────────────────────

    def test_predicted_obs_are_not_noise(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        """
        Run plan() twice with the same beliefs and the same candidate actions.
        If observations were random noise, EFEs would differ across calls.
        With a deterministic generative model they must be identical.
        """
        fixed_actions = [np.ones(planner.action_dim) * i for i in range(planner.num_policies)]

        _, info1 = planner.plan(beliefs, available_actions=list(fixed_actions))
        _, info2 = planner.plan(beliefs, available_actions=list(fixed_actions))

        np.testing.assert_allclose(
            info1["policy_efes"],
            info2["policy_efes"],
            atol=1e-10,
            err_msg="EFE values differ across identical calls — observations are still random",
        )

    # ── Reproducibility (seeded RNG for action sampling) ───────────────────

    def test_plan_reproducible_with_same_seed(self) -> None:
        """Two planners with the same seed must sample the same candidate actions."""
        p1 = MotorPlanner(BASE_CONFIG)
        p2 = MotorPlanner(BASE_CONFIG)
        beliefs = _make_beliefs([4, 4])

        action1, info1 = p1.plan(beliefs)
        action2, info2 = p2.plan(beliefs)

        np.testing.assert_array_equal(action1, action2)
        assert info1["policy_efes"] == pytest.approx(info2["policy_efes"])

    def test_plan_with_provided_actions_ignores_rng(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        """When actions are provided explicitly, the RNG should not influence results."""
        fixed = [np.eye(1, planner.action_dim, i).flatten() for i in range(planner.num_policies)]
        _, info1 = planner.plan(beliefs, available_actions=list(fixed))
        _, info2 = planner.plan(beliefs, available_actions=list(fixed))
        assert info1["policy_efes"] == pytest.approx(info2["policy_efes"])

    # ── EFE differentiation ─────────────────────────────────────────────────

    def test_efe_varies_across_different_actions(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        """
        Actions pointing in very different directions should produce different EFEs,
        demonstrating that the EFE is truly state-dependent (not uniform noise).
        """
        actions_spread = [
            np.array([1, 0, 0, 0, 0, 0], dtype=float),
            np.array([0, 1, 0, 0, 0, 0], dtype=float),
            np.array([-1, 0, 0, 0, 0, 0], dtype=float),
            np.array([0, -1, 0, 0, 0, 0], dtype=float),
        ]
        _, info = planner.plan(beliefs, available_actions=actions_spread)
        efes = info["policy_efes"]
        # With a meaningful generative model, at least two EFEs should differ
        unique_efes = set(round(e, 6) for e in efes)
        assert len(unique_efes) > 1, (
            "All EFE values are identical — EFE is not differentiating between actions. "
            "This suggests observations are still noise-based."
        )

    # ── Preferences ────────────────────────────────────────────────────────

    def test_set_preferences_updates_attribute(self, planner: MotorPlanner) -> None:
        new_pref = np.array([0.5, 0.3, 0.2, 0.0, 0.0, 0.0])
        planner.set_preferences(new_pref)
        np.testing.assert_array_equal(planner.preferences, new_pref)

    def test_preferences_normalised_internally(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        """Unnormalised preferences must not crash plan() or produce NaN EFEs."""
        planner.set_preferences(np.array([100.0, 200.0, 50.0, 0.0, 0.0, 0.0]))
        _, info = planner.plan(beliefs)
        for efe in info["policy_efes"]:
            assert math.isfinite(efe), "NaN/Inf EFE with unnormalised preferences"

    def test_zero_preferences_handled_gracefully(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        planner.set_preferences(np.zeros(planner.obs_dim))
        _, info = planner.plan(beliefs)
        for efe in info["policy_efes"]:
            assert math.isfinite(efe)

    # ── Edge cases ──────────────────────────────────────────────────────────

    def test_single_policy(self) -> None:
        cfg = {**BASE_CONFIG}
        cfg = dict(BASE_CONFIG)
        cfg["active_inference"] = {
            **BASE_CONFIG["active_inference"],
            "planning": {"horizon": 1, "num_policies": 1, "precision": 1.0},
        }
        p = MotorPlanner(cfg)
        beliefs = _make_beliefs([4])
        action, info = p.plan(beliefs)
        assert info["best_idx"] == 0
        assert len(info["policy_probs"]) == 1
        assert info["policy_probs"][0] == pytest.approx(1.0)

    def test_single_level_hierarchy(self, planner: MotorPlanner) -> None:
        """Plan should work when the hierarchy has only one level (top == bottom)."""
        beliefs = _make_beliefs([4])
        action, info = planner.plan(beliefs)
        assert action.shape == (planner.action_dim,)

    # ── reset() ────────────────────────────────────────────────────────────

    def test_reset_does_not_error(self, planner: MotorPlanner) -> None:
        planner.reset()  # Should be a no-op without raising

    def test_generative_model_retained_after_reset(
        self, planner: MotorPlanner, beliefs: List[MagicMock]
    ) -> None:
        """Weights should be preserved across reset() to avoid re-initialisation cost."""
        planner.plan(beliefs)
        model_before = planner._generative_model
        planner.reset()
        assert planner._generative_model is model_before
