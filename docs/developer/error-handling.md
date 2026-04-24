# Error Handling Quick Reference Guide

## Quick Start

### Initialize Error Handling (Application Startup)

```python
from apgi_framework.falsification.error_handling_wrapper import initialize_error_handling

# Call once at application startup

initialize_error_handling()
```python

### Using the Decorator

```python
from apgi_framework.falsification.error_handling_wrapper import with_error_handling

@with_error_handling(validate_params=True, enable_retry=True, log_errors=True, max_retries=3)
def my_test_function(n_trials: int, n_participants: int):
    # Your test implementation
    pass
```python

### Using the Wrapper Class

```python
from apgi_framework.falsification.error_handling_wrapper import ErrorHandlingTestWrapper
from apgi_framework.falsification.primary_falsification_test import PrimaryFalsificationTest

# Create and wrap controller

controller = PrimaryFalsificationTest()
wrapped = ErrorHandlingTestWrapper(controller)

# Use normally - errors handled automatically

result = wrapped.run_falsification_test(n_trials=100, n_participants=20)

# Check for errors

summary = wrapped.get_error_summary()
if summary['total_errors'] > 0:
    print(f"Encountered {summary['total_errors']} errors")
    print(f"Recovery success rate: {summary['recovery_success_rate']}")
```json

## Common Error Types

 | Error Type | Description | Auto-Retry | Recovery Strategy |
 | ------------ | ------------- | ------------ | ------------------- |
 | ValidationError | Invalid parameters | No | Fix parameters |
 | ConfigurationError | Invalid config | No | Fix configuration |
 | SimulationError | Simulation failure | Yes | Reset random seed |
 | StatisticalError | Statistical issue | No | Check sample size |
 | MemoryError | Out of memory | No | Reduce data size |
 | IOError/OSError | File system error | Yes | Create directories |

## Error Handling Parameters

### Decorator Parameters

```python
@with_error_handling(
    validate_params=True,    # Validate parameters before execution
    enable_retry=True,       # Enable automatic retry
    log_errors=True,         # Log errors to file and console
    max_retries=3           # Maximum retry attempts
)
```python

### Retry Configuration

```python
from apgi_framework.validation.error_recovery import RetryConfig

config = RetryConfig(
    max_attempts=3,                    # Maximum retry attempts
    initial_delay=1.0,                 # Initial delay in seconds
    backoff_factor=2.0,                # Exponential backoff multiplier
    max_delay=10.0,                    # Maximum delay between retries
    retriable_exceptions=[             # Exceptions that trigger retry
        SimulationError,
        IOError,
        OSError,
        RuntimeError
    ]
)
```python

## Checking Error Status

### Get Error Handling System Status

```python
from apgi_framework.falsification.error_handling_wrapper import get_error_handling_status

status = get_error_handling_status()
print(f"Logging configured: {status['logging_configured']}")
print(f"Recovery manager active: {status['recovery_manager_active']}")
print(f"Total errors logged: {status['total_errors_logged']}")
```json

### Get Error Summary from Wrapper

```python
summary = wrapped_controller.get_error_summary()

# Available fields

# - total_errors: Total number of errors

# - error_types: Dictionary of error types and counts

# - error_methods: Dictionary of methods and error counts

# - recovery_attempts: Number of recovery attempts

# - successful_recoveries: Number of successful recoveries

# - failed_recoveries: Number of failed recoveries

# - recovery_success_rate: Success rate as percentage string

# - most_common_error: Most frequent error type

# - most_problematic_method: Method with most errors

```python

## Custom Recovery Strategies

### Register Custom Recovery

```python
from apgi_framework.validation.error_recovery import get_recovery_manager
from apgi_framework.exceptions import SimulationError

def my_recovery_strategy(error: Exception, context: dict):
    """Custom recovery logic"""
    # Implement recovery
    # Return None to signal retry
    # Return a value to use as result
    return None

manager = get_recovery_manager()
manager.register_recovery_strategy(SimulationError, my_recovery_strategy)
```python

## Logging

### Log Locations

- Console: INFO level and above
- File: `logs/falsification_tests_YYYYMMDD.log` (DEBUG level and above)

### Log Levels

- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

### Manual Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```json

## Error Report Generation

### Generate Error Report

```python
from apgi_framework.falsification.error_handling_wrapper import create_error_report

error_report = create_error_report(
    test_name="my_test",
    error=exception_object,
    context={'param1': value1, 'param2': value2}
)

print(error_report)  # Formatted error report with troubleshooting
```python

