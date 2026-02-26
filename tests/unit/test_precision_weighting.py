"""Unit tests for PrecisionWeighting."""

import pytest
import numpy as np
import yaml
from pathlib import Path
from typing import Any

from apgi_system.core.precision import PrecisionWeighting, NeuromodulatorType


@pytest.fixture
def config() -> dict[str, Any]:
    """Load default configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def simple_config() -> dict[str, Any]:
    """Simple test configuration."""
    return {
        "precision": {
            "exteroceptive_baseline": 1.0,
            "interoceptive_baseline": 0.8,
            "attention_gain_range": [0.5, 3.0],
            "volatility_sensitivity": 0.1,
            "neuromodulator_effects": {"norepinephrine": 1.5, "acetylcholine": 1.2},
        },
        "active_inference": {"precision_range": [0.1, 10.0]},
    }


class TestPrecisionWeighting:
    """Test PrecisionWeighting functionality."""

    def test_initialization(self, simple_config: dict[str, Any]) -> None:
        """Test precision weighting initializes correctly."""
        precision = PrecisionWeighting(simple_config)

        assert precision.extero_baseline == 1.0
        assert precision.intero_baseline == 0.8
        assert precision.extero_precision == 1.0
        assert precision.intero_precision == 0.8
        assert precision.attention_focus is None
        assert precision.fatigue_level == 0.0
        assert precision.cognitive_load == 0.0

    def test_update_basic(self, simple_config: dict[str, Any]) -> None:
        """Test basic precision update."""
        precision = PrecisionWeighting(simple_config)

        result = precision.update(extero_error_variance=2.0, intero_error_variance=1.0)

        assert "exteroceptive" in result
        assert "interoceptive" in result
        assert "attention_gain" in result
        assert "fatigue_penalty" in result

        # Precision should be positive
        assert result["exteroceptive"] > 0
        assert result["interoceptive"] > 0

    def test_inverse_relationship_with_variance(self, simple_config: dict[str, Any]) -> None:
        """Test precision inversely correlates with error variance."""
        precision = PrecisionWeighting(simple_config)

        # Low variance should give high precision
        result_low = precision.update(extero_error_variance=0.1)
        precision_low = result_low["exteroceptive"]

        # Reset and test high variance
        precision = PrecisionWeighting(simple_config)
        result_high = precision.update(extero_error_variance=10.0)
        precision_high = result_high["exteroceptive"]

        # Low variance should give higher precision
        assert precision_low > precision_high

    def test_attention_modulation(self, simple_config: dict[str, Any]) -> None:
        """Test attention-based precision modulation."""
        precision = PrecisionWeighting(simple_config)

        # Test exteroceptive attention
        result_extero = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, attention_target="extero"
        )

        # Reset for interoceptive attention
        precision = PrecisionWeighting(simple_config)
        result_intero = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, attention_target="intero"
        )

        # Attended stream should have higher precision
        assert result_extero["exteroceptive"] > result_intero["exteroceptive"]
        assert result_intero["interoceptive"] > result_extero["interoceptive"]

    def test_neuromodulator_effects(self, simple_config: dict[str, Any]) -> None:
        """Test neuromodulator effects on precision."""
        precision = PrecisionWeighting(simple_config)

        # Baseline precision
        baseline_result = precision.update(extero_error_variance=1.0)
        baseline_extero = baseline_result["exteroceptive"]

        # High norepinephrine should increase precision
        precision.set_neuromodulator(NeuromodulatorType.NOREPINEPHRINE, 1.0)
        ne_result = precision.update(extero_error_variance=1.0)
        ne_extero = ne_result["exteroceptive"]

        assert ne_extero > baseline_extero

    def test_fatigue_effects(self, simple_config: dict[str, Any]) -> None:
        """Test fatigue effects on precision."""
        precision = PrecisionWeighting(simple_config)

        # No fatigue
        precision.set_fatigue(0.0)
        result_fresh = precision.update(extero_error_variance=1.0)

        # High fatigue
        precision.set_fatigue(1.0)
        result_tired = precision.update(extero_error_variance=1.0)

        # Fatigue should reduce precision
        assert result_fresh["exteroceptive"] > result_tired["exteroceptive"]

    def test_cognitive_load_effects(self, simple_config: dict[str, Any]) -> None:
        """Test cognitive load effects on precision."""
        precision = PrecisionWeighting(simple_config)

        # Low cognitive load
        precision.set_cognitive_load(0.0)
        result_low_load = precision.update(extero_error_variance=1.0)

        # High cognitive load
        precision.set_cognitive_load(1.0)
        result_high_load = precision.update(extero_error_variance=1.0)

        # High load should reduce precision
        assert result_low_load["exteroceptive"] > result_high_load["exteroceptive"]

    def test_context_modulation(self, simple_config: dict[str, Any]) -> None:
        """Test context-dependent precision modulation."""
        precision = PrecisionWeighting(simple_config)

        # No threat context
        result_safe = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, context={"threat_level": 0.0}
        )

        # High threat context
        precision = PrecisionWeighting(simple_config)
        result_threat = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, context={"threat_level": 0.8}
        )

        # Threat should increase interoceptive precision
        assert result_threat["interoceptive"] > result_safe["interoceptive"]

    def test_precision_bounds(self, simple_config: dict[str, Any]) -> None:
        """Test precision stays within configured bounds."""
        precision = PrecisionWeighting(simple_config)

        # Extreme error variance
        result = precision.update(extero_error_variance=1e6)

        # Should be clamped to valid range
        assert 0.1 <= result["exteroceptive"] <= 10.0
        assert 0.1 <= result["interoceptive"] <= 10.0

    def test_precision_matrix_generation(self, simple_config: dict[str, Any]) -> None:
        """Test precision matrix generation."""
        precision = PrecisionWeighting(simple_config)
        precision.update(extero_error_variance=2.0)

        # Test exteroceptive matrix
        matrix = precision.get_precision_matrix("extero", 16)
        assert matrix.shape == (16, 16)
        assert np.allclose(matrix, matrix.T)  # Should be symmetric
        assert np.all(np.diag(matrix) > 0)  # Diagonal should be positive

        # Test interoceptive matrix
        matrix = precision.get_precision_matrix("intero", 8)
        assert matrix.shape == (8, 8)

    def test_reset(self, simple_config: dict[str, Any]) -> None:
        """Test precision system reset."""
        precision = PrecisionWeighting(simple_config)

        # Modify state
        precision.update(extero_error_variance=5.0, attention_target="extero")
        precision.set_fatigue(0.8)
        precision.set_neuromodulator(NeuromodulatorType.NOREPINEPHRINE, 0.9)

        # Reset
        precision.reset()

        # Should return to baseline
        assert precision.extero_precision == precision.extero_baseline
        assert precision.intero_precision == precision.intero_baseline
        assert precision.attention_focus is None
        assert precision.fatigue_level == 0.0
        assert precision.neuromodulators[NeuromodulatorType.NOREPINEPHRINE] == 0.5

    def test_invalid_error_variance(self, simple_config: dict[str, Any]) -> None:
        """Test error handling for invalid error variance."""
        precision = PrecisionWeighting(simple_config)

        # Negative variance
        with pytest.raises(ValueError):
            precision.update(extero_error_variance=-1.0)

        # NaN variance
        with pytest.raises(ValueError):
            precision.update(extero_error_variance=np.nan)

        # Inf variance
        with pytest.raises(ValueError):
            precision.update(extero_error_variance=np.inf)

    def test_invalid_attention_target(self, simple_config: dict[str, Any]) -> None:
        """Test error handling for invalid attention target."""
        precision = PrecisionWeighting(simple_config)

        with pytest.raises(ValueError):
            precision.update(attention_target="invalid")

    def test_neuromodulator_clamping(self, simple_config: dict[str, Any]) -> None:
        """Test neuromodulator level clamping."""
        precision = PrecisionWeighting(simple_config)

        # Set extreme values
        precision.set_neuromodulator(NeuromodulatorType.NOREPINEPHRINE, -1.0)
        assert precision.neuromodulators[NeuromodulatorType.NOREPINEPHRINE] == 0.0

        precision.set_neuromodulator(NeuromodulatorType.NOREPINEPHRINE, 2.0)
        assert precision.neuromodulators[NeuromodulatorType.NOREPINEPHRINE] == 1.0

    def test_fatigue_clamping(self, simple_config: dict[str, Any]) -> None:
        """Test fatigue level clamping."""
        precision = PrecisionWeighting(simple_config)

        precision.set_fatigue(-0.5)
        assert precision.fatigue_level == 0.0

        precision.set_fatigue(1.5)
        assert precision.fatigue_level == 1.0

    def test_cognitive_load_clamping(self, simple_config: dict[str, Any]) -> None:
        """Test cognitive load clamping."""
        precision = PrecisionWeighting(simple_config)

        precision.set_cognitive_load(-0.5)
        assert precision.cognitive_load == 0.0

        precision.set_cognitive_load(1.5)
        assert precision.cognitive_load == 1.0

    def test_volatility_tracking(self, simple_config: dict[str, Any]) -> None:
        """Test volatility tracking over time."""
        precision = PrecisionWeighting(simple_config)

        # Generate varying error variances
        variances = [1.0, 2.0, 0.5, 3.0, 1.5, 0.8, 2.5]

        for var in variances:
            precision.update(extero_error_variance=var)

        # Volatility should be computed
        assert hasattr(precision, "extero_volatility")
        assert hasattr(precision, "intero_volatility")

    def test_acetylcholine_volatility_interaction(self, simple_config: dict[str, Any]) -> None:
        """Test acetylcholine-volatility interaction."""
        precision = PrecisionWeighting(simple_config)

        # Create high volatility by varying error variance
        variances = [0.1, 5.0, 0.2, 4.8, 0.15, 4.9, 0.12]
        for var in variances:
            precision.update(extero_error_variance=var)

        # Set high acetylcholine
        precision.set_neuromodulator(NeuromodulatorType.ACETYLCHOLINE, 1.0)

        # Update should show ACh effect
        result = precision.update(extero_error_variance=1.0)

        # Should still produce valid precision
        assert result["exteroceptive"] > 0
        assert np.isfinite(result["exteroceptive"])

    def test_boundary_zero_variance(self, simple_config: dict[str, Any]) -> None:
        """Test boundary condition with zero error variance."""
        precision = PrecisionWeighting(simple_config)

        result = precision.update(extero_error_variance=0.0)

        # Should handle zero variance gracefully
        assert result["exteroceptive"] > 0
        assert np.isfinite(result["exteroceptive"])

    def test_boundary_very_small_variance(self, simple_config: dict[str, Any]) -> None:
        """Test boundary condition with very small error variance."""
        precision = PrecisionWeighting(simple_config)

        result = precision.update(extero_error_variance=1e-10)

        # Should produce high but bounded precision
        assert result["exteroceptive"] > 0
        assert result["exteroceptive"] <= 10.0  # Should be clamped

    def test_multiple_updates_consistency(self, simple_config: dict[str, Any]) -> None:
        """Test consistency across multiple updates."""
        precision = PrecisionWeighting(simple_config)

        # Same inputs should give same results
        result1 = precision.update(extero_error_variance=2.0, intero_error_variance=1.5)
        result2 = precision.update(extero_error_variance=2.0, intero_error_variance=1.5)

        # Results should be close (allowing for smoothing effects)
        assert abs(result1["exteroceptive"] - result2["exteroceptive"]) < 0.5
        assert abs(result1["interoceptive"] - result2["interoceptive"]) < 0.5

    def test_intero_only_update(self, simple_config: dict[str, Any]) -> None:
        """Test updating only interoceptive precision without exteroceptive."""
        precision = PrecisionWeighting(simple_config)

        # Update only interoceptive variance
        result = precision.update(intero_error_variance=2.0)

        # Should update interoceptive precision
        assert result["interoceptive"] > 0
        assert result["interoceptive"] != precision.intero_baseline

        # Exteroceptive should remain at baseline (with modulations applied)
        assert result["exteroceptive"] > 0

    def test_no_attention_target(self, simple_config: dict[str, Any]) -> None:
        """Test update without attention target (neutral attention)."""
        precision = PrecisionWeighting(simple_config)

        # Update without attention target
        result = precision.update(extero_error_variance=1.0, intero_error_variance=1.0)

        # Attention gain should be neutral (1.0)
        assert result["attention_gain"] == 1.0
        assert precision.attention_focus is None

    def test_task_demand_context(self, simple_config: dict[str, Any]) -> None:
        """Test task demand context modulation."""
        precision = PrecisionWeighting(simple_config)

        # Low task demand
        result_low = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, context={"task_demand": 0.0}
        )

        # Reset and test high task demand
        precision = PrecisionWeighting(simple_config)
        result_high = precision.update(
            extero_error_variance=1.0, intero_error_variance=1.0, context={"task_demand": 0.8}
        )

        # High task demand should increase exteroceptive precision
        assert result_high["exteroceptive"] > result_low["exteroceptive"]

    def test_apply_attention_else_branch(self, simple_config: dict[str, Any]) -> None:
        """Test the else branch in _apply_attention for neutral attention."""
        precision = PrecisionWeighting(simple_config)

        # Directly call _apply_attention with a value that triggers else branch
        # This tests defensive programming even though it shouldn't happen in normal use
        precision._apply_attention(None)

        # Should set neutral attention gain
        assert precision.attention_gain == 1.0
        assert precision.attention_focus is None
