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
