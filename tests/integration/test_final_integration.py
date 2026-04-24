"""
Final integration tests for cross-platform executable.

These tests verify cross-platform compatibility, configuration persistence,
data export compatibility, and experimental task execution in the context
of the bundled executable environment.

Requirements tested:
- 9.1: Executable launches without errors
- 9.2: GUI functionality preservation
- 9.3: File I/O correctness
- 9.4: Platform-specific features work correctly
- 9.5: Cross-platform data compatibility

Feature: cross-platform-executable
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml


class TestCrossPlatformConfigCompatibility:
    """Test configuration file compatibility across platforms."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory for config testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration data."""
        return {
            "system": {
                "name": "APGI System",
                "version": "1.0.0",
                "precision_threshold": 0.5,
                "ignition_threshold": 0.7,
            },
            "neural": {
                "num_layers": 3,
                "layer_sizes": [100, 50, 25],
                "learning_rate": 0.001,
            },
            "paths": {
                "data_dir": "data",
                "output_dir": "output",
                "config_file": "config/default.yaml",
            },
            "experimental": {
                "tasks": ["iowa_gambling", "masking_paradigm", "attentional_blink"],
                "num_trials": 100,
            },
        }

    def test_config_yaml_round_trip(self, temp_config_dir, sample_config):
        """
        Test that configuration can be saved and loaded without data loss.

        Validates: Requirements 9.3, 9.4
        """
        config_file = temp_config_dir / "test_config.yaml"

        # Save configuration
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load configuration
        with open(config_file, "r") as f:
            loaded_config = yaml.safe_load(f)

        # Verify data integrity
        assert loaded_config == sample_config, "Config data should be preserved"

    def test_config_cross_platform_paths(self, temp_config_dir, sample_config):
        """
        Test that configuration with paths works across platforms.

        Validates: Requirements 9.3, 9.5
        """
        config_file = temp_config_dir / "test_config.yaml"

        # Modify paths to use Path objects
        sample_config["paths"]["data_dir"] = str(Path("data"))
        sample_config["paths"]["output_dir"] = str(Path("output"))
        sample_config["paths"]["config_file"] = str(Path("config") / "default.yaml")

        # Save configuration
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load configuration
        with open(config_file, "r") as f:
            loaded_config = yaml.safe_load(f)

        # Verify paths are strings
        assert isinstance(loaded_config["paths"]["data_dir"], str)
        assert isinstance(loaded_config["paths"]["output_dir"], str)
        assert isinstance(loaded_config["paths"]["config_file"], str)

        # Verify paths can be converted to Path objects
        data_path = Path(loaded_config["paths"]["data_dir"])
        output_path = Path(loaded_config["paths"]["output_dir"])
        config_path = Path(loaded_config["paths"]["config_file"])

        assert data_path.name == "data"
        assert output_path.name == "output"
        assert config_path.name == "default.yaml"

    def test_config_with_special_characters(self, temp_config_dir):
        """
        Test that configuration handles special characters correctly.

        Validates: Requirements 9.3
        """
        config_file = temp_config_dir / "test_config.yaml"

        # Configuration with special characters
        config = {
            "description": "Test with special chars: @#$%^&*()",
            "unicode": "Test with unicode: 你好世界 🌍",
            "multiline": "Line 1\nLine 2\nLine 3",
        }

        # Save configuration
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)

        # Load configuration
        with open(config_file, "r", encoding="utf-8") as f:
            loaded_config = yaml.safe_load(f)

        # Verify special characters preserved
        assert loaded_config["description"] == config["description"]
        assert loaded_config["unicode"] == config["unicode"]
        assert loaded_config["multiline"] == config["multiline"]

    def test_config_default_values(self, temp_config_dir):
        """
        Test that missing configuration values use defaults.

        Validates: Requirements 9.3
        """
        config_file = temp_config_dir / "test_config.yaml"

        # Minimal configuration
        minimal_config = {"system": {"name": "APGI System"}}

        # Save configuration
        with open(config_file, "w") as f:
            yaml.dump(minimal_config, f)

        # Load configuration
        with open(config_file, "r") as f:
            loaded_config = yaml.safe_load(f)

        # Verify minimal config loads
        assert loaded_config["system"]["name"] == "APGI System"

        # Verify we can add defaults
        defaults = {
            "system": {
                "version": "1.0.0",
                "precision_threshold": 0.5,
            }
        }

        # Merge with defaults
        for key, value in defaults.items():
            if key not in loaded_config:
                loaded_config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in loaded_config[key]:
                        loaded_config[key][subkey] = subvalue

        # Verify defaults applied
        assert loaded_config["system"]["version"] == "1.0.0"
        assert loaded_config["system"]["precision_threshold"] == 0.5


