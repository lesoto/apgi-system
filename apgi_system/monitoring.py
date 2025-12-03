"""Performance monitoring utilities for the APGI system.

This module provides tools for tracking and analyzing system performance metrics
including execution time, memory usage, and computational efficiency.
"""

import time
import psutil
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class PerformanceMetrics:
    """Track system performance metrics.
    
    Attributes
    ----------
    step_time_ms : float
        Time taken for a single system step in milliseconds
    memory_usage_mb : float
        Current memory usage in megabytes
    ignition_rate_hz : float
        Rate of ignition events per second
    free_energy_mean : float
        Mean free energy value
    precision_mean : float
        Mean precision value
    timestamp : float
        Timestamp when metrics were recorded (in milliseconds)
    """
    step_time_ms: float
    memory_usage_mb: float
    ignition_rate_hz: float
    free_energy_mean: float
    precision_mean: float
    timestamp: float


class PerformanceMonitor:
    """Monitor and track system performance over time.
    
    This class provides utilities for tracking execution time, memory usage,
    and other performance metrics during system operation.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing monitoring settings
    
    Attributes
    ----------
    enabled : bool
        Whether performance monitoring is enabled
    history : List[PerformanceMetrics]
        History of recorded performance metrics
    max_history_size : int
        Maximum number of metrics to keep in history
    process : psutil.Process
        Process object for memory tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize performance monitor.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary
        """
        self.config = config
        self.enabled = config.get("monitoring", {}).get("enabled", True)
        self.max_history_size = config.get("monitoring", {}).get("max_history_size", 1000)
        
        # Performance tracking
        self.history: List[PerformanceMetrics] = []
        self.step_start_time: Optional[float] = None
        self.last_step_time_ms: float = 0.0
        
        # Memory tracking
        self.process = psutil.Process()
        
        # Ignition tracking for rate calculation
        self.ignition_times: List[float] = []
        self.ignition_window_ms: float = 1000.0  # 1 second window
        
    def start_step(self) -> None:
        """Mark the start of a system step for timing."""
        if self.enabled:
            self.step_start_time = time.perf_counter()
    
    def end_step(
        self,
        system_time_ms: float,
        ignition_occurred: bool,
        free_energy: float,
        precision: float
    ) -> Optional[PerformanceMetrics]:
        """Mark the end of a system step and record metrics.
        
        Parameters
        ----------
        system_time_ms : float
            Current system time in milliseconds
        ignition_occurred : bool
            Whether an ignition event occurred in this step
        free_energy : float
            Current free energy value
        precision : float
            Current precision value
            
        Returns
        -------
        metrics : Optional[PerformanceMetrics]
            Performance metrics for this step, or None if monitoring disabled
        """
        if not self.enabled or self.step_start_time is None:
            return None
        
        # Calculate step execution time
        step_end_time = time.perf_counter()
        self.last_step_time_ms = (step_end_time - self.step_start_time) * 1000.0
        
        # Get memory usage
        memory_info = self.process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        
        # Track ignition events
        if ignition_occurred:
            self.ignition_times.append(system_time_ms)
        
        # Calculate ignition rate (events per second)
        ignition_rate_hz = self._calculate_ignition_rate(system_time_ms)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            step_time_ms=self.last_step_time_ms,
            memory_usage_mb=memory_usage_mb,
            ignition_rate_hz=ignition_rate_hz,
            free_energy_mean=free_energy,
            precision_mean=precision,
            timestamp=system_time_ms
        )
        
        # Add to history
        self.history.append(metrics)
        
        # Trim history if needed
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
        
        # Reset step timer
        self.step_start_time = None
        
        return metrics
    
    def _calculate_ignition_rate(self, current_time_ms: float) -> float:
        """Calculate ignition rate over recent window.
        
        Parameters
        ----------
        current_time_ms : float
            Current system time in milliseconds
            
        Returns
        -------
        rate_hz : float
            Ignition rate in Hz (events per second)
        """
        # Remove old ignition events outside the window
        cutoff_time = current_time_ms - self.ignition_window_ms
        self.ignition_times = [t for t in self.ignition_times if t >= cutoff_time]
        
        # Calculate rate
        if len(self.ignition_times) == 0:
            return 0.0
        
        # Events per second
        time_span_s = self.ignition_window_ms / 1000.0
        return len(self.ignition_times) / time_span_s
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of performance metrics.
        
        Returns
        -------
        stats : Dict[str, Any]
            Dictionary containing performance statistics including:
            - mean_step_time_ms: Average step execution time
            - max_step_time_ms: Maximum step execution time
            - min_step_time_ms: Minimum step execution time
            - mean_memory_mb: Average memory usage
            - max_memory_mb: Peak memory usage
            - mean_ignition_rate_hz: Average ignition rate
            - total_samples: Number of recorded samples
        """
        if not self.history:
            return {
                "mean_step_time_ms": 0.0,
                "max_step_time_ms": 0.0,
                "min_step_time_ms": 0.0,
                "mean_memory_mb": 0.0,
                "max_memory_mb": 0.0,
                "mean_ignition_rate_hz": 0.0,
                "total_samples": 0
            }
        
        step_times = [m.step_time_ms for m in self.history]
        memory_usage = [m.memory_usage_mb for m in self.history]
        ignition_rates = [m.ignition_rate_hz for m in self.history]
        
        return {
            "mean_step_time_ms": float(np.mean(step_times)),
            "max_step_time_ms": float(np.max(step_times)),
            "min_step_time_ms": float(np.min(step_times)),
            "std_step_time_ms": float(np.std(step_times)),
            "mean_memory_mb": float(np.mean(memory_usage)),
            "max_memory_mb": float(np.max(memory_usage)),
            "min_memory_mb": float(np.min(memory_usage)),
            "mean_ignition_rate_hz": float(np.mean(ignition_rates)),
            "max_ignition_rate_hz": float(np.max(ignition_rates)),
            "total_samples": len(self.history)
        }
    
    def get_recent_metrics(self, n: int = 10) -> List[PerformanceMetrics]:
        """Get the most recent n performance metrics.
        
        Parameters
        ----------
        n : int, optional
            Number of recent metrics to retrieve, by default 10
            
        Returns
        -------
        metrics : List[PerformanceMetrics]
            List of recent performance metrics
        """
        return self.history[-n:] if self.history else []
    
    def reset(self) -> None:
        """Reset performance monitoring state."""
        self.history.clear()
        self.ignition_times.clear()
        self.step_start_time = None
        self.last_step_time_ms = 0.0
    
    def log_performance(self, verbose: bool = False) -> None:
        """Log current performance statistics.
        
        Parameters
        ----------
        verbose : bool, optional
            Whether to print detailed statistics, by default False
        """
        if not self.enabled or not self.history:
            return
        
        stats = self.get_statistics()
        
        print(f"\n=== Performance Statistics ===")
        print(f"Total samples: {stats['total_samples']}")
        print(f"Step time: {stats['mean_step_time_ms']:.3f} ms "
              f"(min: {stats['min_step_time_ms']:.3f}, "
              f"max: {stats['max_step_time_ms']:.3f})")
        print(f"Memory usage: {stats['mean_memory_mb']:.1f} MB "
              f"(max: {stats['max_memory_mb']:.1f} MB)")
        print(f"Ignition rate: {stats['mean_ignition_rate_hz']:.2f} Hz "
              f"(max: {stats['max_ignition_rate_hz']:.2f} Hz)")
        
        if verbose and len(self.history) > 0:
            recent = self.get_recent_metrics(5)
            print(f"\nRecent metrics (last 5):")
            for i, m in enumerate(recent, 1):
                print(f"  {i}. Time: {m.timestamp:.1f}ms, "
                      f"Step: {m.step_time_ms:.3f}ms, "
                      f"Mem: {m.memory_usage_mb:.1f}MB")
