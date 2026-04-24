"""
Tests for core analysis modules.
"""

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")  # Use non-interactive backend for testing

# Import the functions from the core analysis modules
import sys
from pathlib import Path

# Add core models to path
sys.path.append(str(Path(__file__).parent.parent / "core" / "analysis"))

# Import specific function from threshold_phenomenon
from core.analysis.threshold_phenomenon import ignition_probability


class TestSurpriseDynamics:
    """Test surprise dynamics calculations and simulations."""

    def test_surprise_calculation(self):
        """Test total surprise calculation."""
        # Test basic surprise calculation
        pi_e = 1.0
        pi_i = 0.8
        epsilon_e = 0.5
        epsilon_i = 0.3

        S_t = pi_e * np.abs(epsilon_e) + pi_i * np.abs(epsilon_i)
        expected = 1.0 * 0.5 + 0.8 * 0.3

        assert S_t == expected

    def test_ignition_detection(self):
        """Test ignition event detection."""
        # Create test data
        S_t = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        theta_t = np.array([2.5, 2.5, 2.5, 2.5, 2.5])

        ignitions = S_t > theta_t
        expected = np.array([False, False, True, True, True])

        np.testing.assert_array_equal(ignitions, expected)

    def test_dynamic_threshold_simulation(self):
        """Test dynamic threshold simulation."""
        np.random.seed(42)
        steps = 10

        # Generate test data
        epsilon_e = np.random.normal(0, 1, steps)
        epsilon_i = np.random.normal(0, 1, steps)
        pi_e = 1.0
        pi_i = np.abs(np.random.normal(1, 0.5, steps))

        # Calculate dynamic threshold
        theta_t = 1.5 + np.cumsum(np.random.normal(0, 0.1, steps)) * 0.2

        # Verify threshold is dynamic (not constant)
        assert not np.allclose(theta_t, theta_t[0])

        # Calculate total surprise
        S_t = pi_e * np.abs(epsilon_e) + pi_i * np.abs(epsilon_i)

        # Verify surprise is always positive
        assert np.all(S_t >= 0)

        # Detect ignitions
        ignitions = S_t > theta_t
        assert len(ignitions) == steps
        assert all(isinstance(ig, (bool, np.bool_)) for ig in ignitions)

    def test_precision_effects(self):
        """Test effects of precision weights on surprise."""
        epsilon_e = 0.5
        epsilon_i = 0.5

        # Test different precision weights
        pi_e_low, pi_i_low = 0.5, 0.5
        pi_e_high, pi_i_high = 2.0, 2.0

        S_t_low = pi_e_low * np.abs(epsilon_e) + pi_i_low * np.abs(epsilon_i)
        S_t_high = pi_e_high * np.abs(epsilon_e) + pi_i_high * np.abs(epsilon_i)

        # Higher precision should lead to higher surprise
        assert S_t_high > S_t_low

    def test_somatic_bias_variation(self):
        """Test somatic bias variation in interoceptive precision."""
        np.random.seed(42)
        steps = 100

        # Generate interoceptive precision with variation
        pi_i = np.abs(np.random.normal(1, 0.5, steps))

        # Verify variation exists
        assert np.std(pi_i) > 0
        assert np.all(pi_i >= 0)  # Should be non-negative

        # Verify mean is close to expected
        assert abs(np.mean(pi_i) - 1.0) < 0.5  # Within reasonable range


