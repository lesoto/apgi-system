# Logging Configuration Guide

## Overview

The APGI Framework uses a comprehensive logging system to help with debugging, monitoring, and understanding system behavior. This guide explains how to configure and use the logging system effectively.

## Logging Architecture

The framework uses Python's built-in `logging` module with standardized configuration across all components.

### Key Components

- **Centralized Logging**: `apgi_framework/logging/centralized_logging.py`
- **Standardized Logging**: `apgi_framework/logging/standardized_logging.py`
- **Log Files**: Stored in `logs/` directory
- **Configuration**: Environment variables and code-based configuration

## Log Levels

The framework uses standard Python logging levels:

| Level | Numeric Value | When to Use |
| ------- | --------------- | ------------- |
| `DEBUG` | 10 | Detailed diagnostic information |
| `INFO` | 20 | General information about program execution |
| `WARNING` | 30 | Something unexpected happened, but the program continues |
| `ERROR` | 40 | A serious problem occurred |
| `CRITICAL` | 50 | A very serious error occurred |

## Configuration Methods

### 1. Environment Variables

Set logging level using environment variables:

```bash
# Set global logging level
export APGI_LOG_LEVEL=DEBUG

# Set specific module logging levels
export APGI_GUI_LOG_LEVEL=INFO
export APGI_ANALYSIS_LOG_LEVEL=WARNING
```

### 2. Code Configuration

```python
import logging
from apgi_framework.logging.standardized_logging import get_logger, configure_logging

# Configure logging for the entire application
configure_logging(
    level=logging.INFO,
    log_file="logs/apgi_application.log",
    console_output=True
)

# Get a logger for your module
logger = get_logger(__name__)

# Use the logger
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

### 3. Configuration File

Create a `logging.conf` file in your project root:

```ini
[loggers]
keys=root,apgi

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=standardFormatter

[logger_root]
level=WARNING
handlers=consoleHandler

[logger_apgi]
level=INFO
handlers=consoleHandler,fileHandler
qualname=apgi_framework
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=standardFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=standardFormatter
args=('logs/apgi.log',)