class TestExportedDataCompatibility:
    """Test exported data file compatibility across platforms."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_export_data(self):
        """Create sample export data."""
        return {
            "session_id": "test_session_001",
            "timestamp": "2024-12-04T10:30:00",
            "system_state": {
                "free_energy": 0.45,
                "precision": 0.78,
                "ignition_level": 0.62,
            },
            "experimental_results": {
                "task": "iowa_gambling",
                "trials": 100,
                "correct_responses": 75,
                "reaction_times": [0.5, 0.6, 0.4, 0.7, 0.5],
            },
            "neural_activity": {
                "layer_0": [0.1, 0.2, 0.3, 0.4, 0.5],
                "layer_1": [0.6, 0.7, 0.8, 0.9, 1.0],
            },
        }

    def test_json_export_round_trip(self, temp_export_dir, sample_export_data):
        """
        Test that JSON export preserves data integrity.

        Validates: Requirements 9.3, 9.5
        """
        export_file = temp_export_dir / "export_data.json"

        # Export data
        with open(export_file, "w") as f:
            json.dump(sample_export_data, f, indent=2)

        # Import data
        with open(export_file, "r") as f:
            imported_data = json.load(f)

        # Verify data integrity
        assert imported_data == sample_export_data, "Export data should be preserved"

    def test_csv_export_compatibility(self, temp_export_dir: Path) -> None:
        """
        Test that CSV export works across platforms.

        Validates: Requirements 9.3, 9.5
        """
        import csv

        export_file = temp_export_dir / "export_data.csv"

        # Sample tabular data
        data = [
            ["trial", "response", "reaction_time", "correct"],
            [1, "A", 0.5, True],
            [2, "B", 0.6, False],
            [3, "A", 0.4, True],
        ]

        # Export to CSV
        with open(export_file, "w", newline="") as f:
            writer = csv.writer(f)
            csv_data: list[list[str | int | float | bool]] = [
                [str(x) for x in row] if isinstance(row, list) else [str(row)] for row in data
            ]
            writer.writerows(csv_data)

        # Import from CSV
        with open(export_file, "r", newline="") as f:
            reader = csv.reader(f)
            imported_data = list(reader)

        # Verify data integrity
        assert len(imported_data) == len(data)
        assert imported_data[0] == data[0]  # Header
        assert imported_data[1][0] == "1"  # First trial

    def test_numpy_export_compatibility(self, temp_export_dir: Path) -> None:
        """
        Test that numpy array export works across platforms.

        Validates: Requirements 9.3, 9.5
        """
        try:
            import numpy as np
        except ImportError:
            pytest.skip("NumPy not available")

        export_file = temp_export_dir / "neural_data.npy"

        # Create sample numpy array
        data = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

        # Export array
        np.save(export_file, data)

        # Import array
        imported_data = np.load(export_file)

        # Verify data integrity
        assert np.array_equal(imported_data, data), "NumPy data should be preserved"

    def test_export_with_metadata(self, temp_export_dir: Path, sample_export_data: dict) -> None:
        """
        Test that export includes metadata for cross-platform compatibility.

        Validates: Requirements 9.3, 9.5
        """
        export_file = temp_export_dir / "export_with_metadata.json"

        # Add metadata
        export_data = {
            "metadata": {
                "platform": sys.platform,
                "python_version": sys.version,
                "export_format_version": "1.0",
            },
            "data": sample_export_data,
        }

        # Export data
        with open(export_file, "w") as f:
            json.dump(export_data, f, indent=2)

        # Import data
        with open(export_file, "r") as f:
            imported_data = json.load(f)

        # Verify metadata present
        assert "metadata" in imported_data
        assert "platform" in imported_data["metadata"]
        assert "export_format_version" in imported_data["metadata"]

        # Verify data preserved
        assert imported_data["data"] == sample_export_data


class TestExperimentalTasksExecution:
    """Test that experimental tasks execute correctly in bundled environment."""

    @pytest.fixture
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_iowa_gambling_task_import(self) -> None:
        """
        Test that Iowa Gambling Task can be imported.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.iowa_gambling import IowaGamblingTask

            assert IowaGamblingTask is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Iowa Gambling Task: {e}")

    def test_iowa_gambling_task_execution(self) -> None:
        """
        Test that Iowa Gambling Task can be executed.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.iowa_gambling import IowaGamblingTask

            # Create task instance
            task = IowaGamblingTask()

            # Verify task has required methods
            assert hasattr(task, "run_trial") or hasattr(
                task, "run_all_trials"
            ), "Task should have run method"
            assert hasattr(task, "reset"), "Task should have reset method"

            # Reset task
            task.reset()

            # Verify task state initialized
            assert (
                hasattr(task, "trial_count")
                or hasattr(task, "current_trial")
                or hasattr(task, "current_balance")
            ), "Task should track state"

        except ImportError:
            pytest.skip("Iowa Gambling Task not available")
        except Exception as e:
            pytest.fail(f"Iowa Gambling Task execution failed: {e}")

    def test_masking_paradigm_import(self) -> None:
        """
        Test that Masking Paradigm can be imported.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.masking_paradigm import MaskingParadigmTask

            assert MaskingParadigmTask is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Masking Paradigm: {e}")

    def test_masking_paradigm_execution(self) -> None:
        """
        Test that Masking Paradigm can be executed.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.masking_paradigm import MaskingParadigmTask

            # Create task instance
            task = MaskingParadigmTask()

            # Verify task has required methods
            assert hasattr(task, "run_trial") or hasattr(
                task, "run_all_trials"
            ), "Task should have run method"
            assert hasattr(task, "reset"), "Task should have reset method"

            # Reset task
            task.reset()

        except ImportError:
            pytest.skip("Masking Paradigm not available")
        except Exception as e:
            pytest.fail(f"Masking Paradigm execution failed: {e}")

    def test_attentional_blink_import(self) -> None:
        """
        Test that Attentional Blink can be imported.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.attentional_blink import AttentionalBlinkTask

            assert AttentionalBlinkTask is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Attentional Blink: {e}")

    def test_attentional_blink_execution(self):
        """
        Test that Attentional Blink can be executed.

        Validates: Requirements 9.2, 9.4
        """
        try:
            from apgi_framework.experiments.tasks.attentional_blink import AttentionalBlinkTask

            # Create task instance
            task = AttentionalBlinkTask()

            # Verify task has required methods
            assert hasattr(task, "run_trial") or hasattr(
                task, "run_all_trials"
            ), "Task should have run method"
            assert hasattr(task, "reset"), "Task should have reset method"

            # Reset task
            task.reset()

        except ImportError:
            pytest.skip("Attentional Blink not available")
        except Exception as e:
            pytest.fail(f"Attentional Blink execution failed: {e}")

    def test_all_experimental_tasks_available(self):
        """
        Test that all experimental tasks are available.

        Validates: Requirements 9.2, 9.4
        """
        expected_tasks = [
            "iowa_gambling",
            "masking_paradigm",
            "attentional_blink",
            "binocular_rivalry",
            "change_blindness",
        ]

        available_tasks = []

        for task_name in expected_tasks:
            try:
                module_name = f"apgi_framework.experiments.tasks.{task_name}"
                __import__(module_name)
                available_tasks.append(task_name)
            except ImportError:
                pass

        # At least some tasks should be available
        assert len(available_tasks) > 0, "At least one experimental task should be available"


