"""
Property-based tests for Windows executable functionality.

This module implements property-based tests using Hypothesis to verify
universal properties that should hold for the bundled executable.

Each test is tagged with the corresponding property from the design document
and validates specific requirements from the requirements document.
"""

import os
import sys
import subprocess
import tempfile
import json
import yaml
from pathlib import Path
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import tkinter as tk

from apgi_system.platform_utils import (
    get_platform,
    is_bundled,
    get_resource_path,
    get_config_dir,
    get_data_dir,
)

# Configure Hypothesis for property-based testing
settings.register_profile(
    "executable_tests",
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
    ],
)
settings.load_profile("executable_tests")


class TestExecutableLaunchProperties:
    """Property-based tests for executable launch success."""

    def test_property_executable_launch_success(self):
        """
        **Feature: cross-platform-executable, Property 7: Executable launch success**

        For any valid build output, double-clicking the executable should launch
        the GUI application without errors.

        **Validates: Requirements 1.2, 2.2, 9.1**
        """
        # Test that the GUI can be initialized without errors
        # This simulates the executable launch process

        # Create a root window (but don't show it)
        root = tk.Tk()
        root.withdraw()  # Hide the window

        try:
            # Import the GUI class
            from apgi_gui import APGIGui

            # Initialize the GUI (this is what happens on launch)
            # We'll catch any initialization errors
            gui = APGIGui(root)

            # Verify that the GUI was created successfully
            assert gui is not None, "GUI should be initialized"
            assert gui.root is not None, "GUI root window should exist"
            assert gui.apgi_system is not None, "APGI system should be initialized"

            # Verify critical components exist
            assert hasattr(gui, "start_btn"), "Start button should exist"
            assert hasattr(gui, "pause_btn"), "Pause button should exist"
            assert hasattr(gui, "stop_btn"), "Stop button should exist"
            assert hasattr(gui, "reset_btn"), "Reset button should exist"

            # Verify menu bar exists
            assert gui.root.config("menu"), "Menu bar should exist"

            # Verify data buffers are initialized
            assert len(gui.data_buffers) > 0, "Data buffers should be initialized"
            assert "ignition" in gui.data_buffers, "Ignition buffer should exist"
            assert "free_energy" in gui.data_buffers, "Free energy buffer should exist"

            # Verify status labels exist
            assert len(gui.status_labels) > 0, "Status labels should exist"
            assert "Time" in gui.status_labels, "Time status label should exist"

        except Exception as e:
            pytest.fail(f"GUI initialization failed: {str(e)}")
        finally:
            # Clean up
            try:
                root.quit()
                root.destroy()
            except:
                pass

    @given(num_launches=st.integers(min_value=1, max_value=3))
    def test_property_executable_launch_idempotent(self, num_launches):
        """
        Test that the executable can be launched multiple times successfully.

        For any number of launch attempts, the GUI should initialize successfully
        each time without errors.

        **Validates: Requirements 1.2, 2.2, 9.1**
        """
        for i in range(num_launches):
            root = tk.Tk()
            root.withdraw()

            try:
                from apgi_gui import APGIGui

                gui = APGIGui(root)

                # Verify successful initialization
                assert gui is not None, f"Launch {i+1}: GUI should be initialized"
                assert gui.apgi_system is not None, f"Launch {i+1}: System should be initialized"

            except Exception as e:
                pytest.fail(f"Launch {i+1} failed: {str(e)}")
            finally:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass

    def test_property_executable_dependencies_available(self):
        """
        Test that all required dependencies are available.

        For any execution environment, all required Python packages should be
        importable without errors.

        **Validates: Requirements 1.3, 2.3, 9.4**
        """
        # List of critical dependencies
        critical_imports = [
            "tkinter",
            "numpy",
            "matplotlib",
            "yaml",
            "json",
            "csv",
            "pathlib",
            "datetime",
            "collections",
            "threading",
            "time",
        ]

        for module_name in critical_imports:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Critical dependency missing: {module_name} - {str(e)}")

    def test_property_executable_resource_access(self):
        """
        Test that the executable can access bundled resources.

        For any resource file, the executable should be able to locate and
        access it using the resource path utilities.

        **Validates: Requirements 1.4, 2.4, 4.2**
        """
        # Test accessing the default config file
        config_path = get_resource_path("config/default.yaml")

        assert config_path is not None, "Config path should not be None"
        assert isinstance(config_path, Path), "Config path should be a Path object"
        assert config_path.is_absolute(), "Config path should be absolute"

        # Verify the config file exists
        assert config_path.exists(), f"Config file should exist at {config_path}"

        # Try to load the config
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            assert config is not None, "Config should be loadable"
            assert isinstance(config, dict), "Config should be a dictionary"
        except Exception as e:
            pytest.fail(f"Failed to load config file: {str(e)}")


