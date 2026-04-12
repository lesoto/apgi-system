"""
Production Logging Configuration

Provides optimized logging configuration for production environments
including structured logging, log levels, and performance optimization.
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml


class ProductionLogger:
    """
    Production-optimized logging configuration.

    Features:
    - Structured JSON logging for production
    - Configurable log levels per module
    - Performance-optimized formatters
    - Log rotation and archival
    - Sensitive data filtering
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize production logger.

        Args:
            config_path: Path to logging configuration file
        """
        self.config_path = config_path or "config/logging.yaml"
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

    def get_production_config(self, log_level: str = "INFO") -> Dict[str, Any]:
        """
        Get production logging configuration.

        Args:
            log_level: Global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Returns:
            Logging configuration dictionary
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            # Formatters
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
                },
                "simple": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
                },
            },
            # Filters
            "filters": {
                "sensitive_data": {
                    "()": "api.logging.filters.SensitiveDataFilter",
                },
                "performance": {
                    "()": "api.logging.filters.PerformanceFilter",
                },
            },
            # Handlers
            "handlers": {
                # Console handler for development
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
                # File handler for general logs
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "formatter": "json",
                    "filename": str(self.log_dir / "apgi.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf8",
                    "filters": ["sensitive_data"],
                },
                # Error file handler
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "json",
                    "filename": str(self.log_dir / "apgi_errors.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf8",
                    "filters": ["sensitive_data"],
                },
                # Performance file handler
                "performance_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": str(self.log_dir / "apgi_performance.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 3,
                    "encoding": "utf8",
                    "filters": ["performance"],
                },
                # Security file handler
                "security_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "json",
                    "filename": str(self.log_dir / "apgi_security.log"),
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 10,
                    "encoding": "utf8",
                    "filters": ["sensitive_data"],
                },
            },
            # Loggers
            "loggers": {
                # Root logger
                "": {
                    "level": log_level,
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                # API loggers
                "api": {
                    "level": log_level,
                    "handlers": ["file", "error_file"],
                    "propagate": False,
                },
                # Authentication logger (security sensitive)
                "api.auth": {
                    "level": "INFO",
                    "handlers": ["security_file", "file"],
                    "propagate": False,
                },
                # Performance logger
                "api.performance": {
                    "level": "INFO",
                    "handlers": ["performance_file"],
                    "propagate": False,
                },
                # Database logger
                "api.database": {
                    "level": "WARNING",  # Reduce database verbosity
                    "handlers": ["file"],
                    "propagate": False,
                },
                # APGI system loggers
                "apgi_system": {
                    "level": "INFO",  # Reduce system verbosity in production
                    "handlers": ["file"],
                    "propagate": False,
                },
                # GUI logger
                "apgi_gui": {
                    "level": "WARNING",  # Only warnings and errors from GUI
                    "handlers": ["file"],
                    "propagate": False,
                },
                # Third-party libraries (reduce verbosity)
                "urllib3": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False,
                },
                "requests": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False,
                },
                "sqlalchemy": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False,
                },
                "redis": {
                    "level": "WARNING",
                    "handlers": ["file"],
                    "propagate": False,
                },
            },
            # Root logger
            "root": {
                "level": log_level,
                "handlers": ["console", "file"],
            },
        }

    def configure_production_logging(self, log_level: str = "INFO") -> None:
        """
        Configure production logging.

        Args:
            log_level: Global log level
        """
        config = self.get_production_config(log_level)
        logging.config.dictConfig(config)

        # Log successful configuration
        logger = logging.getLogger(__name__)
        logger.info(
            "Production logging configured",
            extra={
                "log_level": log_level,
                "log_dir": str(self.log_dir),
                "config_file": self.config_path,
            },
        )

    def configure_development_logging(self, log_level: str = "DEBUG") -> None:
        """
        Configure development logging with more verbosity.

        Args:
            log_level: Global log level
        """
        config = self.get_production_config(log_level)

        # Enable more verbose logging for development
        config["loggers"]["apgi_system"]["level"] = "DEBUG"
        config["loggers"]["api"]["level"] = "DEBUG"
        config["loggers"]["api.database"]["level"] = "INFO"

        logging.config.dictConfig(config)

        logger = logging.getLogger(__name__)
        logger.info("Development logging configured with DEBUG level")


class SensitiveDataFilter(logging.Filter):
    """Filter to mask sensitive data in logs."""

    SENSITIVE_PATTERNS = [
        ("password", "***MASKED***"),
        ("token", "***MASKED***"),
        ("secret", "***MASKED***"),
        ("key", "***MASKED***"),
        ("authorization", "***MASKED***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg = record.msg.lower()
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                if pattern in msg:
                    record.msg = record.msg.replace(pattern, replacement)
                    break

        return True


class PerformanceFilter(logging.Filter):
    """Filter for performance-related logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance context to log records."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg_lower = record.msg.lower()
            if any(
                keyword in msg_lower for keyword in ["slow", "timeout", "performance", "duration"]
            ):
                record.performance = True
            else:
                record.performance = False

        return True


def setup_logging(
    environment: str = "production", log_level: str = "INFO", config_file: Optional[str] = None
) -> None:
    """
    Setup logging based on environment.

    Args:
        environment: 'production' or 'development'
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        config_file: Optional custom logging configuration file
    """
    if config_file and Path(config_file).exists():
        # Load custom configuration
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # Use standard configuration
        logger_config = ProductionLogger(config_file)

        if environment.lower() == "production":
            # Guard against DEBUG level in production to prevent data leaks
            managed_log_level = "INFO" if log_level.upper() == "DEBUG" else log_level
            logger_config.configure_production_logging(managed_log_level)
        else:
            logger_config.configure_development_logging(log_level)

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized for {environment} environment",
        extra={"environment": environment, "log_level": log_level, "python_version": sys.version},
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with optimized configuration.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Performance monitoring decorator
def log_performance(func_name: Optional[str] = None) -> Callable[..., Any]:
    """
    Decorator to log function performance.

    Args:
        func_name: Optional custom function name
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            name = func_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger = logging.getLogger("api.performance")
                logger.info(
                    f"Function executed: {name}",
                    extra={
                        "function": name,
                        "duration_ms": duration * 1000,
                        "success": True,
                        "performance": True,
                    },
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger = logging.getLogger("api.performance")
                logger.error(
                    f"Function failed: {name}",
                    extra={
                        "function": name,
                        "duration_ms": duration * 1000,
                        "success": False,
                        "error": str(e),
                        "performance": True,
                    },
                )

                raise

        return wrapper

    return decorator
