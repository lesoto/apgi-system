"""Tests for core active inference components."""

from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest
import yaml

from apgi_simulation.core import ActiveInferenceEngine, FreeEnergyCalculator, PrecisionWeighting


@pytest.fixture
def config() -> Dict[str, Any]:
    """Load default configuration."""
    config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def test_free_energy_calculator() -> None:
    """Test free energy calculation."""
    calc = FreeEnergyCalculator()

    obs = np.array([1.0, 2.0, 3.0])
    pred = np.array([1.1, 1.9, 3.2])
    precision = 1.0

    posterior_mean = np.array([1.0, 2.0, 3.0])
    posterior_cov = np.eye(3) * 0.5
    prior_mean = np.array([0.0, 0.0, 0.0])
    prior_cov = np.eye(3)

    fe, components = calc.compute_variational_free_energy(
        obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
    )

    assert fe > 0
    assert "accuracy" in components
    assert "complexity" in components


def test_precision_weighting(config: Dict[str, Any]) -> None:
    """Test precision weighting system."""
    precision = PrecisionWeighting(config)

    # Update with error variance
    result = precision.update(
        extero_error_variance=1.0, intero_error_variance=0.5, attention_target=np.array(["extero"])
    )

    assert "exteroceptive" in result
    assert "interoceptive" in result
    assert result["exteroceptive"] > 0
    assert result["interoceptive"] > 0


def test_active_inference_engine(config: Dict[str, Any]) -> None:
    """Test active inference engine."""
    engine = ActiveInferenceEngine(config)

    obs = np.random.randn(256)
    action, info = engine.step(obs)

    assert action is not None
    assert "free_energy" in info
    assert "beliefs" in info


def test_system_initialization(config: Dict[str, Any]) -> None:
    """Test that system can be initialized."""
    from apgi_simulation.system import APGISystem

    system = APGISystem()
    assert system is not None
    assert system.time == 0.0


def test_system_step(config: Dict[str, Any]) -> None:
    """Test single system step."""
    from apgi_simulation.system import APGISystem

    system = APGISystem()
    extero_input = np.random.randn(256)

    state = system.step(extero_input)

    assert "time" in state
    assert "ignition" in state
    assert "workspace" in state
    assert "body" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
