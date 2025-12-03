"""
Example script demonstrating configuration validation.

This script shows how to use the ConfigValidator to validate
APGI system configuration files and get helpful error messages.
"""

from apgi_system.config_validator import (
    ConfigValidator,
    ConfigValidationError,
    validate_config_file
)
import yaml


def example_1_validate_default_config():
    """Example 1: Validate the default configuration file."""
    print("=" * 60)
    print("Example 1: Validating default configuration")
    print("=" * 60)

    try:
        validate_config_file("config/default.yaml")
        print("✓ Default configuration is valid!")
    except ConfigValidationError as e:
        print(f"✗ Validation failed:\n{e}")
    print()


def example_2_validate_invalid_config():
    """Example 2: Validate an invalid configuration."""
    print("=" * 60)
    print("Example 2: Validating invalid configuration")
    print("=" * 60)

    # Create an invalid config (missing required fields)
    invalid_config = {
        "system": {
            "timestep_ms": 1000.0  # Out of range!
        }
        # Missing other required sections
    }

    validator = ConfigValidator()
    try:
        validator.validate(invalid_config)
        print("✓ Configuration is valid!")
    except ConfigValidationError as e:
        print(f"✗ Validation failed (as expected):\n{e}")
    print()


def example_3_get_detailed_errors():
    """Example 3: Get detailed error messages."""
    print("=" * 60)
    print("Example 3: Getting detailed validation errors")
    print("=" * 60)

    invalid_config = {
        "system": {
            "timestep_ms": "not a number"  # Wrong type
        },
        "active_inference": {
            "learning_rate": 5.0,  # Out of range
            "precision_range": [10.0, 1.0]  # Invalid range (min > max)
        }
    }

    validator = ConfigValidator()
    errors = validator.validate_with_details(invalid_config)

    print(f"Found {len(errors)} validation errors:")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
    print()


def example_4_check_warnings():
    """Example 4: Check for configuration warnings."""
    print("=" * 60)
    print("Example 4: Checking for configuration warnings")
    print("=" * 60)

    # Config with thermodynamic inconsistency
    config = {
        "thermodynamic": {
            "total_energy_budget": 100.0,
            "baseline_consumption": 60.0,
            "ignition_cost": 50.0,  # Total exceeds budget!
            "recovery_rate": 5.0,
            "depletion_threshold": 10.0
        }
    }

    validator = ConfigValidator()
    warnings = validator.validate_parameter_ranges(config)

    if warnings:
        print(f"Found {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print("✓ No warnings found!")
    print()


def example_5_get_fix_suggestions():
    """Example 5: Get automatic fix suggestions."""
    print("=" * 60)
    print("Example 5: Getting fix suggestions")
    print("=" * 60)

    config = {
        "active_inference": {
            "precision_init": 15.0,  # Outside range
            "precision_range": [0.1, 10.0]
        },
        "thermodynamic": {
            "total_energy_budget": 50.0,
            "baseline_consumption": 40.0,
            "ignition_cost": 20.0  # Exceeds budget
        }
    }

    validator = ConfigValidator()
    suggestions = validator.suggest_fixes(config)

    if suggestions:
        print(f"Found {len(suggestions)} suggested fix(es):")
        for field, suggestion in suggestions.items():
            print(f"\n  Field: {field}")
            print(f"    Current value: {suggestion['current']}")
            print(f"    Suggested value: {suggestion['suggested']}")
            print(f"    Reason: {suggestion['reason']}")
    else:
        print("✓ No fixes needed!")
    print()


def example_6_get_help():
    """Example 6: Get help for common mistakes."""
    print("=" * 60)
    print("Example 6: Getting help for common mistakes")
    print("=" * 60)

    validator = ConfigValidator()
    help_text = validator.get_common_mistakes_help()
    print(help_text)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("APGI Configuration Validator Examples")
    print("=" * 60 + "\n")

    example_1_validate_default_config()
    example_2_validate_invalid_config()
    example_3_get_detailed_errors()
    example_4_check_warnings()
    example_5_get_fix_suggestions()
    example_6_get_help()

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)