### Export Error Log

```python
wrapped_controller.export_error_log('error_log.json')
```json

## Troubleshooting Common Issues

### ValidationError: Invalid Parameters

```python

# Problem: Negative or zero values

result = test.run_test(n_trials=-10)  # ❌ Error

# Solution: Use positive values

result = test.run_test(n_trials=100)  # ✅ Correct
```python

### SimulationError: Simulation Failed

```python

# The system will automatically

# 1. Reset random seed

# 2. Retry up to max_retries times

# 3. Log each attempt

# If all retries fail, check

# - Simulation parameters are reasonable

# - Input data is not corrupted

# - System has sufficient resources

```python

### MemoryError: Out of Memory

```python

# Problem: Too much data

result = test.run_test(n_trials=1000000)  # ❌ May run out of memory

# Solution: Reduce data size

result = test.run_test(n_trials=10000)  # ✅ More reasonable
```python

### IOError: File Not Found

```python

# The system will automatically

# 1. Create missing directories

# 2. Retry the operation

# If it still fails, check

# - File paths are correct

# - Permissions allow read/write

# - Disk space is available

```python

## Best Practices

1. **Always initialize error handling at startup**

   ```python
   initialize_error_handling()
```python

2. **Use the decorator for all test methods**

   ```python
   @with_error_handling(validate_params=True, enable_retry=True)
   def run_test(...):
       pass
   ```

1. **Check error summaries after test runs**

   ```python
   summary = wrapped.get_error_summary()
   if summary['total_errors'] > 0:
       print("Error occurred")
       print(summary)
   ```

2. **Export error logs for analysis**

   ```python
   wrapped.export_error_log('errors.json')
   print("Error log exported")
   ```

3. **Review log files regularly**
   - Check `logs/` directory
   - Look for patterns in errors
   - Address recurring issues

4. **Use appropriate retry counts**
   - Transient failures: 3-5 retries
   - Non-transient: 0-1 retries

5. **Validate parameters before running tests**

   ```python
   from apgi_framework.validation import get_validator

   validator = get_validator()
   result = validator.validate_experimental_config(n_trials=100)
   if not result.is_valid:
       print(result.get_message())
   ```python

## Performance Considerations

- Error handling adds minimal overhead (~1-2% for successful operations)
- Retry mechanisms only activate on failures
- Logging to file is asynchronous and non-blocking
- Error statistics tracking uses minimal memory

## Getting Help

If you encounter persistent errors:

1. Check the error report for troubleshooting guidance
2. Review logs in `logs/` directory
3. Check error statistics for patterns
4. Consult documentation in `docs/`
5. Review examples in `examples/`
6. Check test files for proper usage patterns

## Example: Complete Error Handling Setup

```python
from apgi_framework.falsification.error_handling_wrapper import (
    initialize_error_handling,
    ErrorHandlingTestWrapper,
    get_error_handling_status
)
from apgi_framework.falsification.primary_falsification_test import PrimaryFalsificationTest

# 1. Initialize error handling system

initialize_error_handling()

# 2. Check system status

status = get_error_handling_status()
print(f"Error handling ready: {status['recovery_manager_active']}")

# 3. Create and wrap test controller

controller = PrimaryFalsificationTest()
wrapped = ErrorHandlingTestWrapper(controller)

# 4. Run test (errors handled automatically)

try:
    result = wrapped.run_falsification_test(n_trials=100, n_participants=20)
    print(f"Test completed: {result.test_id}")
except Exception as e:
    print(f"Test failed after all retries: {e}")

# 5. Check error summary

summary = wrapped.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"Recovery success rate: {summary['recovery_success_rate']}")

# 6. Export error log if needed

if summary['total_errors'] > 0:
    wrapped.export_error_log('test_errors.json')
```json

## Quick Checklist

- [ ] Initialize error handling at startup
- [ ] Use `@with_error_handling` decorator on test methods
- [ ] Wrap test controllers with `ErrorHandlingTestWrapper`
- [ ] Check error summaries after test runs
- [ ] Review log files regularly
- [ ] Export error logs for analysis
- [ ] Register custom recovery strategies if needed
- [ ] Monitor recovery success rates
- [ ] Address recurring errors
- [ ] Keep logs directory clean (archive old logs)