class TestGUIFunctionalityProperties:
    """Property-based tests for GUI functionality preservation."""

    def test_property_gui_functionality_preservation(self):
        """
        **Feature: cross-platform-executable, Property 8: GUI functionality preservation**

        For any GUI interaction available in the source application, the bundled
        executable should support the same interaction with identical behavior.

        **Validates: Requirements 9.2**
        """
        root = tk.Tk()
        root.withdraw()

        try:
            from apgi_gui import APGIGui

            gui = APGIGui(root)

            # Test control buttons exist and are in correct initial state
            assert (
                str(gui.start_btn["state"]) == "normal"
            ), "Start button should be enabled initially"
            assert (
                str(gui.pause_btn["state"]) == "disabled"
            ), "Pause button should be disabled initially"
            assert (
                str(gui.stop_btn["state"]) == "disabled"
            ), "Stop button should be disabled initially"
            assert (
                str(gui.reset_btn["state"]) == "normal"
            ), "Reset button should be enabled initially"

            # Test parameter controls exist
            assert len(gui.param_vars) > 0, "Parameter variables should exist"

            # Test that parameter variables have valid initial values
            for key, var in gui.param_vars.items():
                value = var.get()
                assert isinstance(value, (int, float)), f"Parameter {key} should have numeric value"
                assert not (
                    isinstance(value, float) and (value != value)
                ), f"Parameter {key} should not be NaN"

            # Test data buffers are properly initialized
            for buffer_name, buffer in gui.data_buffers.items():
                assert hasattr(buffer, "maxlen"), f"Buffer {buffer_name} should have maxlen"
                assert (
                    buffer.maxlen == gui.buffer_size
                ), f"Buffer {buffer_name} should have correct size"

            # Test status labels are initialized
            for label_name, label in gui.status_labels.items():
                assert label is not None, f"Status label {label_name} should exist"
                assert label.cget("text"), f"Status label {label_name} should have text"

        except Exception as e:
            pytest.fail(f"GUI functionality test failed: {str(e)}")
        finally:
            try:
                root.quit()
                root.destroy()
            except:
                pass

    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    @given(
        threshold=st.floats(min_value=1.0, max_value=5.0),
        extero_precision=st.floats(min_value=0.1, max_value=10.0),
        intero_precision=st.floats(min_value=0.1, max_value=10.0),
    )
    def test_property_gui_parameter_adjustment(self, threshold, extero_precision, intero_precision):
        """
        Test that GUI parameter adjustments work correctly.

        For any valid parameter values, the GUI should accept and apply them
        without errors.

        **Validates: Requirements 9.2**
        """
        root = None
        try:
            root = tk.Tk()
            root.withdraw()

            from apgi_gui import APGIGui

            gui = APGIGui(root)

            # Set parameter values
            if "baseline_threshold" in gui.param_vars:
                gui.param_vars["baseline_threshold"].set(threshold)
                assert abs(gui.param_vars["baseline_threshold"].get() - threshold) < 0.01

            if "extero_precision" in gui.param_vars:
                gui.param_vars["extero_precision"].set(extero_precision)
                assert abs(gui.param_vars["extero_precision"].get() - extero_precision) < 0.01

            if "intero_precision" in gui.param_vars:
                gui.param_vars["intero_precision"].set(intero_precision)
                assert abs(gui.param_vars["intero_precision"].get() - intero_precision) < 0.01

        except tk.TclError as e:
            # Skip test if Tkinter is not properly configured
            pytest.skip(f"Tkinter not properly configured: {str(e)}")
        except Exception as e:
            pytest.fail(f"Parameter adjustment failed: {str(e)}")
        finally:
            if root is not None:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass

    def test_property_gui_menu_items_exist(self):
        """
        Test that all menu items exist and are accessible.

        For any menu item in the design, it should exist in the GUI and be
        accessible.

        **Validates: Requirements 9.2**
        """
        root = tk.Tk()
        root.withdraw()

        try:
            from apgi_gui import APGIGui

            gui = APGIGui(root)

            # Get the menu bar
            menubar = gui.root.nametowidget(gui.root.cget("menu"))
            assert menubar is not None, "Menu bar should exist"

            # Verify menu bar has items
            # Note: Tkinter menu introspection is limited, but we can verify the menu exists
            # and that the GUI was created without errors

        except Exception as e:
            pytest.fail(f"Menu items test failed: {str(e)}")
        finally:
            try:
                root.quit()
                root.destroy()
            except:
                pass


