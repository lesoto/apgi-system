"""Demonstration of extended analysis capabilities.

This script demonstrates how to use the analysis module to examine
APGI system behavior after a simulation run.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apgi_framework.system import APGISystem  # noqa: E402


def main() -> None:
    """Run a simulation and perform comprehensive analysis."""
    print("=" * 60)
    print("APGI System Analysis Demonstration")
    print("=" * 60)

    # Create and run system
    print("\n1. Initializing APGI system...")
    system = APGISystem()

    print("2. Running simulation (5 seconds)...")
    run_results = system.run(duration_ms=5000.0)

    print(f"   - Total steps: {run_results['total_steps']}")
    print(f"   - Duration: {run_results['duration_ms']:.1f} ms")
    print(f"   - Ignition count: {run_results['ignition_count']}")

    # Perform comprehensive analysis
    print("\n3. Performing comprehensive analysis...")
    from apgi_framework.analysis import SystemAnalyzer

    analyzer = SystemAnalyzer(config={})
    results = analyzer.analyze_system(system)
    # Access the underlying data to avoid mypy issues with dynamic attributes
    results_data = results._data  # type: ignore[attr-defined]

    # Display ignition statistics
    print("\n" + "=" * 60)
    print("IGNITION STATISTICS")
    print("=" * 60)
    ign_stats = results_data.get("ignition_statistics", {})
    print(f"Total ignitions:        {ign_stats.get('total_ignitions', 0)}")
    print(f"Ignition rate:          {ign_stats.get('ignition_rate_hz', 0):.2f} Hz")
    print(f"Mean interval:          {ign_stats.get('mean_ignition_interval_ms', 0):.1f} ms")
    print(f"Std interval:           {ign_stats.get('std_ignition_interval_ms', 0):.1f} ms")
    print(f"Min interval:           {ign_stats.get('min_ignition_interval_ms', 0):.1f} ms")
    print(f"Max interval:           {ign_stats.get('max_ignition_interval_ms', 0):.1f} ms")
    print(f"Mean duration:          {ign_stats.get('mean_ignition_duration_ms', 0):.1f} ms")

    # Display energy budget summary
    print("\n" + "=" * 60)
    print("ENERGY BUDGET SUMMARY")
    print("=" * 60)
    energy = results_data.get("energy_budget_summary", {})
    print(f"Total consumed:         {energy.get('total_energy_consumed', 0):.3f} units")
    print(f"Mean per step:          {energy.get('mean_energy_per_step', 0):.6f} units")
    print(f"Energy per ignition:    {energy.get('energy_per_ignition', 0):.3f} units")
    print(f"Final reserves:         {energy.get('final_reserves', 0):.2f} units")
    print(f"Min reserves:           {energy.get('min_reserves', 0):.2f} units")
    print(f"Depletion rate:         {energy.get('reserve_depletion_rate', 0):.3f} units/s")

    # Display somatic marker statistics
    print("\n" + "=" * 60)
    print("SOMATIC MARKER STATISTICS")
    print("=" * 60)
    markers = results_data.get("somatic_marker_stats", {})
    print(f"Total markers:          {markers.get('total_markers', 0)}")
    print(f"Capacity used:          {markers.get('capacity_used', 0):.1%}")
    print(f"Retrieval success rate: {markers.get('retrieval_success_rate', 0):.1%}")
    print(f"Mean marker strength:   {markers.get('mean_marker_strength', 0):.3f}")
    print(f"Mean marker outcome:    {markers.get('mean_marker_outcome', 0):.3f}")
    print(f"Learning events:        {markers.get('learning_events', 0)}")

    # Display coherence metrics
    print("\n" + "=" * 60)
    print("COHERENCE METRICS")
    print("=" * 60)
    coherence = results_data.get("coherence_metrics", {})
    print(f"Mean coherence:         {coherence.get('mean_coherence', 0):.3f}")
    print(f"Current coherence:      {coherence.get('current_coherence', 0):.3f}")
    print(
        f"Phenomenal unity:       {'Yes' if coherence.get('phenomenal_unity', 0) > 0.5 else 'No'}"
    )

    # Display temporal dynamics summary
    print("\n" + "=" * 60)
    print("TEMPORAL DYNAMICS SUMMARY")
    print("=" * 60)
    dynamics = results_data.get("temporal_dynamics", {})
    print(f"Time points recorded:   {len(dynamics.get('time', []))}")

    if len(dynamics.get("free_energy", [])) > 0:
        import numpy as np

        print(
            f"Free energy range:      [{np.min(dynamics.get('free_energy', [])):.2f}, "
            f"{np.max(dynamics.get('free_energy', [])):.2f}]"
        )

    if len(dynamics.get("precision", [])) > 0:
        import numpy as np

        print(
            f"Precision range:        [{np.min(dynamics.get('precision', [])):.2f}, "
            f"{np.max(dynamics.get('precision', [])):.2f}]"
        )

    if len(dynamics.get("ignition_signal", [])) > 0:
        import numpy as np

        print(
            f"Ignition signal range:  [{np.min(dynamics.get('ignition_signal', [])):.2f}, "
            f"{np.max(dynamics.get('ignition_signal', [])):.2f}]"
        )

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
