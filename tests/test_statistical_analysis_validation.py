"""Validation tests for statistical analysis utilities.

These tests use small, deterministic synthetic datasets to validate core
statistical computations and error handling.
"""

import numpy as np
import pytest

from apgi_framework.analysis.bayesian_models import SurpriseAccumulator
from apgi_framework.analysis.effect_size_calculator import (
    ConfidenceIntervalMethod,
    EffectSizeCalculator,
)


class TestEffectSizeCalculatorValidation:
    def test_cohens_d_matches_manual_calculation_parametric(self):
        calc = EffectSizeCalculator(random_state=0)

        group1 = np.array([1.0, 2.0, 3.0, 4.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0])

        result = calc.cohens_d(
            group1,
            group2,
            confidence_level=0.95,
            method=ConfidenceIntervalMethod.PARAMETRIC,
        )

        assert np.isclose(result.value, 0.0)
        assert result.confidence_interval[0] <= result.value <= result.confidence_interval[1]

    def test_pearson_r_perfect_correlation(self):
        calc = EffectSizeCalculator(random_state=0)

        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        # Near-perfect (not exact) correlation to avoid arctanh(1.0) warnings
        y = 2.0 * x + 1.0 + np.array([0.0, 0.0, 0.0, 0.0, 1e-6])

        result = calc.pearson_r(x, y, confidence_level=0.95)
        assert result.value > 0.999
        assert result.confidence_interval[0] <= result.value <= result.confidence_interval[1]

    def test_pearson_r_length_mismatch_raises(self):
        calc = EffectSizeCalculator(random_state=0)

        x = np.array([0.0, 1.0, 2.0])
        y = np.array([0.0, 1.0])

        with pytest.raises(ValueError, match="equal length"):
            calc.pearson_r(x, y)


class TestSurpriseAccumulatorValidation:
    def test_weighted_prediction_error_is_sum_of_terms(self):
        acc = SurpriseAccumulator(tau=1.0, dt=0.1)

        pi_e = 2.0
        epsilon_e = -3.0
        pi_i = 4.0
        epsilon_i = 5.0
        beta = 0.5

        weighted = acc.compute_weighted_prediction_error(pi_e, epsilon_e, pi_i, epsilon_i, beta)
        expected = pi_e * abs(epsilon_e) + beta * pi_i * abs(epsilon_i)
        assert np.isclose(weighted, expected)

    def test_integrate_produces_non_negative_trace(self):
        acc = SurpriseAccumulator(tau=1.0, dt=0.1)

        duration = 1.0
        pi_e = np.ones(5)
        epsilon_e = np.zeros(5)
        pi_i = np.ones(5)
        epsilon_i = np.zeros(5)

        trace = acc.integrate(pi_e, epsilon_e, pi_i, epsilon_i, beta=1.0, duration=duration)

        assert len(trace) == int(duration / acc.dt)
        assert np.all(np.isfinite(trace))
        assert np.all(trace >= 0.0)

    def test_integrate_zero_inputs_remains_zero(self):
        acc = SurpriseAccumulator(tau=1.0, dt=0.1)

        duration = 1.0
        pi_e = np.ones(5)
        epsilon_e = np.zeros(5)
        pi_i = np.ones(5)
        epsilon_i = np.zeros(5)

        trace = acc.integrate(pi_e, epsilon_e, pi_i, epsilon_i, beta=0.0, duration=duration)
        assert np.allclose(trace, 0.0)
