# APGI Framework CLI Reference

The APGI Framework CLI is accessed via:

```bash
# Run as a module
python -m apgi_framework.cli [command] [options]

# Direct execution
python apgi_framework/cli.py [command] [options]
```

## Command Overview

### Available Commands

| Command | Description |
| ------- | ----------- |
| `run-test` | Run individual falsification tests |
| `run-batch` | Run batch experiments |
| `batch-test` | Advanced batch test execution |
| `run-tests` | Enhanced test execution with GUI feature parity |
| `test-results` | Manage test results |
| `test-analysis` | Analyze test results and performance |
| `test-coverage` | Analyze and generate test coverage |
| `organize-tests` | Organize and categorize tests |
| `generate-config` | Generate configuration files |
| `validate-system` | Validate system components |
| `status` | Show system status |
| `set-params` | Set APGI parameters |

## Global Options

| Option | Short | Description |
| ------ | ----- | ----------- |
| `--help` | `-h` | Show help message |
| `--verbose` | `-v` | Enable verbose output |
| `--quiet` | `-q` | Suppress non-error output |
| `--config` | `-c` | Specify configuration file |
| `--log-level` | `-l` | Set logging level (DEBUG, INFO, WARNING, ERROR) |
| `--output-dir` | `-o` | Specify output directory |

## Test Commands

### Run Individual Test

```bash
# Run primary falsification test
python -m apgi_framework.cli run-test primary --trials 1000

# Run consciousness without ignition test
python -m apgi_framework.cli run-test consciousness-without-ignition --trials 1000

# Run threshold insensitivity test
python -m apgi_framework.cli run-test threshold-insensitivity

# Run soma-bias test
python -m apgi_framework.cli run-test soma-bias --participants 100
```

**Test Options:**

| Option | Type | Range | Default | Description |
| --- | --- | --- | --- | --- |
| `--trials` | `-n` | 100-10000 | 1000 | Number of trials |
| `--participants` | `-p` | 10-1000 | 100 | Number of participants |
| `--seed` | | positive int | None | Random seed |
| `--config` | `-c` | path | None | Configuration file |

### Run Batch Tests

```bash
# Run all tests in batch
python -m apgi_framework.cli run-batch --all-tests

# Run specific tests in batch
python -m apgi_framework.cli run-batch --tests primary soma-bias

# Run in parallel (experimental)
python -m apgi_framework.cli run-batch --tests primary --parallel
```

### Advanced Batch Test Execution

```bash
# Run specific test files
python -m apgi_framework.cli batch-test --test-paths tests/test_core.py tests/test_cli.py

# Run tests with specific markers
python -m apgi_framework.cli batch-test --markers unit integration

# Run with keywords filter
python -m apgi_framework.cli batch-test --keywords "agent or cli"

# Parallel execution with custom workers
python -m apgi_framework.cli batch-test --parallel --max-workers 8 --timeout 600

# Generate HTML report
python -m apgi_framework.cli batch-test --report report.html
```

**Advanced Batch Options:**

| Option | Type | Range | Default | Description |
| --- | --- | --- | --- | --- |
| `--test-paths` | | paths | None | Specific test file paths |
| `--markers` | | unit, integration, research, core, slow, neural, behavioral | None | Test markers |
| `--keywords` | | string | None | Keyword patterns |
| `--parallel` | | flag | True | Run tests in parallel |
| `--sequential` | | flag | False | Run tests sequentially |
| `--max-workers` | | 1-64 | auto | Maximum parallel workers |
| `--timeout` | | 1-3600 | 600 | Timeout per test (seconds) |
| `--failfast` | | flag | False | Stop on first failure |
| `--report` | | path | None | Output path for HTML report |

### Enhanced Test Execution

```bash
# Run tests by category
python -m apgi_framework.cli run-tests --categories unit integration

# Run tests by module
python -m apgi_framework.cli run-tests --modules core clinical neural

# Run with coverage
python -m apgi_framework.cli run-tests --coverage --coverage-report html

# Quiet mode with progress bar
python -m apgi_framework.cli run-tests --quiet --progress bar
```

## Test Result Management

```bash
# List recent test results
python -m apgi_framework.cli test-results --list

# Show specific test result details
python -m apgi_framework.cli test-results --show session_123.json

# Re-run failed tests from previous run
python -m apgi_framework.cli test-results --rerun-failed session_123.json

# Clean old test results
python -m apgi_framework.cli test-results --clean
```

## Test Analysis

```bash
# Generate performance report for last 30 days
python -m apgi_framework.cli test-analysis --performance-report --days 30

# Show performance trends
python -m apgi_framework.cli test-analysis --trends --days 60

# Analyze failure patterns
python -m apgi_framework.cli test-analysis --failures --days 30

# Export analysis results
python -m apgi_framework.cli test-analysis --performance-report --export results.json --format json
```

## Test Coverage

```bash
# Analyze coverage gaps
python -m apgi_framework.cli test-coverage --analyze

# Generate missing tests
python -m apgi_framework.cli test-coverage --generate

# Generate coverage report
python -m apgi_framework.cli test-coverage --report

# Custom threshold and format
python -m apgi_framework.cli test-coverage --report --threshold 85 --format html
```

**Coverage Options:**

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--analyze` | flag | | Analyze test coverage gaps |
| `--generate` | flag | | Generate missing tests |
| `--report` | flag | | Generate coverage report |
| `--output-dir` | path | `generated_tests` | Output directory for generated tests |
| `--report-file` | path | `coverage_report.md` | Output file for report |
| `--threshold` | 0-100 | 90.0 | Coverage threshold percentage |
| `--format` | html, xml, json, text | html | Report format |
| `--include-patterns` | paths | None | File patterns to include |
| `--exclude-patterns` | paths | None | File patterns to exclude |

## Test Organization

```bash
# Discover all tests
python -m apgi_framework.cli organize-tests --discover

