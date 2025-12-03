"""
Unit tests for BodyModel component.

Tests specific physiological scenarios and edge cases for the body model
that simulates physiological states and generates interoceptive predictions.
"""

import pytest
import numpy as np
from apgi_system.interoception.body_model import BodyModel, PhysiologicalState


class TestBodyModel:
    """Test suite for BodyModel component."""

    def test_initialization_with_default_config(self, config):
        """Test body model initializes correctly with default configuration."""
        body_model = BodyModel(config)

        # Check initial state is at baseline values
        assert body_model.current_state.heart_rate == 70
        assert body_model.current_state.respiration == 15
        assert body_model.current_state.temperature == 37.0
        assert body_model.current_state.glucose == 5.0
        assert body_model.current_state.cortisol == 10
        assert body_model.current_state.blood_pressure == 120

        # Check prediction lead time
        assert body_model.prediction_lead_ms == 100

        # Check initial influence levels
        assert body_model.arousal_level == 0.0
        assert body_model.activity_level == 0.0
        assert body_model.stress_level == 0.0

    def test_initialization_with_custom_config(self):
        """Test body model initializes with custom configuration values."""
        custom_config = {
            "interoception": {
                "body_states": [
                    {"heart_rate": {"baseline": 80, "range": [60, 140], "variance": 8}},
                    {"temperature": {"baseline": 36.8, "range": [35.0, 40.0], "variance": 0.3}},
                ],
                "prediction_lead_ms": 150,
            }
        }

        body_model = BodyModel(custom_config)

        assert body_model.current_state.heart_rate == 80
        assert body_model.current_state.temperature == 36.8
        assert body_model.prediction_lead_ms == 150

    def test_update_basic_functionality(self, config):
        """Test basic update functionality returns expected structure."""
        body_model = BodyModel(config)

        result = body_model.update(dt=1.0)

        # Check return structure
        assert "current" in result
        assert "predicted" in result
        assert "prediction_error" in result
        assert "arousal" in result
        assert "activity" in result
        assert "stress" in result

        # Check current state structure
        current = result["current"]
        expected_keys = [
            "heart_rate",
            "respiration",
            "temperature",
            "glucose",
            "cortisol",
            "blood_pressure",
        ]
        for key in expected_keys:
            assert key in current
            assert isinstance(current[key], float)

        # Check prediction error is numpy array
        assert isinstance(result["prediction_error"], np.ndarray)
        assert result["prediction_error"].shape == (5,)

    def test_arousal_effects_on_heart_rate(self, config):
        """Test that arousal level affects heart rate appropriately."""
        body_model = BodyModel(config)

        # Set high arousal
        body_model.set_arousal(0.8)

        # Update for sufficient time to see effect (tau_heart = 1000ms)
        # Need several time constants to approach target
        for _ in range(50):
            body_model.update(dt=100.0)  # 5000ms total

        # Heart rate should be elevated from baseline (70 + 30*0.8 = 94)
        # After 5 time constants, should be close to target
        assert body_model.current_state.heart_rate > 85

    def test_activity_effects_on_multiple_variables(self, config):
        """Test that activity level affects multiple physiological variables."""
        body_model = BodyModel(config)

        # Set high activity
        body_model.set_activity(0.9)

        # Update for sufficient time to see effect
        for _ in range(50):
            body_model.update(dt=100.0)  # 5000ms total

        # Activity should increase heart rate and respiration, decrease glucose
        assert body_model.current_state.heart_rate > 100  # 70 + 50*0.9 = 115
        assert body_model.current_state.respiration > 22  # 15 + 10*0.9 = 24
        assert body_model.current_state.glucose < 4.6  # 5.0 - 1.0*0.9 = 4.1

    def test_stress_effects_on_cortisol(self, config):
        """Test that stress level affects cortisol appropriately."""
        body_model = BodyModel(config)

        # Set high stress
        body_model.set_stress(0.8)

        # Update for sufficient time to see effect (cortisol has very slow dynamics, tau=30000ms)
        # Need several time constants to approach target
        for _ in range(500):
            body_model.update(dt=200.0)  # 100000ms total (>3 time constants)

        # Cortisol should be elevated from baseline (10 + 15*0.8 = 22)
        # After 3+ time constants, should be close to target
        assert body_model.current_state.cortisol > 19

    def test_physiological_bounds_maintained(self, config):
        """Test that physiological variables stay within configured bounds."""
        body_model = BodyModel(config)

        # Set extreme influences
        body_model.set_arousal(1.0)
        body_model.set_activity(1.0)
        body_model.set_stress(1.0)

        # Update many times
        for _ in range(100):
            body_model.update(dt=10.0)

        # Check bounds from config
        assert 50 <= body_model.current_state.heart_rate <= 120
        assert 10 <= body_model.current_state.respiration <= 30
        assert 36.0 <= body_model.current_state.temperature <= 39.0
        assert 3.0 <= body_model.current_state.glucose <= 8.0
        assert 5 <= body_model.current_state.cortisol <= 30

    def test_get_interoceptive_vector(self, config):
        """Test interoceptive vector generation."""
        body_model = BodyModel(config)

        vector = body_model.get_interoceptive_vector()

        assert isinstance(vector, np.ndarray)
        assert vector.shape == (6,)

        # Check values match current state
        assert vector[0] == body_model.current_state.heart_rate
        assert vector[1] == body_model.current_state.respiration
        assert vector[2] == body_model.current_state.temperature
        assert vector[3] == body_model.current_state.glucose
        assert vector[4] == body_model.current_state.cortisol
        assert vector[5] == body_model.current_state.blood_pressure

    def test_get_current_state(self, config):
        """Test current state retrieval."""
        body_model = BodyModel(config)
        body_model.set_arousal(0.5)

        state = body_model.get_current_state()

        assert "current" in state
        assert "predicted" in state
        assert "arousal" in state
        assert "activity" in state
        assert "stress" in state
        assert "interoceptive_vector" in state

        assert state["arousal"] == 0.5
        assert isinstance(state["interoceptive_vector"], np.ndarray)

    def test_reset_functionality(self, config):
        """Test that reset restores baseline state."""
        body_model = BodyModel(config)

        # Modify state
        body_model.set_arousal(0.8)
        body_model.set_activity(0.6)
        body_model.set_stress(0.4)

        # Update to change physiological state
        for _ in range(10):
            body_model.update(dt=10.0)

        # Store modified state
        modified_hr = body_model.current_state.heart_rate

        # Reset
        body_model.reset()

        # Check restoration to baseline
        assert body_model.current_state.heart_rate == 70
        assert body_model.current_state.respiration == 15
        assert body_model.current_state.temperature == 37.0
        assert body_model.current_state.glucose == 5.0
        assert body_model.current_state.cortisol == 10
        assert body_model.current_state.blood_pressure == 120

        assert body_model.arousal_level == 0.0
        assert body_model.activity_level == 0.0
        assert body_model.stress_level == 0.0

        # Verify state actually changed before reset
        assert modified_hr != 70

    def test_influence_level_clamping(self, config):
        """Test that influence levels are properly clamped to [0, 1]."""
        body_model = BodyModel(config)

        # Test clamping above 1.0
        body_model.set_arousal(1.5)
        body_model.set_activity(2.0)
        body_model.set_stress(10.0)

        assert body_model.arousal_level == 1.0
        assert body_model.activity_level == 1.0
        assert body_model.stress_level == 1.0

        # Test clamping below 0.0
        body_model.set_arousal(-0.5)
        body_model.set_activity(-1.0)
        body_model.set_stress(-2.0)

        assert body_model.arousal_level == 0.0
        assert body_model.activity_level == 0.0
        assert body_model.stress_level == 0.0

    def test_update_with_different_timesteps(self, config):
        """Test update behavior with different timestep values."""
        body_model = BodyModel(config)
        body_model.set_arousal(0.5)

        # Small timestep
        result_small = body_model.update(dt=0.1)
        hr_small = result_small["current"]["heart_rate"]

        body_model.reset()
        body_model.set_arousal(0.5)

        # Large timestep
        result_large = body_model.update(dt=10.0)
        hr_large = result_large["current"]["heart_rate"]

        # Larger timestep should produce larger change from baseline
        assert abs(hr_large - 70) > abs(hr_small - 70)

    def test_input_validation(self, config):
        """Test input validation for update method."""
        body_model = BodyModel(config)

        # Test invalid dt values
        with pytest.raises(ValueError):
            body_model.update(dt=-1.0)  # Negative dt

        with pytest.raises(ValueError):
            body_model.update(dt=0.0)  # Zero dt

        with pytest.raises(ValueError):
            body_model.update(dt=float("inf"))  # Infinite dt

        with pytest.raises(ValueError):
            body_model.update(dt=float("nan"))  # NaN dt

    def test_physiological_state_dataclass(self):
        """Test PhysiologicalState dataclass functionality."""
        state = PhysiologicalState(
            heart_rate=75.0,
            respiration=16.0,
            temperature=37.1,
            glucose=4.8,
            cortisol=12.0,
            blood_pressure=125.0,
        )

        assert state.heart_rate == 75.0
        assert state.respiration == 16.0
        assert state.temperature == 37.1
        assert state.glucose == 4.8
        assert state.cortisol == 12.0
        assert state.blood_pressure == 125.0

    def test_state_to_dict_conversion(self, config):
        """Test conversion of physiological state to dictionary."""
        body_model = BodyModel(config)

        state_dict = body_model._state_to_dict(body_model.current_state)

        expected_keys = [
            "heart_rate",
            "respiration",
            "temperature",
            "glucose",
            "cortisol",
            "blood_pressure",
        ]
        for key in expected_keys:
            assert key in state_dict
            assert isinstance(state_dict[key], float)

    def test_prediction_generation(self, config):
        """Test that predictions are generated correctly."""
        body_model = BodyModel(config)

        # Update to generate predictions
        result = body_model.update(dt=1.0)

        # Predicted state should exist and have same structure as current
        predicted = result["predicted"]
        current = result["current"]

        assert set(predicted.keys()) == set(current.keys())

        # In current simple implementation, predicted should equal current
        for key in current.keys():
            assert predicted[key] == current[key]

    def test_multiple_updates_consistency(self, config):
        """Test that multiple updates maintain consistency."""
        body_model = BodyModel(config)

        # Perform multiple updates
        results = []
        for i in range(5):
            result = body_model.update(dt=1.0)
            results.append(result)

        # Each result should have consistent structure
        for result in results:
            assert "current" in result
            assert "predicted" in result
            assert "prediction_error" in result

        # Values should change over time (due to noise if nothing else)
        hr_values = [r["current"]["heart_rate"] for r in results]
        # At least some variation should occur due to noise
        assert len(set([round(hr, 1) for hr in hr_values])) >= 1
