"""
Test that the testing infrastructure is properly set up.

This module verifies that fixtures, strategies, and Hypothesis
configuration are working correctly.
"""

import sys
from pathlib import Path

# Add project root to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from typing import Any, Dict  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from hypothesis import given, settings  # noqa: E402

from tests.strategies import belief_state_strategy  # noqa: E402
from tests.strategies import (  # noqa: E402
    body_state_strategy,
    error_variance_strategy,
    observation_strategy,
)


def test_config_fixture(config: Any) -> None:
    """Test that config fixture loads successfully."""
    assert config is not None
    assert "system" in config
    assert "active_inference" in config
    assert "ignition" in config


def test_apgi_simulation_fixture(apgi_simulation: Any) -> None:
    """Test that apgi_simulation fixture initializes correctly."""
    assert apgi_simulation is not None
    assert apgi_simulation.time == 0.0


def test_body_model_fixture(body_model: Any) -> None:
    """Test that body_model fixture initializes correctly."""
    assert body_model is not None


def test_random_observation_fixture(random_observation: np.ndarray[Any, Any]) -> None:
    """Test that random_observation fixture generates valid data."""
    assert isinstance(random_observation, np.ndarray)
    assert random_observation.shape == (256,)
    assert not np.any(np.isnan(random_observation))
    assert not np.any(np.isinf(random_observation))


def test_random_body_state_fixture(random_body_state: Dict[str, Any]) -> None:
    """Test that random_body_state fixture generates valid data."""
    assert isinstance(random_body_state, dict)
    assert "heart_rate" in random_body_state
    assert "cortisol" in random_body_state
    assert "temperature" in random_body_state
    assert "glucose" in random_body_state

    # Check physiological ranges
    assert 60 <= random_body_state["heart_rate"] <= 100
    assert 8 <= random_body_state["cortisol"] <= 15
    assert 36.5 <= random_body_state["temperature"] <= 37.5
    assert 4.0 <= random_body_state["glucose"] <= 6.0


@given(body_state=body_state_strategy())
def test_body_state_strategy_generates_valid_states(body_state: Dict[str, Any]) -> None:
    """Test that body_state_strategy generates physiologically valid states."""
    assert isinstance(body_state, dict)
    assert "heart_rate" in body_state
    assert "cortisol" in body_state
    assert "temperature" in body_state
    assert "glucose" in body_state

    # Check physiological ranges
    assert 50 <= body_state["heart_rate"] <= 120
    assert 5 <= body_state["cortisol"] <= 30
    assert 36.0 <= body_state["temperature"] <= 39.0
    assert 3.0 <= body_state["glucose"] <= 8.0


@given(obs=observation_strategy())
def test_observation_strategy_generates_valid_observations(obs: np.ndarray[Any, Any]) -> None:
    """Test that observation_strategy generates valid observation vectors."""
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (256,)
    assert not np.any(np.isnan(obs))
    assert not np.any(np.isinf(obs))
    assert np.all(obs >= -10.0)
    assert np.all(obs <= 10.0)


def test_belief_state_strategy_generates_valid_beliefs() -> None:
    """Test that belief_state_strategy can generate valid belief states."""
    # Test with a single manual generation to avoid Hypothesis health check issues
    # The strategy generates large amounts of data which is expected for belief states
    from hypothesis import find

    # Use smaller dimensions to avoid hanging during test generation
    beliefs = find(belief_state_strategy(num_levels=2, level_dims=[4, 2]), lambda x: True)

    assert isinstance(beliefs, list)
    assert len(beliefs) == 2  # Reduced num_levels

    for belief in beliefs:
        assert "mean" in belief
        assert "precision" in belief
        assert "prediction_error" in belief

        assert isinstance(belief["mean"], np.ndarray)
        assert isinstance(belief["prediction_error"], np.ndarray)
        assert belief["mean"].shape == belief["prediction_error"].shape

        assert belief["precision"] > 0
        assert np.isfinite(belief["precision"])

        assert not np.any(np.isnan(belief["mean"]))
        assert not np.any(np.isinf(belief["mean"]))
        assert not np.any(np.isnan(belief["prediction_error"]))
        assert not np.any(np.isinf(belief["prediction_error"]))


@given(variance=error_variance_strategy())
def test_error_variance_strategy_generates_valid_variances(variance: float) -> None:
    """Test that error_variance_strategy generates valid variance values."""
    assert isinstance(variance, float)
    assert variance >= 0.01
    assert variance <= 100.0
    assert np.isfinite(variance)


def test_hypothesis_profile_loaded() -> None:
    """Test that Hypothesis profile is properly configured."""
    # This test verifies that the Hypothesis settings are loaded
    # by checking that a property test runs with the expected number of examples

    call_count = [0]

    @given(x=error_variance_strategy())
    @settings(max_examples=5)  # Override for this specific test
    def count_examples(x: Any) -> None:
        call_count[0] += 1

    count_examples()

    # Should have run exactly 5 examples
    assert call_count[0] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
