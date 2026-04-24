"""
Unit tests for TemporalDynamics.

Covers:
- Deterministic / seeded initialisation
- Phase evolution (dφ/dt = 2πf)
- Phase-Amplitude Coupling (PAC) direction and bounds
- Synchrony metric range
- Gain modulation range and band selection
- reset() reproducibility with seeded RNG
- reset() does NOT reset the shared RNG state (so subsequent calls differ)
"""

import math
from typing import Any

import numpy as np
import pytest

from apgi_framework.core.temporal_dynamics import TemporalDynamics

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_CONFIG: dict = {
    "oscillations": {
        "bands": {
            "delta": {"range": [1, 4], "amplitude": 0.5},
            "theta": {"range": [4, 8], "amplitude": 0.7},
            "alpha": {"range": [8, 12], "amplitude": 1.0},
            "beta": {"range": [12, 30], "amplitude": 0.8},
            "gamma": {"range": [30, 80], "amplitude": 0.6},
        },
        "coupling_strength": 0.3,
    }
}


def _make_td(seed: int = 42) -> TemporalDynamics:
    """Helper: create a TemporalDynamics with a fixed seed."""
    rng = np.random.default_rng(seed)
    return TemporalDynamics(MINIMAL_CONFIG, rng=rng)


# ---------------------------------------------------------------------------
# 1. Initialisation
# ---------------------------------------------------------------------------


class TestInit:
    def test_bands_loaded_from_config(self) -> None:
        td = _make_td()
        assert set(td.bands.keys()) == {"delta", "theta", "alpha", "beta", "gamma"}

    def test_time_starts_at_zero(self) -> None:
        td = _make_td()
        assert td.time == pytest.approx(0.0)

    def test_phases_in_valid_range(self) -> None:
        td = _make_td()
        for band, phase in td.phases.items():
            assert 0.0 <= phase < 2 * math.pi, f"Band '{band}' phase {phase} out of range"

    def test_empty_oscillations_config_uses_defaults(self) -> None:
        td = TemporalDynamics({}, rng=np.random.default_rng(0))
        assert "delta" in td.bands
        assert "gamma" in td.bands

    def test_coupling_strength_read_from_config(self) -> None:
        td = _make_td()
        assert td.coupling_strength == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# 2. Seeded reproducibility
# ---------------------------------------------------------------------------


class TestSeededReproducibility:
    def test_same_seed_same_initial_phases(self) -> None:
        td1 = _make_td(seed=7)
        td2 = _make_td(seed=7)
        for band in td1.bands:
            assert td1.phases[band] == pytest.approx(td2.phases[band])

    def test_different_seed_different_initial_phases(self) -> None:
        td1 = _make_td(seed=1)
        td2 = _make_td(seed=99)
        # At least one band should differ (very high probability)
        diffs = [abs(td1.phases[b] - td2.phases[b]) > 1e-9 for b in td1.bands]
        assert any(diffs), "Seeds 1 and 99 produced identical phases — RNG not seeded"

    def test_no_global_rng_side_effect(self) -> None:
        """Global np.random state should not be consumed during init or update."""
        # Snapshot the global RNG state (returns a tuple: (str, ndarray, int, int, float))
        global_state_before: Any = np.random.get_state()
        _make_td(seed=123)
        td = _make_td(seed=123)
        td.update(0.001)
        global_state_after: Any = np.random.get_state()
        # The MT state arrays should be identical
        np.testing.assert_array_equal(
            global_state_before[1],
            global_state_after[1],
            err_msg="TemporalDynamics consumed the global np.random state",
        )


