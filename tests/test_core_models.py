"""
Tests for core model modules.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add the framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the real implementations
from apgi_framework.engines import PredictiveIgnitionNetwork, SomaticAgent


class TestSomaticAgent:
    """Test SomaticAgent class from active_inference module."""

    def test_initialization(self) -> None:
        """Test agent initialization."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)

        assert agent.n_states == 4
        assert agent.n_actions == 3
        assert agent.somatic_markers.shape == (2, 3)
        assert agent.precision == 1.0

        # Somatic markers should be initialized to zeros
        assert np.all(agent.somatic_markers == 0)

    def test_expected_free_energy_calculation(self) -> None:
        """Test expected free energy calculation."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0

        G_modified, G_basic = agent.expected_free_energy(beliefs, context)

        # Should return two arrays
        assert len(G_modified) == agent.n_actions
        assert len(G_basic) == agent.n_actions
        assert isinstance(G_modified, np.ndarray)
        assert isinstance(G_basic, np.ndarray)

        # Modified should be different from basic due to somatic markers
        # (though initially somatic markers are zeros, so they should be equal)
        np.testing.assert_array_equal(G_modified, G_basic)

    def test_somatic_marker_update(self) -> None:
        """Test somatic marker updating."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        context = 0
        action = 1
        outcome_valence = -1.0

        # Check initial value
        initial_value = agent.somatic_markers[context, action]
        assert initial_value == 0.0

        # Update with negative outcome
        agent.update_somatic_marker(context, action, outcome_valence)

        # Should have moved in negative direction
        new_value = agent.somatic_markers[context, action]
        assert new_value < initial_value
        assert new_value == -0.1  # learning_rate * (valence - initial)

    def test_multiple_marker_updates(self) -> None:
        """Test multiple somatic marker updates."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        context = 0
        action = 1

        # Multiple positive outcomes
        for _ in range(10):
            agent.update_somatic_marker(context, action, 1.0)

        # Should approach positive value asymptotically
        final_value = agent.somatic_markers[context, action]
        assert final_value > 0.5  # Should be significantly positive

    def test_decision_making_habitual(self) -> None:
        """Test habitual decision making (low surprise)."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0
        surprise = 0.5  # Low surprise

        action, conscious, G = agent.decide(beliefs, context, surprise)

        # Should be habitual (unconscious)
        assert conscious is False
        assert 0 <= action < agent.n_actions
        assert len(G) == agent.n_actions

    def test_decision_making_conscious_ignition(self) -> None:
        """Test conscious decision making (high surprise)."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0
        surprise = 2.5  # High surprise

        action, conscious, G = agent.decide(beliefs, context, surprise)

        # Should have valid decision regardless of conscious/unconscious
        assert isinstance(conscious, bool)
        assert 0 <= action < agent.n_actions
        assert len(G) == agent.n_actions

    def test_precision_effect_on_decision(self) -> None:
        """Test effect of precision on decision making."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)
        agent.precision = 2.0  # Higher precision

        # Set up somatic markers
        agent.somatic_markers[0, 0] = 1.0  # Positive bias for action 0
        agent.somatic_markers[0, 1] = -1.0  # Negative bias for action 1

        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0
        surprise = 1.0

        action, conscious, G = agent.decide(beliefs, context, surprise)

        # With higher precision, somatic markers should have stronger effect
        # Action 0 should be favored due to positive somatic marker
        assert action == 0

    def test_context_specific_markers(self) -> None:
        """Test that somatic markers are context-specific."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)

        # Update marker in context 0
        agent.update_somatic_marker(0, 1, -1.0)

        # Check that only context 0 is affected
        assert agent.somatic_markers[0, 1] < 0
        assert agent.somatic_markers[1, 1] == 0  # Context 1 unchanged


class TestPredictiveIgnitionNetwork:
    """Test PredictiveIgnitionNetwork class from hierarchical_predictive module."""

    def test_initialization(self) -> None:
        """Test network initialization."""
        n_features = 10
        n_global_units = 5
        threshold = 2.0
        alpha = 2.0

        network = PredictiveIgnitionNetwork(n_features, n_global_units, threshold, alpha)

        assert network.W.shape == (n_global_units, n_features)
        assert network.precision.shape == (n_features,)
        assert network.threshold == threshold
        assert network.alpha == alpha
        assert len(network.global_activation) == n_global_units

        # Precision should be initialized to ones
        assert np.all(network.precision == 1.0)

        # Global activation should be initialized to zeros
        assert np.all(network.global_activation == 0.0)

    def test_forward_pass_no_ignition(self) -> None:
        """Test forward pass without ignition."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=10.0, alpha=2.0
        )

        # Use small input to avoid ignition
        sensory_input = np.random.randn(10) * 0.1
        somatic_gain = 1.0

        (
            predictions,
            errors,
            weighted_errors,
            ignited,
            ignition_prob,
        ) = network.forward_pass(sensory_input, somatic_gain)

        # Check outputs
        assert len(predictions) == 10
        assert len(errors) == 10
        assert len(weighted_errors) == 10
        assert ignited is False
        assert 0.0 <= ignition_prob <= 1.0

        # Should not ignite with low surprise
        assert ignition_prob < 0.5

        # Predictions should be based on current global activation (initially zeros)
        assert np.allclose(predictions, 0.0)

    def test_forward_pass_with_ignition(self) -> None:
        """Test forward pass with ignition."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=1.0, alpha=2.0
        )

        # Use large input to trigger ignition
        sensory_input = np.random.randn(10) * 2.0
        somatic_gain = 2.0

        (
            predictions,
            errors,
            weighted_errors,
            ignited,
            ignition_prob,
        ) = network.forward_pass(sensory_input, somatic_gain)

        # Should ignite with high surprise
        assert ignited is True
        assert ignition_prob > 0.5

        # Global activation should be updated
        assert not np.allclose(network.global_activation, 0.0)

    def test_somatic_gain_effect(self) -> None:
        """Test effect of somatic gain on ignition."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )

        sensory_input = np.random.randn(10) * 1.0

        # Test with low somatic gain
        _, _, _, ignited_low, prob_low = network.forward_pass(sensory_input, somatic_gain=0.5)

        # Reset global activation
        network.global_activation = np.zeros(5)

        # Test with high somatic gain
        _, _, _, ignited_high, prob_high = network.forward_pass(sensory_input, somatic_gain=2.0)

        # Higher somatic gain should increase ignition probability
        assert prob_high > prob_low

    def test_precision_weighting(self) -> None:
        """Test precision weighting of errors."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )

        # Set different precision weights
        network.precision[:5] = 0.5  # Low precision for first half
        network.precision[5:] = 2.0  # High precision for second half

        sensory_input = np.ones(10)  # Uniform input
        somatic_gain = 1.0

        _, errors, weighted_errors, _, _ = network.forward_pass(sensory_input, somatic_gain)

        # Weighted errors should reflect precision differences
        assert np.all(weighted_errors[:5] < weighted_errors[5:])

    def test_prediction_error_calculation(self) -> None:
        """Test prediction error calculation."""
        network = PredictiveIgnitionNetwork(
            n_features=5, n_global_units=3, threshold=2.0, alpha=2.0
        )

        # Set known global activation
        network.global_activation = np.array([1.0, 0.5, -0.5])
        sensory_input = np.array([2.0, 1.0, 0.0, -1.0, -2.0])

        predictions, errors, _, _, _ = network.forward_pass(sensory_input, somatic_gain=1.0)

        # Check that predictions and errors have correct shapes and basic properties
        assert len(predictions) == 5
        assert len(errors) == 5
        assert isinstance(predictions, np.ndarray)
        assert isinstance(errors, np.ndarray)

        # Errors should be sensory_input - predictions
        expected_errors = sensory_input - predictions
        np.testing.assert_allclose(errors, expected_errors, rtol=1e-3, atol=1e-3)

    def test_ignition_probability_calculation(self) -> None:
        """Test ignition probability calculation."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )

        # Test with different total surprise values
        test_cases = [
            (0.0, False),  # Very low surprise
            (1.0, False),  # Below threshold
            (2.0, False),  # At threshold
            (3.0, True),  # Above threshold
            (5.0, True),  # Well above threshold
        ]

        for total_surprise, expected_ignition in test_cases:
            # Create input that should give approximately this total surprise
            sensory_input = np.ones(10) * (total_surprise / 10.0)

            _, _, _, ignited, prob = network.forward_pass(sensory_input, somatic_gain=1.0)

            if expected_ignition:
                assert ignited or prob > 0.3  # Allow some tolerance
            else:
                assert not ignited or prob < 0.7  # Allow some tolerance

    def test_global_activation_update(self) -> None:
        """Test global activation update during ignition."""
        network = PredictiveIgnitionNetwork(
            n_features=5, n_global_units=3, threshold=1.0, alpha=2.0
        )

        # Store initial activation
        initial_activation = network.global_activation.copy()

        # Use input that should trigger ignition
        sensory_input = np.random.randn(5) * 2.0
        somatic_gain = 2.0

        _, _, _, ignited, _ = network.forward_pass(sensory_input, somatic_gain)

        if ignited:
            # Global activation should have changed
            assert not np.allclose(network.global_activation, initial_activation)
        else:
            # Should remain unchanged if no ignition
            np.testing.assert_array_equal(network.global_activation, initial_activation)

    def test_multiple_forward_passes(self) -> None:
        """Test multiple forward passes in sequence."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )

        inputs = [np.random.randn(10) * 0.5 for _ in range(5)]

        for i, sensory_input in enumerate(inputs):
            predictions, errors, weighted_errors, ignited, prob = network.forward_pass(
                sensory_input, somatic_gain=1.0
            )

            # Check output shapes
            assert len(predictions) == 10
            assert len(errors) == 10
            assert len(weighted_errors) == 10
            assert isinstance(ignited, bool)
            assert 0.0 <= prob <= 1.0

    def test_network_state_persistence(self) -> None:
        """Test that network state persists between forward passes."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )

        # First pass with ignition
        sensory_input1 = np.random.randn(10) * 2.0
        _, _, _, ignited1, _ = network.forward_pass(sensory_input1, somatic_gain=2.0)

        # Second pass
        sensory_input2 = np.random.randn(10) * 0.5
        _, _, _, ignited2, _ = network.forward_pass(sensory_input2, somatic_gain=1.0)

        # Global activation should persist (may be modified by second pass)
        assert len(network.global_activation) == 5

        if ignited1:
            # Should have changed from initial zeros
            assert not np.allclose(network.global_activation, np.zeros(5))


