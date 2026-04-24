"""
Tests for web-based real-time monitoring system.

Tests the web monitor functionality including data updates,
WebSocket communication, and dashboard features.
"""

from unittest.mock import MagicMock

from apgi_framework.visualization.simple_monitor import (
    MonitoringIntegration,
    SimpleMonitor,
    WebMonitor,
)


class TestSimpleMonitor:
    """Test the SimpleMonitor class."""

    def test_monitor_initialization(self) -> None:
        """Test SimpleMonitor initialization."""
        monitor = SimpleMonitor(port=8080)

        assert monitor.port == 8080
        assert monitor.monitoring_active is False
        assert len(monitor.data_buffer) == 0

    def test_monitor_default_initialization(self) -> None:
        """Test SimpleMonitor with default parameters."""
        monitor = SimpleMonitor()

        assert monitor.port == 8080
        assert monitor.monitoring_active is False

    def test_start_stop_monitoring(self) -> None:
        """Test starting and stopping monitoring."""
        monitor = SimpleMonitor()

        # Initially stopped
        assert monitor.monitoring_active is False

        # Start monitoring
        status = monitor.start()
        assert monitor.monitoring_active is True
        assert status["status"] == "started"

        # Stop monitoring
        status = monitor.stop()
        assert monitor.monitoring_active is False
        assert status["status"] == "stopped"

    def test_add_data(self) -> None:
        """Test adding data to monitor."""
        monitor = SimpleMonitor()
        monitor.start()

        test_data = {"test_key": "test_value"}
        monitor.add_data(test_data)

        assert len(monitor.data_buffer) == 1
        assert monitor.data_buffer[0] == test_data

    def test_add_data_when_stopped(self) -> None:
        """Test that data is not added when monitor is stopped."""
        monitor = SimpleMonitor()

        test_data = {"test_key": "test_value"}
        monitor.add_data(test_data)

        # Data should not be added when not monitoring
        assert len(monitor.data_buffer) == 0

    def test_get_data(self) -> None:
        """Test getting monitoring data."""
        monitor = SimpleMonitor()
        monitor.start()

        # Add test data
        for i in range(5):
            monitor.add_data({"index": i})

        data = monitor.get_data(limit=3)

        assert len(data) == 3
        assert data[0]["index"] == 2  # Last 3 items
        assert data[-1]["index"] == 4

    def test_get_data_empty(self) -> None:
        """Test getting data when buffer is empty."""
        monitor = SimpleMonitor()

        data = monitor.get_data()

        assert len(data) == 0

    def test_buffer_overflow(self) -> None:
        """Test data buffer overflow handling."""
        monitor = SimpleMonitor()
        monitor.start()

        # Add more data than buffer size (1000)
        for i in range(1005):
            monitor.add_data({"index": i})

        # Buffer should be limited to 1000
        assert len(monitor.data_buffer) == 1000
        assert monitor.data_buffer[0]["index"] == 5  # First 5 items removed
        assert monitor.data_buffer[-1]["index"] == 1004


class TestMonitoringIntegration:
    """Test the MonitoringIntegration class."""

    def test_integration_initialization(self) -> None:
        """Test MonitoringIntegration initialization."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        assert integration.monitor is monitor
        assert len(integration.integrations) == 0

    def test_integration_without_monitor(self) -> None:
        """Test MonitoringIntegration without explicit monitor."""
        integration = MonitoringIntegration()

        assert integration.monitor is not None
        assert isinstance(integration.monitor, SimpleMonitor)

    def test_register_integration(self) -> None:
        """Test registering an integration."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        mock_integration = MagicMock()
        integration.register_integration("test_integration", mock_integration)

        assert "test_integration" in integration.integrations
        assert integration.integrations["test_integration"] == mock_integration

    def test_get_status(self) -> None:
        """Test getting integration status."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        status = integration.get_status()

        assert "monitor_active" in status
        assert "integrations" in status
        assert "data_points" in status
        assert status["monitor_active"] is False
        assert status["data_points"] == 0


class TestWebMonitor:
    """Test the WebMonitor class."""

    def test_web_monitor_initialization(self) -> None:
        """Test WebMonitor initialization."""
        monitor = WebMonitor(buffer_size=500, update_interval=0.2)

        assert monitor.buffer_size == 500
        assert monitor.update_interval == 0.2
        assert monitor.monitoring_active is False
        assert len(monitor.data_buffer) == 0

    def test_web_monitor_default_initialization(self) -> None:
        """Test WebMonitor with default parameters."""
        monitor = WebMonitor()

        assert monitor.buffer_size == 1000
        assert monitor.update_interval == 1.0
        assert monitor.monitoring_active is False

    def test_web_monitor_start_stop(self) -> None:
        """Test starting and stopping web monitor."""
        monitor = WebMonitor()

        # Initially stopped
        assert monitor.monitoring_active is False

        # Start monitoring
        status = monitor.start()
        assert monitor.monitoring_active is True
        assert status["status"] == "started"

        # Stop monitoring
        status = monitor.stop()
        assert monitor.monitoring_active is False
        assert status["status"] == "stopped"

    def test_web_monitor_add_data(self) -> None:
        """Test adding data to web monitor."""
        monitor = WebMonitor()
        monitor.start()

        test_data = {"test_key": "test_value"}
        monitor.add_data(test_data)

        assert len(monitor.data_buffer) == 1
        assert monitor.data_buffer[0] == test_data

    def test_web_monitor_add_data_when_stopped(self) -> None:
        """Test that data is not added when monitor is stopped."""
        monitor = WebMonitor()

        test_data = {"test_key": "test_value"}
        monitor.add_data(test_data)

        # Data should not be added when not monitoring
        assert len(monitor.data_buffer) == 0

    def test_web_monitor_get_data(self) -> None:
        """Test getting data from web monitor."""
        monitor = WebMonitor()
        monitor.start()

        # Add test data
        for i in range(5):
            monitor.add_data({"index": i})

        data = monitor.get_data(limit=3)

        assert len(data) == 3
        assert data[0]["index"] == 2  # Last 3 items
        assert data[-1]["index"] == 4

    def test_web_monitor_broadcast_update(self) -> None:
        """Test broadcast update (stub method)."""
        monitor = WebMonitor()

        # This is a stub method, should not raise an error
        monitor.broadcast_update({"test": "data"})

        # Verify no clients by default
        assert len(monitor.websocket_clients) == 0
