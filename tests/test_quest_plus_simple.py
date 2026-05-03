#!/usr/bin/env python3
"""
Simple tests for QUEST+ adaptive staircase module.

Tests cover the actual functionality available in the module.
"""

import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

# Import the modules we're testing
try:
    from apgi_framework.adaptive.quest_plus_staircase import (
        QuestPlusParameters,
        QuestPlusStaircase,
        StaircaseState,
    )

    QUEST_PLUS_AVAILABLE = True
except ImportError:
    QUEST_PLUS_AVAILABLE = False


class TestQuestPlusParameters:
    """Test QuestPlusParameters dataclass and validation."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = QuestPlusParameters()

        assert params.stimulus_min == 0.01
        assert params.stimulus_max == 1.0
        assert params.stimulus_steps == 50
        assert params.threshold_min == 0.01
        assert params.threshold_max == 1.0
        assert params.threshold_steps == 40
        assert params.slope_min == 1.0
        assert params.slope_max == 10.0
        assert params.slope_steps == 20
        assert params.lapse_rate == 0.02
        assert params.guess_rate == 0.5
        assert params.min_trials == 20
        assert params.max_trials == 200
        assert params.convergence_criterion == 0.05
        assert params.min_reversals == 4

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_custom_initialization(self):
        """Test custom parameter initialization."""
        threshold_prior = np.ones(40) / 40
        slope_prior = np.ones(20) / 20
        params = QuestPlusParameters(
            stimulus_min=0.1,
            stimulus_max=2.0,
            stimulus_steps=100,
            threshold_prior=threshold_prior,
            slope_prior=slope_prior,
            min_trials=30,
            max_trials=300,
        )

        assert params.stimulus_min == 0.1
        assert params.stimulus_max == 2.0
        assert params.stimulus_steps == 100
        assert np.array_equal(params.threshold_prior, threshold_prior)
        assert np.array_equal(params.slope_prior, slope_prior)
        assert params.min_trials == 30
        assert params.max_trials == 300

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Test invalid ranges
        with pytest.raises(ValueError):
            QuestPlusParameters(stimulus_min=1.0, stimulus_max=0.5)

        with pytest.raises(ValueError):
            QuestPlusParameters(threshold_min=1.0, threshold_max=0.5)

        with pytest.raises(ValueError):
            QuestPlusParameters(slope_min=10.0, slope_max=5.0)

        # Test invalid steps
        with pytest.raises(ValueError):
            QuestPlusParameters(stimulus_steps=0)

        with pytest.raises(ValueError):
            QuestPlusParameters(threshold_steps=-1)

        # Test invalid rates
        with pytest.raises(ValueError):
            QuestPlusParameters(lapse_rate=-0.1)

        with pytest.raises(ValueError):
            QuestPlusParameters(lapse_rate=1.5)

        with pytest.raises(ValueError):
            QuestPlusParameters(guess_rate=-0.1)

        with pytest.raises(ValueError):
            QuestPlusParameters(guess_rate=1.5)

        # Test invalid convergence criteria
        with pytest.raises(ValueError):
            QuestPlusParameters(convergence_criterion=-0.01)

        with pytest.raises(ValueError):
            QuestPlusParameters(min_trials=0)

        with pytest.raises(ValueError):
            QuestPlusParameters(max_trials=0)

        with pytest.raises(ValueError):
            QuestPlusParameters(min_reversals=0)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_prior_validation(self):
        """Test prior distribution validation."""
        # Test wrong size priors
        invalid_prior = np.ones(5)

        with pytest.raises(ValueError):
            QuestPlusParameters(threshold_prior=invalid_prior)

        with pytest.raises(ValueError):
            QuestPlusParameters(slope_prior=invalid_prior)

        # Test non-normalized priors
        non_normalized_prior = np.ones(40) * 2  # Sum = 80, not 1

        with pytest.raises(ValueError):
            QuestPlusParameters(threshold_prior=non_normalized_prior)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_parameter_serialization(self):
        """Test parameter serialization/deserialization."""
        params = QuestPlusParameters()

        # Test JSON serialization
        json_str = json.dumps(asdict(params))
        reconstructed = QuestPlusParameters(**json.loads(json_str))

        assert reconstructed.stimulus_min == params.stimulus_min
        assert reconstructed.stimulus_max == params.stimulus_max
        assert reconstructed.stimulus_steps == params.stimulus_steps


class TestStaircaseState:
    """Test StaircaseState dataclass and operations."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_state_creation(self):
        """Test state creation."""
        state = StaircaseState()

        assert state.trial_number == 0
        assert state.current_intensity == 0.5
        assert state.threshold_estimate == 0.5
        assert state.threshold_std == 0.2
        assert len(state.intensities) == 0
        assert len(state.responses) == 0
        assert len(state.timestamps) == 0
        assert state.reversals == 0
        assert state.last_direction is None
        assert state.converged is False
        assert state.convergence_trial is None
        assert state.posterior is None

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_state_serialization(self):
        """Test state serialization/deserialization."""
        state = StaircaseState(
            trial_number=5,
            current_intensity=0.75,
            threshold_estimate=0.68,
            threshold_std=0.15,
            intensities=[0.3, 0.4, 0.5, 0.6, 0.7],
            responses=[True, False, True, True, False],
            reversals=2,
            last_direction=1,
            converged=False,
        )

        # Test to_dict
        state_dict = state.to_dict()
        assert state_dict["trial_number"] == 5
        assert state_dict["current_intensity"] == 0.75
        assert state_dict["threshold_estimate"] == 0.68
        assert len(state_dict["intensities"]) == 5
        assert len(state_dict["responses"]) == 5

        # Test from_dict
        reconstructed = StaircaseState.from_dict(state_dict)
        assert reconstructed.trial_number == state.trial_number
        assert reconstructed.current_intensity == state.current_intensity
        assert reconstructed.threshold_estimate == state.threshold_estimate
        assert reconstructed.reversals == state.reversals
        assert reconstructed.last_direction == state.last_direction


