# APGI Framework GUI - Visual Guide

A visual walkthrough of the APGI Framework Testing System GUI.

## Table of Contents

1. [Main Window Layout](#main-window-layout)
2. [Test Selection Panel](#test-selection-panel)
3. [Parameter Configuration](#parameter-configuration)
4. [Running Tests](#running-tests)
5. [Viewing Results](#viewing-results)
6. [Menu Bar Functions](#menu-bar-functions)

## Main Window Layout

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ File   Edit   View   Tools   Help                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────────────┐  ┌────────────────────┐   │
│  │              │  │                      │  │                    │   │
│  │     Test     │  │     Parameter        │  │      Results       │   │
│  │  Selection   │  │   Configuration      │  │       Display       │   │
│  │    Panel     │  │       Panel          │  │       Panel        │   │
│  │              │  │                      │  │                    │   │
│  │  [Primary]   │  │  Extero Precision:   │  │  Falsification     │   │
│  │              │  │  [2.0        ]       │  │  Status:           │   │
│  │  [Conscious  │  │                      │  │  NOT FALSIFIED     │   │
│  │   w/o Ign.]  │  │  Intero Precision:   │  │                    │   │
│  │              │  │  [1.5        ]       │  │  Confidence: 0.87  │   │
│  │  [Threshold  │  │                      │  │  P-value: 0.002    │   │
│  │   Insens.]   │  │  Threshold:          │  │  Effect: 0.62      │   │
│  │              │  │  [3.5        ]       │  │  Power: 0.85       │   │
│  │  [Soma-Bias] │  │                      │  │                    │   │
│  │              │  │  Steepness:          │  │  [Visualization]   │   │
│  │              │  │  [2.0        ]       │  │                    │   │
│  │              │  │                      │  │  ┌──────────────┐  │   │
│  │              │  │  Somatic Gain:       │  │  │   Plot Area  │  │   │
│  │              │  │  [1.3        ]       │  │  │              │  │   │
│  │              │  │                      │  │  │              │  │   │
│  │              │  │  Trials: [1000  ]    │  │  │              │  │   │
│  │              │  │  Seed:   [42    ]    │  │  └──────────────┘  │   │
│  │              │  │                      │  │                    │   │
│  │              │  │  [  Run Test  ]      │  │  [Export Results]  │   │
│  └──────────────┘  └──────────────────────┘  └────────────────────┘   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Progress: [████████████████████████████████████] 100%          │    │
│  │ Status: Test completed successfully                            │    │
│  │ Time: 45.2 seconds                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Test Selection Panel

The left panel contains buttons for each falsification test type.

```text
┌──────────────────────┐
│   Test Selection     │
├──────────────────────┤
│                      │
│  ┌────────────────┐  │
│  │   Primary      │  │  ← Click to select primary falsification test
│  │ Falsification  │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │ Consciousness  │  │  ← Test consciousness without ignition
│  │ Without Ign.   │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │   Threshold    │  │  ← Test neuromodulatory effects
│  │ Insensitivity  │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │   Soma-Bias    │  │  ← Test interoceptive bias
│  │      Test      │  │
│  └────────────────┘  │
│                      │
└──────────────────────┘
```

### Button States

**Normal State:**

```python
┌────────────────┐
│   Primary      │
│ Falsification  │
└────────────────┘
```

## Parameter Configuration

The center panel allows you to configure APGI parameters and experimental settings.

```text
┌─────────────────────────────────┐
│   Parameter Configuration       │
├─────────────────────────────────┤
│                                 │
│  APGI Parameters                 │
│  ───────────────                │
│                                 │
│  Exteroceptive Precision:       │
│  ┌─────────────┐  [i]          │  ← Hover [i] for tooltip
│  │ 2.0         │                │
│  └─────────────┘                │
│  Range: 0.1 - 10.0              │
│                                 │
│  Interoceptive Precision:       │
│  ┌─────────────┐  [i]          │
│  │ 1.5         │                │
│  └─────────────┘                │
│  Range: 0.1 - 10.0              │
│                                 │
│  Ignition Threshold:            │
│  ┌─────────────┐  [i]          │
│  │ 3.5         │                │
│  └─────────────┘                │
│  Range: 0.5 - 10.0              │
│                                 │
│  Sigmoid Steepness:             │
│  ┌─────────────┐  [i]          │
│  │ 2.0         │                │
│  └─────────────┘                │
│  Range: 0.1 - 5.0               │
│                                 │
│  Somatic Marker Gain:           │
│  ┌─────────────┐  [i]          │
│  │ 1.3         │                │
│  └─────────────┘                │
│  Range: 0.1 - 5.0               │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  Experimental Settings          │
│  ──────────────────             │
│                                 │
│  Number of Trials:              │
│  ┌─────────────┐               │
│  │ 1000        │                │
│  └─────────────┘                │
│  Range: 100 - 10000             │
│                                 │
│  Random Seed (optional):        │
│  ┌─────────────┐               │
│  │ 42          │                │
│  └─────────────┘                │
│  Leave empty for random         │
│                                 │
│  ┌───────────────────────────┐ │
│  │      Run Test             │ │  ← Click to start test
│  └───────────────────────────┘ │
│                                 │
└─────────────────────────────────┘
```

### Parameter Tooltips

When hovering over [i] icons:

```text
┌─────────────────────────────────────┐
│ Exteroceptive Precision             │
│                                     │
│ Precision (inverse variance) of     │
│ external sensory prediction errors. │
│                                     │
│ Higher values = more reliable       │
│ external signals                    │
│                                     │
│ Default: 2.0                        │
│ Range: 0.1 - 10.0                   │
└─────────────────────────────────────┘
```

### Validation Feedback

**Valid Input:**

```python
Threshold:
┌─────────────┐
│ 3.5         │  ← Normal border
└─────────────┘
```

**Invalid Input:**

```python
Threshold:
┌═════════════┐
│ 15.0        │  ← Red border
└═════════════┘
⚠ Value must be between 0.5 and 10.0
```

## Running Tests

### Before Test Starts

```python
┌───────────────────────────────┐
│      Run Test                 │  ← Enabled button
└───────────────────────────────┘

Progress: [                    ] 0%
Status: Ready to run test
```

### During Test Execution

```python
┌───────────────────────────────┐
│      Running...               │  ← Disabled button
└───────────────────────────────┘

Progress: [████████          ] 45%
Status: Processing trial 450/1000
Time elapsed: 22.5 seconds
```

### Test Completed

```python
┌───────────────────────────────┐
│      Run Test                 │  ← Re-enabled button
└───────────────────────────────┘

Progress: [████████████████████] 100%
Status: Test completed successfully
Time: 45.2 seconds
```

### Progress Panel States

**Idle:**

```python
┌────────────────────────────────┐
│ Progress: [                    ] 0%    │
│ Status: Ready                          │
└────────────────────────────────┘
```

**Running:**

```python
┌────────────────────────────────┐
│ Progress: [████████          ] 45%     │
│ Status: Processing trial 450/1000      │
│ Time elapsed: 22.5 seconds             │
└────────────────────────────────┘
```

**Completed:**

```python
┌────────────────────────────────┐
│ Progress: [████████████████████] 100%  │
│ Status: ✓ Test completed successfully  │
│ Total time: 45.2 seconds               │
└────────────────────────────────┘
```

**Error:**

```python
┌────────────────────────────────┐
│ Progress: [████████          ] 45%     │
│ Status: ✗ Error: Invalid parameter     │
│ See log for details                    │
└────────────────────────────────┘
```

## Viewing Results

The right panel displays test results and visualizations.

```text
┌─────────────────────────────────────┐
│         Results Display             │
├─────────────────────────────────────┤
│                                     │
│  Test: Primary Falsification        │
│  Date: 2025-01-07 10:30:45          │
│                                     │
│  ═══════════════════════════════    │
│  FALSIFICATION STATUS               │
│  ═══════════════════════════════    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    NOT FALSIFIED            │   │  ← Large, clear status
│  └─────────────────────────────┘   │
│                                     │
│  ───────────────────────────────    │
│  Statistical Metrics                │
│  ───────────────────────────────    │
│                                     │
│  Confidence Level:    0.87          │
│  ├─────────────────────────┤        │
│  │████████████████████     │ 87%    │
│  └─────────────────────────┘        │
│  Interpretation: High confidence    │
│                                     │
│  P-value:            0.002          │
│  Significance: ** (p < 0.01)        │
│                                     │
│  Effect Size (d):    0.62           │
│  Interpretation: Medium-large       │
│                                     │
│  Statistical Power:  0.85           │
│  Interpretation: Well-powered       │
│                                     │
│  ───────────────────────────────    │
│  Detailed Results                   │
│  ───────────────────────────────    │
│                                     │
│  Full ignition trials:  847/1000    │
│  Conscious trials:      845/847     │
│  Violation rate:        0.2%        │
│                                     │
│  ───────────────────────────────    │
│  Visualization                      │
│  ───────────────────────────────    │
│                                     │
│  ┌───────────────────────────┐     │
│  │                           │     │
│  │  [Distribution Plot]      │     │
│  │                           │     │
│  │         ▁▃▅▇▅▃▁          │     │
│  │                           │     │
│  └───────────────────────────┘     │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    Export Results           │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

### Result Status Display

**NOT FALSIFIED (Green):**

```python
┌─────────────────────────────┐
│  ✓ NOT FALSIFIED            │  ← Green background
└─────────────────────────────┘
Framework survived this test
```

**FALSIFIED (Red):**

```python
┌─────────────────────────────┐
│  ⚠ FALSIFIED                │  ← Red background
└─────────────────────────────┘
Framework contradicted by evidence
```

**INCONCLUSIVE (Yellow):**

```python
┌─────────────────────────────┐
│  ? INCONCLUSIVE             │  ← Yellow background
└─────────────────────────────┘
Insufficient evidence (low power)
```

### Confidence Level Visualization

```text
Confidence Level: 0.87

Low                    High
├─────────────────────────┤
│████████████████████     │ 87%
└─────────────────────────┘
     ^
     └─ Indicator shows confidence level
```

### Statistical Significance Indicators

```text
P-value: 0.002

*** p < 0.001  (Extremely significant)
**  p < 0.01   (Highly significant)

*   p < 0.05   (Significant)

ns  p ≥ 0.05   (Not significant)
```

## Menu Bar Functions

```python
┌─────────────────────────────────────────────────────────────┐
│ File   Edit   View   Tools   Help                           │
└─────────────────────────────────────────────────────────────┘
```

```text
┌──────────────┬──────────────┐
│   Test 1     │   Test 2     │
├──────────────┼──────────────┤
│ NOT FALSIF.  │ NOT FALSIF.  │
│ Conf: 0.87   │ Conf: 0.91   │
│ P: 0.002     │ P: 0.001     │
└──────────────┴──────────────┘
```

---

**Version:** 1.0  
**Last Updated:** 2025-01-07  
**See Also:** [USER_GUIDE.md](USER_GUIDE.md), [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
