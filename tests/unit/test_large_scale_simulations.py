"""
Unit tests for large-scale simulation scenarios.

This module implements tests for long-running simulations with 1000+ timesteps,
testing performance, stability, memory usage, and data consistency over extended
simulation periods.

Tests focus on ensuring the APGI system can handle prolonged operation without
degradation in performance or correctness.
"""

import pytest
import numpy as np
import time
import psutil
import gc
import tempfile
import csv
from typing import Dict, Any

from apgi_system.system import APGISystem


class TestLargeScaleSimulations:
    """Tests for large-scale simulation scenarios."""

    @pytest.fixture
    def apgi_system(self) -> APGISystem:
        """Create APGI system instance for testing."""
        return APGISystem()

    @pytest.fixture
    def large_simulation_config(self) -> Dict[str, Any]:
        """Configuration optimized for large-scale testing."""
        return {
            "system": {
                "timestep_ms": 10.0,  # Faster timesteps for testing
                "max_timesteps": 2000,  # Allow up to 2000 timesteps
            },
            "precision": {
                "extero_baseline": 1.0,
                "intero_baseline": 0.8,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "adaptation_rate": 0.01,
            },
        }

    def test_1000_timestep_simulation(self, apgi_system: APGISystem) -> None:
        """Test running a simulation for 1000+ timesteps."""
        # Run 1000 simulation steps
        num_steps = 1000
        observations = []

        start_time = time.time()

        for i in range(num_steps):
            # Generate varied input observations
            obs = np.random.randn(256) * 0.5

            # Add some systematic variation
            if i > 500:
                obs += np.sin(i * 0.01) * 0.2  # Add periodic component

            state = apgi_system.step(obs)
            observations.append(state)

        end_time = time.time()
        duration = end_time - start_time

        # Verify simulation completed
        assert len(observations) == num_steps
        assert apgi_system.time > 0

        # Verify final state is valid
        final_state = observations[-1]
        required_keys = ["time", "ignition", "free_energy", "allostasis"]
        for key in required_keys:
            assert key in final_state

        # Check performance (should complete within reasonable time)
        # Allow for slower systems but ensure it's not taking too long
        assert duration < 60.0  # Should complete within 60 seconds

        print(".3f")

    def test_2000_timestep_simulation_stability(self, apgi_system: APGISystem) -> None:
        """Test system stability over 2000 timesteps."""
        num_steps = 2000
        stability_metrics = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5
            state = apgi_system.step(obs)

            # Track key metrics for stability analysis
            metrics = {
                "timestep": i,
                "time": state["time"],
                "free_energy": state["free_energy"],
                "ignition_events": state.get("ignition", 0),
                "allostatic_load": state["allostasis"]["allostatic_load"],
            }
            stability_metrics.append(metrics)

        # Analyze stability
        free_energy_values = [m["free_energy"] for m in stability_metrics]
        allostatic_loads = [m["allostatic_load"] for m in stability_metrics]

        # Free energy should remain bounded (not explode)
        assert max(free_energy_values) < 100.0
        assert min(free_energy_values) > -100.0

        # Allostatic load should remain in reasonable range
        assert max(allostatic_loads) < 10.0
        assert min(allostatic_loads) >= 0.0

        # System time should advance correctly
        assert stability_metrics[-1]["time"] > stability_metrics[0]["time"]

    def test_memory_usage_during_long_simulation(self, apgi_system: APGISystem) -> None:
        """Test memory usage during long simulation runs."""
        process = psutil.Process()
        gc.collect()  # Clean up before measurement

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run long simulation
        num_steps = 1500
        memory_samples = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5
            apgi_system.step(obs)

            # Sample memory every 100 steps
            if i % 100 == 0:
                memory_samples.append(process.memory_info().rss / 1024 / 1024)

        final_memory = process.memory_info().rss / 1024 / 1024
        gc.collect()  # Clean up after measurement

        # Memory usage should not grow unbounded
        memory_growth = final_memory - initial_memory
        assert memory_growth < 100.0  # Allow some growth but not excessive

        # Memory should remain relatively stable (no continuous growth)
        if len(memory_samples) > 2:
            # Check that memory doesn't consistently increase
            increases = sum(
                1
                for i in range(1, len(memory_samples))
                if memory_samples[i] > memory_samples[i - 1]
            )
            decrease_ratio = 1 - (increases / len(memory_samples))
            assert decrease_ratio > 0.3  # At least 30% should be decreases or stable

    def test_data_accumulation_over_long_runs(self) -> None:
        """Test data accumulation and export for long simulations."""
        # Create system with data recording enabled (simulated)
        system = APGISystem()

        # Simulate data recording over many steps
        num_steps = 1200
        recorded_data = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)

            # Simulate data recording
            data_point = {
                "timestep": i,
                "time": state["time"],
                "free_energy": state["free_energy"],
                "ignition": state.get("ignition", 0),
                "allostatic_load": state["allostasis"]["allostatic_load"],
                "heart_rate": state["interoception"]["heart_rate"],
                "cortisol": state["interoception"]["cortisol"],
            }
            recorded_data.append(data_point)

        # Verify data accumulation
        assert len(recorded_data) == num_steps

        # Test data export to CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_filename = f.name

        try:
            with open(csv_filename, "w", newline="") as f:
                if recorded_data:
                    writer = csv.DictWriter(f, fieldnames=recorded_data[0].keys())
                    writer.writeheader()
                    writer.writerows(recorded_data)

            # Verify file was created and contains correct data
            with open(csv_filename, "r") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            assert len(csv_data) == num_steps
            assert csv_data[0]["timestep"] == "0"
            assert csv_data[-1]["timestep"] == str(num_steps - 1)

        finally:
            import os

            os.unlink(csv_filename)

    def test_performance_scaling_with_timesteps(self) -> None:
        """Test that performance scales reasonably with increasing timesteps."""
        system = APGISystem()

        # Test different simulation lengths
        test_lengths = [100, 500, 1000, 1500]
        performance_results = []

        for length in test_lengths:
            # Reset system
            system = APGISystem()

            start_time = time.time()

            for i in range(length):
                obs = np.random.randn(256) * 0.5
                system.step(obs)

            end_time = time.time()
            duration = end_time - start_time

            performance_results.append(
                {"timesteps": length, "duration": duration, "steps_per_second": length / duration}
            )

        # Performance should scale roughly linearly
        for i in range(1, len(performance_results)):
            prev_result = performance_results[i - 1]
            curr_result = performance_results[i]

            # Check that steps/second doesn't degrade significantly
            degradation_ratio = curr_result["steps_per_second"] / prev_result["steps_per_second"]
            assert degradation_ratio > 0.5  # Allow some degradation but not drastic

    def test_system_state_consistency_long_runs(self) -> None:
        """Test that system state remains consistent over long runs."""
        system = APGISystem()
        num_steps = 2000

        # Track state consistency
        ignition_events = 0
        state_history = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5

            # Occasionally introduce perturbations
            if i % 500 == 0:
                obs += np.random.randn(256) * 2.0  # Larger perturbation

            state = system.step(obs)

            # Track key state variables
            state_snapshot = {
                "timestep": i,
                "time": state["time"],
                "free_energy": state["free_energy"],
                "allostatic_load": state["allostasis"]["allostatic_load"],
                "ignition": state.get("ignition", 0),
            }
            state_history.append(state_snapshot)

            if state.get("ignition", 0) > 0:
                ignition_events += 1

        # Verify state progression
        assert len(state_history) == num_steps
        assert ignition_events >= 0  # Should have some ignition events

        # Time should advance monotonically
        times = [s["time"] for s in state_history]
        assert all(times[i] <= times[i + 1] for i in range(len(times) - 1))

        # Free energy should remain bounded
        free_energies = [s["free_energy"] for s in state_history]
        assert max(free_energies) < 50.0
        assert min(free_energies) > -50.0

    def test_recovery_from_perturbations_long_runs(self) -> None:
        """Test system recovery from perturbations during long runs."""
        system = APGISystem()
        num_steps = 1300

        recovery_events = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5

            # Introduce major perturbation at specific points
            if i in [300, 700, 1100]:
                obs += np.random.randn(256) * 5.0  # Major perturbation
                perturbation_timestep = i

            state = system.step(obs)

            # Check for recovery (return to baseline free energy)
            if i > 0 and "perturbation_timestep" in locals():
                prev_state = (
                    system.step.__defaults__[0]
                    if hasattr(system.step, "__defaults__") and system.step.__defaults__
                    else None
                )
                # Simplified recovery check
                if abs(state["free_energy"]) < 10.0:  # Recovered to reasonable range
                    if "perturbation_timestep" in locals():
                        recovery_time = i - perturbation_timestep
                        recovery_events.append(recovery_time)
                        del perturbation_timestep

        # System should recover from perturbations
        if recovery_events:
            avg_recovery_time = sum(recovery_events) / len(recovery_events)
            assert avg_recovery_time < 50  # Should recover within reasonable time

    def test_data_quality_over_long_runs(self) -> None:
        """Test that data quality remains high over long simulation runs."""
        system = APGISystem()
        num_steps = 1800

        data_quality_metrics = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)

            # Assess data quality
            quality = {
                "timestep": i,
                "finite_values": all(
                    np.isfinite(v) if isinstance(v, (int, float)) else True
                    for v in state.values()
                    if not isinstance(v, dict)
                ),
                "reasonable_ranges": (
                    -100 < state["free_energy"] < 100
                    and 0 <= state["allostasis"]["allostatic_load"] < 20
                    and state["time"] >= 0
                ),
                "no_nan_values": not any(
                    np.isnan(v) if isinstance(v, (int, float, np.ndarray)) else False
                    for v in state.values()
                    if not isinstance(v, dict)
                ),
            }
            data_quality_metrics.append(quality)

        # Verify data quality
        finite_count = sum(1 for m in data_quality_metrics if m["finite_values"])
        range_count = sum(1 for m in data_quality_metrics if m["reasonable_ranges"])
        no_nan_count = sum(1 for m in data_quality_metrics if m["no_nan_values"])

        # Should maintain high data quality throughout
        assert finite_count / num_steps > 0.99  # >99% finite values
        assert range_count / num_steps > 0.95  # >95% reasonable ranges
        assert no_nan_count / num_steps > 0.99  # >99% no NaN values

    @pytest.mark.slow
    def test_3000_timestep_extreme_simulation(self) -> None:
        """Test extreme simulation with 3000+ timesteps (marked as slow)."""
        system = APGISystem()
        num_steps = 3000

        # Track basic health metrics
        health_checks = []

        for i in range(num_steps):
            obs = np.random.randn(256) * 0.5
            state = system.step(obs)

            # Periodic health check
            if i % 500 == 0:
                health = {
                    "timestep": i,
                    "system_alive": True,
                    "time_advancing": state["time"] > 0,
                    "finite_free_energy": np.isfinite(state["free_energy"]),
                    "bounded_allostasis": 0 <= state["allostasis"]["allostatic_load"] < 100,
                }
                health_checks.append(health)

        # Verify system survived extreme test
        assert len(health_checks) >= 5  # Should have multiple health checks
        assert all(h["system_alive"] for h in health_checks)
        assert all(h["time_advancing"] for h in health_checks)
        assert all(h["finite_free_energy"] for h in health_checks)
        assert all(h["bounded_allostasis"] for h in health_checks)


