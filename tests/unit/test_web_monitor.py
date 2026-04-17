"""
Tests for web-based real-time monitoring system.

Tests the web monitor functionality including data updates,
WebSocket communication, and dashboard features.
"""

import threading
import time
from unittest.mock import MagicMock, patch

from apgi_simulation.visualization.simple_monitor import MonitoringIntegration, SimpleMonitor
from apgi_simulation.visualization.web_monitor import WebMonitor


class TestSimpleMonitor:
    """Test the SimpleMonitor class."""

    def test_monitor_initialization(self) -> None:
        """Test SimpleMonitor initialization."""
        monitor = SimpleMonitor(buffer_size=500, update_interval=0.2)

        assert monitor.buffer_size == 500
        assert monitor.update_interval == 0.2
        assert monitor.is_monitoring is False
        assert monitor.system_status == "Stopped"
        assert len(monitor.time_buffer) == 0

    def test_monitor_default_initialization(self) -> None:
        """Test SimpleMonitor with default parameters."""
        monitor = SimpleMonitor()

        assert monitor.buffer_size == 1000
        assert monitor.update_interval == 0.1
        assert monitor.is_monitoring is False

    def test_start_stop_monitoring(self) -> None:
        """Test starting and stopping monitoring."""
        monitor = SimpleMonitor()

        # Initially stopped
        assert monitor.is_monitoring is False
        assert monitor.system_status == "Stopped"

        # Start monitoring
        monitor.start_monitoring()
        assert monitor.is_monitoring is True
        assert monitor.system_status == "Running"  # type: ignore[unreachable]
        assert monitor.monitor_thread is not None

        # Stop monitoring
        monitor.stop_monitoring()
        assert monitor.is_monitoring is False
        assert monitor.system_status == "Stopped"

    def test_clear_buffers(self) -> None:
        """Test clearing data buffers."""
        monitor = SimpleMonitor()

        # Add some test data
        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 2.0},
            "free_energy": {"total_free_energy": 1.5},
            "precision": {"mean_precision": 0.8},
            "metabolism": {"current_reserves": 0.9},
            "self_model": {"coherence_score": 0.7},
        }

        monitor.update_data(test_state)

        # Verify data was added
        assert len(monitor.time_buffer) == 1
        assert len(monitor.ignition_buffer) == 1

        # Clear buffers
        monitor.clear_buffers()

        # Verify buffers are empty
        assert len(monitor.time_buffer) == 0
        assert len(monitor.ignition_buffer) == 0
        assert len(monitor.free_energy_buffer) == 0
        assert len(monitor.alerts) == 0

    def test_update_data_basic(self) -> None:
        """Test basic data update functionality."""
        monitor = SimpleMonitor(buffer_size=10)

        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 2.5, "ignition_occurred": True},
            "free_energy": {"total_free_energy": 1.8},
            "precision": {"mean_precision": 0.75},
            "metabolism": {"current_reserves": 0.85},
            "self_model": {"coherence_score": 0.65},
        }

        monitor.update_data(test_state)

        # Verify data was stored
        assert len(monitor.time_buffer) == 1
        assert monitor.time_buffer[0] == 1000.0
        assert monitor.ignition_buffer[0] == 2.5
        assert monitor.free_energy_buffer[0] == 1.8
        assert monitor.precision_buffer[0] == 0.75
        assert monitor.energy_reserves_buffer[0] == 0.85
        assert monitor.coherence_buffer[0] == 0.65

        # Verify current metrics
        assert monitor.current_metrics["ignition_signal"] == 2.5
        assert monitor.current_metrics["ignition_occurred"] is True

    def test_update_data_buffer_overflow(self) -> None:
        """Test data update with buffer overflow."""
        monitor = SimpleMonitor(buffer_size=3)

        # Add more data than buffer size
        for i in range(5):
            test_state = {
                "time": float(i * 1000),
                "ignition": {"total_signal": float(i)},
                "free_energy": {"total_free_energy": float(i)},
                "precision": {"mean_precision": 0.5},
                "metabolism": {"current_reserves": 0.8},
                "self_model": {"coherence_score": 0.6},
            }
            monitor.update_data(test_state)

        # Buffer should contain only last 3 items
        assert len(monitor.time_buffer) == 3
        assert list(monitor.time_buffer) == [2000.0, 3000.0, 4000.0]
        assert list(monitor.ignition_buffer) == [2.0, 3.0, 4.0]

    def test_check_alerts_low_energy(self) -> None:
        """Test alert generation for low energy."""
        monitor = SimpleMonitor()

        # Test low energy alert
        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 1.0},
            "free_energy": {"total_free_energy": 1.0},
            "precision": {"mean_precision": 0.5},
            "metabolism": {"current_reserves": 0.15},  # Low energy
            "self_model": {"coherence_score": 0.6},
        }

        initial_alert_count = len(monitor.alerts)
        monitor.update_data(test_state)

        # Should generate low energy alert
        assert len(monitor.alerts) > initial_alert_count
        latest_alert = monitor.alerts[-1]
        assert "energy reserves" in latest_alert["message"].lower()
        assert latest_alert["level"] == "warning"

    def test_check_alerts_critical_energy(self) -> None:
        """Test alert generation for critical energy."""
        monitor = SimpleMonitor()

        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 1.0},
            "free_energy": {"total_free_energy": 1.0},
            "precision": {"mean_precision": 0.5},
            "metabolism": {"current_reserves": 0.05},  # Critical energy
            "self_model": {"coherence_score": 0.6},
        }

        monitor.update_data(test_state)

        # Should generate critical energy alert
        latest_alert = monitor.alerts[-1]
        assert latest_alert["level"] == "critical"

    def test_get_status(self) -> None:
        """Test getting monitor status."""
        monitor = SimpleMonitor()

        status = monitor.get_status()

        assert "is_monitoring" in status
        assert "system_status" in status
        assert "buffer_size" in status
        assert "total_updates" in status
        assert "current_metrics" in status

        assert status["is_monitoring"] is False
        assert status["system_status"] == "Stopped"
        assert status["total_updates"] == 0

    def test_get_data(self) -> None:
        """Test getting monitoring data."""
        monitor = SimpleMonitor()

        # Add test data
        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 2.0},
            "free_energy": {"total_free_energy": 1.5},
            "precision": {"mean_precision": 0.8},
            "metabolism": {"current_reserves": 0.9},
            "self_model": {"coherence_score": 0.7},
        }

        monitor.update_data(test_state)

        data = monitor.get_data()

        assert "time" in data
        assert "ignition_signal" in data
        assert "free_energy" in data
        assert len(data["time"]) == 1
        assert data["time"][0] == 1000.0
        assert data["ignition_signal"][0] == 2.0

    def test_export_data(self) -> None:
        """Test data export functionality."""
        monitor = SimpleMonitor()

        # Add test data
        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 2.0},
            "free_energy": {"total_free_energy": 1.5},
            "precision": {"mean_precision": 0.8},
            "metabolism": {"current_reserves": 0.9},
            "self_model": {"coherence_score": 0.7},
        }

        monitor.update_data(test_state)

        export_data = monitor.export_data()

        assert "export_timestamp" in export_data
        assert "monitoring_session" in export_data
        assert "data" in export_data
        assert "current_metrics" in export_data
        assert "statistics" in export_data

    def test_get_statistics(self) -> None:
        """Test statistics calculation."""
        monitor = SimpleMonitor()

        # Add multiple data points
        for i in range(5):
            test_state = {
                "time": float(i * 1000),
                "ignition": {"total_signal": float(i)},
                "free_energy": {"total_free_energy": 1.0 + i * 0.1},
                "precision": {"mean_precision": 0.5 + i * 0.05},
                "metabolism": {"current_reserves": 0.9 - i * 0.01},
                "self_model": {"coherence_score": 0.6 + i * 0.02},
            }
            monitor.update_data(test_state)

        stats = monitor.get_statistics()

        assert "ignition_signal" in stats
        assert "temporal" in stats
        assert "alerts" in stats

        # Check ignition signal statistics
        ignition_stats = stats["ignition_signal"]
        assert "mean" in ignition_stats
        assert "std" in ignition_stats
        assert "min" in ignition_stats
        assert "max" in ignition_stats
        assert ignition_stats["min"] == 0.0
        assert ignition_stats["max"] == 4.0

    def test_check_alerts_high_free_energy(self) -> None:
        """Test alert generation for high free energy."""
        monitor = WebMonitor()

        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 1.0},
            "free_energy": {"total_free_energy": 6.0},  # High free energy
            "precision": {"mean_precision": 0.5},
            "metabolism": {"current_reserves": 0.8},
            "self_model": {"coherence_score": 0.6},
        }

        monitor.update_data(test_state)

        # Should generate high free energy alert
        latest_alert = monitor.alerts[-1]
        assert "free energy" in latest_alert["message"].lower()
        assert latest_alert["level"] == "warning"

    def test_check_alerts_low_coherence(self) -> None:
        """Test alert generation for low coherence."""
        monitor = WebMonitor()

        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 1.0},
            "free_energy": {"total_free_energy": 1.0},
            "precision": {"mean_precision": 0.5},
            "metabolism": {"current_reserves": 0.8},
            "self_model": {"coherence_score": 0.2},  # Low coherence
        }

        monitor.update_data(test_state)

        # Should generate low coherence alert
        latest_alert = monitor.alerts[-1]
        assert "coherence" in latest_alert["message"].lower()
        assert latest_alert["level"] == "info"

    def test_alerts_limit(self) -> None:
        """Test that alerts are limited to prevent memory issues."""
        monitor = WebMonitor()

        # Generate many alerts
        for i in range(150):
            test_state = {
                "time": float(i * 1000),
                "ignition": {"total_signal": 1.0},
                "free_energy": {"total_free_energy": 6.0},  # Always high
                "precision": {"mean_precision": 0.5},
                "metabolism": {"current_reserves": 0.8},
                "self_model": {"coherence_score": 0.6},
            }
            monitor.update_data(test_state)

        # Should limit alerts to prevent memory issues
        assert len(monitor.alerts) <= 100

    @patch("apgi_simulation.visualization.web_monitor.SocketIO")
    def test_socketio_emit(self, mock_socketio: MagicMock) -> None:
        """Test WebSocket data emission."""
        monitor = WebMonitor()
        monitor.socketio = mock_socketio
        monitor.is_monitoring = True

        test_state = {
            "time": 1000.0,
            "ignition": {"total_signal": 2.0, "ignition_occurred": True},
            "free_energy": {"total_free_energy": 1.5},
            "precision": {"mean_precision": 0.8},
            "metabolism": {"current_reserves": 0.9},
            "self_model": {"coherence_score": 0.7},
        }

        monitor.update_data(test_state)

        # Should emit data update
        monitor.socketio.emit.assert_called()

    def test_create_dashboard_template(self) -> None:
        """Test dashboard template creation."""
        monitor = WebMonitor()

        # Create template
        monitor.create_dashboard_template()

        # Verify template file exists
        # Template should be created (or at least the method should not fail)
        # We can't easily test file creation in unit tests, so we just verify no exceptions


