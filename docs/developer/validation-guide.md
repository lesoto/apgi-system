# Validation and Error Handling Quick Reference

## Quick Start

### 1. Validate Parameters

```python
from apgi_framework.validation import get_validator

validator = get_validator()
result = validator.validate_apgi_parameters(
    extero_precision=2.0,
    intero_precision=1.5,
    threshold=3.5
)

if not result.is_valid:
    print(result.get_message())
```

### 2. Run Health Check

```python
from apgi_framework.validation import get_health_checker

health_checker = get_health_checker()
result = health_checker.run_full_health_check()
print(result.get_report())
```

### 3. Use Safe Test Execution

```python
from apgi_framework.falsification.primary_falsification_test import PrimaryFalsificationTest

# Tests now have automatic error handling

test = PrimaryFalsificationTest()
result = test.run_falsification_test(n_trials=100, n_participants=20)
```python

## Command Line Tools

### Health Check

```bash
python -m apgi_framework.validation.diagnostics_cli health-check
```python

### Validate Parameters

```bash
python -m apgi_framework.validation.diagnostics_cli validate --params extero_precision=2.0 threshold=3.5
```python

### Get Parameter Info

```bash
python -m apgi_framework.validation.diagnostics_cli param-info --parameter threshold
```python

## Common Validation Patterns

### Validate Before Creating Config

```python
from apgi_framework.validation import get_validator
from apgi_framework.config import APGIParameters

validator = get_validator()

# Validate first

result = validator.validate_apgi_parameters(
    extero_precision=2.0,
    intero_precision=1.5,
    # ... other params
)

if result.is_valid:
    # Create config
    params = APGIParameters(
        extero_precision=2.0,
        intero_precision=1.5,
        # ... other params
    )
```python

### Check Specific Component

```python
from apgi_framework.validation import get_health_checker

health_checker = get_health_checker()
result = health_checker.check_component("python")

if result.overall_status != "healthy":
    print("Python environment issues detected")
```python

### Add Retry to Custom Function

```python
from apgi_framework.validation import with_retry, RetryConfig

config = RetryConfig(max_attempts=3, initial_delay=1.0)

@with_retry(config)
def my_function():
    # Function that might fail transiently
    pass
```python

## Parameter Ranges

### APGI Parameters

- `extero_precision`: 0.01 - 10.0 (typical: 0.5-5.0)
- `intero_precision`: 0.01 - 10.0 (typical: 0.5-5.0)
- `extero_error`: -10.0 - 10.0 (typical: -3 to 3)
- `intero_error`: -10.0 - 10.0 (typical: -3 to 3)
- `somatic_gain`: 0.01 - 5.0 (typical: 0.5-2.0)
- `threshold`: 0.1 - 10.0 (typical: 2.0-5.0)
- `steepness`: 0.1 - 10.0 (typical: 1.0-3.0)

### Experimental Config

- `n_trials`: 1 - 100000 (typical: 50-1000)
- `n_participants`: 1 - 10000 (typical: 20-200)
- `alpha_level`: 0.001 - 0.1 (typical: 0.05)

### Neural Thresholds

- `p3b_threshold`: 1.0 - 20.0 μV (typical: 3.0-7.0)
- `gamma_plv_threshold`: 0.05 - 0.8 (typical: 0.2-0.4)
- `bold_z_threshold`: 1.0 - 5.0 (typical: 2.3-3.5)
- `pci_threshold`: 0.1 - 0.8 (typical: 0.3-0.5)

## Error Types

### ValidationError

- Parameter validation failures
- Not retried automatically
- Fix parameters and retry

### ConfigurationError

- Configuration file issues
- Not retried automatically
- Fix configuration and retry

### SimulationError

- Simulation failures
- Retried automatically (up to 2 times)
- May recover with different random seed

### StatisticalError

- Statistical analysis failures
- Not retried automatically
- May indicate insufficient data

## Troubleshooting

### "Parameter validation failed"

1. Check parameter ranges in this guide
2. Use `param-info` command to get details
3. Review error message for specific issue

### "System health check failed"

1. Run `health-check` command
2. Review component status
3. Follow recommendations in report

### "All trials failed"

1. Check system health
2. Review error logs
3. Verify parameters are reasonable
4. Try with smaller sample size

### "Configuration error"

1. Validate parameters before creating config
2. Check for typos in parameter names
3. Ensure all required parameters provided

## Best Practices

1. **Always validate parameters** before running tests
2. **Run health check** before long-running experiments
3. **Check error logs** if tests fail
4. **Use reasonable parameter values** within typical ranges
5. **Start with small samples** to verify setup
6. **Monitor system resources** during large experiments

## Getting Help

- Run examples: `python examples/validation_and_error_handling_example.py`
- Read full documentation: `VALIDATION_AND_ERROR_HANDLING_SUMMARY.md`
- Check parameter info: `python -m apgi_framework.validation.diagnostics_cli param-info --parameter <name>`
- Run health check: `python -m apgi_framework.validation.diagnostics_cli health-check`
