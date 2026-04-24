"""
Test suite for refactored GUI components.

Tests the modular GUI architecture to ensure all components work correctly
and maintain backward compatibility.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Detect headless environment early
IS_HEADLESS = os.environ.get("CI") == "true" or os.environ.get("DISPLAY") is None

# Skip GUI tests entirely in headless environments
if IS_HEADLESS:
    pytest.skip("Headless environment - skipping all GUI tests", allow_module_level=True)

try:
    import tkinter as tk

    # Test if tkinter can actually create a window
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        TKINTER_AVAILABLE = True
    except Exception:
        TKINTER_AVAILABLE = False
except ImportError:
    TKINTER_AVAILABLE = False

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test imports
try:
    from apgi_framework.gui.components.logging_panel import LoggingPanel
    from apgi_framework.gui.components.main_gui_controller import MainGUIController
    from apgi_framework.gui.components.parameter_config_panel import (
        ParameterConfigPanel,
    )
    from apgi_framework.gui.components.results_visualization_panel import (
        ResultsVisualizationPanel,
    )
    from apgi_framework.gui.components.test_execution_panel import TestExecutionPanel

    GUI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"GUI components not available for testing: {e}")
    GUI_COMPONENTS_AVAILABLE = False


@pytest.mark.skipif(
    not (TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE),
    reason="GUI components not available",
)
class TestParameterConfigPanel:
    """Test the Parameter Configuration Panel."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests

        # Mock config manager
        self.mock_config_manager = Mock()
        self.mock_config_manager.load_config.return_value = {}
        self.mock_config_manager.save_config.return_value = None

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_panel_initialization(self) -> None:
        """Test panel initialization."""
        panel = ParameterConfigPanel(self.root, self.mock_config_manager)

        assert panel is not None
        assert panel.config_manager == self.mock_config_manager
        assert len(panel.param_vars) > 0
        assert len(panel.exp_vars) > 0

    def test_parameter_validation(self) -> None:
        """Test parameter validation."""
        panel = ParameterConfigPanel(self.root, self.mock_config_manager)

        # Test valid parameters
        panel.param_vars["extero_precision"].set(2.0)
        panel._validate_parameter("extero_precision")

        # Test invalid parameters
        panel.param_vars["extero_precision"].set(-1.0)
        panel._validate_parameter("extero_precision")  # Should handle gracefully

    def test_configuration_export(self) -> None:
        """Test configuration export."""
        panel = ParameterConfigPanel(self.root, self.mock_config_manager)

        config_dict = panel._get_configuration_dict()

        assert "apgi_parameters" in config_dict
        assert "experimental_config" in config_dict
        assert "timestamp" in config_dict
        assert "version" in config_dict

    def test_parameter_defaults(self) -> None:
        """Test parameter default values."""
        panel = ParameterConfigPanel(self.root, self.mock_config_manager)

        # Check APGI parameters
        assert panel.param_vars["extero_precision"].get() == 2.0
        assert panel.param_vars["intero_precision"].get() == 1.5
        assert panel.param_vars["threshold"].get() == 3.5

        # Check experimental parameters
        assert panel.exp_vars["n_trials"].get() == 1000
        assert panel.exp_vars["n_participants"].get() == 100


@pytest.mark.skipif(
    not (TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE),
    reason="GUI components not available",
)
class TestTestExecutionPanel:
    """Test the Test Execution Panel."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()

        # Mock controller
        self.mock_controller = Mock()
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "test_id": "test_001",
            "success_rate": 0.75,
            "falsification_rate": 0.25,
            "execution_time": 2.5,
        }
        self.mock_controller.run_test.return_value = mock_result

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_panel_initialization(self) -> None:
        """Test panel initialization."""
        panel = TestExecutionPanel(self.root, "Primary", self.mock_controller)

        assert panel is not None
        assert panel.test_name == "Primary"
        assert panel.controller == self.mock_controller
        assert not panel.is_test_running()

    def test_parameter_validation(self) -> None:
        """Test parameter validation."""
        panel = TestExecutionPanel(self.root, "Primary", self.mock_controller)

        # Test valid parameters
        panel.test_vars["n_trials"].set(1000)
        assert panel._validate_parameters()

        # Test invalid parameters
        panel.test_vars["n_trials"].set(-1)
        assert not panel._validate_parameters()

    def test_progress_tracking(self) -> None:
        """Test progress tracking."""
        panel = TestExecutionPanel(self.root, "Primary", self.mock_controller)

        # Test progress update
        panel._update_progress(50, 100, "Test running...")
        assert panel.progress_var.get() == 0.5

    def test_results_display(self) -> None:
        """Test results display."""
        panel = TestExecutionPanel(self.root, "Primary", self.mock_controller)

        # Mock test results
        mock_results = {
            "success_rate": 0.8,
            "falsification_rate": 0.2,
            "execution_time": 3.0,
        }

        panel.test_results = mock_results  # type: ignore[assignment]
        panel._display_results()

        # Check that results were added to text widget
        results_text = panel.results_text.get("1.0", "end")
        assert "Primary Test Results" in results_text
        assert "success rate" in results_text.lower()


@pytest.mark.skipif(
    not (TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE),
    reason="GUI components not available",
)
class TestResultsVisualizationPanel:
    """Test the Results Visualization Panel."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_panel_initialization(self) -> None:
        """Test panel initialization."""
        panel = ResultsVisualizationPanel(self.root)

        assert panel is not None
        assert len(panel.results_data) == 0
        assert len(panel.test_run_history) == 0
        assert panel.current_view_mode == "Overview"

    def test_results_addition(self) -> None:
        """Test adding results data."""
        panel = ResultsVisualizationPanel(self.root)

        test_results = {
            "test_type": "Primary",
            "is_falsified": False,
            "effect_size": 0.6,
            "p_value": 0.03,
            "statistical_power": 0.8,
        }

        panel.add_results("Primary", test_results)

        assert len(panel.results_data) == 1
        assert len(panel.test_run_history) == 1
        assert panel.results_data[0]["test_type"] == "Primary"

    def test_view_mode_change(self) -> None:
        """Test view mode changes."""
        panel = ResultsVisualizationPanel(self.root)

        panel._change_view_mode("Statistical Details")
        assert panel.current_view_mode == "Statistical Details"

        panel._change_view_mode("Comparison")
        assert panel.current_view_mode == "Comparison"

    def test_statistics_calculation(self) -> None:
        """Test statistics calculation."""
        panel = ResultsVisualizationPanel(self.root)

        # Add some test data
        for i in range(10):
            test_results = {
                "test_type": "Primary",
                "is_falsified": i < 3,  # 3 falsified out of 10
                "effect_size": 0.5 + i * 0.1,
                "p_value": 0.05 - i * 0.005,
                "statistical_power": 0.7 + i * 0.02,
            }
            panel.add_results(f"Test_{i}", test_results)

        stats = panel._calculate_summary_stats()

        assert stats["total_tests"] == 10
        assert stats["falsified_tests"] == 3
        assert stats["falsification_rate"] == 0.3
        assert stats["mean_effect_size"] > 0.5


