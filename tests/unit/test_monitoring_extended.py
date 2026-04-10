"""
Extended tests for monitoring module to improve coverage.

Tests the performance monitoring capabilities including metrics tracking,
performance analysis, and system monitoring functionality.
"""

import pytest
import time
import numpy as np
from unittest.mock import patch, MagicMock
from apgi_system.monitoring import (
    PerformanceMetrics,
    PerformanceMonitor,
    SystemProfiler,
    MetricsCollector,
)


class TestPerformanceMetrics:
    """Test the PerformanceMetrics dataclass."""

    def test_performance_metrics_initialization(self):
        """Test that PerformanceMetrics can be initialized."""
        metrics = PerformanceMetrics(
            step_time_ms=10.5,
            memory_usage_mb=256.0,
            ignition_rate_hz=0.5,
            free_energy_mean=1.2,
            precision_mean=0.8,
            timestamp=1000.0,
        )

        assert metrics.step_time_ms == 10.5
        assert metrics.memory_usage_mb == 256.0
        assert metrics.ignition_rate_hz == 0.5
        assert metrics.free_energy_mean == 1.2
        assert metrics.precision_mean == 0.8
        assert metrics.timestamp == 1000.0

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metrics = PerformanceMetrics(
            step_time_ms=0.0,
            memory_usage_mb=0.0,
            ignition_rate_hz=0.0,
            free_energy_mean=0.0,
            precision_mean=0.0,
            timestamp=0.0,
        )

        assert all(
            value == 0.0
            for value in [
                metrics.step_time_ms,
                metrics.memory_usage_mb,
                metrics.ignition_rate_hz,
                metrics.free_energy_mean,
                metrics.precision_mean,
                metrics.timestamp,
            ]
        )


class TestPerformanceMonitor:
    """Test the PerformanceMonitor class."""

    def test_monitor_initialization(self):
        """Test that PerformanceMonitor initializes correctly."""
        config = {"sampling_interval": 100, "memory_threshold_mb": 1000, "enable_profiling": True}

        monitor = PerformanceMonitor(config)

        assert monitor.config == config
        assert monitor.sampling_interval == 100
        assert monitor.memory_threshold_mb == 1000
        assert monitor.enable_profiling is True
        assert isinstance(monitor.metrics_history, list)
        assert len(monitor.metrics_history) == 0

    def test_monitor_default_config(self):
        """Test PerformanceMonitor with default configuration."""
        monitor = PerformanceMonitor()

        assert monitor.sampling_interval == 1000  # Default 1 second
        assert monitor.memory_threshold_mb == 2000  # Default 2GB
        assert monitor.enable_profiling is False
        assert isinstance(monitor.metrics_history, list)

    @patch("psutil.Process")
    @patch("time.time")
    def test_record_metrics(self, mock_time, mock_process):
        """Test recording performance metrics."""
        # Mock time and memory
        mock_time.return_value = 1000.0
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 256 * 1024 * 1024  # 256 MB
        mock_process.return_value = mock_proc

        monitor = PerformanceMonitor()

        # Mock system state
        system_state = {
            "ignition": {"ignition_occurred": True, "total_signal": 2.0},
            "free_energy": {"total_free_energy": 1.5},
            "precision": {"mean_precision": 0.8},
        }

        step_time = 15.5
        monitor.record_metrics(system_state, step_time)

        assert len(monitor.metrics_history) == 1
        metrics = monitor.metrics_history[0]
        assert metrics.step_time_ms == 15.5
        assert metrics.memory_usage_mb == 256.0
        assert metrics.free_energy_mean == 1.5
        assert metrics.precision_mean == 0.8

    def test_get_average_metrics_empty(self):
        """Test getting average metrics with no data."""
        monitor = PerformanceMonitor()

        avg_metrics = monitor.get_average_metrics()

        assert avg_metrics["step_time_ms"] == 0.0
        assert avg_metrics["memory_usage_mb"] == 0.0
        assert avg_metrics["ignition_rate_hz"] == 0.0

    def test_get_average_metrics_with_data(self):
        """Test getting average metrics with actual data."""
        monitor = PerformanceMonitor()

        # Add some mock metrics
        metrics1 = PerformanceMetrics(10.0, 200.0, 0.5, 1.0, 0.8, 1000.0)
        metrics2 = PerformanceMetrics(20.0, 300.0, 0.3, 1.5, 0.6, 2000.0)
        metrics3 = PerformanceMetrics(15.0, 250.0, 0.4, 1.2, 0.7, 3000.0)

        monitor.metrics_history = [metrics1, metrics2, metrics3]

        avg_metrics = monitor.get_average_metrics()

        assert avg_metrics["step_time_ms"] == 15.0  # (10+20+15)/3
        assert avg_metrics["memory_usage_mb"] == 250.0  # (200+300+250)/3
        assert avg_metrics["ignition_rate_hz"] == 0.4  # (0.5+0.3+0.4)/3
        assert avg_metrics["free_energy_mean"] == pytest.approx(1.233, abs=1e-3)
        assert avg_metrics["precision_mean"] == pytest.approx(0.7, abs=1e-3)

    def test_get_performance_summary(self):
        """Test getting performance summary."""
        monitor = PerformanceMonitor()

        # Add metrics with varying performance
        for i in range(10):
            metrics = PerformanceMetrics(
                step_time_ms=10.0 + i,
                memory_usage_mb=200.0 + i * 10,
                ignition_rate_hz=0.1 * i,
                free_energy_mean=1.0 + 0.1 * i,
                precision_mean=0.5 + 0.05 * i,
                timestamp=1000.0 + i * 100,
            )
            monitor.metrics_history.append(metrics)

        summary = monitor.get_performance_summary()

        assert "total_samples" in summary
        assert "time_range_ms" in summary
        assert "average_metrics" in summary
        assert "peak_metrics" in summary
        assert "performance_trends" in summary

        assert summary["total_samples"] == 10
        assert summary["time_range_ms"] == 900.0  # 9 * 100
        assert summary["peak_metrics"]["max_step_time_ms"] == 19.0
        assert summary["peak_metrics"]["max_memory_usage_mb"] == 290.0

    def test_detect_performance_issues(self):
        """Test performance issue detection."""
        config = {
            "step_time_threshold_ms": 15.0,
            "memory_threshold_mb": 250.0,
            "ignition_rate_threshold_hz": 0.1,
        }
        monitor = PerformanceMonitor(config)

        # Add metrics that exceed thresholds
        slow_metrics = PerformanceMetrics(20.0, 300.0, 0.05, 1.0, 0.8, 1000.0)
        monitor.metrics_history.append(slow_metrics)

        issues = monitor.detect_performance_issues()

        assert len(issues) > 0
        assert any("step time" in issue.lower() for issue in issues)
        assert any("memory usage" in issue.lower() for issue in issues)
        assert any("ignition rate" in issue.lower() for issue in issues)

    def test_reset_metrics(self):
        """Test resetting metrics history."""
        monitor = PerformanceMonitor()

        # Add some metrics
        metrics = PerformanceMetrics(10.0, 200.0, 0.5, 1.0, 0.8, 1000.0)
        monitor.metrics_history.append(metrics)

        assert len(monitor.metrics_history) == 1

        monitor.reset_metrics()

        assert len(monitor.metrics_history) == 0


