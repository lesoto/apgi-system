"""
Tests for effect size calculator module coverage.
"""

import numpy as np
import pytest

from apgi_framework.analysis.effect_size_calculator import (
    BootstrapResult,
    ConfidenceIntervalMethod,
    EffectSizeCalculator,
    EffectSizeResult,
    EffectSizeType,
)


class TestEffectSizeCalculator:
    """Test suite for the EffectSizeCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create an EffectSizeCalculator instance."""
        return EffectSizeCalculator(random_state=42)

    def test_cohens_d(self, calculator):
        """Test Cohen's d calculation."""
        group1 = np.random.normal(10, 1, 30)
        group2 = np.random.normal(11, 1, 30)

        result = calculator.cohens_d(group1, group2, method=ConfidenceIntervalMethod.PARAMETRIC)
        assert isinstance(result, EffectSizeResult)
        assert result.effect_size_type == EffectSizeType.COHENS_D.value
        assert result.value < 0  # Group 1 < Group 2
        assert len(result.confidence_interval) == 2

    def test_hedges_g(self, calculator):
        """Test Hedges' g calculation."""
        group1 = np.random.normal(10, 1, 10)
        group2 = np.random.normal(11, 1, 10)

        result = calculator.hedges_g(group1, group2)
        assert result.effect_size_type == EffectSizeType.HEDGES_G.value
        # Hedges' g should be slightly smaller than Cohen's d for small samples
        # But here we just check it runs and produces reasonable output
        assert abs(result.value) > 0

    def test_eta_squared(self, calculator):
        """Test eta-squared calculation."""
        group1 = np.random.normal(10, 1, 20)
        group2 = np.random.normal(11, 1, 20)
        group3 = np.random.normal(12, 1, 20)

        from scipy import stats

        f_stat, _ = stats.f_oneway(group1, group2, group3)

        result = calculator.eta_squared((group1, group2, group3), f_stat)
        assert result.effect_size_type == EffectSizeType.ETA_SQUARED.value
        assert 0 <= result.value <= 1

    def test_omega_squared(self, calculator):
        """Test omega-squared calculation."""
        group1 = np.random.normal(10, 1, 20)
        group2 = np.random.normal(11, 1, 20)
        group3 = np.random.normal(12, 1, 20)

        from scipy import stats

        f_stat, _ = stats.f_oneway(group1, group2, group3)

        result = calculator.omega_squared((group1, group2, group3), f_stat)
        assert result.effect_size_type == EffectSizeType.OMEGA_SQUARED.value
        assert 0 <= result.value <= 1

    def test_pearson_r(self, calculator):
        """Test Pearson correlation."""
        x = np.linspace(0, 10, 50)
        y = 0.5 * x + np.random.normal(0, 1, 50)

        result = calculator.pearson_r(x, y)
        assert result.effect_size_type == EffectSizeType.PEARSON_R.value
        assert 0 < result.value <= 1  # Positive correlation

    def test_bootstrap_confidence_interval(self, calculator):
        """Test bootstrap confidence interval."""
        data = np.random.normal(10, 2, 50)

        def mean_stat(d):
            return np.mean(d)

        result = calculator.bootstrap_confidence_interval(
            data,
            mean_stat,
            n_bootstrap=100,
            method=ConfidenceIntervalMethod.PERCENTILE_BOOTSTRAP,
        )
        assert isinstance(result, BootstrapResult)
        assert result.original_statistic == pytest.approx(np.mean(data))
        assert len(result.confidence_interval) == 2

    def test_interpretations(self, calculator):
        """Test interpretation strings."""
        assert "small" in calculator._interpret_cohens_d(0.3)
        assert "medium" in calculator._interpret_cohens_d(0.6)
        assert "large" in calculator._interpret_cohens_d(0.9)

        assert "small" in calculator._interpret_eta_squared(0.02)
        assert "medium" in calculator._interpret_eta_squared(0.07)
        assert "large" in calculator._interpret_eta_squared(0.15)

        assert "small" in calculator._interpret_correlation(0.15)
        assert "medium" in calculator._interpret_correlation(0.35)
        assert "large" in calculator._interpret_correlation(0.55)

    def test_error_handling(self, calculator):
        """Test error handling in calculator."""
        with pytest.raises(ValueError):
            calculator.cohens_d(np.array([1]), np.array([2]))  # Too few observations

        with pytest.raises(ValueError):
            calculator.pearson_r(np.array([1, 2]), np.array([1, 2, 3]))  # Mismatched lengths