[formatter_standardFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

## Module-Specific Configuration

### GUI Components

```python
# In GUI components
from apgi_framework.logging.standardized_logging import get_logger

logger = get_logger(__name__)

# Log user interactions
logger.info("User clicked start button")
logger.debug(f"Parameter values: {parameters}")

# Log errors with context
try:
    result = process_data()
except Exception as e:
    logger.error(f"Data processing failed: {e}", exc_info=True)
```

### Analysis Modules

```python
# In analysis modules
logger = get_logger(__name__)

# Log analysis progress
logger.info("Starting parameter estimation")
logger.info(f"Processing {len(data)} data points")

# Log results
logger.info(f"Analysis completed in {duration:.2f}s")
logger.debug(f"Results: {results}")
```

### Experiment Runners

```python
# In experiment runners
logger = get_logger(__name__)

# Log experiment setup
logger.info(f"Starting experiment: {experiment_name}")
logger.info(f"Parameters: n_participants={n_participants}, n_trials={n_trials}")

# Log progress
logger.info(f"Completed trial {trial_num}/{total_trials}")

# Log completion
logger.info(f"Experiment completed successfully")
```

## Log File Management

### Default Log Files

- `logs/apgi_framework.log` - Main application log
- `logs/gui_application.log` - GUI-specific events
- `logs/analysis_engine.log` - Analysis and computation logs
- `logs/experiment_runner.log` - Experiment execution logs
- `logs/error.log` - Error-only log for quick debugging

### Log Rotation

Configure automatic log rotation to prevent large files:

```python
import logging.handlers

# Rotate logs when they reach 10MB, keep 5 backup files
handler = logging.handlers.RotatingFileHandler(
    'logs/apgi.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Time-based Rotation

```python
import logging.handlers

# Rotate logs daily, keep 30 days of logs
handler = logging.handlers.TimedRotatingFileHandler(
    'logs/apgi.log',
    when='midnight',
    interval=1,
    backupCount=30
)
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# Good examples
logger.debug("Entering function with parameters: %s", params)
logger.info("User started new experiment session")
logger.warning("Parameter value outside recommended range: %s", value)
logger.error("Failed to load configuration file: %s", filename)
logger.critical("Database connection lost, shutting down")

# Avoid
logger.info("x = 5")  # Too verbose for INFO
logger.error("User clicked button")  # Not an error
```

### 2. Include Context

```python
# Good - includes context
logger.error("Failed to process participant %s data: %s", participant_id, error)

# Less helpful
logger.error("Processing failed")
```

### 3. Use Structured Logging

```python
# Include structured data
logger.info("Experiment completed", extra={
    'experiment_id': exp_id,
    'duration': duration,
    'participant_count': len(participants),
    'success_rate': success_rate
})
```

### 4. Handle Exceptions Properly

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.warning("Expected issue occurred: %s", e)
    # Handle gracefully
except Exception as e:
    logger.error("Unexpected error in operation", exc_info=True)
    # exc_info=True includes the full traceback
    raise
```

## Debugging with Logs

### 1. Temporary Debug Logging

```python
# Temporarily increase logging level for debugging
import logging
logging.getLogger('apgi_framework.analysis').setLevel(logging.DEBUG)

# Your code here

# Reset to normal level
logging.getLogger('apgi_framework.analysis').setLevel(logging.INFO)
```

### 2. Conditional Debug Logging

```python
import os

DEBUG_MODE = os.getenv('APGI_DEBUG', 'false').lower() == 'true'

if DEBUG_MODE:
    logger.debug("Debug mode enabled - extra information: %s", debug_data)
```

### 3. Performance Logging

```python
import time

start_time = time.time()
# Your operation here
duration = time.time() - start_time

if duration > 1.0:  # Log slow operations
    logger.warning("Slow operation detected: %s took %.2fs", operation_name, duration)
else:
    logger.debug("Operation %s completed in %.2fs", operation_name, duration)
```

## Common Configuration Examples

### Development Environment

```python
# Development - verbose logging to console
configure_logging(
    level=logging.DEBUG,
    console_output=True,
    log_file=None  # No file logging in development
)
```

### Production Environment

```python
# Production - minimal console output, detailed file logging
configure_logging(
    level=logging.INFO,
    console_output=False,
    log_file="logs/apgi_production.log",
    max_file_size=50*1024*1024,  # 50MB
    backup_count=10
)
```

### Testing Environment

```python
# Testing - capture all logs for test analysis
configure_logging(
    level=logging.DEBUG,
    console_output=False,
    log_file="logs/test_run.log"
)
```

## Monitoring and Alerting

### Log Analysis

Use tools to analyze logs:

```bash
# Find errors in the last hour
grep "ERROR" logs/apgi.log | grep "$(date '+%Y-%m-%d %H')"

# Count warnings by type
grep "WARNING" logs/apgi.log | cut -d'-' -f4 | sort | uniq -c

# Monitor real-time logs
tail -f logs/apgi.log | grep "ERROR\|WARNING"
```

### Integration with Monitoring Systems

```python
# Example: Send critical errors to monitoring system
import logging

class MonitoringHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            # Send to monitoring system
            send_alert(record.getMessage())

# Add to logger
logger.addHandler(MonitoringHandler())
```

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check log level configuration
2. **Log files not created**: Verify directory permissions
3. **Too many log files**: Configure log rotation
4. **Performance impact**: Reduce log level in production

### Debug Logging Configuration

```python
# Check current logging configuration
import logging

# List all loggers
for name in logging.Logger.manager.loggerDict:
    logger = logging.getLogger(name)
    print(f"Logger: {name}, Level: {logger.level}, Handlers: {len(logger.handlers)}")

# Check specific logger
logger = logging.getLogger('apgi_framework')
print(f"Effective level: {logger.getEffectiveLevel()}")
print(f"Handlers: {[h.__class__.__name__ for h in logger.handlers]}")
```

## Summary

The APGI Framework logging system provides:

- **Centralized configuration** for consistent logging across modules
- **Multiple output options** (console, files, external systems)
- **Flexible log levels** for different environments
- **Structured logging** for better analysis
- **Performance considerations** for production use

For most users, the default configuration works well. Advanced users can customize logging behavior using the methods described in this guide.
