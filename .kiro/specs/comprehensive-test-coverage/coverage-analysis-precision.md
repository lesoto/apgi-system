# Coverage Analysis: core/precision.py

## Current Coverage: 96.88%

### Missing Lines

1. **Line 257->260**: Branch in `_update_uncertainty` for "intero" stream
   - The else branch that handles interoceptive uncertainty updates
   - Currently only exteroceptive branch is tested

2. **Line 345**: Else branch in `_apply_attention` for neutral attention
   - When attention_target is neither "extero" nor "intero" (should be None)
   - Sets attention_gain to 1.0 (neutral)

3. **Line 400**: Context modulation for task_demand
   - The branch that increases exteroceptive precision when task_demand > 0.5
   - Currently only threat_level context is tested

### Gap Classification

1. **Line 257->260** (intero branch): **Untested Logic**
   - Type: Branch coverage gap
   - Priority: High
   - Fix: Add test that updates intero_error_variance without extero_error_variance

2. **Line 345** (neutral attention): **Untested Logic**
   - Type: Branch coverage gap
   - Priority: Medium
   - Fix: Add test that calls update without attention_target or with None

3. **Line 400** (task_demand context): **Untested Logic**
   - Type: Branch coverage gap
   - Priority: Medium
   - Fix: Add test with context={'task_demand': 0.8}

## Required Tests

### Test 1: Interoceptive-only update
```python
def test_intero_only_update(simple_config):
    """Test updating only interoceptive precision."""
    precision = PrecisionWeighting(simple_config)
    result = precision.update(intero_error_variance=2.0)
    assert result["interoceptive"] > 0
```

### Test 2: Neutral attention (no target)
```python
def test_no_attention_target(simple_config):
    """Test update without attention target."""
    precision = PrecisionWeighting(simple_config)
    result = precision.update(extero_error_variance=1.0)
    assert result["attention_gain"] == 1.0
```

### Test 3: Task demand context
```python
def test_task_demand_context(simple_config):
    """Test task demand context modulation."""
    precision = PrecisionWeighting(simple_config)
    result_low = precision.update(
        extero_error_variance=1.0,
        context={"task_demand": 0.0}
    )
    
    precision = PrecisionWeighting(simple_config)
    result_high = precision.update(
        extero_error_variance=1.0,
        context={"task_demand": 0.8}
    )
    
    assert result_high["exteroceptive"] > result_low["exteroceptive"]
```

## Summary

All gaps are straightforward untested logic branches. No dead code or complex edge cases. Adding 3 targeted tests should achieve 100% coverage.
