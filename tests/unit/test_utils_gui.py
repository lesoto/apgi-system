"""
Unit tests for Utils GUI application components.

This module implements unit tests for the APGI Utils GUI application,
testing initialization, utility execution, result display, and
configuration management without launching the full GUI.

Tests focus on the backend logic that powers the Utils GUI functionality.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest


def load_module_from_file(module_name: str, file_path: Path):
    """Load a Python module from a file path, handling hyphenated filenames."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import GUI class with error handling
try:
    # Utils-GUI.py is a thin wrapper that imports from utils.script_runner_gui
    # Import directly from script_runner_gui for testing
    from utils.script_runner_gui import ScriptRunnerGUI  # type: ignore

    HAS_UTILS_GUI = True
except ImportError as e:
    HAS_UTILS_GUI = False
    ScriptRunnerGUI = None  # type: ignore
    print(f"Warning: Could not import ScriptRunnerGUI: {e}")


def create_utils_runner_gui(root):
    """Create a ScriptRunnerGUI instance with utils configuration."""
    if ScriptRunnerGUI is None:
        raise ImportError("ScriptRunnerGUI not available")
    return ScriptRunnerGUI(
        root,
        script_dir_name="utils",
        title="APGI Utils Scripts Runner",
        script_list_label="Available Scripts",
        run_all_text="Run All Scripts",
        tooltip_selected="Run the currently selected script",
        tooltip_all="Run all scripts in sequence",
        tooltip_stop="Stop the currently running script",
    )


class TestUtilsGUIInitialization:
    """Test Utils GUI initialization and setup."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_gui_launches_without_errors(self: Any) -> None:
        """
        Test that Utils GUI can be initialized without errors.

        This test verifies that the GUI window can be created and
        all components are properly initialized.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Verify GUI was created
            assert app is not None
            assert app.root is root

            # Verify UI components were created
            assert hasattr(app, "main_frame")
            assert hasattr(app, "control_frame")
            assert hasattr(app, "output_frame")

            # Verify utility selection
            assert hasattr(app, "utility_var")
            assert app.utility_var is not None

            # Verify text widgets
            assert hasattr(app, "output_text")
            assert app.output_text is not None

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_gui_initializes_with_available_utilities(self: Any) -> None:
        """
        Test that GUI initializes with list of available utilities.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Verify utilities list exists
            assert hasattr(app, "utilities")
            assert isinstance(app.utilities, list)
            assert len(app.utilities) > 0

            # Verify utility descriptions
            assert hasattr(app, "utility_descriptions")
            assert isinstance(app.utility_descriptions, dict)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_output_display_widgets_created(self: Any) -> None:
        """
        Test that output display widgets are properly created.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Verify output text widget
            assert app.output_text.winfo_exists()

            # Verify scrollbars
            assert hasattr(app, "output_scrollbar")
            assert app.output_scrollbar is not None

            # Verify status label
            assert hasattr(app, "status_label")
            assert app.status_label is not None

        finally:
            root.quit()
            root.destroy()


class TestUtilityExecution:
    """Test utility execution functionality."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_utility_selection_validation(self: Any) -> None:
        """
        Test that utility selection validation works correctly.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Test valid utility selection
            if app.utilities:
                valid_utility = app.utilities[0]
                assert app._validate_utility_selection(valid_utility)

            # Test invalid utility selection
            assert not app._validate_utility_selection("invalid_utility")
            assert not app._validate_utility_selection("")

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_utility_execution_with_mock_subprocess(self: Any) -> None:
        """
        Test utility execution with mocked subprocess calls.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Mock subprocess.run
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                # Execute a utility
                if app.utilities:
                    utility = app.utilities[0]
                    app._execute_utility(utility)

                    # Verify subprocess was called
                    mock_run.assert_called()

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_utility_execution_error_handling(self: Any) -> None:
        """
        Test error handling during utility execution.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Mock subprocess.run to simulate error
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "test_cmd", "Error output")

                # Execute utility (should handle error gracefully)
                if app.utilities:
                    utility = app.utilities[0]
                    app._execute_utility(utility)

                    # Should not raise exception
                    assert True

        finally:
            root.quit()
            root.destroy()


class TestOutputDisplay:
    """Test output display and formatting."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_output_text_display(self: Any) -> None:
        """
        Test displaying text output in the GUI.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Display some test output
            test_output = "Test utility output\nLine 2\nLine 3"
            app._display_output(test_output)

            # Verify output was displayed
            displayed_text = app.output_text.get(1.0, tk.END).strip()
            assert test_output in displayed_text

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_output_clearing(self: Any) -> None:
        """
        Test clearing output display.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Add some output
            app._display_output("Test output")
            assert len(app.output_text.get(1.0, tk.END).strip()) > 0

            # Clear output
            app._clear_output()
            displayed_text = app.output_text.get(1.0, tk.END).strip()
            assert displayed_text == ""

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_status_updates(self: Any) -> None:
        """
        Test status label updates during execution.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Update status
            test_status = "Running utility..."
            app._update_status(test_status)

            # Verify status was updated
            assert app.status_label.cget("text") == test_status

        finally:
            root.quit()
            root.destroy()


