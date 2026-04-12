"""Unit tests for AllostaticRegulator."""

from typing import Any, Dict

import pytest

from apgi_system.interoception.allostasis import AllostaticRegulator


class TestAllostaticRegulator:
    """Test suite for AllostaticRegulator."""

    @pytest.fixture
    def config(self) -> Dict[str, Any]:
        """Create test configuration."""
        return {
            "interoception": {"allostatic_ranges": {"tight": 0.1, "moderate": 0.2, "wide": 0.3}}
        }

    @pytest.fixture
    def regulator(self, config: Dict[str, Any]) -> AllostaticRegulator:
        """Create test regulator."""
        return AllostaticRegulator(config)

    def test_initialization(self, regulator: AllostaticRegulator, config: Dict[str, Any]):
        """Test regulator initialization."""
        assert regulator.config == config
        assert regulator.total_load == 0.0
        assert regulator.load_decay_rate == 0.001
        assert regulator.load_accumulation_rate == 0.01
        assert regulator.tight_range_factor == 0.1
        assert regulator.moderate_range_factor == 0.2
        assert regulator.wide_range_factor == 0.3

        # Check set points
        assert len(regulator.set_points) == 4
        set_point_names = [sp.name for sp in regulator.set_points]
        assert "heart_rate" in set_point_names
        assert "temperature" in set_point_names
        assert "glucose" in set_point_names
        assert "cortisol" in set_point_names

        # Check specific set point values
        hr_sp = next(sp for sp in regulator.set_points if sp.name == "heart_rate")
        assert hr_sp.target == 70.0
        assert hr_sp.acceptable_range == (65, 75)

    def test_update_normal_values(self, regulator: AllostaticRegulator):
        """Test update with normal physiological values."""
        body_state = {"heart_rate": 70.0, "temperature": 37.0, "glucose": 5.0, "cortisol": 10.0}

        result = regulator.update(body_state, dt=1.0)

        # Should have no load accumulation for normal values
        assert result["allostatic_load"] == 0.0
        assert result["total_deviation"] == 0.0
        assert result["homeostatic_stability"] == 1.0

        # Check regulatory signals (should be zero for target values)
        signals = result["regulation_signals"]
        assert all(abs(signal) < 1e-10 for signal in signals.values())

        # Check set points status
        status = result["set_points_status"]
        assert len(status) == 4
        for sp_status in status:
            assert sp_status["in_range"] is True
            assert sp_status["load_contribution"] == 0.0

    def test_update_deviated_values(self, regulator: AllostaticRegulator):
        """Test update with deviated physiological values."""
        body_state = {
            "heart_rate": 85.0,  # Above range (65-75)
            "temperature": 37.5,  # Above range (36.8-37.2)
            "glucose": 4.0,  # Below range (4.5-5.5)
            "cortisol": 15.0,  # Above range (8-12)
        }

        result = regulator.update(body_state, dt=1000.0)  # 1 second

        # Should accumulate load
        assert result["allostatic_load"] > 0.0
        assert result["total_deviation"] > 0.0
        assert result["homeostatic_stability"] < 1.0

        # Check regulatory signals (negative for high values, positive for low)
        signals = result["regulation_signals"]
        assert signals["heart_rate"] < 0  # Should decrease heart rate
        assert signals["temperature"] < 0  # Should decrease temperature
        assert signals["glucose"] > 0  # Should increase glucose
        assert signals["cortisol"] < 0  # Should decrease cortisol

    def test_load_decay(self, regulator: AllostaticRegulator):
        """Test that allostatic load decays over time."""
        # First create some load
        body_state = {"heart_rate": 85.0}
        result1 = regulator.update(body_state, dt=1000.0)
        load1 = result1["allostatic_load"]
        assert load1 > 0.0

        # Then update with normal values - load should decay
        body_state = {"heart_rate": 70.0}
        result2 = regulator.update(body_state, dt=1000.0)
        load2 = result2["allostatic_load"]

        # Load should have decayed
        assert load2 < load1

    def test_load_accumulation(self, regulator: AllostaticRegulator):
        """Test load accumulation with sustained deviation."""
        body_state = {"heart_rate": 85.0}  # Out of range

        # Multiple updates should accumulate load
        loads = []
        for i in range(5):
            result = regulator.update(body_state, dt=1000.0)
            loads.append(result["allostatic_load"])

        # Load should increase with each update
        assert loads[0] < loads[1] < loads[2] < loads[3] < loads[4]

    def test_load_clamping(self, regulator: AllostaticRegulator):
        """Test that load is clamped to [0, 1] range."""
        # Create very high load
        for _ in range(100):
            body_state = {"heart_rate": 200.0}  # Extreme deviation
            regulator.update(body_state, dt=1000.0)

        # Load should be clamped to 1.0
        assert regulator.get_allostatic_load() == 1.0

    def test_stressor_trigger(self, regulator: AllostaticRegulator):
        """Test stressor triggering."""
        initial_load = regulator.get_allostatic_load()
        assert initial_load == 0.0

        regulator.trigger_stressor(intensity=0.5)
        new_load = regulator.get_allostatic_load()

        assert new_load == 0.1  # 0.5 * 0.2

        # Trigger again
        regulator.trigger_stressor(intensity=0.8)
        final_load = regulator.get_allostatic_load()

        assert final_load == 0.1 + 0.16  # 0.8 * 0.2

    def test_reset(self, regulator: AllostaticRegulator):
        """Test reset functionality."""
        # Create some load and deviations
        body_state = {"heart_rate": 85.0, "temperature": 38.0}
        regulator.update(body_state, dt=1000.0)

        assert regulator.get_allostatic_load() > 0.0

        # Reset
        regulator.reset()

        assert regulator.get_allostatic_load() == 0.0
        for sp in regulator.set_points:
            assert sp.current_deviation == 0.0
            assert sp.load_contribution == 0.0

    def test_input_validation(self, regulator: AllostaticRegulator):
        """Test input validation."""
        # Test invalid body_state type
        with pytest.raises(TypeError, match="body_state must be dict"):
            regulator.update("not a dict")  # type: ignore[arg-type]

        # Test invalid dt
        body_state = {"heart_rate": 70.0}
        with pytest.raises(ValueError):
            regulator.update(body_state, dt=-1.0)

        # Test invalid body_state values
        with pytest.raises(ValueError):
            regulator.update({"heart_rate": float("inf")})

    def test_stability_computation(self, regulator: AllostaticRegulator):
        """Test stability computation."""
        # Perfect stability
        body_state = {"heart_rate": 70.0, "temperature": 37.0, "glucose": 5.0, "cortisol": 10.0}
        result = regulator.update(body_state)
        assert result["homeostatic_stability"] == 1.0

        # Maximum instability (all at range limits)
        body_state = {
            "heart_rate": 75.0,  # At upper limit
            "temperature": 37.2,  # At upper limit
            "glucose": 5.5,  # At upper limit
            "cortisol": 12.0,  # At upper limit
        }
        result = regulator.update(body_state)
        stability = result["homeostatic_stability"]
        assert 0.0 <= stability < 1.0

    def test_regulatory_signals(self, regulator: AllostaticRegulator):
        """Test regulatory signal generation."""
        body_state = {
            "heart_rate": 80.0,  # Above target (70)
            "temperature": 36.5,  # Below target (37)
        }

        result = regulator.update(body_state)

        signals = result["regulation_signals"]
        # Heart rate above target -> negative signal
        assert signals["heart_rate"] < 0
        # Temperature below target -> positive signal
        assert signals["temperature"] > 0

        # Magnitude should be proportional to deviation
        hr_deviation = 80.0 - 70.0  # 10
        temp_deviation = 36.5 - 37.0  # -0.5

        expected_hr_signal = -0.1 * hr_deviation  # -1.0
        expected_temp_signal = -0.1 * temp_deviation  # 0.05

        assert abs(signals["heart_rate"] - expected_hr_signal) < 1e-10
        assert abs(signals["temperature"] - expected_temp_signal) < 1e-10

    def test_partial_body_state(self, regulator: AllostaticRegulator):
        """Test update with partial body state."""
        # Only provide some variables
        body_state = {"heart_rate": 75.0}
        result = regulator.update(body_state)

        # Should only have signal for heart_rate
        signals = result["regulation_signals"]
        assert "heart_rate" in signals
        assert "temperature" not in signals
        assert "glucose" not in signals
        assert "cortisol" not in signals

        # Should have deviation and load for heart_rate
        assert result["total_deviation"] > 0

    def test_set_points_status(self, regulator: AllostaticRegulator):
        """Test set points status reporting."""
        body_state = {
            "heart_rate": 72.0,  # Slightly above target, within range
            "temperature": 37.5,  # Above range
        }

        result = regulator.update(body_state)
        status = result["set_points_status"]

        # Check heart rate status (in range)
        hr_status = next(s for s in status if s["name"] == "heart_rate")
        assert hr_status["target"] == 70.0
        assert hr_status["deviation"] == 2.0
        assert hr_status["in_range"] is True
        assert hr_status["load_contribution"] == 0.0

        # Check temperature status (out of range)
        temp_status = next(s for s in status if s["name"] == "temperature")
        assert temp_status["target"] == 37.0
        assert temp_status["deviation"] == 0.5
        assert temp_status["in_range"] is False
        assert temp_status["load_contribution"] > 0.0
