"""
Unit tests for Assistant GUI application components.

This module implements unit tests for the APGI Assistant GUI application,
testing initialization, UI components, query processing, and assistant
interactions without launching the full GUI.

Tests focus on the backend logic that powers the Assistant GUI functionality.
"""

import pytest
import tkinter as tk
from unittest.mock import patch
import tempfile
import json
import time

# Import the GUI class with error handling
try:
    from Assistant_GUI import APGIGUI  # type: ignore [import]

    HAS_ASSISTANT_GUI = True
except ImportError as e:
    HAS_ASSISTANT_GUI = False
    APGIGUI = None
    print(f"Warning: Could not import APGIGUI: {e}")

try:
    from AI_Assistant import APGIAssistant

    HAS_ASSISTANT = True
except ImportError:
    HAS_ASSISTANT = False
    APGIAssistant = None


class TestAssistantGUIInitialization:
    """Test Assistant GUI initialization and setup."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_gui_launches_without_errors(self):
        """
        Test that Assistant GUI can be initialized without errors.

        This test verifies that the GUI window can be created and
        all components are properly initialized.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Verify GUI was created
            assert app is not None
            assert app.root is root

            # Verify assistant integration
            if HAS_ASSISTANT:
                assert hasattr(app, "assistant")
                assert app.assistant is not None
            else:
                assert app.assistant is None

            # Verify UI components were created
            assert hasattr(app, "query_text")
            assert hasattr(app, "response_text")
            assert hasattr(app, "status_label")
            assert hasattr(app, "progress_bar")

            # Verify configuration
            assert hasattr(app, "config")
            assert isinstance(app.config, dict)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_gui_initializes_with_default_config(self):
        """
        Test that Assistant GUI initializes with default configuration.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Verify default configuration values
            config = app.config
            assert "max_response_length" in config
            assert "temperature" in config
            assert "model_name" in config
            assert "auto_save" in config

            # Verify UI state
            assert app.query_text is not None
            assert app.response_text is not None

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_gui_creates_all_ui_panels(self):
        """
        Test that all UI panels are created.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Verify main panels exist
            assert hasattr(app, "main_frame")
            assert hasattr(app, "query_frame")
            assert hasattr(app, "response_frame")
            assert hasattr(app, "control_frame")

            # Verify text widgets
            assert app.query_text.winfo_exists()
            assert app.response_text.winfo_exists()

        finally:
            root.quit()
            root.destroy()


class TestQueryProcessing:
    """Test query processing functionality."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_query_validation(self):
        """
        Test that query validation works correctly.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Test valid query
            valid_query = "What is active inference?"
            assert app._validate_query(valid_query)

            # Test empty query
            assert not app._validate_query("")

            # Test whitespace-only query
            assert not app._validate_query("   ")

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(
        not HAS_ASSISTANT_GUI or not HAS_ASSISTANT, reason="Assistant components not available"
    )
    def test_query_processing_with_mock_assistant(self):
        """
        Test query processing with mocked assistant.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Mock the assistant
            with patch.object(app.assistant, "process_query") as mock_process:
                mock_process.return_value = {
                    "response": "Mock response",
                    "confidence": 0.8,
                    "query_type": "general",
                }

                # Process a query
                result = app._process_query("Test query")

                # Verify result
                assert result["response"] == "Mock response"
                assert result["confidence"] == 0.8
                mock_process.assert_called_once_with("Test query")

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_query_type_classification(self):
        """
        Test query type classification.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Test different query types
            assert app._classify_query_type("What is active inference?") == "general"
            assert app._classify_query_type("Explain the free energy principle") == "explanatory"
            assert app._classify_query_type("Run a simulation") == "simulation"
            assert app._classify_query_type("Set parameter x to 5") == "configuration"

        finally:
            root.quit()
            root.destroy()


