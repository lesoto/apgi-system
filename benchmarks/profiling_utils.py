"""
Performance profiling utilities for APGI Framework
Provides tools for profiling and analyzing performance bottlenecks.
"""

import cProfile
import functools
import io
import pstats
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd
import psutil


class Profiler:
    """Advanced profiling utility for performance analysis."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.profiles: Dict[str, Any] = {}

    def profile_function(self, name: Optional[str] = None):
        """Decorator to profile a function."""

        def decorator(func: Callable) -> Callable:
            profile_name = name or f"{func.__module__}.{func.__name__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                pr = cProfile.Profile()
                pr.enable()

                try:
                    result = func(*args, **kwargs)
                finally:
                    pr.disable()

                    # Save profile stats
                    s = io.StringIO()
                    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")

                    # Save to file
                    profile_file = self.output_dir / f"{profile_name}.prof"
                    ps.dump_stats(profile_file)

                    # Save human-readable stats
                    text_file = self.output_dir / f"{profile_name}.txt"
                    with open(text_file, "w") as f:
                        ps.print_stats(20, f)  # Top 20 functions

                    # Store summary
                    self.profiles[profile_name] = {
                        "file": profile_file,
                        "text_file": text_file,
                        "stats": ps,
                    }

                return result

            return wrapper

        return decorator

    def profile_method(self, cls_name: Optional[str] = None):
        """Decorator to profile all methods of a class."""

        def decorator(cls):
            class_name = cls_name or cls.__name__

            for attr_name, attr_value in cls.__dict__.items():
                if callable(attr_value) and not attr_name.startswith("_"):
                    # Profile the method
                    profiled_method = self.profile_function(f"{class_name}.{attr_name}")(attr_value)
                    setattr(cls, attr_name, profiled_method)

            return cls

        return decorator

    def compare_profiles(self, profile_names: List[str]) -> pd.DataFrame:
        """Compare multiple profiles and return performance metrics."""
        comparison_data = []

        for name in profile_names:
            if name in self.profiles:
                stats = self.profiles[name]["stats"]

                # Extract key metrics
                total_calls = sum(stat.callcount for stat in stats.stats.values())
                total_time = sum(stat.cumtime for stat in stats.stats.values())

                # Get top function
                top_func = max(stats.stats.items(), key=lambda x: x[1].cumtime)
                top_func_name = top_func[0]
                top_func_time = top_func[1].cumtime

                comparison_data.append(
                    {
                        "profile": name,
                        "total_calls": total_calls,
                        "total_time": total_time,
                        "top_function": str(top_func_name),
                        "top_function_time": top_func_time,
                    }
                )

        df = pd.DataFrame(comparison_data)

        # Save comparison
        comparison_file = self.output_dir / "profile_comparison.csv"
        df.to_csv(comparison_file, index=False)

        return df

    def generate_report(self) -> str:
        """Generate a comprehensive profiling report."""
        report_lines = ["# Performance Profiling Report\n"]

        for name, profile_data in self.profiles.items():
            report_lines.append(f"## {name}\n")

            # Read the text file
            with open(profile_data["text_file"], "r") as f:
                content = f.read()
                report_lines.append(content)

            report_lines.append("\n" + "=" * 50 + "\n")

        report_content = "\n".join(report_lines)

        # Save report
        report_file = self.output_dir / "profiling_report.md"
        with open(report_file, "w") as f:
            f.write(report_content)

        return report_content


class MemoryProfiler:
    """Memory profiling utility."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.snapshots: List[Dict[str, Any]] = []

    def take_snapshot(self, name: Optional[str] = None):
        """Take a memory snapshot."""
        import tracemalloc

        if not tracemalloc.is_tracing():
            tracemalloc.start()

        snapshot = tracemalloc.take_snapshot()
        snapshot_name = name or f"snapshot_{len(self.snapshots)}"

        self.snapshots.append({"name": snapshot_name, "snapshot": snapshot, "time": time.time()})

        return snapshot

    def compare_snapshots(self, before_idx: int, after_idx: int) -> str:
        """Compare two memory snapshots."""
        before = self.snapshots[before_idx]["snapshot"]
        after = self.snapshots[after_idx]["snapshot"]

        stats = after.compare_to(before, "lineno")

        # Generate comparison report
        report_lines = [
            f"Memory comparison: {self.snapshots[after_idx]['name']} - "
            f"{self.snapshots[before_idx]['name']}\n"
        ]

        for stat in stats[:10]:  # Top 10 memory consumers
            report_lines.append(f"{stat}\n")

        # Save comparison
        comparison_file = self.output_dir / f"memory_comparison_{before_idx}_{after_idx}.txt"
        with open(comparison_file, "w") as f:
            f.writelines(report_lines)

        return "".join(report_lines)

    def plot_memory_usage(self):
        """Plot memory usage over time."""
        if len(self.snapshots) < 2:
            return

        # Calculate memory usage for each snapshot
        memory_usage = []
        times = []
        names = []

        for snapshot_data in self.snapshots:
            stats = snapshot_data["snapshot"].statistics("lineno")
            total_memory = sum(stat.size for stat in stats)

            memory_usage.append(total_memory / (1024 * 1024))  # Convert to MB
            times.append(snapshot_data["time"])
            names.append(snapshot_data["name"])

        # Create plot
        plt.figure(figsize=(10, 6))
        plt.plot(times, memory_usage, "b-o")
        plt.xlabel("Time")
        plt.ylabel("Memory Usage (MB)")
        plt.title("Memory Usage Over Time")
        plt.grid(True)

        # Add labels for each point
        for i, name in enumerate(names):
            plt.annotate(
                name,
                (times[i], memory_usage[i]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )

        plt.tight_layout()

        # Save plot
        plot_file = self.output_dir / "memory_usage.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()

        return plot_file


class SystemMonitor:
    """Monitor system resources during execution."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.monitoring = False
        self.data: List[Dict[str, Any]] = []

    def start_monitoring(self, interval: float = 0.1):
        """Start monitoring system resources."""
        self.monitoring = True
        self.data = []

        import threading

        def monitor_loop():
            process = psutil.Process()
            while self.monitoring:
                try:
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)

                    self.data.append(
                        {
                            "time": time.time(),
                            "cpu_percent": cpu_percent,
                            "memory_mb": memory_mb,
                            "memory_percent": process.memory_percent(),
                        }
                    )

                    time.sleep(interval)
                except Exception:
                    break

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring and save results."""
        self.monitoring = False

        if self.data:
            df = pd.DataFrame(self.data)

            # Save raw data
            data_file = self.output_dir / "system_monitoring.csv"
            df.to_csv(data_file, index=False)

            # Create plots
            self._plot_system_usage(df)

            return df
        return None

    def _plot_system_usage(self, df: pd.DataFrame):
        """Create system usage plots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # CPU usage
        ax1.plot(df["time"], df["cpu_percent"], "b-", linewidth=1)
        ax1.set_ylabel("CPU Usage (%)")
        ax1.set_title("System Resource Usage")
        ax1.grid(True)

        # Memory usage
        ax2.plot(df["time"], df["memory_mb"], "r-", linewidth=1)
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Memory Usage (MB)")
        ax2.grid(True)

        plt.tight_layout()

        # Save plot
        plot_file = self.output_dir / "system_usage.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()


class BenchmarkRunner:
    """Run comprehensive benchmarks with monitoring."""

    def __init__(self, output_dir: str = "benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.profiler = Profiler(output_dir)
        self.memory_profiler = MemoryProfiler(output_dir)
        self.system_monitor = SystemMonitor(output_dir)

    def run_benchmark(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Run a single benchmark with full monitoring."""
        results = {}

        # Start monitoring
        self.system_monitor.start_monitoring()
        self.memory_profiler.take_snapshot("before")

        # Time the function
        start_time = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            results["result"] = result
            results["success"] = True
        except Exception as e:
            results["error"] = str(e)
            results["success"] = False
        finally:
            end_time = time.perf_counter()
            results["duration"] = end_time - start_time

        # Stop monitoring
        self.memory_profiler.take_snapshot("after")
        system_data = self.system_monitor.stop_monitoring()

        # Add system metrics
        if system_data is not None:
            results["avg_cpu"] = system_data["cpu_percent"].mean()
            results["max_memory"] = system_data["memory_mb"].max()
            results["avg_memory"] = system_data["memory_mb"].mean()

        # Memory comparison
        if len(self.memory_profiler.snapshots) >= 2:
            memory_diff = self.memory_profiler.compare_snapshots(0, -1)
            results["memory_diff"] = memory_diff

        return results

    def run_benchmark_suite(self, benchmarks: Dict[str, Callable]) -> pd.DataFrame:
        """Run a suite of benchmarks."""
        all_results = []

        for name, func in benchmarks.items():
            print(f"Running benchmark: {name}")

            results = self.run_benchmark(func)
            results["benchmark"] = name

            all_results.append(results)

        df = pd.DataFrame(all_results)

        # Save results
        results_file = self.output_dir / "benchmark_suite_results.csv"
        df.to_csv(results_file, index=False)

        # Generate summary report
        self._generate_summary_report(df)

        return df

    def _generate_summary_report(self, df: pd.DataFrame):
        """Generate a summary report of benchmark results."""
        report_lines = ["# Benchmark Suite Results\n"]

        # Summary statistics
        successful = df[df["success"]]

        if not successful.empty:
            report_lines.append("## Summary\n")
            report_lines.append(f"- Total benchmarks: {len(df)}\n")
            report_lines.append(f"- Successful: {len(successful)}\n")
            report_lines.append(f"- Failed: {len(df) - len(successful)}\n")

            if "duration" in successful.columns:
                avg_duration = successful["duration"].mean()
                total_duration = successful["duration"].sum()
                report_lines.append(f"- Average duration: {avg_duration:.4f}s\n")
                report_lines.append(f"- Total duration: {total_duration:.4f}s\n")

            if "max_memory" in successful.columns:
                max_mem = successful["max_memory"].max()
                report_lines.append(f"- Max memory usage: {max_mem:.2f}MB\n")

        # Individual results
        report_lines.append("\n## Individual Results\n")

        for _, row in df.iterrows():
            report_lines.append(f"### {row['benchmark']}\n")

            if row["success"]:
                report_lines.append("- Status: [OK] Success\n")
                if "max_memory" in row:
                    report_lines.append(f"- Max Memory: {row['max_memory']:.2f}MB\n")
            else:
                report_lines.append("- Status: [ERROR] Failed\n")
                if "error" in row:
                    report_lines.append(f"- Error: {row['error']}\n")

            report_lines.append("\n")

        # Save report
        report_content = "".join(report_lines)
        report_file = self.output_dir / "benchmark_summary.md"
        with open(report_file, "w") as f:
            f.write(report_content)

        return report_content


# Example usage and decorators
@Profiler().profile_function()
def example_function():
    """Example function to demonstrate profiling."""
    import numpy as np

    result = np.random.rand(1000, 1000)
    return np.mean(result)


@Profiler().profile_method("ExampleClass")
class ExampleClass:
    """Example class to demonstrate method profiling."""

    def method1(self):
        """Example method 1."""
        import numpy as np

        return np.random.rand(100, 100)

    def method2(self):
        """Example method 2."""
        import numpy as np

        return np.sum(np.random.rand(1000, 1000))


if __name__ == "__main__":
    # Example usage
    runner = BenchmarkRunner()

    # Define some benchmark functions
    def numpy_benchmark():
        import numpy as np

        return np.linalg.svd(np.random.rand(1000, 1000))

    def pandas_benchmark():
        import numpy as np
        import pandas as pd

        df = pd.DataFrame(np.random.rand(10000, 100))
        return df.describe()

    benchmarks = {
        "numpy_svd": numpy_benchmark,
        "pandas_describe": pandas_benchmark,
        "example_function": example_function,
    }

    # Run benchmark suite
    results = runner.run_benchmark_suite(benchmarks)
    print(results)