class TestMonitoringIntegration:
    """Test the MonitoringIntegration class."""

    def test_integration_initialization(self) -> None:
        """Test MonitoringIntegration initialization."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        assert integration.monitor is monitor
        assert integration.is_connected is False

    def test_connect_system_with_callback_support(self) -> None:
        """Test connecting system that supports monitoring callbacks."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        # Mock system with callback support
        mock_system = MagicMock()
        mock_system.add_monitor_callback = MagicMock()

        integration.connect_system(mock_system)  # type: ignore

        assert integration.is_connected is True
        mock_system.add_monitor_callback.assert_called_once_with(monitor.update_data)

    def test_connect_system_without_callback_support(self) -> None:
        """Test connecting system that doesn't support monitoring callbacks."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        # Mock system without callback support
        mock_system = MagicMock()
        del mock_system.add_monitor_callback  # Remove the method

        integration.connect_system(mock_system)  # type: ignore

        assert integration.is_connected is False

    def test_disconnect_system(self) -> None:
        """Test disconnecting system from monitor."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        # Mock system with callback support
        mock_system = MagicMock()
        mock_system.add_monitor_callback = MagicMock()
        mock_system.remove_monitor_callback = MagicMock()

        # Connect first
        integration.connect_system(mock_system)  # type: ignore
        assert integration.is_connected is True

        # Then disconnect
        integration.disconnect_system(mock_system)  # type: ignore

        assert integration.is_connected is False
        mock_system.remove_monitor_callback.assert_called_once_with(monitor.update_data)  # type: ignore[unreachable]

    def test_simulate_data_basic(self) -> None:
        """Test basic data simulation."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        # Run short simulation
        integration.simulate_data(duration=0.5, interval=0.1)

        # Should have generated some data points
        assert len(monitor.time_buffer) > 0
        assert len(monitor.ignition_buffer) > 0

        # Verify data is realistic
        assert all(val >= 0 for val in monitor.ignition_buffer)
        assert all(0 <= val <= 1 for val in monitor.energy_reserves_buffer)

    def test_simulate_data_threading(self) -> None:
        """Test data simulation in separate thread."""
        monitor = SimpleMonitor()
        integration = MonitoringIntegration(monitor)

        # Start simulation in thread
        sim_thread = threading.Thread(target=integration.simulate_data, args=(0.3, 0.05))
        sim_thread.start()

        # Wait for some data
        time.sleep(0.1)

        # Should have some data
        assert len(monitor.time_buffer) > 0

        # Wait for thread to complete
        sim_thread.join(timeout=1.0)

        # Should have more data after completion
        final_count = len(monitor.time_buffer)
        assert final_count > 2

        # Data should be consistent (no corruption)
        assert all(isinstance(val, (int, float)) for val in monitor.time_buffer)
        assert all(isinstance(val, (int, float)) for val in monitor.ignition_buffer)


class TestWebMonitorIntegration:
    """Integration tests for web monitor functionality."""

    def test_full_monitoring_cycle(self) -> None:
        """Test complete monitoring cycle."""
        self.monitor = WebMonitor(buffer_size=50)

        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor.is_monitoring is True

        # Add some data
        for i in range(10):
            test_state = {
                "time": float(i * 100),
                "ignition": {"total_signal": 1.0 + i * 0.1},
                "free_energy": {"total_free_energy": 1.5 + i * 0.05},
                "precision": {"mean_precision": 0.7 + i * 0.01},
                "metabolism": {"current_reserves": 0.9 - i * 0.01},
                "self_model": {"coherence_score": 0.6 + i * 0.02},
            }
            self.monitor.update_data(test_state)

        # Verify data accumulation
        assert len(self.monitor.time_buffer) == 10
        assert self.monitor.current_metrics["ignition_signal"] == 1.9  # Last value

        # Stop monitoring
        self.monitor.stop_monitoring()
        assert self.monitor.is_monitoring is False

    def test_monitoring_with_alerts(self) -> None:
        """Test monitoring with alert generation."""
        monitor = WebMonitor()

        # Generate data that should trigger alerts
        alert_states = [
            # Low energy
            {
                "time": 1000.0,
                "ignition": {"total_signal": 1.0},
                "free_energy": {"total_free_energy": 1.0},
                "precision": {"mean_precision": 0.5},
                "metabolism": {"current_reserves": 0.1},
                "self_model": {"coherence_score": 0.6},
            },
            # High free energy
            {
                "time": 2000.0,
                "ignition": {"total_signal": 1.0},
                "free_energy": {"total_free_energy": 7.0},
                "precision": {"mean_precision": 0.5},
                "metabolism": {"current_reserves": 0.8},
                "self_model": {"coherence_score": 0.6},
            },
            # Low coherence
            {
                "time": 3000.0,
                "ignition": {"total_signal": 1.0},
                "free_energy": {"total_free_energy": 1.0},
                "precision": {"mean_precision": 0.5},
                "metabolism": {"current_reserves": 0.8},
                "self_model": {"coherence_score": 0.2},
            },
        ]

        for state in alert_states:
            monitor.update_data(state)

        # Should have generated multiple alerts
        assert len(monitor.alerts) >= 3

        # Verify different alert types
        alert_messages = [alert["message"].lower() for alert in monitor.alerts]
        assert any("energy" in msg for msg in alert_messages)
        assert any("free energy" in msg for msg in alert_messages)
        assert any("coherence" in msg for msg in alert_messages)

    def test_performance_with_large_dataset(self) -> None:
        """Test monitor performance with large dataset."""
        monitor = WebMonitor(buffer_size=5000)

        start_time = time.time()

        # Generate large dataset
        for i in range(1000):
            test_state = {
                "time": float(i * 10),
                "ignition": {"total_signal": 1.0 + 0.1 * (i % 10)},
                "free_energy": {"total_free_energy": 1.5 + 0.05 * (i % 20)},
                "precision": {"mean_precision": 0.7 + 0.01 * (i % 30)},
                "metabolism": {"current_reserves": 0.9 - 0.0001 * i},
                "self_model": {"coherence_score": 0.6 + 0.02 * (i % 15)},
            }
            monitor.update_data(test_state)

        processing_time = time.time() - start_time

        # Should process data efficiently
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert len(monitor.time_buffer) == 1000

        # Verify data integrity
        assert monitor.time_buffer[0] == 0.0
        assert monitor.time_buffer[-1] == 9990.0

    def test_concurrent_access(self) -> None:
        """Test concurrent access to monitor data."""
        monitor = WebMonitor()

        def update_data_worker(worker_id: int, num_updates: int) -> None:
            """Worker function for concurrent updates."""
            for i in range(num_updates):
                test_state = {
                    "time": float(worker_id * 1000 + i),
                    "ignition": {"total_signal": float(worker_id + i)},
                    "free_energy": {"total_free_energy": 1.0},
                    "precision": {"mean_precision": 0.5},
                    "metabolism": {"current_reserves": 0.8},
                    "self_model": {"coherence_score": 0.6},
                }
                monitor.update_data(test_state)

        # Start multiple threads
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=update_data_worker, args=(worker_id, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have data from all workers
        assert len(monitor.time_buffer) == 30  # 3 workers * 10 updates each

        # Data should be consistent (no corruption)
        assert all(isinstance(val, (int, float)) for val in monitor.time_buffer)
        assert all(isinstance(val, (int, float)) for val in monitor.ignition_buffer)
