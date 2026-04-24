"""
Performance benchmarks for APGI Framework
Tests critical performance paths and identifies regressions.
"""

import pytest

try:
    import pytest_benchmark  # type: ignore  # noqa: F401

    HAS_BENCHMARK = True
except ImportError:
    HAS_BENCHMARK = False

if not HAS_BENCHMARK:
    pytest.skip("pytest-benchmark not available", allow_module_level=True)

import cProfile
import io
import pstats
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Declare variables as Any to avoid type conflicts
APGIAgent: Any = None
AnalysisEngine: Any = None
ExperimentData: Any = None
StimulusGenerator: Any = None

try:
    from apgi_framework.adaptive.stimulus_generators import (
        GaborPatchGenerator as ImportedStimulusGenerator,
    )
    from apgi_framework.analysis.analysis_engine import (
        AnalysisEngine as ImportedAnalysisEngine,
    )
    from apgi_framework.core.data_models import ExperimentalTrial
    from apgi_framework.core.models import APGIModel  # type: ignore[import-not-found]

    # Use imported classes
    APGIAgent = APGIModel
    AnalysisEngine = ImportedAnalysisEngine
    ExperimentData = ExperimentalTrial
    StimulusGenerator = ImportedStimulusGenerator
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Warning: Could not import APGI modules: {e}")

    IMPORTS_SUCCESSFUL = False

# Define mock classes if imports failed
if not IMPORTS_SUCCESSFUL:

    class FallbackAPGIAgent:
        def __init__(self):
            self.state = np.random.rand(100)

        def update(self, observation):
            return np.random.rand(10)

        def decide(self, beliefs, context, surprise):
            return 0, False, np.array([1.0, 2.0, 3.0])

    class FallbackAnalysisEngine:
        def __init__(self):
            pass

        def analyze_data(self, data):
            return {"result": np.random.rand(100)}

    class FallbackExperimentData:
        def __init__(self, data):
            self.data = data

    class FallbackStimulusGenerator:
        def __init__(self):
            pass

        def generate_stimulus(self, params):
            return np.random.rand(1000)

        def initialize(self):
            return True

        def cleanup(self):
            pass

    APGIAgent = FallbackAPGIAgent
    AnalysisEngine = FallbackAnalysisEngine
    ExperimentData = FallbackExperimentData
    StimulusGenerator = FallbackStimulusGenerator


class BenchmarkTimer:
    """Context manager for timing operations."""

    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        print(f"{self.name}: {duration:.4f} seconds")


def profile_function(func, *args, **kwargs):
    """Profile a function and return stats."""
    pr = cProfile.Profile()
    pr.enable()

    result = func(*args, **kwargs)

    pr.disable()

    # Create string buffer to capture stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(10)  # Top 10 functions

    return result, s.getvalue()


@pytest.mark.benchmark
class TestAPGIAgentPerformance:
    """Benchmark APGI Agent performance."""

    def setup_method(self):
        """Set up test data."""
        self.agent = APGIAgent()
        self.n_iterations = 1000
        self.observation_size = 50

        # Generate test observations
        self.observations = [
            np.random.rand(self.observation_size) for _ in range(self.n_iterations)
        ]
        self.beliefs = np.random.rand(4)  # SomaticAgent expects beliefs
        self.context = 0  # Default context

    def test_agent_update_performance(self, benchmark):
        """Benchmark agent update performance."""

        def agent_updates():
            for obs in self.observations:
                # SomaticAgent uses decide() method, not update()
                self.agent.decide(self.beliefs, self.context, 1.0)

        result = benchmark(agent_updates)
        assert result is None

    def test_agent_update_with_profiling(self):
        """Profile agent updates to identify bottlenecks."""

        def single_update():
            return self.agent.decide(self.beliefs, self.context, 1.0)

        result, profile_stats = profile_function(single_update)

        # Save profile stats for analysis
        profile_dir = Path("benchmark_results")
        profile_dir.mkdir(exist_ok=True)

        with open(profile_dir / "agent_update_profile.txt", "w") as f:
            f.write(profile_stats)

        assert result is not None

    def test_agent_memory_usage(self):
        """Test agent memory usage over time."""
        import tracemalloc

        tracemalloc.start()

        # Take initial memory snapshot
        snapshot1 = tracemalloc.take_snapshot()

        # Run many updates
        for obs in self.observations:
            self.agent.decide(self.beliefs, self.context, 1.0)

        # Take final memory snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, "lineno")

        # Save memory stats
        profile_dir = Path("benchmark_results")
        profile_dir.mkdir(exist_ok=True)

        with open(profile_dir / "agent_memory_stats.txt", "w") as f:
            for stat in top_stats[:10]:
                f.write(f"{stat}\n")

        tracemalloc.stop()

        # Check that memory growth is reasonable (less than 10MB)
        total_memory = sum(stat.size_diff for stat in top_stats)
        assert total_memory < 10 * 1024 * 1024  # 10MB


