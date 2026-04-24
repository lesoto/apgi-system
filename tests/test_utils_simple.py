"""
Simple test for utility modules - direct execution without pytest discovery
issues.
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_dependency_checker():
    """Test dependency checker functionality."""
    try:
        from dependency_checker import CORE_DEPENDENCIES  # type: ignore[import-not-found]

        print("✓ DependencyChecker imported successfully")
        print(f"✓ Found {len(CORE_DEPENDENCIES)} core dependencies")

        # Check structure
        for dep_name, dep_info in CORE_DEPENDENCIES.items():
            assert "min_version" in dep_info
            assert "description" in dep_info

        print("✓ Core dependencies structure is valid")
        return True

    except Exception as e:
        print(f"✗ DependencyChecker test failed: {e}")
        return False


def test_parameter_validator():
    """Test parameter validator functionality."""
    try:
        from parameter_validator import APGIParameterValidator  # type: ignore[import-not-found]

        validator = APGIParameterValidator()
        print("✓ APGIParameterValidator imported successfully")

        # Check methods exist
        assert hasattr(validator, "validate")
        assert hasattr(validator, "get_parameter_info")
        assert hasattr(validator, "list_valid_parameters")

        print("✓ APGIParameterValidator has required methods")
        return True

    except Exception as e:
        print(f"✗ ParameterValidator test failed: {e}")
        return False


def test_config_manager():
    """Test config manager functionality."""
    try:
        from config_manager import ConfigManager  # type: ignore[import-not-found]

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(config_file)  # Pass Path object directly

            print("✓ ConfigManager imported and initialized successfully")
            assert manager is not None

            # Check that the config file path is set correctly
            assert str(manager.config_file) == str(config_file)

            print("✓ ConfigManager initialized correctly")
            return True

    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False


def test_error_handler():
    """Test error handler functionality."""
    try:
        from error_handler import ErrorHandler  # type: ignore[import-not-found]

        handler = ErrorHandler()
        print("✓ ErrorHandler imported and initialized successfully")

        # Check methods exist
        assert hasattr(handler, "handle_error")
        assert hasattr(handler, "create_error")
        assert hasattr(handler, "get_error_summary")

        print("✓ ErrorHandler has required methods")
        return True

    except Exception as e:
        print(f"✗ ErrorHandler test failed: {e}")
        return False


def test_logging_config():
    """Test logging configuration functionality."""
    try:
        from logging_config import LogEntry  # type: ignore[import-not-found]

        entry = LogEntry(
            timestamp="2023-01-01T12:00:00",
            level="INFO",
            message="Test message",
            module="test_module",
            function="test_function",
            line=42,
        )

        print("✓ LogEntry created successfully")

        # Test to_dict method
        entry_dict = entry.to_dict()
        assert isinstance(entry_dict, dict)
        assert "timestamp" in entry_dict
        assert "level" in entry_dict

        print("✓ LogEntry.to_dict() works correctly")
        return True

    except Exception as e:
        print(f"✗ LoggingConfig test failed: {e}")
        return False


def test_utils_directory_structure():
    """Test utils directory structure."""
    utils_dir = Path(__file__).parent

    assert utils_dir.exists(), "Utils directory does not exist"
    assert utils_dir.is_dir(), "Utils path is not a directory"

    print("✓ Utils directory exists")

    # Check for key modules
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

    print(f"✓ All {len(key_modules)} key modules exist")
    return True


def main():
    """Run all tests."""
    print("Running Utility Module Tests")
    print("=" * 50)

    tests = [
        ("Dependency Checker", test_dependency_checker),
        ("Parameter Validator", test_parameter_validator),
        ("Config Manager", test_config_manager),
        ("Error Handler", test_error_handler),
        ("Logging Config", test_logging_config),
        ("Directory Structure", test_utils_directory_structure),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