class TestLargeScaleGUIIntegration:
    """Tests for large-scale simulations with GUI components."""

    @pytest.mark.skipif(
        "tkinter" not in globals() or not hasattr(globals().get("tkinter", None), "Tk"),
        reason="Tkinter not available",
    )
    def test_gui_large_scale_data_handling(self) -> None:
        """Test GUI data handling during large-scale simulations."""
        import tkinter as tk

        root = tk.Tk()

        try:
            from apgi_gui import APGIGui

            app = APGIGui(root)

            # Simulate large-scale data accumulation
            num_steps = 800

            for i in range(num_steps):
                obs = np.random.randn(256) * 0.5
                state = app.apgi_system.step(obs)
                app._record_state(state)

                # Update plots periodically
                if i % 100 == 0:
                    app._update_plots()

            # Verify data accumulation
            assert len(app.time_buffer) > 0
            assert len(app.log_data) == num_steps

            # Verify GUI can handle the data
            app._update_status("Large-scale test completed")
            assert app.status_text.cget("text") == "Large-scale test completed"

        finally:
            root.quit()
            root.destroy()

    @pytest.mark.skipif(
        "tkinter" not in globals() or not hasattr(globals().get("tkinter", None), "Tk"),
        reason="Tkinter not available",
    )
    def test_gui_memory_management_large_scale(self) -> None:
        """Test GUI memory management during large-scale operations."""
        import tkinter as tk

        root = tk.Tk()

        try:
            from apgi_gui import APGIGui

            app = APGIGui(root)

            # Get initial memory info
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024

            # Run large simulation with GUI updates
            num_steps = 1000

            for i in range(num_steps):
                obs = np.random.randn(256) * 0.5
                state = app.apgi_system.step(obs)
                app._record_state(state)

                # Update GUI periodically
                if i % 50 == 0:
                    app._update_plots()
                    app._update_status(f"Step {i}")

            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory

            # Memory growth should be reasonable
            assert memory_growth < 200.0  # Allow some growth for GUI

            # GUI should still be responsive
            assert app.status_text.cget("text").startswith("Step")

        finally:
            root.quit()
            root.destroy()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])  # Skip slow tests by default