@pytest.mark.benchmark
class TestAnalysisEnginePerformance:
    """Benchmark Analysis Engine performance."""

    def setup_method(self):
        """Set up test data."""
        self.engine = AnalysisEngine()

        # Generate test datasets of different sizes
        self.small_data = np.random.rand(1000, 10)
        self.medium_data = np.random.rand(10000, 10)
        self.large_data = np.random.rand(100000, 10)

        self.experiment_data_small = ExperimentData(self.small_data)
        self.experiment_data_medium = ExperimentData(self.medium_data)
        self.experiment_data_large = ExperimentData(self.large_data)

    def test_small_data_analysis(self, benchmark):
        """Benchmark analysis of small dataset."""
        # Convert numpy array to DataFrame for AnalysisEngine
        df = pd.DataFrame(self.small_data)
        result = benchmark(self.engine.analyze, df, "descriptive", generate_plots=False)
        assert result is not None

    def test_medium_data_analysis(self, benchmark):
        """Benchmark analysis of medium dataset."""
        df = pd.DataFrame(self.medium_data)
        result = benchmark(self.engine.analyze, df, "descriptive", generate_plots=False)
        assert result is not None

    def test_large_data_analysis(self, benchmark):
        """Benchmark analysis of large dataset."""
        df = pd.DataFrame(self.large_data)
        result = benchmark(self.engine.analyze, df, "descriptive", generate_plots=False)
        assert result is not None

    def test_analysis_scaling(self):
        """Test how analysis performance scales with data size."""
        sizes = [1000, 5000, 10000, 50000]
        times = []

        for size in sizes:
            data = np.random.rand(size, 10)

            with BenchmarkTimer(f"Analysis size {size}") as timer:
                df = pd.DataFrame(data)
                _ = self.engine.analyze(df, "descriptive", generate_plots=False)

            times.append(timer.end_time - timer.start_time)

        # Check that performance scales reasonably (should be roughly linear)
        # Time for 5x data should be less than 10x time
        if len(times) >= 2:
            scaling_factor = times[-1] / times[0]
            data_factor = sizes[-1] / sizes[0]

            # Allow for some overhead but should be roughly linear
            assert (
                scaling_factor < data_factor * 2
            ), f"Poor scaling: {scaling_factor}x time for {data_factor}x data"

        # Save scaling results
        profile_dir = Path("benchmark_results")
        profile_dir.mkdir(exist_ok=True)

        scaling_data = pd.DataFrame({"size": sizes, "time": times})
        scaling_data.to_csv(profile_dir / "analysis_scaling.csv", index=False)


@pytest.mark.benchmark
class TestStimulusGeneratorPerformance:
    """Benchmark Stimulus Generator performance."""

    def setup_method(self):
        """Set up test data."""
        self.generator = StimulusGenerator()
        self.generator.initialize()
        self.n_stimuli = 1000

        # Different parameter configurations - use GaborParameters
        from apgi_framework.adaptive.stimulus_generators import (
            GaborParameters,
        )

        self.simple_params = GaborParameters(
            intensity=0.5,
            duration_ms=500.0,
            contrast=0.5,
            spatial_frequency=2.0,
        )
        self.complex_params = GaborParameters(
            intensity=0.7,
            duration_ms=1000.0,
            contrast=0.7,
            spatial_frequency=3.0,
            orientation=45.0,
            phase=0.5,
        )

    def test_simple_stimulus_generation(self, benchmark):
        """Benchmark simple stimulus generation."""

        def generate_simple():
            return [
                self.generator.generate_stimulus(self.simple_params) for _ in range(self.n_stimuli)
            ]

        result = benchmark(generate_simple)
        assert len(result) == self.n_stimuli

    def test_complex_stimulus_generation(self, benchmark):
        """Benchmark complex stimulus generation."""

        def generate_complex():
            return [
                self.generator.generate_stimulus(self.complex_params) for _ in range(self.n_stimuli)
            ]

        result = benchmark(generate_complex)
        assert len(result) == self.n_stimuli

    def test_stimulus_generation_throughput(self):
        """Test stimulus generation throughput (stimuli per second)."""
        n_test = 10000

        start_time = time.perf_counter()
        for _ in range(n_test):
            self.generator.generate_stimulus(self.simple_params)
        end_time = time.perf_counter()

        duration = end_time - start_time
        throughput = n_test / duration

        print(f"Stimulus generation throughput: {throughput:.2f} stimuli/second")

        # Should be able to generate at least 100 stimuli per second
        assert throughput > 100, f"Low throughput: {throughput:.2f} stimuli/second"

        # Save throughput results
        profile_dir = Path("benchmark_results")
        profile_dir.mkdir(exist_ok=True)

        with open(profile_dir / "stimulus_throughput.txt", "w") as f:
            f.write(f"Throughput: {throughput:.2f} stimuli/second\n")


