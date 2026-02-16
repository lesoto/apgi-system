"""
Test input validation integration in core components.

This test verifies that input validation is properly integrated into
the core components and catches invalid inputs.
"""

import pytest
import numpy as np
import yaml
from pathlib import Path

from apgi_system.core.active_inference import HierarchicalGaussianFilter
from apgi_system.core.predictive_processing import HierarchicalPredictor
from apgi_system.core.precision import PrecisionWeighting
from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.ignition.threshold import IgnitionThreshold
from apgi_system.ignition.global_workspace import GlobalWorkspace

# Load default config
config_path = Path(__file__).parent.parent / "config" / "default.yaml"
with open(config_path, "r") as f:
    DEFAULT_CONFIG = yaml.safe_load(f)


class TestActiveInferenceValidation:
    """Test validation in ActiveInferenceEngine and HierarchicalGaussianFilter."""

    def test_filter_update_invalid_observation_type(self) -> None:
        """Test that update rejects non-array observation."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)

        with pytest.raises(TypeError, match="observation must be numpy array"):
            filter.update([1.0, 2.0, 3.0])  # type: ignore

    def test_filter_update_invalid_observation_shape(self) -> None:
        """Test that update rejects wrong-shaped observation."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)

        with pytest.raises(ValueError, match="observation shape mismatch"):
            filter.update(np.random.randn(128))  # Wrong size

    def test_filter_update_nan_observation(self) -> None:
        """Test that update rejects NaN values."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)
        obs = np.random.randn(256)
        obs[0] = np.nan

        with pytest.raises(ValueError, match="observation contains NaN or Inf"):
            filter.update(obs)

    def test_filter_update_inf_observation(self) -> None:
        """Test that update rejects Inf values."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)
        obs = np.random.randn(256)
        obs[0] = np.inf

        with pytest.raises(ValueError, match="observation contains NaN or Inf"):
            filter.update(obs)

    def test_filter_update_invalid_dt(self) -> None:
        """Test that update rejects invalid dt values."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)
        obs = np.random.randn(256)

        # Negative dt
        with pytest.raises(ValueError, match="dt must be positive"):
            filter.update(obs, dt=-0.001)

        # Zero dt
        with pytest.raises(ValueError, match="dt must be positive"):
            filter.update(obs, dt=0.0)

        # Too large dt
        with pytest.raises(ValueError, match="dt must be in range"):
            filter.update(obs, dt=2.0)

    def test_filter_update_valid_inputs(self) -> None:
        """Test that update accepts valid inputs."""
        filter = HierarchicalGaussianFilter(3, [256, 128, 64], 256)
        obs = np.random.randn(256)

        # Should not raise
        beliefs, fe = filter.update(obs, dt=0.001)
        assert len(beliefs) == 3
        assert isinstance(fe, float)


class TestPredictiveProcessingValidation:
    """Test validation in HierarchicalPredictor."""

    def test_predict_invalid_extero_type(self) -> None:
        """Test that predict rejects non-array extero input."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="extero_input must be numpy array"):
            predictor.predict(extero_input=[1.0, 2.0])  # type: ignore

    def test_predict_invalid_extero_shape(self) -> None:
        """Test that predict rejects wrong-shaped extero input."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="extero_input shape mismatch"):
            predictor.predict(extero_input=np.random.randn(128))

    def test_predict_invalid_intero_shape(self) -> None:
        """Test that predict rejects wrong-shaped intero input."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="intero_input shape mismatch"):
            predictor.predict(intero_input=np.random.randn(10))  # Should be 6

    def test_predict_nan_extero(self) -> None:
        """Test that predict rejects NaN in extero input."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)
        extero = np.random.randn(256)
        extero[0] = np.nan

        with pytest.raises(ValueError, match="extero_input contains NaN or Inf"):
            predictor.predict(extero_input=extero)

    def test_predict_invalid_dt(self) -> None:
        """Test that predict rejects invalid dt values."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)
        extero = np.random.randn(256)

        # Negative dt
        with pytest.raises(ValueError, match="dt_ms must be positive"):
            predictor.predict(extero_input=extero, dt_ms=-1.0)

        # Too small dt
        with pytest.raises(ValueError, match="dt_ms must be in range"):
            predictor.predict(extero_input=extero, dt_ms=0.0001)

    def test_predict_valid_inputs(self) -> None:
        """Test that predict accepts valid inputs."""
        predictor = HierarchicalPredictor(DEFAULT_CONFIG)
        extero = np.random.randn(256)
        intero = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        # Should not raise
        results = predictor.predict(extero_input=extero, intero_input=intero, dt_ms=1.0)
        assert "exteroceptive" in results
        assert "interoceptive" in results


