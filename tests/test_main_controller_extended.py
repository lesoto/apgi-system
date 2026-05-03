"""
Extended Main Controller Coverage Tests

Tests MainApplicationController initialization, system initialization, and properties.
"""

from unittest.mock import Mock, patch

import pytest

from apgi_framework.exceptions import APGIFrameworkError
from apgi_framework.main_controller import MainApplicationController


class TestMainControllerInit:
    """Test MainApplicationController initialization."""

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_init_without_config_path(self, mock_get_config):
        """Test initialization without config path uses default config."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        controller = MainApplicationController()

        assert controller.config_manager is mock_config
        assert controller._initialized is False
        assert controller._components_registered is False
        mock_get_config.assert_called_once()

    @patch("apgi_framework.main_controller.ConfigManager")
    def test_init_with_config_path(self, mock_config_class):
        """Test initialization with custom config path."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config

        controller = MainApplicationController("/path/to/config.yaml")

        assert controller.config_manager is mock_config
        mock_config_class.assert_called_once_with("/path/to/config.yaml")


class TestMainControllerProperties:
    """Test MainApplicationController properties."""

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_is_initialized_property_false(self, mock_get_config):
        """Test is_initialized property returns False initially."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        assert controller.is_initialized is False

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_is_initialized_property_true(self, mock_get_config):
        """Test is_initialized property returns True after initialization."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        controller._initialized = True
        assert controller.is_initialized is True

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_is_components_registered_property(self, mock_get_config):
        """Test is_components_registered property."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        assert controller.is_components_registered is False

        controller._components_registered = True
        assert controller.is_components_registered is True


class TestMainControllerInitializeSystem:
    """Test MainApplicationController system initialization."""

    @patch(
        "apgi_framework.main_controller.MainApplicationController._initialize_falsification_tests"
    )
    @patch("apgi_framework.main_controller.MainApplicationController._initialize_data_manager")
    @patch("apgi_framework.main_controller.MainApplicationController._initialize_neural_simulators")
    @patch(
        "apgi_framework.main_controller.MainApplicationController._initialize_mathematical_engine"
    )
    @patch("apgi_framework.main_controller.get_config_manager")
    def test_initialize_system_success(
        self,
        mock_get_config,
        mock_init_math,
        mock_init_neural,
        mock_init_data,
        mock_init_falsification,
    ):
        """Test successful system initialization."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        controller.initialize_system()

        assert controller._initialized is True
        mock_init_math.assert_called_once()
        mock_init_neural.assert_called_once()
        mock_init_data.assert_called_once()
        mock_init_falsification.assert_called_once()

    @patch(
        "apgi_framework.main_controller.MainApplicationController._initialize_mathematical_engine"
    )
    @patch("apgi_framework.main_controller.get_config_manager")
    def test_initialize_system_failure(self, mock_get_config, mock_init_math):
        """Test system initialization failure raises APGIFrameworkError."""
        mock_get_config.return_value = Mock()
        mock_init_math.side_effect = Exception("Math engine failed")

        controller = MainApplicationController()

        with pytest.raises(APGIFrameworkError, match="Failed to initialize system"):
            controller.initialize_system()

        assert controller._initialized is False


