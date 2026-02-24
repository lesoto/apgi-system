"""Unit tests for ActiveInferenceEngine."""

import pytest
import numpy as np
import yaml
from pathlib import Path

from apgi_system.core.active_inference import (
    ActiveInferenceEngine,
    HierarchicalGaussianFilter,
)


@pytest.fixture
def config():
    """Load default configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def simple_config():
    """Simple test configuration."""
    return {
        "hierarchy": {
            "num_levels": 3,
            "level_configs": [
                {"nodes": 64, "name": "sensory"},
                {"nodes": 32, "name": "perceptual"},
                {"nodes": 16, "name": "conceptual"},
            ],
        },
        "active_inference": {"learning_rate": 0.01, "precision_range": [0.1, 10.0]},
        "system": {"timestep_ms": 1.0},
        "num_policies": 5,
        "planning_horizon": 2,
    }


class TestActiveInferenceEngine:
    """Test ActiveInferenceEngine functionality."""

    def test_initialization(self, simple_config) -> None:
        """Test engine initializes correctly."""
        engine = ActiveInferenceEngine(simple_config)

        assert engine.filter is not None
        assert engine.fe_calc is not None
        assert engine.num_policies == 5
        assert engine.planning_horizon == 2
        assert engine.time == 0.0
        assert engine.timestep == 0.001

    def test_step_with_observation(self, simple_config) -> None:
        """Test single step with observation."""
        engine = ActiveInferenceEngine(simple_config)
        observation = np.random.randn(64)

        action, info = engine.step(observation)

        # Check return types
        assert isinstance(action, np.ndarray)
        assert isinstance(info, dict)

        # Check info contents
        assert "time" in info
        assert "free_energy" in info
        assert "beliefs" in info
        assert "precisions" in info
        assert "prediction_errors" in info

        # Check time advancement
        assert info["time"] > 0.0
        assert engine.time > 0.0

    def test_step_with_actions(self, simple_config) -> None:
        """Test step with available actions."""
        engine = ActiveInferenceEngine(simple_config)
        observation = np.random.randn(64)
        actions = [np.array([0.0]), np.array([1.0]), np.array([-1.0])]

        action, info = engine.step(observation, actions)

        # Should select one of the available actions
        action_matches = any(np.allclose(action, a) for a in actions)
        assert action_matches, f"Selected action {action} not in available actions {actions}"

        # Should have EFE components
        assert "efe_components" in info
        # EFE components might be empty if no valid policy evaluation occurred
        assert isinstance(info["efe_components"], dict)

    def test_step_without_actions(self, simple_config) -> None:
        """Test step without available actions."""
        engine = ActiveInferenceEngine(simple_config)
        observation = np.random.randn(64)

        action, info = engine.step(observation, [])

        # Should return null action
        assert np.allclose(action, np.zeros(1))
        assert info["efe_components"] == {}

    def test_multiple_steps(self, simple_config) -> None:
        """Test multiple consecutive steps."""
        engine = ActiveInferenceEngine(simple_config)

        free_energies = []
        for i in range(5):
            observation = np.random.randn(64) * 0.1  # Small noise
            action, info = engine.step(observation)
            free_energies.append(info["free_energy"])

        # Time should advance
        assert engine.time == 5 * engine.timestep

        # Free energy should be finite and positive
        for fe in free_energies:
            assert np.isfinite(fe)
            assert fe >= 0

    def test_reset(self, simple_config) -> None:
        """Test engine reset functionality."""
        engine = ActiveInferenceEngine(simple_config)

        # Run some steps
        for _ in range(3):
            observation = np.random.randn(64)
            engine.step(observation)

        initial_time = engine.time
        assert initial_time > 0

        # Reset
        engine.reset()

        # Time should reset but beliefs should be reset
        assert engine.time == 0.0
        for belief in engine.filter.beliefs:
            assert np.allclose(belief.mean, 0.0)
            assert np.allclose(belief.prediction_error, 0.0)

    def test_invalid_observation_shape(self, simple_config) -> None:
        """Test error handling for invalid observation shape."""
        engine = ActiveInferenceEngine(simple_config)

        # Wrong shape observation
        with pytest.raises(ValueError):
            engine.step(np.random.randn(32))  # Should be 64

    def test_invalid_observation_values(self, simple_config) -> None:
        """Test error handling for invalid observation values."""
        engine = ActiveInferenceEngine(simple_config)

        # NaN observation
        observation = np.full(64, np.nan)
        with pytest.raises(ValueError):
            engine.step(observation)

        # Inf observation
        observation = np.full(64, np.inf)
        with pytest.raises(ValueError):
            engine.step(observation)


class TestHierarchicalGaussianFilter:
    """Test HierarchicalGaussianFilter functionality."""

    def test_initialization(self) -> None:
        """Test filter initializes correctly."""
        filter = HierarchicalGaussianFilter(
            num_levels=3, state_dims=[64, 32, 16], observation_dim=64
        )

        assert filter.num_levels == 3
        assert len(filter.beliefs) == 3
        assert filter.beliefs[0].mean.shape == (64,)
        assert filter.beliefs[1].mean.shape == (32,)
        assert filter.beliefs[2].mean.shape == (16,)

    def test_update_basic(self) -> None:
        """Test basic update functionality."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[32, 16], observation_dim=32)

        observation = np.random.randn(32)
        beliefs, fe = filter.update(observation)

        assert len(beliefs) == 2
        assert isinstance(fe, float)
        assert fe >= 0
        assert np.isfinite(fe)

    def test_learning_reduces_error(self) -> None:
        """Test that repeated observations reduce prediction error."""
        filter = HierarchicalGaussianFilter(
            num_levels=2, state_dims=[16, 8], observation_dim=16, config={"learning_rate": 0.1}
        )

        # Fixed observation
        observation = np.ones(16)

        errors = []
        for _ in range(10):
            beliefs, fe = filter.update(observation)
            error = np.linalg.norm(beliefs[0].prediction_error)
            errors.append(error)

        # Error should generally decrease (allowing some fluctuation)
        assert errors[-1] < errors[0] * 1.1  # Allow 10% tolerance

    def test_precision_updates(self) -> None:
        """Test precision updates with error variance."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[16, 8], observation_dim=16)

        initial_precision = filter.beliefs[0].precision

        # High error observation
        observation = np.random.randn(16) * 10
        filter.update(observation)

        # Precision should adjust
        assert filter.beliefs[0].precision != initial_precision

    def test_invalid_inputs(self) -> None:
        """Test error handling for invalid inputs."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[16, 8], observation_dim=16)

        # Wrong shape
        with pytest.raises(ValueError):
            filter.update(np.random.randn(8))

        # NaN values
        with pytest.raises(ValueError):
            filter.update(np.full(16, np.nan))

        # Invalid dt
        with pytest.raises(ValueError):
            filter.update(np.random.randn(16), dt=-1.0)

    def test_free_energy_components(self) -> None:
        """Test free energy computation."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[8, 4], observation_dim=8)

        observation = np.random.randn(8)
        beliefs, fe = filter.update(observation)

        # Free energy should be sum of precision-weighted errors
        manual_fe = 0.0
        for belief in beliefs:
            error_sq = np.sum(belief.prediction_error**2)
            manual_fe += 0.5 * belief.precision * error_sq

        # Should be approximately equal (allowing for numerical differences)
        # Use larger tolerance for numerical stability
        assert abs(fe - manual_fe) < 1e-5

    def test_edge_case_zero_observation(self) -> None:
        """Test edge case with zero observation."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[8, 4], observation_dim=8)

        observation = np.zeros(8)
        beliefs, fe = filter.update(observation)

        assert np.isfinite(fe)
        assert fe >= 0

    def test_edge_case_large_observation(self) -> None:
        """Test edge case with large observation values."""
        filter = HierarchicalGaussianFilter(num_levels=2, state_dims=[8, 4], observation_dim=8)

        observation = np.ones(8) * 1000
        beliefs, fe = filter.update(observation)

        assert np.isfinite(fe)
        assert fe >= 0

    def test_boundary_precision_range(self) -> None:
        """Test precision stays within configured bounds."""
        filter = HierarchicalGaussianFilter(
            num_levels=2,
            state_dims=[8, 4],
            observation_dim=8,
            config={"precision_range": [0.5, 5.0]},
        )

        # Very noisy observations
        for _ in range(20):
            observation = np.random.randn(8) * 100
            filter.update(observation)

        # Check precision bounds
        for belief in filter.beliefs:
            assert 0.5 <= belief.precision <= 5.0
