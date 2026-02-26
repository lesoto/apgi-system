# Coverage Analysis: predictive_processing.py

## Summary

**Module**: `apgi_system/core/predictive_processing.py`  
**Current Coverage**: 90.24%  
**Statements**: 128 total, 9 missed  
**Branches**: 36 total, 7 missed  
**Target**: 100% coverage

## Uncovered Lines

### Line 152: Empty buffer edge case
```python
if len(self.error_buffer) == 0:
    self.accumulated_error = 0.0
```
**Location**: `PredictionErrorChannel._update_accumulated_error()`  
**Gap Type**: Edge case - empty buffer handling  
**Classification**: Untested edge case  
**Priority**: High  
**Test Strategy**: Test `_update_accumulated_error()` when buffer is empty (immediately after initialization or reset)

---

### Line 197: Empty buffer statistics edge case
```python
if len(self.error_buffer) == 0:
    return {"mean_error": 0.0, "std_error": 0.0, "max_error": 0.0, "accumulated": 0.0}
```
**Location**: `PredictionErrorChannel.get_statistics()`  
**Gap Type**: Edge case - empty buffer statistics  
**Classification**: Untested edge case  
**Priority**: High  
**Test Strategy**: Call `get_statistics()` immediately after initialization or reset, before any updates

---

### Line 534: Top-level prediction (no higher level)
```python
else:
    # Top level predicts based on prior
    level["prediction"] = level["state"] * 0.9  # Drift toward zero
```
**Location**: `HierarchicalPredictor._update_hierarchy()`  
**Gap Type**: Untested logic - top level prediction  
**Classification**: Untested logic path  
**Priority**: High  
**Test Strategy**: Test hierarchy update for the top-most level (i == num_levels - 1), verify prediction is computed as state * 0.9

---

### Line 556: Downsample branch in _map_down
```python
else:
    # Downsample
    return state[:target_dim]
```
**Location**: `HierarchicalPredictor._map_down()`  
**Gap Type**: Untested logic - downsampling path  
**Classification**: Untested logic path  
**Priority**: Medium  
**Test Strategy**: Test `_map_down()` with state dimension > target_dim to trigger downsampling

---

### Line 564: Same dimension branch in _map_up
```python
if len(state) == target_dim:
    return state.copy()
```
**Location**: `HierarchicalPredictor._map_up()`  
**Gap Type**: Untested logic - same dimension path  
**Classification**: Untested logic path  
**Priority**: Medium  
**Test Strategy**: Test `_map_up()` with state dimension == target_dim

---

### Line 569: Expand branch in _map_up
```python
else:
    # Expand
    result = np.zeros(target_dim)
    result[: len(state)] = state
    return result
```
**Location**: `HierarchicalPredictor._map_up()`  
**Gap Type**: Untested logic - expansion path  
**Classification**: Untested logic path  
**Priority**: Medium  
**Test Strategy**: Test `_map_up()` with state dimension < target_dim to trigger expansion

---

### Lines 581-583: Empty statistics in get_prediction_errors (partial)
```python
"exteroceptive_stats": self.exteroceptive_channel.get_statistics(),
"interoceptive_stats": self.interoceptive_channel.get_statistics(),
```
**Location**: `HierarchicalPredictor.get_prediction_errors()`  
**Gap Type**: Edge case - statistics retrieval when channels are empty  
**Classification**: Untested edge case  
**Priority**: Low  
**Test Strategy**: Call `get_prediction_errors()` immediately after initialization, before any predictions

---

## Gap Classification Summary

### By Type
- **Untested Logic**: 4 gaps (lines 534, 556, 564, 569)
- **Edge Cases**: 3 gaps (lines 152, 197, 581-583)
- **Error Paths**: 0 gaps
- **Dead Code**: 0 gaps

### By Priority
- **High**: 3 gaps (lines 152, 197, 534)
- **Medium**: 3 gaps (lines 556, 564, 569)
- **Low**: 1 gap (lines 581-583)

## Test Implementation Plan

### Test 1: Empty buffer edge cases (High Priority)
**Target Lines**: 152, 197, 581-583  
**Test Function**: `test_empty_buffer_edge_cases()`  
**Description**: Test behavior when error buffers are empty
```python
def test_empty_buffer_edge_cases():
    """Test prediction error channel with empty buffer."""
    # Test get_statistics() on empty buffer
    # Test get_accumulated_signal() on empty buffer
    # Test get_prediction_errors() before any predictions
```

### Test 2: Top-level hierarchy prediction (High Priority)
**Target Line**: 534  
**Test Function**: `test_top_level_prediction()`  
**Description**: Test that top level predicts based on prior (state * 0.9)
```python
def test_top_level_prediction():
    """Test top-level prediction without higher level."""
    # Create predictor with single level or test top level specifically
    # Verify prediction = state * 0.9 for top level
```

### Test 3: Dimension mapping edge cases (Medium Priority)
**Target Lines**: 556, 564, 569  
**Test Function**: `test_dimension_mapping_all_cases()`  
**Description**: Test all branches of _map_down and _map_up
```python
def test_dimension_mapping_all_cases():
    """Test dimension mapping for all size relationships."""
    # Test _map_down with state > target (downsample)
    # Test _map_up with state == target (same dimension)
    # Test _map_up with state < target (expand)
```

## Coverage Improvement Strategy

1. **Phase 1**: Implement high-priority tests (lines 152, 197, 534)
   - Expected coverage increase: ~4-5%
   - Focus on empty buffer and top-level logic

2. **Phase 2**: Implement medium-priority tests (lines 556, 564, 569)
   - Expected coverage increase: ~3-4%
   - Focus on dimension mapping edge cases

3. **Phase 3**: Verify 100% coverage achieved
   - Run coverage report
   - Confirm all lines and branches covered

## Requirements Validation

This coverage analysis addresses:
- **Requirement 1.4**: Validate all prediction generation, prediction error calculation, and hierarchical processing code paths
- **Requirement 1.8**: Achieve 100% statement coverage for predictive_processing.py

## Notes

- All identified gaps are legitimate code paths that should be tested
- No dead code identified - all uncovered lines serve functional purposes
- Edge cases (empty buffers) are important for robustness
- Dimension mapping cases are critical for hierarchical processing correctness
- Tests should verify both correctness and numerical stability
