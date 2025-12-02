"""Unit tests for FreeEnergyCalculator."""

import pytest
import numpy as np
from scipy import linalg

from apgi_system.core.free_energy import FreeEnergyCalculator


class TestFreeEnergyCalculator:
    """Test FreeEnergyCalculator functionality."""

    def test_initialization(self):
        """Test calculator initializes correctly."""
        calc = FreeEnergyCalculator()
        assert calc.eps == 1e-10
        
        # With config
        config = {'numerical_tolerance': 1e-8}
        calc = FreeEnergyCalculator(config)
        assert calc.config == config

    def test_compute_variational_free_energy_basic(self):
        """Test basic variational free energy computation."""
        calc = FreeEnergyCalculator()
        
        # Simple 2D case
        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])
        precision = 2.0
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.array([0.0, 0.0])
        prior_cov = np.eye(2)
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )
        
        assert isinstance(fe, float)
        assert fe >= 0  # Free energy should be non-negative
        assert 'accuracy' in components
        assert 'complexity' in components
        assert 'prediction_error' in components
        
        # Components should be non-negative
        assert components['accuracy'] >= 0
        assert components['complexity'] >= 0
        assert components['prediction_error'] >= 0

    def test_accuracy_term_computation(self):
        """Test accuracy term computation."""
        calc = FreeEnergyCalculator()
        
        # Perfect prediction should give zero accuracy term
        observation = np.array([1.0, 2.0, 3.0])
        prediction = observation.copy()
        precision = 1.0
        posterior_mean = np.zeros(3)
        posterior_cov = np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )
        
        # Accuracy should be zero for perfect prediction
        assert abs(components['accuracy']) < 1e-10

    def test_complexity_term_computation(self):
        """Test complexity term (KL divergence) computation."""
        calc = FreeEnergyCalculator()
        
        # Identical posterior and prior should give zero complexity
        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])
        precision = 1.0
        mean = np.array([0.5, 1.0])
        cov = np.eye(2) * 0.5
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            mean, cov,  # Same posterior
            mean, cov   # and prior
        )
        
        # Complexity should be zero when posterior equals prior
        assert abs(components['complexity']) < 1e-10

    def test_precision_matrix_formats(self):
        """Test different precision matrix formats."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)
        
        # Scalar precision
        fe1, _ = calc.compute_variational_free_energy(
            observation, prediction, 2.0,
            posterior_mean, posterior_cov, prior_mean, prior_cov
        )
        
        # Vector precision (positive values)
        fe2, _ = calc.compute_variational_free_energy(
            observation, prediction, np.array([2.0, 2.0]),
            posterior_mean, posterior_cov, prior_mean, prior_cov
        )
        
        # Test that scalar and vector give same results
        assert abs(fe1 - fe2) < 1e-10
        
        # Test that all results are valid
        assert fe1 >= 0
        assert fe2 >= 0
        assert np.isfinite(fe1)
        assert np.isfinite(fe2)

    def test_compute_expected_free_energy_basic(self):
        """Test basic expected free energy computation."""
        calc = FreeEnergyCalculator()
        
        policy = np.array([1.0])
        predicted_states = [np.random.randn(8) for _ in range(3)]
        predicted_observations = np.random.rand(3, 8)
        preferences = np.ones(8) / 8  # Uniform preferences
        state_uncertainty = np.array([0.5, 0.4, 0.3])
        
        efe, components = calc.compute_expected_free_energy(
            policy, predicted_states, predicted_observations,
            preferences, state_uncertainty, horizon=3
        )
        
        assert isinstance(efe, float)
        assert 'epistemic_value' in components
        assert 'pragmatic_value' in components
        assert 'exploration_drive' in components
        assert 'exploitation_drive' in components
        
        # Exploration drive should be negative of epistemic value
        assert abs(components['exploration_drive'] + components['epistemic_value']) < 1e-10

    def test_epistemic_value_uncertainty_relationship(self):
        """Test epistemic value increases with uncertainty."""
        calc = FreeEnergyCalculator()
        
        policy = np.array([1.0])
        predicted_states = [np.ones(4)]
        predicted_observations = np.ones((1, 4)) * 0.25
        preferences = np.ones(4) / 4
        
        # Low uncertainty
        low_uncertainty = np.array([0.1])
        efe_low, comp_low = calc.compute_expected_free_energy(
            policy, predicted_states, predicted_observations,
            preferences, low_uncertainty, horizon=1
        )
        
        # High uncertainty
        high_uncertainty = np.array([1.0])
        efe_high, comp_high = calc.compute_expected_free_energy(
            policy, predicted_states, predicted_observations,
            preferences, high_uncertainty, horizon=1
        )
        
        # Higher uncertainty should give more negative epistemic value (more exploration)
        assert comp_high['epistemic_value'] < comp_low['epistemic_value']

    def test_kl_divergence_gaussian(self):
        """Test KL divergence computation between Gaussians."""
        calc = FreeEnergyCalculator()
        
        # Identical distributions should give zero KL
        mu = np.array([1.0, 2.0])
        sigma = np.eye(2) * 0.5
        
        kl = calc._kl_divergence_gaussian(mu, sigma, mu, sigma)
        assert abs(kl) < 1e-10
        
        # Different means should give positive KL
        mu_q = np.array([1.0, 2.0])
        mu_p = np.array([0.0, 0.0])
        sigma = np.eye(2)
        
        kl = calc._kl_divergence_gaussian(mu_q, sigma, mu_p, sigma)
        assert kl > 0

    def test_kl_divergence_properties(self):
        """Test KL divergence mathematical properties."""
        calc = FreeEnergyCalculator()
        
        mu_q = np.array([1.0, 2.0])
        sigma_q = np.eye(2) * 0.5
        mu_p = np.array([0.0, 1.0])
        sigma_p = np.eye(2) * 2.0
        
        kl = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)
        
        # KL divergence should be non-negative
        assert kl >= 0
        
        # Should be finite
        assert np.isfinite(kl)

    def test_compute_prediction_error(self):
        """Test prediction error computation."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0, 3.0])
        prediction = np.array([1.1, 1.9, 3.2])
        precision = np.array([1.0, 2.0, 1.5])
        
        errors = calc.compute_prediction_error(observation, prediction, precision)
        
        assert 'raw_error' in errors
        assert 'weighted_error' in errors
        assert 'mean_absolute_error' in errors
        assert 'max_error' in errors
        assert 'precision_weighted_elements' in errors
        
        # Raw error should be L2 norm
        expected_raw = np.linalg.norm(observation - prediction)
        assert abs(errors['raw_error'] - expected_raw) < 1e-10
        
        # All errors should be non-negative
        assert errors['raw_error'] >= 0
        assert errors['weighted_error'] >= 0
        assert errors['mean_absolute_error'] >= 0
        assert errors['max_error'] >= 0

    def test_compute_surprise(self):
        """Test surprise computation."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0])
        
        # High probability should give low surprise
        high_prob = np.array([0.9, 0.8])
        surprise_low = calc.compute_surprise(observation, high_prob)
        
        # Low probability should give high surprise
        low_prob = np.array([0.1, 0.2])
        surprise_high = calc.compute_surprise(observation, low_prob)
        
        assert surprise_high > surprise_low
        assert surprise_low >= 0
        assert surprise_high >= 0

    def test_numerical_edge_cases(self):
        """Test numerical edge cases."""
        calc = FreeEnergyCalculator()
        
        # Very small values
        observation = np.array([1e-10, 2e-10])
        prediction = np.array([1.1e-10, 1.9e-10])
        precision = 1.0
        posterior_mean = observation
        posterior_cov = np.eye(2) * 1e-12
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2) * 1e-6
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )
        
        assert np.isfinite(fe)
        assert fe >= 0

    def test_large_values(self):
        """Test with large values."""
        calc = FreeEnergyCalculator()
        
        # Large values
        observation = np.array([1e6, 2e6])
        prediction = np.array([1.1e6, 1.9e6])
        precision = 1e-6  # Small precision to avoid overflow
        posterior_mean = observation
        posterior_cov = np.eye(2) * 1e12
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2) * 1e12
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )
        
        assert np.isfinite(fe)

    def test_singular_covariance_handling(self):
        """Test handling of singular covariance matrices."""
        calc = FreeEnergyCalculator()
        
        # Singular covariance (zero determinant)
        mu_q = np.array([1.0, 2.0])
        sigma_q = np.zeros((2, 2))  # Singular
        mu_p = np.array([0.0, 0.0])
        sigma_p = np.eye(2)
        
        # Should handle gracefully (return large value)
        kl = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)
        assert np.isfinite(kl)
        assert kl >= 0

    def test_input_validation_errors(self):
        """Test input validation error handling."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])
        precision = 1.0
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)
        
        # Mismatched observation and prediction shapes
        with pytest.raises(ValueError):
            calc.compute_variational_free_energy(
                observation, np.array([1.1]),  # Wrong shape
                precision, posterior_mean, posterior_cov, prior_mean, prior_cov
            )
        
        # Negative precision
        with pytest.raises(ValueError):
            calc.compute_variational_free_energy(
                observation, prediction, -1.0,  # Negative precision
                posterior_mean, posterior_cov, prior_mean, prior_cov
            )
        
        # NaN observation
        with pytest.raises(ValueError):
            calc.compute_variational_free_energy(
                np.array([np.nan, 2.0]), prediction, precision,
                posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_zero_precision_handling(self):
        """Test handling of zero precision."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])
        posterior_mean = observation
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)
        
        # Zero precision should raise error
        with pytest.raises(ValueError):
            calc.compute_variational_free_energy(
                observation, prediction, 0.0,
                posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_prediction_error_without_precision(self):
        """Test prediction error computation without precision."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0, 3.0])
        prediction = np.array([1.1, 1.9, 3.2])
        
        errors = calc.compute_prediction_error(observation, prediction)
        
        # Should use uniform precision of 1.0
        assert 'raw_error' in errors
        assert 'weighted_error' in errors
        
        # Without precision weighting, weighted should equal raw
        assert abs(errors['raw_error'] - errors['weighted_error']) < 1e-10

    def test_surprise_boundary_conditions(self):
        """Test surprise computation boundary conditions."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0])
        
        # Very low probability (should be clamped)
        very_low_prob = np.array([1e-15])
        surprise = calc.compute_surprise(observation, very_low_prob)
        assert np.isfinite(surprise)
        
        # Probability of 1 (should give zero surprise)
        perfect_prob = np.array([1.0])
        surprise = calc.compute_surprise(observation, perfect_prob)
        assert surprise >= 0
        assert surprise < 1e-6  # Should be very small

    def test_free_energy_decomposition(self):
        """Test that free energy equals accuracy plus complexity."""
        calc = FreeEnergyCalculator()
        
        observation = np.array([1.0, 2.0, 3.0])
        prediction = np.array([1.2, 1.8, 3.1])
        precision = 1.5
        posterior_mean = np.array([1.1, 1.9, 3.0])
        posterior_cov = np.eye(3) * 0.2
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)
        
        fe, components = calc.compute_variational_free_energy(
            observation, prediction, precision,
            posterior_mean, posterior_cov,
            prior_mean, prior_cov
        )
        
        # Free energy should equal sum of components
        expected_fe = components['accuracy'] + components['complexity']
        assert abs(fe - expected_fe) < 1e-10