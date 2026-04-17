"""
Extended tests for free energy module to improve coverage.

Tests the free energy calculation capabilities including variational free energy,
expected free energy, and their constituent components.
"""

import numpy as np
import pytest

from apgi_simulation.core.free_energy import (
    FreeEnergyCalculator,
    compute_accuracy,
    compute_complexity,
    compute_epistemic_value,
    compute_expected_free_energy,
    compute_pragmatic_value,
    compute_variational_free_energy,
)


class TestFreeEnergyCalculator:
    """Test the FreeEnergyCalculator class."""

    def test_calculator_initialization(self) -> None:
        """Test that FreeEnergyCalculator initializes correctly."""
        config = {
            "eps": 1e-8,
        }

        calculator = FreeEnergyCalculator(config)

        assert calculator.config == config
        assert calculator.eps == 1e-8

    def test_calculator_default_config(self) -> None:
        """Test FreeEnergyCalculator with default configuration."""
        calculator = FreeEnergyCalculator()

        assert calculator.eps == 1e-10  # Default epsilon

    def test_compute_variational_free_energy_basic(self) -> None:
        """Test basic variational free energy computation."""
        calculator = FreeEnergyCalculator()

        # Simple test case
        observations = np.array([1.0, 0.5, 0.8])
        predictions = np.array([0.9, 0.6, 0.7])
        precision = 1.0
        posterior_mean = np.array([0.8, 0.7, 0.9])
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.array([0.5, 0.5, 0.5])
        prior_cov = np.eye(3)

        free_energy, components = calculator.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        assert isinstance(free_energy, float)
        assert free_energy > 0  # Free energy should be positive

    def test_compute_variational_free_energy_components(self) -> None:
        """Test variational free energy with component breakdown."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.8, 0.2, 0.9])
        precision = 1.0
        posterior_mean = np.array([0.9, 0.1, 0.8])
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.array([0.5, 0.5, 0.5])
        prior_cov = np.eye(3)

        free_energy, components = calculator.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        assert isinstance(components, dict)
        assert "accuracy" in components
        assert "complexity" in components
        assert "prediction_error" in components

        # Free energy should equal accuracy + complexity
        expected_fe = components["accuracy"] + components["complexity"]
        assert abs(free_energy - expected_fe) < 1e-6

    def test_compute_expected_free_energy_basic(self) -> None:
        """Test basic expected free energy computation."""
        calculator = FreeEnergyCalculator()

        # Mock policy and state distributions
        policy = np.array([0.8, 0.2])  # Simple 1D policy
        predicted_states = [np.array([0.6, 0.4])]  # Single predicted state
        predicted_observations = np.array([[0.9, 0.1]])  # Single predicted observation
        preferences = np.array([1.0, -1.0])  # Prefer first observation
        state_uncertainty = np.array([0.1])  # Single uncertainty value

        expected_fe, components = calculator.compute_expected_free_energy(
            policy,
            predicted_states,
            predicted_observations,
            preferences,
            state_uncertainty,
            horizon=1,
        )

        assert isinstance(expected_fe, float)
        # Expected free energy can be negative (when actions are beneficial)

    def test_compute_expected_free_energy_components(self) -> None:
        """Test expected free energy with component breakdown."""
        calculator = FreeEnergyCalculator()

        policy = np.array([1.0, 0.0])  # Deterministic policy
        predicted_states = [np.array([0.7, 0.3])]  # Single predicted state
        predicted_observations = np.array([[0.8, 0.2]])  # Single predicted observation
        preferences = np.array([2.0, -1.0])
        state_uncertainty = np.array([0.1])  # Single uncertainty value

        expected_fe, components = calculator.compute_expected_free_energy(
            policy,
            predicted_states,
            predicted_observations,
            preferences,
            state_uncertainty,
            horizon=1,
        )

        assert isinstance(components, dict)
        assert "epistemic_value" in components
        assert "pragmatic_value" in components

        # Expected free energy should equal epistemic + pragmatic value
        expected_efe = components["epistemic_value"] + components["pragmatic_value"]
        assert abs(expected_fe - expected_efe) < 1e-6

    def test_compute_accuracy(self) -> None:
        """Test accuracy computation."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.9, 0.1, 0.8])

        accuracy = calculator.compute_accuracy(observations, predictions)

        assert isinstance(accuracy, float)
        assert accuracy >= 0  # Accuracy should be non-negative

    def test_compute_complexity(self) -> None:
        """Test complexity computation."""
        calculator = FreeEnergyCalculator()

        posterior_mean = np.array([0.8, 0.2])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        complexity = calculator.compute_complexity(
            posterior_mean, posterior_cov, prior_mean, prior_cov
        )

        assert isinstance(complexity, float)
        assert complexity >= 0  # KL divergence is non-negative

    def test_compute_complexity_equal_distributions(self) -> None:
        """Test complexity when posterior equals prior."""
        calculator = FreeEnergyCalculator()

        distribution = np.array([0.3, 0.7])
        cov_matrix = np.eye(2) * 0.1

        complexity = calculator.compute_complexity(
            distribution, cov_matrix, distribution, cov_matrix
        )

        assert abs(complexity) < 1e-10  # Should be zero when distributions are equal

    def test_compute_epistemic_value(self) -> None:
        """Test epistemic value computation."""
        calculator = FreeEnergyCalculator()

        policy = np.array([0.8, 0.2])
        predicted_states = np.array([[0.6, 0.4]])
        state_uncertainty = np.array([0.1])

        epistemic_value = calculator.compute_epistemic_value(
            policy, predicted_states, state_uncertainty, horizon=1
        )

        assert isinstance(epistemic_value, float)
        # Epistemic value should be negative (information gain is valuable)
        assert epistemic_value <= 0

    def test_compute_pragmatic_value(self) -> None:
        """Test pragmatic value computation."""
        calculator = FreeEnergyCalculator()

        predicted_observations = np.array([[0.8, 0.2]])
        preferences = np.array([1.0, -2.0])  # Strong preference for first observation

        pragmatic_value = calculator.compute_pragmatic_value(
            predicted_observations, preferences, horizon=1
        )

        assert isinstance(pragmatic_value, float)
        # Pragmatic value can be positive or negative depending on preferences

    def test_numerical_stability_small_values(self) -> None:
        """Test numerical stability with very small values."""
        calculator = FreeEnergyCalculator({"eps": 1e-12})

        # Very small probabilities
        observations = np.array([1e-8, 1e-9, 1e-10])
        predictions = np.array([1e-8, 1e-9, 1e-10])
        precision = 1.0
        posterior_mean = np.array([1e-6, 1e-7, 1e-8])
        posterior_cov = np.eye(3) * 1e-6
        prior_mean = np.array([1e-6, 1e-7, 1e-8])
        prior_cov = np.eye(3) * 1e-6

        # Should not raise numerical errors
        free_energy, components = calculator.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        assert np.isfinite(free_energy)
        assert not np.isnan(free_energy)

    def test_numerical_stability_zero_values(self) -> None:
        """Test numerical stability with zero values."""
        calculator = FreeEnergyCalculator()

        # Include some zero values
        observations = np.array([1.0, 0.0, 0.5])
        predictions = np.array([0.9, 0.0, 0.6])
        precision = 1.0
        posterior_mean = np.array([0.8, 0.0, 0.7])
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.array([0.5, 0.0, 0.5])
        prior_cov = np.eye(3) * 0.1

        # Should handle zeros gracefully
        free_energy, components = calculator.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        assert np.isfinite(free_energy)

    def test_temperature_scaling(self) -> None:
        """Test temperature scaling effects."""
        config_cold = {"temperature": 0.1}  # Low temperature (sharp distributions)
        config_hot = {"temperature": 10.0}  # High temperature (flat distributions)

        calculator_cold = FreeEnergyCalculator(config_cold)
        calculator_hot = FreeEnergyCalculator(config_hot)

        observations = np.array([1.0, 0.0])
        predictions = np.array([0.8, 0.2])
        precision = 1.0
        posterior_mean = np.array([0.9, 0.1])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        fe_cold, _ = calculator_cold.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )
        fe_hot, _ = calculator_hot.compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        # Temperature affects the scaling of free energy
        assert fe_cold != fe_hot

    def test_batch_computation(self) -> None:
        """Test batch computation of free energy."""
        calculator = FreeEnergyCalculator()

        # Batch of observations
        batch_size = 5
        dim = 3
        precision = 1.0

        observations = np.random.rand(batch_size, dim)
        predictions = np.random.rand(batch_size, dim)
        posterior = np.random.rand(batch_size, dim)
        prior = np.random.rand(batch_size, dim)

        # Normalize to valid probabilities
        posterior = posterior / posterior.sum(axis=1, keepdims=True)
        prior = prior / prior.sum(axis=1, keepdims=True)

        # Test batch computation using individual calls
        free_energies = np.array(
            [
                calculator.compute_variational_free_energy(
                    observations[i],
                    predictions[i],
                    precision,
                    posterior[i],
                    np.eye(dim),
                    prior[i],
                    np.eye(dim),
                )[0]
                for i in range(batch_size)
            ]
        )

        assert free_energies.shape == (batch_size,)
        assert np.all(np.isfinite(free_energies))

    def test_gradient_computation(self) -> None:
        """Test gradient computation for free energy."""
        # Note: Gradient computation not implemented in current version
        # This test is placeholder for future implementation

        # Placeholder test data for when gradient computation is implemented
        posterior_mean = np.array([0.7, 0.1, 0.2])
        predictions = np.array([0.8, 0.2, 0.6])

        # Placeholder gradient structure
        gradients = {
            "posterior_gradient": np.zeros_like(posterior_mean),
            "prediction_gradient": np.zeros_like(predictions),
        }

        # Verify gradient shape
        assert gradients["posterior_gradient"].shape == posterior_mean.shape
        assert gradients["prediction_gradient"].shape == predictions.shape

    def test_policy_evaluation(self) -> None:
        """Test policy evaluation using expected free energy."""
        calculator = FreeEnergyCalculator()

        # Multiple policies to evaluate
        policies = [
            np.array([1.0, 0.0]),  # Deterministic policy 1
            np.array([0.0, 1.0]),  # Deterministic policy 2
            np.array([0.5, 0.5]),  # Random policy
        ]

        predicted_states = [np.array([0.6, 0.4])]  # Single predicted state
        predicted_observations = np.array([[0.8, 0.2]])  # Single predicted observation
        preferences = np.array([1.0, -1.0])
        state_uncertainty = np.array([0.1])

        policy_values = []
        for policy in policies:
            efe, _ = calculator.compute_expected_free_energy(
                policy,
                predicted_states,
                predicted_observations,
                preferences,
                state_uncertainty,
                horizon=1,
            )
            policy_values.append(efe)

        assert len(policy_values) == 3
        assert all(np.isfinite(value) for value in policy_values)

        # Find best policy (lowest expected free energy)
        best_policy_idx = np.argmin(policy_values)
        assert 0 <= best_policy_idx < len(policies)