class TestUIInteractions:
    """Test UI interaction functionality."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_clear_query_action(self):
        """
        Test clearing query text.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Set some text
            app.query_text.insert(1.0, "Test query text")
            assert len(app.query_text.get(1.0, tk.END).strip()) > 0

            # Clear it
            app._clear_query()
            assert app.query_text.get(1.0, tk.END).strip() == ""

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_status_updates(self):
        """
        Test status label updates.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Update status
            test_message = "Processing query..."
            app._update_status(test_message)

            # Verify status was updated
            assert app.status_label.cget("text") == test_message

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_progress_bar_updates(self):
        """
        Test progress bar functionality.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Test progress updates
            app._update_progress(0)
            assert app.progress_bar["value"] == 0

            app._update_progress(50)
            assert app.progress_bar["value"] == 50

            app._update_progress(100)
            assert app.progress_bar["value"] == 100

        finally:
            root.quit()
            root.destroy()


class TestDataManagement:
    """Test data management and export functionality."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_conversation_history_management(self):
        """
        Test conversation history storage and retrieval.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Add some conversation data
            app._add_to_history("User query", "Assistant response")

            # Verify history was stored
            assert len(app.conversation_history) > 0
            assert app.conversation_history[-1]["query"] == "User query"
            assert app.conversation_history[-1]["response"] == "Assistant response"

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_export_conversation_to_json(self):
        """
        Test exporting conversation to JSON.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Add conversation data
            app._add_to_history("Query 1", "Response 1")
            app._add_to_history("Query 2", "Response 2")

            # Export to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json_filename = f.name

            try:
                app._export_conversation(json_filename)

                # Verify file was created and contains data
                with open(json_filename, "r") as f:
                    data = json.load(f)

                assert len(data) == 2
                assert data[0]["query"] == "Query 1"
                assert data[1]["response"] == "Response 2"

            finally:
                import os

                os.unlink(json_filename)

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_configuration_persistence(self):
        """
        Test saving and loading configuration.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Modify configuration
            app.config["temperature"] = 0.9

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                config_filename = f.name

            try:
                app._save_config(config_filename)

                # Load configuration
                app._load_config(config_filename)
                assert app.config["temperature"] == 0.9

            finally:
                import os

                os.unlink(config_filename)

        finally:
            root.quit()
            root.destroy()


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_assistant_unavailable_handling(self):
        """
        Test graceful handling when assistant is not available.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Simulate assistant being unavailable
            app.assistant = None

            # Try to process query
            result = app._process_query("Test query")

            # Should return error response
            assert "error" in result
            assert "not available" in result["error"].lower()

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_invalid_query_handling(self):
        """
        Test handling of invalid queries.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Test with invalid query
            result = app._process_query("")

            # Should return validation error
            assert "error" in result
            assert "invalid" in result["error"].lower() or "empty" in result["error"].lower()

        finally:
            root.quit()
            root.destroy()


class TestThreadingAndAsync:
    """Test threading and asynchronous operations."""

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_query_processing_threading(self):
        """
        Test that query processing runs in separate thread.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Mock the assistant to simulate processing time
            with patch.object(app, "_process_query") as mock_process:
                mock_process.return_value = {"response": "Test response"}

                # Start query processing
                app._submit_query()

                # Verify threading setup (should not block UI)
                # Note: Full threading test would require more complex setup
                assert app.processing_thread is not None

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(not HAS_ASSISTANT_GUI, reason="APGIGUI not available")
    def test_ui_update_threading(self):
        """
        Test UI updates from background threads.
        """
        root = tk.Tk()

        try:
            app = APGIGUI(root)

            # Test thread-safe UI updates
            initial_status = app.status_label.cget("text")

            # Update from "background thread" (simulated)
            app.root.after(10, lambda: app._update_status("Updated from thread"))

            # Wait for update
            app.root.update()
            time.sleep(0.1)
            app.root.update()

            # Status should have been updated
            assert app.status_label.cget("text") != initial_status

        finally:
            root.quit()
            root.destroy()


if __name__ == "__main__":
    pytest.main([__file__])
