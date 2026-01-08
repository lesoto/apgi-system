# Configuration Validation Guide

The APGI system includes a comprehensive configuration validation tool to help catch configuration errors early and provide helpful error messages.

## Quick Start

### Validate a Configuration File

```python
from apgi_system.config_validator import validate_config_file

# Validate the default configuration
validate_config_file("config/default.yaml")
```

### Validate a Configuration Dictionary

```python
from apgi_system.config_validator import ConfigValidator

validator = ConfigValidator()
config = {
    "system": {"timestep_ms": 1.0},
    # ... rest of config
}

# Raises ConfigValidationError if invalid
validator.validate(config)
```

## Features

### 1. Schema Validation

The validator checks:

- Required sections are present
- Required fields within sections are present
- Field types are correct (int, float, list, dict)
- Numeric values are within acceptable ranges
- List lengths match expected values
- Range specifications have min < max

### 2. Cross-Parameter Validation

The validator performs consistency checks:

- Thermodynamic budget consistency (baseline + ignition ≤ total)
- Ignition timing consistency (amplification vs refractory period)
- Precision initialization within range
- Hierarchy level count matches configuration list length

### 3. Detailed Error Messages

Get specific error messages for each validation failure:

```python
errors = validator.validate_with_details(config)
for error in errors:
    print(error)
```

Example output:

```text
Field 'system.timestep_ms' value 1000.0 is out of range [0.01, 100.0]
Missing required field: 'active_inference.learning_rate' (Learning rate for active inference)
Field 'active_inference.precision_range' range invalid: min (10.0) must be less than max (1.0)
```

### 4. Automatic Fix Suggestions

Get suggestions for common configuration issues:

```python
suggestions = validator.suggest_fixes(config)
for field, suggestion in suggestions.items():
    print(f"{field}: {suggestion['current']} → {suggestion['suggested']}")
    print(f"  Reason: {suggestion['reason']}")
```

### 5. Common Mistakes Help

Get help text for common configuration mistakes:

```python
help_text = validator.get_common_mistakes_help()
print(help_text)
```

## Configuration Schema

### Required Sections

All configurations must include these sections:

1. **system**: Basic system parameters
   - `timestep_ms` (0.01-100.0): Simulation timestep in milliseconds

2. **hierarchy**: Hierarchical structure
   - `num_levels` (1-10): Number of hierarchical levels
   - `level_configs`: List of level configurations

3. **active_inference**: Active inference parameters
   - `learning_rate` (0.0-1.0): Learning rate
   - `precision_init` (0.01-100.0): Initial precision
   - `precision_range`: [min, max] precision values
   - `free_energy_threshold` (0.0-10000.0): Threshold value

4. **predictive_processing**: Prediction parameters
   - `prediction_horizon_ms` (1.0-10000.0): Prediction horizon
   - `error_accumulation_window_ms` (1.0-10000.0): Error window
   - `temporal_discount` (0.0-1.0): Temporal discount factor

5. **precision**: Precision weighting parameters
   - `exteroceptive_baseline` (0.01-100.0): Baseline precision
   - `interoceptive_baseline` (0.01-100.0): Baseline precision
   - `attention_gain_range`: [min, max] attention gain
   - `volatility_sensitivity` (0.0-10.0): Sensitivity value

6. **ignition**: Ignition dynamics parameters
   - `baseline_threshold` (0.1-100.0): Baseline threshold
   - `threshold_range`: [min, max] threshold values
   - `sigmoid_alpha` (0.1-100.0): Sigmoid steepness
   - `amplification_duration_ms` (10.0-10000.0): Duration
   - `refractory_period_ms` (10.0-10000.0): Refractory period
   - `workspace_nodes` (10-100000): Number of workspace nodes

7. **interoception**: Interoceptive parameters
   - `body_states`: List of body state configurations
   - `prediction_lead_ms` (1.0-10000.0): Prediction lead time
   - `allostatic_ranges`: Dictionary of range configurations

8. **somatic_markers**: Somatic marker parameters
   - `capacity` (1-1000000): Maximum marker capacity
   - `learning_rate` (0.0-1.0): Learning rate
   - `decay_rate` (0.0-1.0): Decay rate
   - `retrieval_threshold` (0.0-1.0): Retrieval threshold
   - `gain_modulation_range`: [min, max] gain values