class TestConfigurationManagement:
    """Test configuration and settings management."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_configuration_loading(self: Any) -> None:
        """
        Test loading utility configurations.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Verify configuration was loaded
            assert hasattr(app, "config")
            assert isinstance(app.config, dict)

            # Verify expected config keys
            assert "timeout" in app.config
            assert "working_directory" in app.config

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_configuration_validation(self: Any) -> None:
        """
        Test configuration parameter validation.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Test valid configuration
            valid_config = {"timeout": 30, "working_directory": "/tmp", "environment_vars": {}}
            assert app._validate_config(valid_config)

            # Test invalid configuration
            invalid_config = {
                "timeout": -1,  # Invalid negative timeout
                "working_directory": "/nonexistent/path",
            }
            assert not app._validate_config(invalid_config)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_configuration_save_and_load(self: Any) -> None:
        """
        Test saving and loading configuration files.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Modify configuration
            app.config["timeout"] = 60

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_filename = f.name

            try:
                app._save_config(config_filename)

                # Load configuration
                app._load_config(config_filename)
                assert app.config["timeout"] == 60

            finally:
                import os

                os.unlink(config_filename)

        finally:
            root.quit()
            root.destroy()


class TestDataExport:
    """Test data export functionality."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_export_output_to_file(self: Any) -> None:
        """
        Test exporting utility output to file.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Set some output
            test_output = "Utility execution output\nResult: Success"
            app._display_output(test_output)

            # Export to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                output_filename = f.name

            try:
                app._export_output(output_filename)

                # Verify file was created and contains output
                with open(output_filename, "r") as f:
                    file_content = f.read()

                assert test_output in file_content

            finally:
                import os

                os.unlink(output_filename)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_export_execution_log_to_json(self: Any) -> None:
        """
        Test exporting execution log to JSON.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Simulate some execution history
            app.execution_history = [
                {
                    "timestamp": "2024-01-01T12:00:00",
                    "utility": "test_utility",
                    "exit_code": 0,
                    "output": "Success",
                }
            ]

            # Export to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                log_filename = f.name

            try:
                app._export_execution_log(log_filename)

                # Verify file was created and contains data
                with open(log_filename, "r") as f:
                    data = json.load(f)

                assert len(data) == 1
                assert data[0]["utility"] == "test_utility"
                assert data[0]["exit_code"] == 0

            finally:
                import os

                os.unlink(log_filename)

        finally:
            root.quit()
            root.destroy()


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_utility_not_found_handling(self: Any) -> None:
        """
        Test handling when selected utility is not found.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Try to execute non-existent utility
            app._execute_utility("nonexistent_utility")

            # Should not raise exception and should update status
            assert True

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_timeout_handling(self: Any) -> None:
        """
        Test handling of utility execution timeouts.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Mock subprocess.run to simulate timeout
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("test_cmd", 30)

                # Execute utility (should handle timeout gracefully)
                if app.utilities:
                    utility = app.utilities[0]
                    app._execute_utility(utility)

                    # Should not raise exception
                    assert True

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_file_operation_error_handling(self: Any) -> None:
        """
        Test handling of file operation errors.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Try to export to invalid path
            app._export_output("/invalid/path/file.txt")

            # Should not raise exception
            assert True

        finally:
            root.quit()
            root.destroy()


class TestThreadingAndAsync:
    """Test threading and asynchronous operations."""

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_utility_execution_threading(self: Any) -> None:
        """
        Test that utility execution runs in separate thread.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Mock the execution method
            with patch.object(app, "_execute_utility"):
                # Start utility execution
                if app.utilities:
                    utility = app.utilities[0]
                    app._run_utility_threaded(utility)

                    # Verify threading setup
                    assert app.execution_thread is not None

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_UTILS_GUI, reason="ScriptRunnerGUI not available")
    def test_ui_update_threading(self: Any) -> None:
        """
        Test UI updates from background threads.
        """
        root = tk.Tk()

        try:
            app = create_utils_runner_gui(root)

            # Test thread-safe UI updates
            initial_status = app.status_label.cget("text")

            # Update from "background thread" (simulated)
            app.root.after(10, lambda: app._update_status("Updated from thread"))

            # Wait for update
            app.root.update()
            import time

            time.sleep(0.1)
            app.root.update()

            # Status should have been updated
            assert app.status_label.cget("text") != initial_status

        finally:
            root.quit()
            root.destroy()


if __name__ == "__main__":
    pytest.main([__file__])
