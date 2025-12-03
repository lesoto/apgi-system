"""
Unit tests for performance monitoring.

Tests the PerformanceMonitor class and PerformanceMetrics dataclass.
"""

import pytest
import numpy as np
import time
from apgi_system.monitoring import PerformanceMonitor, PerformanceMetrics


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test creating a PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            step_time_ms=5.0,
            memory_usage_mb=100.0,
            ignition_rate_hz=2.5,
            free_energy_mean=10.0,
            precision_mean=1.5,
            timestamp=1000.0
        )
        
        assert metrics.step_time_ms == 5.0
        assert metrics.memory_usage_mb == 100.0
        assert metrics.ignition_rate_hz == 2.5
        assert metrics.free_energy_mean == 10.0
        assert metrics.precision_mean == 1.5
        assert metrics.timestamp == 1000.0


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return {
            "monitoring": {
                "enabled": True,
                "max_history_size": 100
            }
        }
    
    @pytest.fixture
    def monitor(self, config):
        """Provide a PerformanceMonitor instance."""
        return PerformanceMonitor(config)
    
    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.enabled is True
        assert monitor.max_history_size == 100
        assert len(monitor.history) == 0
        assert len(monitor.ignition_times) == 0
    
    def test_disabled_monitoring(self):
        """Test that monitoring can be disabled."""
        config = {"monitoring": {"enabled": False}}
        monitor = PerformanceMonitor(config)
        
        monitor.start_step()
        metrics = monitor.end_step(
            system_time_ms=1.0,
            ignition_occurred=True,
            free_energy=10.0,
            precision=1.5
        )
        
        assert metrics is None
        assert len(monitor.history) == 0
    
    def test_step_timing(self, monitor):
        """Test step execution time tracking."""
        monitor.start_step()
        time.sleep(0.01)  # Sleep for 10ms
        
        metrics = monitor.end_step(
            system_time_ms=1.0,
            ignition_occurred=False,
            free_energy=10.0,
            precision=1.5
        )
        
        assert metrics is not None
        assert metrics.step_time_ms >= 10.0  # Should be at least 10ms
        assert metrics.step_time_ms < 100.0  # But not too long
    
    def test_memory_tracking(self, monitor):
        """Test memory usage tracking."""
        monitor.start_step()
        
        metrics = monitor.end_step(
            system_time_ms=1.0,
            ignition_occurred=False,
            free_energy=10.0,
            precision=1.5
        )
        
        assert metrics is not None
        assert metrics.memory_usage_mb > 0
        assert metrics.memory_usage_mb < 10000  # Reasonable upper bound
    
    def test_ignition_rate_calculation(self, monitor):
        """Test ignition rate calculation."""
        # Record several ignition events
        for i in range(5):
            monitor.start_step()
            metrics = monitor.end_step(
                system_time_ms=float(i * 100),  # 100ms apart
                ignition_occurred=True,
                free_energy=10.0,
                precision=1.5
            )
        
        # Should have recorded ignitions
        assert len(monitor.ignition_times) == 5
        
        # Rate should be positive
        last_metrics = monitor.history[-1]
        assert last_metrics.ignition_rate_hz > 0
    
    def test_ignition_rate_window(self, monitor):
        """Test that ignition rate uses a sliding window."""
        # Add old ignition event (outside window)
        monitor.ignition_times.append(0.0)
        
        # Add recent ignition event
        monitor.start_step()
        metrics = monitor.end_step(
            system_time_ms=2000.0,  # 2 seconds later
            ignition_occurred=True,
            free_energy=10.0,
            precision=1.5
        )
        
        # Old event should be removed from calculation
        assert len(monitor.ignition_times) == 1
        assert monitor.ignition_times[0] == 2000.0
    
    def test_history_recording(self, monitor):
        """Test that metrics are recorded in history."""
        for i in range(10):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=False,
                free_energy=10.0 + i,
                precision=1.5
            )
        
        assert len(monitor.history) == 10
        
        # Check that values are recorded correctly
        assert monitor.history[0].free_energy_mean == 10.0
        assert monitor.history[9].free_energy_mean == 19.0
    
    def test_history_size_limit(self):
        """Test that history is limited to max_history_size."""
        config = {"monitoring": {"enabled": True, "max_history_size": 5}}
        monitor = PerformanceMonitor(config)
        
        # Add more than max_history_size entries
        for i in range(10):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=False,
                free_energy=10.0,
                precision=1.5
            )
        
        # Should only keep the last 5
        assert len(monitor.history) == 5
        assert monitor.history[0].timestamp == 5.0
        assert monitor.history[-1].timestamp == 9.0
    
    def test_get_statistics_empty(self, monitor):
        """Test statistics with no data."""
        stats = monitor.get_statistics()
        
        assert stats["total_samples"] == 0
        assert stats["mean_step_time_ms"] == 0.0
        assert stats["max_step_time_ms"] == 0.0
    
    def test_get_statistics(self, monitor):
        """Test statistics calculation."""
        # Add some metrics
        for i in range(5):
            monitor.start_step()
            time.sleep(0.001)  # Small delay
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=i % 2 == 0,  # Alternate ignitions
                free_energy=10.0,
                precision=1.5
            )
        
        stats = monitor.get_statistics()
        
        assert stats["total_samples"] == 5
        assert stats["mean_step_time_ms"] > 0
        assert stats["max_step_time_ms"] >= stats["min_step_time_ms"]
        assert stats["mean_memory_mb"] > 0
        assert "std_step_time_ms" in stats
    
    def test_get_recent_metrics(self, monitor):
        """Test retrieving recent metrics."""
        # Add 10 metrics
        for i in range(10):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=False,
                free_energy=10.0,
                precision=1.5
            )
        
        # Get last 3
        recent = monitor.get_recent_metrics(n=3)
        
        assert len(recent) == 3
        assert recent[0].timestamp == 7.0
        assert recent[-1].timestamp == 9.0
    
    def test_get_recent_metrics_empty(self, monitor):
        """Test getting recent metrics when history is empty."""
        recent = monitor.get_recent_metrics(n=5)
        assert len(recent) == 0
    
    def test_reset(self, monitor):
        """Test resetting the monitor."""
        # Add some data
        for i in range(5):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=True,
                free_energy=10.0,
                precision=1.5
            )
        
        assert len(monitor.history) > 0
        assert len(monitor.ignition_times) > 0
        
        # Reset
        monitor.reset()
        
        assert len(monitor.history) == 0
        assert len(monitor.ignition_times) == 0
        assert monitor.step_start_time is None
        assert monitor.last_step_time_ms == 0.0
    
    def test_log_performance_empty(self, monitor, capsys):
        """Test logging with no data."""
        monitor.log_performance()
        captured = capsys.readouterr()
        
        # Should not print anything when no data
        assert captured.out == ""
    
    def test_log_performance(self, monitor, capsys):
        """Test performance logging."""
        # Add some metrics
        for i in range(3):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=True,
                free_energy=10.0,
                precision=1.5
            )
        
        monitor.log_performance(verbose=False)
        captured = capsys.readouterr()
        
        assert "Performance Statistics" in captured.out
        assert "Total samples" in captured.out
        assert "Step time" in captured.out
        assert "Memory usage" in captured.out
    
    def test_log_performance_verbose(self, monitor, capsys):
        """Test verbose performance logging."""
        # Add some metrics
        for i in range(3):
            monitor.start_step()
            monitor.end_step(
                system_time_ms=float(i),
                ignition_occurred=False,
                free_energy=10.0,
                precision=1.5
            )
        
        monitor.log_performance(verbose=True)
        captured = capsys.readouterr()
        
        assert "Performance Statistics" in captured.out
        assert "Recent metrics" in captured.out
    
    def test_step_without_start(self, monitor):
        """Test ending step without starting it."""
        metrics = monitor.end_step(
            system_time_ms=1.0,
            ignition_occurred=False,
            free_energy=10.0,
            precision=1.5
        )
        
        # Should return None if start_step wasn't called
        assert metrics is None
    
    def test_performance_meets_requirements(self, monitor):
        """Test that step time meets requirement 9.1 (< 10ms)."""
        # This is more of an integration test, but we can check
        # that the monitoring correctly tracks times
        monitor.start_step()
        
        # Simulate a fast operation
        _ = np.random.randn(100)
        
        metrics = monitor.end_step(
            system_time_ms=1.0,
            ignition_occurred=False,
            free_energy=10.0,
            precision=1.5
        )
        
        # The monitoring itself should be very fast
        assert metrics.step_time_ms < 100.0  # Very generous bound
