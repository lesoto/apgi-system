"""Unit tests for FreeEnergyCalculator."""

import pytest
import numpy as np
from apgi_system.core.free_energy import (
    FreeEnergyCalculator,
    compute_variational_free_energy,
    compute_expected_free_energy,
    compute_accuracy,
    compute_complexity,
    compute_epistemic_value,
    compute_pragmatic_value,
)


class TestFreeEnergyCalculator:
    """Test FreeEnergyCalculator functionality."""

    @pytest.fixture
    def calc(self):
        """Create calculator instance."""
        return FreeEnergyCalculator()

    def test_initialization(self, calc):
        """Test calculator initializes correctly."""
        assert calc is not None
        assert calc.eps == 1e-10
        assert calc.precision_min == 1e-6
        assert calc.precision_max == 1e6

    def test_compute_variational_free_energy_basic(self, calc):
        """Test basic variational free energy computation."""
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])
        precision = 2.0
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        fe, components = calc.compute_variational_free_energy(
            obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
        )

        assert isinstance(fe, float)
        assert fe >= 0
        assert "accuracy" in components
        assert "complexity" in components
        assert "prediction_error" in components

    def test_compute_expected_free_energy_basic(self, calc):
        """Test basic expected free energy computation."""
        policy = np.array([1.0])
        pred_states = [np.random.randn(10) for _ in range(3)]
        pred_obs = np.random.rand(3, 10)
        preferences = np.ones(10) / 10
        uncertainty = np.array([0.5, 0.4, 0.3])

        efe, components = calc.compute_expected_free_energy(
            policy, pred_states, pred_obs, preferences, uncertainty
        )

        assert isinstance(efe, float)
        assert "epistemic_value" in components
        assert "pragmatic_value" in components

    def test_compute_prediction_error(self, calc):
        """Test prediction error computation."""
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])
        precision = np.array([1.0, 2.0, 1.5])

        errors = calc.compute_prediction_error(obs, pred, precision)

        assert "raw_error" in errors
        assert "weighted_error" in errors
        assert "mean_absolute_error" in errors
        assert "max_error" in errors

    def test_compute_surprise(self, calc):
        """Test surprise computation."""
        obs = np.array([1.0, 2.0])
        prob_density = np.array([0.8, 0.7])

        surprise = calc.compute_surprise(obs, prob_density)

        assert isinstance(surprise, float)
        assert surprise >= 0

    def test_compute_accuracy(self, calc):
        """Test accuracy computation."""
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])
        precision = 2.0

        accuracy = calc.compute_accuracy(obs, pred, precision)

        assert isinstance(accuracy, float)
        assert accuracy >= 0

    def test_compute_complexity(self, calc):
        """Test complexity computation."""
        post_mean = np.array([1.0, 2.0])
        post_cov = 0.1 * np.eye(2)
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)

        complexity = calc.compute_complexity(post_mean, post_cov, prior_mean, prior_cov)

        assert isinstance(complexity, float)
        assert complexity >= 0

    def test_compute_epistemic_value(self, calc):
        """Test epistemic value computation."""
        policy = np.array([1.0])
        pred_states = np.random.randn(3, 10)
        uncertainty = np.array([0.5, 0.4, 0.3])

        epistemic = calc.compute_epistemic_value(policy, pred_states, uncertainty)

        assert isinstance(epistemic, float)

    def test_compute_pragmatic_value(self, calc):
        """Test pragmatic value computation."""
        pred_obs = np.random.rand(3, 10)
        preferences = np.ones(10) / 10

        pragmatic = calc.compute_pragmatic_value(pred_obs, preferences)

        assert isinstance(pragmatic, float)

    def test_kl_divergence_gaussian(self, calc):
        """Test KL divergence computation."""
        mu_q = np.array([1.0, 2.0])
        sigma_q = np.eye(2) * 0.5
        mu_p = np.zeros(2)
        sigma_p = np.eye(2)

        kl = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)

        assert isinstance(kl, float)
        assert kl >= 0


class TestFreeEnergyWrappers:
    """Test standalone wrapper functions."""

    def test_compute_variational_free_energy_wrapper(self):
        """Test wrapper function."""
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])
        precision = 2.0
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        fe, components = compute_variational_free_energy(
            obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
        )

        assert isinstance(fe, float)
        assert fe >= 0

    def test_compute_expected_free_energy_wrapper(self):
        """Test expected free energy wrapper."""
        policy = np.array([1.0])
        pred_states = [np.random.randn(10) for _ in range(3)]
        pred_obs = np.random.rand(3, 10)
        preferences = np.ones(10) / 10
        uncertainty = np.array([0.5, 0.4, 0.3])

        efe, components = compute_expected_free_energy(
            policy, pred_states, pred_obs, preferences, uncertainty
        )

        assert isinstance(efe, float)

    def test_compute_accuracy_wrapper(self):
        """Test accuracy wrapper."""
        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])

        accuracy = compute_accuracy(obs, pred)

        assert isinstance(accuracy, float)
        assert accuracy >= 0

    def test_compute_complexity_wrapper(self):
        """Test complexity wrapper."""
        post_mean = np.array([1.0, 2.0])
        post_cov = 0.1 * np.eye(2)
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)

        complexity = compute_complexity(post_mean, post_cov, prior_mean, prior_cov)

        assert isinstance(complexity, float)
        assert complexity >= 0

    def test_compute_epistemic_value_wrapper(self) -> None:
        """Test epistemic value wrapper."""
        policy = np.array([1.0])
        pred_states = np.random.randn(3, 10)
        uncertainty = np.array([0.5, 0.4, 0.3])

        epistemic = compute_epistemic_value(policy, pred_states, uncertainty)

        assert isinstance(epistemic, float)

    def test_compute_pragmatic_value_wrapper(self) -> None:
        """Test pragmatic value wrapper."""
        pred_obs = np.random.rand(3, 10)
        preferences = np.ones(10) / 10

        pragmatic = compute_pragmatic_value(pred_obs, preferences)

        assert isinstance(pragmatic, float)
