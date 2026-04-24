# Parameter Validation Guide

## Overview

The APGI Framework includes a comprehensive parameter validation system that ensures all experimental parameters are within valid ranges and provides helpful feedback for optimal configuration. This guide explains how to use the validation system effectively.

## Features

### 1. Real-Time Validation

- Parameters are validated as you type in the GUI
- Visual indicators show validation status (✓, ⚠, ✗)
- Immediate feedback prevents invalid configurations

### 2. Comprehensive Error Messages

- Clear descriptions of what went wrong
- Specific valid ranges for each parameter
- Typical values for reference

### 3. Warnings and Suggestions

- Warnings for unusual but valid values
- Suggestions for optimal parameter choices
- Context-aware recommendations

### 4. Multiple Validation Levels

- Individual parameter validation
- Configuration-level validation
- Comprehensive system-wide validation

## Parameter Categories

### APGI Equation Parameters

 | Parameter | Range | Typical Values | Description |
 | ----------- | ------- | ---------------- | ------------- |
 | `extero_precision` | 0.01 - 10.0 | 0.5 - 5.0 | Precision of exteroceptive signals |
 | `intero_precision` | 0.01 - 10.0 | 0.5 - 5.0 | Precision of interoceptive signals |
 | `extero_error` | -10.0 - 10.0 | -3.0 - 3.0 | Exteroceptive prediction error (z-score) |
 | `intero_error` | -10.0 - 10.0 | -3.0 - 3.0 | Interoceptive prediction error (z-score) |
 | `somatic_gain` | 0.01 - 5.0 | 0.5 - 2.0 | Somatic marker gain |
 | `threshold` | 0.1 - 10.0 | 2.0 - 5.0 | Ignition threshold |
 | `steepness` | 0.1 - 10.0 | 1.0 - 3.0 | Sigmoid steepness |

### Experimental Configuration Parameters

 | Parameter | Range | Typical Values | Description |
 | ----------- | ------- | ---------------- | ------------- |
 | `n_trials` | 1 - 100,000 | 50 - 1,000 | Number of trials per test |
 | `n_participants` | 1 - 10,000 | 20 - 200 | Number of participants |
 | `alpha_level` | 0.001 - 0.1 | 0.05 | Statistical significance level |
 | `effect_size_threshold` | 0.1 - 2.0 | 0.3 - 0.8 | Minimum effect size |
 | `power_threshold` | 0.5 - 0.99 | 0.8 - 0.95 | Statistical power threshold |

### Neural Signature Thresholds

 | Parameter | Range | Typical Values | Description |
 | ----------- | ------- | ---------------- | ------------- |
 | `p3b_threshold` | 1.0 - 20.0 μV | 3.0 - 7.0 μV | P3b amplitude threshold |
 | `gamma_plv_threshold` | 0.05 - 0.8 | 0.2 - 0.4 | Gamma phase-locking value |
 | `bold_z_threshold` | 1.0 - 5.0 | 2.3 - 3.5 | BOLD Z-score threshold |
 | `pci_threshold` | 0.1 - 0.8 | 0.3 - 0.5 | PCI threshold |

## Using Validation in the GUI

### Visual Indicators

The GUI provides three types of visual indicators:

- **✓ (Green)**: Parameter is valid and within typical range
- **⚠ (Orange)**: Parameter is valid but unusual (warning)
- **✗ (Red)**: Parameter is invalid and must be corrected

### Tooltips

Hover over parameter labels to see:

- Valid range
- Typical values
- Parameter description

### Validation Status Panel

The validation status panel shows:

- Overall validation status
- Detailed error messages
- Warnings and suggestions
- Recommendations for improvement

### Validation Workflow

1. **Enter Parameters**: Type values into parameter fields
2. **Real-Time Feedback**: See immediate validation indicators
3. **Review Status**: Check validation status panel for details
4. **Validate All**: Click "Validate All" for comprehensive check
5. **Apply Changes**: Click "Apply Changes" to save configuration

## Using Validation Programmatically

### Basic Validation

```python
from apgi_framework.validation import get_validator

validator = get_validator()

# Validate APGI parameters
result = validator.validate_apgi_parameters(
    extero_precision=2.0,
    intero_precision=1.5,
    somatic_gain=1.3,
    threshold=3.5,
    steepness=2.0
)

if result.is_valid:
    print("✓ Parameters are valid")
else:
    print("✗ Validation failed:")
    print(result.get_message())
    print(result.get_details())
```

### Handling Validation Results

```python
# Check validation status
if not result.is_valid:
    # Handle errors
    for error in result.errors:
        print(f"Error: {error}")

# Check for warnings
if result.warnings:
    for warning in result.warnings:
        print(f"Warning: {warning}")

# Get suggestions
if result.suggestions:
    for suggestion in result.suggestions:
        print(f"Suggestion: {suggestion}")
```

### Comprehensive Validation