class TestThresholdPhenomenon:
    """Test threshold phenomenon calculations and visualizations."""

    def test_ignition_probability_function(self):
        """Test ignition probability calculation."""
        # Test basic cases
        S_t = 5.0
        theta_t = 3.0
        alpha = 1.0

        prob = ignition_probability(S_t, theta_t, alpha)

        # Should be between 0 and 1
        assert 0.0 <= prob <= 1.0

        # When surprise > threshold, probability should be > 0.5
        assert prob > 0.5

        # Test edge case: surprise equals threshold
        prob_equal = ignition_probability(theta_t, theta_t, alpha)
        assert abs(prob_equal - 0.5) < 0.01  # Should be ~0.5

    def test_ignition_probability_edge_cases(self):
        """Test ignition probability with edge cases."""
        theta_t = 5.0
        alpha = 1.0

        # Very low surprise
        prob_low = ignition_probability(0.0, theta_t, alpha)
        assert prob_low < 0.1

        # Very high surprise
        prob_high = ignition_probability(10.0, theta_t, alpha)
        assert prob_high > 0.9

        # Different alpha values
        prob_sharp = ignition_probability(6.0, theta_t, alpha=2.0)
        prob_gentle = ignition_probability(6.0, theta_t, alpha=0.5)

        # Sharper transition should give higher probability for same difference
        assert prob_sharp > prob_gentle

    def test_threshold_effect(self):
        """Test effect of different threshold values."""
        S_t_range = np.linspace(0, 10, 100)
        alpha = 1.0
        theta_values = [3, 5, 7]

        probabilities = {}
        for theta in theta_values:
            probs = [ignition_probability(S, theta, alpha) for S in S_t_range]
            probabilities[theta] = probs

        # Higher threshold should shift curve right
        # At a fixed S_t, higher threshold -> lower probability
        test_S = 6.0
        prob_theta_3 = ignition_probability(test_S, 3, alpha)
        prob_theta_5 = ignition_probability(test_S, 5, alpha)
        prob_theta_7 = ignition_probability(test_S, 7, alpha)

        assert prob_theta_3 > prob_theta_5 > prob_theta_7

    def test_alpha_effect(self):
        """Test effect of sigmoid steepness (alpha)."""
        S_t = 6.0
        theta_t = 5.0
        alpha_values = [0.5, 1.0, 2.0]

        probabilities = {}
        for alpha in alpha_values:
            prob = ignition_probability(S_t, theta_t, alpha)
            probabilities[alpha] = prob

        # Higher alpha should give more extreme probability
        # (further from 0.5 when S_t != theta_t)
        assert probabilities[2.0] > probabilities[1.0] > probabilities[0.5]

    def test_somatic_marker_effect(self):
        """Test somatic marker effect on ignition probability."""
        S_t_extero = 2.5
        epsilon_i = 3.0
        theta_t = 5.0
        alpha = 1.0
        M_values = [0.5, 1.0, 2.0]

        probabilities = {}
        for M in M_values:
            S_t_total = S_t_extero + M * epsilon_i
            prob = ignition_probability(S_t_total, theta_t, alpha)
            probabilities[M] = prob

        # Higher somatic marker should increase total surprise and probability
        assert probabilities[2.0] > probabilities[1.0] > probabilities[0.5]

    def test_probability_range_validation(self):
        """Test that probabilities always stay in valid range."""
        # Test with extreme values
        test_cases = [
            (0.0, 10.0, 1.0),  # Low surprise, high threshold
            (10.0, 0.0, 1.0),  # High surprise, low threshold
            (5.0, 5.0, 10.0),  # Equal, very sharp transition
            (5.0, 5.0, 0.1),  # Equal, very gentle transition
        ]

        for S_t, theta_t, alpha in test_cases:
            prob = ignition_probability(S_t, theta_t, alpha)
            assert 0.0 <= prob <= 1.0, f"Failed for S_t={S_t}, theta_t={theta_t}, alpha={alpha}"

    def test_monotonicity(self):
        """Test monotonicity of ignition probability function."""
        theta_t = 5.0
        alpha = 1.0
        S_t_values = np.linspace(0, 10, 50)

        probabilities = [ignition_probability(S, theta_t, alpha) for S in S_t_values]

        # Function should be monotonically increasing
        for i in range(1, len(probabilities)):
            assert probabilities[i] >= probabilities[i - 1] - 1e-10  # Allow tiny numerical errors

    def test_symmetry_property(self):
        """Test symmetry property around threshold."""
        theta_t = 5.0
        alpha = 1.0

        # Test points equidistant from threshold
        delta = 2.0
        prob_above = ignition_probability(theta_t + delta, theta_t, alpha)
        prob_below = ignition_probability(theta_t - delta, theta_t, alpha)

        # Should satisfy: P(theta + delta) = 1 - P(theta - delta)
        assert abs(prob_above - (1 - prob_below)) < 0.01


class TestAnalysisIntegration:
    """Test integration between analysis modules."""

    def test_surprise_to_probability_conversion(self):
        """Test converting surprise dynamics to ignition probabilities."""
        # Create surprise dynamics data
        np.random.seed(42)
        steps = 20
        epsilon_e = np.random.normal(0, 1, steps)
        epsilon_i = np.random.normal(0, 1, steps)
        pi_e = 1.0
        pi_i = np.abs(np.random.normal(1, 0.5, steps))
        theta_t = np.full(steps, 5.0)

        # Calculate surprise
        S_t = pi_e * np.abs(epsilon_e) + pi_i * np.abs(epsilon_i)

        # Convert to probabilities
        alpha = 1.0
        B_t = np.array([ignition_probability(S, theta, alpha) for S, theta in zip(S_t, theta_t)])

        # Validate probabilities
        assert len(B_t) == steps
        assert np.all(B_t >= 0.0)
        assert np.all(B_t <= 1.0)

    def test_threshold_adaptation_scenario(self):
        """Test scenario with dynamic threshold adaptation."""
        steps = 50

        # Create dynamic threshold
        base_threshold = 5.0
        threshold_noise = np.random.normal(0, 0.2, steps)
        theta_t = base_threshold + np.cumsum(threshold_noise) * 0.1

        # Create surprise signal
        S_t = np.linspace(2, 8, steps)

        # Calculate ignition probabilities with dynamic threshold
        alpha = 1.0
        B_t = np.array([ignition_probability(S, theta, alpha) for S, theta in zip(S_t, theta_t)])

        # Verify adaptation effect
        assert len(B_t) == steps
        assert np.all(B_t >= 0.0) and np.all(B_t <= 1.0)

        # Should show variation due to dynamic threshold
        assert np.std(B_t) > 0

    def test_precision_modulation_effects(self):
        """Test effects of precision modulation on ignition probabilities."""
        base_surprise = 4.0
        theta_t = 5.0
        alpha = 1.0

        # Test different precision scenarios
        scenarios = [
            {"pi_e": 0.5, "pi_i": 0.5, "name": "low_precision"},
            {"pi_e": 1.0, "pi_i": 1.0, "name": "medium_precision"},
            {"pi_e": 2.0, "pi_i": 2.0, "name": "high_precision"},
        ]

        results = {}
        for scenario in scenarios:
            # Modulate base surprise by precision
            S_t = base_surprise * (scenario["pi_e"] + scenario["pi_i"]) / 2.0
            prob = ignition_probability(S_t, theta_t, alpha)
            results[scenario["name"]] = prob

        # Higher precision should lead to higher ignition probability
        assert results["high_precision"] > results["medium_precision"] > results["low_precision"]


if __name__ == "__main__":
    pytest.main([__file__])
