"""
Unit tests for free energy calculations - Coverage Gap Tests.

This test module specifically targets the uncovered lines identified in the
coverage analysis for free_energy.py (Task 4.2).

Coverage gaps addressed:
- Gap 1: Array precision validation (lines 203, 213)
- Gap 2: Shape mismatch validation (lines 235-239)
- Gap 3: Ill-conditioned matrix regularization (lines 424, 426, 441-442)
- Gap 4: Scalar precision in compute_prediction_error (line 520)
- Gap 5: Alternative precision formats in compute_accuracy (lines 613-618)

Requirements validated: 1.2, 1.6
"""

import numpy as np
import pytest

from apgi_framework.core.free_energy import FreeEnergyCalculator


class TestArrayPrecisionValidation:
    """Test array precision validation (Gap 1)."""

    def test_array_precision_with_zero_values(self) -> None:
        """Test that array precision with zero values raises ValueError.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 203
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)

        # Test with zero precision in array
        precision_zero = np.array([1.0, 0.0])

        with pytest.raises(ValueError, match="precision must be positive"):
            calc.compute_variational_free_energy(
                obs, pred, precision_zero, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_array_precision_with_negative_values(self) -> None:
        """Test that array precision with negative values raises ValueError.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 203
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.1])
        posterior_mean = np.array([1.0, 2.0, 3.0])
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.zeros(3)
        prior_cov = np.eye(3)

        # Test with negative precision in array
        precision_neg = np.array([1.0, 2.0, -0.5])

        with pytest.raises(ValueError, match="precision must be positive"):
            calc.compute_variational_free_energy(
                obs, pred, precision_neg, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_array_precision_all_negative(self) -> None:
        """Test that array precision with all negative values raises ValueError.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 203
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1
        prior_mean = np.zeros(2)
        prior_cov = np.eye(2)

        # Test with all negative precision values
        precision_all_neg = np.array([-1.0, -2.0])

        with pytest.raises(ValueError, match="precision must be positive"):
            calc.compute_variational_free_energy(
                obs, pred, precision_all_neg, posterior_mean, posterior_cov, prior_mean, prior_cov
            )


class TestShapeMismatchValidation:
    """Test shape mismatch validation (Gap 2)."""

    def test_posterior_prior_mean_shape_mismatch(self) -> None:
        """Test that mismatched posterior/prior mean shapes raise ValueError.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 235-239
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])
        precision = 1.0

        # Mismatched shapes: posterior is 2D, prior is 3D
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2)
        prior_mean = np.array([0.0, 0.0, 0.0])  # Wrong shape!
        prior_cov = np.eye(3)

        with pytest.raises(ValueError, match="shapes must match"):
            calc.compute_variational_free_energy(
                obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_posterior_prior_mean_shape_mismatch_larger_posterior(self) -> None:
        """Test shape mismatch with larger posterior than prior.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 235-239
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0, 4.0])
        pred = np.array([1.1, 1.9, 3.1, 3.9])
        precision = 1.0

        # Mismatched shapes: posterior is 4D, prior is 2D
        posterior_mean = np.array([1.0, 2.0, 3.0, 4.0])
        posterior_cov = np.eye(4)
        prior_mean = np.array([0.0, 0.0])  # Wrong shape!
        prior_cov = np.eye(2)

        with pytest.raises(ValueError, match="shapes must match"):
            calc.compute_variational_free_energy(
                obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_shape_mismatch_error_message_includes_shapes(self) -> None:
        """Test that error message includes both shapes for debugging.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 235-239
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.1])
        precision = 1.0

        posterior_mean = np.array([1.0, 2.0, 3.0])
        posterior_cov = np.eye(3)
        prior_mean = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        prior_cov = np.eye(5)

        # Check that error message contains shape information
        with pytest.raises(ValueError) as exc_info:
            calc.compute_variational_free_energy(
                obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

        error_msg = str(exc_info.value)
        assert "(3,)" in error_msg or "3" in error_msg
        assert "(5,)" in error_msg or "5" in error_msg


class TestIllConditionedMatrixHandling:
    """Test ill-conditioned matrix regularization (Gap 3)."""

    def test_ill_conditioned_covariance_matrix(self) -> None:
        """Test KL divergence with ill-conditioned covariance matrix.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 424, 426, 441-442
        """
        calc = FreeEnergyCalculator()

        # Create nearly singular matrix with high condition number
        # Two vectors that are almost parallel
        sigma_p = np.array([[1.0, 0.9999999], [0.9999999, 1.0]])
        sigma_q = np.eye(2) * 0.5
        mu_p = np.zeros(2)
        mu_q = np.array([0.1, 0.1])

        # Should handle ill-conditioned matrix gracefully with regularization
        kl_div = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)

        assert np.isfinite(kl_div), "KL divergence should be finite"
        assert kl_div >= 0.0, "KL divergence should be non-negative"

    def test_very_ill_conditioned_matrix(self) -> None:
        """Test with extremely ill-conditioned matrix.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 424, 426, 441-442
        """
        calc = FreeEnergyCalculator()

        # Create matrix with very high condition number
        # Using a matrix that's almost rank-deficient
        epsilon = 1e-14
        sigma_p = np.array([[1.0, 1.0 - epsilon], [1.0 - epsilon, 1.0]])
        sigma_q = np.eye(2) * 0.1
        mu_p = np.array([0.5, 0.5])
        mu_q = np.array([0.6, 0.4])

        # Should apply regularization and return valid result
        kl_div = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)

        assert np.isfinite(kl_div), "KL divergence should be finite with regularization"
        assert kl_div >= 0.0, "KL divergence should be non-negative"
        assert kl_div < 1e10, "KL divergence should not be excessively large"

    def test_ill_conditioned_matrix_in_free_energy(self) -> None:
        """Test ill-conditioned matrix handling in full free energy computation.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 424, 426, 441-442
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])
        precision = 1.0
        posterior_mean = np.array([1.0, 2.0])
        posterior_cov = np.eye(2) * 0.1

        # Prior with ill-conditioned covariance
        prior_mean = np.zeros(2)
        prior_cov = np.array([[1.0, 0.99999999], [0.99999999, 1.0]])

        # Should complete without error
        fe, components = calc.compute_variational_free_energy(
            obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov
        )

        assert np.isfinite(fe), "Free energy should be finite"
        assert fe >= 0.0, "Free energy should be non-negative"
        assert np.isfinite(components["complexity"]), "Complexity should be finite"


class TestScalarPrecisionInPredictionError:
    """Test scalar precision in compute_prediction_error (Gap 4)."""

    def test_compute_prediction_error_with_scalar_precision(self) -> None:
        """Test prediction error computation with scalar precision.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 520
        """
        calc = FreeEnergyCalculator()

        observation = np.array([1.0, 2.0, 3.0])
        prediction = np.array([1.1, 1.9, 3.2])
        precision_scalar = 2.5

        errors = calc.compute_prediction_error(observation, prediction, precision_scalar)

        assert "raw_error" in errors
        assert "weighted_error" in errors
        assert "mean_absolute_error" in errors
        assert "max_error" in errors
        assert "precision_weighted_elements" in errors

        # All errors should be non-negative
        assert errors["raw_error"] >= 0
        assert errors["weighted_error"] >= 0
        assert errors["mean_absolute_error"] >= 0
        assert errors["max_error"] >= 0

        # Weighted error should be scaled by precision
        assert errors["weighted_error"] > 0
        assert np.isfinite(errors["weighted_error"])

    def test_scalar_precision_creates_uniform_weights(self) -> None:
        """Test that scalar precision creates uniform weight array.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 520
        """
        calc = FreeEnergyCalculator()

        observation = np.array([1.0, 2.0, 3.0, 4.0])
        prediction = np.array([1.2, 1.8, 3.1, 3.9])
        precision_scalar = 1.5

        errors = calc.compute_prediction_error(observation, prediction, precision_scalar)

        # Check that precision_weighted_elements are uniformly scaled
        weighted_elements = np.array(errors["precision_weighted_elements"])
        raw_errors = np.abs(observation - prediction)
        expected_weighted = raw_errors * precision_scalar

        np.testing.assert_allclose(weighted_elements, expected_weighted, rtol=1e-10)

    def test_scalar_precision_different_values(self) -> None:
        """Test scalar precision with different values.

        Validates: Requirements 1.2, 1.6
        Coverage: Line 520
        """
        calc = FreeEnergyCalculator()

        observation = np.array([1.0, 2.0])
        prediction = np.array([1.1, 1.9])

        # Test with different scalar precision values
        for precision_val in [0.5, 1.0, 2.0, 5.0]:
            errors = calc.compute_prediction_error(observation, prediction, precision_val)

            assert np.isfinite(errors["weighted_error"])
            assert errors["weighted_error"] >= 0

            # Higher precision should give higher weighted error
            if precision_val > 1.0:
                errors_low = calc.compute_prediction_error(observation, prediction, 1.0)
                assert errors["weighted_error"] >= errors_low["weighted_error"]


class TestAlternativePrecisionFormatsInAccuracy:
    """Test alternative precision formats in compute_accuracy (Gap 5)."""

    def test_compute_accuracy_with_1d_precision_array(self) -> None:
        """Test compute_accuracy with 1D precision array (vector).

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 613-614
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])

        # Test with 1D precision array
        precision_1d = np.array([1.0, 2.0, 1.5])

        acc = calc.compute_accuracy(obs, pred, precision_1d)

        assert isinstance(acc, float)
        assert np.isfinite(acc)
        assert acc >= 0.0

    def test_compute_accuracy_with_2d_precision_matrix(self) -> None:
        """Test compute_accuracy with 2D precision matrix.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 615-618
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])

        # Test with 2D precision matrix (diagonal)
        precision_2d = np.diag([1.0, 2.0, 1.5])

        acc = calc.compute_accuracy(obs, pred, precision_2d)

        assert isinstance(acc, float)
        assert np.isfinite(acc)
        assert acc >= 0.0

    def test_precision_formats_give_equivalent_results(self) -> None:
        """Test that different precision formats give equivalent results.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 613-618
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])

        # Test with 1D array
        precision_1d = np.array([2.0, 2.0, 2.0])
        acc_1d = calc.compute_accuracy(obs, pred, precision_1d)

        # Test with 2D diagonal matrix
        precision_2d = np.diag([2.0, 2.0, 2.0])
        acc_2d = calc.compute_accuracy(obs, pred, precision_2d)

        # Test with scalar
        precision_scalar = 2.0
        acc_scalar = calc.compute_accuracy(obs, pred, precision_scalar)

        # All should give the same result
        np.testing.assert_allclose(acc_1d, acc_2d, rtol=1e-10)
        np.testing.assert_allclose(acc_1d, acc_scalar, rtol=1e-10)

    def test_precision_clamping_in_1d_array(self) -> None:
        """Test precision clamping works correctly for 1D arrays.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 613-614
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.2])

        # Test with very large precision values (should be clamped)
        precision_large = np.array([1e10, 1e10, 1e10])

        acc = calc.compute_accuracy(obs, pred, precision_large)

        # Should be finite due to clamping
        assert np.isfinite(acc)
        assert acc >= 0.0

    def test_precision_clamping_in_2d_matrix(self) -> None:
        """Test precision clamping works correctly for 2D matrices.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 615-618
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])

        # Test with 2D matrix with very large diagonal values
        precision_2d = np.array([[1e10, 0.0], [0.0, 1e10]])

        acc = calc.compute_accuracy(obs, pred, precision_2d)

        # Should be finite due to clamping
        assert np.isfinite(acc)
        assert acc >= 0.0

    def test_2d_precision_matrix_with_off_diagonal_elements(self) -> None:
        """Test 2D precision matrix with off-diagonal elements.

        Validates: Requirements 1.2, 1.6
        Coverage: Lines 615-618
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0])
        pred = np.array([1.1, 1.9])

        # Test with full 2D precision matrix (not just diagonal)
        precision_2d = np.array([[2.0, 0.5], [0.5, 3.0]])

        acc = calc.compute_accuracy(obs, pred, precision_2d)

        assert isinstance(acc, float)
        assert np.isfinite(acc)
        assert acc >= 0.0


class TestEdgeCasesForCoverage:
    """Additional edge case tests to ensure robustness."""

    def test_uniform_beliefs_with_zero_precision_array(self) -> None:
        """Test with uniform beliefs and zero precision in array.

        Validates: Requirements 1.2, 1.6
        """
        calc = FreeEnergyCalculator()

        # Uniform beliefs
        obs = np.ones(3) / 3
        pred = np.ones(3) / 3
        posterior_mean = np.ones(3) / 3
        posterior_cov = np.eye(3) * 0.1
        prior_mean = np.ones(3) / 3
        prior_cov = np.eye(3) * 0.1

        # Zero precision should raise error
        precision_with_zero = np.array([1.0, 0.0, 1.0])

        with pytest.raises(ValueError, match="precision must be positive"):
            calc.compute_variational_free_energy(
                obs, pred, precision_with_zero, posterior_mean, posterior_cov, prior_mean, prior_cov
            )

    def test_energy_minimization_with_various_precision_formats(self) -> None:
        """Test energy minimization logic with various precision formats.

        Validates: Requirements 1.2, 1.6
        """
        calc = FreeEnergyCalculator()

        obs = np.array([1.0, 2.0, 3.0])
        pred = np.array([1.1, 1.9, 3.1])
        posterior_mean = np.array([1.05, 1.95, 3.05])
        posterior_cov = np.eye(3) * 0.05
        prior_mean = np.ones(3)
        prior_cov = np.eye(3) * 0.5

        # Test with different precision formats
        # Note: 2D matrix format is not supported in compute_variational_free_energy
        # Only scalar and 1D array formats are supported
        precisions = [
            1.5,  # scalar
            np.array([1.5, 1.5, 1.5]),  # 1D array
        ]

        free_energies = []
        for precision in precisions:
            fe, _ = calc.compute_variational_free_energy(
                obs, pred, precision, posterior_mean, posterior_cov, prior_mean, prior_cov  # type: ignore[arg-type]
            )
            free_energies.append(fe)

        # All should give similar results
        for fe in free_energies:
            assert np.isfinite(fe)
            assert fe >= 0.0

        # Results should be very close
        np.testing.assert_allclose(free_energies[0], free_energies[1], rtol=1e-10)
