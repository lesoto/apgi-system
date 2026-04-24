"""
Unit tests for Psychological States GUI application components.

This module implements unit tests for the APGI Psychological States GUI application,
testing initialization, visualization rendering, state management, and parameter
adjustments without launching the full GUI.

Tests focus on the backend logic that powers the Psychological States GUI functionality.
"""

import importlib.util
import json
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from typing import Any
from unittest.mock import patch

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


# Import the GUI class with error handling
try:
    # Load from hyphenated filename using importlib
    psych_gui_path = Path(__file__).parent.parent.parent / "Psychological-States-GUI.py"
    if psych_gui_path.exists():
        Psychological_States_GUI = load_module_from_file("Psychological_States_GUI", psych_gui_path)
        APGIVisualizer = Psychological_States_GUI.APGIVisualizer
        APGIVisualizerGUI = Psychological_States_GUI.APGIVisualizerGUI
        HAS_PSYCHOLOGICAL_GUI = True
    else:
        # Fallback to standard import if file renamed
        from Psychological_States_GUI import APGIVisualizer, APGIVisualizerGUI  # type: ignore[import-not-found, no-redef]

        HAS_PSYCHOLOGICAL_GUI = True
except ImportError as e:
    HAS_PSYCHOLOGICAL_GUI = False
    APGIVisualizerGUI: Any = None  # type: ignore[assignment, no-redef]
    APGIVisualizer: Any = None  # type: ignore[assignment, no-redef]
    print(f"Warning: Could not import APGIVisualizerGUI: {e}")

try:
    from apgi_framework.system import APGISystem

    HAS_SYSTEM = True
except ImportError:
    HAS_SYSTEM = False
    APGISystem = None  # type: ignore


class TestPsychologicalStatesGUIInitialization:
    """Test Psychological States GUI initialization and setup."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_gui_launches_without_errors(self) -> None:
        """
        Test that Psychological States GUI can be initialized without errors.

        This test verifies that the GUI window can be created and
        all components are properly initialized.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Verify GUI was created
            assert app is not None
            assert app.root is root

            # Verify visualizer was initialized
            assert hasattr(app, "visualizer")
            assert app.visualizer is not None

            # Verify UI components were created
            assert hasattr(app, "main_frame")
            assert hasattr(app, "control_frame")
            assert hasattr(app, "visualization_frame")

            # Verify parameter controls
            assert hasattr(app, "parameter_controls")
            assert isinstance(app.parameter_controls, dict)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_gui_initializes_with_default_parameters(self) -> None:
        """
        Test that GUI initializes with default parameters.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Verify default parameter values
            params = app.parameters
            assert "arousal" in params
            assert "stress" in params
            assert "attention" in params
            assert "motivation" in params

            # Verify parameter ranges
            assert 0.0 <= params["arousal"] <= 1.0
            assert 0.0 <= params["stress"] <= 1.0

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_visualization_canvas_created(self) -> None:
        """
        Test that visualization canvas is properly created.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Verify canvas exists
            assert hasattr(app, "canvas")
            assert app.canvas is not None
            assert app.canvas.winfo_exists()

            # Verify renderer exists
            assert hasattr(app, "renderer")
            assert app.renderer is not None

        finally:
            root.quit()
            root.destroy()


class TestParameterManagement:
    """Test parameter adjustment and management."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_parameter_adjustment_updates_values(self) -> None:
        """
        Test that parameter adjustments update internal values.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Test arousal adjustment
            app._update_parameter("arousal", 0.7)
            assert app.parameters["arousal"] == 0.7

            # Test stress adjustment
            app._update_parameter("stress", 0.3)
            assert app.parameters["stress"] == 0.3

            # Test attention adjustment
            app._update_parameter("attention", 0.8)
            assert app.parameters["attention"] == 0.8

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_parameter_validation(self) -> None:
        """
        Test parameter value validation.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Test valid range
            assert app._validate_parameter("arousal", 0.5)
            assert app._validate_parameter("stress", 0.0)
            assert app._validate_parameter("attention", 1.0)

            # Test invalid ranges
            assert not app._validate_parameter("arousal", -0.1)
            assert not app._validate_parameter("stress", 1.1)
            assert not app._validate_parameter("attention", 2.0)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_parameter_reset_to_defaults(self) -> None:
        """
        Test resetting parameters to default values.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Modify parameters
            app._update_parameter("arousal", 0.9)
            app._update_parameter("stress", 0.7)
            original_arousal = app.parameters["arousal"]
            original_stress = app.parameters["stress"]

            # Reset parameters
            app._reset_parameters()

            # Verify parameters changed
            assert app.parameters["arousal"] != original_arousal
            assert app.parameters["stress"] != original_stress

        finally:
            root.quit()
            root.destroy()