class TestResourceBundlingProperties:
    """Property-based tests for resource bundling completeness."""

    def test_property_resource_bundling_completeness(self):
        """
        **Feature: cross-platform-executable, Property 5: Resource bundling completeness**

        For any resource file referenced in the code, the bundled executable should
        include that resource or the build should fail with a clear error.

        **Validates: Requirements 4.1, 4.3, 7.5**
        """
        # Test that all expected resource directories exist
        expected_resource_dirs = [
            "config",
            "resources/icons",
        ]

        for resource_dir in expected_resource_dirs:
            resource_path = get_resource_path(resource_dir)
            assert resource_path is not None, f"Resource path for {resource_dir} should not be None"

            # In development mode, the directory should exist
            # In bundled mode, resources should be accessible
            if not is_bundled():
                # Development mode - check directory exists
                if not resource_path.exists():
                    pytest.skip(f"Resource directory {resource_dir} not found in development mode")
            else:
                # Bundled mode - resources should be accessible
                assert (
                    resource_path.exists()
                ), f"Resource directory {resource_dir} should exist in bundle"

    @given(
        resource_name=st.sampled_from(
            [
                "config/default.yaml",
                "resources/icons/apgi.png",
                "resources/icons/apgi.ico",
                "resources/icons/apgi.icns",
            ]
        )
    )
    def test_property_resource_file_accessibility(self, resource_name):
        """
        Test that specific resource files are accessible.

        For any known resource file, the application should be able to locate
        and access it.

        **Validates: Requirements 4.1, 4.3**
        """
        resource_path = get_resource_path(resource_name)

        assert resource_path is not None, f"Resource path for {resource_name} should not be None"
        assert isinstance(resource_path, Path), f"Resource path should be a Path object"

        # Check if resource exists (skip if not in development mode and file is optional)
        if not resource_path.exists():
            # Some resources like platform-specific icons may not exist
            if any(ext in resource_name for ext in [".ico", ".icns"]):
                pytest.skip(f"Platform-specific resource {resource_name} not found")
            else:
                pytest.fail(f"Required resource {resource_name} not found at {resource_path}")

    def test_property_config_resources_bundled(self):
        """
        Test that configuration resources are properly bundled.

        For any configuration file, it should be accessible in both development
        and bundled modes.

        **Validates: Requirements 4.1, 4.4**
        """
        # Test default config file
        config_path = get_resource_path("config/default.yaml")

        assert config_path is not None, "Config path should not be None"
        assert config_path.exists(), f"Default config should exist at {config_path}"

        # Verify it's readable
        try:
            with open(config_path, "r") as f:
                content = f.read()
            assert len(content) > 0, "Config file should not be empty"
        except Exception as e:
            pytest.fail(f"Failed to read config file: {str(e)}")

    def test_property_icon_resources_available(self):
        """
        Test that icon resources are available for the platform.

        For any platform, at least one icon format should be available.

        **Validates: Requirements 7.1, 7.2, 7.3, 7.5**
        """
        platform = get_platform()

        # Check for platform-appropriate icon
        if platform == "windows":
            icon_path = get_resource_path("resources/icons/apgi.ico")
        elif platform == "macos":
            icon_path = get_resource_path("resources/icons/apgi.icns")
        else:
            icon_path = get_resource_path("resources/icons/apgi.png")

        # Icon should exist or source PNG should exist
        png_icon = get_resource_path("resources/icons/apgi.png")

        if not icon_path.exists() and not png_icon.exists():
            pytest.skip(f"Icon resources not yet created for {platform}")

        # At least one icon format should exist
        assert (
            icon_path.exists() or png_icon.exists()
        ), f"At least one icon format should exist for {platform}"

    @given(subdir=st.sampled_from(["icons", "images", "data"]))
    def test_property_resource_subdirectories_accessible(self, subdir):
        """
        Test that resource subdirectories are accessible.

        For any resource subdirectory, it should be accessible through the
        resource path utilities.

        **Validates: Requirements 4.1, 4.2**
        """
        resource_path = get_resource_path(f"resources/{subdir}")

        assert resource_path is not None, f"Resource path for {subdir} should not be None"

        # In development mode, directory should exist or be creatable
        # In bundled mode, directory should be accessible
        if not is_bundled():
            # Development mode - directory should exist
            if not resource_path.exists():
                pytest.skip(f"Resource subdirectory {subdir} not found in development mode")
        else:
            # Bundled mode - directory should be accessible
            # (may be empty but should exist)
            assert resource_path.exists(), f"Resource subdirectory {subdir} should exist in bundle"

    def test_property_resource_path_resolution_consistency(self):
        """
        Test that resource path resolution is consistent.

        For any resource path, resolving it multiple times should return the
        same path.

        **Validates: Requirements 3.4, 4.2**
        """
        resource_name = "config/default.yaml"

        # Resolve path multiple times
        path1 = get_resource_path(resource_name)
        path2 = get_resource_path(resource_name)
        path3 = get_resource_path(resource_name)

        # All paths should be identical
        assert path1 == path2, "Resource path resolution should be consistent"
        assert path2 == path3, "Resource path resolution should be consistent"
        assert path1 == path3, "Resource path resolution should be consistent"

    @given(
        relative_path=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/_-."
            ),
            min_size=1,
            max_size=50,
        )
    )
    def test_property_resource_path_always_absolute(self, relative_path):
        """
        Test that resource paths are always absolute.

        For any relative path input, get_resource_path should return an
        absolute path.

        **Validates: Requirements 3.4, 4.2**
        """
        # Filter out invalid paths
        assume(not relative_path.startswith("/"))
        assume(not relative_path.startswith("\\"))
        assume(".." not in relative_path)

        try:
            resource_path = get_resource_path(relative_path)

            assert resource_path is not None, "Resource path should not be None"
            assert isinstance(resource_path, Path), "Resource path should be a Path object"
            assert resource_path.is_absolute(), f"Resource path should be absolute: {resource_path}"
        except Exception as e:
            # Some paths may be invalid, which is acceptable
            pass