@pytest.mark.benchmark
class TestDataProcessingPerformance:
    """Benchmark data processing performance."""

    def setup_method(self):
        """Set up test data."""
        # Simulate different data types
        self.eeg_data = np.random.rand(60000, 8)  # 1 minute of 8-channel EEG at 1kHz
        self.behavioral_data = pd.DataFrame(
            {
                "reaction_time": np.random.normal(300, 50, 1000),
                "accuracy": np.random.choice([0, 1], 1000),
                "condition": np.random.choice(["easy", "hard"], 1000),
            }
        )

    def test_eeg_data_processing(self, benchmark):
        """Benchmark EEG data processing."""

        def process_eeg():
            # Simulate common EEG processing steps
            filtered_data = self._bandpass_filter(self.eeg_data, 1, 40)
            features = self._extract_features(filtered_data)
            return features

        result = benchmark(process_eeg)
        assert result is not None

    def test_behavioral_data_processing(self, benchmark):
        """Benchmark behavioral data processing."""

        def process_behavioral():
            # Simulate common behavioral analysis
            rt_by_condition = self.behavioral_data.groupby("condition")["reaction_time"].mean()
            accuracy_by_condition = self.behavioral_data.groupby("condition")["accuracy"].mean()
            return {"rt": rt_by_condition, "accuracy": accuracy_by_condition}

        result = benchmark(process_behavioral)
        assert result is not None

    def _bandpass_filter(self, data, low_freq, high_freq):
        """Simple bandpass filter simulation."""
        # In real implementation, this would use scipy.signal
        return data * 0.9  # Simple attenuation simulation

    def _extract_features(self, data):
        """Extract features from EEG data."""
        # Simulate feature extraction
        return {
            "mean_power": np.mean(data**2, axis=0),
            "peak_frequency": np.random.rand(data.shape[1]) * 40,
            "variance": np.var(data, axis=0),
        }


@pytest.mark.benchmark
class TestMemoryPerformance:
    """Test memory performance and identify leaks."""

    def test_large_array_allocation(self, benchmark):
        """Test large array allocation performance."""

        def allocate_large_arrays():
            arrays = []
            for i in range(100):
                arr = np.random.rand(10000, 100)  # ~80MB per array
                arrays.append(arr)
                # Simulate some processing
                _ = np.mean(arr)
            return len(arrays)

        result = benchmark(allocate_large_arrays)
        assert result == 100

    def test_memory_cleanup(self):
        """Test that memory is properly cleaned up."""
        import gc
        import tracemalloc

        tracemalloc.start()

        # Allocate memory
        arrays = []
        for i in range(50):
            arr = np.random.rand(10000, 100)
            arrays.append(arr)

        snapshot_before = tracemalloc.take_snapshot()

        # Clear references and force garbage collection
        arrays.clear()
        gc.collect()

        snapshot_after = tracemalloc.take_snapshot()

        # Check memory difference
        stats = snapshot_after.compare_to(snapshot_before, "lineno")
        total_freed = sum(-stat.size_diff for stat in stats if stat.size_diff < 0)

        print(f"Memory freed: {total_freed / (1024 * 1024):.2f} MB")

        # Should free at least 1GB of memory
        assert total_freed > 1024 * 1024 * 1024, "Memory not properly cleaned up"

        tracemalloc.stop()


if __name__ == "__main__":
    # Run benchmarks manually if called directly
    pytest.main([__file__, "-v", "--benchmark-only"])
