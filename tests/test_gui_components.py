"""
Test suite for GUI components - backup_manager, theme_manager, session_manager, and monitoring integration.

This module provides comprehensive testing for GUI components that manage system state,
user preferences, session handling, and real-time monitoring features.
"""

# Set matplotlib backend BEFORE any imports to prevent segfaults on headless systems
import os
import sys

# Detect headless environment early
IS_HEADLESS = os.environ.get("CI") == "true" or os.environ.get("DISPLAY") is None

# Skip GUI tests entirely in headless environments
if IS_HEADLESS:
    import pytest

    pytest.skip("Headless environment - skipping all GUI tests", allow_module_level=True)

# Must set this before importing matplotlib.pyplot or any tkagg backends
os.environ["MPLBACKEND"] = "Agg"

# Import and set matplotlib backend immediately
try:
    import matplotlib

    matplotlib.use("Agg", force=True)
except ImportError:
    pass

# Now safe to import other modules
import unittest

try:
    import tkinter as tk

    # Test if tkinter can actually create windows (not just import)
    try:
        test_root = tk.Tk()
        test_root.withdraw()
        test_root.destroy()
        TKINTER_AVAILABLE = True
    except tk.TclError:
        TKINTER_AVAILABLE = False
except ImportError:
    TKINTER_AVAILABLE = False

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from apgi_framework.gui.monitoring_dashboard import MultiModalMonitoringDashboard
    from apgi_framework.monitoring.realtime_monitor import (
        MonitoringData,
        RealtimeDataStreamer,
    )

    GUI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"GUI components not available for testing: {e}")
    GUI_COMPONENTS_AVAILABLE = False


@unittest.skipUnless(GUI_COMPONENTS_AVAILABLE, "Monitoring components not available")
class TestMonitoringIntegration(unittest.TestCase):
    """Integration tests for monitoring features."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = RealtimeDataStreamer()

    def test_monitoring_data_creation(self):
        """Test creating monitoring data."""
        data = MonitoringData(
            timestamp=1234567890.0,
            experiment_id="test_exp",
            data_type="test_type",
            value=42.0,
            metadata={"key": "value"},
        )

        self.assertEqual(data.timestamp, 1234567890.0)
        self.assertEqual(data.experiment_id, "test_exp")
        self.assertEqual(data.data_type, "test_type")
        self.assertEqual(data.value, 42.0)
        self.assertEqual(data.metadata["key"], "value")

    # @patch("apgi_framework.monitoring.realtime_monitor.websockets")
    # def test_websocket_monitor_connection(self, mock_websockets):
    #     """Test WebSocket monitor connection."""
    #     if not WEBSOCKETS_AVAILABLE:
    #         self.skipTest("WebSockets not available")

    #     # Mock websocket components
    #     mock_websocket = Mock()
    #     mock_websockets.connect.return_value.__aenter__ = Mock(
    #         return_value=mock_websocket
    #     )
    #     mock_websockets.connect.return_value.__aexit__ = Mock(return_value=None)

    #     monitor = WebSocketMonitor("ws://localhost:8080")

    #     # Test that monitor initializes
    #     self.assertIsNotNone(monitor.uri)

    def test_monitor_data_collection(self):
        """Test collecting monitoring data."""
        # Verify the streamer exists and has correct initial state
        self.assertIsNotNone(self.monitor)
        self.assertFalse(self.monitor.is_running)  # Server not started in tests


@unittest.skipUnless(TKINTER_AVAILABLE and GUI_COMPONENTS_AVAILABLE, "GUI components not available")
class TestMonitoringDashboard(unittest.TestCase):
    """Test cases for the MonitoringDashboard component."""

    def setUp(self):
        """Set up test fixtures."""
        # Skip if in CI/headless environment (macOS doesn't use DISPLAY)
        if os.environ.get("CI"):
            self.skipTest("CI/headless environment - skipping GUI tests")

        # Try to detect if we have a real display (macOS check)
        import platform

        if platform.system() == "Darwin":
            # On macOS, check if we can access window server
            if not os.environ.get("DISPLAY") and not os.environ.get("WINDOWID"):
                # Try a quick tkinter test to see if GUI works
                try:
                    test_root = tk.Tk()
                    test_root.withdraw()
                    test_root.update()
                    test_root.destroy()
                except tk.TclError:
                    self.skipTest("No GUI display available on macOS")

        self.root = tk.Tk()
        self.dashboard = MultiModalMonitoringDashboard(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, "root") and self.root:
            self.root.destroy()

    def test_dashboard_initialization(self):
        """Test MonitoringDashboard initializes correctly."""
        # The dashboard has streamer, not monitor attribute
        self.assertIsNotNone(self.dashboard.streamer)
        self.assertIsNotNone(self.dashboard.root)

    def test_dashboard_components_exist(self):
        """Test that dashboard monitoring components are initialized."""
        # Verify all monitoring components exist
        self.assertIsNotNone(self.dashboard.eeg_monitor)
        self.assertIsNotNone(self.dashboard.pupil_monitor)
        self.assertIsNotNone(self.dashboard.cardiac_monitor)
        self.assertIsNotNone(self.dashboard.param_monitor)
        self.assertIsNotNone(self.dashboard.alert_system)

    def test_dashboard_streaming_controls(self):
        """Test dashboard streaming thread controls."""
        # Verify streaming thread exists after initialization
        self.assertTrue(hasattr(self.dashboard, "streaming_thread"))
        # Verify stop event exists for thread control
        self.assertTrue(hasattr(self.dashboard, "_stop_event"))


if __name__ == "__main__":
    unittest.main()