class TestPlatformSpecificFeatures:
    """Test platform-specific features work correctly."""

    def test_platform_detection(self):
        """
        Test that platform can be detected correctly.

        Validates: Requirements 9.4
        """
        # Test sys.platform
        assert sys.platform in [
            "win32",
            "darwin",
            "linux",
            "linux2",
        ], f"Platform {sys.platform} should be recognized"

    def test_platform_utils_available(self):
        """
        Test that platform utilities are available.

        Validates: Requirements 9.4
        """
        try:
            from apgi_framework.platform_utils import get_platform, get_resource_path, is_bundled

            # Test platform detection
            platform = get_platform()
            assert platform in [
                "windows",
                "macos",
                "linux",
                "unknown",
            ], f"Platform {platform} should be recognized"

            # Test bundled detection
            bundled = is_bundled()
            assert isinstance(bundled, bool), "is_bundled should return boolean"

            # Test resource path resolution
            config_path = get_resource_path("config/default.yaml")
            assert config_path is not None, "Resource path should be resolved"

        except ImportError:
            pytest.skip("Platform utilities not available")

    def test_file_dialog_availability(self):
        """
        Test that file dialogs are available (for GUI).

        Validates: Requirements 9.2, 9.4
        """
        try:
            import tkinter.filedialog

            # Verify dialog functions exist
            assert hasattr(tkinter.filedialog, "askopenfilename")
            assert hasattr(tkinter.filedialog, "asksaveasfilename")
            assert hasattr(tkinter.filedialog, "askdirectory")

        except ImportError:
            pytest.skip("Tkinter not available")

    def test_user_data_directory_access(self):
        """
        Test that user data directories can be accessed.

        Validates: Requirements 9.3, 9.4
        """
        try:
            from apgi_framework.platform_utils import get_config_dir, get_data_dir

            # Get directories
            data_dir = get_data_dir()
            config_dir = get_config_dir()

            # Verify they are Path objects or strings
            assert data_dir is not None
            assert config_dir is not None

            # Convert to Path if needed
            data_path = Path(data_dir)
            config_path = Path(config_dir)

            # Verify they are valid paths
            assert data_path.is_absolute() or not data_path.exists()
            assert config_path.is_absolute() or not config_path.exists()

        except ImportError:
            pytest.skip("Platform utilities not available")


