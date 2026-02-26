# Coverage Analysis: free_energy.py

**Date:** 2025-01-XX  
**Module:** `apgi_system/core/free_energy.py`  
**Current Coverage:** 85.96%  
**Target Coverage:** 100%  
**Missing Lines:** 15 statements, 8 partial branches

## Summary

The `free_energy.py` module has good test coverage at 85.96%, but there are specific edge cases and error paths that remain untested. The gaps fall into three main categories:

1. **Error validation paths** - Input validation for array precision
2. **Edge case handling** - Ill-conditioned matrix regularization
3. **Alternative code paths** - Different precision format handling

## Detailed Gap Analysis

### Gap 1: Array Precision Validation (Lines 203, 213)

**Location:** `compute_variational_free_energy()` method  
**Code:**
```python
if np.any(precision <= 0):
    raise ValueError("precision must be positive")
```

**Gap Type:** Error Path - Input Validation  
**Classification:** Untested error handling  
**Priority:** High  

**Description:**  
When precision is provided as an array (not scalar), the code validates that all precision values are positive. This validation path is not covered by existing tests.

**Test Needed:**  
- Test with array precision containing zero values
- Test with array precision containing negative values
- Verify appropriate ValueError is raised with correct message

---

### Gap 2: Shape Mismatch Validation (Lines 235-239)

**Location:** `compute_variational_free_energy()` method  
**Code:**
```python
if posterior_mean.shape != prior_mean.shape:
    raise ValueError(
        f"posterior_mean and prior_mean shapes must match: "
        f"got {posterior_mean.shape} and {prior_mean.shape}"
    )
```

**Gap Type:** Error Path - Input Validation  
**Classification:** Untested error handling  
**Priority:** High  

**Description:**  
Validates that posterior and prior means have matching shapes. This error path is not exercised by current tests.

**Test Needed:**  
- Test with mismatched posterior_mean and prior_mean shapes
- Verify ValueError is raised with descriptive message showing both shapes

---

### Gap 3: Ill-Conditioned Matrix Regularization (Lines 424, 426, 441-442)

**Location:** `_kl_divergence_gaussian()` method  
**Code:**
```python
cond_num = np.linalg.cond(sigma_p)
if cond_num > 1e12:
    # Matrix is ill-conditioned, use regularization
    sigma_p_reg = sigma_p + 1e-6 * np.eye(d)
    sigma_p_inv = linalg.pinv(sigma_p_reg)
```

**Gap Type:** Edge Case - Numerical Stability  
**Classification:** Untested edge case handling  
**Priority:** Medium  

**Description:**  
When computing KL divergence, the code checks if the prior covariance matrix is ill-conditioned (condition number > 1e12) and applies regularization. This numerical stability path is not tested.

**Test Needed:**  
- Create a nearly singular covariance matrix with high condition number
- Verify regularization is applied correctly
- Ensure KL divergence computation completes without error

---

### Gap 4: Scalar Precision in compute_prediction_error (Line 520)

**Location:** `compute_prediction_error()` method  
**Code:**
```python
elif np.isscalar(precision):
    precision_weights = float(precision) * np.ones_like(error)
```

**Gap Type:** Alternative Code Path  
**Classification:** Untested logic branch  
**Priority:** Low  

**Description:**  
When precision is provided as a scalar to `compute_prediction_error()`, it's converted to a weight array. This branch is not covered.

**Test Needed:**  
- Test `compute_prediction_error()` with scalar precision value
- Verify correct weight array is created
- Check error metrics are computed correctly

---

### Gap 5: Alternative Precision Formats in compute_accuracy (Lines 613-618)

**Location:** `compute_accuracy()` method  
**Code:**
```python
elif hasattr(precision, "ndim") and precision.ndim == 1:
    precision_clipped = np.clip(precision, self.precision_min, self.precision_max)
    precision_matrix = np.diag(precision_clipped)
else:
    precision_matrix = np.asarray(precision).copy()
    np.fill_diagonal(
        precision_matrix,
        np.clip(np.diag(precision_matrix), self.precision_min, self.precision_max),
    )
```

**Gap Type:** Alternative Code Path  
**Classification:** Untested logic branches  
**Priority:** Medium  

**Description:**  
The `compute_accuracy()` method handles three precision formats: scalar, 1D array, and 2D matrix. The 1D array and 2D matrix branches are not fully covered.

**Test Needed:**  
- Test with 1D precision array (vector)
- Test with 2D precision matrix
- Verify precision clamping works correctly for each format
- Check accuracy calculation is correct for all formats

---

## Coverage Gap Summary by Type

