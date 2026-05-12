#!/usr/bin/env python3
"""
Comprehensive tests for critical Utils modules with lowest coverage.

Tests cover:
- Error handling system
- Data validation utilities
- Configuration management
- Performance profiling
- Cache management
- Circuit breaker utilities
"""

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import pytest

# Import utils modules we're testing
try:
    from utils.cache_manager import CacheManager
    from utils.circuit_breaker_utils import (
        CircuitBreaker,
        CircuitBreakerException,
        CircuitBreakerState,
    )
    from utils.config_manager import ConfigManager
    from utils.data_validation import DataValidator, ValidationConfig
    from utils.error_handler import (
        APGIError,
        ErrorCategory,
        ErrorHandler,
        ErrorInfo,
        ErrorSeverity,
    )
    from utils.performance_profiler import PerformanceProfiler

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


# Mock implementations for missing functionality
@dataclass
class CacheStats:
    """Mock cache statistics class."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    memory_usage_mb: float = 0.0

    def update_hit_rate(self):
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests


class CircuitBreakerError(CircuitBreakerException):
    """Mock circuit breaker error."""

    pass


@dataclass
class ConfigLoadError(Exception):
    """Mock config load error."""

    message: str
    file_path: Optional[str] = None


@dataclass
class ConfigValidationError(Exception):
    """Mock config validation error."""

    message: str
    field: Optional[str] = None
    value: Optional[Any] = None


class OutlierDetector:
    """Mock outlier detector."""

    def __init__(self, threshold: float = 3.0):
        self.threshold = threshold

    def detect_outliers(self, data: np.ndarray) -> np.ndarray:
        """Detect outliers in data."""
        if len(data) < 3:
            return np.array([False] * len(data))

        mean = np.mean(data)
        std = np.std(data)
        z_scores = np.abs((data - mean) / std)
        return z_scores > self.threshold


class SignalQualityAnalyzer:
    """Mock signal quality analyzer."""

    def __init__(self, sampling_rate: float = 1000.0):
        self.sampling_rate = sampling_rate

    def analyze_quality(self, signal: np.ndarray) -> dict:
        """Analyze signal quality."""
        if len(signal) == 0:
            return {"quality_score": 0.0, "noise_level": 0.0}

        # Simple quality metrics
        signal_power = np.mean(signal**2)
        noise_estimate = np.var(np.diff(signal))
        quality_score = min(1.0, signal_power / (signal_power + noise_estimate))

        return {
            "quality_score": quality_score,
            "noise_level": noise_estimate,
            "signal_power": signal_power,
        }


class TemporalConsistencyChecker:
    """Mock temporal consistency checker."""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size

    def check_consistency(self, data: np.ndarray) -> bool:
        """Check temporal consistency."""
        if len(data) < self.window_size:
            return True

        # Simple consistency check based on variance
        recent_data = data[-self.window_size :]
        variance = np.var(recent_data)
        return variance < np.var(data) * 2.0  # Allow some variation


@dataclass
class ValidationResult:
    """Mock validation result."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def create_error_info(
    category: ErrorCategory,
    severity: ErrorSeverity,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> ErrorInfo:
    """Mock error info creation function."""
    return ErrorInfo(
        category=category,
        severity=severity,
        code="TEST_ERROR",
        message=message,
        details=details or {},
    )