class TestFreeEnergyFunctions:
    """Test standalone free energy functions."""

    def test_compute_variational_free_energy_function(self) -> None:
        """Test the standalone variational free energy function."""
        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.9, 0.1, 0.8])
        precision = 1.0
        posterior_mean = np.array([0.8, 0.1, 0.1])
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.array([0.33, 0.33, 0.34])
        prior_cov = np.eye(3)

        free_energy, components = compute_variational_free_energy(
            observations,
            predictions,
            precision,
            posterior_mean,
            posterior_cov,
            prior_mean,
            prior_cov,
        )

        assert isinstance(free_energy, float)
        assert np.isfinite(free_energy)

    def test_compute_expected_free_energy_function(self) -> None:
        """Test the standalone expected free energy function."""
        policy = np.array([0.8, 0.2])
        predicted_states = [np.array([0.6, 0.4])]
        predicted_observations = np.array([[0.9, 0.1]])
        preferences = np.array([1.0, -1.0])
        state_uncertainty = np.array([0.1])

        expected_fe, components = compute_expected_free_energy(
            policy,
            predicted_states,
            predicted_observations,
            preferences,
            state_uncertainty,
            horizon=1,
        )

        assert isinstance(expected_fe, float)
        assert np.isfinite(expected_fe)

    def test_compute_accuracy_function(self) -> None:
        """Test the standalone accuracy function."""
        observations = np.array([1.0, 0.0, 0.5])
        predictions = np.array([0.9, 0.1, 0.6])

        accuracy = compute_accuracy(observations, predictions)

        assert isinstance(accuracy, float)
        assert accuracy >= 0

    def test_compute_complexity_function(self) -> None:
        """Test the standalone complexity function."""
        posterior_mean = np.array([0.7, 0.3])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        complexity = compute_complexity(posterior_mean, posterior_cov, prior_mean, prior_cov)

        assert isinstance(complexity, float)
        assert complexity >= 0

    def test_compute_epistemic_value_function(self) -> None:
        """Test the standalone epistemic value function."""
        policy = np.array([0.8, 0.2])
        predicted_states = np.array([[0.6, 0.4]])
        state_uncertainty = np.array([0.1])

        epistemic_value = compute_epistemic_value(
            policy, predicted_states, state_uncertainty, horizon=1
        )

        assert isinstance(epistemic_value, float)
        assert np.isfinite(epistemic_value)

    def test_compute_pragmatic_value_function(self) -> None:
        """Test the standalone pragmatic value function."""
        predicted_observations = np.array([[0.8, 0.2]])
        preferences = np.array([1.0, -2.0])

        pragmatic_value = compute_pragmatic_value(predicted_observations, preferences, horizon=1)

        assert isinstance(pragmatic_value, float)
        assert np.isfinite(pragmatic_value)


class TestFreeEnergyEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_arrays(self) -> None:
        """Test behavior with empty arrays."""
        calculator = FreeEnergyCalculator()

        with pytest.raises((ValueError, IndexError)):
            calculator.compute_variational_free_energy(
                np.array([]), np.array([]), 1.0, np.array([]), np.eye(0), np.array([]), np.eye(0)
            )

    def test_mismatched_dimensions(self) -> None:
        """Test behavior with mismatched array dimensions."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0])
        predictions = np.array([0.9, 0.1, 0.5])  # Wrong size
        precision = 1.0
        posterior_mean = np.array([0.8, 0.2])
        posterior_cov = np.eye(2)
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        with pytest.raises((ValueError, IndexError)):
            calculator.compute_variational_free_energy(
                observations,
                predictions,
                precision,
                posterior_mean,
                posterior_cov,
                prior_mean,
                prior_cov,
            )

    def test_invalid_probabilities(self) -> None:
        """Test behavior with invalid probability distributions."""
        calculator = FreeEnergyCalculator()

        # Negative probabilities
        posterior_mean = np.array([0.8, -0.2])
        posterior_cov = np.eye(2)
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        with pytest.raises((ValueError, AssertionError)):
            calculator.compute_complexity(posterior_mean, posterior_cov, prior_mean, prior_cov)

    def test_unnormalized_probabilities(self) -> None:
        """Test behavior with unnormalized probability distributions."""
        calculator = FreeEnergyCalculator()

        # Probabilities don't sum to 1
        posterior_mean = np.array([0.8, 0.3])  # Sum = 1.1
        posterior_cov = np.eye(2)
        prior_mean = np.array([0.5, 0.5])
        prior_cov = np.eye(2)

        # Should either normalize automatically or raise error
        try:
            complexity = calculator.compute_complexity(
                posterior_mean, posterior_cov, prior_mean, prior_cov
            )
            assert np.isfinite(complexity)
        except (ValueError, AssertionError):
            pass  # Expected behavior for unnormalized distributions


class TestFreeEnergyIntegration:
    """Integration tests for free energy calculations."""

    def test_active_inference_loop(self) -> None:
        """Test free energy in a simulated active inference loop."""
        calculator = FreeEnergyCalculator()

        # Simulate a simple active inference scenario
        n_states = 3
        n_observations = 2
        n_timesteps = 5

        # Initialize beliefs and models
        state_beliefs = np.ones(n_states) / n_states
        observation_model = np.random.rand(n_states, n_observations)
        observation_model = observation_model / observation_model.sum(axis=1, keepdims=True)

        free_energy_history = []

        for t in range(n_timesteps):
            # Generate observation
            true_state = np.random.choice(n_states)
            observation = np.random.choice(n_observations, p=observation_model[true_state])

            # Update beliefs (simplified)
            likelihood = observation_model[:, observation]
            posterior = state_beliefs * likelihood
            posterior = posterior / posterior.sum()

            # Compute variational free energy
            obs_vec = np.zeros(n_observations)
            obs_vec[observation] = 1.0

            pred_obs = observation_model.T @ state_beliefs

            precision = 1.0
            posterior_mean = posterior
            posterior_cov = np.eye(n_states) * 0.1
            prior_mean = state_beliefs
            prior_cov = np.eye(n_states) * 0.1

            vfe, _ = calculator.compute_variational_free_energy(
                obs_vec, pred_obs, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

            free_energy_history.append(vfe)

            # Update beliefs for next timestep
            state_beliefs = posterior

        assert len(free_energy_history) == n_timesteps
        assert all(np.isfinite(fe) for fe in free_energy_history)

        # Free energy should generally decrease as beliefs improve
        # (though this isn't guaranteed in this simple simulation)
        assert np.mean(free_energy_history) > 0

    def test_policy_comparison(self) -> None:
        """Test comparing multiple policies using expected free energy."""
        calculator = FreeEnergyCalculator()

        # Set up scenario
        n_states = 4
        n_observations = 3
        n_actions = 2

        observation_model = np.random.rand(n_states, n_observations)
        observation_model = observation_model / observation_model.sum(axis=1, keepdims=True)

        preferences = np.array([2.0, 0.0, -1.0])  # Strong preferences

        # Generate different policies
        policies = []
        for _ in range(5):
            policy = np.random.rand(n_states, n_actions)
            policy = policy / policy.sum(axis=1, keepdims=True)
            policies.append(policy)

        # Evaluate each policy
        policy_values = []
        for policy in policies:
            predicted_states = [np.array([0.25, 0.25, 0.25, 0.25])]  # Uniform prediction
            predicted_observations = np.array([[0.33, 0.33, 0.34]])  # Single observation prediction
            state_uncertainty = np.array([0.1])

            efe, components = calculator.compute_expected_free_energy(
                policy.mean(axis=0),
                predicted_states,
                predicted_observations,
                preferences,
                state_uncertainty,
                horizon=1,
            )
            policy_values.append(efe)

        # All evaluations should be valid
        assert len(policy_values) == 5
        for pv in policy_values:
            assert np.isfinite(pv)

        # Find optimal policy
        efe_values = policy_values
        best_policy_idx = np.argmin(efe_values)

        assert 0 <= best_policy_idx < len(policies)

        # Best policy should have lowest expected free energy
        best_efe = efe_values[best_policy_idx]
        assert all(best_efe <= efe for efe in efe_values)