| Gap Type | Count | Priority | Lines |
|----------|-------|----------|-------|
| Error Path - Input Validation | 2 | High | 203, 213, 235-239 |
| Edge Case - Numerical Stability | 1 | Medium | 424, 426, 441-442 |
| Alternative Code Path | 2 | Low-Medium | 520, 613-618 |

## Recommendations

### Immediate Actions (High Priority)
1. Add tests for array precision validation (negative/zero values)
2. Add tests for shape mismatch between posterior and prior

### Short-term Actions (Medium Priority)
3. Add tests for ill-conditioned matrix handling in KL divergence
4. Add tests for alternative precision formats in `compute_accuracy()`

### Nice-to-have (Low Priority)
5. Add tests for scalar precision in `compute_prediction_error()`

## Test Implementation Strategy

### Test 1: Invalid Array Precision
```python
def test_array_precision_validation():
    """Test that array precision with invalid values raises ValueError."""
    calc = FreeEnergyCalculator()
    obs = np.array([1.0, 2.0])
    pred = np.array([1.1, 1.9])
    
    # Test with zero precision
    precision_zero = np.array([1.0, 0.0])
    with pytest.raises(ValueError, match="precision must be positive"):
        calc.compute_variational_free_energy(
            obs, pred, precision_zero, obs, np.eye(2), np.zeros(2), np.eye(2)
        )
    
    # Test with negative precision
    precision_neg = np.array([1.0, -0.5])
    with pytest.raises(ValueError, match="precision must be positive"):
        calc.compute_variational_free_energy(
            obs, pred, precision_neg, obs, np.eye(2), np.zeros(2), np.eye(2)
        )
```

### Test 2: Shape Mismatch
```python
def test_posterior_prior_shape_mismatch():
    """Test that mismatched posterior/prior shapes raise ValueError."""
    calc = FreeEnergyCalculator()
    obs = np.array([1.0, 2.0])
    pred = np.array([1.1, 1.9])
    precision = 1.0
    
    posterior_mean = np.array([1.0, 2.0])
    posterior_cov = np.eye(2)
    prior_mean = np.array([0.0, 0.0, 0.0])  # Wrong shape!
    prior_cov = np.eye(3)
    
    with pytest.raises(ValueError, match="shapes must match"):
        calc.compute_variational_free_energy(
            obs, pred, precision, posterior_mean, posterior_cov, 
            prior_mean, prior_cov
        )
```

### Test 3: Ill-Conditioned Matrix
```python
def test_ill_conditioned_covariance():
    """Test KL divergence with ill-conditioned covariance matrix."""
    calc = FreeEnergyCalculator()
    
    # Create nearly singular matrix with high condition number
    sigma_p = np.array([[1.0, 0.9999999], [0.9999999, 1.0]])
    sigma_q = np.eye(2) * 0.5
    mu_p = np.zeros(2)
    mu_q = np.array([0.1, 0.1])
    
    # Should handle ill-conditioned matrix gracefully
    kl_div = calc._kl_divergence_gaussian(mu_q, sigma_q, mu_p, sigma_p)
    
    assert np.isfinite(kl_div)
    assert kl_div >= 0.0
```

### Test 4: Alternative Precision Formats
```python
def test_compute_accuracy_precision_formats():
    """Test compute_accuracy with different precision formats."""
    calc = FreeEnergyCalculator()
    obs = np.array([1.0, 2.0, 3.0])
    pred = np.array([1.1, 1.9, 3.2])
    
    # Test with 1D precision array
    precision_1d = np.array([1.0, 2.0, 1.5])
    acc_1d = calc.compute_accuracy(obs, pred, precision_1d)
    assert np.isfinite(acc_1d)
    assert acc_1d >= 0.0
    
    # Test with 2D precision matrix
    precision_2d = np.diag([1.0, 2.0, 1.5])
    acc_2d = calc.compute_accuracy(obs, pred, precision_2d)
    assert np.isfinite(acc_2d)
    assert acc_2d >= 0.0
```

## Notes

- All gaps are in error handling or edge case paths, not core functionality
- Core free energy calculations are well-tested (main paths have 100% coverage)
- Missing coverage is primarily defensive programming and robustness checks
- No dead code identified - all uncovered lines serve a purpose

## Validation Requirements

To achieve 100% coverage for `free_energy.py`:
- Requirements 1.2: Free energy calculations ✓ (core paths covered)
- Requirements 1.6: 100% statement coverage (needs 5 additional tests)
- Requirements 13.1: Property tests for free energy (separate task 4.3, 4.4)
- Requirements 14.2: Invalid input rejection (gaps 1, 2)
- Requirements 14.3: Boundary value handling (gap 3)
