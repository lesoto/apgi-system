"""
Tests for configuration manager edge cases and error handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from apgi_framework.config.config_manager import APGIParameters, ConfigManager, ConfigurationError


class TestConfigManagerEdgeCases:
    """Test edge cases in configuration management."""

    def test_save_preset_creates_directory(self):
        """Test that save_preset creates the presets directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(str(config_path))

            # Override presets_dir to a subdirectory
            manager.presets_dir = Path(temp_dir) / "presets" / "sub"

            # Save a preset
            manager.save_preset("test_preset")

            # Check that directory was created
            assert manager.presets_dir.exists()
            assert (manager.presets_dir / "test_preset.json").exists()

    def test_load_preset_invalid_name(self):
        """Test loading a non-existent preset raises ConfigurationError."""
        manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Preset not found"):
            manager.load_preset("non_existent_preset")

    def test_load_preset_corrupted_json(self):
        """Test loading a preset with corrupted JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            # Create corrupted preset file
            preset_file = manager.presets_dir / "corrupted.json"
            preset_file.write_text("{invalid json")

            with pytest.raises(ConfigurationError):
                manager.load_preset("corrupted")

    def test_delete_preset_invalid_name(self):
        """Test deleting a non-existent preset raises ConfigurationError."""
        manager = ConfigManager()

        with pytest.raises(ConfigurationError, match="Preset not found"):
            manager.delete_preset("non_existent_preset")

    def test_save_and_load_preset_with_custom_data(self):
        """Test saving and loading preset with custom parameter values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.json"
            manager = ConfigManager(str(config_path))

            # Modify some parameters
            manager.apgi_params.extero_precision = 5.0
            manager.experimental_config.n_trials = 2000

            # Save preset
            manager.save_preset("custom_preset")

            # Create new manager and load preset
            manager2 = ConfigManager()
            manager2.presets_dir = manager.presets_dir
            manager2.load_preset("custom_preset")

            # Check values were loaded
            assert manager2.apgi_params.extero_precision == 5.0
            assert manager2.experimental_config.n_trials == 2000

    def test_list_presets_empty(self):
        """Test listing presets when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            assert manager.list_presets() == []

    def test_list_presets_with_files(self):
        """Test listing presets with existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            # Create some preset files
            (manager.presets_dir / "preset1.json").write_text("{}")
            (manager.presets_dir / "preset2.json").write_text("{}")
            (manager.presets_dir / "not_preset.txt").write_text("not json")

            presets = manager.list_presets()
            assert "preset1" in presets
            assert "preset2" in presets
            assert "not_preset" not in presets

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "invalid_config.json"
            config_path.write_text("{invalid json")

            manager = ConfigManager(str(config_path))

            # Should not load invalid config, keep defaults
            assert isinstance(manager.apgi_params, APGIParameters)

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "missing_config.json"

            # Should not raise, just use defaults
            manager = ConfigManager(str(config_path))
            assert isinstance(manager.apgi_params, APGIParameters)

    @patch("apgi_framework.config.config_manager.logger")
    def test_save_preset_logging(self, mock_logger):
        """Test that save_preset logs success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            manager.save_preset("test_preset")

            mock_logger.info.assert_called_with("Saved configuration preset: test_preset")

    @patch("apgi_framework.config.config_manager.logger")
    def test_load_preset_logging(self, mock_logger):
        """Test that load_preset logs success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            # Save first
            manager.save_preset("test_preset")

            # Load
            manager.load_preset("test_preset")

            mock_logger.info.assert_called_with("Loaded configuration preset: test_preset")

    @patch("apgi_framework.config.config_manager.logger")
    def test_delete_preset_logging(self, mock_logger):
        """Test that delete_preset logs success."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ConfigManager()
            manager.presets_dir = Path(temp_dir)

            # Save first
            manager.save_preset("test_preset")

            # Delete
            manager.delete_preset("test_preset")

            mock_logger.info.assert_called_with("Deleted configuration preset: test_preset")