class TestPrecisionWeightingValidation:
    """Test validation in PrecisionWeighting."""

    def test_update_invalid_variance_type(self) -> None:
        """Test that update rejects non-numeric variance."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="extero_error_variance must be numeric"):
            precision.update(extero_error_variance="invalid")  # type: ignore[arg-type]

    def test_update_negative_variance(self) -> None:
        """Test that update rejects negative variance."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="extero_error_variance must be in range"):
            precision.update(extero_error_variance=-1.0)

    def test_update_nan_variance(self) -> None:
        """Test that update rejects NaN variance."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="extero_error_variance is NaN or Inf"):
            precision.update(extero_error_variance=np.nan)

    def test_update_inf_variance(self) -> None:
        """Test that update rejects Inf variance."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="intero_error_variance is NaN or Inf"):
            precision.update(intero_error_variance=np.inf)

    def test_update_invalid_attention_target(self) -> None:
        """Test that update rejects invalid attention target."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="attention_target must be 'extero' or 'intero'"):
            precision.update(attention_target="invalid")

    def test_update_valid_inputs(self) -> None:
        """Test that update accepts valid inputs."""
        precision = PrecisionWeighting(DEFAULT_CONFIG)

        # Should not raise
        result = precision.update(
            extero_error_variance=2.0, intero_error_variance=1.5, attention_target="extero"
        )
        assert "exteroceptive" in result
        assert "interoceptive" in result


class TestFreeEnergyCalculatorValidation:
    """Test validation in FreeEnergyCalculator."""

    def test_compute_invalid_observation_type(self) -> None:
        """Test that compute rejects non-array observation."""
        calc = FreeEnergyCalculator()

        with pytest.raises(TypeError, match="observation must be numpy array"):
            calc.compute_variational_free_energy(
                observation=[1.0, 2.0],  # type: ignore[arg-type]
                prediction=np.array([1.0, 2.0]),
                precision=1.0,
                posterior_mean=np.array([1.0, 2.0]),
                posterior_cov=np.eye(2),
                prior_mean=np.zeros(2),
                prior_cov=np.eye(2),
            )

    def test_compute_shape_mismatch(self) -> None:
        """Test that compute rejects mismatched shapes."""
        calc = FreeEnergyCalculator()

        with pytest.raises(ValueError, match="observation and prediction shapes must match"):
            calc.compute_variational_free_energy(
                observation=np.array([1.0, 2.0, 3.0]),
                prediction=np.array([1.0, 2.0]),
                precision=1.0,
                posterior_mean=np.array([1.0, 2.0]),
                posterior_cov=np.eye(2),
                prior_mean=np.zeros(2),
                prior_cov=np.eye(2),
            )

    def test_compute_nan_observation(self) -> None:
        """Test that compute rejects NaN values."""
        calc = FreeEnergyCalculator()
        obs = np.array([1.0, np.nan, 3.0])

        with pytest.raises(ValueError, match="observation contains NaN or Inf"):
            calc.compute_variational_free_energy(
                observation=obs,
                prediction=np.array([1.0, 2.0, 3.0]),
                precision=1.0,
                posterior_mean=np.array([1.0, 2.0, 3.0]),
                posterior_cov=np.eye(3),
                prior_mean=np.zeros(3),
                prior_cov=np.eye(3),
            )

    def test_compute_negative_precision(self) -> None:
        """Test that compute rejects negative precision."""
        calc = FreeEnergyCalculator()

        with pytest.raises(ValueError, match="precision must be positive"):
            calc.compute_variational_free_energy(
                observation=np.array([1.0, 2.0, 3.0]),
                prediction=np.array([1.0, 2.0, 3.0]),
                precision=-1.0,
                posterior_mean=np.array([1.0, 2.0, 3.0]),
                posterior_cov=np.eye(3),
                prior_mean=np.zeros(3),
                prior_cov=np.eye(3),
            )

    def test_compute_prior_posterior_shape_mismatch(self) -> None:
        """Test that compute rejects mismatched prior/posterior shapes."""
        calc = FreeEnergyCalculator()

        with pytest.raises(ValueError, match="posterior_mean and prior_mean shapes must match"):
            calc.compute_variational_free_energy(
                observation=np.array([1.0, 2.0, 3.0]),
                prediction=np.array([1.0, 2.0, 3.0]),
                precision=1.0,
                posterior_mean=np.array([1.0, 2.0, 3.0]),
                posterior_cov=np.eye(3),
                prior_mean=np.zeros(2),  # Wrong size
                prior_cov=np.eye(2),
            )

    def test_compute_valid_inputs(self) -> None:
        """Test that compute accepts valid inputs."""
        calc = FreeEnergyCalculator()

        # Should not raise
        fe, components = calc.compute_variational_free_energy(
            observation=np.array([1.0, 2.0, 3.0]),
            prediction=np.array([1.1, 1.9, 3.2]),
            precision=2.0,
            posterior_mean=np.array([1.0, 2.0, 3.0]),
            posterior_cov=0.1 * np.eye(3),
            prior_mean=np.zeros(3),
            prior_cov=np.eye(3),
        )
        assert isinstance(fe, float)
        assert "accuracy" in components
        assert "complexity" in components


class TestIgnitionThresholdValidation:
    """Test validation in IgnitionThreshold."""

    def test_compute_ignition_signal_invalid_extero_error_type(self) -> None:
        """Test that compute_ignition_signal rejects non-array extero_error."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="extero_error must be numpy array"):
            threshold.compute_ignition_signal(
                extero_error=[1.0, 2.0],  # type: ignore[arg-type]
                extero_precision=1.5,
                intero_error=np.array([0.5]),
                intero_precision=1.0,
            )

    def test_compute_ignition_signal_negative_extero_precision(self) -> None:
        """Test that compute_ignition_signal rejects negative extero_precision."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="extero_precision must be positive"):
            threshold.compute_ignition_signal(
                extero_error=np.array([1.0, 2.0]),
                extero_precision=-1.5,
                intero_error=np.array([0.5]),
                intero_precision=1.0,
            )

    def test_compute_ignition_signal_negative_intero_precision(self) -> None:
        """Test that compute_ignition_signal rejects negative intero_precision."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="intero_precision must be positive"):
            threshold.compute_ignition_signal(
                extero_error=np.array([1.0, 2.0]),
                extero_precision=1.5,
                intero_error=np.array([0.5]),
                intero_precision=-1.0,
            )

    def test_compute_ignition_signal_invalid_somatic_marker_gain(self) -> None:
        """Test that compute_ignition_signal rejects out-of-range somatic_marker_gain."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)

        # Too low
        with pytest.raises(ValueError, match="somatic_marker_gain must be in range"):
            threshold.compute_ignition_signal(
                extero_error=np.array([1.0, 2.0]),
                extero_precision=1.5,
                intero_error=np.array([0.5]),
                intero_precision=1.0,
                somatic_marker_gain=0.3,
            )

        # Too high
        with pytest.raises(ValueError, match="somatic_marker_gain must be in range"):
            threshold.compute_ignition_signal(
                extero_error=np.array([1.0, 2.0]),
                extero_precision=1.5,
                intero_error=np.array([0.5]),
                intero_precision=1.0,
                somatic_marker_gain=3.0,
            )

    def test_compute_ignition_signal_nan_extero_error(self) -> None:
        """Test that compute_ignition_signal rejects NaN in extero_error."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)
        extero = np.array([1.0, np.nan, 2.0])

        with pytest.raises(ValueError, match="extero_error contains NaN or Inf"):
            threshold.compute_ignition_signal(
                extero_error=extero,
                extero_precision=1.5,
                intero_error=np.array([0.5]),
                intero_precision=1.0,
            )

    def test_compute_ignition_signal_inf_intero_error(self) -> None:
        """Test that compute_ignition_signal rejects Inf in intero_error."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)
        intero = np.array([0.5, np.inf])

        with pytest.raises(ValueError, match="intero_error contains NaN or Inf"):
            threshold.compute_ignition_signal(
                extero_error=np.array([1.0, 2.0]),
                extero_precision=1.5,
                intero_error=intero,
                intero_precision=1.0,
            )

    def test_compute_ignition_signal_valid_inputs(self) -> None:
        """Test that compute_ignition_signal accepts valid inputs."""
        threshold = IgnitionThreshold(DEFAULT_CONFIG)

        # Should not raise
        ignited, info = threshold.compute_ignition_signal(
            extero_error=np.array([1.0, 2.0, 1.5]),
            extero_precision=1.5,
            intero_error=np.array([0.5, 0.3]),
            intero_precision=1.0,
            somatic_marker_gain=1.2,
            current_time=100.0,
        )
        assert isinstance(ignited, bool)
        assert "total_signal" in info
        assert "threshold" in info


class TestGlobalWorkspaceValidation:
    """Test validation in GlobalWorkspace."""

    def test_update_invalid_ignition_occurred_type(self) -> None:
        """Test that update rejects non-bool ignition_occurred."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="ignition_occurred must be bool"):
            workspace.update(ignition_occurred="true", dt=1.0)  # type: ignore[arg-type]

    def test_update_invalid_candidate_content_type(self) -> None:
        """Test that update rejects non-array candidate_content."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="candidate_content must be numpy array"):
            workspace.update(ignition_occurred=False, candidate_content=[1.0, 2.0, 3.0], dt=1.0)  # type: ignore[arg-type]

    def test_update_nan_candidate_content(self) -> None:
        """Test that update rejects NaN in candidate_content."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)
        content = np.array([1.0, np.nan, 3.0])

        with pytest.raises(ValueError, match="candidate_content contains NaN or Inf"):
            workspace.update(ignition_occurred=False, candidate_content=content, dt=1.0)

    def test_update_invalid_source_type(self) -> None:
        """Test that update rejects non-string source."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(TypeError, match="source must be str"):
            workspace.update(ignition_occurred=False, source=123, dt=1.0)  # type: ignore[arg-type]

    def test_update_negative_priority(self) -> None:
        """Test that update rejects negative priority."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="priority must be positive"):
            workspace.update(ignition_occurred=False, priority=-1.0, dt=1.0)

    def test_update_negative_dt(self) -> None:
        """Test that update rejects negative dt."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="dt must be positive"):
            workspace.update(ignition_occurred=False, dt=-1.0)

    def test_update_zero_dt(self) -> None:
        """Test that update rejects zero dt."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        with pytest.raises(ValueError, match="dt must be positive"):
            workspace.update(ignition_occurred=False, dt=0.0)

    def test_update_valid_inputs(self) -> None:
        """Test that update accepts valid inputs."""
        workspace = GlobalWorkspace(DEFAULT_CONFIG)

        # Should not raise
        state = workspace.update(
            ignition_occurred=True,
            candidate_content=np.random.randn(256),
            source="visual_cortex",
            priority=1.5,
            dt=1.0,
        )
        assert "state" in state
        assert "is_broadcasting" in state
        assert "is_reportable" in state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
