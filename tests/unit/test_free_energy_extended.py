"""
Extended tests for free energy module to improve coverage.

Tests the free energy calculation capabilities including variational free energy,
expected free energy, and their constituent components.
"""

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
    """Test the FreeEnergyCalculator class."""

    def test_calculator_initialization(self):
        """Test that FreeEnergyCalculator initializes correctly."""
        config = {
            "eps": 1e-8,
            "temperature": 1.0,
            "complexity_weight": 1.0,
            "epistemic_weight": 1.0,
        }

        calculator = FreeEnergyCalculator(config)

        assert calculator.config == config
        assert calculator.eps == 1e-8
        assert calculator.temperature == 1.0
        assert calculator.complexity_weight == 1.0
        assert calculator.epistemic_weight == 1.0

    def test_calculator_default_config(self):
        """Test FreeEnergyCalculator with default configuration."""
        calculator = FreeEnergyCalculator()

        assert calculator.eps == 1e-10  # Default epsilon
        assert calculator.temperature == 1.0
        assert calculator.complexity_weight == 1.0
        assert calculator.epistemic_weight == 1.0

    def test_compute_variational_free_energy_basic(self):
        """Test basic variational free energy computation."""
        calculator = FreeEnergyCalculator()

        # Simple test case
        observations = np.array([1.0, 0.5, 0.8])
        predictions = np.array([0.9, 0.6, 0.7])
        posterior = np.array([0.8, 0.7, 0.9])
        prior = np.array([0.5, 0.5, 0.5])

        free_energy = calculator.compute_variational_free_energy(
            observations, predictions, posterior, prior
        )

        assert isinstance(free_energy, float)
        assert free_energy > 0  # Free energy should be positive

    def test_compute_variational_free_energy_components(self):
        """Test variational free energy with component breakdown."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.8, 0.2, 0.9])
        posterior = np.array([0.9, 0.1, 0.8])
        prior = np.array([0.5, 0.5, 0.5])

        result = calculator.compute_variational_free_energy(
            observations, predictions, posterior, prior, return_components=True
        )

        assert isinstance(result, dict)
        assert "free_energy" in result
        assert "accuracy" in result
        assert "complexity" in result
        assert "prediction_error" in result

        # Free energy should equal accuracy + complexity
        expected_fe = result["accuracy"] + result["complexity"]
        assert abs(result["free_energy"] - expected_fe) < 1e-6

    def test_compute_expected_free_energy_basic(self):
        """Test basic expected free energy computation."""
        calculator = FreeEnergyCalculator()

        # Mock policy and state distributions
        policy = np.array([[0.8, 0.2], [0.3, 0.7]])  # 2 states, 2 actions
        state_beliefs = np.array([0.6, 0.4])
        observation_model = np.array([[0.9, 0.1], [0.2, 0.8]])
        preferences = np.array([1.0, -1.0])  # Prefer first observation

        expected_fe = calculator.compute_expected_free_energy(
            policy, state_beliefs, observation_model, preferences
        )

        assert isinstance(expected_fe, float)
        # Expected free energy can be negative (when actions are beneficial)

    def test_compute_expected_free_energy_components(self):
        """Test expected free energy with component breakdown."""
        calculator = FreeEnergyCalculator()

        policy = np.array([[1.0, 0.0], [0.0, 1.0]])  # Deterministic policy
        state_beliefs = np.array([0.7, 0.3])
        observation_model = np.array([[0.8, 0.2], [0.3, 0.7]])
        preferences = np.array([2.0, -1.0])

        result = calculator.compute_expected_free_energy(
            policy, state_beliefs, observation_model, preferences, return_components=True
        )

        assert isinstance(result, dict)
        assert "expected_free_energy" in result
        assert "epistemic_value" in result
        assert "pragmatic_value" in result

        # Expected free energy should equal epistemic + pragmatic value
        expected_efe = result["epistemic_value"] + result["pragmatic_value"]
        assert abs(result["expected_free_energy"] - expected_efe) < 1e-6

    def test_compute_accuracy(self):
        """Test accuracy computation."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.9, 0.1, 0.8])

        accuracy = calculator.compute_accuracy(observations, predictions)

        assert isinstance(accuracy, float)
        assert accuracy >= 0  # Accuracy should be non-negative

    def test_compute_complexity(self):
        """Test complexity computation."""
        calculator = FreeEnergyCalculator()

        posterior = np.array([0.8, 0.2])
        prior = np.array([0.5, 0.5])

        complexity = calculator.compute_complexity(posterior, prior)

        assert isinstance(complexity, float)
        assert complexity >= 0  # KL divergence is non-negative

    def test_compute_complexity_equal_distributions(self):
        """Test complexity when posterior equals prior."""
        calculator = FreeEnergyCalculator()

        distribution = np.array([0.3, 0.7])

        complexity = calculator.compute_complexity(distribution, distribution)

        assert abs(complexity) < 1e-10  # Should be zero when distributions are equal

    def test_compute_epistemic_value(self):
        """Test epistemic value computation."""
        calculator = FreeEnergyCalculator()

        policy = np.array([[0.8, 0.2], [0.4, 0.6]])
        state_beliefs = np.array([0.6, 0.4])
        observation_model = np.array([[0.9, 0.1], [0.2, 0.8]])

        epistemic_value = calculator.compute_epistemic_value(
            policy, state_beliefs, observation_model
        )

        assert isinstance(epistemic_value, float)
        # Epistemic value should be negative (information gain is valuable)
        assert epistemic_value <= 0

    def test_compute_pragmatic_value(self):
        """Test pragmatic value computation."""
        calculator = FreeEnergyCalculator()

        policy = np.array([[1.0, 0.0], [0.0, 1.0]])
        state_beliefs = np.array([0.7, 0.3])
        observation_model = np.array([[0.8, 0.2], [0.3, 0.7]])
        preferences = np.array([1.0, -2.0])  # Strong preference for first observation

        pragmatic_value = calculator.compute_pragmatic_value(
            policy, state_beliefs, observation_model, preferences
        )

        assert isinstance(pragmatic_value, float)
        # Pragmatic value can be positive or negative depending on preferences

    def test_numerical_stability_small_values(self):
        """Test numerical stability with very small values."""
        calculator = FreeEnergyCalculator({"eps": 1e-12})

        # Very small probabilities
        observations = np.array([1e-8, 1e-9, 1e-10])
        predictions = np.array([1e-8, 1e-9, 1e-10])
        posterior = np.array([1e-6, 1e-7, 1e-8])
        prior = np.array([1e-6, 1e-7, 1e-8])

        # Should not raise numerical errors
        free_energy = calculator.compute_variational_free_energy(
            observations, predictions, posterior, prior
        )

        assert np.isfinite(free_energy)
        assert not np.isnan(free_energy)

    def test_numerical_stability_zero_values(self):
        """Test numerical stability with zero values."""
        calculator = FreeEnergyCalculator()

        # Include some zero values
        observations = np.array([1.0, 0.0, 0.5])
        predictions = np.array([0.9, 0.0, 0.6])
        posterior = np.array([0.8, 0.0, 0.7])
        prior = np.array([0.5, 0.0, 0.5])

        # Should handle zeros gracefully
        free_energy = calculator.compute_variational_free_energy(
            observations, predictions, posterior, prior
        )

        assert np.isfinite(free_energy)

    def test_temperature_scaling(self):
        """Test temperature scaling effects."""
        config_cold = {"temperature": 0.1}  # Low temperature (sharp distributions)
        config_hot = {"temperature": 10.0}  # High temperature (flat distributions)

        calculator_cold = FreeEnergyCalculator(config_cold)
        calculator_hot = FreeEnergyCalculator(config_hot)

        observations = np.array([1.0, 0.0])
        predictions = np.array([0.8, 0.2])
        posterior = np.array([0.9, 0.1])
        prior = np.array([0.5, 0.5])

        fe_cold = calculator_cold.compute_variational_free_energy(
            observations, predictions, posterior, prior
        )
        fe_hot = calculator_hot.compute_variational_free_energy(
            observations, predictions, posterior, prior
        )

        # Temperature affects the scaling of free energy
        assert fe_cold != fe_hot

    def test_batch_computation(self):
        """Test batch computation of free energy."""
        calculator = FreeEnergyCalculator()

        # Batch of observations
        batch_size = 5
        dim = 3

        observations = np.random.rand(batch_size, dim)
        predictions = np.random.rand(batch_size, dim)
        posterior = np.random.rand(batch_size, dim)
        prior = np.random.rand(batch_size, dim)

        # Normalize to valid probabilities
        posterior = posterior / posterior.sum(axis=1, keepdims=True)
        prior = prior / prior.sum(axis=1, keepdims=True)

        free_energies = calculator.compute_variational_free_energy_batch(
            observations, predictions, posterior, prior
        )

        assert free_energies.shape == (batch_size,)
        assert np.all(np.isfinite(free_energies))

    def test_gradient_computation(self):
        """Test gradient computation for free energy."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0, 0.5])
        predictions = np.array([0.8, 0.2, 0.6])
        posterior = np.array([0.7, 0.1, 0.2])
        prior = np.array([0.33, 0.33, 0.34])

        gradients = calculator.compute_free_energy_gradients(
            observations, predictions, posterior, prior
        )

        assert "posterior_gradient" in gradients
        assert "prediction_gradient" in gradients
        assert gradients["posterior_gradient"].shape == posterior.shape
        assert gradients["prediction_gradient"].shape == predictions.shape

    def test_policy_evaluation(self):
        """Test policy evaluation using expected free energy."""
        calculator = FreeEnergyCalculator()

        # Multiple policies to evaluate
        policies = [
            np.array([[1.0, 0.0], [0.0, 1.0]]),  # Deterministic policy 1
            np.array([[0.0, 1.0], [1.0, 0.0]]),  # Deterministic policy 2
            np.array([[0.5, 0.5], [0.5, 0.5]]),  # Random policy
        ]

        state_beliefs = np.array([0.6, 0.4])
        observation_model = np.array([[0.8, 0.2], [0.3, 0.7]])
        preferences = np.array([1.0, -1.0])

        policy_values = []
        for policy in policies:
            efe = calculator.compute_expected_free_energy(
                policy, state_beliefs, observation_model, preferences
            )
            policy_values.append(efe)

        assert len(policy_values) == 3
        assert all(np.isfinite(value) for value in policy_values)

        # Find best policy (lowest expected free energy)
        best_policy_idx = np.argmin(policy_values)
        assert 0 <= best_policy_idx < len(policies)


class TestFreeEnergyFunctions:
    """Test standalone free energy functions."""

    def test_compute_variational_free_energy_function(self):
        """Test the standalone variational free energy function."""
        observations = np.array([1.0, 0.0, 1.0])
        predictions = np.array([0.9, 0.1, 0.8])
        posterior = np.array([0.8, 0.1, 0.1])
        prior = np.array([0.33, 0.33, 0.34])

        free_energy = compute_variational_free_energy(observations, predictions, posterior, prior)

        assert isinstance(free_energy, float)
        assert np.isfinite(free_energy)

    def test_compute_expected_free_energy_function(self):
        """Test the standalone expected free energy function."""
        policy = np.array([[0.8, 0.2], [0.3, 0.7]])
        state_beliefs = np.array([0.6, 0.4])
        observation_model = np.array([[0.9, 0.1], [0.2, 0.8]])
        preferences = np.array([1.0, -1.0])

        expected_fe = compute_expected_free_energy(
            policy, state_beliefs, observation_model, preferences
        )

        assert isinstance(expected_fe, float)
        assert np.isfinite(expected_fe)

    def test_compute_accuracy_function(self):
        """Test the standalone accuracy function."""
        observations = np.array([1.0, 0.0, 0.5])
        predictions = np.array([0.9, 0.1, 0.6])

        accuracy = compute_accuracy(observations, predictions)

        assert isinstance(accuracy, float)
        assert accuracy >= 0

    def test_compute_complexity_function(self):
        """Test the standalone complexity function."""
        posterior = np.array([0.7, 0.3])
        prior = np.array([0.5, 0.5])

        complexity = compute_complexity(posterior, prior)

        assert isinstance(complexity, float)
        assert complexity >= 0

    def test_compute_epistemic_value_function(self):
        """Test the standalone epistemic value function."""
        policy = np.array([[0.8, 0.2], [0.4, 0.6]])
        state_beliefs = np.array([0.6, 0.4])
        observation_model = np.array([[0.9, 0.1], [0.2, 0.8]])

        epistemic_value = compute_epistemic_value(policy, state_beliefs, observation_model)

        assert isinstance(epistemic_value, float)
        assert np.isfinite(epistemic_value)

    def test_compute_pragmatic_value_function(self):
        """Test the standalone pragmatic value function."""
        policy = np.array([[1.0, 0.0], [0.0, 1.0]])
        state_beliefs = np.array([0.7, 0.3])
        observation_model = np.array([[0.8, 0.2], [0.3, 0.7]])
        preferences = np.array([1.0, -2.0])

        pragmatic_value = compute_pragmatic_value(
            policy, state_beliefs, observation_model, preferences
        )

        assert isinstance(pragmatic_value, float)
        assert np.isfinite(pragmatic_value)


class TestFreeEnergyEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_arrays(self):
        """Test behavior with empty arrays."""
        calculator = FreeEnergyCalculator()

        with pytest.raises((ValueError, IndexError)):
            calculator.compute_variational_free_energy(
                np.array([]), np.array([]), np.array([]), np.array([])
            )

    def test_mismatched_dimensions(self):
        """Test behavior with mismatched array dimensions."""
        calculator = FreeEnergyCalculator()

        observations = np.array([1.0, 0.0])
        predictions = np.array([0.9, 0.1, 0.5])  # Wrong size
        posterior = np.array([0.8, 0.2])
        prior = np.array([0.5, 0.5])

        with pytest.raises((ValueError, IndexError)):
            calculator.compute_variational_free_energy(observations, predictions, posterior, prior)

    def test_invalid_probabilities(self):
        """Test behavior with invalid probability distributions."""
        calculator = FreeEnergyCalculator()

        # Negative probabilities
        posterior = np.array([0.8, -0.2])
        prior = np.array([0.5, 0.5])

        with pytest.raises((ValueError, AssertionError)):
            calculator.compute_complexity(posterior, prior)

    def test_unnormalized_probabilities(self):
        """Test behavior with unnormalized probability distributions."""
        calculator = FreeEnergyCalculator()

        # Probabilities don't sum to 1
        posterior = np.array([0.8, 0.3])  # Sum = 1.1
        prior = np.array([0.5, 0.5])

        # Should either normalize automatically or raise error
        try:
            complexity = calculator.compute_complexity(posterior, prior)
            assert np.isfinite(complexity)
        except (ValueError, AssertionError):
            pass  # Expected behavior for unnormalized distributions


class TestFreeEnergyIntegration:
    """Integration tests for free energy calculations."""

    def test_active_inference_loop(self):
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

            vfe = calculator.compute_variational_free_energy(
                obs_vec, pred_obs, posterior, state_beliefs
            )

            free_energy_history.append(vfe)

            # Update beliefs for next timestep
            state_beliefs = posterior

        assert len(free_energy_history) == n_timesteps
        assert all(np.isfinite(fe) for fe in free_energy_history)

        # Free energy should generally decrease as beliefs improve
        # (though this isn't guaranteed in this simple simulation)
        assert np.mean(free_energy_history) > 0

    def test_policy_comparison(self):
        """Test comparing multiple policies using expected free energy."""
        calculator = FreeEnergyCalculator()

        # Set up scenario
        n_states = 4
        n_observations = 3
        n_actions = 2

        state_beliefs = np.array([0.4, 0.3, 0.2, 0.1])
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
            efe = calculator.compute_expected_free_energy(
                policy, state_beliefs, observation_model, preferences, return_components=True
            )
            policy_values.append(efe)

        # All evaluations should be valid
        assert len(policy_values) == 5
        for pv in policy_values:
            assert "expected_free_energy" in pv
            assert "epistemic_value" in pv
            assert "pragmatic_value" in pv
            assert np.isfinite(pv["expected_free_energy"])

        # Find optimal policy
        efe_values = [pv["expected_free_energy"] for pv in policy_values]
        best_policy_idx = np.argmin(efe_values)

        assert 0 <= best_policy_idx < len(policies)

        # Best policy should have lowest expected free energy
        best_efe = efe_values[best_policy_idx]
        assert all(best_efe <= efe for efe in efe_values)