class TestQuestPlusStaircase:
    """Test QuestPlusStaircase class."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_initialization(self):
        """Test staircase initialization."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        assert staircase.parameters == params
        assert staircase.state.trial_number == 0
        assert not staircase.state.converged
        assert staircase.should_continue()

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_with_custom_parameters(self):
        """Test staircase with custom parameters."""
        params = QuestPlusParameters(
            stimulus_min=0.1, stimulus_max=0.9, stimulus_steps=20, min_trials=5, max_trials=50
        )
        staircase = QuestPlusStaircase(params)

        assert staircase.parameters == params
        assert staircase.should_continue()

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_get_next_intensity(self):
        """Test getting next stimulus intensity."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        intensity = staircase.get_next_intensity()
        assert isinstance(intensity, float)
        assert params.stimulus_min <= intensity <= params.stimulus_max

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_update_with_response(self):
        """Test updating staircase with response."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Get initial intensity
        intensity = staircase.get_next_intensity()
        initial_trial = staircase.state.trial_number

        # Update with response
        staircase.update(intensity, True)

        # Check state updated
        assert staircase.state.trial_number == initial_trial + 1
        assert len(staircase.state.intensities) == 1
        assert len(staircase.state.responses) == 1
        assert staircase.state.intensities[0] == intensity
        assert staircase.state.responses[0] is True

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_multiple_trials(self):
        """Test multiple trial progression."""
        params = QuestPlusParameters(max_trials=10)
        staircase = QuestPlusStaircase(params)

        trial_count = 0
        while staircase.should_continue() and trial_count < 5:
            intensity = staircase.get_next_intensity()
            response = trial_count % 2 == 0  # Alternate responses
            staircase.update(intensity, response)
            trial_count += 1

        assert staircase.state.trial_number > 0
        assert len(staircase.state.intensities) == staircase.state.trial_number
        assert len(staircase.state.responses) == staircase.state.trial_number

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_threshold_estimate(self):
        """Test threshold estimation."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run a few trials
        for i in range(3):
            intensity = staircase.get_next_intensity()
            staircase.update(intensity, True)

        # Get threshold estimate
        threshold, std = staircase.get_threshold_estimate()
        assert isinstance(threshold, float)
        assert isinstance(std, float)
        assert params.threshold_min <= threshold <= params.threshold_max
        assert std >= 0

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_psychometric_curve(self):
        """Test getting psychometric curve."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run a few trials to establish estimate
        for i in range(3):
            intensity = staircase.get_next_intensity()
            staircase.update(intensity, True)

        # Get psychometric curve
        intensities, probs = staircase.get_psychometric_curve()

        assert len(intensities) == len(probs)
        assert all(0 <= p <= 1 for p in probs)
        assert all(params.stimulus_min <= i <= params.stimulus_max for i in intensities)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_state_persistence(self):
        """Test state save/load functionality."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run some trials
        for i in range(3):
            intensity = staircase.get_next_intensity()
            staircase.update(intensity, True)

        # Save state
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            state_file = f.name

        try:
            staircase.save_state(state_file)

            # Load state in new staircase
            new_staircase = QuestPlusStaircase(params)
            new_staircase.load_state(state_file)

            # Verify state restoration
            assert new_staircase.state.trial_number == staircase.state.trial_number
            assert new_staircase.state.intensities == staircase.state.intensities
            assert new_staircase.state.responses == staircase.state.responses
        finally:
            Path(state_file).unlink()  # Clean up

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_performance_summary(self):
        """Test performance summary."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Test with no trials
        summary = staircase.get_performance_summary()
        assert "error" in summary

        # Run some trials
        for i in range(3):
            intensity = staircase.get_next_intensity()
            staircase.update(intensity, True)

        # Get summary
        summary = staircase.get_performance_summary()
        assert "total_trials" in summary
        assert "threshold_estimate" in summary
        assert "threshold_std" in summary
        assert summary["total_trials"] == 3

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_convergence_checking(self):
        """Test convergence checking."""
        params = QuestPlusParameters(min_trials=5, max_trials=20)
        staircase = QuestPlusStaircase(params)

        # Initially not converged
        assert not staircase.is_converged()
        assert staircase.should_continue()

        # Run trials up to max
        for i in range(25):  # More than max_trials
            if not staircase.should_continue():
                break
            intensity = staircase.get_next_intensity()
            staircase.update(intensity, i % 2 == 0)

        # Should stop at max trials
        assert not staircase.should_continue()
        assert staircase.state.trial_number <= params.max_trials


class TestQuestPlusEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_invalid_response_type(self):
        """Test handling of invalid response types."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        intensity = staircase.get_next_intensity()

        # Test invalid response types
        with pytest.raises((TypeError, ValueError)):
            staircase.update(intensity, "invalid")

        with pytest.raises((TypeError, ValueError)):
            staircase.update(intensity, 2)

        with pytest.raises((TypeError, ValueError)):
            staircase.update(intensity, None)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_invalid_intensity(self):
        """Test handling of invalid intensity values."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Test invalid intensity values
        with pytest.raises((ValueError, TypeError)):
            staircase.update(params.stimulus_min - 0.01, True)

        with pytest.raises((ValueError, TypeError)):
            staircase.update(params.stimulus_max + 0.01, True)

        with pytest.raises((ValueError, TypeError)):
            staircase.update(None, True)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_file_io_errors(self):
        """Test handling of file I/O errors."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Test saving to invalid path
        with pytest.raises((FileNotFoundError, PermissionError, OSError)):
            staircase.save_state("/invalid/path/state.json")

        # Test loading from invalid path
        with pytest.raises((FileNotFoundError, PermissionError, OSError)):
            staircase.load_state("/invalid/path/state.json")


# Mock tests for when QUEST+ is not available
class TestQuestPlusMock:
    """Mock tests when QUEST+ module is not available."""

    @pytest.mark.skipif(QUEST_PLUS_AVAILABLE, reason="QUEST+ module is available")
    def test_module_unavailable(self):
        """Test behavior when QUEST+ module is not available."""
        with pytest.raises(ImportError):
            from apgi_framework.adaptive.quest_plus_staircase import (  # noqa: F401
                QuestPlusStaircase,
            )


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
