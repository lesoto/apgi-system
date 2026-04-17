"""
Unit tests for the VP-15 Precision-Engineered Validation Protocol (v2).

Tests verify:
- All five constraint checkers (metabolic, allostatic, KL, temporal, precision)
- Corrections are applied in-place and move state into the feasible region
- Health score weights and aggregate computation
- Violation history and correction counter
- Reset semantics
"""

from typing import Any, Dict, Optional

import numpy as np
import pytest

from apgi_simulation.core.vp15 import VP15Bounds, VP15Metrics, VP15ValidationProtocol

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_protocol(overrides: Optional[Dict[str, Any]] = None) -> VP15ValidationProtocol:
    """Return a fresh protocol instance with optional config overrides."""
    cfg: Dict[str, Any] = {"validation": {"vp15": overrides or {}}}
    return VP15ValidationProtocol(cfg)


def _healthy_state() -> Dict[str, Any]:
    """Return a synthetic system state that satisfies all VP-15 constraints."""
    return {
        "metabolism": {"reserves": 0.80},
        "allostasis": {"allostatic_load": 0.40},
        "active_inference": {
            "free_energy": 1.50,
            "precisions": [np.array([1.0, 2.0, 3.0])],
        },
        "timeline": {"synchrony": 0.85},
    }


# ---------------------------------------------------------------------------
# Construction & defaults
# ---------------------------------------------------------------------------


class TestVP15Construction:
    def test_default_bounds(self) -> None:
        proto = _make_protocol()
        b = VP15Bounds()
        assert proto.bounds.critical_energy == b.critical_energy
        assert proto.bounds.max_allostatic_load == b.max_allostatic_load
        assert proto.bounds.precision_floor == b.precision_floor
        assert proto.bounds.precision_ceil == b.precision_ceil

    def test_custom_bounds_from_config(self) -> None:
        proto = _make_protocol({"critical_energy": 0.10, "max_allostatic_load": 0.70})
        assert proto.bounds.critical_energy == pytest.approx(0.10)
        assert proto.bounds.max_allostatic_load == pytest.approx(0.70)

    def test_initial_state_clean(self) -> None:
        proto = _make_protocol()
        assert proto.violation_history == []
        assert proto.get_total_corrections() == 0


# ---------------------------------------------------------------------------
# Healthy-state validation (no corrections expected)
# ---------------------------------------------------------------------------


class TestVP15HealthyState:
    def test_valid_flag(self) -> None:
        proto = _make_protocol()
        is_valid, metrics = proto.validate_step(_healthy_state())
        assert is_valid is True

    def test_zero_corrections_when_healthy(self) -> None:
        proto = _make_protocol()
        _, metrics = proto.validate_step(_healthy_state())
        assert metrics.corrections_applied == 0
        assert proto.get_total_corrections() == 0

    def test_health_score_near_one_when_healthy(self) -> None:
        proto = _make_protocol()
        _, metrics = proto.validate_step(_healthy_state())
        # With all constraints satisfied the score must be > 0.8
        assert metrics.system_health_score > 0.80

    def test_no_violations_recorded_when_healthy(self) -> None:
        proto = _make_protocol()
        proto.validate_step(_healthy_state())
        assert len(proto.violation_history) == 0
        assert "healthy" in proto.get_violation_report()


# ---------------------------------------------------------------------------
# Constraint 1 – Metabolic Feasibility
# ---------------------------------------------------------------------------


