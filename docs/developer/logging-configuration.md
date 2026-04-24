# Logging Configuration Guide

This guide explains how to configure and customize logging in the APGI Framework.

> **Note**: For a comprehensive logging configuration guide with detailed examples, see [Logging Configuration Guide](logging-configuration-guide.md).

## Overview

The APGI Framework uses a comprehensive logging system with structured logging across 61+ modules. The logging system is designed to be flexible, configurable, and production-ready.

## Default Configuration

### Log Levels

The framework uses standard Python logging levels:

- **DEBUG**: Detailed information for debugging purposes
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened, but the software is still working
- **ERROR**: Serious problem occurred, software cannot perform some function
- **CRITICAL**: Very serious error, the program itself may be unable to continue

### Default Log Format

```text
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example output:

```text
2024-01-16 14:30:22,123 - apgi_framework.core.equation - INFO - APGI equation initialized successfully
```

## Configuration Methods

### 1. Environment Variables

Set logging configuration via environment variables:

```bash
export APGI_LOG_LEVEL=INFO
export APGI_LOG_FORMAT=detailed
export APGI_LOG_FILE=apgi.log
export APGI_LOG_MAX_SIZE=10MB
export APGI_LOG_BACKUP_COUNT=5
```

### 2. Configuration File

Create a `logging_config.json` file:

```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(funcName)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "apgi.log",
            "maxBytes": 10485760,
            "backupCount": 5
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "apgi_errors.log",
            "maxBytes": 10485760,
            "backupCount": 3
        }
    },
    "loggers": {
        "apgi_framework": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": false
        },
        "apgi_framework_gui": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        }

    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
```

### 3. Programmatic Configuration

Configure logging in your Python code:

```python
import logging
import logging.config
from pathlib import Path

def setup_logging(config_file: str = None, log_level: str = "INFO"):
    """Setup logging configuration."""
    
    if config_file and Path(config_file).exists():
        # Load from file
        with open(config_file, 'r') as f:
            logging.config.dictConfig(json.load(f))
    else:
        # Default configuration
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('apgi.log', mode='a')
            ]
        )

# Usage
setup_logging(log_level="DEBUG")
logger = logging.getLogger(__name__)
logger.info("Logging configured successfully")
```

## Module-Specific Logging

### Core Framework Modules

```python
from apgi_framework.core.equation import APGIEquation
import logging

# Get module-specific logger
logger = logging.getLogger('apgi_framework.core.equation')

# Use structured logging
logger.info("Equation initialized", extra={
    'parameters': {'alpha': 0.5, 'beta': 0.3},
    'timestamp': '2024-01-16T14:30:22Z'
})
```

### GUI Applications

```python
from apgi_framework.gui.parameter_estimation import ParameterEstimationGUI
import logging

# GUI-specific logger
gui_logger = logging.getLogger('apgi_framework.gui')

# Log user actions
gui_logger.info("User clicked launch button", extra={
    'action': 'launch',
    'component': 'parameter_estimation',
    'user_id': 'session_123'
})
```

### Experiment Modules

```python
from apgi_framework.experiment.runner import ExperimentRunner
import logging

exp_logger = logging.getLogger('apgi_framework.experiment')

# Log experiment progress
exp_logger.info("Experiment started", extra={
    'experiment_id': 'exp_001',
    'participant_id': 'p001',
    'condition': 'baseline'
})
```

## Log File Management

### Rotation Configuration

Configure automatic log rotation:

```python
from logging.handlers import RotatingFileHandler
import logging

