"""
Tests for analysis modules.

This module contains comprehensive tests for statistical analysis,
parameter estimation, and effect size calculations.
"""

import pytest
import numpy as np
from apgi_framework.analysis.effect_size_calculator import (
    EffectSizeCalculator,
    EffectSizeResult,
)
from apgi_framework.analysis.statistical_tester import (
    StatisticalTester,
    StatisticalResult,
)


class TestEffectSizeCalculator:
    """Tests for EffectSizeCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create an EffectSizeCalculator instance."""
        return EffectSizeCalculator()

    def test_initialization(self, calculator):
        """Test calculator initialization."""
        assert calculator is not None

    def test_cohens_d(self, calculator):
        """Test Cohen's d calculation."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

        result = calculator.cohens_d(group1, group2)

        assert isinstance(result, EffectSizeResult)
        assert isinstance(result.value, (float, np.floating))
        assert abs(result.value) > 0  # Effect size should be non-zero
        assert result.effect_size_type == "cohens_d"

    def test_hedges_g(self, calculator):
        """Test Hedges' g calculation."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

        result = calculator.hedges_g(group1, group2)

        assert isinstance(result, EffectSizeResult)
        assert isinstance(result.value, (float, np.floating))
        assert abs(result.value) > 0
        assert result.effect_size_type == "hedges_g"

    def test_eta_squared(self, calculator):
        """Test eta squared calculation."""
        group1 = np.random.normal(100, 15, 30)
        group2 = np.random.normal(110, 15, 30)
        group3 = np.random.normal(115, 15, 30)

        # Calculate F-statistic for ANOVA
        from scipy.stats import f_oneway

        f_stat, _ = f_oneway(group1, group2, group3)

        result = calculator.eta_squared((group1, group2, group3), f_stat)

        assert isinstance(result, EffectSizeResult)
        assert 0 <= result.value <= 1
        assert result.effect_size_type == "eta_squared"

    def test_effect_size_interpretation(self, calculator):
        """Test effect size interpretation via cohens_d result."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([10.0, 11.0, 12.0, 13.0, 14.0])

        result = calculator.cohens_d(group1, group2)

        assert isinstance(result, EffectSizeResult)
        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 0


class TestStatisticalTester:
    """Tests for StatisticalTester class."""

    @pytest.fixture
    def tester(self):
        """Create a StatisticalTester instance."""
        return StatisticalTester()

    def test_initialization(self, tester):
        """Test tester initialization."""
        assert tester is not None

    def test_t_test_independent(self, tester):
        """Test independent samples t-test."""
        group1 = np.random.normal(100, 15, 50)
        group2 = np.random.normal(110, 15, 50)

        result = tester.independent_t_test(group1, group2)

        assert isinstance(result, StatisticalResult)
        assert result.statistic is not None
        assert result.p_value is not None
        assert result.degrees_of_freedom is not None

    def test_t_test_paired(self, tester):
        """Test paired samples t-test."""
        before = np.random.normal(100, 15, 50)
        after = before + np.random.normal(5, 5, 50)  # Small increase

        result = tester.paired_t_test(before, after)

        assert isinstance(result, StatisticalResult)
        assert result.statistic is not None
        assert result.p_value is not None

    def test_one_way_anova(self, tester):
        """Test one-way ANOVA."""
        group1 = np.random.normal(100, 15, 30)
        group2 = np.random.normal(105, 15, 30)
        group3 = np.random.normal(110, 15, 30)

        result = tester.one_way_anova(group1, group2, group3)

        assert isinstance(result, StatisticalResult)
        assert result.statistic is not None
        assert result.p_value is not None

    def test_pearson_correlation(self, tester):
        """Test Pearson correlation via EffectSizeCalculator."""
        from apgi_framework.analysis.effect_size_calculator import EffectSizeCalculator

        calc = EffectSizeCalculator()
        x = np.random.normal(100, 15, 100)
        y = x + np.random.normal(0, 5, 100)  # Strong correlation

        result = calc.pearson_r(x, y)

        assert isinstance(result, EffectSizeResult)
        assert -1 <= result.value <= 1
        assert result.effect_size_type == "pearson_r"

    def test_mann_whitney_u(self, tester):
        """Test Mann-Whitney U test."""
        group1 = np.random.normal(100, 15, 30)
        group2 = np.random.normal(110, 15, 30)

        result = tester.mann_whitney_u(group1, group2)

        assert isinstance(result, StatisticalResult)
        assert result.statistic is not None
        assert result.p_value is not None

    def test_wilcoxon_signed_rank(self, tester):
        """Test Wilcoxon signed-rank test."""
        before = np.random.normal(100, 15, 30)
        after = before + np.random.normal(5, 5, 30)

        result = tester.wilcoxon_signed_rank(before, after)

        assert isinstance(result, StatisticalResult)
        assert result.statistic is not None
        assert result.p_value is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
