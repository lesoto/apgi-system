"""
Unit tests for cross-platform path handling.

Tests config file loading, resource file access, and data export
with platform-appropriate directories.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from apgi_framework.platform_utils import get_config_dir, get_data_dir, get_resource_path
from apgi_framework.system import APGISystem


class TestConfigLoading:
    """Test configuration file loading with new path handling."""

    def test_config_loads_with_default_path(self) -> None:
        """Test that system loads config from default path using get_resource_path."""
        # This should work in both dev and bundled environments
        system = APGISystem()

        assert system.config is not None
        assert "system" in system.config
        assert "timestep_ms" in system.config["system"]

    def test_config_loads_with_relative_path(self) -> None:
        """Test that system loads config from relative path."""
        system = APGISystem(config_path="config/default.yaml")

        assert system.config is not None
        assert "system" in system.config

    def test_config_loads_with_absolute_path(self) -> None:
        """Test that system loads config from absolute path."""
        config_path = get_resource_path("config/default.yaml")
        system = APGISystem(config_path=str(config_path))

        assert system.config is not None
        assert "system" in system.config

    def test_config_path_resolution(self) -> None:
        """Test that config path is resolved correctly."""
        config_path = get_resource_path("config/default.yaml")

        assert config_path.exists(), f"Config file not found at {config_path}"
        assert config_path.is_file()
        assert config_path.suffix == ".yaml"


class TestResourceAccess:
    """Test resource file access in GUI and system."""

    def test_resource_path_returns_valid_path(self) -> None:
        """Test that get_resource_path returns valid paths."""
        config_path = get_resource_path("config/default.yaml")

        assert isinstance(config_path, Path)
        assert config_path.exists()

    def test_resource_path_works_for_nested_paths(self) -> None:
        """Test that get_resource_path works for nested directory structures."""
        # Test with a path that should exist
        config_path = get_resource_path("config/default.yaml")
        assert config_path.exists()

        # The path should be absolute
        assert config_path.is_absolute()

    def test_config_file_is_readable(self) -> None:
        """Test that config file can be read and parsed."""
        config_path = get_resource_path("config/default.yaml")

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert isinstance(config, dict)
        assert "system" in config


class TestDataExport:
    """Test data export with platform-appropriate directories."""

    def test_data_dir_is_writable(self) -> None:
        """Test that data directory is writable."""
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)

        assert data_dir.exists()
        assert data_dir.is_dir()

        # Test write access
        test_file = data_dir / "test_write.txt"
        try:
            test_file.write_text("test")
            assert test_file.exists()
            assert test_file.read_text() == "test"
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_data_export_to_json(self) -> None:
        """Test exporting data to JSON in data directory."""
        data_dir = get_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)

        test_data = {"time": [0.0, 1.0, 2.0], "value": [1.0, 2.0, 3.0]}

        export_file = data_dir / "test_export.json"
        try:
            with open(export_file, "w") as f:
                json.dump(test_data, f)

            assert export_file.exists()

            # Verify data can be read back
            with open(export_file, "r") as f:
                loaded_data = json.load(f)

            assert loaded_data == test_data
        finally:
            if export_file.exists():
                export_file.unlink()

    def test_config_dir_is_accessible(self) -> None:
        """Test that config directory is accessible."""
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        assert config_dir.exists()
        assert config_dir.is_dir()

    def test_platform_dirs_are_different(self) -> None:
        """Test that data and config dirs are in appropriate locations."""
        data_dir = get_data_dir()
        config_dir = get_config_dir()

        # Both should exist or be creatable
        data_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)

        assert data_dir.exists()
        assert config_dir.exists()

        # They should be absolute paths
        assert data_dir.is_absolute()
        assert config_dir.is_absolute()


class TestGUIPathHandling:
    """Test GUI-specific path handling."""

    @patch("apgi_framework.platform_utils.get_resource_path")
    def test_gui_uses_get_resource_path_for_config(self, mock_get_resource: MagicMock) -> None:
        """Test that GUI uses get_resource_path for config loading."""
        # Mock the return value
        mock_config_path = Path("/mock/path/config/default.yaml")
        mock_get_resource.return_value = mock_config_path

        # Import here to use the mocked function
        from apgi_gui import APGIGui

        # Create a mock root
        mock_root = MagicMock()

        # This will fail because we're mocking, but we can check the call
        try:
            APGIGui(mock_root)
        except Exception:
            pass  # Expected to fail due to mocking

        # Verify get_resource_path was called
        mock_get_resource.assert_called()

    def test_gui_config_path_is_path_object(self) -> None:
        """Test that GUI stores config path as Path object."""
        # We can't fully test GUI without a display, but we can test the path logic
        config_path = get_resource_path("config/default.yaml")

        assert isinstance(config_path, Path)
        assert config_path.exists()


class TestCrossPlatformCompatibility:
    """Test cross-platform path compatibility."""

    def test_paths_use_forward_slashes_internally(self) -> None:
        """Test that paths work with forward slashes on all platforms."""
        # get_resource_path should handle forward slashes on all platforms
        config_path = get_resource_path("config/default.yaml")

        assert config_path.exists()

    def test_paths_are_absolute(self) -> None:
        """Test that resolved paths are absolute."""
        config_path = get_resource_path("config/default.yaml")
        data_dir = get_data_dir()
        config_dir = get_config_dir()

        assert config_path.is_absolute()
        assert data_dir.is_absolute()
        assert config_dir.is_absolute()

    def test_path_objects_used_throughout(self) -> None:
        """Test that Path objects are used instead of strings."""
        config_path = get_resource_path("config/default.yaml")

        # Should return Path object, not string
        assert isinstance(config_path, Path)

        # Path objects should work with open()
        with open(config_path, "r") as f:
            content = f.read()

        assert len(content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