# Rotate at 10MB, keep 5 backups
handler = RotatingFileHandler(
    'apgi.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

### Time-based Rotation

```python
from logging.handlers import TimedRotatingFileHandler

# Rotate daily at midnight, keep 30 days
handler = TimedRotatingFileHandler(
    'apgi.log',
    when='midnight',
    interval=1,
    backupCount=30
)
```

## Performance Considerations

### Async Logging

For high-performance applications:

```python
import logging.handlers
import queue
import threading

class AsyncHandler(logging.handlers.QueueHandler):
    """Async logging handler for better performance."""
    
    def __init__(self, queue):
        super().__init__(queue)
        self.queue = queue
        
    def emit(self, record):
        self.queue.put_nowait(record)

# Setup async logging
log_queue = queue.Queue()
async_handler = AsyncHandler(log_queue)

# Background thread to process logs
def log_worker():
    while True:
        record = log_queue.get()
        logger = logging.getLogger(record.name)
        logger.handle(record)

threading.Thread(target=log_worker, daemon=True).start()
```

### Conditional Logging

Reduce logging overhead in production:

```python
import os
import logging

# Only log debug in development
if os.getenv('APGI_ENV') == 'development':
    logging.getLogger('apgi_framework').setLevel(logging.DEBUG)
else:
    logging.getLogger('apgi_framework').setLevel(logging.INFO)
```

## Security Considerations

### Sensitive Data Filtering

```python
import logging
from logging import Filter

class SensitiveDataFilter(Filter):
    """Filter to remove sensitive data from logs."""
    
    SENSITIVE_PATTERNS = [
        'password', 'token', 'api_key', 'secret',
        'ssn', 'credit_card', 'personal_data'
    ]
    
    def filter(self, record):
        message = record.getMessage()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message.lower():
                record.msg = message.replace(pattern, '[REDACTED]')
                record.args = ()
                break
        return True

# Apply filter
logger = logging.getLogger('apgi_framework')
logger.addFilter(SensitiveDataFilter())
```

## Troubleshooting

### Common Issues

1. **No log output**: Check log level configuration
2. **Missing log files**: Verify file permissions and paths
3. **Performance issues**: Consider async logging or higher log levels
4. **Large log files**: Implement log rotation

### Debug Logging

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug for specific module
logging.getLogger('apgi_framework.core').setLevel(logging.DEBUG)

# Enable debug for all modules
logging.getLogger('apgi_framework').setLevel(logging.DEBUG)
```

## Integration with External Systems

### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
import pythonjsonlogger
import logging

# JSON formatter for Logstash
json_formatter = pythonjsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)

# Logstash handler (example)
logstash_handler = logging.handlers.SocketHandler(
    'localhost', 5959
)
logstash_handler.setFormatter(json_formatter)

logger.addHandler(logstash_handler)
```

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# Configure Sentry with logging
sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[sentry_logging]
)
```

## Best Practices

1. **Use structured logging**: Include context and metadata
2. **Set appropriate log levels**: Avoid excessive debug logging in production
3. **Implement log rotation**: Prevent disk space issues
4. **Filter sensitive data**: Protect user privacy
5. **Monitor log performance**: Use async logging for high-throughput applications
6. **Centralize configuration**: Use environment variables or config files
7. **Test logging configuration**: Verify logs are generated as expected

## Examples

### Basic Usage

```python
import logging
from apgi_framework.core.equation import APGIEquation

# Get logger
logger = logging.getLogger(__name__)

# Basic logging
logger.info("Starting APGI equation calculation")
logger.debug("Parameters: alpha=0.5, beta=0.3")
logger.warning("Using default values for missing parameters")
logger.error("Failed to calculate equation: division by zero")
```

### Structured Logging

```python
logger.info("Experiment completed", extra={
    'experiment_id': 'exp_001',
    'duration_seconds': 120.5,
    'participant_id': 'p001',
    'condition': 'treatment',
    'success': True
})
```

### Exception Logging

```python
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Failed to execute risky operation", extra={
        'operation': 'risky_operation',
        'error_type': type(e).__name__
    })
```

This logging configuration guide provides comprehensive coverage for all APGI Framework logging needs, from basic setup to advanced production configurations.

## Quick Reference

### Environment Variables

```bash
export APGI_LOG_LEVEL=DEBUG          # Set global log level
export APGI_GUI_LOG_LEVEL=INFO       # Set GUI-specific log level
export APGI_LOG_FILE=logs/apgi.log   # Set log file path
```

### Common Logger Usage

```python
from apgi_framework.logging.standardized_logging import get_logger

logger = get_logger(__name__)
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)  # Include traceback
```

### Configuration Files

- Main logging config: `apgi_framework/logging/`
- User config: Create `logging.conf` in project root
- Environment-specific: Use `.env` files

For detailed configuration examples and advanced usage, see the [comprehensive logging guide](logging-configuration-guide.md).
