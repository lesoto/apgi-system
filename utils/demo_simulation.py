"""
Demonstration of APGI System functionality
Runs a short simulation and displays results
"""

import numpy as np
from apgi_system.system import APGISystem
from apgi_system.platform_utils import get_resource_path

def main():
    print("=" * 70)
    print("APGI System - Demonstration Simulation")
    print("=" * 70)
    print()
    
    # Initialize system
    print("Initializing APGI System...")
    system = APGISystem(config_path=str(get_resource_path("config/default.yaml")))
    print("✓ System initialized successfully")
    print()
    
    # Run simulation
    duration_ms = 1000.0  # 1 second
    print(f"Running simulation for {duration_ms} ms...")
    print()
    
    # Custom input function - sinusoidal with noise
    def input_fn(t):
        base = np.sin(2 * np.pi * t / 1000.0) * np.ones(256)
        noise = np.random.randn(256) * 0.2
        return base + noise
    
    results = system.run(duration_ms=duration_ms, extero_input_fn=input_fn)
    
    print("✓ Simulation complete!")
    print()
    
    # Display results
    print("-" * 70)
    print("SIMULATION RESULTS")
    print("-" * 70)
    print(f"Total Steps:        {results['total_steps']}")
    print(f"Duration:           {results['duration_ms']} ms")
    print(f"Ignition Events:    {results['ignition_count']}")
    print(f"Ignition Rate:      {results['ignition_count'] / (duration_ms / 1000.0):.2f} events/sec")
    print()
    
    # Final state
    final = results['final_state']
    print("-" * 70)
    print("FINAL STATE")
    print("-" * 70)
    print(f"Time:               {final['time']:.2f} ms")
    print(f"Workspace Active:   {final['workspace']['is_broadcasting']}")
    print(f"Metabolic Reserves: {final['metabolism']['reserves']:.1f}")
    print(f"Allostatic Load:    {final['allostasis']['allostatic_load']:.3f}")
    print(f"Self Coherence:     {final['self_model']['minimal']['coherence']:.3f}")
    print()
    
    # Precision
    print("-" * 70)
    print("PRECISION WEIGHTING")
    print("-" * 70)
    print(f"Exteroceptive:      {final['precision']['exteroceptive']:.3f}")
    print(f"Interoceptive:      {final['precision']['interoceptive']:.3f}")
    print()
    
    # Body state
    print("-" * 70)
    print("BODY STATE")
    print("-" * 70)
    print(f"Heart Rate:         {final['body']['current']['heart_rate']:.1f} bpm")
    print(f"Cortisol:           {final['body']['current']['cortisol']:.2f} μg/dL")
    print(f"Temperature:        {final['body']['current']['temperature']:.2f} °C")
    print()
    
    # Oscillations
    print("-" * 70)
    print("NEURAL OSCILLATIONS")
    print("-" * 70)
    band_powers = final['oscillations']['band_powers']
    for band, power in band_powers.items():
        print(f"{band.capitalize():12s}    {power:.3f}")
    print()
    
    # System summary
    print("-" * 70)
    print("SYSTEM SUMMARY")
    print("-" * 70)
    summary = system.get_state_summary()
    print(f"Workspace State:    {summary['workspace_state']}")
    print(f"Somatic Markers:    {summary['somatic_markers']['num_markers']}")
    print()
    
    print("=" * 70)
    print("✓ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("To launch the GUI and see real-time visualization:")
    print("  $ python run_gui.py")
    print()

if __name__ == '__main__':
    main()
