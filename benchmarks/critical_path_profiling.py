"""
cProfile benchmarks for critical performance paths in APGI Framework
Provides detailed profiling of key functions and methods.
"""

import cProfile
import io
import json
import pstats
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class CriticalPathProfiler:
    """Profile critical performance paths in the APGI Framework."""

    def __init__(self, output_dir: str = "benchmark_results"):
        """
        Initialize the critical path profiler.

        Args:
            output_dir: Directory to save profiling results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.profiles: Dict[str, Any] = {}
        self.baseline_profiles: Dict[str, Any] = {}

    def profile_critical_function(
        self,
        name: str,
        func: Callable,
        *args,
        iterations: int = 100,
        warmup_iterations: int = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Profile a critical function with multiple iterations.

        Args:
            name: Name of the function for identification
            func: Function to profile
            iterations: Number of profiling iterations
            warmup_iterations: Number of warmup iterations
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Dictionary with profiling results
        """
        print(f"Profiling critical function: {name}")

        # Warmup
        for _ in range(warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # Ignore warmup errors

        # Profile multiple iterations
        profiles = []
        times = []

        for i in range(iterations):
            pr = cProfile.Profile()

            # Time the execution
            start_time = time.perf_counter()
            pr.enable()

            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)

            pr.disable()
            end_time = time.perf_counter()

            execution_time = end_time - start_time
            times.append(execution_time)

            # Store profile
            profile_data = {
                "profile": pr,
                "result": result,
                "success": success,
                "error": error,
                "execution_time": execution_time,
                "iteration": i,
            }
            profiles.append(profile_data)

        # Analyze results
        analysis = self._analyze_profiles(name, profiles, times)

        # Save detailed profile
        self._save_profile_details(name, profiles[-1]["profile"])

        return analysis

    def _analyze_profiles(
        self, name: str, profiles: List[Dict], times: List[float]
    ) -> Dict[str, Any]:
        """Analyze profiling results."""
        successful_profiles = [p for p in profiles if p["success"]]

        if not successful_profiles:
            return {
                "name": name,
                "success_rate": 0.0,
                "error": "All iterations failed",
                "iterations": len(profiles),
            }

        # Time statistics
        time_stats = {
            "mean": np.mean(times),
            "std": np.std(times),
            "min": np.min(times),
            "max": np.max(times),
            "median": np.median(times),
            "p95": np.percentile(times, 95),
            "p99": np.percentile(times, 99),
        }

        # Profile statistics from the last successful run
        last_profile = successful_profiles[-1]["profile"]
        stats = pstats.Stats(last_profile, stream=io.StringIO())

        # Get top functions by cumulative time
        stats.sort_stats("cumulative")
        top_functions = []

        for func_info in stats.stats.items():  # type: ignore
            func_name, filename, line = func_info[0]
            (
                call_count,
                total_time,
                cumulative_time,
                per_call_time,
            ) = func_info[1]

            top_functions.append(
                {
                    "function": f"{func_name}:{line}",
                    "filename": filename,
                    "call_count": call_count,
                    "total_time": total_time,
                    "cumulative_time": cumulative_time,
                    "per_call_time": per_call_time,
                }
            )

        # Sort by cumulative time
        top_functions.sort(key=lambda x: x["cumulative_time"], reverse=True)

        analysis = {
            "name": name,
            "success_rate": len(successful_profiles) / len(profiles),
            "iterations": len(profiles),
            "time_stats": time_stats,
            "top_functions": top_functions[:20],  # Top 20 functions
            "total_calls": sum(f["call_count"] for f in top_functions),
            "total_time": sum(f["cumulative_time"] for f in top_functions),
        }

        self.profiles[name] = analysis
        return analysis

    def _save_profile_details(self, name: str, profile: cProfile.Profile):
        """Save detailed profile information."""
        # Save binary profile
        profile_file = self.output_dir / f"{name}_profile.prof"
        profile.dump_stats(str(profile_file))

        # Save human-readable stats
        text_file = self.output_dir / f"{name}_profile.txt"
        with open(text_file, "w") as f:
            stats = pstats.Stats(profile, stream=f)
            stats.sort_stats("cumulative")
            stats.print_stats(50)  # Top 50 functions

    def profile_critical_paths(self) -> Dict[str, Dict[str, Any]]:
        """Profile all critical paths in the APGI Framework."""
        results = {}

        # Define critical paths to profile
        critical_paths = self._get_critical_paths()

        for path_name, path_config in critical_paths.items():
            try:
                func = path_config["func"]
                args = path_config.get("args", [])
                iterations = path_config.get("iterations", 50)
                kwargs = path_config.get("kwargs", {})

                result = self.profile_critical_function(  # type: ignore
                    name=path_name,
                    func=func,
                    *args,
                    iterations=iterations,
                    **kwargs,
                )
                results[path_name] = result
            except Exception as e:
                print(f"Failed to profile {path_name}: {e}")
                results[path_name] = {
                    "name": path_name,
                    "error": str(e),
                    "success_rate": 0.0,
                }

        # Save comprehensive report
        self._save_comprehensive_report(results)

        return results

    def _get_critical_paths(self) -> Dict[str, Dict[str, Any]]:
        """Define critical paths to profile."""
        critical_paths = {}

        # Data loading operations
        critical_paths["load_eeg_data"] = {
            "func": self._simulate_eeg_loading,
            "iterations": 30,
            "args": [10000, 8],  # samples, channels
            "kwargs": {},
        }

        # Data processing operations
        critical_paths["process_eeg_data"] = {
            "func": self._simulate_eeg_processing,
            "iterations": 20,
            "args": [10000, 8],
            "kwargs": {},
        }

        # Mathematical operations
        critical_paths["matrix_operations"] = {
            "func": self._simulate_matrix_operations,
            "iterations": 50,
            "args": [1000],  # matrix size
            "kwargs": {},
        }

        # File I/O operations
        critical_paths["file_io"] = {
            "func": self._simulate_file_io,
            "iterations": 25,
            "args": [1000],  # data size
            "kwargs": {},
        }

        # Data analysis operations
        critical_paths["data_analysis"] = {
            "func": self._simulate_data_analysis,
            "iterations": 30,
            "args": [5000, 10],  # samples, features
            "kwargs": {},
        }

        # Visualization operations
        critical_paths["visualization"] = {
            "func": self._simulate_visualization,
            "iterations": 15,
            "args": [1000, 8],  # samples, channels
            "kwargs": {},
        }

        # Machine learning operations
        critical_paths["ml_training"] = {
            "func": self._simulate_ml_training,
            "iterations": 10,
            "args": [1000, 50],  # samples, features
            "kwargs": {},
        }

        return critical_paths

    def _simulate_eeg_loading(self, samples: int, channels: int) -> np.ndarray:
        """Simulate EEG data loading."""
        # Simulate file reading and data parsing
        data = np.random.randn(samples, channels)

        # Simulate some processing during loading
        filtered_data = self._apply_filters(data)
        normalized_data = self._normalize_data(filtered_data)

        return normalized_data

    def _simulate_eeg_processing(
        self,
        samples: int,
        channels: int,
    ) -> Dict[str, Any]:
        """Simulate EEG data processing."""
        data = np.random.randn(samples, channels)

        # Feature extraction
        features = {}
        features["mean_power"] = np.mean(data**2, axis=0)
        features["peak_frequency"] = np.random.rand(channels) * 50
        features["variance"] = np.var(data, axis=0)
        features["correlation_matrix"] = np.corrcoef(data.T)

        # Time-frequency analysis (simplified)
        freq_bands = ["delta", "theta", "alpha", "beta", "gamma"]
        for band in freq_bands:
            features[f"{band}_power"] = np.random.rand(channels)

        return features

    def _simulate_matrix_operations(self, size: int) -> np.ndarray:
        """Simulate intensive matrix operations."""
        # Create matrices
        A = np.random.randn(size, size)
        B = np.random.randn(size, size)

        # Matrix multiplication
        C = np.dot(A, B)

        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(
            C + np.eye(size) * 0.01
        )  # Add small identity for stability

        # SVD
        U, S, V = np.linalg.svd(A)

        return eigenvalues

    def _simulate_file_io(self, data_size: int) -> str:
        """Simulate file I/O operations."""
        # Create test data
        data = np.random.randn(data_size, 5)
        df = pd.DataFrame(data, columns=["A", "B", "C", "D", "E"])

        # Write to temporary file
        temp_file = self.output_dir / "temp_test_data.csv"
        df.to_csv(temp_file, index=False)

        # Read back
        df_read = pd.read_csv(temp_file)

        # Clean up
        temp_file.unlink()

        return str(len(df_read))

    def _simulate_data_analysis(self, samples: int, features: int) -> Dict[str, Any]:
        """Simulate data analysis operations."""
        # Generate data
        data = np.random.randn(samples, features)
        labels = np.random.randint(0, 2, samples)

        # Statistical analysis
        results = {}

        # Basic statistics
        results["means"] = np.mean(data, axis=0)
        results["stds"] = np.std(data, axis=0)
        results["correlations"] = np.corrcoef(data.T)

        # Group analysis
        group1_data = data[labels == 0]
        group2_data = data[labels == 1]

        results["group1_means"] = np.mean(group1_data, axis=0)
        results["group2_means"] = np.mean(group2_data, axis=0)

        # T-tests (simplified)
        from scipy import stats

        t_stats = []
        p_values = []

        for i in range(features):
            t, p = stats.ttest_ind(group1_data[:, i], group2_data[:, i])
            t_stats.append(t)
            p_values.append(p)

        results["t_statistics"] = t_stats
        results["p_values"] = p_values

        return results

    def _simulate_visualization(self, samples: int, channels: int) -> str:
        """Simulate visualization operations."""
        # Generate data
        times = np.linspace(0, 10, samples)
        data = np.random.randn(samples, channels)

        # Create plot
        fig, axes = plt.subplots(channels, 1, figsize=(12, 2 * channels))
        if channels == 1:
            axes = [axes]

        for i, ax in enumerate(axes):
            ax.plot(times, data[:, i])
            ax.set_title(f"Channel {i + 1}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")

        plt.tight_layout()

        # Save plot
        plot_file = self.output_dir / "test_visualization.png"
        plt.savefig(plot_file, dpi=150, bbox_inches="tight")
        plt.close()

        # Clean up
        plot_file.unlink()

        return f"Generated plot with {channels} channels"

    def _simulate_ml_training(self, samples: int, features: int) -> Dict[str, float]:
        """Simulate machine learning training."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import cross_val_score

        # Generate data
        X = np.random.randn(samples, features)
        y = np.random.randint(0, 2, samples)

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)

        # Cross-validation
        scores = cross_val_score(model, X, y, cv=5)

        # Fit final model
        model.fit(X, y)

        return {
            "mean_score": np.mean(scores),
            "std_score": np.std(scores),
            "feature_importance_mean": np.mean(model.feature_importances_),
        }

    def _apply_filters(self, data: np.ndarray) -> np.ndarray:
        """Apply filters to data (simplified)."""
        # Simulate bandpass filter
        from scipy import signal

        b, a = signal.butter(4, [0.1, 40], btype="bandpass", fs=1000)
        filtered: np.ndarray = signal.filtfilt(b, a, data, axis=0)
        return filtered

    def _normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data (z-score)."""
        mean: np.ndarray = np.mean(data, axis=0)
        std: np.ndarray = np.std(data, axis=0)
        result: np.ndarray = (data - mean) / (std + 1e-8)
        return result

    def _save_comprehensive_report(self, results: Dict[str, Dict[str, Any]]):
        """Save comprehensive profiling report."""
        # Create summary data
        summary_data = []

        for name, result in results.items():
            if "time_stats" in result:
                summary_data.append(
                    {
                        "function": name,
                        "success_rate": result["success_rate"],
                        "mean_time": result["time_stats"]["mean"],
                        "std_time": result["time_stats"]["std"],
                        "min_time": result["time_stats"]["min"],
                        "max_time": result["time_stats"]["max"],
                        "p95_time": result["time_stats"]["p95"],
                        "total_calls": result.get("total_calls", 0),
                        "total_time": result.get("total_time", 0),
                    }
                )
            else:
                summary_data.append(
                    {
                        "function": name,
                        "success_rate": result["success_rate"],
                        "error": result.get("error", "Unknown error"),
                    }
                )

        # Save summary CSV
        summary_df = pd.DataFrame(summary_data)
        summary_file = self.output_dir / "critical_paths_summary.csv"
        summary_df.to_csv(summary_file, index=False)

        # Create visualizations
        self._create_performance_visualizations(summary_df)

        # Save detailed JSON report
        json_file = self.output_dir / "critical_paths_detailed.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Create markdown report
        self._create_markdown_report(results, summary_df)

    def _create_performance_visualizations(self, summary_df: pd.DataFrame):
        """Create performance visualization plots."""
        # Filter successful results
        successful = summary_df[summary_df["success_rate"] > 0]

        if len(successful) == 0:
            return

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Execution time comparison
        ax1 = axes[0, 0]
        successful.plot(x="function", y="mean_time", kind="bar", ax=ax1, color="skyblue")
        ax1.set_title("Mean Execution Time by Function")
        ax1.set_ylabel("Time (seconds)")
        ax1.tick_params(axis="x", rotation=45)

        # Time variability
        ax2 = axes[0, 1]
        ax2.errorbar(
            successful["function"],
            successful["mean_time"],
            yerr=successful["std_time"],
            fmt="o",
            capsize=5,
            capthick=2,
        )
        ax2.set_title("Execution Time Variability")
        ax2.set_ylabel("Time (seconds)")
        ax2.tick_params(axis="x", rotation=45)

        # Success rate
        ax3 = axes[1, 0]
        summary_df.plot(x="function", y="success_rate", kind="bar", ax=ax3, color="lightgreen")
        ax3.set_title("Success Rate by Function")
        ax3.set_ylabel("Success Rate")
        ax3.tick_params(axis="x", rotation=45)

        # Total time vs calls
        ax4 = axes[1, 1]
        scatter = ax4.scatter(
            successful["total_calls"],
            successful["total_time"],
            s=100,
            alpha=0.6,
            c=successful["mean_time"],
            cmap="viridis",
        )
        ax4.set_xlabel("Total Function Calls")
        ax4.set_ylabel("Total Time (seconds)")
        ax4.set_title("Total Calls vs Total Time")
        plt.colorbar(scatter, ax=ax4, label="Mean Time (s)")

        plt.tight_layout()

        # Save plot
        plot_file = self.output_dir / "critical_paths_performance.png"
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()

    def _create_markdown_report(self, results: Dict[str, Dict[str, Any]], summary_df: pd.DataFrame):
        """Create markdown report."""
        report_lines = ["# Critical Paths Performance Report\n"]
        report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary table
        report_lines.append("## Performance Summary\n")
        report_lines.append(
            "| Function | Success Rate | Mean Time (s) | Std Time (s) | "
            "P95 Time (s) | Total Calls |\n"
        )
        report_lines.append(
            "|----------|--------------|---------------|--------------|"
            "---------------|-------------|\n"
        )

        for _, row in summary_df.iterrows():
            if pd.notna(row.get("mean_time")):
                report_lines.append(
                    f"| {row['function']} | {row['success_rate']:.2%} | "
                    f"{row['mean_time']:.4f} | {row['std_time']:.4f} | "
                    f"{row.get('p95_time', 'N/A')} | "
                    f"{row.get('total_calls', 'N/A')} |\n"
                )
            else:
                report_lines.append(
                    f"| {row['function']} | {row['success_rate']:.2%} | " f"FAILED | - | - | - |\n"
                )

        # Detailed analysis
        report_lines.append("\n## Detailed Analysis\n")

        for name, result in results.items():
            report_lines.append(f"### {name}\n")

            if result["success_rate"] == 0:
                report_lines.append("**Status:** FAILED\n")
                report_lines.append(f"**Error:** {result.get('error', 'Unknown error')}\n\n")
                continue

            report_lines.append(f"**Success Rate:** {result['success_rate']:.2%}\n")

            if "time_stats" in result:
                ts = result["time_stats"]
                report_lines.append(f"**Mean Time:** {ts['mean']:.4f}s\n")
                report_lines.append(f"**Std Dev:** {ts['std']:.4f}s\n")
                report_lines.append(f"**Min Time:** {ts['min']:.4f}s\n")
                report_lines.append(f"**Max Time:** {ts['max']:.4f}s\n")
                report_lines.append(f"**P95 Time:** {ts['p95']:.4f}s\n")

            if "top_functions" in result and result["top_functions"]:
                report_lines.append("\n**Top Functions by Cumulative Time:**\n")
                report_lines.append("| Function | Calls | Total Time (s) | Per Call (s) |\n")
                report_lines.append("|----------|-------|----------------|--------------|\n")

                for func in result["top_functions"][:10]:
                    report_lines.append(
                        f"| {func['function'][:50]} | {func['call_count']} | "
                        f"{func['cumulative_time']:.4f} | "
                        f"{func['per_call_time']:.6f} |\n"
                    )

            report_lines.append("\n")

        # Save report
        report_content = "".join(report_lines)
        report_file = self.output_dir / "critical_paths_report.md"
        with open(report_file, "w") as f:
            f.write(report_content)


def run_critical_path_profiling():
    """Run critical path profiling and generate report."""
    profiler = CriticalPathProfiler()

    print("Starting critical path profiling...")
    results = profiler.profile_critical_paths()

    print(f"Profiling completed. Results saved to {profiler.output_dir}")

    # Print summary
    print("\n=== PROFILING SUMMARY ===")
    for name, result in results.items():
        if result["success_rate"] > 0 and "time_stats" in result:
            print(
                f"{name}: {result['time_stats']['mean']:.4f}s ± "
                f"{result['time_stats']['std']:.4f}s "
                f"({result['success_rate']:.1%} success)"
            )
        else:
            print(f"{name}: FAILED ({result.get('error', 'Unknown error')})")

    return results


if __name__ == "__main__":
    # Run profiling when called directly
    run_critical_path_profiling()
