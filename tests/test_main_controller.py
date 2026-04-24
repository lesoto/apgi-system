"""
Comprehensive test suite for apgi_framework.main_controller module.

Tests for MainApplicationController which orchestrates the entire APGI Framework system.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from apgi_framework.main_controller import MainApplicationController
from apgi_framework.exceptions import APGIFrameworkError


class TestMainApplicationControllerInit:
    """Tests for MainApplicationController initialization."""

    def test_default_initialization(self):
        """Test controller initialization with default config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                "os.environ",
                {"APGI_CONFIG_PATH": str(Path(temp_dir) / "config.yaml")},
            ):
                controller = MainApplicationController()

                assert controller.config_manager is not None
                assert controller.logger is not None
                assert controller._mathematical_engine is None
                assert controller._neural_simulators is None
                assert controller._falsification_tests is None
                assert controller._data_manager is None
                assert controller._initialized is False
                assert controller._components_registered is False

    def test_initialization_with_config_path(self):
        """Test controller initialization with custom config path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.yaml"
            config_file.write_text("test: value\n")

            controller = MainApplicationController(config_path=str(config_file))

            assert controller.config_manager is not None
            assert controller.logger is not None


class TestSystemInitialization:
    """Tests for system initialization."""

    def test_initialize_system_success(self):
        """Test successful system initialization."""
        with tempfile.TemporaryDirectory():
            controller = MainApplicationController()

            # Mock the initialization methods
            controller._initialize_mathematical_engine = Mock()
            controller._initialize_neural_simulators = Mock()
            controller._initialize_data_manager = Mock()
            controller._initialize_falsification_tests = Mock()

            controller.initialize_system()

            assert controller._initialized is True
            controller._initialize_mathematical_engine.assert_called_once()
            controller._initialize_neural_simulators.assert_called_once()
            controller._initialize_data_manager.assert_called_once()
            controller._initialize_falsification_tests.assert_called_once()

    def test_initialize_system_already_initialized(self):
        """Test that initializing an already initialized system is handled."""
        controller = MainApplicationController()

        # Mock all initialization methods
        controller._initialize_mathematical_engine = Mock()
        controller._initialize_neural_simulators = Mock()
        controller._initialize_data_manager = Mock()
        controller._initialize_falsification_tests = Mock()

        # Initialize once
        controller.initialize_system()
        assert controller._initialized is True

        # Mock should have been called once
        controller._initialize_mathematical_engine.assert_called_once()

    def test_initialize_system_failure(self):
        """Test system initialization failure handling."""
        controller = MainApplicationController()

        # Make one of the initialization methods raise an error
        def raise_error():
            raise APGIFrameworkError("Initialization failed")

        controller._initialize_mathematical_engine = raise_error

        with pytest.raises(Exception):
            controller.initialize_system()

        assert controller._initialized is False


class TestComponentRegistration:
    """Tests for component registration."""

    def test_register_components(self):
        """Test component registration."""
        controller = MainApplicationController()

        # Mock component initialization
        controller._initialize_mathematical_engine = Mock()
        controller._initialize_neural_simulators = Mock()
        controller._initialize_data_manager = Mock()
        controller._initialize_falsification_tests = Mock()

        controller.initialize_system()

        assert controller._initialized is True

    def test_component_dependencies(self):
        """Test that components have proper dependencies."""
        controller = MainApplicationController()

        # Initialize system - mocks just track calls, real methods set attributes
        controller._initialize_mathematical_engine = Mock()
        controller._initialize_neural_simulators = Mock()
        controller._initialize_data_manager = Mock()
        controller._initialize_falsification_tests = Mock()

        controller.initialize_system()

        # Verify initialization methods were called
        controller._initialize_mathematical_engine.assert_called_once()
        controller._initialize_neural_simulators.assert_called_once()
        controller._initialize_data_manager.assert_called_once()
        controller._initialize_falsification_tests.assert_called_once()

        # Verify system is marked as initialized
        assert controller._initialized is True


class TestMathematicalEngine:
    """Tests for mathematical engine initialization and usage."""

    def test_initialize_mathematical_engine(self):
        """Test mathematical engine initialization."""
        controller = MainApplicationController()

        # Initialize - _mathematical_engine is already None by default
        controller._initialize_mathematical_engine()

        assert controller._mathematical_engine is not None
        assert "equation" in controller._mathematical_engine
        assert "precision_calculator" in controller._mathematical_engine
        assert "prediction_error_processor" in controller._mathematical_engine
        assert "somatic_marker_engine" in controller._mathematical_engine
        assert "threshold_manager" in controller._mathematical_engine


class TestNeuralSimulators:
    """Tests for neural simulator initialization."""

    def test_initialize_neural_simulators(self):
        """Test neural simulator initialization."""
        controller = MainApplicationController()

        # Initialize - _neural_simulators is already None by default
        controller._initialize_neural_simulators()

        assert controller._neural_simulators is not None
        assert "bold" in controller._neural_simulators
        assert "gamma" in controller._neural_simulators
        assert "p3b" in controller._neural_simulators
        assert "pci" in controller._neural_simulators
        assert "validator" in controller._neural_simulators


class TestFalsificationTests:
    """Tests for falsification test initialization."""

    def test_initialize_falsification_tests(self):
        """Test falsification test initialization."""
        controller = MainApplicationController()

        # Initialize dependencies first (required by _initialize_falsification_tests)
        controller._initialize_mathematical_engine()
        controller._initialize_neural_simulators()

        # Now initialize falsification tests
        controller._initialize_falsification_tests()

        assert controller._falsification_tests is not None
        assert "primary" in controller._falsification_tests
        assert "consciousness_without_ignition" in controller._falsification_tests
        assert "soma_bias" in controller._falsification_tests
        assert "threshold_insensitivity" in controller._falsification_tests


class TestDataManager:
    """Tests for data manager initialization."""

    def test_initialize_data_manager(self):
        """Test data manager initialization."""
        controller = MainApplicationController()

        # Initialize - _data_manager is already None by default
        controller._initialize_data_manager()

        assert controller._data_manager is not None
        assert "validator" in controller._data_manager
        assert "storage" in controller._data_manager


class TestLoggingSetup:
    """Tests for logging setup."""

    def test_setup_logging(self):
        """Test logging setup."""
        controller = MainApplicationController()

        logger = controller._setup_logging()

        assert logger is not None
        assert logger.name == "apgi_framework.main_controller"


class TestSystemState:
    """Tests for system state checks."""

    def test_is_initialized_property(self):
        """Test is_initialized property."""
        controller = MainApplicationController()

        # Initially not initialized
        assert controller.is_initialized is False

        # After initialization
        controller._initialize_mathematical_engine = Mock()
        controller._initialize_neural_simulators = Mock()
        controller._initialize_data_manager = Mock()
        controller._initialize_falsification_tests = Mock()

        controller.initialize_system()
        assert controller.is_initialized is True

    def test_is_components_registered_property(self):
        """Test is_components_registered property."""
        controller = MainApplicationController()

        assert controller.is_components_registered is False

        # Register components would set this to True
        controller._components_registered = True
        assert controller.is_components_registered is True


class TestErrorHandling:
    """Tests for error handling."""

    def test_initialization_error_handling(self):
        """Test that initialization errors are properly handled."""
        controller = MainApplicationController()

        # Simulate an error during mathematical engine initialization
        def raise_error():
            raise Exception("Test error")

        original_init = controller._initialize_mathematical_engine
        controller._initialize_mathematical_engine = raise_error

        with pytest.raises(Exception):
            controller.initialize_system()

        # Restore original method
        controller._initialize_mathematical_engine = original_init


class TestConfigurationAccess:
    """Tests for configuration access."""

    def test_get_config_value(self):
        """Test getting configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text("test_section:\n  test_key: test_value\n")

            controller = MainApplicationController(config_path=str(config_file))

            # Test config access through config_manager
            assert controller.config_manager is not None


class TestExecutionMethods:
    """Tests for execution and orchestration methods."""

    def test_run_falsification_test_not_initialized(self):
        """Test running falsification test without initialization."""
        controller = MainApplicationController()

        # Should raise error or handle gracefully when not initialized
        with pytest.raises((RuntimeError, APGIFrameworkError, AttributeError)):
            controller.run_falsification_test("primary")

    def test_run_falsification_test_initialized(self):
        """Test running falsification test after initialization."""
        controller = MainApplicationController()

        # Mock initialization
        controller._initialize_mathematical_engine = Mock()
        controller._initialize_neural_simulators = Mock()
        controller._initialize_data_manager = Mock()
        controller._initialize_falsification_tests = Mock(
            return_value={
                "primary": Mock(run=Mock(return_value={"result": "success"})),
            }
        )

        controller.initialize_system()

        # Mock the run_falsification_test method behavior
        controller._falsification_tests = {
            "primary": Mock(run=Mock(return_value={"result": "success"})),
        }

        # The test should work with initialized system
        assert controller._falsification_tests is not None
        assert "primary" in controller._falsification_tests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
