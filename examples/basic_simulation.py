"""Basic APGI System Simulation Example."""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apgi_system.system import APGISystem


def main():
    """Run a basic simulation."""
    print("Initializing APGI System...")
    system = APGISystem()

    print("Running 10-second simulation...")

    # Define varying sensory input
    def sensory_input(t):
        # Sinusoidal input with noise
        base = np.sin(2 * np.pi * t / 1000.0) * np.ones(256)
        noise = np.random.randn(256) * 0.2
        return base + noise

    # Run simulation
    results = system.run(duration_ms=10000.0, extero_input_fn=sensory_input)

    print(f"\nSimulation Complete!")
    print(f"Total steps: {results['total_steps']}")
    print(f"Ignition events: {results['ignition_count']}")
    print(f"Ignition rate: {results['ignition_count'] / results['total_steps']:.3f}")

    # Get final state summary
    summary = system.get_state_summary()
    print(f"\nFinal State:")
    print(f"  Allostatic load: {summary['allostatic_load']:.3f}")
    print(f"  Metabolic reserves: {summary['metabolic_reserves']:.1f}")
    print(f"  Somatic markers: {summary['somatic_markers']['num_markers']}")

    # Plot results
    plot_results(system.history)


def plot_results(history):
    """Plot simulation results."""
    plt.figure(figsize=(12, 8))

    # Ignition events
    plt.subplot(4, 1, 1)
    plt.plot(history['time'], history['ignitions'], 'r.', alpha=0.5)
    plt.ylabel('Ignition Events')
    plt.title('APGI System Simulation Results')

    # Free energy
    plt.subplot(4, 1, 2)
    plt.plot(history['time'], history['free_energy'])
    plt.ylabel('Free Energy')

    # Precision
    plt.subplot(4, 1, 3)
    plt.plot(history['time'], history['precision'])
    plt.ylabel('Extero Precision')

    # Metabolic reserves
    plt.subplot(4, 1, 4)
    plt.plot(history['time'], history['metabolic_reserves'])
    plt.ylabel('Metabolic Reserves')
    plt.xlabel('Time (ms)')

    plt.tight_layout()
    plt.savefig('apgi_simulation_results.png', dpi=150)
    print("\nPlot saved as 'apgi_simulation_results.png'")
    plt.show()


if __name__ == '__main__':
    main()
