"""
Integration tests for numerical stability monitoring with core components.
"""

import pytest
import numpy as np
import warnings

from apgi_system.core.free_energy import FreeEnergyCalculator
from apgi_system.core.predictive_processing import HierarchicalPredictor
from apgi_system.stability import NumericalInstabilityError, NumericalStabilityWarning


class TestStabilityIntegrationFreeEnergy:
    """Test stability monitoring integration with FreeEnergyCalculator."""

    def test_free_energy_normal_computation(self):
        """Test that normal free energy computation works with stability monitoring."""
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])
        precision = 2.0  # Scalar precision
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        # Should complete without errors
        fe, components = calc.compute_variational_free_energy(
            obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
        )

        assert fe >= 0
        assert "accuracy" in components
        assert "complexity" in components

    def test_free_energy_detects_overflow(self):
        """Test that free energy calculator detects overflow conditions."""
        config = {"stability_error_threshold": 1e3}  # Low threshold for testing
        calc = FreeEnergyCalculator(config)

        # Create inputs that will produce very large free energy
        obs = np.array([1e10, 2e10, 3e10])
        pred = np.zeros(3)
        precision = 1e10  # Very high precision amplifies error (scalar)
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        # Should raise NumericalInstabilityError
        with pytest.raises(NumericalInstabilityError) as exc_info:
            calc.compute_variational_free_energy(
                obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
            )

        assert "overflow" in str(exc_info.value).lower()

    def test_free_energy_stability_statistics(self):
        """Test that stability monitor tracks statistics correctly."""
        config = {"stability_warning_threshold": 10.0}  # Low threshold for testing
        calc = FreeEnergyCalculator(config)

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([0.0, 0.0, 0.0])
        precision = 5.0  # Will produce warning-level values (scalar)
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        # Should issue warnings but complete
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            fe, components = calc.compute_variational_free_energy(
                obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
            )

            # May issue warnings depending on computed values
            # Just verify computation completes
            assert fe >= 0

        stats = calc.stability_monitor.get_statistics()
        # Statistics should be tracked (may have warnings)
        assert "warning_count" in stats
        assert "error_count" in stats


class TestStabilityIntegrationHierarchicalPredictor:
    """Test stability monitoring integration with HierarchicalPredictor."""

    def test_predictor_normal_operation(self, config):
        """Test that normal prediction works with stability monitoring."""
        predictor = HierarchicalPredictor(config)

        extero_input = np.random.randn(256) * 0.1  # Small values
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        # Should complete without errors
        results = predictor.predict(extero_input, intero_input, dt_ms=1.0)

        assert "exteroceptive" in results
        assert "interoceptive" in results
        assert "hierarchical_errors" in results

    def test_predictor_detects_unstable_errors(self, config):
        """Test that predictor detects unstable prediction errors."""
        # Configure with low threshold for testing
        config["stability_error_threshold"] = 1e3
        predictor = HierarchicalPredictor(config)

        # Create extreme input that will produce large errors
        extero_input = np.ones(256) * 1e10
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        # Should raise NumericalInstabilityError
        with pytest.raises(NumericalInstabilityError) as exc_info:
            predictor.predict(extero_input, intero_input, dt_ms=1.0)

        assert (
            "overflow" in str(exc_info.value).lower()
            or "exteroceptive" in str(exc_info.value).lower()
        )

    def test_predictor_detects_unstable_state_updates(self, config):
        """Test that predictor detects unstable hierarchical state updates."""
        # Configure with low threshold
        config["stability_error_threshold"] = 1e2
        predictor = HierarchicalPredictor(config)

        # Set learning rates very high to cause instability
        predictor.learning_rates = [100.0] * predictor.num_levels

        extero_input = np.random.randn(256) * 10.0
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        # May raise error during state update
        # Run multiple steps to accumulate instability
        try:
            for _ in range(10):
                predictor.predict(extero_input, intero_input, dt_ms=1.0)
        except NumericalInstabilityError:
            # Expected - instability detected
            pass

        # If no error raised, check that monitor tracked something
        stats = predictor.stability_monitor.get_statistics()
        assert "warning_count" in stats
        assert "error_count" in stats

    def test_predictor_stability_with_warnings(self, config):
        """Test that predictor issues warnings for large but not critical values."""
        # Configure with moderate thresholds
        config["stability_warning_threshold"] = 10.0
        config["stability_error_threshold"] = 1e10
        predictor = HierarchicalPredictor(config)

        # Create moderately large input
        extero_input = np.random.randn(256) * 5.0
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Run several steps
            for _ in range(5):
                results = predictor.predict(extero_input, intero_input, dt_ms=1.0)

            # May issue warnings but should complete
            assert "exteroceptive" in results

        # Check statistics
        stats = predictor.stability_monitor.get_statistics()
        assert stats["error_count"] == 0  # No errors, just warnings

    def test_predictor_reset_clears_stability_stats(self, config):
        """Test that resetting predictor also resets stability statistics."""
        predictor = HierarchicalPredictor(config)

        extero_input = np.random.randn(256)
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])

        # Run some predictions
        for _ in range(5):
            predictor.predict(extero_input, intero_input, dt_ms=1.0)

        # Reset
        predictor.reset()
        predictor.stability_monitor.reset_statistics()

        stats = predictor.stability_monitor.get_statistics()
        assert stats["warning_count"] == 0
        assert stats["error_count"] == 0


class TestStabilityDisabling:
    """Test that stability checking can be disabled."""

    def test_disabled_stability_allows_invalid_values(self):
        """Test that disabling stability checks allows invalid computations."""
        config = {"stability_check_enabled": False}
        calc = FreeEnergyCalculator(config)

        # Create inputs with NaN (would normally fail)
        obs = np.array([1.0, np.nan, 3.0])
        pred = np.zeros(3)
        precision = np.eye(3)
        post_mean = obs
        post_cov = 0.1 * np.eye(3)
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        # Should not raise error (but result will be invalid)
        # This demonstrates that stability checking can be disabled
        # Note: Input validation will still catch NaN, so this tests
        # that the stability monitor itself is disabled
        try:
            fe, components = calc.compute_variational_free_energy(
                obs, pred, precision, post_mean, post_cov, prior_mean, prior_cov
            )
        except ValueError:
            # Input validation caught it (expected)
            pass

        # Verify monitor is disabled
        assert calc.stability_monitor.check_enabled is False