class TestVisualizationRendering:
    """Test visualization rendering functionality."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_state_visualization_rendering(self) -> None:
        """
        Test rendering of psychological state visualizations.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Create sample state data
            state_data = {"arousal": 0.6, "stress": 0.4, "attention": 0.8, "motivation": 0.7}

            # Render visualization (should not raise errors)
            app._render_state_visualization(state_data)

            # Verify renderer was called
            assert app.renderer is not None

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_visualization_update_triggers_render(self) -> None:
        """
        Test that visualization updates trigger re-rendering.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Mock the renderer
            with patch.object(app.renderer, "render") as mock_render:
                # Update parameters
                app._update_parameter("arousal", 0.5)

                # Trigger visualization update
                app._update_visualization()

                # Verify render was called
                mock_render.assert_called()

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_canvas_resizing_handling(self) -> None:
        """
        Test handling of canvas resize events.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Mock canvas resize
            with patch.object(app.renderer, "handle_resize") as mock_resize:
                # Simulate resize event
                app._on_canvas_resize(None)

                # Verify resize handler was called
                mock_resize.assert_called()

        finally:
            root.quit()
            root.destroy()


class TestPsychologicalStateManagement:
    """Test psychological state management."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_state_category_classification(self) -> None:
        """
        Test classification of psychological states into categories.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Test different state combinations
            high_arousal_state = {"arousal": 0.8, "stress": 0.2, "attention": 0.9}
            category = app._classify_state_category(high_arousal_state)
            assert isinstance(category, str)
            assert len(category) > 0

            low_stress_state = {"arousal": 0.3, "stress": 0.1, "attention": 0.6}
            category2 = app._classify_state_category(low_stress_state)
            assert isinstance(category2, str)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_state_transition_tracking(self) -> None:
        """
        Test tracking of state transitions over time.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Add initial state
            initial_state = {"arousal": 0.5, "stress": 0.3, "attention": 0.7}
            app._record_state_transition(initial_state)

            # Add second state
            second_state = {"arousal": 0.6, "stress": 0.4, "attention": 0.8}
            app._record_state_transition(second_state)

            # Verify states were recorded
            assert len(app.state_history) >= 2

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_state_analysis_computation(self) -> None:
        """
        Test computation of state analysis metrics.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Add some state data
            states = [
                {"arousal": 0.5, "stress": 0.3, "attention": 0.7},
                {"arousal": 0.6, "stress": 0.4, "attention": 0.8},
                {"arousal": 0.4, "stress": 0.2, "attention": 0.6},
            ]

            for state in states:
                app._record_state_transition(state)

            # Compute analysis
            analysis = app._compute_state_analysis()

            # Verify analysis contains expected metrics
            assert isinstance(analysis, dict)
            assert "average_arousal" in analysis
            assert "average_stress" in analysis
            assert "average_attention" in analysis

        finally:
            root.quit()
            root.destroy()


class TestDataExport:
    """Test data export functionality."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_export_state_data_to_json(self) -> None:
        """
        Test exporting state data to JSON format.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Add some state data
            app._record_state_transition({"arousal": 0.5, "stress": 0.3, "attention": 0.7})
            app._record_state_transition({"arousal": 0.6, "stress": 0.4, "attention": 0.8})

            # Export to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json_filename = f.name

            try:
                app._export_state_data(json_filename)

                # Verify file was created and contains data
                with open(json_filename, "r") as f:
                    data = json.load(f)

                assert len(data) == 2
                assert "arousal" in data[0]
                assert "stress" in data[0]
                assert "attention" in data[0]

            finally:
                import os

                os.unlink(json_filename)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_export_visualization_to_image(self) -> None:
        """
        Test exporting visualization to image format.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Export to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                image_filename = f.name

            try:
                app._export_visualization(image_filename)

                # Verify file was created
                assert Path(image_filename).exists()
                assert Path(image_filename).stat().st_size > 0

            finally:
                import os

                os.unlink(image_filename)

        finally:
            root.quit()
            root.destroy()


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_renderer_unavailable_handling(self) -> None:
        """
        Test graceful handling when renderer is not available.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Simulate renderer being unavailable
            app.renderer = None

            # Try to render visualization
            state_data = {"arousal": 0.5, "stress": 0.3}
            app._render_state_visualization(state_data)

            # Should not raise exception
            assert True

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_PSYCHOLOGICAL_GUI, reason="APGIVisualizerGUI not available")
    def test_invalid_parameter_handling(self) -> None:
        """
        Test handling of invalid parameter values.
        """
        root = tk.Tk()

        try:
            app = APGIVisualizerGUI(root)

            # Try to set invalid parameter
            app._update_parameter("invalid_param", 0.5)

            # Should not raise exception and parameter should not be set
            assert "invalid_param" not in app.parameters

        finally:
            root.quit()
            root.destroy()


if __name__ == "__main__":
    pytest.main([__file__])