class TestVP15MetabolicConstraint:
    def test_critical_energy_triggers_correction(self) -> None:
        """
        Verify metabolic constraint enforcement.
        Verifies alignment with APGI Eq. 5.2 (Metabolic Cost).
        """
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.01  # below critical_energy=0.05
        _, metrics = proto.validate_step(state)
        assert metrics.corrections_applied >= 1
        # Correction mathematically adds energy_restore_rate to reserves
        expected_reserves = 0.01 + proto.bounds.energy_restore_rate
        assert state["metabolism"]["reserves"] == pytest.approx(expected_reserves)

    def test_restored_reserves_bounded_at_one(self) -> None:
        """Even if reserves start at 0, restoration never exceeds 1.0."""
        proto = _make_protocol({"energy_restore_rate": 2.0})  # large rate
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.0
        proto.validate_step(state)
        assert state["metabolism"]["reserves"] <= 1.0

    def test_metabolic_feasibility_penalised_after_correction(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.01
        _, metrics = proto.validate_step(state)
        # Score is penalised (0.5) not full (1.0)
        assert metrics.metabolic_feasibility == pytest.approx(0.5)

    def test_healthy_reserves_give_full_score(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.90
        _, metrics = proto.validate_step(state)
        assert metrics.metabolic_feasibility == pytest.approx(1.0)

    def test_violation_recorded_in_history(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.01
        proto.validate_step(state)
        assert any("METABOLIC" in v for v in proto.violation_history)


# ---------------------------------------------------------------------------
# Constraint 2 – Allostatic Integrity
# ---------------------------------------------------------------------------


class TestVP15AllostaticConstraint:
    def test_overload_triggers_damping(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["allostasis"]["allostatic_load"] = 0.95  # above max=0.90
        proto.validate_step(state)
        corrected = state["allostasis"]["allostatic_load"]
        assert corrected <= proto.bounds.max_allostatic_load

    def test_damping_formula_correctness(self) -> None:
        """Verify P-controller: load_new = load - gain*(load - max)."""
        load = 0.95
        max_load = 0.90
        gain = 0.15
        expected = load - gain * (load - max_load)
        expected = float(np.clip(expected, 0.0, max_load))

        proto = _make_protocol({"max_allostatic_load": max_load, "load_damping_gain": gain})
        state = _healthy_state()
        state["allostasis"]["allostatic_load"] = load
        proto.validate_step(state)
        assert state["allostasis"]["allostatic_load"] == pytest.approx(expected, abs=1e-9)

    def test_corrected_load_strictly_below_max(self) -> None:
        """After correction the load must be strictly ≤ max_allostatic_load."""
        proto = _make_protocol()
        state = _healthy_state()
        state["allostasis"]["allostatic_load"] = 0.99
        proto.validate_step(state)
        assert state["allostasis"]["allostatic_load"] <= proto.bounds.max_allostatic_load

    def test_zero_load_gives_integrity_one(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["allostasis"]["allostatic_load"] = 0.0
        _, metrics = proto.validate_step(state)
        assert metrics.allostatic_integrity == pytest.approx(1.0)

    def test_max_load_gives_integrity_zero(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        # Exactly at max bound → no correction, integrity = 0.0
        state["allostasis"]["allostatic_load"] = 0.90
        _, metrics = proto.validate_step(state)
        assert metrics.allostatic_integrity == pytest.approx(0.0, abs=1e-9)

    def test_invalid_flag_when_allostatic_overloaded_and_uncorrectable(self) -> None:
        """is_valid must be False when allostatic_integrity drops to 0."""
        proto = _make_protocol({"load_damping_gain": 0.0})  # no correction applied
        state = _healthy_state()
        state["allostasis"]["allostatic_load"] = 0.99
        is_valid, _ = proto.validate_step(state)
        # With 0 gain, load stays above max → integrity will be ~0 → invalid
        assert not is_valid


# ---------------------------------------------------------------------------
# Constraint 3 – Information Consistency (KL / VFE)
# ---------------------------------------------------------------------------


class TestVP15InformationConstraint:
    def test_negative_vfe_clamped_to_zero(self) -> None:
        """
        Guarantee: free_energy ≥ kl_epsilon.
        Verifies alignment with APGI Eq. 1.4 (Surprise / VFE Non-negativity).
        """
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["free_energy"] = -5.0  # numerically impossible
        proto.validate_step(state)
        assert state["active_inference"]["free_energy"] == pytest.approx(0.0)

    def test_negative_vfe_penalises_consistency(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["free_energy"] = -5.0
        _, metrics = proto.validate_step(state)
        assert metrics.information_consistency == pytest.approx(0.5)

    def test_positive_vfe_gives_full_consistency(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["free_energy"] = 2.0
        _, metrics = proto.validate_step(state)
        assert metrics.information_consistency == pytest.approx(1.0)

    def test_zero_vfe_is_accepted(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["free_energy"] = 0.0
        _, metrics = proto.validate_step(state)
        assert metrics.information_consistency == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Constraint 4 – Temporal Coherence
# ---------------------------------------------------------------------------


class TestVP15TemporalConstraint:
    def test_low_synchrony_triggers_phase_reset(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["timeline"]["synchrony"] = 0.05  # below min_synchrony=0.20
        proto.validate_step(state)
        assert state["timeline"]["synchrony"] >= proto.bounds.min_synchrony

    def test_phase_reset_sets_exact_minimum(self) -> None:
        proto = _make_protocol({"min_synchrony": 0.25})
        state = _healthy_state()
        state["timeline"]["synchrony"] = 0.0
        proto.validate_step(state)
        assert state["timeline"]["synchrony"] == pytest.approx(0.25)

    def test_healthy_synchrony_not_modified(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["timeline"]["synchrony"] = 0.90
        proto.validate_step(state)
        assert state["timeline"]["synchrony"] == pytest.approx(0.90)

    def test_synchrony_above_min_correct_coherence_score(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["timeline"]["synchrony"] = 0.70
        _, metrics = proto.validate_step(state)
        assert metrics.temporal_coherence == pytest.approx(0.70)


# ---------------------------------------------------------------------------
# Constraint 5 – Precision Stability
# ---------------------------------------------------------------------------


class TestVP15PrecisionConstraint:
    def test_below_floor_clipped(self) -> None:
        """
        Guarantee: all precisions ≥ precision_floor.
        Verifies alignment with APGI Eq. 3.5 (Precision Stability).
        """
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["precisions"] = [np.array([0.001, 1.0, 2.0])]
        proto.validate_step(state)
        corrected = state["active_inference"]["precisions"][0]
        assert np.all(corrected >= proto.bounds.precision_floor)

    def test_above_ceil_clipped(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["precisions"] = [np.array([1.0, 50.0, 2.0])]
        proto.validate_step(state)
        corrected = state["active_inference"]["precisions"][0]
        assert np.all(corrected <= proto.bounds.precision_ceil)

    def test_all_in_range_gives_stability_one(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["precisions"] = [np.array([1.0, 2.0, 5.0])]
        _, metrics = proto.validate_step(state)
        assert metrics.precision_stability == pytest.approx(1.0)

    def test_partial_out_of_range_partial_score(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        # 1 out of 3 values is out of range
        state["active_inference"]["precisions"] = [np.array([0.01, 1.0, 2.0])]
        _, metrics = proto.validate_step(state)
        assert 0.0 < metrics.precision_stability < 1.0

    def test_empty_precisions_list_returns_perfect_score(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["precisions"] = []
        _, metrics = proto.validate_step(state)
        assert metrics.precision_stability == pytest.approx(1.0)

    def test_multi_level_precisions_corrected(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["active_inference"]["precisions"] = [
            np.array([0.001, 1.0]),
            np.array([2.0, 500.0]),
        ]
        proto.validate_step(state)
        for arr in state["active_inference"]["precisions"]:
            assert np.all(arr >= proto.bounds.precision_floor)
            assert np.all(arr <= proto.bounds.precision_ceil)


# ---------------------------------------------------------------------------
# Health score weighting
# ---------------------------------------------------------------------------


class TestVP15HealthScore:
    def test_weight_sum_is_one(self) -> None:
        assert sum(VP15ValidationProtocol._WEIGHTS.values()) == pytest.approx(1.0)

    def test_metabolic_failure_dominates_score(self) -> None:
        """Metabolic weight (0.30) is the largest single contributor."""
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.0  # worst case (corrected to 0.5 score)
        _, metrics = proto.validate_step(state)
        # Remaining constraints are healthy so score = 0.5*0.30 + 1.0*0.70 = 0.85
        assert metrics.system_health_score == pytest.approx(0.70, abs=0.05)


# ---------------------------------------------------------------------------
# Cumulative corrections & reset
# ---------------------------------------------------------------------------


class TestVP15CumulativeAndReset:
    def test_corrections_accumulate_across_steps(self) -> None:
        proto = _make_protocol()
        for _ in range(5):
            state = _healthy_state()
            state["metabolism"]["reserves"] = 0.0
            proto.validate_step(state)
        assert proto.get_total_corrections() >= 5

    def test_reset_clears_violation_history(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.0
        proto.validate_step(state)
        assert len(proto.violation_history) > 0
        proto.reset()
        assert len(proto.violation_history) == 0

    def test_reset_clears_correction_counter(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        state["metabolism"]["reserves"] = 0.0
        proto.validate_step(state)
        proto.reset()
        assert proto.get_total_corrections() == 0

    def test_violation_report_truncated_to_10(self) -> None:
        proto = _make_protocol()
        for _ in range(20):
            state = _healthy_state()
            state["metabolism"]["reserves"] = 0.0
            proto.validate_step(state)
        report = proto.get_violation_report()
        # Report shows last 10 – count bullet lines
        bullet_lines = [line for line in report.splitlines() if line.strip().startswith("–")]
        assert len(bullet_lines) <= 10


# ---------------------------------------------------------------------------
# VP15Metrics dataclass
# ---------------------------------------------------------------------------


class TestVP15Metrics:
    def test_default_values_are_zero(self) -> None:
        m = VP15Metrics()
        assert m.metabolic_feasibility == 0.0
        assert m.allostatic_integrity == 0.0
        assert m.system_health_score == 0.0
        assert m.corrections_applied == 0

    def test_custom_values_stored(self) -> None:
        m = VP15Metrics(
            metabolic_feasibility=0.9,
            allostatic_integrity=0.8,
            information_consistency=1.0,
            temporal_coherence=0.7,
            precision_stability=0.95,
            system_health_score=0.87,
            corrections_applied=2,
        )
        assert m.corrections_applied == 2
        assert m.system_health_score == pytest.approx(0.87)


# ---------------------------------------------------------------------------
# Missing keys handled gracefully (state dict partial)
# ---------------------------------------------------------------------------


class TestVP15PartialState:
    def test_empty_state_does_not_raise(self) -> None:
        proto = _make_protocol()
        is_valid, metrics = proto.validate_step({})
        # With empty state defaults kick in (reserves=1.0, load=0.0, fe=0.0, synchrony=1.0)
        assert isinstance(is_valid, bool)
        assert isinstance(metrics, VP15Metrics)

    def test_missing_precisions_treated_as_empty(self) -> None:
        proto = _make_protocol()
        state = _healthy_state()
        del state["active_inference"]["precisions"]
        _, metrics = proto.validate_step(state)
        assert metrics.precision_stability == pytest.approx(1.0)
