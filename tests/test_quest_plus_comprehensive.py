#!/usr/bin/env python3
"""
Comprehensive tests for QUEST+ adaptive staircase implementation.

Tests cover:
- Parameter validation and initialization
- Psychometric function computation
- Prior distribution management
- Trial-by-trial adaptation
- Convergence detection
"""

import json
import pickle
from dataclasses import asdict

import numpy as np
import pytest

# Import the modules we're testing
try:
    from apgi_framework.adaptive.quest_plus_staircase import (
        QuestPlusParameters,
        QuestPlusStaircase,
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
        assert params.threshold_prior is None
        assert params.slope_prior is None
        assert params.min_trials == 20
        assert params.max_trials == 200
        assert params.convergence_criterion == 0.05
        assert params.min_reversals == 4

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_custom_initialization(self):
        """Test custom parameter initialization."""
        custom_prior = np.ones(10) / 10
        params = QuestPlusParameters(
            stimulus_min=0.1,
            stimulus_max=2.0,
            stimulus_steps=100,
            threshold_prior=custom_prior,
            slope_prior=custom_prior,
            min_trials=30,
            max_trials=300,
        )

        assert params.stimulus_min == 0.1
        assert params.stimulus_max == 2.0
        assert params.stimulus_steps == 100
        assert np.array_equal(params.threshold_prior, custom_prior)
        assert np.array_equal(params.slope_prior, custom_prior)
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
        # Test mismatched prior sizes
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
        json_str = params.to_json() if hasattr(params, "to_json") else json.dumps(asdict(params))
        reconstructed = QuestPlusParameters(**json.loads(json_str))

        assert reconstructed.stimulus_min == params.stimulus_min
        assert reconstructed.stimulus_max == params.stimulus_max
        assert reconstructed.stimulus_steps == params.stimulus_steps


class TestPsychometricFunction:
    """Test psychometric function computation."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_basic_psychometric_function(self):
        """Test basic psychometric function computation."""
        stimulus_levels = np.linspace(0.01, 1.0, 50)
        threshold = 0.5
        slope = 3.0
        lapse_rate = 0.02
        guess_rate = 0.5

        response_rates = compute_psychometric_function(
            stimulus_levels, threshold, slope, lapse_rate, guess_rate
        )

        # Check output properties
        assert len(response_rates) == len(stimulus_levels)
        assert np.all(response_rates >= guess_rate)  # Lower bound
        assert np.all(response_rates <= 1.0 - lapse_rate + guess_rate)  # Upper bound
        assert np.all(np.isfinite(response_rates))

        # Check monotonicity
        assert np.all(np.diff(response_rates) >= 0)  # Should be non-decreasing

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_psychometric_function_edge_cases(self):
        """Test psychometric function with edge case parameters."""
        stimulus_levels = np.linspace(0.01, 1.0, 50)

        # Test with zero lapse rate
        response_rates = compute_psychometric_function(stimulus_levels, 0.5, 3.0, 0.0, 0.0)
        assert np.all(response_rates >= 0.0)
        assert np.all(response_rates <= 1.0)

        # Test with high guess rate (1AFC)
        response_rates = compute_psychometric_function(stimulus_levels, 0.5, 3.0, 0.02, 0.0)
        assert np.all(response_rates >= 0.0)

        # Test with extreme threshold
        response_rates_low = compute_psychometric_function(stimulus_levels, 0.01, 3.0, 0.02, 0.5)
        response_rates_high = compute_psychometric_function(stimulus_levels, 1.0, 3.0, 0.02, 0.5)

        # Low threshold should produce higher response rates
        assert np.mean(response_rates_low) > np.mean(response_rates_high)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_psychometric_function_parameter_sensitivity(self):
        """Test sensitivity to parameter changes."""
        stimulus_levels = np.linspace(0.01, 1.0, 50)

        # Test slope sensitivity
        response_shallow = compute_psychometric_function(stimulus_levels, 0.5, 1.0, 0.02, 0.5)
        response_steep = compute_psychometric_function(stimulus_levels, 0.5, 10.0, 0.02, 0.5)

        # Steeper slope should have more transition
        steepness_diff = np.std(response_steep) - np.std(response_shallow)
        assert steepness_diff > 0  # Steeper should have higher variance

        # Test threshold shift
        response_low = compute_psychometric_function(stimulus_levels, 0.3, 3.0, 0.02, 0.5)
        response_high = compute_psychometric_function(stimulus_levels, 0.7, 3.0, 0.02, 0.5)

        # Higher threshold should shift curve right
        midpoint_idx = len(stimulus_levels) // 2
        assert response_low[midpoint_idx] > response_high[midpoint_idx]


class TestPosteriorDistribution:
    """Test posterior distribution computation."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_basic_posterior_computation(self):
        """Test basic posterior distribution computation."""
        # Create test priors
        threshold_prior = np.ones(40) / 40
        slope_prior = np.ones(20) / 20

        # Create likelihood matrix
        likelihood = np.random.dirichlet(np.ones(40 * 20)).reshape(40, 20)

        # Compute posterior
        posterior = compute_posterior_distribution(threshold_prior, slope_prior, likelihood)

        # Check properties
        assert posterior.shape == (40, 20)
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0, rtol=1e-10)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_posterior_edge_cases(self):
        """Test posterior computation with edge cases."""
        # Test with uniform priors
        threshold_prior = np.ones(40) / 40
        slope_prior = np.ones(20) / 20

        # Test with deterministic likelihood
        likelihood = np.zeros((40, 20))
        likelihood[20, 10] = 1.0  # Single peak

        posterior = compute_posterior_distribution(threshold_prior, slope_prior, likelihood)

        # Posterior should match likelihood for uniform priors
        assert np.argmax(posterior) == 20 * 20 + 10

        # Test with zero likelihood (should handle gracefully)
        zero_likelihood = np.zeros((40, 20))

        with pytest.raises(ValueError):
            compute_posterior_distribution(threshold_prior, slope_prior, zero_likelihood)