class TestMainControllerMathematicalEngine:
    """Test mathematical engine initialization."""

    @patch("apgi_framework.main_controller.PrecisionCalculator")
    @patch("apgi_framework.main_controller.PredictionErrorProcessor")
    @patch("apgi_framework.main_controller.SomaticMarkerEngine")
    @patch("apgi_framework.main_controller.ThresholdManager")
    @patch("apgi_framework.main_controller.APGIEquation")
    @patch("apgi_framework.main_controller.get_config_manager")
    def test_initialize_mathematical_engine(
        self,
        mock_get_config,
        mock_equation,
        mock_threshold,
        mock_somatic,
        mock_prediction,
        mock_precision,
    ):
        """Test mathematical engine components are initialized."""
        mock_config = Mock()
        mock_apgi_params = Mock()
        mock_apgi_params.min_precision = 1e-6
        mock_apgi_params.max_precision = 100.0
        mock_apgi_params.standardize_errors = True
        mock_apgi_params.outlier_threshold = 3.0
        mock_apgi_params.baseline_somatic_gain = 1.0
        mock_apgi_params.max_somatic_gain = 5.0
        mock_apgi_params.min_somatic_gain = 0.1
        mock_apgi_params.baseline_threshold = 3.5
        mock_apgi_params.min_threshold = 0.5
        mock_apgi_params.max_threshold = 10.0
        mock_apgi_params.numerical_stability = True
        mock_config.get_apgi_parameters.return_value = mock_apgi_params
        mock_get_config.return_value = mock_config

        controller = MainApplicationController()
        controller._initialize_mathematical_engine()

        assert controller._mathematical_engine is not None
        assert "equation" in controller._mathematical_engine
        assert "precision_calculator" in controller._mathematical_engine
        assert "prediction_error_processor" in controller._mathematical_engine
        assert "somatic_marker_engine" in controller._mathematical_engine
        assert "threshold_manager" in controller._mathematical_engine


class TestMainControllerNeuralSimulators:
    """Test neural simulators initialization."""

    @patch("apgi_framework.main_controller.P3bSimulator")
    @patch("apgi_framework.main_controller.GammaSimulator")
    @patch("apgi_framework.main_controller.BOLDSimulator")
    @patch("apgi_framework.main_controller.PCICalculator")
    @patch("apgi_framework.main_controller.SignatureValidator")
    @patch("apgi_framework.main_controller.get_config_manager")
    def test_initialize_neural_simulators(
        self, mock_get_config, mock_signature, mock_pci, mock_bold, mock_gamma, mock_p3b
    ):
        """Test neural simulators are initialized."""
        mock_config = Mock()
        mock_exp_config = Mock()
        mock_exp_config.random_seed = 42
        mock_config.get_experimental_config.return_value = mock_exp_config
        mock_get_config.return_value = mock_config

        controller = MainApplicationController()
        controller._initialize_neural_simulators()

        assert controller._neural_simulators is not None
        assert "p3b" in controller._neural_simulators
        assert "gamma" in controller._neural_simulators
        assert "bold" in controller._neural_simulators
        assert "pci" in controller._neural_simulators
        assert "validator" in controller._neural_simulators


class TestMainControllerDataManager:
    """Test data manager initialization."""

    @patch("apgi_framework.main_controller.StorageManager")
    @patch("apgi_framework.main_controller.DataValidator")
    @patch("apgi_framework.main_controller.get_config_manager")
    def test_initialize_data_manager(
        self, mock_get_config, mock_validator_class, mock_storage_class
    ):
        """Test data manager components are initialized."""
        mock_config = Mock()
        mock_exp_config = Mock()
        mock_exp_config.output_directory = "./output"
        mock_config.get_experimental_config.return_value = mock_exp_config
        mock_get_config.return_value = mock_config

        mock_storage = Mock()
        mock_storage_class.return_value = mock_storage
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        controller = MainApplicationController()
        controller._initialize_data_manager()

        assert controller._data_manager is not None
        mock_storage_class.assert_called_once_with(storage_path="./output")


class TestMainControllerComponentAccess:
    """Test component access methods."""

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_get_mathematical_engine_before_init(self, mock_get_config):
        """Test getting mathematical engine before initialization."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        result = controller.get_mathematical_engine()
        assert result is None

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_get_neural_simulators_before_init(self, mock_get_config):
        """Test getting neural simulators before initialization."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        result = controller.get_neural_simulators()
        assert result is None

    @patch("apgi_framework.main_controller.get_config_manager")
    def test_get_data_manager_before_init(self, mock_get_config):
        """Test getting data manager before initialization."""
        mock_get_config.return_value = Mock()

        controller = MainApplicationController()
        result = controller.get_data_manager()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
