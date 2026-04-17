# APGI System Testing Guide

This guide provides comprehensive information about the testing infrastructure for achieving high test coverage (Target: 85%+).

## Table of Contents

1. [Test Organization](#test-organization)
2. [Running Tests](#running-tests)
3. [Writing Tests](#writing-tests)
4. [Property-Based Testing](#property-based-testing)
5. [Coverage Analysis](#coverage-analysis)
6. [Fixtures and Utilities](#fixtures-and-utilities)
7. [Best Practices](#best-practices)

## Test Organization

Tests are organized into three main categories:

```text
tests/
├── unit/              # Unit tests for individual functions/classes
│   ├── core/         # Core module tests
│   ├── experiments/  # Experimental task tests
│   ├── neural/       # Neural module tests
│   └── ...
├── property/         # Property-based tests using Hypothesis
│   ├── test_free_energy_properties.py
│   ├── test_precision_properties.py
│   └── ...
├── integration/      # Integration tests for subsystem interactions
│   ├── test_core_integration.py
│   └── ...
├── conftest.py       # Shared fixtures and configuration
└── strategies.py     # Custom Hypothesis strategies
```

## Running Tests

### All Tests

```bash
pytest tests/
# or
make test
```

### By Category

```bash
# Unit tests only
pytest tests/unit/ -v -m unit
make test-unit

# Property-based tests only
pytest tests/property/ -v -m property
make test-property

# Integration tests only
pytest tests/integration/ -v -m integration
make test-integration
```

### With Coverage

```bash
# Full coverage analysis
make test-coverage

# Coverage report only
make coverage-report

# Detailed gap analysis
make coverage-gaps
```

### Specific Tests

```bash
# Run specific test file
pytest tests/unit/core/test_free_energy.py -v

# Run specific test function
pytest tests/unit/core/test_free_energy.py::test_free_energy_non_negative -v

# Run tests matching pattern
pytest -k "free_energy" -v
```

### Excluding Slow Tests

```bash
# Skip slow tests during development
pytest -m "not slow"
```

## Writing Tests

### Unit Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_feature_behavior():
    """
    Clear description of what is being tested.
    
    This test validates that [specific behavior] works correctly
    when [specific conditions]. It covers requirement X.Y.
    """
    # Arrange: Set up test data and preconditions
    input_data = create_test_data()
    expected_output = calculate_expected_result(input_data)
    
    # Act: Execute the code under test
    actual_output = function_under_test(input_data)
    
    # Assert: Verify the results
    assert actual_output == expected_output
    assert validate_invariants(actual_output)
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_unit_behavior():
    """Unit test for specific function."""
    pass

@pytest.mark.integration
def test_subsystem_interaction():
    """Integration test for multiple components."""
    pass

@pytest.mark.slow
def test_expensive_computation():
    """Test that takes significant time."""
    pass

@pytest.mark.edge_case
def test_boundary_condition():
    """Test for edge case or boundary value."""
    pass
```

### Using Fixtures

Leverage shared fixtures from `conftest.py`:

```python
def test_with_config(config):
    """Test using default configuration fixture."""
    assert config["system"]["timestep_ms"] > 0

def test_with_apgi_simulation(apgi_simulation):
    """Test using APGI system fixture."""
    apgi_simulation.step()
    assert apgi_simulation.time > 0

def test_with_random_data(random_observation, random_body_state):
    """Test using random data fixtures."""
    assert len(random_observation) == 256
    assert "heart_rate" in random_body_state
```

### Edge Case Testing

Test boundary conditions and invalid inputs:

```python
def test_empty_inputs(empty_input_cases):
    """Test handling of empty inputs."""
    for case_name, empty_value in empty_input_cases.items():
        with pytest.raises(ValueError, match="Input cannot be empty"):
            process_input(empty_value)

def test_boundary_values(boundary_values):
    """Test behavior at boundaries."""
    assert calculate_precision(boundary_values["zero"]) == 0.0
    assert calculate_precision(boundary_values["one"]) == 1.0

def test_invalid_inputs(invalid_inputs):
    """Test error handling for invalid inputs."""
    with pytest.raises(ValueError):
        validate_precision(invalid_inputs["negative_precision"])
```

## Property-Based Testing

### Writing Property Tests

Use Hypothesis to test universal properties:

```python
from hypothesis import given, strategies as st
from tests.strategies import belief_state_strategy, observation_strategy

@given(belief_state_strategy(), observation_strategy())
def test_belief_update_preserves_probability(belief, observation):
    """
    Property: Belief updates preserve probability normalization.
    
    Feature: comprehensive-test-coverage, Property 5
    Validates: Requirements 13.3
    
    For any belief state and observation, the updated belief
    should sum to 1.0 (within numerical tolerance).
    """
    updated_belief = update_belief(belief, observation)
    assert abs(sum(updated_belief) - 1.0) < 1e-6
```

### Custom Strategies

Use custom strategies from `tests/strategies.py`:

```python
from tests.strategies import (
    belief_state_strategy,
    observation_strategy,
    precision_weighted_error_strategy,
    config_strategy,
    probability_distribution_strategy,
    free_energy_components_strategy,
)

@given(free_energy_components_strategy())
def test_free_energy_non_negative(components):
    """Property: Free energy is always non-negative."""
    fe = calculate_free_energy(
        components["belief"],
        components["observation"],
        components["precision"]
    )
    assert fe >= 0.0
```

### Hypothesis Profiles

Configure test thoroughness via environment variable:

```bash
# Fast feedback during development (20 examples)
export HYPOTHESIS_PROFILE=dev
pytest tests/property/

# Balanced for CI/CD (100 examples)
export HYPOTHESIS_PROFILE=ci
pytest tests/property/

# Thorough testing (1000 examples)
export HYPOTHESIS_PROFILE=thorough
pytest tests/property/
```

## Coverage Analysis

### Viewing Coverage

```bash
# Generate HTML report
make coverage-report

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Analyzing Gaps

```bash
# Detailed gap analysis
make coverage-gaps

# View analysis
cat coverage_gap_analysis.json
```

### Coverage Configuration

Coverage settings in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=apgi_simulation",
    "--cov=api",
    "--cov-fail-under=85",
]

[tool.coverage.run]
source = ["apgi_simulation", "api"]
omit = [
    "**/apgi_gui.py",
    "**/*_GUI.py",
    "**/tests/*",
]
branch = true
```

## Fixtures and Utilities

### Available Fixtures

From `tests/conftest.py`:

- `config` - Default system configuration
- `apgi_simulation` - Fresh APGI system instance
- `body_model` - Body model instance
- `random_observation` - Random observation vector
- `random_body_state` - Random physiological state
- `valid_belief_state` - Normalized probability distribution
- `valid_precision` - Valid precision value
- `empty_input_cases` - Various empty inputs
- `boundary_values` - Boundary value test cases
- `invalid_inputs` - Invalid input test cases
- `test_data_dir` - Temporary directory for test data
- `mock_config_minimal` - Minimal valid configuration
- `sample_time_series` - Sample temporal data
- `performance_timer` - Context manager for timing
- `db` - Test database session

### Hypothesis Strategies

From `tests/strategies.py`:

- `body_state_strategy()` - Physiological body states
- `observation_strategy(dim)` - Observation vectors
- `belief_state_strategy(num_levels, level_dims)` - Hierarchical beliefs
- `config_strategy()` - Valid configurations
- `precision_weighted_error_strategy()` - Precision-weighted errors
- `probability_distribution_strategy(size)` - Probability distributions
- `precision_weight_strategy()` - Precision weights [0, 1]
- `confidence_value_strategy()` - Confidence values
- `free_energy_components_strategy()` - Free energy components
- `serializable_config_strategy()` - JSON-serializable configs
- `invalid_input_strategy()` - Various invalid inputs

## Best Practices

### Test Quality

1. **Meaningful Tests**: Validate actual behavior, not just exercise code
2. **Clear Intent**: Use descriptive names and docstrings
3. **Appropriate Scope**: Unit tests test units, integration tests test interactions
4. **Maintainability**: Keep tests simple and focused
5. **Performance**: Tests should execute quickly

### Test Documentation

```python
def test_feature():
    """
    One-line summary of what is tested.
    
    Detailed description of the test scenario, including:
    - What behavior is being validated
    - What conditions are being tested
    - What requirements are covered
    
    Validates: Requirements X.Y, X.Z
    """
    pass
```

### Property Test Documentation

```python
@given(strategy())
def test_property():
    """
    Property: Universal property being tested.
    
    Feature: feature-name, Property N
    Validates: Requirements X.Y
    
    Detailed explanation of the property and why it should hold.
    """
    pass
```

### Avoiding Common Pitfalls

1. **Don't test framework behavior**: Test your code, not pytest/Hypothesis
2. **Don't use mocks to make tests pass**: Tests must validate real functionality
3. **Don't write trivial tests**: Focus on meaningful validation
4. **Don't ignore test failures**: Fix the code or the test, don't skip
5. **Don't write interdependent tests**: Each test should be independent

### Test Execution Performance

1. **Mark slow tests**: Use `@pytest.mark.slow` for tests >1 second
2. **Use appropriate fixtures**: Session-scoped for expensive setup
3. **Parallelize when possible**: Use `pytest-xdist` for parallel execution
4. **Optimize property tests**: Balance thoroughness and speed

### Coverage Goals

- **Target**: 85% statement coverage (minimum recommended)
- **Exclude**: GUI modules, test files themselves
- **Focus**: Meaningful tests that validate correctness
- **Quality**: High-quality tests that serve as documentation

## Continuous Integration

Tests run automatically in GitHub Actions:

- `.github/workflows/test.yml` - Basic test workflow
- `.github/workflows/ci-cd.yml` - Full CI/CD pipeline

Both workflows:

- Run on push to main/develop branches
- Run on pull requests
- Require 85%+ coverage to pass
- Upload coverage reports to Codecov
- Archive HTML reports as artifacts

## Getting Help

- Review existing tests for examples
- Check `scripts/README.md` for coverage tools
- See design document for property definitions
- Ask questions in pull request reviews
