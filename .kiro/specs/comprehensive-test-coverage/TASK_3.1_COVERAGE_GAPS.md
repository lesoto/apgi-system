# Coverage Gap Analysis: active_inference.py

**Date:** 2025-01-XX  
**Current Coverage:** 87.22%  
**Target Coverage:** 100%  
**Missing Lines:** 20 lines  

## Summary

The active_inference.py module has 87.22% coverage with 20 uncovered lines. Analysis shows these gaps fall into three main categories:

1. **Error handling paths** - Exception handling and edge case validation
2. **Cache management logic** - LRU cache eviction and projection matrix caching
3. **Numerical stability paths** - NaN/Inf handling and fallback computations

## Detailed Gap Analysis

### Gap 1: Shape Mismatch Error Handling (Lines 299, 304)

**Location:** `HierarchicalGaussianFilter._top_down_pass()`

**Code:**
```python
if error_below.shape != belief_shape:
    raise ValueError(
        f"Shape mismatch at level {level}: "
        f"belief mean shape {belief_shape} vs error_below shape {error_below.shape}"
    )
if error_above.shape != belief_shape:
    raise ValueError(
        f"Shape mismatch at level {level}: "
        f"belief mean shape {belief_shape} vs error_above shape {error_above.shape}"
    )
```

**Gap Type:** Error path  
**Classification:** Edge case validation  
**Priority:** High  

**Why Uncovered:** Current tests don't create scenarios where projection operations produce mismatched shapes.

**Test Strategy:** Create a test with mismatched state dimensions that trigger shape validation errors.

---

### Gap 2: Dimension Mismatch Projection (Lines 271, 283)

**Location:** `HierarchicalGaussianFilter._top_down_pass()`

**Code:**
```python
if target_dim != source_dim:
    error_below = self._project_up(level - 1, error_below_raw)
else:
    error_below = error_below_raw
```

**Gap Type:** Untested logic  
**Classification:** Dimension handling branch  
**Priority:** High  

**Why Uncovered:** Tests use uniform dimensions across levels, never triggering projection logic.

**Test Strategy:** Create hierarchical filter with varying dimensions (e.g., [256, 128, 64]) to exercise projection paths.

---

### Gap 3: Cache Eviction Logic (Lines 422-423)

**Location:** `HierarchicalGaussianFilter._get_projection_matrix()`

**Code:**
```python
if len(self._projection_cache) > self._projection_cache_max_size:
    oldest_key = self._cache_access_order.popleft()
    del self._projection_cache[oldest_key]
```

**Gap Type:** Untested logic  
**Classification:** Cache management  
**Priority:** Medium  

**Why Uncovered:** Tests don't create enough projection matrices to fill cache and trigger eviction.

**Test Strategy:** Create filter with small cache size and perform many updates with varying dimensions to trigger eviction.

---

### Gap 4: Same Dimension Projection Matrix (Line 402)

**Location:** `HierarchicalGaussianFilter._get_projection_matrix()`

**Code:**
```python
if target_dim == source_dim:
    projection_matrix = (
        np.eye(target_dim) + np.random.randn(target_dim, source_dim) * 0.01
    )
```

**Gap Type:** Untested logic  
**Classification:** Initialization branch  
**Priority:** Medium  

**Why Uncovered:** Tests use varying dimensions, never hitting same-dimension case.

**Test Strategy:** Create filter with uniform dimensions across all levels.

---

### Gap 5: NaN/Inf Handling in _map_down (Lines 451, 459-461)

**Location:** `HierarchicalGaussianFilter._map_down()`

**Code:**
```python
if not np.all(np.isfinite(projection_matrix)) or not np.all(np.isfinite(state)):
    return np.zeros(target_dim)

try:
    with threading.Lock():
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            result = projection_matrix @ state
except (FloatingPointError, ValueError):
    result = np.zeros(target_dim)
```

**Gap Type:** Error path  
**Classification:** Numerical stability  
**Priority:** High  

**Why Uncovered:** Tests use well-behaved numerical inputs, never triggering NaN/Inf paths.

**Test Strategy:** Inject NaN/Inf values into observations or manually corrupt projection matrices to test fallback paths.

---

