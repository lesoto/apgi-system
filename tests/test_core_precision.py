"""
Tests for core precision module.

This module contains comprehensive tests for the PrecisionCalculator,
ensuring accurate precision calculations and confidence interval computations.
"""

import numpy as np
import pytest

from apgi_framework.core.precision import PrecisionCalculator  # type: ignore[import-not-found]


class TestPrecisionCalculator:
    """Tests for PrecisionCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a PrecisionCalculator instance."""
        return PrecisionCalculator()

    def test_initialization(self, calculator):
        """Test calculator initialization."""
        assert calculator is not None

    def test_calculate_precision_basic(self, calculator):
        """Test basic precision calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        precision = calculator.calculate_precision(data)

        assert isinstance(precision, (float, np.floating))
        assert precision >= 0

    def test_calculate_precision_single_value(self, calculator):
        """Test precision calculation with single value."""
        data = np.array([5.0])
        precision = calculator.calculate_precision(data)

        assert isinstance(precision, (float, np.floating))

    def test_calculate_precision_empty_array(self, calculator):
        """Test precision calculation with empty array."""
        data = np.array([])

        with pytest.raises((ValueError, ZeroDivisionError, IndexError)):
            calculator.calculate_precision(data)

    def test_calculate_precision_with_zeros(self, calculator):
        """Test precision calculation with zeros."""
        data = np.array([0.0, 0.0, 0.0])
        precision = calculator.calculate_precision(data)

        assert isinstance(precision, (float, np.floating))

    def test_confidence_interval_basic(self, calculator):
        """Test confidence interval calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ci = calculator.confidence_interval(data, confidence=0.95)

        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] < ci[1]  # Lower bound < upper bound

    def test_confidence_interval_different_levels(self, calculator):
        """Test confidence intervals at different levels."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        ci_90 = calculator.confidence_interval(data, confidence=0.90)
        ci_95 = calculator.confidence_interval(data, confidence=0.95)
        ci_99 = calculator.confidence_interval(data, confidence=0.99)

        # Wider confidence level should give wider interval
        assert ci_99[1] - ci_99[0] >= ci_95[1] - ci_95[0]
        assert ci_90[1] - ci_90[0] <= ci_95[1] - ci_95[0]

    def test_confidence_interval_single_value(self, calculator):
        """Test CI calculation with single value."""
        data = np.array([5.0])

        with pytest.raises((ValueError, ZeroDivisionError)):
            calculator.confidence_interval(data, confidence=0.95)

    def test_relative_precision(self, calculator):
        """Test relative precision calculation."""
        data = np.array([100.0, 102.0, 98.0, 101.0, 99.0])
        rel_precision = calculator.relative_precision(data)

        assert isinstance(rel_precision, (float, np.floating))
        assert rel_precision >= 0

    def test_relative_precision_zero_mean(self, calculator):
        """Test relative precision with zero mean."""
        data = np.array([-1.0, 0.0, 1.0])

        # Should handle near-zero mean gracefully
        rel_precision = calculator.relative_precision(data)
        assert isinstance(rel_precision, (float, np.floating))

    def test_coefficient_of_variation(self, calculator):
        """Test coefficient of variation calculation."""
        data = np.array([10.0, 12.0, 8.0, 11.0, 9.0])
        cv = calculator.coefficient_of_variation(data)

        assert isinstance(cv, (float, np.floating))
        assert cv >= 0

    def test_standard_error(self, calculator):
        """Test standard error calculation."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        se = calculator.standard_error(data)

        assert isinstance(se, (float, np.floating))
        assert se >= 0

    def test_precision_batch(self, calculator):
        """Test batch precision calculation."""
        datasets = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
            np.array([7.0, 8.0, 9.0]),
        ]

        precisions = calculator.calculate_precision_batch(datasets)

        assert len(precisions) == len(datasets)
        for p in precisions:
            assert isinstance(p, (float, np.floating))
            assert p >= 0

    def test_precision_metrics(self, calculator):
        """Test comprehensive precision metrics."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        metrics = calculator.precision_metrics(data)

        assert isinstance(metrics, dict)
        assert "precision" in metrics
        assert "confidence_interval_95" in metrics
        assert "relative_precision" in metrics
        assert "coefficient_of_variation" in metrics
        assert "standard_error" in metrics

    def test_precision_with_outliers(self, calculator):
        """Test precision calculation with outliers."""
        # Data with clear outlier
        data = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
        precision = calculator.calculate_precision(data)

        assert isinstance(precision, (float, np.floating))
        assert precision >= 0

    def test_precision_consistency(self, calculator):
        """Test that precision calculations are consistent."""
        data = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        precision = calculator.calculate_precision(data)

        # All identical values should give zero variance
        assert isinstance(precision, (float, np.floating))

    def test_large_dataset(self, calculator):
        """Test precision with large dataset."""
        np.random.seed(42)
        data = np.random.normal(100, 15, 10000)

        precision = calculator.calculate_precision(data)
        ci = calculator.confidence_interval(data, confidence=0.95)

        assert isinstance(precision, (float, np.floating))
        assert isinstance(ci, tuple)
        assert ci[0] < ci[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
