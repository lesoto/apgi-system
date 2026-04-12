"""Unit tests for AllostaticRegulator."""

from typing import Any, Dict

import numpy as np
import pytest

from apgi_system.interoception.allostasis import AllostaticRegulator, AllostaticSetPoint


class TestAllostaticSetPoint:
    """Test AllostaticSetPoint dataclass."""

    def test_initialization(self):
        """Test AllostaticSetPoint initializes correctly."""
        sp = AllostaticSetPoint(
            name="heart_rate",
            target=70.0,
            acceptable_range=(65, 75),
            current_deviation=5.0,
            load_contribution=0.1,
        )

        assert sp.name == "heart_rate"
        assert sp.target == 70.0
        assert sp.acceptable_range == (65, 75)
        assert sp.current_deviation == 5.0
        assert sp.load_contribution == 0.1


class TestAllostaticRegulator:
    """Test AllostaticRegulator functionality."""

    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Simple test configuration."""
        return {
            "interoception": {
                "allostatic_ranges": {
                    "tight": 0.1,
                    "moderate": 0.2,
                    "wide": 0.3,
                }
            }
        }

    @pytest.fixture
    def regulator(self, config: Dict[str, Any]) -> AllostaticRegulator:
        """Create regulator instance."""
        return AllostaticRegulator(config)

    def test_initialization(self, regulator: AllostaticRegulator) -> None:
        """Test regulator initializes correctly."""
        assert len(regulator.set_points) == 4
        assert regulator.total_load == 0.0
        assert regulator.load_decay_rate == 0.001
        assert regulator.load_accumulation_rate == 0.01

        # Check set points
        sp_names = [sp.name for sp in regulator.set_points]
        assert "heart_rate" in sp_names
        assert "temperature" in sp_names
        assert "glucose" in sp_names
        assert "cortisol" in sp_names

    def test_update_normal_body_state(self, regulator: AllostaticRegulator) -> None:
        """Test update with normal body state."""
        body_state = {
            "heart_rate": 70.0,
            "temperature": 37.0,
            "glucose": 5.0,
            "cortisol": 10.0,
        }

        result = regulator.update(body_state, dt=1.0)

        assert isinstance(result, dict)
        assert "regulation_signals" in result
        assert "allostatic_load" in result
        assert "total_deviation" in result
        assert "set_points_status" in result
        assert "homeostatic_stability" in result

        # Should be stable with normal values
        assert result["allostatic_load"] < 0.1
        assert result["homeostatic_stability"] > 0.8

    def test_update_stressed_body_state(self, regulator: AllostaticRegulator) -> None:
        """Test update with stressed body state."""
        body_state = {
            "heart_rate": 90.0,  # High
            "temperature": 38.0,  # High
            "glucose": 3.0,  # Low
            "cortisol": 15.0,  # High
        }

        result = regulator.update(body_state, dt=1000.0)  # Longer dt to accumulate load

        # Should accumulate load
        assert result["allostatic_load"] > 0.1
        assert result["homeostatic_stability"] < 0.8

        # Check regulation signals
        signals = result["regulation_signals"]
        assert signals["heart_rate"] < 0  # Should reduce heart rate
        assert signals["temperature"] < 0  # Should reduce temperature
        assert signals["glucose"] > 0  # Should increase glucose
        assert signals["cortisol"] < 0  # Should reduce cortisol

    def test_update_partial_body_state(self, regulator: AllostaticRegulator) -> None:
        """Test update with partial body state."""
        body_state = {"heart_rate": 80.0}

        result = regulator.update(body_state, dt=1.0)

        # Should only update heart_rate
        assert "heart_rate" in result["regulation_signals"]
        assert result["regulation_signals"]["heart_rate"] < 0

    def test_update_invalid_inputs(self, regulator):
        """Test error handling for invalid inputs."""
        # Invalid body_state type
        with pytest.raises(TypeError):
            regulator.update("not a dict")

        # Invalid dt
        with pytest.raises(ValueError):
            regulator.update({"heart_rate": 70.0}, dt=-1.0)

        # Invalid body_state value
        with pytest.raises(ValueError):
            regulator.update({"heart_rate": float("nan")})

    def test_get_allostatic_load(self, regulator):
        """Test get_allostatic_load method."""
        load = regulator.get_allostatic_load()
        assert isinstance(load, float)
        assert 0.0 <= load <= 1.0

    def test_trigger_stressor(self, regulator):
        """Test trigger_stressor method."""
        initial_load = regulator.total_load

        regulator.trigger_stressor(intensity=0.5)

        assert regulator.total_load > initial_load
        assert regulator.total_load <= 1.0

    def test_trigger_stressor_max_intensity(self, regulator):
        """Test trigger_stressor with maximum intensity."""
        regulator.trigger_stressor(intensity=1.0)

        assert regulator.total_load == 0.2  # 1.0 * 0.2

    def test_reset(self, regulator):
        """Test reset method."""
        # Accumulate some load
        regulator.trigger_stressor(intensity=0.5)
        assert regulator.total_load > 0

        # Update with deviations
        body_state = {"heart_rate": 90.0}
        regulator.update(body_state, dt=1000.0)

        # Reset
        regulator.reset()

        assert regulator.total_load == 0.0
        for sp in regulator.set_points:
            assert sp.current_deviation == 0.0
            assert sp.load_contribution == 0.0

    def test_load_decay(self, regulator):
        """Test load decay over time."""
        # Add load
        regulator.trigger_stressor(intensity=0.5)
        initial_load = regulator.total_load

        # Update without deviations (should decay)
        body_state = {"heart_rate": 70.0}
        regulator.update(body_state, dt=1000.0)  # 1 second

        assert regulator.total_load < initial_load

    def test_get_set_points_status(self, regulator):
        """Test _get_set_points_status method."""
        status = regulator._get_set_points_status()

        assert isinstance(status, list)
        assert len(status) == 4

        for sp_status in status:
            assert "name" in sp_status
            assert "target" in sp_status
            assert "deviation" in sp_status
            assert "load_contribution" in sp_status
            assert "in_range" in sp_status

    def test_compute_stability(self, regulator):
        """Test _compute_stability method."""
        # Set up some deviations
        regulator.set_points[0].current_deviation = 5.0  # heart_rate
        regulator.set_points[1].current_deviation = 0.5  # temperature

        stability = regulator._compute_stability()

        assert isinstance(stability, float)
        assert 0.0 <= stability <= 1.0

    def test_edge_cases(self, regulator):
        """Test various edge cases."""
        # Empty body state
        result = regulator.update({}, dt=1.0)
        assert result["total_deviation"] == 0.0

        # Extreme values
        body_state = {
            "heart_rate": 200.0,  # Very high
            "temperature": 30.0,  # Very low
        }
        result = regulator.update(body_state, dt=1.0)

        # Should handle gracefully
        assert np.isfinite(result["allostatic_load"])
        assert np.isfinite(result["homeostatic_stability"])

    def test_load_clamping(self, regulator):
        """Test load clamping to [0, 1] range."""
        # Force load above 1
        regulator.total_load = 1.5

        body_state = {"heart_rate": 70.0}
        result = regulator.update(body_state, dt=1.0)

        assert result["allostatic_load"] <= 1.0

        # Force negative load
        regulator.total_load = -0.5
        result = regulator.update(body_state, dt=1.0)

        assert result["allostatic_load"] >= 0.0
