# Parameter Validation Features - Visual Guide

## GUI Enhancements

### Before (Without Validation)

```text
┌─────────────────────────────────────┐
│ APGI Parameters                      │
├─────────────────────────────────────┤
│ Exteroceptive Precision: [2.0    ] │
│ Interoceptive Precision: [1.5    ] │
│ Exteroceptive Error:     [1.2    ] │
│ ...                                 │
└─────────────────────────────────────┘
```

### After (With Validation)

```text
┌──────────────────────────────────────────┐
│ APGI Parameters                           │
├──────────────────────────────────────────┤
│ Exteroceptive Precision: [2.0    ] ✓    │  ← Valid indicator
│ Interoceptive Precision: [1.5    ] ✓    │
│ Exteroceptive Error:     [-5.0   ] ✗    │  ← Invalid indicator
│ Interoceptive Error:     [0.8    ] ✓    │
│ Somatic Gain:            [0.2    ] ⚠    │  ← Warning indicator
│ ...                                      │
├──────────────────────────────────────────┤
│ Validation Status                        │
├──────────────────────────────────────────┤
│ ✗ Validation failed                      │
│                                          │
│ ERRORS:                                  │
│   ❌ extero_error: Value -5.0 outside   │
│      valid range [-10.0, 10.0]          │
│                                          │
│ WARNINGS:                                │
│   ⚠️  somatic_gain: Very low gain (0.2) │
│      reduces interoceptive influence    │
└──────────────────────────────────────────┘
```

## Validation Indicators

### ✓ Green Checkmark

- **Meaning**: Parameter is valid and within typical range
- **Action**: No action needed
- **Example**: `extero_precision: 2.0` (typical: 0.5-5.0)

### ⚠ Orange Warning

- **Meaning**: Parameter is valid but unusual
- **Action**: Review parameter choice
- **Example**: `somatic_gain: 0.2` (typical: 0.5-2.0)

### ✗ Red Cross

- **Meaning**: Parameter is invalid
- **Action**: Must correct before proceeding
- **Example**: `threshold: -1.0` (must be positive)

## Tooltip System

### Hover Over Parameter Label

```text
┌─────────────────────────────────────────────┐
│ Exteroceptive Precision: [2.0    ] ✓       │
│  ↑                                          │
│  └─ Hover here                              │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │ Precision of exteroceptive signals   │  │
│  │ Valid range: 0.01 - 10.0             │  │
│  │ Typical values: 0.5 - 5.0            │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Validation Workflow

### Step 1: Enter Parameters

```text
User types: extero_precision = 2.0
            ↓
Real-time validation triggered
            ↓
Indicator updates: ✓
```python

### Step 2: Review Validation Status

```text
┌─────────────────────────────────────┐
│ Validation Status                   │
├─────────────────────────────────────┤
│ ✓ All parameters valid              │
│                                     │
│ SUGGESTIONS:                        │
│   💡 Interoceptive precision is    │
│      1.3x higher than exteroceptive│
└─────────────────────────────────────┘
```

### Step 3: Validate All (Optional)

```text
Click "Validate All" button
            ↓
Comprehensive validation runs
            ↓
Dialog shows results
```

### Step 4: Apply Changes

```text
Click "Apply Changes"
            ↓
Pre-validation check
            ↓
If invalid: Show error dialog
If warnings: Prompt for confirmation
If valid: Save configuration
```python

## Test Execution Validation

### Before Running Test

```text
Click "Run Test"
            ↓
Validate test parameters
            ↓
┌─────────────────────────────────────┐
│ Invalid Parameters                  │
├─────────────────────────────────────┤
│ Test parameters are invalid:        │
│                                     │
│ ERRORS:                             │
│   ❌ n_trials: Value -100 outside  │
│      valid range [1, 100000]       │
│                                     │
│ [OK]                                │
└─────────────────────────────────────┘
            ↓
Test does not run
```

### With Warnings

```text
Click "Run Test"
            ↓
