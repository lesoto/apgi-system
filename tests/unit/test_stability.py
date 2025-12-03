"""
Unit tests for numerical stability monitoring.
"""

import pytest
import numpy as np
import warnings

from apgi_system.stability import (
    NumericalStabilityMonitor,
    NumericalInstabilityError,
    NumericalStabilityWarning,
)


class TestNumericalStabilityMonitor:
    """Test suite for NumericalStabilityMonitor."""

    def test_initialization_default(self):
        """Test monitor initialization with default config."""
        monitor = NumericalStabilityMonitor()

        assert monitor.warning_threshold == 1e10
        assert monitor.error_threshold == 1e15
        assert monitor.underflow_threshold == 1e-10
        assert monitor.check_enabled is True
        assert monitor.warning_count == 0
        assert monitor.error_count == 0

    def test_initialization_custom_config(self):
        """Test monitor initialization with custom config."""
        config = {
            "stability_warning_threshold": 1e8,
            "stability_error_threshold": 1e12,
            "stability_underflow_threshold": 1e-8,
            "stability_check_enabled": False,
        }
        monitor = NumericalStabilityMonitor(config)

        assert monitor.warning_threshold == 1e8
        assert monitor.error_threshold == 1e12
        assert monitor.underflow_threshold == 1e-8
        assert monitor.check_enabled is False

    def test_check_stability_valid_scalar(self):
        """Test stability check with valid scalar value."""
        monitor = NumericalStabilityMonitor()
        value = 100.0

        status = monitor.check_stability(value, context="test")

        assert status["stable"] is True
        assert status["has_nan"] is False
        assert status["has_inf"] is False
        assert status["max_abs_value"] == 100.0
        assert status["warning_issued"] is False
        assert status["error_detected"] is False

    def test_check_stability_valid_array(self):
        """Test stability check with valid array."""
        monitor = NumericalStabilityMonitor()
        values = np.array([1.0, 2.0, 3.0, -4.0])

        status = monitor.check_stability(values, context="test")

        assert status["stable"] is True
        assert status["has_nan"] is False
        assert status["has_inf"] is False
        assert status["max_abs_value"] == 4.0
        assert status["warning_issued"] is False
        assert status["error_detected"] is False

    def test_check_stability_nan_detection(self):
        """Test detection of NaN values."""
        monitor = NumericalStabilityMonitor()
        values = np.array([1.0, np.nan, 3.0])

        with pytest.raises(NumericalInstabilityError) as exc_info:
            monitor.check_stability(values, context="nan_test")

        assert "NaN detected" in str(exc_info.value)
        assert "nan_test" in str(exc_info.value)
        assert monitor.error_count == 1

    def test_check_stability_inf_detection(self):
        """Test detection of Inf values."""
        monitor = NumericalStabilityMonitor()
        values = np.array([1.0, np.inf, 3.0])

        with pytest.raises(NumericalInstabilityError) as exc_info:
            monitor.check_stability(values, context="inf_test")

        assert "Inf detected" in str(exc_info.value)
        assert "inf_test" in str(exc_info.value)
        assert monitor.error_count == 1

    def test_check_stability_negative_inf_detection(self):
        """Test detection of negative Inf values."""
        monitor = NumericalStabilityMonitor()
        values = np.array([1.0, -np.inf, 3.0])

        with pytest.raises(NumericalInstabilityError) as exc_info:
            monitor.check_stability(values, context="neg_inf_test")

        assert "Inf detected" in str(exc_info.value)
        assert monitor.error_count == 1

    def test_check_stability_overflow_detection(self):
        """Test detection of overflow (values exceeding error threshold)."""
        monitor = NumericalStabilityMonitor()
        values = np.array([1e16, 2e16])  # Exceeds default error threshold of 1e15

        with pytest.raises(NumericalInstabilityError) as exc_info:
            monitor.check_stability(values, context="overflow_test")

        assert "overflow" in str(exc_info.value).lower()
        assert "overflow_test" in str(exc_info.value)
        assert monitor.error_count == 1

    def test_check_stability_warning_threshold(self):
        """Test warning issued when values exceed warning threshold."""
        monitor = NumericalStabilityMonitor()
        values = np.array([5e10, 6e10])  # Exceeds warning threshold but not error

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            status = monitor.check_stability(values, context="warning_test")

            assert len(w) == 1
            assert issubclass(w[0].category, NumericalStabilityWarning)
            assert "Large values detected" in str(w[0].message)
            assert "warning_test" in str(w[0].message)

        assert status["stable"] is True
        assert status["warning_issued"] is True
        assert status["error_detected"] is False
        assert monitor.warning_count == 1

    def test_check_stability_disabled(self):
        """Test that checking can be disabled."""
        config = {"stability_check_enabled": False}
        monitor = NumericalStabilityMonitor(config)
        values = np.array([np.nan, np.inf, 1e20])  # Would normally fail

        status = monitor.check_stability(values, context="disabled_test")

        # Should return stable status without checking
        assert status["stable"] is True
        assert status["has_nan"] is False
        assert status["has_inf"] is False
        assert monitor.error_count == 0

    def test_check_stability_no_raise_on_error(self):
        """Test that errors can be detected without raising exception."""
        monitor = NumericalStabilityMonitor()
        values = np.array([np.nan])

        status = monitor.check_stability(values, context="no_raise_test", raise_on_error=False)

        assert status["stable"] is False
        assert status["has_nan"] is True
        assert status["error_detected"] is True
        assert monitor.error_count == 1

    def test_check_array_properties_valid(self):
        """Test array property checking with valid array."""
        monitor = NumericalStabilityMonitor()
        array = np.array([[1.0, 2.0], [3.0, 4.0]])

        status = monitor.check_array_properties(
            array, context="array_test", expected_shape=(2, 2), expected_range=(0.0, 10.0)
        )

        assert status["stable"] is True
        assert status["shape_valid"] is True
        assert status["range_valid"] is True
        assert status["actual_shape"] == (2, 2)
        assert status["actual_range"] == (1.0, 4.0)

    def test_check_array_properties_shape_mismatch(self):
        """Test array property checking with shape mismatch."""
        monitor = NumericalStabilityMonitor()
        array = np.array([[1.0, 2.0], [3.0, 4.0]])

        with pytest.raises(ValueError) as exc_info:
            monitor.check_array_properties(array, context="shape_test", expected_shape=(3, 2))

        assert "shape mismatch" in str(exc_info.value)
        assert "expected (3, 2)" in str(exc_info.value)
        assert "got (2, 2)" in str(exc_info.value)

    def test_check_array_properties_range_violation(self):
        """Test array property checking with range violation."""
        monitor = NumericalStabilityMonitor()
        array = np.array([1.0, 2.0, 15.0])  # 15.0 exceeds range

        with pytest.raises(ValueError) as exc_info:
            monitor.check_array_properties(array, context="range_test", expected_range=(0.0, 10.0))

        assert "range violation" in str(exc_info.value)
        assert "expected [0.0, 10.0]" in str(exc_info.value)

    def test_get_statistics(self):
        """Test retrieval of monitoring statistics."""
        monitor = NumericalStabilityMonitor()

        # Trigger some warnings and errors
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            monitor.check_stability(5e10, context="test1")  # Warning

        try:
            monitor.check_stability(np.nan, context="test2")  # Error
        except NumericalInstabilityError:
            pass

        stats = monitor.get_statistics()

        assert stats["warning_count"] == 1
        assert stats["error_count"] == 1

    def test_reset_statistics(self):
        """Test resetting of monitoring statistics."""
        monitor = NumericalStabilityMonitor()

        # Trigger some warnings and errors
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            monitor.check_stability(5e10, context="test1")

        try:
            monitor.check_stability(np.nan, context="test2")
        except NumericalInstabilityError:
            pass

        # Reset
        monitor.reset_statistics()
        stats = monitor.get_statistics()

        assert stats["warning_count"] == 0
        assert stats["error_count"] == 0

    def test_custom_exception_attributes(self):
        """Test custom exception attributes."""
        error = NumericalInstabilityError("Test error", context="test_context", value=1e20)

        assert error.message == "Test error"
        assert error.context == "test_context"
        assert error.value == 1e20
        assert "test_context" in str(error)
        assert "Test error" in str(error)

    def test_multiple_checks_accumulate_stats(self):
        """Test that multiple checks accumulate statistics correctly."""
        monitor = NumericalStabilityMonitor()

        # Multiple warnings
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            monitor.check_stability(5e10, context="test1")
            monitor.check_stability(6e10, context="test2")
            monitor.check_stability(7e10, context="test3")

        stats = monitor.get_statistics()
        assert stats["warning_count"] == 3

    def test_edge_case_exactly_at_threshold(self):
        """Test behavior when value is exactly at threshold."""
        config = {"stability_warning_threshold": 100.0}
        monitor = NumericalStabilityMonitor(config)

        # Exactly at threshold should trigger warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            status = monitor.check_stability(100.1, context="threshold_test")

            assert len(w) == 1
            assert status["warning_issued"] is True

    def test_negative_values_handled_correctly(self):
        """Test that negative values are handled using absolute value."""
        monitor = NumericalStabilityMonitor()
        values = np.array([-5e10, -6e10])  # Large negative values

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            status = monitor.check_stability(values, context="negative_test")

            assert len(w) == 1
            assert status["max_abs_value"] == 6e10
            assert status["warning_issued"] is True