class TestSystemProfiler:
    """Test the SystemProfiler class."""

    def test_profiler_initialization(self):
        """Test SystemProfiler initialization."""
        profiler = SystemProfiler()

        assert isinstance(profiler.profile_data, dict)
        assert profiler.is_profiling is False
        assert profiler.start_time is None

    def test_start_profiling(self):
        """Test starting profiling."""
        profiler = SystemProfiler()

        profiler.start_profiling()

        assert profiler.is_profiling is True
        assert profiler.start_time is not None
        assert isinstance(profiler.start_time, float)

    def test_stop_profiling(self):
        """Test stopping profiling."""
        profiler = SystemProfiler()

        profiler.start_profiling()
        time.sleep(0.01)  # Small delay
        profile_data = profiler.stop_profiling()

        assert profiler.is_profiling is False
        assert isinstance(profile_data, dict)
        assert "total_time_ms" in profile_data
        assert profile_data["total_time_ms"] > 0

    def test_profile_function_decorator(self):
        """Test function profiling decorator."""
        profiler = SystemProfiler()

        @profiler.profile_function("test_function")
        def test_func():
            time.sleep(0.01)
            return 42

        result = test_func()

        assert result == 42
        assert "test_function" in profiler.profile_data
        assert profiler.profile_data["test_function"]["call_count"] == 1
        assert profiler.profile_data["test_function"]["total_time_ms"] > 0

    def test_profile_context_manager(self):
        """Test profiling context manager."""
        profiler = SystemProfiler()

        with profiler.profile_section("test_section"):
            time.sleep(0.01)

        assert "test_section" in profiler.profile_data
        assert profiler.profile_data["test_section"]["total_time_ms"] > 0

    def test_get_profile_summary(self):
        """Test getting profile summary."""
        profiler = SystemProfiler()

        # Add some mock profile data
        profiler.profile_data = {
            "function_a": {"call_count": 5, "total_time_ms": 100.0},
            "function_b": {"call_count": 3, "total_time_ms": 50.0},
            "section_c": {"total_time_ms": 75.0},
        }

        summary = profiler.get_profile_summary()

        assert "total_functions" in summary
        assert "total_time_ms" in summary
        assert "top_functions" in summary

        assert summary["total_functions"] == 3
        assert summary["total_time_ms"] == 225.0  # 100 + 50 + 75


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()

        assert isinstance(collector.metrics, dict)
        assert isinstance(collector.timestamps, list)
        assert collector.collection_interval == 1.0  # Default 1 second

    def test_collect_system_metrics(self):
        """Test collecting system metrics."""
        collector = MetricsCollector()

        # Mock system state
        system_state = {
            "ignition": {"ignition_occurred": True, "total_signal": 2.5, "ignition_count": 5},
            "free_energy": {"total_free_energy": 1.8, "prediction_error": 0.3},
            "precision": {"mean_precision": 0.75, "precision_weights": np.array([0.8, 0.7, 0.8])},
            "workspace": {"is_broadcasting": True, "broadcast_strength": 1.2},
            "time": 5000.0,
        }

        collector.collect_metrics(system_state)

        assert len(collector.timestamps) == 1
        assert collector.timestamps[0] == 5000.0

        # Check that metrics were collected
        assert "ignition_signal" in collector.metrics
        assert "free_energy" in collector.metrics
        assert "precision" in collector.metrics
        assert "workspace_activity" in collector.metrics

        assert collector.metrics["ignition_signal"][-1] == 2.5
        assert collector.metrics["free_energy"][-1] == 1.8
        assert collector.metrics["precision"][-1] == 0.75

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()

        # Add some mock data
        collector.timestamps = [1000.0, 2000.0, 3000.0]
        collector.metrics = {
            "ignition_signal": [1.0, 2.0, 1.5],
            "free_energy": [1.2, 1.8, 1.5],
            "precision": [0.7, 0.8, 0.75],
        }

        summary = collector.get_summary()

        assert "collection_period_ms" in summary
        assert "total_samples" in summary
        assert "metrics_summary" in summary

        assert summary["total_samples"] == 3
        assert summary["collection_period_ms"] == 2000.0  # 3000 - 1000

        # Check individual metric summaries
        ignition_summary = summary["metrics_summary"]["ignition_signal"]
        assert ignition_summary["mean"] == 1.5  # (1.0 + 2.0 + 1.5) / 3
        assert ignition_summary["min"] == 1.0
        assert ignition_summary["max"] == 2.0

    def test_export_metrics(self):
        """Test exporting metrics to different formats."""
        collector = MetricsCollector()

        # Add some data
        collector.timestamps = [1000.0, 2000.0]
        collector.metrics = {"ignition_signal": [1.0, 2.0], "free_energy": [1.2, 1.8]}

        # Test CSV export
        csv_data = collector.export_csv()
        assert isinstance(csv_data, str)
        assert "timestamp" in csv_data
        assert "ignition_signal" in csv_data
        assert "free_energy" in csv_data

        # Test JSON export
        json_data = collector.export_json()
        assert isinstance(json_data, str)
        assert '"timestamps"' in json_data
        assert '"metrics"' in json_data

    def test_clear_metrics(self):
        """Test clearing collected metrics."""
        collector = MetricsCollector()

        # Add some data
        collector.timestamps = [1000.0, 2000.0]
        collector.metrics = {"test_metric": [1.0, 2.0]}

        assert len(collector.timestamps) == 2
        assert len(collector.metrics["test_metric"]) == 2

        collector.clear()

        assert len(collector.timestamps) == 0
        assert len(collector.metrics) == 0


