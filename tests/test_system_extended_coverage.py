"""
Extended System Module Coverage Tests - Increases system.py coverage

Tests APGISystem initialization, configuration, and subsystem integration.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from apgi_framework.system import APGISystem


class TestAPGISystemInit:
    """Test APGISystem initialization."""

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_init_with_default_config(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test initialization with default config path."""
        mock_get_resource.return_value = Path("/fake/config/default.yaml")
        mock_yaml_load.return_value = {
            "system": {"random_seed": 42, "timestep_ms": 10, "max_history_size": 1000}
        }
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        system = APGISystem()

        mock_get_resource.assert_called_once_with("config/default.yaml")
        assert system.time == 0.0
        assert system.timestep_ms == 10
        assert system.is_running is False

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_init_with_custom_config(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test initialization with custom config path."""
        mock_get_resource.return_value = Path("/fake/custom/config.yaml")
        mock_yaml_load.return_value = {
            "system": {"random_seed": 123, "timestep_ms": 5, "max_history_size": 5000}
        }
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        system = APGISystem("custom/config.yaml")

        mock_get_resource.assert_called_once_with("custom/config.yaml")
        assert system.timestep_ms == 5

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_init_with_absolute_path(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test initialization with absolute config path."""
        mock_yaml_load.return_value = {
            "system": {"random_seed": 42, "timestep_ms": 10, "max_history_size": 1000}
        }
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        APGISystem("/absolute/path/config.yaml")

        # get_resource_path should not be called for absolute paths
        mock_get_resource.assert_not_called()

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch("apgi_framework.system.ConfigValidator")
    def test_init_config_validation_failure(
        self, mock_validator_class, mock_get_resource, mock_open, mock_yaml_load
    ):
        """Test that config validation failure raises ValueError."""
        from apgi_framework.config_validator import ConfigValidationError

        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {"system": {"timestep_ms": 10}}

        mock_validator = Mock()
        mock_validator.validate.side_effect = ConfigValidationError("Invalid config")
        mock_validator_class.return_value = mock_validator

        with pytest.raises(ValueError, match="Configuration validation failed"):
            APGISystem()


class TestAPGISystemRNG:
    """Test APGISystem random number generator initialization."""

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    @patch("apgi_framework.system.np.random.default_rng")
    def test_rng_initialized_with_seed(
        self,
        mock_default_rng,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test RNG is initialized with configured seed."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {
            "system": {"random_seed": 42, "timestep_ms": 10, "max_history_size": 1000}
        }
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_rng = Mock()
        mock_default_rng.return_value = mock_rng

        system = APGISystem()

        mock_default_rng.assert_called_once_with(42)
        assert system._rng is mock_rng

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    @patch("apgi_framework.system.np.random.default_rng")
    def test_rng_initialized_without_seed(
        self,
        mock_default_rng,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test RNG is initialized without seed when none provided."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {
            "system": {"timestep_ms": 10, "max_history_size": 1000}  # No random_seed
        }
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_rng = Mock()
        mock_default_rng.return_value = mock_rng

        APGISystem()

        mock_default_rng.assert_called_once_with(None)


class TestAPGISystemHistory:
    """Test APGISystem history initialization."""

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_history_initialized_with_bounded_deques(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test history is initialized as bounded deques."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {"system": {"timestep_ms": 10, "max_history_size": 5000}}
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        system = APGISystem()

        assert "time" in system.history
        assert "ignitions" in system.history
        assert "free_energy" in system.history
        assert "precision" in system.history
        assert "metabolic_reserves" in system.history

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_history_uses_default_max_size(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test history uses default max_history_size when not specified."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {"system": {"timestep_ms": 10}}  # No max_history_size
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        system = APGISystem()

        # Should use default of 10000
        assert system.history["time"].maxlen == 10000


class TestAPGISystemState:
    """Test APGISystem state properties."""

    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch.object(APGISystem, "_initialize_subsystems")
    @patch("apgi_framework.system.ConfigValidator")
    def test_initial_state(
        self,
        mock_validator_class,
        mock_init_subsystems,
        mock_get_resource,
        mock_open,
        mock_yaml_load,
    ):
        """Test initial system state."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        mock_yaml_load.return_value = {"system": {"timestep_ms": 10, "max_history_size": 1000}}
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        system = APGISystem()

        assert system.time == 0.0
        assert system.is_running is False
        assert system.timestep_ms == 10


class TestAPGISystemSubsystemInitialization:
    """Test APGISystem subsystem initialization."""

    @patch("apgi_framework.system.ActiveInferenceEngine")
    @patch("apgi_framework.system.yaml.safe_load")
    @patch("apgi_framework.system.open")
    @patch("apgi_framework.system.get_resource_path")
    @patch("apgi_framework.system.ConfigValidator")
    def test_active_inference_initialized(
        self, mock_validator_class, mock_get_resource, mock_open, mock_yaml_load, mock_engine
    ):
        """Test ActiveInferenceEngine is initialized."""
        mock_get_resource.return_value = Path("/fake/config.yaml")
        config = {"system": {"timestep_ms": 10}, "active_inference": {"enabled": True}}
        mock_yaml_load.return_value = config
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance

        system = APGISystem()

        mock_engine.assert_called_once_with(config)
        assert system.active_inference is mock_engine_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