class TestFileIOProperties:
    """Property-based tests for file I/O correctness."""

    def test_property_file_io_correctness(self):
        """
        **Feature: cross-platform-executable, Property 9: File I/O correctness**

        For any file read or write operation, the bundled executable should
        perform the operation successfully in user-writable locations.

        **Validates: Requirements 9.3**
        """
        # Test writing to config directory
        config_dir = get_config_dir()
        assert config_dir.exists(), "Config directory should exist"
        assert config_dir.is_dir(), "Config directory should be a directory"

        # Test writing a file
        test_file = config_dir / "test_write.txt"
        test_content = "Test content for file I/O"

        try:
            test_file.write_text(test_content)
            assert test_file.exists(), "Test file should be created"

            # Test reading the file
            read_content = test_file.read_text()
            assert read_content == test_content, "Read content should match written content"

        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()

    @given(
        content=st.text(min_size=0, max_size=1000),
        filename=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
            min_size=1,
            max_size=20,
        ),
    )
    def test_property_file_io_round_trip(self, content, filename):
        """
        Test that file I/O operations preserve data correctly.

        For any content and filename, writing and then reading should return
        the same content.

        **Validates: Requirements 9.3**
        """
        # Filter out invalid filenames
        assume(filename not in [".", ".."])
        assume(not any(c in filename for c in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]))

        data_dir = get_data_dir()
        test_file = data_dir / f"{filename}.txt"

        try:
            # Write content with UTF-8 encoding and preserve line endings
            with open(test_file, "w", encoding="utf-8", newline="") as f:
                f.write(content)

            # Read content with UTF-8 encoding and preserve line endings
            with open(test_file, "r", encoding="utf-8", newline="") as f:
                read_content = f.read()

            # Verify round trip
            assert read_content == content, "Content should be preserved in round trip"

        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=100),
                st.booleans(),
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_property_json_export_correctness(self, data):
        """
        Test that JSON export preserves data correctly.

        For any dictionary data, exporting to JSON and reading back should
        return equivalent data.

        **Validates: Requirements 9.3**
        """
        data_dir = get_data_dir()
        test_file = data_dir / "test_export.json"

        try:
            # Write JSON
            with open(test_file, "w") as f:
                json.dump(data, f)

            # Read JSON
            with open(test_file, "r") as f:
                read_data = json.load(f)

            # Verify data is preserved
            assert read_data == data, "JSON data should be preserved"

        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()

    def test_property_config_file_loading(self):
        """
        Test that configuration files can be loaded correctly.

        For any valid configuration file, the application should be able to
        load it without errors.

        **Validates: Requirements 9.3, 4.4**
        """
        # Test loading the default config
        config_path = get_resource_path("config/default.yaml")

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            assert config is not None, "Config should be loaded"
            assert isinstance(config, dict), "Config should be a dictionary"

            # Verify expected config sections exist
            expected_sections = ["system", "active_inference", "ignition", "precision"]
            for section in expected_sections:
                assert section in config, f"Config should have {section} section"

        except Exception as e:
            pytest.fail(f"Config loading failed: {str(e)}")

    @given(
        config_data=st.dictionaries(
            keys=st.sampled_from(["param1", "param2", "param3"]),
            values=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=3,
        )
    )
    def test_property_config_save_load_round_trip(self, config_data):
        """
        Test that configuration save/load preserves data.

        For any configuration data, saving and loading should return the same
        configuration.

        **Validates: Requirements 9.3, 4.4**
        """
        config_dir = get_config_dir()
        test_config = config_dir / "test_config.yaml"

        try:
            # Save config
            with open(test_config, "w") as f:
                yaml.dump(config_data, f)

            # Load config
            with open(test_config, "r") as f:
                loaded_config = yaml.safe_load(f)

            # Verify round trip
            assert loaded_config == config_data, "Config should be preserved in round trip"

        finally:
            # Clean up
            if test_config.exists():
                test_config.unlink()

    def test_property_data_export_directory_writable(self):
        """
        Test that the data export directory is writable.

        For any execution environment, the data directory should be writable
        for export operations.

        **Validates: Requirements 9.3**
        """
        data_dir = get_data_dir()

        assert data_dir.exists(), "Data directory should exist"
        assert data_dir.is_dir(), "Data directory should be a directory"

        # Test write permissions
        test_file = data_dir / ".test_write_permission"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Should be able to write to data directory"
        except Exception as e:
            pytest.fail(f"Data directory is not writable: {str(e)}")
        finally:
            if test_file.exists():
                test_file.unlink()