def handle_exception(
    exception: Exception,
    logger: Any = None,
    reraise: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> APGIError:
    """Mock exception handling function."""
    # Create appropriate error type based on exception
    if isinstance(exception, ValueError):
        error = APGIError(
            message=str(exception), category=ErrorCategory.VALIDATION, severity=ErrorSeverity.MEDIUM
        )
    elif isinstance(exception, FileNotFoundError):
        error = APGIError(
            message=str(exception), category=ErrorCategory.IO, severity=ErrorSeverity.HIGH
        )
    else:
        error = APGIError(
            message=str(exception), category=ErrorCategory.RUNTIME, severity=ErrorSeverity.MEDIUM
        )

    if reraise:
        raise error

    return error


class TestErrorHandler:
    """Test error handling system."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_severity_enum(self):
        """Test error severity enum values."""
        assert ErrorSeverity.CRITICAL.value == "CRITICAL"
        assert ErrorSeverity.HIGH.value == "HIGH"
        assert ErrorSeverity.MEDIUM.value == "MEDIUM"
        assert ErrorSeverity.LOW.value == "LOW"
        assert ErrorSeverity.INFO.value == "INFO"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_category_enum(self):
        """Test error category enum values."""
        assert ErrorCategory.CONFIGURATION.value == "CONFIGURATION"
        assert ErrorCategory.VALIDATION.value == "VALIDATION"
        assert ErrorCategory.SIMULATION.value == "SIMULATION"
        assert ErrorCategory.DATA.value == "DATA"
        assert ErrorCategory.IO.value == "IO"
        assert ErrorCategory.NETWORK.value == "NETWORK"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_apgi_error_creation(self):
        """Test APGIError creation and properties."""
        error = APGIError(
            message="Test error message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            context={"param1": "value1"},
            cause=ValueError("Original error"),
        )

        assert error.message == "Test error message"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.context["param1"] == "value1"
        assert error.cause.__class__ == ValueError
        assert str(error) == "Test error message"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_info_creation(self):
        """Test ErrorInfo creation."""
        info = ErrorInfo(
            timestamp=datetime.now(),
            error_type="ValueError",
            message="Test message",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.DATA,
            context={"key": "value"},
            stack_trace="Stack trace here",
        )

        assert info.error_type == "ValueError"
        assert info.message == "Test message"
        assert info.severity == ErrorSeverity.MEDIUM
        assert info.category == ErrorCategory.DATA
        assert info.context["key"] == "value"
        assert info.stack_trace == "Stack trace here"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()

        assert hasattr(handler, "error_history")
        assert hasattr(handler, "max_history_size")
        assert hasattr(handler, "logger")
        assert len(handler.error_history) == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_handle_exception_function(self):
        """Test exception handling function."""
        try:
            raise ValueError("Test exception")
        except Exception as e:
            error_info = handle_exception(
                exception=e,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.HIGH,
                context={"test": True},
            )

            assert error_info.error_type == "ValueError"
            assert error_info.message == "Test exception"
            assert error_info.category == ErrorCategory.VALIDATION
            assert error_info.severity == ErrorSeverity.HIGH
            assert error_info.context["test"] is True

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_create_error_info_function(self):
        """Test error info creation function."""
        exception = RuntimeError("Runtime error")

        info = create_error_info(
            exception=exception,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SIMULATION,
            context={"simulation_id": "sim123"},
        )

        assert info.error_type == "RuntimeError"
        assert info.message == "Runtime error"
        assert info.severity == ErrorSeverity.CRITICAL
        assert info.category == ErrorCategory.SIMULATION
        assert info.context["simulation_id"] == "sim123"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_history_management(self):
        """Test error history management."""
        handler = ErrorHandler(max_history_size=3)

        # Add errors beyond capacity
        for i in range(5):
            try:
                raise ValueError(f"Error {i}")
            except Exception as e:
                handler.handle_error(e, ErrorCategory.DATA, ErrorSeverity.LOW)

        # Should only keep the most recent errors
        assert len(handler.error_history) == 3
        assert "Error 4" in handler.error_history[-1].message
        assert "Error 2" in handler.error_history[0].message

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_statistics(self):
        """Test error statistics generation."""
        handler = ErrorHandler()

        # Add different types of errors
        for i in range(3):
            try:
                raise ValueError("Validation error")
            except Exception as e:
                handler.handle_error(e, ErrorCategory.VALIDATION, ErrorSeverity.HIGH)

        for i in range(2):
            try:
                raise IOError("IO error")
            except Exception as e:
                handler.handle_error(e, ErrorCategory.IO, ErrorSeverity.MEDIUM)

        stats = handler.get_error_statistics()

        assert stats["total_errors"] == 5
        assert stats["by_category"]["VALIDATION"] == 3
        assert stats["by_category"]["IO"] == 2
        assert stats["by_severity"]["HIGH"] == 3
        assert stats["by_severity"]["MEDIUM"] == 2


class TestDataValidation:
    """Test data validation utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_validation_config_defaults(self):
        """Test validation config default values."""
        config = ValidationConfig()

        assert config.missing_data_threshold == 10.0
        assert config.outlier_threshold == 5.0
        assert config.outlier_zscore_threshold == 1.5
        assert config.signal_quality_threshold == 70.0
        assert config.temporal_irregular_threshold == 5.0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_validation_config_custom(self):
        """Test validation config custom values."""
        config = ValidationConfig(
            missing_data_threshold=5.0, outlier_threshold=3.0, signal_quality_threshold=80.0
        )

        assert config.missing_data_threshold == 5.0
        assert config.outlier_threshold == 3.0
        assert config.signal_quality_threshold == 80.0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_data_validator_initialization(self):
        """Test DataValidator initialization."""
        config = ValidationConfig()
        validator = DataValidator(config)

        assert validator.config == config
        assert hasattr(validator, "outlier_detector")
        assert hasattr(validator, "signal_analyzer")
        assert hasattr(validator, "temporal_checker")

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_validate_numeric_data_basic(self):
        """Test basic numeric data validation."""
        config = ValidationConfig()
        validator = DataValidator(config)

        # Create test data with some issues
        data = pd.Series([1, 2, 3, np.nan, 5, 100, 2, 3, 4, 5])

        result = validator.validate_numeric_data(data, "test_column")

        assert isinstance(result, ValidationResult)
        assert result.column_name == "test_column"
        assert result.total_samples == 10
        assert result.missing_count == 1
        assert result.missing_percentage == 10.0
        assert result.outlier_count > 0  # Should detect the value 100
        assert result.is_valid is not None  # Should be determined

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_validate_dataframe_comprehensive(self):
        """Test comprehensive DataFrame validation."""
        config = ValidationConfig()
        validator = DataValidator(config)

        # Create test DataFrame
        df = pd.DataFrame(
            {
                "col1": [1, 2, 3, np.nan, 5],
                "col2": [1.1, 2.2, 3.3, 4.4, 5.5],
                "col3": ["a", "b", "c", "d", "e"],
            }
        )

        results = validator.validate_dataframe(df)

        assert isinstance(results, dict)
        assert "col1" in results
        assert "col2" in results
        assert "col3" in results

        # Check missing data detection in col1
        col1_result = results["col1"]
        assert col1_result.missing_count == 1
        assert col1_result.missing_percentage == 20.0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_signal_quality_analysis(self):
        """Test signal quality analysis."""
        config = ValidationConfig()
        analyzer = SignalQualityAnalyzer(config)

        # Create test signal
        signal = np.sin(np.linspace(0, 10, 100)) + np.random.normal(0, 0.1, 100)

        quality_result = analyzer.analyze_signal_quality(signal, sampling_rate=10.0)

        assert quality_result.overall_quality >= 0
        assert quality_result.overall_quality <= 100
        assert quality_result.snr is not None
        assert quality_result.noise_level is not None
        assert quality_result.drift_detected is not None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_outlier_detection(self):
        """Test outlier detection methods."""
        config = ValidationConfig(outlier_zscore_threshold=2.0)
        detector = OutlierDetector(config)

        # Create data with outliers
        data = np.array([1, 2, 3, 4, 5, 50, 6, 7, 8, 9])  # 50 is an outlier

        outliers_zscore = detector.detect_outliers_zscore(data)
        outliers_iqr = detector.detect_outliers_iqr(data)

        assert len(outliers_zscore) > 0
        assert len(outliers_iqr) > 0
        assert 5 in outliers_zscore or 5 in outliers_iqr  # Should detect the outlier

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_temporal_consistency_check(self):
        """Test temporal consistency checking."""
        config = ValidationConfig()
        checker = TemporalConsistencyChecker(config)

        # Create time series data
        timestamps = pd.date_range("2023-01-01", periods=100, freq="1H")
        values = np.random.normal(0, 1, 100)

        # Add some irregularities
        timestamps[50] = timestamps[50] + pd.Timedelta(days=1)  # Large gap
        values[75] = 100  # Extreme value

        result = checker.check_temporal_consistency(timestamps, values)

        assert result.is_consistent is not None
        assert result.irregular_timestamps > 0
        assert result.extreme_values > 0
        assert result.consistency_score >= 0
        assert result.consistency_score <= 100


class TestConfigManager:
    """Test configuration management."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            manager = ConfigManager(config_file)

            assert manager.config_file == config_file
            assert hasattr(manager, "config")
            assert hasattr(manager, "watchers")

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_load_config_success(self):
        """Test successful config loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            # Create test config
            test_config = {
                "database": {"host": "localhost", "port": 5432, "name": "test_db"},
                "logging": {"level": "INFO", "file": "app.log"},
            }

            config_file.write_text(json.dumps(test_config))

            manager = ConfigManager(config_file)
            loaded_config = manager.load_config()

            assert loaded_config["database"]["host"] == "localhost"
            assert loaded_config["database"]["port"] == 5432
            assert loaded_config["logging"]["level"] == "INFO"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "nonexistent.json"

            manager = ConfigManager(config_file)

            with pytest.raises(ConfigLoadError):
                manager.load_config()

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "invalid.json"

            # Write invalid JSON
            config_file.write_text('{"invalid": json}')

            manager = ConfigManager(config_file)

            with pytest.raises(ConfigLoadError):
                manager.load_config()

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_save_config(self):
        """Test config saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            manager = ConfigManager(config_file)

            test_config = {
                "app_name": "test_app",
                "version": "1.0.0",
                "settings": {"debug": True, "max_connections": 10},
            }

            manager.save_config(test_config)

            # Verify file was created and contains correct data
            assert config_file.exists()

            loaded_config = manager.load_config()
            assert loaded_config["app_name"] == "test_app"
            assert loaded_config["version"] == "1.0.0"
            assert loaded_config["settings"]["debug"] is True

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_get_config_value(self):
        """Test getting individual config values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            test_config = {"database": {"host": "localhost", "port": 5432}, "debug": True}

            config_file.write_text(json.dumps(test_config))

            manager = ConfigManager(config_file)
            manager.load_config()

            # Test getting values
            assert manager.get("database.host") == "localhost"
            assert manager.get("database.port") == 5432
            assert manager.get("debug") is True
            assert manager.get("nonexistent", "default") == "default"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_set_config_value(self):
        """Test setting individual config values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            manager = ConfigManager(config_file)

            # Set values
            manager.set("app.name", "my_app")
            manager.set("app.version", "2.0.0")
            manager.set("debug", True)

            # Save and reload
            manager.save_config(manager.config)

            new_manager = ConfigManager(config_file)
            new_manager.load_config()

            assert new_manager.get("app.name") == "my_app"
            assert new_manager.get("app.version") == "2.0.0"
            assert new_manager.get("debug") is True

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_config_validation(self):
        """Test config validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"

            manager = ConfigManager(config_file)

            # Define validation schema
            schema = {
                "type": "object",
                "required": ["database", "logging"],
                "properties": {
                    "database": {
                        "type": "object",
                        "required": ["host", "port"],
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        },
                    },
                    "logging": {
                        "type": "object",
                        "required": ["level"],
                        "properties": {
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                            }
                        },
                    },
                },
            }

            # Test valid config
            valid_config = {
                "database": {"host": "localhost", "port": 5432},
                "logging": {"level": "INFO"},
            }

            assert manager.validate_config(valid_config, schema) is True

            # Test invalid config
            invalid_config = {
                "database": {"host": "localhost", "port": -1},  # Invalid port
                "logging": {"level": "INVALID"},  # Invalid level
            }

            with pytest.raises(ConfigValidationError):
                manager.validate_config(invalid_config, schema)