# Categorize discovered tests
python -m apgi_framework.cli organize-tests --categorize

# List test categories
python -m apgi_framework.cli organize-tests --list-categories

# List test modules
python -m apgi_framework.cli organize-tests --list-modules

# List available tags
python -m apgi_framework.cli organize-tests --list-tags

# Export test tree to JSON
python -m apgi_framework.cli organize-tests --export-tree test_tree.json
```

## Configuration Commands

### Generate Configuration

```bash
# Generate default configuration
python -m apgi_framework.cli generate-config --output config.json

# Generate minimal configuration
python -m apgi_framework.cli generate-config --template minimal --output minimal.json

# Generate comprehensive configuration
python -m apgi_framework.cli generate-config --template comprehensive --output full.json
```

**Configuration Templates:**

| Template | Description |
| --- | --- |
| `default` | Standard APGI parameters (threshold=3.5, steepness=2.0, n_trials=1000) |
| `minimal` | Minimal configuration for quick testing |
| `comprehensive` | Full configuration with detailed logging and plots |

**Default Configuration includes:**

- APGI Parameters: extero_precision, intero_precision, extero_error, intero_error, somatic_gain, threshold, steepness
- Experimental Config: n_trials, n_participants, random_seed, output_directory, log_level, p3b_threshold, gamma_plv_threshold, bold_z_threshold, pci_threshold, alpha_level, effect_size_threshold, power_threshold

## System Commands

### Validate System

```bash
# Basic system validation
python -m apgi_framework.cli validate-system

# Detailed validation results
python -m apgi_framework.cli validate-system --detailed
```

### Show Status

```bash
# Display system status
python -m apgi_framework.cli status
```

## Parameter Commands

### Set Parameters

```bash
# Set threshold parameter
python -m apgi_framework.cli set-params --threshold 3.5

# Set multiple parameters
python -m apgi_framework.cli set-params --extero-precision 2.0 --intero-precision 1.5 --threshold 4.0

# Set steepness and somatic gain
python -m apgi_framework.cli set-params --steepness 2.0 --somatic-gain 1.3
```

**Parameter Ranges:**

| Parameter | Range | Description |
| --- | --- | --- |
| `--extero-precision` | 0.001-1000 | Exteroceptive precision |
| `--intero-precision` | 0.001-1000 | Interoceptive precision |
| `--threshold` | 0.5-10.0 | Ignition threshold |
| `--steepness` | 0.1-50.0 | Sigmoid steepness |
| `--somatic-gain` | -10.0 to 10.0 | Somatic marker gain |

## Examples

### Basic Usage

```bash
# Run primary falsification test with 1000 trials
python -m apgi_framework.cli run-test primary --trials 1000

# Generate default configuration
python -m apgi_framework.cli generate-config --output my_config.json

# Validate system
python -m apgi_framework.cli validate-system
```

### Advanced Usage

```bash
# Run batch test with parallel execution and custom workers
python -m apgi_framework.cli batch-test --test-paths tests/test_core.py --parallel --max-workers 8 --timeout 600

# Run tests by category with coverage
python -m apgi_framework.cli run-tests --categories unit integration --coverage --coverage-report html

# Analyze test results with trends
python -m apgi_framework.cli test-analysis --trends --days 60 --export trends.json
```

### CI/CD Integration

```bash
# Run unit tests with JSON output
python -m apgi_framework.cli batch-test --markers unit --report test_results.json

# Validate deployment readiness
python -m apgi_framework.cli validate-system

# Generate coverage report
python -m apgi_framework.cli test-coverage --report --format xml

# Re-run only failed tests from previous run
python -m apgi_framework.cli test-results --rerun-failed test_results.json
```

### Research Workflows

```bash
# Run all falsification tests
python -m apgi_framework.cli run-batch --all-tests

# Run with specific parameters
python -m apgi_framework.cli set-params --threshold 3.5 --steepness 2.0
python -m apgi_framework.cli run-test primary --trials 5000 --participants 200

# Analyze failure patterns over time
python -m apgi_framework.cli test-analysis --failures --days 90
```

## Exit Codes

| Code | Meaning | Description |
| --- | --- | --- |
| 0 | Success | Command completed successfully |
| 1 | General Error | Unspecified error occurred |
| 2 | Invalid Usage | Invalid command-line arguments |

## Validation Functions

The CLI includes built-in validation for numeric arguments:

- `trials`: Must be between 100 and 10000
- `participants`: Must be between 10 and 1000
- `threshold`: Must be between 0.5 and 10.0
- `max-workers`: Must be between 1 and 64
- `timeout`: Must be between 1 and 3600 seconds
- `days`: Must be between 1 and 365
- `coverage-threshold`: Must be between 0 and 100
- `precision`: Must be between 0.001 and 1000
- `steepness`: Must be between 0.1 and 50.0
- `somatic-gain`: Must be between -10.0 and 10.0

## Troubleshooting

### Common Issues

**Import errors**: Ensure APGI modules are properly installed (`pip install -e .`)
**Permission errors**: Run with appropriate file system permissions
**Timeout errors**: Increase timeout values for slow tests

### Getting Help

```bash
# Show general help
python -m apgi_framework.cli --help

# Show command-specific help
python -m apgi_framework.cli run-test --help
python -m apgi_framework.cli batch-test --help

# Enable debug logging
python -m apgi_framework.cli --log-level DEBUG run-test primary
```

For more detailed documentation, see the [User Guide](USER-GUIDE.md).
