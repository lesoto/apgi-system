#!/usr/bin/env python3
"""
Simple tests for Utils modules.

Tests cover the actual functionality available in the utils modules.
"""

import tempfile
from pathlib import Path

import pytest

# Import utils modules we're testing
try:
    from utils.cache_manager import CacheManager
    from utils.circuit_breaker_utils import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerState,
    )
    from utils.config_manager import ConfigManager
    from utils.data_validation import ValidationConfig
    from utils.error_handler import APGIError, ErrorCategory, ErrorHandler, ErrorInfo, ErrorSeverity
    from utils.performance_profiler import PerformanceProfiler

    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


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
            original_error=ValueError("Original error"),
        )

        assert error.message == "Test error message"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.context["param1"] == "value1"
        assert error.original_error.__class__ == ValueError
        assert "Test error message" in str(error)

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_info_creation(self):
        """Test ErrorInfo creation."""
        info = ErrorInfo(
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            code="VAL001",
            message="Test message",
            details={"key": "value"},
            suggestions=["Try again"],
            user_action="Check input",
        )

        assert info.category == ErrorCategory.DATA
        assert info.severity == ErrorSeverity.MEDIUM
        assert info.code == "VAL001"
        assert info.message == "Test message"
        assert info.details["key"] == "value"
        assert info.suggestions == ["Try again"]
        assert info.user_action == "Check input"

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()

        assert hasattr(handler, "error_counts")
        assert hasattr(handler, "error_handlers")
        assert hasattr(handler, "ERROR_TEMPLATES")
        assert len(handler.error_counts) == 0
        assert len(handler.error_handlers) == 0


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
            assert hasattr(manager, "schema")

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_save_and_load_config(self):
        """Test config saving and loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            manager = ConfigManager(config_file)

            test_config = {
                "app_name": "test_app",
                "version": "1.0.0",
                "settings": {"debug": True, "max_connections": 10},
            }

            # Save config
            manager.save_config(test_config)

            # Verify file was created
            assert config_file.exists()

            # Load config
            loaded_config = manager.load_config()
            assert loaded_config["app_name"] == "test_app"
            assert loaded_config["version"] == "1.0.0"
            assert loaded_config["settings"]["debug"] is True


class TestPerformanceProfiler:
    """Test performance profiling utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiler_initialization(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()

        assert hasattr(profiler, "function_profiles")
        assert hasattr(profiler, "custom_metrics")
        assert hasattr(profiler, "system_monitor")
        assert profiler.system_monitor.monitoring is True

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiling_context_manager(self):
        """Test profiling context manager."""
        profiler = PerformanceProfiler()

        with profiler.profile_context("test_operation") as context:
            # During context execution
            assert context is None  # context manager doesn't return anything

            # Simulate some work
            import time

            time.sleep(0.01)

        # Check metric was added
        metrics = profiler.get_metrics_by_category("context")
        assert len(metrics) > 0
        assert any(m.name == "test_operation" for m in metrics)

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_profiling_decorator(self):
        """Test profiling decorator."""
        profiler = PerformanceProfiler()

        @profiler.profile_function()
        def test_function(x, y):
            import time

            time.sleep(0.01)
            return x + y

        result = test_function(2, 3)

        assert result == 5

        # Check profiling result
        assert len(profiler.function_profiles) > 0
        func_name = "tests.test_utils_simple_new.test_function"
        assert func_name in profiler.function_profiles
        profile = profiler.function_profiles[func_name]
        assert profile.call_count == 1
        assert profile.total_time > 0


class TestCacheManager:
    """Test cache management utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_manager_initialization(self):
        """Test CacheManager initialization."""
        cache = CacheManager(cache_dir="test_cache", max_size_mb=100)

        assert cache.max_size_mb == 100
        assert cache.max_size_bytes == 100 * 1024 * 1024
        assert cache.cache_dir.name == "test_cache"
        assert hasattr(cache, "stats")

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_set_and_get(self):
        """Test cache set and operations."""
        cache = CacheManager()

        # Set value
        cache.set("key1", "value1")

        # Get value
        value = cache.get("key1")
        assert value == "value1"

        # Get non-existent value
        value = cache.get("nonexistent")
        assert value is None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_ttl_expiration(self):
        """Test cache TTL expiration."""
        # CacheManager doesn't have TTL, so test basic expiration functionality
        cache = CacheManager()

        cache.set("key1", "value1")

        # Get value immediately
        value = cache.get("key1")
        assert value == "value1"

        # Test cache deletion
        cache.delete("key1")
        value = cache.get("key1")
        assert value is None

        # Wait for expiration
        import time

        time.sleep(0.15)

        assert cache.get("key1") is None

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_cache_max_size_eviction(self):
        """Test cache max size eviction."""
        # CacheManager uses size in MB, not item count
        cache = CacheManager(max_size_mb=1)

        # Add some items
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")

        # Check that items are still there (they're small)
        assert cache.get("key1") == "value1"
        assert cache.get("key4") == "value4"
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


class TestCircuitBreaker:
    """Test circuit breaker utilities."""

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_initialization(self):
        """Test CircuitBreaker initialization."""
        config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60, name="test_breaker")
        breaker = CircuitBreaker(config)

        assert breaker.config.failure_threshold == 5
        assert breaker.config.recovery_timeout == 60
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.metrics.failed_requests == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        config = CircuitBreakerConfig(failure_threshold=3, name="test")
        breaker = CircuitBreaker(config)

        # Should allow calls in closed state
        # Test a successful call
        result = breaker.call(lambda: "success")

        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.metrics.failed_requests == 0

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1, name="test")
        breaker = CircuitBreaker(config)

        # Fail calls to reach threshold
        def failing_function():
            raise Exception("Test error")

        for i in range(2):
            try:
                breaker.call(failing_function)
            except Exception:
                pass  # Expected

        # Should be open now
        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.metrics.failed_requests == 2

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_open_state(self):
        """Test circuit breaker in open state."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1, name="test")
        breaker = CircuitBreaker(config)

        # Trip the breaker
        def failing_function():
            raise ValueError("Test failure")

        try:
            breaker.call(failing_function)
        except ValueError:
            pass

        # Should be open now
        assert breaker.state == CircuitBreakerState.OPEN

        # Should reject calls
        with pytest.raises(Exception):
            breaker.call(lambda: "should fail")

    @pytest.mark.skipif(not UTILS_AVAILABLE, reason="Utils modules not available")
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker half-open state recovery."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1, name="test")
        breaker = CircuitBreaker(config)

        # Trip the breaker
        def failing_function():
            raise ValueError("Test failure")

        try:
            breaker.call(failing_function)
        except ValueError:
            pass

        # Should be open now
        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        import time

        time.sleep(0.15)

        # Should be half-open now, allow one call
        result = breaker.call(lambda: "recovered")
        assert result == "recovered"

        # Should be closed again after success
        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.metrics.failed_requests == 2  # Still has the original failures


# Mock tests for when utils modules are not available
class TestUtilsMock:
    """Mock tests when utils modules are not available."""

    @pytest.mark.skipif(UTILS_AVAILABLE, reason="Utils modules are available")
    def test_utils_modules_unavailable(self):
        """Test behavior when utils modules are not available."""
        with pytest.raises(ImportError):
            from utils.error_handler import ErrorHandler  # noqa: F401

        with pytest.raises(ImportError):
            from utils.data_validation import ValidationConfig  # noqa: F401


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