Validate test parameters
            ↓
┌─────────────────────────────────────┐
│ Parameter Warnings                  │
├─────────────────────────────────────┤
│ Test parameters have warnings:      │
│                                     │
│ WARNINGS:                           │
│   ⚠️  Low trial count (30) may     │
│      have insufficient power       │
│                                     │
│ Run test anyway?                    │
│                                     │
│ [Yes]  [No]                         │
└─────────────────────────────────────┘
            ↓
User decides whether to proceed
```

## Validation Messages

### Error Message Format

```text
ERRORS:
  ❌ parameter_name: Value X outside valid range [min, max]. Description
```python

### Warning Message Format

```text
WARNINGS:
  ⚠️  parameter_name: Unusual value (X) - explanation
```python

### Suggestion Message Format

```text
SUGGESTIONS:
  💡 Helpful suggestion about parameter choice or optimization
```

## Parameter Categories

### APGI Equation Parameters (7 parameters)

```text
┌─────────────────────────────────────┐
│ extero_precision    [0.01 - 10.0]  │
│ intero_precision    [0.01 - 10.0]  │
│ extero_error        [-10.0 - 10.0] │
│ intero_error        [-10.0 - 10.0] │
│ somatic_gain        [0.01 - 5.0]   │
│ threshold           [0.1 - 10.0]   │
│ steepness           [0.1 - 10.0]   │
└─────────────────────────────────────┘
```

### Experimental Configuration (10 parameters)

```python
┌─────────────────────────────────────┐
│ n_trials            [1 - 100,000]   │
│ n_participants      [1 - 10,000]    │
│ random_seed         [optional]      │
│ p3b_threshold       [1.0 - 20.0]    │
│ gamma_plv_threshold [0.05 - 0.8]    │
│ bold_z_threshold    [1.0 - 5.0]     │
│ pci_threshold       [0.1 - 0.8]     │
│ alpha_level         [0.001 - 0.1]   │
│ effect_size_thresh  [0.1 - 2.0]     │
│ power_threshold     [0.5 - 0.99]    │
└─────────────────────────────────────┘
```

## Common Scenarios

### Scenario 1: All Valid

```python
Status: ✓ All parameters valid
Action: Proceed with confidence
```python

### Scenario 2: Some Warnings

```python
Status: ⚠ Parameters valid with warnings
Action: Review warnings, decide if intentional
```python

### Scenario 3: Some Errors

```python
Status: ✗ Validation failed
Action: Correct errors before proceeding
```python

### Scenario 4: Mixed Errors and Warnings

```python
Status: ✗ Validation failed
Action: 1. Fix errors first

        2. Then review warnings
        3. Validate again

```python

## Benefits Summary

### For Users

- ✅ Immediate feedback on parameter validity
- ✅ Clear guidance on valid ranges
- ✅ Helpful suggestions for optimization
- ✅ Prevents invalid test execution
- ✅ Reduces trial-and-error

### For Developers

- ✅ Consistent validation across system
- ✅ Reusable validation components
- ✅ Comprehensive error handling
- ✅ Easy to extend with new parameters
- ✅ Well-documented API

### For Research

- ✅ Ensures valid experimental parameters
- ✅ Promotes best practices
- ✅ Reduces experimental errors
- ✅ Improves reproducibility
- ✅ Facilitates parameter exploration

## Quick Reference

### Validation Levels

1. **Real-time**: As you type
2. **On-demand**: Click "Validate All"
3. **Pre-execution**: Before running tests
4. **On-save**: Before applying changes

### Visual Indicators

- ✓ = Valid
- ⚠ = Warning
- ✗ = Error

### Message Types

- ❌ = Error (must fix)
- ⚠️ = Warning (review)
- 💡 = Suggestion (optimize)

### Actions

- Hover = See tooltip
- Type = Real-time validation
- Click "Validate All" = Comprehensive check
- Click "Apply Changes" = Save with validation
- Click "Run Test" = Execute with validation
