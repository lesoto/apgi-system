# APGI Framework - Quick Start Guide

Get up and running with the APGI Framework Testing System in 5 minutes.

## Installation (2 minutes)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python -m apgi_framework.cli validate-system
```

Expected output:

```text
System Validation: PASS
```

✅ **You're ready to go!**

## Your First Test (3 minutes)

### Option A: Using the GUI (Recommended for Beginners)

**1. Launch the GUI:**

```python
python GUI-Launcher.py
```

**2. Run a test:**

- Click **"Primary Falsification Test"** button
- Leave default parameters
- Click **"Run Test"**
- Wait 30-60 seconds

**3. View results:**

- Results appear in the right panel
- Look for "Falsification Status: NOT FALSIFIED" or "FALSIFIED"

### Option B: Using the CLI (Recommended for Automation)

**1. Run a test:**

```python
python -m apgi_framework.cli run-test primary --trials 1000
```

**2. View results:**
Results are displayed in the terminal and saved to `results/` directory.

### Option C: Using Python API (Recommended for Integration)

**1. Create a script:**

```python
from apgi_framework.main_controller import MainApplicationController

# Initialize
controller = MainApplicationController()
controller.initialize_system()

# Run test
tests = controller.get_falsification_tests()
result = tests['primary'].run_test(n_trials=1000)

# View results
print(f"Falsified: {result.is_falsified}")
print(f"Confidence: {result.confidence_level:.2f}")

# Cleanup
controller.shutdown_system()
```

**2. Run it:**

```python
python my_first_test.py
```

## Understanding Your Results

### Key Metrics

**Falsification Status:**

- `NOT FALSIFIED` = Framework survived this test
- `FALSIFIED` = Framework contradicted by evidence

**Confidence Level:**

- `> 0.8` = High confidence in result
- `0.5-0.8` = Moderate confidence
- `< 0.5` = Low confidence (increase sample size)

**P-value:**

- `< 0.05` = Statistically significant
- `≥ 0.05` = Not significant

**Effect Size (Cohen's d):**

- `> 0.8` = Large effect
- `0.5-0.8` = Medium effect
- `0.2-0.5` = Small effect
- `< 0.2` = Negligible effect

### Example Result Interpretation

```text
Falsification Status: NOT FALSIFIED
Confidence Level: 0.87
P-value: 0.002
Effect Size: 0.62
Statistical Power: 0.85
```

**What this means:**

- Framework survived this test
- High confidence (0.87)
- Highly significant (p = 0.002)
- Medium-large effect (d = 0.62)
- Well-powered study (0.85)

**Conclusion:** Strong evidence supporting the framework.

## Common Workflows

### Workflow 1: Quick Test

**Goal:** Run a single test with default settings.

```python
python -m apgi_framework.cli run-test primary --trials 1000
```

**Time:** ~1 minute

### Workflow 2: Comprehensive Evaluation

**Goal:** Test all falsification criteria.

```python
python -m apgi_framework.cli run-batch --all-tests
```

**Time:** ~5 minutes

### Workflow 3: Parameter Exploration

**Goal:** Test different threshold values.

```bash
# Create configuration
python -m apgi_framework.cli generate-config --output config.json

# Edit config.json to set different threshold values

# Then run
python -m apgi_framework.cli --config config.json run-test primary
```

**Time:** ~2 minutes per configuration

### Workflow 4: Reproducible Research

**Goal:** Get exactly reproducible results.

```python
python -m apgi_framework.cli run-test primary --trials 2000 --seed 42
```

**Time:** ~2 minutes

## Next Steps

### Learn More

1. **Full User Guide:** [USER_GUIDE.md](USER_GUIDE.md)
   - Detailed GUI instructions
   - Advanced CLI usage
   - Best practices

2. **Examples:** [examples/](../examples/)
   - Working code samples
   - Common use cases
   - Advanced techniques

3. **Results Interpretation:** [RESULTS_INTERPRETATION_GUIDE.md](RESULTS_INTERPRETATION_GUIDE.md)
   - Detailed metric explanations
   - Decision trees
   - Reporting guidelines

### Try These Examples

#### Example 1: Batch Processing

```bash
cd examples/
python 02_batch_processing_configurations.py
```

#### Example 2: Custom Analysis

```bash
cd examples/
python 03_custom_analysis_saved_results.py
```

#### Example 3: Validation and Error Handling

```bash
cd examples/
python validation_and_error_handling_example.py
```

## Troubleshooting

### Problem: "System not initialized" error

**Solution:**

```python
controller = MainApplicationController()
controller.initialize_system()  # Don't forget this!
```

### Problem: Import errors

**Solution:**

```bash
pip install -r requirements.txt
```

### Problem: GUI won't launch

**Solution:**

```bash
pip install PyQt5
```

### Problem: Tests take too long

**Solution:**

```bash
# Reduce trial count for testing
python -m apgi_framework.cli run-test primary --trials 100
```

### More Help

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

## Quick Reference

### Common Commands

```bash
# Validate system
python -m apgi_framework.cli validate-system

# Run primary test
python -m apgi_framework.cli run-test primary --trials 1000

# Run all tests
python -m apgi_framework.cli run-batch --all-tests

# Generate config
python -m apgi_framework.cli generate-config --output config.json

# Check status
python -m apgi_framework.cli status

# Launch GUI
python GUI-Launcher.py
```

### Parameter Ranges

| Parameter | Range | Default |
| ----------- | ------- | --------- |
| extero_precision | 0.1-10.0 | 2.0 |
| intero_precision | 0.1-10.0 | 1.5 |
| threshold | 0.5-10.0 | 3.5 |
| steepness | 0.1-5.0 | 2.0 |
| somatic_gain | 0.1-5.0 | 1.3 |

### Test Types

| Test | Command | Description |
| ------ | --------- | ------------- |
| Primary | `primary` | Full ignition without consciousness |
| Consciousness Without Ignition | `consciousness-without-ignition` | Consciousness without ignition |
| Threshold Insensitivity | `threshold-insensitivity` | Neuromodulatory effects |
| Soma-Bias | `soma-bias` | Interoceptive vs exteroceptive bias |

## Tips for Success

1. **Start Simple:** Begin with default parameters and 1000 trials
2. **Validate First:** Always run `validate-system` before important experiments
3. **Set Random Seeds:** Use `--seed 42` for reproducible results
4. **Check Power:** Ensure statistical power ≥ 0.8
5. **Save Everything:** Keep configuration files with results
6. **Document:** Note parameter choices and rationale

## Getting Help

1. **Check Documentation:**
   - [USER_GUIDE.md](USER_GUIDE.md)
   - [CLI_REFERENCE.md](CLI_REFERENCE.md)
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

2. **Run Diagnostics:**

   ```bash
   python -m apgi_framework.cli validate-system --detailed
   ```

3. **Enable Debug Logging:**

   ```bash
   python -m apgi_framework.cli --log-level DEBUG run-test primary
   ```

4. **Check Logs:**

   ```bash
   cat results/apgi_framework.log
   ```

---

**Congratulations!** You're now ready to use the APGI Framework Testing System.

For detailed information, see the [Full Documentation Index](DOCUMENTATION_INDEX.md).

**Version:** 1.0  
**Last Updated:** 2025-01-07