class TestMonitoringIntegration:
    """Integration tests for monitoring functionality."""

    @patch("psutil.Process")
    def test_full_monitoring_pipeline(self, mock_process):
        """Test the complete monitoring pipeline."""
        # Mock memory usage
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 512 * 1024 * 1024  # 512 MB
        mock_process.return_value = mock_proc

        # Initialize components
        monitor = PerformanceMonitor({"sampling_interval": 100})
        profiler = SystemProfiler()
        collector = MetricsCollector()

        # Simulate system operation
        profiler.start_profiling()

        for i in range(5):
            # Mock system state
            system_state = {
                "ignition": {
                    "ignition_occurred": i % 2 == 0,
                    "total_signal": 1.0 + i * 0.2,
                    "ignition_count": i,
                },
                "free_energy": {"total_free_energy": 1.5 + i * 0.1},
                "precision": {"mean_precision": 0.7 + i * 0.05},
                "workspace": {"is_broadcasting": True, "broadcast_strength": 1.0},
                "time": 1000.0 + i * 100,
            }

            # Record metrics
            step_time = 10.0 + i
            monitor.record_metrics(system_state, step_time)
            collector.collect_metrics(system_state)

        profile_data = profiler.stop_profiling()

        # Verify monitoring results
        assert len(monitor.history) == 5
        assert profile_data["total_time_ms"] > 0

        # Get summaries
        perf_summary = monitor.get_statistics()
        metrics_summary = collector.get_metrics_summary()

        assert perf_summary["total_samples"] == 5
        assert metrics_summary["total_sources"] == 0  # No sources added

        # Check for statistics fields
        assert "mean_step_time_ms" in perf_summary
        assert "max_step_time_ms" in perf_summary