### Gap 6: NaN/Inf Handling in _project_up (Lines 478, 496, 504, 512-514)

**Location:** `HierarchicalGaussianFilter._project_up()`

**Code:**
```python
if from_level >= self.num_levels - 1:
    return state

# ... later ...

if np.any(np.abs(projection_matrix) < 1e-10):
    projection_matrix = np.where(
        np.abs(projection_matrix) < 1e-10,
        np.sign(projection_matrix) * 1e-10,
        projection_matrix,
    )

if not np.all(np.isfinite(projection_matrix)) or not np.all(np.isfinite(state)):
    return np.zeros(target_dim)

try:
    with threading.Lock():
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            result = projection_matrix @ state
except (FloatingPointError, ValueError):
    result = np.zeros(target_dim)
```

**Gap Type:** Error path  
**Classification:** Numerical stability and edge cases  
**Priority:** High  

**Why Uncovered:** Tests don't exercise top-level projection or inject problematic numerical values.

**Test Strategy:** 
1. Test projection from top level (should return state unchanged)
2. Inject near-zero values in projection matrix
3. Inject NaN/Inf values to trigger fallback paths

---

### Gap 7: Empty Uncertainty List (Line 803)

**Location:** `ActiveInferenceEngine._select_action()`

**Code:**
```python
if not level_uncertainties:
    level_uncertainties = [0.0]
```

**Gap Type:** Edge case  
**Classification:** Defensive programming  
**Priority:** Low  

**Why Uncovered:** Beliefs always have covariance matrices in tests.

**Test Strategy:** Create scenario with empty beliefs or zero-size covariance matrices.

---

### Gap 8: Zero Planning Horizon (Line 813)

**Location:** `ActiveInferenceEngine._select_action()`

**Code:**
```python
if self.planning_horizon > 0:
    repeats = max(1, (self.planning_horizon + len(level_uncertainties) - 1) // len(level_uncertainties))
    state_uncertainty = np.tile(level_uncertainties, repeats)[:self.planning_horizon]
else:
    state_uncertainty = np.array(level_uncertainties)
```

**Gap Type:** Edge case  
**Classification:** Configuration edge case  
**Priority:** Medium  

**Why Uncovered:** Tests use default planning_horizon > 0.

**Test Strategy:** Create engine with planning_horizon=0 and test action selection.

---

### Gap 9: Custom Horizon in _simulate_future (Lines 826-828)

**Location:** `ActiveInferenceEngine._simulate_future()`

**Code:**
```python
if horizon is None:
    horizon = self.planning_horizon
```

**Gap Type:** Untested logic  
**Classification:** Optional parameter handling  
**Priority:** Low  

**Why Uncovered:** Tests never pass explicit horizon parameter.

**Test Strategy:** Call _simulate_future with explicit horizon parameter (though this is a private method, test via public API if possible).

---

## Gap Classification Summary

| Gap Type | Count | Priority |
|----------|-------|----------|
| Error paths | 8 | High |
| Untested logic | 6 | Medium-High |
| Edge cases | 6 | Medium-Low |

## Recommended Test Implementation Order

1. **High Priority - Dimension Handling (Lines 271, 283, 299, 304)**
   - Create tests with varying dimensions across hierarchy levels
   - Test shape mismatch error conditions

2. **High Priority - Numerical Stability (Lines 451, 459-461, 478, 496, 504, 512-514)**
   - Test NaN/Inf injection and fallback paths
   - Test near-zero projection matrix values
   - Test top-level projection edge case

3. **Medium Priority - Cache Management (Lines 402, 422-423)**
   - Test cache eviction with small cache size
   - Test same-dimension projection matrix creation

4. **Low Priority - Configuration Edge Cases (Lines 803, 813, 826-828)**
   - Test zero planning horizon
   - Test empty uncertainty lists
   - Test custom horizon parameter

## Test Files to Update

- `tests/unit/test_active_inference.py` - Add new test cases for uncovered paths

## Estimated Effort

- **Test Implementation:** 2-3 hours
- **Verification:** 30 minutes
- **Total:** 2.5-3.5 hours

## Requirements Validated

- **Requirement 1.1:** Belief updating, policy selection, and action execution code paths
- **Requirement 1.5:** 100% statement coverage for active_inference.py
