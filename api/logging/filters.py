"""
Logging Filters

Custom logging filters for production use including
sensitive data masking and performance tracking.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any


class SensitiveDataFilter(logging.Filter):
    """
    Filter to mask sensitive data in log messages.

    Masks passwords, tokens, API keys, and other sensitive information
    while preserving the rest of the log message structure.
    """

    # Patterns for sensitive data (regex patterns)
    SENSITIVE_PATTERNS: List[Tuple[str, str]] = [
        # Passwords
        (r'password["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'password":"***MASKED***'),
        (r"'password'\s*:\s*'[^']+'", "'password':'***MASKED***'"),
        (r"password\s*=\s*[^\s]+", "password=***MASKED***"),
        # Tokens and API keys
        (r'token["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'token":"***MASKED***'),
        (r"'token'\s*:\s*'[^']+'", "'token':'***MASKED***'"),
        (r'api_key["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'api_key":"***MASKED***'),
        (r"'api_key'\s*:\s*'[^']+'", "'api_key':'***MASKED***'"),
        # Authorization headers
        (r'authorization["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'authorization":"***MASKED***'),
        (r"'authorization'\s*:\s*'[^']+'", "'authorization':'***MASKED***'"),
        (r"Bearer\s+[A-Za-z0-9\-_\.]+", "Bearer ***MASKED***"),
        # Secrets and keys
        (r'secret["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'secret":"***MASKED***'),
        (r"'secret'\s*:\s*'[^']+'", "'secret':'***MASKED***'"),
        (r'private_key["\s]*[:=]["\s]*["\s]*[^"\\s]+', 'private_key":"***MASKED***'),
        # Database connection strings (basic pattern)
        (r"mysql://[^:]+:[^@]+@", "mysql://***:***@"),
        (r"postgresql://[^:]+:[^@]+@", "postgresql://***:***@"),
        (r"mongodb://[^:]+:[^@]+@", "mongodb://***:***@"),
    ]

    def __init__(self, name: str = ""):
        """
        Initialize sensitive data filter.

        Args:
            name: Filter name
        """
        super().__init__(name)
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in self.SENSITIVE_PATTERNS
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter sensitive data from log record.

        Args:
            record: Log record to filter

        Returns:
            True (always allows the record, but modifies it)
        """
        if hasattr(record, "msg"):
            message = str(record.msg)

            # Apply all patterns
            for pattern, replacement in self.patterns:
                message = pattern.sub(replacement, message)

            record.msg = message

        # Also filter args if present
        if hasattr(record, "args") and record.args:
            filtered_args: List[Any] = []
            for arg in record.args:
                if isinstance(arg, str):
                    filtered_arg = arg
                    for pattern, replacement in self.patterns:
                        filtered_arg = pattern.sub(replacement, filtered_arg)
                    filtered_args.append(filtered_arg)
                else:
                    filtered_args.append(arg)
            record.args = tuple(filtered_args)

        return True


class PerformanceFilter(logging.Filter):
    """
    Filter for performance-related logging.

    Adds performance metadata to log records and can filter
    based on performance characteristics.
    """

    def __init__(self, name: str = "", slow_threshold_ms: float = 1000.0):
        """
        Initialize performance filter.

        Args:
            name: Filter name
            slow_threshold_ms: Threshold in milliseconds to mark as slow
        """
        super().__init__(name)
        self.slow_threshold_ms = slow_threshold_ms

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add performance metadata to log record.

        Args:
            record: Log record to enhance

        Returns:
            True (always allows the record)
        """
        # Check if this is a performance-related log
        message = str(record.msg).lower() if hasattr(record, "msg") else ""

        performance_keywords = [
            "slow",
            "timeout",
            "duration",
            "performance",
            "latency",
            "response_time",
            "execution_time",
            "processing_time",
        ]

        is_performance = any(keyword in message for keyword in performance_keywords)

        # Add performance metadata
        record.is_performance = is_performance
        record.slow_threshold_ms = self.slow_threshold_ms

        # Check if duration information is available
        if hasattr(record, "duration_ms"):
            record.is_slow = record.duration_ms > self.slow_threshold_ms
        else:
            record.is_slow = False

        return True


class ContextFilter(logging.Filter):
    """
    Filter to add contextual information to log records.

    Adds request ID, user ID, session ID, and other context
    information to log records for better tracing.
    """

    def __init__(self, name: str = ""):
        """
        Initialize context filter.

        Args:
            name: Filter name
        """
        super().__init__(name)
        self._context: Dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """
        Set context information.

        Args:
            **kwargs: Context key-value pairs
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context information."""
        self._context.clear()

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context information to log record.

        Args:
            record: Log record to enhance

        Returns:
            True (always allows the record)
        """
        # Add context to record
        for key, value in self._context.items():
            setattr(record, key, value)

        return True


class LevelFilter(logging.Filter):
    """
    Filter to control log levels based on conditions.

    Can filter logs based on time of day, source module,
    or other custom conditions.
    """

    def __init__(self, name: str = "", min_level: int = logging.INFO):
        """
        Initialize level filter.

        Args:
            name: Filter name
            min_level: Minimum log level to allow
        """
        super().__init__(name)
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter based on log level.

        Args:
            record: Log record to filter

        Returns:
            True if record level meets minimum, False otherwise
        """
        return record.levelno >= self.min_level


class ModuleFilter(logging.Filter):
    """
    Filter to control logging from specific modules.

    Can include or exclude logs from specific modules
    based on configuration.
    """

    def __init__(
        self,
        name: str = "",
        included_modules: Optional[List[str]] = None,
        excluded_modules: Optional[List[str]] = None,
    ):
        """
        Initialize module filter.

        Args:
            name: Filter name
            included_modules: List of modules to include (None = all)
            excluded_modules: List of modules to exclude
        """
        super().__init__(name)
        self.included_modules = included_modules
        self.excluded_modules = excluded_modules or []

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter based on module name.

        Args:
            record: Log record to filter

        Returns:
            True if module is allowed, False otherwise
        """
        module_name = record.name

        # Check exclusions first
        if any(module_name.startswith(excluded) for excluded in self.excluded_modules):
            return False

        # Check inclusions if specified
        if self.included_modules:
            return any(module_name.startswith(included) for included in self.included_modules)

        # If no inclusions specified, allow all non-excluded
        return True


# Global context filter instance
_context_filter = ContextFilter("global_context")


def get_context_filter() -> ContextFilter:
    """
    Get the global context filter instance.

    Returns:
        Global ContextFilter instance
    """
    return _context_filter


def set_log_context(**kwargs: Any) -> None:
    """
    Set global logging context.

    Args:
        **kwargs: Context key-value pairs
    """
    _context_filter.set_context(**kwargs)


def clear_log_context() -> None:
    """Clear global logging context."""
    _context_filter.clear_context()