class TestPerformanceProfiler:
    """Test performance profiling utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiler_initialization(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()

        assert hasattr(profiler, "results")
        assert hasattr(profiler, "current_context")
        assert hasattr(profiler, "enabled")
        assert profiler.enabled is True

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiling_context_manager(self):
        """Test profiling context manager."""
        profiler = PerformanceProfiler()

        with profiler.profile("test_operation") as context:
            assert context.name == "test_operation"
            assert context.start_time is not None
            assert context.end_time is None

            # Simulate some work
            import time

            time.sleep(0.01)

        # After context exit
        assert context.end_time is not None
        assert context.duration > 0

        # Check result was stored
        results = profiler.get_results()
        assert "test_operation" in results
        assert results["test_operation"].duration > 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiling_decorator(self):
        """Test profiling decorator."""
        profiler = PerformanceProfiler()

        @profiler.profile_function
        def test_function(x, y):
            import time

            time.sleep(0.01)
            return x + y

        result = test_function(2, 3)

        assert result == 5

        # Check profiling result
        results = profiler.get_results()
        assert "test_function" in results
        assert results["test_function"].call_count == 1
        assert results["test_function"].total_duration > 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_multiple_calls_profiling(self):
        """Test profiling multiple function calls."""
        profiler = PerformanceProfiler()

        @profiler.profile_function
        def fast_function():
            return "quick"

        # Call function multiple times
        for _ in range(5):
            fast_function()

        results = profiler.get_results()
        function_result = results["fast_function"]

        assert function_result.call_count == 5
        assert function_result.min_duration > 0
        assert function_result.max_duration >= function_result.min_duration
        assert function_result.avg_duration == function_result.total_duration / 5

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiling_statistics(self):
        """Test profiling statistics generation."""
        profiler = PerformanceProfiler()

        @profiler.profile_function
        def function_a():
            import time

            time.sleep(0.01)
            return "a"

        @profiler.profile_function
        def function_b():
            import time

            time.sleep(0.02)
            return "b"

        # Call functions
        function_a()
        function_a()
        function_b()

        stats = profiler.get_statistics()

        assert "total_functions" in stats
        assert "total_calls" in stats
        assert "total_duration" in stats
        assert "slowest_function" in stats
        assert "fastest_function" in stats

        assert stats["total_functions"] == 2
        assert stats["total_calls"] == 3
        assert stats["slowest_function"] == "function_b"
        assert stats["fastest_function"] == "function_a"


class TestCacheManager:
    """Test cache management utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        cache = CacheManager(max_size=100, ttl_seconds=300)

        assert cache.max_size == 100
        assert cache.ttl_seconds == 300
        assert len(cache.cache) == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_set_and_get(self):
        """Test cache set and get operations."""
        cache = CacheManager()

        # Set value
        cache.set("key1", "value1")

        # Get value
        value = cache.get("key1")
        assert value == "value1"

        # Get non-existent key
        value = cache.get("nonexistent")
        assert value is None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = CacheManager(ttl_seconds=0.1)  # 100ms TTL

        cache.set("key1", "value1")

        # Should be available immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        import time

        time.sleep(0.15)

        # Should be expired
        assert cache.get("key1") is None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_max_size_eviction(self):
        """Test cache max size eviction (LRU)."""
        cache = CacheManager(max_size=3)

        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert len(cache.cache) == 3

        # Add one more (should evict oldest)
        cache.set("key4", "value4")

        assert len(cache.cache) == 3
        assert cache.get("key1") is None  # Should be evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_delete(self):
        """Test cache deletion."""
        cache = CacheManager()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Delete existing key
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

        # Delete non-existent key
        assert cache.delete("nonexistent") is False

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_clear(self):
        """Test cache clearing."""
        cache = CacheManager()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache.cache) == 2

        cache.clear()

        assert len(cache.cache) == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = CacheManager()

        # Perform operations
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss
        cache.delete("key1")

        stats = cache.get_stats()

        assert isinstance(stats, CacheStats)
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.sets == 1
        assert stats.deletes == 1
        assert stats.hit_rate == 0.5  # 1 hit / (1 hit + 1 miss)