# ---------------------------------------------------------------------------
# 3. update() — phase evolution
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_time_advances_by_dt(self) -> None:
        td = _make_td()
        dt = 0.005
        td.update(dt)
        assert td.time == pytest.approx(dt)

    def test_accumulative_time(self) -> None:
        td = _make_td()
        for _ in range(10):
            td.update(0.001)
        assert td.time == pytest.approx(0.01)

    def test_phases_advance_correctly(self) -> None:
        """Phase should increase by 2π·f·dt and wrap to [0, 2π)."""
        td = _make_td(seed=0)
        initial_phases = dict(td.phases)
        dt = 0.01
        td.update(dt)

        for band, params in td.bands.items():
            freq = (params["range"][0] + params["range"][1]) / 2.0
            expected_advance = 2 * math.pi * freq * dt
            expected_phase = (initial_phases[band] + expected_advance) % (2 * math.pi)
            assert td.phases[band] == pytest.approx(expected_phase, abs=1e-10)

    def test_phases_stay_in_0_to_2pi(self) -> None:
        td = _make_td()
        for _ in range(500):
            td.update(0.01)
            for band, phase in td.phases.items():
                assert (
                    0.0 <= phase < 2 * math.pi + 1e-9
                ), f"Band '{band}' phase {phase} escaped [0, 2π)"

    def test_returns_required_keys(self) -> None:
        td = _make_td()
        result = td.update(0.001)
        assert set(result.keys()) == {"phases", "amplitudes", "pac_factor", "synchrony"}

    def test_amplitudes_all_bands_present(self) -> None:
        td = _make_td()
        result = td.update(0.001)
        assert set(result["amplitudes"].keys()) == set(td.bands.keys())

    def test_pac_factor_bounds(self) -> None:
        """pac_factor = 1 + coupling_strength * sin(theta_phase).
        With coupling_strength=0.3, factor ∈ [0.7, 1.3]."""
        td = _make_td()
        for _ in range(200):
            result = td.update(0.001)
            pac = result["pac_factor"]
            assert 0.7 - 1e-9 <= pac <= 1.3 + 1e-9, f"PAC factor {pac} out of bounds"


# ---------------------------------------------------------------------------
# 4. Synchrony metric
# ---------------------------------------------------------------------------


class TestSynchrony:
    def test_synchrony_range(self) -> None:
        """Synchrony ∈ [0, 1] by definition of the ratio metric."""
        td = _make_td()
        for _ in range(100):
            result = td.update(0.001)
            s = result["synchrony"]
            assert 0.0 <= s <= 1.0 + 1e-9, f"Synchrony {s} out of [0, 1]"

    def test_synchrony_empty_amplitudes(self) -> None:
        td = _make_td()
        # Call private method with empty dict to exercise the guard clause
        assert td._compute_synchrony({}) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 5. Gain modulation
# ---------------------------------------------------------------------------


class TestGainModulation:
    def test_gain_default_alpha_band(self) -> None:
        """Gain = 1 + 0.5 * sin(phase) ∈ [0.5, 1.5]."""
        td = _make_td()
        for _ in range(200):
            td.update(0.001)
            gain = td.get_gain_modulation("alpha")
            assert 0.5 - 1e-9 <= gain <= 1.5 + 1e-9, f"Alpha gain {gain} out of bounds"

    def test_gain_unknown_band_returns_default(self) -> None:
        """Missing band key → phase defaults to 0.0 → gain = 1 + 0.5*sin(0) = 1.0."""
        td = _make_td()
        gain = td.get_gain_modulation("nonexistent_band")
        assert gain == pytest.approx(1.0)

    def test_gain_all_known_bands(self) -> None:
        td = _make_td()
        td.update(0.05)
        for band in td.bands:
            gain = td.get_gain_modulation(band)
            assert 0.5 - 1e-9 <= gain <= 1.5 + 1e-9


# ---------------------------------------------------------------------------
# 6. reset()
# ---------------------------------------------------------------------------


class TestReset:
    def test_time_resets_to_zero(self) -> None:
        td = _make_td()
        td.update(0.5)
        td.reset()
        assert td.time == pytest.approx(0.0)  # type: ignore[attr-defined]

    def test_same_seed_same_post_reset_phases(self) -> None:
        """Two identically-seeded instances should have the same phases after reset."""
        td1 = TemporalDynamics(MINIMAL_CONFIG, rng=np.random.default_rng(77))  # type: ignore[call-arg]
        td2 = TemporalDynamics(MINIMAL_CONFIG, rng=np.random.default_rng(77))  # type: ignore[call-arg]
        td1.update(0.1)  # type: ignore[attr-defined]
        td2.update(0.5)  # type: ignore[attr-defined]
        td1.reset()  # type: ignore[attr-defined]
        td2.reset()  # type: ignore[attr-defined]
        for band in td1.bands:  # type: ignore[attr-defined]
            assert td1.phases[band] == pytest.approx(td2.phases[band])  # type: ignore[attr-defined]

    def test_phases_after_reset_in_valid_range(self) -> None:
        td = _make_td()
        td.update(1.0)  # type: ignore[attr-defined]
        td.reset()  # type: ignore[attr-defined]
        for band, phase in td.phases.items():  # type: ignore[attr-defined]
            assert (
                0.0 <= phase < 2 * math.pi
            ), f"After reset, band '{band}' phase {phase} is invalid"

    def test_update_after_reset_works(self) -> None:
        td = _make_td()
        td.update(0.1)  # type: ignore[attr-defined]
        td.reset()  # type: ignore[attr-defined]
        result = td.update(0.001)  # type: ignore[attr-defined]
        assert result["synchrony"] >= 0.0