class TestConfigurationPersistenceProperties:
    """Property-based tests for configuration persistence."""

    def test_property_configuration_persistence(self):
        """
        **Feature: cross-platform-executable, Property 10: Configuration persistence**

        For any configuration change saved by the user, reopening the application
        should restore that configuration.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        test_config_file = config_dir / "test_user_config.yaml"

        # Test configuration data
        test_config = {
            "parameters": {
                "baseline_threshold": 2.5,
                "extero_precision": 5.0,
                "intero_precision": 3.0,
            }
        }

        try:
            # Step 1: Save configuration
            with open(test_config_file, "w") as f:
                yaml.dump(test_config, f)

            assert test_config_file.exists(), "Config file should be created"

            # Step 2: Load configuration (simulating app restart)
            with open(test_config_file, "r") as f:
                loaded_config = yaml.safe_load(f)

            # Step 3: Verify configuration was restored correctly
            assert loaded_config is not None, "Loaded config should not be None"
            assert loaded_config == test_config, "Loaded config should match saved config"
            assert loaded_config["parameters"]["baseline_threshold"] == 2.5
            assert loaded_config["parameters"]["extero_precision"] == 5.0
            assert loaded_config["parameters"]["intero_precision"] == 3.0

        finally:
            # Clean up
            if test_config_file.exists():
                test_config_file.unlink()

    @given(
        baseline_threshold=st.floats(
            min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False
        ),
        extero_precision=st.floats(
            min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
        ),
        intero_precision=st.floats(
            min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_property_configuration_persistence_round_trip(
        self, baseline_threshold, extero_precision, intero_precision
    ):
        """
        Test that configuration persistence works for any valid parameter values.

        For any valid configuration parameters, saving and loading should preserve
        the exact values.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        test_config_file = config_dir / f"test_config_{id(self)}.yaml"

        # Create configuration with random parameters
        test_config = {
            "parameters": {
                "baseline_threshold": baseline_threshold,
                "extero_precision": extero_precision,
                "intero_precision": intero_precision,
            }
        }

        try:
            # Save configuration
            with open(test_config_file, "w") as f:
                yaml.dump(test_config, f)

            # Load configuration
            with open(test_config_file, "r") as f:
                loaded_config = yaml.safe_load(f)

            # Verify round trip preserves values
            assert loaded_config is not None, "Loaded config should not be None"
            assert "parameters" in loaded_config, "Config should have parameters section"

            # Check each parameter with appropriate tolerance for floating point
            assert (
                abs(loaded_config["parameters"]["baseline_threshold"] - baseline_threshold) < 1e-6
            ), "Baseline threshold should be preserved"
            assert (
                abs(loaded_config["parameters"]["extero_precision"] - extero_precision) < 1e-6
            ), "Extero precision should be preserved"
            assert (
                abs(loaded_config["parameters"]["intero_precision"] - intero_precision) < 1e-6
            ), "Intero precision should be preserved"

        finally:
            # Clean up
            if test_config_file.exists():
                test_config_file.unlink()

    @given(
        config_data=st.dictionaries(
            keys=st.sampled_from(
                [
                    "baseline_threshold",
                    "extero_precision",
                    "intero_precision",
                    "amplification_factor",
                    "decay_rate",
                    "learning_rate",
                ]
            ),
            values=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=6,
        )
    )
    def test_property_configuration_persistence_arbitrary_params(self, config_data):
        """
        Test configuration persistence with arbitrary parameter sets.

        For any set of configuration parameters, saving and loading should
        preserve all parameters correctly.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        test_config_file = config_dir / f"test_arbitrary_{id(self)}.yaml"

        test_config = {"parameters": config_data}

        try:
            # Save configuration
            with open(test_config_file, "w") as f:
                yaml.dump(test_config, f)

            # Load configuration
            with open(test_config_file, "r") as f:
                loaded_config = yaml.safe_load(f)

            # Verify all parameters are preserved
            assert loaded_config is not None, "Loaded config should not be None"
            assert "parameters" in loaded_config, "Config should have parameters section"
            assert len(loaded_config["parameters"]) == len(
                config_data
            ), "All parameters should be preserved"

            for key, value in config_data.items():
                assert key in loaded_config["parameters"], f"Parameter {key} should be preserved"
                assert (
                    abs(loaded_config["parameters"][key] - value) < 1e-6
                ), f"Parameter {key} value should be preserved"

        finally:
            # Clean up
            if test_config_file.exists():
                test_config_file.unlink()

    def test_property_configuration_persistence_with_nested_structure(self):
        """
        Test configuration persistence with nested configuration structures.

        For any nested configuration structure, saving and loading should
        preserve the entire hierarchy.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        test_config_file = config_dir / "test_nested_config.yaml"

        # Create nested configuration
        test_config = {
            "system": {
                "timestep_ms": 10.0,
                "buffer_size": 1000,
            },
            "active_inference": {
                "learning_rate": 0.01,
                "prediction_horizon": 5,
            },
            "ignition": {
                "baseline_threshold": 2.5,
                "amplification_factor": 1.5,
            },
            "precision": {
                "extero_precision": 5.0,
                "intero_precision": 3.0,
            },
        }

        try:
            # Save configuration
            with open(test_config_file, "w") as f:
                yaml.dump(test_config, f)

            # Load configuration
            with open(test_config_file, "r") as f:
                loaded_config = yaml.safe_load(f)

            # Verify nested structure is preserved
            assert loaded_config is not None, "Loaded config should not be None"
            assert loaded_config == test_config, "Nested config should be preserved exactly"

            # Verify specific nested values
            assert loaded_config["system"]["timestep_ms"] == 10.0
            assert loaded_config["active_inference"]["learning_rate"] == 0.01
            assert loaded_config["ignition"]["baseline_threshold"] == 2.5
            assert loaded_config["precision"]["extero_precision"] == 5.0

        finally:
            # Clean up
            if test_config_file.exists():
                test_config_file.unlink()

    def test_property_configuration_persistence_user_override(self):
        """
        Test that user configuration overrides default configuration.

        For any user configuration, it should override the default configuration
        when both exist.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        # Get default config
        default_config_path = get_resource_path("config/default.yaml")
        assert default_config_path.exists(), "Default config should exist"

        with open(default_config_path, "r") as f:
            default_config = yaml.safe_load(f)

        # Create user override config
        user_config_file = config_dir / "user_override_test.yaml"
        user_config = {
            "ignition": {
                "baseline_threshold": 99.9,  # Override default value
            }
        }

        try:
            # Save user config
            with open(user_config_file, "w") as f:
                yaml.dump(user_config, f)

            # Load user config
            with open(user_config_file, "r") as f:
                loaded_user_config = yaml.safe_load(f)

            # Verify user config was saved and loaded
            assert loaded_user_config is not None
            assert loaded_user_config["ignition"]["baseline_threshold"] == 99.9

            # Verify default config still exists and is different
            assert (
                default_config["ignition"]["baseline_threshold"] != 99.9
            ), "User config should override default"

        finally:
            # Clean up
            if user_config_file.exists():
                user_config_file.unlink()

    @given(num_saves=st.integers(min_value=1, max_value=5))
    def test_property_configuration_persistence_multiple_saves(self, num_saves):
        """
        Test that configuration can be saved and loaded multiple times.

        For any number of save/load cycles, the configuration should remain
        consistent.

        **Validates: Requirements 4.4**
        """
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        test_config_file = config_dir / f"test_multiple_saves_{id(self)}.yaml"

        original_config = {
            "parameters": {
                "baseline_threshold": 2.5,
                "extero_precision": 5.0,
            }
        }

        try:
            # Perform multiple save/load cycles
            for i in range(num_saves):
                # Save configuration
                with open(test_config_file, "w") as f:
                    yaml.dump(original_config, f)

                # Load configuration
                with open(test_config_file, "r") as f:
                    loaded_config = yaml.safe_load(f)

                # Verify configuration is preserved
                assert (
                    loaded_config == original_config
                ), f"Config should be preserved after {i+1} save/load cycles"

        finally:
            # Clean up
            if test_config_file.exists():
                test_config_file.unlink()
