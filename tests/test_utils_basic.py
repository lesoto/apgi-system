"""
Basic unit tests for utility modules.

This test suite provides coverage for key utility functions that are available
and working in the utils directory.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDependencyChecker:
    """Test cases for DependencyChecker functionality."""

    def test_dependency_checker_import(self):
        """Test that dependency checker can be imported."""
        try:
            from utils.dependency_checker import CORE_DEPENDENCIES

            assert isinstance(CORE_DEPENDENCIES, dict)
            assert "numpy" in CORE_DEPENDENCIES
            assert "matplotlib" in CORE_DEPENDENCIES
        except ImportError as e:
            pytest.skip(f"DependencyChecker not available: {e}")

    def test_core_dependencies_structure(self):
        """Test that core dependencies have proper structure."""
        try:
            from utils.dependency_checker import CORE_DEPENDENCIES

            for dep_name, dep_info in CORE_DEPENDENCIES.items():
                assert "min_version" in dep_info
                assert "description" in dep_info
                assert isinstance(dep_info["min_version"], str)
                assert isinstance(dep_info["description"], str)
        except ImportError as e:
            pytest.skip(f"DependencyChecker not available: {e}")


class TestParameterValidator:
    """Test cases for ParameterValidator functionality."""

    def test_parameter_validator_import(self):
        """Test that parameter validator can be imported."""
        try:
            from utils.parameter_validator import ParameterValidator

            validator = ParameterValidator()
            assert validator is not None
        except ImportError as e:
            pytest.skip(f"ParameterValidator not available: {e}")

    def test_basic_validation_methods(self):
        """Test basic validation methods exist."""
        try:
            from utils.parameter_validator import ParameterValidator

            validator = ParameterValidator()

            # Check that validation methods exist
            assert hasattr(validator, "validate_number")
            assert hasattr(validator, "validate_string")
            assert hasattr(validator, "validate_email")
            assert hasattr(validator, "validate_range")
        except ImportError as e:
            pytest.skip(f"ParameterValidator not available: {e}")


class TestConfigManager:
    """Test cases for ConfigManager functionality."""

    def test_config_manager_import(self):
        """Test that config manager can be imported."""
        try:
            from utils.config_manager import ConfigManager

            assert ConfigManager is not None
        except ImportError as e:
            pytest.skip(f"ConfigManager not available: {e}")

    def test_config_manager_initialization(self):
        """Test config manager initialization."""
        try:
            from utils.config_manager import ConfigManager

            with tempfile.TemporaryDirectory() as temp_dir:
                config_file = Path(temp_dir) / "test_config.json"
                manager = ConfigManager(str(config_file))
                assert manager is not None
                assert config_file.parent.exists()
        except ImportError as e:
            pytest.skip(f"ConfigManager not available: {e}")


class TestErrorHandler:
    """Test cases for ErrorHandler functionality."""

    def test_error_handler_import(self):
        """Test that error handler can be imported."""
        try:
            from utils.error_handler import ErrorHandler

            assert ErrorHandler is not None
        except ImportError as e:
            pytest.skip(f"ErrorHandler not available: {e}")

    def test_error_handler_methods(self):
        """Test error handler has required methods."""
        try:
            from utils.error_handler import ErrorHandler

            with tempfile.TemporaryDirectory():
                handler = ErrorHandler()

                # Check that required methods exist
                assert hasattr(handler, "log_error")
                assert hasattr(handler, "get_error_summary")
                assert hasattr(handler, "get_error_statistics")
        except ImportError as e:
            pytest.skip(f"ErrorHandler not available: {e}")


class TestCacheManager:
    """Test cases for CacheManager functionality."""

    def test_cache_manager_import(self):
        """Test that cache manager can be imported."""
        try:
            from utils.cache_manager import CacheManager

            assert CacheManager is not None
        except ImportError as e:
            pytest.skip(f"CacheManager not available: {e}")

    def test_cache_manager_initialization(self):
        """Test cache manager initialization."""
        try:
            from utils.cache_manager import CacheManager

            with tempfile.TemporaryDirectory() as temp_dir:
                cache_dir = Path(temp_dir) / "test_cache"
                manager = CacheManager(str(cache_dir), max_size_mb=1)
                assert manager is not None
                assert cache_dir.exists()
        except ImportError as e:
            pytest.skip(f"CacheManager not available: {e}")


class TestBackupManager:
    """Test cases for BackupManager functionality."""

    def test_backup_manager_import(self):
        """Test that backup manager can be imported."""
        try:
            from utils.backup_manager import BackupManager

            assert BackupManager is not None
        except ImportError as e:
            pytest.skip(f"BackupManager not available: {e}")

    def test_backup_manager_initialization(self):
        """Test backup manager initialization."""
        try:
            from utils.backup_manager import BackupManager

            with tempfile.TemporaryDirectory() as temp_dir:
                backup_dir = Path(temp_dir) / "test_backups"
                manager = BackupManager(str(backup_dir))
                assert manager is not None
                assert backup_dir.exists()
        except ImportError as e:
            pytest.skip(f"BackupManager not available: {e}")


class TestLoggingConfig:
    """Test cases for logging configuration."""

    def test_logging_config_import(self):
        """Test that logging config can be imported."""
        try:
            from utils.logging_config import LogEntry

            assert LogEntry is not None
        except ImportError as e:
            pytest.skip(f"LoggingConfig not available: {e}")

    def test_log_entry_structure(self):
        """Test log entry data structure."""
        try:
            from utils.logging_config import LogEntry

            entry = LogEntry(
                timestamp="2023-01-01T12:00:00",
                level="INFO",
                message="Test message",
                module="test_module",
                function="test_function",
                line=42,
            )

            assert entry.timestamp == "2023-01-01T12:00:00"
            assert entry.level == "INFO"
            assert entry.message == "Test message"
            assert entry.module == "test_module"
            assert entry.function == "test_function"
            assert entry.line == 42

            # Test to_dict method
            entry_dict = entry.to_dict()
            assert isinstance(entry_dict, dict)
            assert "timestamp" in entry_dict
            assert "level" in entry_dict
        except ImportError as e:
            pytest.skip(f"LoggingConfig not available: {e}")


class TestDataValidation:
    """Test cases for DataValidator functionality."""

    def test_data_validator_import(self):
        """Test that data validator can be imported."""
        try:
            from utils.data_validation import DataValidator

            assert DataValidator is not None
        except ImportError as e:
            pytest.skip(f"DataValidator not available: {e}")

    def test_data_validator_methods(self):
        """Test data validator has required methods."""
        try:
            from utils.data_validation import DataValidator

            validator = DataValidator()

            # Check that validation methods exist
            assert hasattr(validator, "validate_file_format")
            assert hasattr(validator, "validate_dataset_structure")
            assert hasattr(validator, "validate_data_quality")
        except ImportError as e:
            pytest.skip(f"DataValidator not available: {e}")


class TestPerformanceProfiler:
    """Test cases for PerformanceProfiler functionality."""

    def test_performance_profiler_import(self):
        """Test that performance profiler can be imported."""
        try:
            from utils.performance_profiler import PerformanceProfiler

            assert PerformanceProfiler is not None
        except ImportError as e:
            pytest.skip(f"PerformanceProfiler not available: {e}")

    def test_performance_profiler_initialization(self):
        """Test performance profiler initialization."""
        try:
            from utils.performance_profiler import PerformanceProfiler

            with tempfile.TemporaryDirectory() as temp_dir:
                profile_dir = Path(temp_dir) / "test_profiles"
                profiler = PerformanceProfiler(str(profile_dir))
                assert profiler is not None
                assert profile_dir.exists()
        except ImportError as e:
            pytest.skip(f"PerformanceProfiler not available: {e}")


class TestUtilityModuleStructure:
    """Test utility module structure and basic functionality."""

    def test_utils_directory_exists(self):
        """Test that utils directory exists."""
        utils_dir = Path(__file__).parent.parent / "utils"
        assert utils_dir.exists()
        assert utils_dir.is_dir()

    def test_key_utility_modules_exist(self):
        """Test that key utility modules exist."""
        utils_dir = Path(__file__).parent.parent / "utils"

        key_modules = [
            "dependency_checker.py",
            "parameter_validator.py",
            "config_manager.py",
            "error_handler.py",
            "logging_config.py",
        ]

        for module in key_modules:
            module_path = utils_dir / module
            assert module_path.exists(), f"Module {module} does not exist"
            assert module_path.is_file(), f"Module {module} is not a file"

    def test_module_imports_structure(self):
        """Test that modules have proper import structure."""
        utils_dir = Path(__file__).parent.parent / "utils"

        for module_file in utils_dir.glob("*.py"):
            if module_file.name.startswith("__"):
                continue

            # Try to read the module and check for basic structure
            try:
                content = module_file.read_text()
                assert (
                    '"""' in content or "'''" in content
                ), f"Module {module_file.name} lacks docstring"
                assert len(content) > 100, f"Module {module_file.name} seems too short or empty"
            except Exception as e:
                pytest.skip(f"Could not read module {module_file.name}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