class TestCircuitBreaker:
    """Test circuit breaker utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_initialization(self):
        """Test CircuitBreaker initialization."""
        breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, expected_exception=Exception
        )

        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker(failure_threshold=3)

        # Should allow calls in closed state
        with breaker.call():
            pass  # Successful call

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker failure threshold."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        # Fail calls to reach threshold
        for i in range(2):
            try:
                with breaker.call():
                    raise ValueError("Test failure")
            except ValueError:
                pass  # Expected

        # Should trip to open state
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 2

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trip the breaker
        try:
            with breaker.call():
                raise ValueError("Test failure")
        except ValueError:
            pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Should reject calls in open state
        with pytest.raises(CircuitBreakerError):
            with breaker.call():
                pass  # Should not execute

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open state recovery."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trip the breaker
        try:
            with breaker.call():
                raise ValueError("Test failure")
        except ValueError:
            pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        import time

        time.sleep(0.15)

        # Next call should go to half-open state
        with breaker.call():
            pass  # Successful call

        # Should return to closed state on success
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker half-open state failure."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        # Trip the breaker
        try:
            with breaker.call():
                raise ValueError("Test failure")
        except ValueError:
            pass

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        import time

        time.sleep(0.15)

        # Fail in half-open state
        try:
            with breaker.call():
                raise ValueError("Another failure")
        except ValueError:
            pass

        # Should return to open state
        assert breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        breaker = CircuitBreaker(failure_threshold=2)

        @breaker.protect
        def risky_function(should_fail=False):
            if should_fail:
                raise ValueError("Function failed")
            return "success"

        # Successful call
        assert risky_function(False) == "success"

        # Failed calls
        for _ in range(2):
            try:
                risky_function(True)
            except ValueError:
                pass

        # Should be tripped now
        with pytest.raises(CircuitBreakerError):
            risky_function(False)


# Mock tests for when utils modules are not available
class TestUtilsMock:
    """Mock tests when utils modules are not available."""

    @pytest.mark.skipif(UTILS_AVAILABLE, reason="Utils modules are available")
    def test_utils_modules_unavailable(self):
        """Test behavior when utils modules are not available."""
        with pytest.raises(ImportError):
            from utils.error_handler import ErrorHandler  # noqa: F401

        with pytest.raises(ImportError):
            from utils.data_validation import DataValidator  # noqa: F401


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
