"""Unit tests for Active Inference module."""

import numpy as np

from apgi_framework.core.active_inference import (
    ActiveInferenceAgent,
    HierarchicalGaussianFilter,
    simulate_active_inference,
)


class TestHierarchicalGaussianFilter:
    """Test HierarchicalGaussianFilter functionality."""

    def test_initialization_default(self) -> None:
        """Test filter initializes with default parameters."""
        filter = HierarchicalGaussianFilter()
        assert filter.num_levels == 3
        assert filter.state_dims == [32, 16, 8]
        assert filter.observation_dim == 16

    def test_initialization_custom(self) -> None:
        """Test filter initializes with custom parameters."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[64, 32], observation_dim=64)
        assert filter.num_levels == 2
        assert filter.state_dims == [64, 32]
        assert filter.observation_dim == 64

    def test_update_returns_tuple(self) -> None:
        """Test update returns tuple of (belief_states, free_energy)."""
        filter = HierarchicalGaussianFilter(observation_dim=16, state_dims=[16, 8, 4])
        observation = np.random.randn(16)
        beliefs, fe = filter.update(observation)

        assert isinstance(beliefs, list)
        assert len(beliefs) == 3
        assert isinstance(fe, float)

    def test_update_belief_state_changes(self) -> None:
        """Test that update modifies belief state."""
        filter = HierarchicalGaussianFilter(observation_dim=8, state_dims=[8, 4, 2])
        initial_belief = filter.get_belief_state().copy()
        observation = np.ones(8)

        filter.update(observation)
        new_belief = filter.get_belief_state()

        # Belief should have changed
        assert not np.allclose(initial_belief, new_belief)

    def test_update_free_energy_positive(self) -> None:
        """Test that free energy is non-negative."""
        filter = HierarchicalGaussianFilter(observation_dim=8, state_dims=[8, 4, 2])
        observation = np.random.randn(8)
        beliefs, fe = filter.update(observation)

        assert fe >= 0
        assert np.isfinite(fe)

    def test_get_belief_state_returns_copy(self) -> None:
        """Test that get_belief_state returns a copy."""
        filter = HierarchicalGaussianFilter(observation_dim=8, state_dims=[8, 4, 2])
        belief1 = filter.get_belief_state()
        belief2 = filter.get_belief_state()

        # Should be copies, not the same object
        assert belief1 is not belief2
        assert np.array_equal(belief1, belief2)

    def test_multiple_updates(self) -> None:
        """Test multiple consecutive updates."""
        filter = HierarchicalGaussianFilter(observation_dim=16, state_dims=[16, 8, 4])
        free_energies = []

        for _ in range(10):
            observation = np.random.randn(16) * 0.1
            beliefs, fe = filter.update(observation)
            free_energies.append(fe)

        # All free energies should be finite and non-negative
        for fe in free_energies:
            assert np.isfinite(fe)
            assert fe >= 0

    def test_update_with_zero_observation(self) -> None:
        """Test update with zero observation."""
        filter = HierarchicalGaussianFilter(observation_dim=8, state_dims=[8, 4, 2])
        observation = np.zeros(8)
        beliefs, fe = filter.update(observation)

        assert np.isfinite(fe)
        assert fe >= 0

    def test_cache_attributes_exist(self) -> None:
        """Test that cache attributes are initialized."""
        filter = HierarchicalGaussianFilter()
        assert hasattr(filter, "_projection_cache")
        assert hasattr(filter, "_cache_access_order")
        assert hasattr(filter, "_cache_lock")

    def test_project_up_top_level(self) -> None:
        """Test _project_up from top level returns state unchanged."""
        filter = HierarchicalGaussianFilter(num_levels=3, state_dims=[16, 12, 8])
        state = np.random.randn(8)
        result = filter._project_up(2, state)
        assert np.array_equal(result, state)


class TestActiveInferenceAgent:
    """Test ActiveInferenceAgent functionality."""

    def test_initialization_default(self) -> None:
        """Test agent initializes with default configuration."""
        agent = ActiveInferenceAgent(agent_id=1)
        assert agent.agent_id == 1
        assert agent.config is not None

    def test_initialization_custom(self) -> None:
        """Test agent initializes with custom configuration."""
        agent = ActiveInferenceAgent(agent_id=2, config={"test": True})
        assert agent.agent_id == 2
        assert agent.config["test"] is True

    def test_select_action_returns_int(self) -> None:
        """Test select_action returns an integer."""
        agent = ActiveInferenceAgent(agent_id=3)
        observation = np.random.randn(32)
        action = agent.select_action(observation)

        assert isinstance(action, int)
        assert 0 <= action

    def test_select_action_updates_belief(self) -> None:
        """Test that select_action updates free energy history."""
        agent = ActiveInferenceAgent(agent_id=4)
        observation = np.ones(32)

        agent.select_action(observation)

        # Free energy should have been recorded
        assert len(agent.free_energy_history) > 0

    def test_get_free_energy(self) -> None:
        """Test get_free_energy returns non-negative float."""
        agent = ActiveInferenceAgent(agent_id=5)
        observation = np.random.randn(32)
        agent.select_action(observation)
        fe = agent.free_energy_history[-1]

        assert isinstance(fe, float)
        assert fe >= 0
        assert np.isfinite(fe)

    def test_action_selection_bounds(self) -> None:
        """Test that selected action is within valid bounds."""
        agent = ActiveInferenceAgent(agent_id=6)

        for _ in range(20):
            observation = np.random.randn(32)
            action = agent.select_action(observation)
            assert 0 <= action


class TestSimulateActiveInference:
    """Test simulate_active_inference function."""

    def test_simulate_returns_dict(self) -> None:
        """Test simulation returns correct structure."""
        agent = ActiveInferenceAgent(agent_id=7)
        observations = [np.random.randn(32) for _ in range(5)]
        result = simulate_active_inference(observations, agent)

        assert isinstance(result, dict)
        assert "actions" in result
        assert "free_energies" in result
        assert "total_free_energy" in result

    def test_simulate_actions_length(self) -> None:
        """Test that actions list matches observations length."""
        agent = ActiveInferenceAgent(agent_id=8)
        observations = [np.random.randn(32) for _ in range(5)]
        result = simulate_active_inference(observations, agent)

        assert len(result["actions"]) == 5
        assert len(result["free_energies"]) == 5

    def test_simulate_actions_valid(self) -> None:
        """Test that all actions are within valid bounds."""
        agent = ActiveInferenceAgent(agent_id=9)
        observations = [np.random.randn(32) for _ in range(10)]
        result = simulate_active_inference(observations, agent)

        for action in result["actions"]:
            assert isinstance(action, int)
            assert 0 <= action

    def test_simulate_total_free_energy(self) -> None:
        """Test that total_free_energy is sum of free energies."""
        agent = ActiveInferenceAgent(agent_id=10)
        observations = [np.random.randn(32) for _ in range(5)]
        result = simulate_active_inference(observations, agent)

        expected_total = sum(result["free_energies"])
        assert abs(result["total_free_energy"] - expected_total) < 1e-10

    def test_simulate_empty_observations(self) -> None:
        """Test simulation with empty observations list."""
        agent = ActiveInferenceAgent(agent_id=11)
        observations: list = []
        result = simulate_active_inference(observations, agent)

        assert result["actions"] == []
        assert result["free_energies"] == []
        assert result["total_free_energy"] == 0

    def test_simulate_single_observation(self) -> None:
        """Test simulation with single observation."""
        agent = ActiveInferenceAgent(agent_id=12)
        observations = [np.random.randn(32)]
        result = simulate_active_inference(observations, agent)

        assert len(result["actions"]) == 1
        assert len(result["free_energies"]) == 1
        assert result["total_free_energy"] == result["free_energies"][0]