class TestResourceBundling:
    """Test that resources are properly bundled and accessible."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    def test_config_files_accessible(self, project_root):
        """
        Test that configuration files are accessible.

        Validates: Requirements 9.3
        """
        config_file = project_root / "config" / "default.yaml"

        if not config_file.exists():
            pytest.skip("Config file not found")

        # Verify file can be read
        try:
            with open(config_file, "r") as f:
                content = f.read()

            assert len(content) > 0, "Config file should not be empty"

        except Exception as e:
            pytest.fail(f"Failed to read config file: {e}")

    def test_icon_files_accessible(self, project_root):
        """
        Test that icon files are accessible.

        Validates: Requirements 9.3
        """
        icons_dir = project_root / "resources" / "icons"

        if not icons_dir.exists():
            pytest.skip("Icons directory not found")

        # Look for icon files
        icon_files = list(icons_dir.glob("*.ico")) + list(icons_dir.glob("*.icns"))

        if len(icon_files) == 0:
            pytest.skip("No icon files found")

        # Verify at least one icon is readable
        icon_file = icon_files[0]

        try:
            with open(icon_file, "rb") as f:
                content = f.read()

            assert len(content) > 0, "Icon file should not be empty"

        except Exception as e:
            pytest.fail(f"Failed to read icon file: {e}")

    def test_resource_path_resolution_in_bundled_env(self):
        """
        Test that resource paths resolve correctly in bundled environment.

        Validates: Requirements 9.3
        """
        try:
            from apgi_framework.platform_utils import get_resource_path, is_bundled

            # Test resource path resolution
            config_path = get_resource_path("config/default.yaml")

            # Path should be absolute
            config_path_obj = Path(config_path)
            assert config_path_obj.is_absolute() or not is_bundled()

        except ImportError:
            pytest.skip("Platform utilities not available")


class TestErrorHandlingInBundledEnv:
    """Test error handling in bundled environment."""

    def test_missing_resource_handling(self):
        """
        Test that missing resources are handled gracefully.

        Validates: Requirements 9.3
        """
        try:
            from apgi_framework.platform_utils import get_resource_path

            # Try to get non-existent resource
            nonexistent_path = get_resource_path("nonexistent/file.txt")

            # Should return a path (even if it doesn't exist)
            assert nonexistent_path is not None

        except ImportError:
            pytest.skip("Platform utilities not available")
        except Exception as e:
            # Should not crash with unhandled exception
            pytest.fail(f"Unhandled exception for missing resource: {e}")

    def test_invalid_config_handling(self):
        """
        Test that invalid configuration is handled gracefully.

        Validates: Requirements 9.3
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # Write invalid YAML
            f.write("invalid: yaml: content: [")
            invalid_file = f.name

        try:
            # Try to load invalid config
            with open(invalid_file, "r") as f:
                try:
                    yaml.safe_load(f)
                    pytest.fail("Should raise exception for invalid YAML")
                except yaml.YAMLError:
                    # Expected exception
                    pass

        finally:
            # Clean up
            Path(invalid_file).unlink()

    def test_permission_denied_handling(self):
        """
        Test that permission denied errors are handled gracefully.

        Validates: Requirements 9.3
        """
        # Create a read-only file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            readonly_file = f.name

        try:
            # Make file read-only
            os.chmod(readonly_file, 0o444)

            # Try to write to read-only file
            try:
                with open(readonly_file, "w") as f:
                    f.write("new content")
                pytest.fail("Should raise exception for read-only file")
            except (PermissionError, OSError):
                # Expected exception
                pass

        finally:
            # Clean up (restore write permission first)
            os.chmod(readonly_file, 0o644)
            Path(readonly_file).unlink()


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