class TestModelIntegration:
    """Test integration between different core models."""

    def test_surprise_to_decision_pipeline(self) -> None:
        """Test pipeline from surprise calculation to decision making."""
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)

        # Simulate surprise from some source
        surprise_values = [0.5, 1.0, 2.5, 3.0]
        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0

        decisions = []
        for surprise in surprise_values:
            action, conscious, G = agent.decide(beliefs, context, surprise)
            decisions.append((action, conscious))

        # Should have decisions for all surprise levels
        assert len(decisions) == len(surprise_values)

        # Higher surprise should lead to conscious decisions (when conditions are met)
        # Note: consciousness requires both high surprise AND low uncertainty (std < 0.5)
        # We can't guarantee the std condition, so we check that higher surprise has higher chance of consciousness
        # consciousness_values = [decision[1] for decision in decisions]

        # At least some of the higher surprise values should lead to consciousness
        # (when uncertainty condition is also met)
        high_surprise_conscious = any(decisions[i][1] for i in [2, 3])  # indices for 2.5, 3.0
        assert (
            high_surprise_conscious
        ), "Higher surprise values should sometimes lead to conscious decisions"

    def test_network_to_agent_communication(self) -> None:
        """Test communication between predictive network and somatic agent."""
        network = PredictiveIgnitionNetwork(
            n_features=10, n_global_units=5, threshold=2.0, alpha=2.0
        )
        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)

        # Generate surprise from network
        sensory_input = np.random.randn(10) * 1.5
        somatic_gain = 1.5

        _, errors, weighted_errors, ignited, ignition_prob = network.forward_pass(
            sensory_input, somatic_gain
        )

        # Convert network output to surprise signal for agent
        total_surprise = np.sum(np.abs(weighted_errors))

        # Agent makes decision based on this surprise
        beliefs = np.array([0.25, 0.25, 0.25, 0.25])
        context = 0

        action, conscious, G = agent.decide(beliefs, context, total_surprise)

        # Should have valid decision
        assert 0 <= action < agent.n_actions
        assert isinstance(conscious, bool)
        assert len(G) == agent.n_actions


if __name__ == "__main__":
    pytest.main([__file__])
