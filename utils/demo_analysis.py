"""Demonstration of extended analysis capabilities.

This script demonstrates how to use the analysis module to examine
APGI system behavior after a simulation run.
"""

from apgi_system.system import APGISystem
from apgi_system.analysis import analyze_simulation_run


def main():
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
    results = analyze_simulation_run(system)
    
    # Display ignition statistics
    print("\n" + "=" * 60)
    print("IGNITION STATISTICS")
    print("=" * 60)
    ign_stats = results.ignition_statistics
    print(f"Total ignitions:        {ign_stats['total_ignitions']}")
    print(f"Ignition rate:          {ign_stats['ignition_rate_hz']:.2f} Hz")
    print(f"Mean interval:          {ign_stats['mean_ignition_interval_ms']:.1f} ms")
    print(f"Std interval:           {ign_stats['std_ignition_interval_ms']:.1f} ms")
    print(f"Min interval:           {ign_stats['min_ignition_interval_ms']:.1f} ms")
    print(f"Max interval:           {ign_stats['max_ignition_interval_ms']:.1f} ms")
    print(f"Mean duration:          {ign_stats['mean_ignition_duration_ms']:.1f} ms")
    
    # Display energy budget summary
    print("\n" + "=" * 60)
    print("ENERGY BUDGET SUMMARY")
    print("=" * 60)
    energy = results.energy_budget_summary
    print(f"Total consumed:         {energy['total_energy_consumed']:.3f} units")
    print(f"Mean per step:          {energy['mean_energy_per_step']:.6f} units")
    print(f"Energy per ignition:    {energy['energy_per_ignition']:.3f} units")
    print(f"Final reserves:         {energy['final_reserves']:.2f} units")
    print(f"Min reserves:           {energy['min_reserves']:.2f} units")
    print(f"Depletion rate:         {energy['reserve_depletion_rate']:.3f} units/s")
    
    # Display somatic marker statistics
    print("\n" + "=" * 60)
    print("SOMATIC MARKER STATISTICS")
    print("=" * 60)
    markers = results.somatic_marker_stats
    print(f"Total markers:          {markers['total_markers']}")
    print(f"Capacity used:          {markers['capacity_used']:.1%}")
    print(f"Retrieval success rate: {markers['retrieval_success_rate']:.1%}")
    print(f"Mean marker strength:   {markers['mean_marker_strength']:.3f}")
    print(f"Mean marker outcome:    {markers['mean_marker_outcome']:.3f}")
    print(f"Learning events:        {markers['learning_events']}")
    
    # Display coherence metrics
    print("\n" + "=" * 60)
    print("COHERENCE METRICS")
    print("=" * 60)
    coherence = results.coherence_metrics
    print(f"Mean coherence:         {coherence['mean_coherence']:.3f}")
    print(f"Current coherence:      {coherence['current_coherence']:.3f}")
    print(f"Phenomenal unity:       {'Yes' if coherence['phenomenal_unity'] > 0.5 else 'No'}")
    
    # Display temporal dynamics summary
    print("\n" + "=" * 60)
    print("TEMPORAL DYNAMICS SUMMARY")
    print("=" * 60)
    dynamics = results.temporal_dynamics
    print(f"Time points recorded:   {len(dynamics['time'])}")
    
    if len(dynamics['free_energy']) > 0:
        import numpy as np
        print(f"Free energy range:      [{np.min(dynamics['free_energy']):.2f}, "
              f"{np.max(dynamics['free_energy']):.2f}]")
    
    if len(dynamics['precision']) > 0:
        import numpy as np
        print(f"Precision range:        [{np.min(dynamics['precision']):.2f}, "
              f"{np.max(dynamics['precision']):.2f}]")
    
    if len(dynamics['ignition_signal']) > 0:
        import numpy as np
        print(f"Ignition signal range:  [{np.min(dynamics['ignition_signal']):.2f}, "
              f"{np.max(dynamics['ignition_signal']):.2f}]")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