```python
# Validate all parameter types at once
result = validator.validate_all(
    apgi_params={
        'extero_precision': 2.0,
        'intero_precision': 1.5,
        # ... other APGI parameters
    },
    experimental_config={
        'n_trials': 1000,
        'n_participants': 100,
        # ... other experimental parameters
    },
    neural_thresholds={
        'p3b_threshold': 5.0,
        'gamma_plv_threshold': 0.3,
        # ... other thresholds
    }
)
```

### Using with ConfigManager

```python
from apgi_framework.config import APGIParameters, ConfigurationError

# ConfigManager automatically validates on creation
try:
    params = APGIParameters(
        extero_precision=2.0,
        intero_precision=1.5,
        extero_error=1.2,
        intero_error=0.8,
        somatic_gain=1.3,
        threshold=3.5,
        steepness=2.0
    )
    print("✓ Configuration created successfully")
except ConfigurationError as e:
    print(f"✗ Invalid configuration: {e}")
```

## Common Validation Scenarios

### Scenario 1: Invalid Parameter Range

**Problem**: Parameter value is outside valid range

```text
Error: extero_precision: Value -1.0 outside valid range [0.01, 10.0]
```

**Solution**: Adjust parameter to be within valid range (0.01 - 10.0)

### Scenario 2: Low Statistical Power

**Problem**: Trial count is too low for reliable results

```text
Warning: Low trial count (30) may have insufficient statistical power
```

**Solution**: Increase `n_trials` to at least 50-100 for better power

### Scenario 3: Unusual Parameter Values

**Problem**: Parameter is valid but unusual

```text
Warning: Very low precision (0.2) may indicate weak signal
```

**Solution**: Review parameter choice or proceed if intentional

### Scenario 4: Cross-Parameter Issues

**Problem**: Parameter combination is problematic

```text
Suggestion: Interoceptive precision is 7.5x higher than exteroceptive - strong interoceptive bias
```

**Solution**: Review relative precision values for balance

## Best Practices

### 1. Validate Early and Often

- Validate parameters before running experiments
- Use real-time validation in GUI
- Check validation status regularly

### 2. Pay Attention to Warnings

- Warnings indicate unusual but valid values
- Review warnings to ensure intentional choices
- Consider suggestions for optimization

### 3. Use Typical Values as Starting Points

- Start with typical values from documentation
- Adjust based on experimental needs
- Validate after each adjustment

### 4. Document Parameter Choices

- Save validated configurations
- Document reasons for unusual values
- Track parameter changes over time

### 5. Test with Validation

- Always validate before running tests
- Use comprehensive validation for final checks
- Review validation history for patterns

## Troubleshooting

### Problem: Validation Fails Unexpectedly

**Possible Causes**:

- Parameter value is outside valid range
- Type mismatch (string instead of number)
- Missing required parameters

**Solutions**:

1. Check error messages for specific issues
2. Verify parameter types match expected types
3. Ensure all required parameters are provided
4. Review parameter ranges in documentation

### Problem: Too Many Warnings

**Possible Causes**:

- Parameters are at edge of typical ranges
- Unusual experimental design
- Cross-parameter interactions

**Solutions**:

1. Review each warning individually
2. Adjust parameters if warnings are unintentional
3. Document reasons if warnings are intentional
4. Consider suggestions for optimization

### Problem: Validation Passes but Tests Fail

**Possible Causes**:

- Validation checks ranges, not experimental validity
- Parameter combination is valid but ineffective
- System-level issues beyond parameter validation

**Solutions**:

1. Review experimental design
2. Check system status and health
3. Validate test controller initialization
4. Review test-specific requirements

## API Reference

### ParameterValidator Class

#### Methods

- `validate_apgi_parameters(**params)`: Validate APGI equation parameters
- `validate_experimental_config(**config)`: Validate experimental configuration
- `validate_neural_thresholds(**thresholds)`: Validate neural signature thresholds
- `validate_pharmacological_condition(drug_type, dosage, time)`: Validate drug conditions
- `validate_statistical_parameters(**params)`: Validate statistical parameters
- `validate_all(apgi_params, experimental_config, neural_thresholds)`: Comprehensive validation
- `get_parameter_info(param_name)`: Get detailed parameter information
- `get_validation_summary()`: Get validation history summary

### ValidationResult Class

#### Attributes

- `is_valid`: Boolean indicating if validation passed
- `errors`: List of error messages
- `warnings`: List of warning messages
- `suggestions`: List of suggestion messages

#### ValidationResult Methods

- `get_message()`: Get formatted validation message
- `__bool__()`: Returns `is_valid` for boolean checks

## Examples

See `examples/parameter_validation_example.py` for comprehensive examples of:

- Basic validation
- Error handling
- Working with warnings and suggestions
- ConfigManager integration
- Comprehensive validation
- Parameter information retrieval
- Validation history tracking

## Related Documentation

- [Configuration Management](configuration_guide.md)
- [Error Handling](error_handling_guide.md)
- [System Validation](system_validation_guide.md)
- [GUI User Guide](gui_user_guide.md)