9. **thermodynamic**: Energy budget parameters
   - `total_energy_budget` (1.0-100000.0): Total energy
   - `baseline_consumption` (0.0-100000.0): Baseline consumption
   - `ignition_cost` (0.0-100000.0): Cost per ignition
   - `recovery_rate` (0.0-100000.0): Energy recovery rate
   - `depletion_threshold` (0.0-100000.0): Minimum reserve

### Optional Sections

These sections are optional but will be validated if present:

- `self_model`: Self-model parameters
- `oscillations`: Neural oscillation parameters
- `validation`: Validation and metrics settings
- `visualization`: Visualization settings

## Common Validation Errors

### 1. Missing Required Section

**Error**: `Missing required section: 'ignition'`

**Solution**: Add the missing section to your configuration file. Use `config/default.yaml` as a template.

### 2. Wrong Parameter Type

**Error**: `Field 'system.timestep_ms' has wrong type: expected int or float, got str`

**Solution**: Remove quotes from numeric values in YAML:

```yaml
# Wrong
timestep_ms: "1.0"

# Correct
timestep_ms: 1.0
```

### 3. Out of Range Value

**Error**: `Field 'active_inference.learning_rate' value 5.0 is out of range [0.0, 1.0]`

**Solution**: Adjust the value to be within the acceptable range:

```yaml
# Wrong
learning_rate: 5.0

# Correct
learning_rate: 0.01
```

### 4. Invalid Range Specification

**Error**: `Field 'precision_range' range invalid: min (10.0) must be less than max (1.0)`

**Solution**: Ensure the first value is less than the second:

```yaml
# Wrong
precision_range: [10.0, 1.0]

# Correct
precision_range: [0.1, 10.0]
```

### 5. Thermodynamic Budget Issues

**Warning**: `baseline_consumption (60.0) + ignition_cost (50.0) exceeds total_energy_budget (100.0)`

**Solution**: Increase the total budget or reduce consumption/costs:

```yaml
# Option 1: Increase budget
total_energy_budget: 150.0

# Option 2: Reduce costs
baseline_consumption: 40.0
ignition_cost: 30.0
```

## Integration with APGI System

The configuration validator can be integrated into the APGI system initialization:

```python
from apgi_system.system import APGISystem
from apgi_system.config_validator import validate_config_file, ConfigValidationError

try:
    # Validate before loading
    validate_config_file("my_config.yaml")
    
    # Initialize system
    system = APGISystem(config_path="my_config.yaml")
    
except ConfigValidationError as e:
    print(f"Configuration validation failed:\n{e}")
    # Handle error appropriately
```

## Examples

See `examples/validate_config_example.py` for complete working examples of:

1. Validating the default configuration
2. Handling invalid configurations
3. Getting detailed error messages
4. Checking for warnings
5. Getting automatic fix suggestions
6. Accessing help for common mistakes

Run the examples:

```bash
python examples/validate_config_example.py
```

## API Reference

### ConfigValidator

Main validation class.

**Methods**:

- `validate(config)`: Validate and raise exception if invalid
- `validate_with_details(config)`: Return list of error messages
- `validate_parameter_ranges(config)`: Check cross-parameter consistency
- `suggest_fixes(config)`: Get automatic fix suggestions
- `get_common_mistakes_help()`: Get help text for common mistakes

### validate_config_file(config_path)

Convenience function to validate a YAML configuration file.

**Parameters**:

- `config_path` (str): Path to YAML configuration file

**Raises**:

- `ConfigValidationError`: If configuration is invalid
- `FileNotFoundError`: If file doesn't exist

### Exceptions

- `ConfigValidationError`: Raised when configuration validation fails
- `ConfigValidationWarning`: Warning for non-critical issues

## Best Practices

1. **Always validate before deployment**: Run validation on configuration files before using them in production
2. **Use the default config as a template**: Start with `config/default.yaml` and modify as needed
3. **Check warnings**: Even if validation passes, check for warnings about potential issues
4. **Test configuration changes**: Validate after making any configuration changes
5. **Use version control**: Keep configuration files in version control to track changes

## Troubleshooting

If you encounter validation errors:

1. Read the error message carefully - it tells you exactly what's wrong
2. Check the parameter ranges in this documentation
3. Use `validate_with_details()` to get all errors at once
4. Use `suggest_fixes()` to get automatic suggestions
5. Consult `get_common_mistakes_help()` for guidance
6. Compare with `config/default.yaml` to see correct format

For additional help, see the main APGI documentation or open an issue on GitHub.
