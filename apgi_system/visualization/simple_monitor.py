"""
Simple Real-time Monitoring System for APGI

Provides basic real-time monitoring capabilities without web dependencies.
This is a lightweight alternative to the full web monitor.
"""

import time
import threading
import json
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime

import numpy as np


class SimpleMonitor:
    """
    Simple real-time monitoring system for APGI.

    Features:
    - Real-time data collection and buffering
    - Alert generation and monitoring
    - Data export capabilities
    - Performance metrics tracking
    - Thread-safe operations
    """

    def __init__(self, buffer_size: int = 1000, update_interval: float = 0.1):
        """
        Initialize simple monitor.

        Args:
            buffer_size: Maximum number of data points to keep in memory
            update_interval: Update interval in seconds
        """
        self.buffer_size = buffer_size
        self.update_interval = update_interval

        # Data buffers
        self.time_buffer: deque[float] = deque(maxlen=buffer_size)
        self.ignition_buffer: deque[int] = deque(maxlen=buffer_size)
        self.free_energy_buffer: deque[float] = deque(maxlen=buffer_size)
        self.precision_buffer: deque[float] = deque(maxlen=buffer_size)
        self.energy_reserves_buffer: deque[float] = deque(maxlen=buffer_size)
        self.coherence_buffer: deque[float] = deque(maxlen=buffer_size)

        # System state
        self.is_monitoring = False
        self.system_status = "Stopped"
        self.current_metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []

        # Statistics
        self.total_updates = 0
        self.start_time: Optional[float] = None

        # Thread safety
        self._lock = threading.Lock()

        # Background thread for monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start_monitoring(self) -> None:
        """Start real-time monitoring."""
        with self._lock:
            if not self.is_monitoring:
                self.is_monitoring = True
                self.system_status = "Running"
                self.start_time = time.time()
                self.stop_event.clear()

                # Start background monitoring thread
                self.monitor_thread = threading.Thread(target=self._monitor_loop)
                self.monitor_thread.daemon = True
                self.monitor_thread.start()

                print("Simple monitoring started")

    def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        with self._lock:
            if self.is_monitoring:
                self.is_monitoring = False
                self.system_status = "Stopped"
                self.stop_event.set()

                if self.monitor_thread and self.monitor_thread.is_alive():
                    self.monitor_thread.join(timeout=1.0)

                print("Simple monitoring stopped")

    def clear_buffers(self) -> None:
        """Clear all data buffers."""
        with self._lock:
            self.time_buffer.clear()
            self.ignition_buffer.clear()
            self.free_energy_buffer.clear()
            self.precision_buffer.clear()
            self.energy_reserves_buffer.clear()
            self.coherence_buffer.clear()
            self.alerts.clear()
            self.total_updates = 0
            print("Data buffers cleared")

    def update_data(self, system_state: Dict[str, Any]) -> None:
        """
        Update monitoring data with new system state.

        Args:
            system_state: Current APGI system state dictionary
        """
        with self._lock:
            current_time = system_state.get("time", time.time() * 1000)

            # Extract key metrics
            ignition_signal = system_state.get("ignition", {}).get("total_signal", 0.0)
            free_energy = system_state.get("free_energy", {}).get("total_free_energy", 0.0)
            precision = system_state.get("precision", {}).get("mean_precision", 0.0)
            energy_reserves = system_state.get("metabolism", {}).get("current_reserves", 1.0)
            coherence = system_state.get("self_model", {}).get("coherence_score", 0.0)

            # Update buffers
            self.time_buffer.append(current_time)
            self.ignition_buffer.append(ignition_signal)
            self.free_energy_buffer.append(free_energy)
            self.precision_buffer.append(precision)
            self.energy_reserves_buffer.append(energy_reserves)
            self.coherence_buffer.append(coherence)

            # Update current metrics
            self.current_metrics = {
                "ignition_signal": ignition_signal,
                "free_energy": free_energy,
                "precision": precision,
                "energy_reserves": energy_reserves,
                "coherence": coherence,
                "ignition_occurred": system_state.get("ignition", {}).get(
                    "ignition_occurred", False
                ),
                "timestamp": current_time,
            }

            # Update statistics
            self.total_updates += 1

            # Check for alerts
            self._check_alerts(system_state)

    def _check_alerts(self, system_state: Dict[str, Any]) -> None:
        """Check for system alerts and warnings."""
        current_time = datetime.now().isoformat()

        # Low energy alert
        energy_reserves = system_state.get("metabolism", {}).get("current_reserves", 1.0)
        if energy_reserves < 0.2:
            alert = {
                "timestamp": current_time,
                "level": "warning" if energy_reserves > 0.1 else "critical",
                "message": f"Low energy reserves: {energy_reserves:.2%}",
                "metric": "energy_reserves",
                "value": energy_reserves,
            }
            self.alerts.append(alert)

        # High free energy alert
        free_energy = system_state.get("free_energy", {}).get("total_free_energy", 0.0)
        if free_energy > 5.0:
            alert = {
                "timestamp": current_time,
                "level": "warning",
                "message": f"High free energy: {free_energy:.2f}",
                "metric": "free_energy",
                "value": free_energy,
            }
            self.alerts.append(alert)

        # Low coherence alert
        coherence = system_state.get("self_model", {}).get("coherence_score", 0.0)
        if coherence < 0.3:
            alert = {
                "timestamp": current_time,
                "level": "info",
                "message": f"Low self-model coherence: {coherence:.2f}",
                "metric": "coherence",
                "value": coherence,
            }
            self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while not self.stop_event.is_set():
            try:
                # Periodic monitoring tasks
                if self.is_monitoring:
                    self._periodic_check()

                time.sleep(self.update_interval)

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                break

    def _periodic_check(self) -> None:
        """Perform periodic monitoring checks."""
        # Check for system health issues
        if len(self.time_buffer) > 0:
            # Check for data staleness
            last_update_time = self.time_buffer[-1]
            current_time = time.time() * 1000

            if current_time - last_update_time > 5000:  # 5 seconds
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "level": "warning",
                    "message": "Data updates have stopped",
                    "metric": "system_health",
                    "value": current_time - last_update_time,
                }
                self.alerts.append(alert)

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        with self._lock:
            runtime = time.time() - self.start_time if self.start_time else 0

            return {
                "is_monitoring": self.is_monitoring,
                "system_status": self.system_status,
                "buffer_size": len(self.time_buffer),
                "total_updates": self.total_updates,
                "runtime_seconds": runtime,
                "current_metrics": self.current_metrics.copy(),
                "alert_count": len(self.alerts),
                "recent_alerts": self.alerts[-5:] if self.alerts else [],
            }

    def get_data(self) -> Dict[str, List[float]]:
        """Get current monitoring data."""
        with self._lock:
            return {
                "time": list(self.time_buffer),
                "ignition_signal": list(self.ignition_buffer),
                "free_energy": list(self.free_energy_buffer),
                "precision": list(self.precision_buffer),
                "energy_reserves": list(self.energy_reserves_buffer),
                "coherence": list(self.coherence_buffer),
            }

    def export_data(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Export monitoring data to JSON format.

        Args:
            filepath: Optional file path to save data

        Returns:
            Dictionary containing all monitoring data
        """
        with self._lock:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "monitoring_session": {
                    "start_time": self.start_time,
                    "total_updates": self.total_updates,
                    "buffer_size": self.buffer_size,
                    "system_status": self.system_status,
                },
                "data": self.get_data(),
                "current_metrics": self.current_metrics.copy(),
                "alerts": self.alerts.copy(),
                "statistics": self.get_statistics(),
            }

            if filepath:
                with open(filepath, "w") as f:
                    json.dump(export_data, f, indent=2, default=str)
                print(f"Data exported to: {filepath}")

            return export_data

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        with self._lock:
            if len(self.time_buffer) == 0:
                return {"error": "No data available"}

            # Calculate basic statistics
            stats: Dict[str, Any] = {}

            # Metric statistics
            for metric_name, buffer in [
                ("ignition_signal", self.ignition_buffer),
                ("free_energy", self.free_energy_buffer),
                ("precision", self.precision_buffer),
                ("energy_reserves", self.energy_reserves_buffer),
                ("coherence", self.coherence_buffer),
            ]:
                if len(buffer) > 0:
                    values = np.array(list(buffer))
                    stats[metric_name] = {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values)),
                        "current": float(values[-1]) if len(values) > 0 else 0.0,
                    }

            # Time-based statistics
            if len(self.time_buffer) > 1:
                time_values = np.array(list(self.time_buffer))
                duration_ms = time_values[-1] - time_values[0]
                update_rate = (
                    len(self.time_buffer) / (duration_ms / 1000.0) if duration_ms > 0 else 0
                )

                stats["temporal"] = {
                    "duration_ms": float(duration_ms),
                    "update_rate_hz": float(update_rate),
                    "total_samples": len(self.time_buffer),
                }

            # Alert statistics
            alert_levels: Dict[str, int] = {}
            for alert in self.alerts:
                level = alert["level"]
                alert_levels[level] = alert_levels.get(level, 0) + 1

            # Create alert stats as a separate structure
            alert_stats = {
                "total_alerts": float(len(self.alerts)),
                "by_level": {k: float(v) for k, v in alert_levels.items()},
            }
            stats.update(alert_stats)

            return stats

    def print_status(self) -> None:
        """Print current monitoring status to console."""
        status = self.get_status()
        stats = self.get_statistics()

        print("\n" + "=" * 50)
        print("APGI Simple Monitor Status")
        print("=" * 50)
        print(f"Status: {status['system_status']}")
        print(f"Monitoring: {'Yes' if status['is_monitoring'] else 'No'}")
        print(f"Runtime: {status['runtime_seconds']:.1f} seconds")
        print(f"Total Updates: {status['total_updates']}")
        print(f"Buffer Size: {status['buffer_size']}/{self.buffer_size}")
        print(f"Alerts: {status['alert_count']}")

        if status["current_metrics"]:
            print("\nCurrent Metrics:")
            for key, value in status["current_metrics"].items():
                if key != "timestamp":
                    if isinstance(value, float):
                        print(f"  {key}: {value:.3f}")
                    else:
                        print(f"  {key}: {value}")

        if "temporal" in stats:
            print(f"\nUpdate Rate: {stats['temporal']['update_rate_hz']:.2f} Hz")
            print(f"Duration: {stats['temporal']['duration_ms']/1000:.1f} seconds")

        if status["recent_alerts"]:
            print("\nRecent Alerts:")
            for alert in status["recent_alerts"]:
                print(f"  [{alert['level'].upper()}] {alert['message']}")

        print("=" * 50)

    def __del__(self):
        """Cleanup when monitor is destroyed."""
        self.stop_monitoring()


class MonitoringIntegration:
    """
    Integration helper for connecting APGI system to simple monitor.
    """

    def __init__(self, monitor: SimpleMonitor):
        """
        Initialize monitoring integration.

        Args:
            monitor: SimpleMonitor instance
        """
        self.monitor = monitor
        self.is_connected = False

    def connect_system(self, apgi_system):
        """
        Connect APGI system to monitor.

        Args:
            apgi_system: APGI system instance to monitor
        """
        # Add monitoring callback to system
        if hasattr(apgi_system, "add_monitor_callback"):
            apgi_system.add_monitor_callback(self.monitor.update_data)
            self.is_connected = True
            print("APGI system connected to simple monitor")
        else:
            print("Warning: APGI system does not support monitoring callbacks")

    def disconnect_system(self, apgi_system):
        """
        Disconnect APGI system from monitor.

        Args:
            apgi_system: APGI system instance to disconnect
        """
        if hasattr(apgi_system, "remove_monitor_callback"):
            apgi_system.remove_monitor_callback(self.monitor.update_data)
            self.is_connected = False
            print("APGI system disconnected from simple monitor")

    def simulate_data(self, duration: float = 60.0, interval: float = 0.1):
        """
        Simulate APGI system data for testing the monitor.

        Args:
            duration: Simulation duration in seconds
            interval: Update interval in seconds
        """
        print(f"Starting data simulation for {duration} seconds...")

        start_time = time.time()
        step = 0

        while time.time() - start_time < duration:
            # Generate synthetic APGI system state
            current_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Simulate realistic system dynamics
            ignition_base = 1.0 + 0.5 * np.sin(step * 0.1)
            ignition_noise = 0.2 * np.random.randn()
            ignition_signal = max(0, ignition_base + ignition_noise)

            free_energy = 1.5 + 0.3 * np.cos(step * 0.05) + 0.1 * np.random.randn()
            precision = 0.7 + 0.2 * np.sin(step * 0.08) + 0.05 * np.random.randn()
            energy_reserves = max(0.1, 1.0 - step * 0.0001 + 0.02 * np.random.randn())
            coherence = 0.6 + 0.3 * np.sin(step * 0.03) + 0.05 * np.random.randn()

            # Create mock system state
            system_state = {
                "time": current_time,
                "ignition": {
                    "total_signal": ignition_signal,
                    "ignition_occurred": ignition_signal > 2.0,
                },
                "free_energy": {"total_free_energy": free_energy},
                "precision": {"mean_precision": precision},
                "metabolism": {"current_reserves": energy_reserves},
                "self_model": {"coherence_score": coherence},
            }

            # Update monitor
            self.monitor.update_data(system_state)

            step += 1
            time.sleep(interval)

        print("Data simulation completed")


# Example usage
if __name__ == "__main__":
    # Create simple monitor
    monitor = SimpleMonitor(buffer_size=1000, update_interval=0.1)
    integration = MonitoringIntegration(monitor)

    # Start monitoring
    monitor.start_monitoring()

    try:
        # Run simulation
        integration.simulate_data(duration=10.0, interval=0.1)

        # Print final status
        monitor.print_status()

        # Export data
        export_path = "monitoring_data.json"
        monitor.export_data(export_path)

    except KeyboardInterrupt:
        print("\nStopping monitoring...")
    finally:
        monitor.stop_monitoring()