class TestConvergenceDetection:
    """Test convergence detection algorithms."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_basic_convergence_detection(self):
        """Test basic convergence detection."""
        # Create converging threshold estimates
        thresholds = np.array([0.5, 0.52, 0.48, 0.51, 0.49, 0.505, 0.495])
        trials = np.arange(len(thresholds))
        responses = np.array([1, 1, 0, 1, 0, 1, 0])
        stimulus_levels = thresholds  # Simplified case

        converged, convergence_info = detect_convergence(
            thresholds, trials, responses, stimulus_levels, convergence_criterion=0.05, min_trials=5
        )

        assert isinstance(converged, bool)
        assert "criterion_met" in convergence_info
        assert "threshold_change" in convergence_info
        assert "reversals" in convergence_info

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_convergence_insufficient_trials(self):
        """Test convergence detection with insufficient trials."""
        thresholds = np.array([0.5, 0.52])
        trials = np.arange(len(thresholds))
        responses = np.array([1, 1])
        stimulus_levels = thresholds

        converged, convergence_info = detect_convergence(
            thresholds, trials, responses, stimulus_levels, convergence_criterion=0.05, min_trials=5
        )

        assert not converged
        assert not convergence_info["criterion_met"]
        assert "insufficient_trials" in convergence_info

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_convergence_reversal_detection(self):
        """Test reversal detection in convergence."""
        # Create pattern with clear reversals
        thresholds = np.array([0.5, 0.6, 0.7, 0.6, 0.5, 0.4, 0.5, 0.6])
        trials = np.arange(len(thresholds))
        responses = np.array([1, 1, 1, 0, 0, 0, 1, 1])
        stimulus_levels = thresholds

        converged, convergence_info = detect_convergence(
            thresholds,
            trials,
            responses,
            stimulus_levels,
            convergence_criterion=0.05,
            min_trials=5,
            min_reversals=3,
        )

        assert "reversals" in convergence_info
        assert convergence_info["reversals"] >= 3


class TestQuestPlusStaircase:
    """Test the main QUEST+ staircase class."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_initialization(self):
        """Test staircase initialization."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        assert staircase.parameters == params
        assert staircase.current_trial == 0
        assert len(staircase.stimulus_levels) == params.stimulus_steps
        assert len(staircase.threshold_grid) == params.threshold_steps
        assert len(staircase.slope_grid) == params.slope_steps
        assert staircase.posterior.shape == (params.threshold_steps, params.slope_steps)
        assert np.isclose(np.sum(staircase.posterior), 1.0)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_first_trial(self):
        """Test first trial selection."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        stimulus_level, trial_info = staircase.get_next_stimulus()

        assert isinstance(stimulus_level, float)
        assert params.stimulus_min <= stimulus_level <= params.stimulus_max
        assert "trial_number" in trial_info
        assert "selected_stimulus" in trial_info
        assert "posterior_entropy" in trial_info
        assert trial_info["trial_number"] == 0

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_trial_update(self):
        """Test trial update with response."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Get first stimulus
        stimulus_level, _ = staircase.get_next_stimulus()

        # Update with response
        posterior_before = staircase.posterior.copy()
        staircase.update_trial(stimulus_level, response=1)

        # Check updates
        assert staircase.current_trial == 1
        assert not np.array_equal(staircase.posterior, posterior_before)
        assert len(staircase.trial_history) == 1
        assert staircase.trial_history[0]["stimulus"] == stimulus_level
        assert staircase.trial_history[0]["response"] == 1

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_multiple_trials(self):
        """Test multiple trial progression."""
        params = QuestPlusParameters(min_trials=10, max_trials=50)
        staircase = QuestPlusStaircase(params)

        trial_count = 0
        max_trials_to_test = 20

        while trial_count < max_trials_to_test and not staircase.is_converged():
            stimulus_level, _ = staircase.get_next_stimulus()
            # Simulate response based on psychometric function
            response_prob = compute_psychometric_function(
                np.array([stimulus_level]), 0.5, 3.0, 0.02, 0.5
            )[0]
            response = 1 if np.random.random() < response_prob else 0

            staircase.update_trial(stimulus_level, response)
            trial_count += 1

        assert staircase.current_trial > 0
        assert len(staircase.trial_history) == staircase.current_trial

        # Check threshold estimate
        threshold_estimate = staircase.get_threshold_estimate()
        assert isinstance(threshold_estimate, float)
        assert params.threshold_min <= threshold_estimate <= params.threshold_max

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_convergence(self):
        """Test convergence detection."""
        params = QuestPlusParameters(min_trials=10, max_trials=100, convergence_criterion=0.1)
        staircase = QuestPlusStaircase(params)

        # Simulate consistent responses around true threshold
        true_threshold = 0.5
        trial_count = 0

        while trial_count < 50 and not staircase.is_converged():
            stimulus_level, _ = staircase.get_next_stimulus()

            # Generate response with some noise
            response_prob = compute_psychometric_function(
                np.array([stimulus_level]), true_threshold, 3.0, 0.02, 0.5
            )[0]
            response = 1 if np.random.random() < response_prob else 0

            staircase.update_trial(stimulus_level, response)
            trial_count += 1

        # Should converge after sufficient trials
        if staircase.current_trial >= params.min_trials:
            convergence_info = staircase.get_convergence_info()
            assert "converged" in convergence_info
            assert "criterion" in convergence_info

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_max_trials_limit(self):
        """Test maximum trials limit."""
        params = QuestPlusParameters(max_trials=10)
        staircase = QuestPlusStaircase(params)

        # Run until max trials
        for i in range(params.max_trials + 5):
            if staircase.current_trial >= params.max_trials:
                break

            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)

        # Should stop at max trials
        assert staircase.current_trial <= params.max_trials
        assert staircase.trial_limit_reached()

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_state_management(self):
        """Test state save/load functionality."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run a few trials
        for i in range(5):
            stimulus_level, _ = staircase.get_next_stimulus()
            response = 1 if i % 2 == 0 else 0
            staircase.update_trial(stimulus_level, response)

        # Save state
        state = staircase.save_state()

        # Check state contents
        assert "current_trial" in state
        assert "posterior" in state
        assert "trial_history" in state
        assert "parameters" in state
        assert state["current_trial"] == 5

        # Create new staircase and load state
        new_staircase = QuestPlusStaircase(params)
        new_staircase.load_state(state)

        # Verify state restoration
        assert new_staircase.current_trial == staircase.current_trial
        assert np.array_equal(new_staircase.posterior, staircase.posterior)
        assert len(new_staircase.trial_history) == len(staircase.trial_history)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_parameter_estimates(self):
        """Test parameter estimation methods."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run some trials
        for i in range(10):
            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)

        # Get estimates
        threshold_estimate = staircase.get_threshold_estimate()
        slope_estimate = staircase.get_slope_estimate()

        assert isinstance(threshold_estimate, float)
        assert isinstance(slope_estimate, float)
        assert params.threshold_min <= threshold_estimate <= params.threshold_max
        assert params.slope_min <= slope_estimate <= params.slope_max

        # Get confidence intervals
        threshold_ci = staircase.get_threshold_confidence_interval()
        slope_ci = staircase.get_slope_confidence_interval()

        assert len(threshold_ci) == 2
        assert len(slope_ci) == 2
        assert threshold_ci[0] <= threshold_estimate <= threshold_ci[1]
        assert slope_ci[0] <= slope_estimate <= slope_ci[1]

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_staircase_entropy_tracking(self):
        """Test entropy tracking for information gain."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        initial_entropy = staircase.get_posterior_entropy()

        # Run trials and track entropy
        entropies = [initial_entropy]
        for i in range(10):
            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)
            entropies.append(staircase.get_posterior_entropy())

        # Entropy should generally decrease (or stay same)
        assert len(entropies) == 11
        assert all(isinstance(e, float) for e in entropies)
        assert all(e >= 0 for e in entropies)

        # Check information gain calculation
        information_gains = staircase.get_information_gains()
        assert len(information_gains) == 10  # One less than trials
        assert all(isinstance(g, float) for g in information_gains)


class TestQuestPlusEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_extreme_parameter_values(self):
        """Test with extreme parameter values."""
        # Very small stimulus range
        params = QuestPlusParameters(stimulus_min=0.001, stimulus_max=0.01, stimulus_steps=10)
        staircase = QuestPlusStaircase(params)

        # Should still work
        stimulus_level, _ = staircase.get_next_stimulus()
        assert params.stimulus_min <= stimulus_level <= params.stimulus_max

        # Very large slope range
        params = QuestPlusParameters(slope_min=0.1, slope_max=100.0, slope_steps=50)
        staircase = QuestPlusStaircase(params)

        stimulus_level, _ = staircase.get_next_stimulus()
        assert isinstance(stimulus_level, float)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_invalid_responses(self):
        """Test handling of invalid responses."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        stimulus_level, _ = staircase.get_next_stimulus()

        # Test invalid response values
        with pytest.raises(ValueError):
            staircase.update_trial(stimulus_level, response=2)

        with pytest.raises(ValueError):
            staircase.update_trial(stimulus_level, response=-1)

        with pytest.raises(ValueError):
            staircase.update_trial(stimulus_level, response=0.5)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_invalid_stimulus_levels(self):
        """Test handling of invalid stimulus levels."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Test stimulus outside valid range
        with pytest.raises(ValueError):
            staircase.update_trial(params.stimulus_min - 0.01, response=1)

        with pytest.raises(ValueError):
            staircase.update_trial(params.stimulus_max + 0.01, response=1)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_numerical_stability(self):
        """Test numerical stability with extreme values."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Test with very small/large numbers
        for i in range(10):
            stimulus_level, _ = staircase.get_next_stimulus()

            # Add tiny numerical noise
            noisy_stimulus = stimulus_level + np.random.normal(0, 1e-10)
            staircase.update_trial(noisy_stimulus, response=1)

            # Check posterior remains valid
            assert np.all(np.isfinite(staircase.posterior))
            assert np.isclose(np.sum(staircase.posterior), 1.0, rtol=1e-10)


class TestQuestPlusPerformance:
    """Test performance characteristics."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_performance_large_grids(self):
        """Test performance with large parameter grids."""
        import time

        # Create large parameter space
        params = QuestPlusParameters(stimulus_steps=200, threshold_steps=100, slope_steps=50)

        start_time = time.time()
        staircase = QuestPlusStaircase(params)
        init_time = time.time() - start_time

        # Should initialize reasonably quickly
        assert init_time < 5.0  # 5 seconds max

        # Test trial update performance
        start_time = time.time()
        for i in range(10):
            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)
        trial_time = time.time() - start_time

        # Should handle trials quickly
        assert trial_time < 2.0  # 2 seconds for 10 trials

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_memory_usage(self):
        """Test memory usage with different grid sizes."""
        import sys

        # Test small grid
        params_small = QuestPlusParameters(stimulus_steps=10, threshold_steps=10, slope_steps=10)
        staircase_small = QuestPlusStaircase(params_small)

        # Test large grid
        params_large = QuestPlusParameters(stimulus_steps=100, threshold_steps=100, slope_steps=50)
        staircase_large = QuestPlusStaircase(params_large)

        # Large grid should use more memory but not excessively
        small_size = sys.getsizeof(staircase_small.posterior)
        large_size = sys.getsizeof(staircase_large.posterior)

        assert large_size > small_size
        assert large_size < 100 * small_size  # Shouldn't be 100x larger