@pytest.mark.skipif(
    not (TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE),
    reason="GUI components not available",
)
class TestLoggingPanel:
    """Test the Logging Panel."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_panel_initialization(self) -> None:
        """Test panel initialization."""
        panel = LoggingPanel(self.root)

        assert panel is not None
        assert panel.max_log_lines == 1000
        assert panel.is_polling
        assert panel.current_log_level == 20  # INFO level

    def test_log_level_change(self) -> None:
        """Test log level changes."""
        panel = LoggingPanel(self.root)

        panel._change_log_level("DEBUG")
        assert panel.current_log_level == 10  # DEBUG level

        panel._change_log_level("ERROR")
        assert panel.current_log_level == 40  # ERROR level

    def test_log_message_addition(self) -> None:
        """Test adding log messages."""
        panel = LoggingPanel(self.root)

        panel.add_message("Test message", "INFO")

        # Check that message was added
        log_content = panel.log_text.get("1.0", "end")
        assert "Test message" in log_content
        assert "INFO" in log_content

    def test_log_statistics(self) -> None:
        """Test log statistics."""
        panel = LoggingPanel(self.root)

        # Add some log messages
        panel.add_message("Debug message", "DEBUG")
        panel.add_message("Info message", "INFO")
        panel.add_message("Warning message", "WARNING")
        panel.add_message("Error message", "ERROR")

        stats = panel.get_log_statistics()

        assert stats["DEBUG"] >= 1
        assert stats["INFO"] >= 1
        assert stats["WARNING"] >= 1
        assert stats["ERROR"] >= 1


@pytest.mark.skipif(
    not (TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE),
    reason="GUI components not available",
)
class TestMainGUIController:
    """Test the Main GUI Controller."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_controller_initialization(self) -> None:
        """Test controller initialization."""
        controller = MainGUIController(self.root)

        assert controller is not None
        assert controller.parent == self.root
        assert len(controller.test_panels) > 0
        assert controller.parameter_panel is not None
        assert controller.results_panel is not None
        assert controller.logging_panel is not None

    def test_component_access(self) -> None:
        """Test component access methods."""
        controller = MainGUIController(self.root)

        # Test parameter panel access
        param_panel = controller.get_parameter_panel()
        assert param_panel is not None

        # Test test panel access
        test_panel = controller.get_test_panel("Primary")
        assert test_panel is not None

        # Test results panel access
        results_panel = controller.get_results_panel()
        assert results_panel is not None

        # Test logging panel access
        logging_panel = controller.get_logging_panel()
        assert logging_panel is not None

    def test_system_status(self) -> None:
        """Test system status reporting."""
        controller = MainGUIController(self.root)

        status = controller.get_system_status()

        assert "initialized" in status
        assert "current_test" in status
        assert "total_tests" in status
        assert "running_tests" in status
        assert "total_results" in status
        assert "log_statistics" in status


@pytest.mark.skipif(
    not TKINTER_AVAILABLE,
    reason="tkinter not available",
)
class TestFallbackFunctionality:
    """Test fallback functionality when components aren't available."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.root = tk.Tk()
        self.root.withdraw()

    def teardown_method(self) -> None:
        """Cleanup test environment."""
        self.root.destroy()

    def test_fallback_gui_initialization(self) -> None:
        """Test that fallback GUI initializes when components aren't available."""
        # Skip if the refactored GUI module doesn't exist
        try:
            from apps.apgi_falsification_gui_refactored import APGIFalsificationGUI  # type: ignore
        except ImportError:
            pytest.skip("apgi_falsification_gui_refactored module not available")

        # Mock the components to be unavailable
        with patch.dict("sys.modules", {"apgi_framework.gui.components": None}):
            app = APGIFalsificationGUI()

            # Should initialize in fallback mode
            assert app.system_status_label.cget("text") == "● System: Fallback Mode"

            app.destroy()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