# Integration tests
class TestQuestPlusIntegration:
    """Test QUEST+ integration with other components."""

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_json_serialization_roundtrip(self):
        """Test complete JSON serialization roundtrip."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run some trials
        for i in range(5):
            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)

        # Serialize to JSON
        json_state = (
            staircase.to_json()
            if hasattr(staircase, "to_json")
            else json.dumps(staircase.save_state())
        )

        # Deserialize
        state_dict = json.loads(json_state)
        new_staircase = QuestPlusStaircase(params)
        new_staircase.load_state(state_dict)

        # Verify equivalence
        assert new_staircase.current_trial == staircase.current_trial
        assert np.allclose(new_staircase.posterior, staircase.posterior)

    @pytest.mark.skipif(not QUEST_PLUS_AVAILABLE, reason="QUEST+ module not available")
    def test_pickle_serialization(self):
        """Test pickle serialization."""
        params = QuestPlusParameters()
        staircase = QuestPlusStaircase(params)

        # Run some trials
        for i in range(5):
            stimulus_level, _ = staircase.get_next_stimulus()
            staircase.update_trial(stimulus_level, response=1)

        # Pickle and unpickle
        pickled = pickle.dumps(staircase)
        unpickled = pickle.loads(pickled)

        # Verify equivalence
        assert unpickled.current_trial == staircase.current_trial
        assert np.allclose(unpickled.posterior, staircase.posterior)


# Helper functions for testing
def compute_psychometric_function(stimulus_levels, threshold, slope, lapse_rate, guess_rate):
    """Compute psychometric function for testing purposes."""
    from scipy.stats import norm

    # Standard psychometric function (cumulative normal)
    z = (stimulus_levels - threshold) / slope
    psychometric = norm.cdf(z)

    # Apply lapse and guess rates
    return guess_rate + (1 - lapse_rate - guess_rate) * psychometric


def compute_posterior_distribution(threshold_prior, slope_prior, likelihood):
    """Compute posterior distribution for testing purposes."""
    # Normalize likelihood
    normalized_likelihood = likelihood / np.sum(likelihood)

    # Compute posterior (simplified - assumes uniform priors)
    posterior = normalized_likelihood * np.outer(threshold_prior, slope_prior)

    # Normalize posterior
    posterior = posterior / np.sum(posterior)

    # Check if posterior is valid
    if np.sum(posterior) == 0:
        raise ValueError("Posterior is zero - likelihood may be invalid")

    return posterior


def detect_convergence(
    thresholds,
    trials,
    responses,
    stimulus_levels,
    convergence_criterion=0.05,
    min_trials=5,
    min_reversals=3,
):
    """Detect convergence in threshold estimates for testing purposes."""
    if len(thresholds) < min_trials:
        return False, {
            "criterion_met": False,
            "threshold_change": float("inf"),
            "reversals": 0,
            "insufficient_trials": True,
        }

    # Calculate threshold change
    recent_thresholds = thresholds[-min(5, len(thresholds)) :]
    if len(recent_thresholds) >= 2:
        threshold_change = np.std(recent_thresholds)
        criterion_met = threshold_change < convergence_criterion
    else:
        threshold_change = float("inf")
        criterion_met = False

    # Count reversals (simplified)
    reversals = 0
    if len(thresholds) >= 3:
        for i in range(2, len(thresholds)):
            if (thresholds[i] > thresholds[i - 1] and thresholds[i - 1] < thresholds[i - 2]) or (
                thresholds[i] < thresholds[i - 1] and thresholds[i - 1] > thresholds[i - 2]
            ):
                reversals += 1

    convergence_info = {
        "criterion_met": criterion_met,
        "threshold_change": threshold_change,
        "reversals": reversals,
    }

    if len(thresholds) < min_trials:
        convergence_info["insufficient_trials"] = True

    return criterion_met and reversals >= min_reversals, convergence_info


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
