"""
Virtual Metabolic Layer Demo
==============================

This example demonstrates the Virtual Metabolic Layer with Neural Mass Models
for ATP flux estimation and dynamic κ (kappa) calculation.

The Virtual Metabolic Layer provides biophysically-grounded metabolic cost
estimates for Global Ignition events, replacing order-of-magnitude approximations
with detailed calculations based on:

1. Neural Mass Model dynamics (Jansen-Rit inspired)
2. Glutamate recycling costs
3. Ion pumping (Na+/K+-ATPase, Ca2+-ATPase)
4. Baseline neural metabolism

Example Output:
--------------
- Baseline ATP consumption: ~10^14 ATP/s per cortical column
- Ignition event cost: ~10^16 ATP molecules
- κ (kappa) value: ~10^6 (millions of times the Landauer limit)
"""

import numpy as np

# Import the Virtual Metabolic Layer
from apgi_framework.thermodynamic import (
    IntegratedMetabolicSystem,
    VirtualMetabolicLayer,
    create_metabolic_system_with_vml,
    estimate_kappa_for_ignition,
)


def demo_basic_vml():
    """Demonstrate basic Virtual Metabolic Layer usage."""
    print("=" * 60)
    print("Demo 1: Basic Virtual Metabolic Layer")
    print("=" * 60)

    # Create the Virtual Metabolic Layer
    vml = VirtualMetabolicLayer()

    # Simulate pre-ignition neural activity (100ms of input processing)
    print("\n1. Simulating pre-ignition neural activity...")
    result = vml.simulate_neural_activity(
        input_drive=0.3,  # Moderate input
        duration_ms=100.0,
    )
    print(f"   Average pyramidal firing rate: {result['average_pyramidal_firing_hz']:.2f} Hz")
    print(f"   ATP consumed: {result['total_atp_consumed']:.2e} molecules")

    # Compute cost of a Global Ignition event
    print("\n2. Computing Global Ignition cost...")
    workspace_content = np.random.randn(256)  # Typical workspace dimensionality

    ignition_cost = vml.compute_ignition_cost(
        ignition_signal=3.5,  # S_t (accumulated surprise)
        threshold=2.0,  # θ_t (ignition threshold)
        workspace_content=workspace_content,
        ignition_duration_ms=300.0,  # Typical ignition duration
    )

    print(f"   Signal excess (S_t - θ_t): {ignition_cost['signal_excess']:.2f}")
    print(f"   Broadcast amplitude: {ignition_cost['broadcast_amplitude']:.2f}")
    print("\n   ATP Cost Breakdown:")
    print(f"   - Glutamate recycling: {ignition_cost['atp_glutamate']:.2e} ATP")
    print(f"   - Na+/K+ pumping: {ignition_cost['atp_na_k_pump']:.2e} ATP")
    print(f"   - Ca2+ pumping: {ignition_cost['atp_ca_pump']:.2e} ATP")
    print(f"   - Baseline: {ignition_cost['atp_baseline']:.2e} ATP")
    print(f"   - Total: {ignition_cost['atp_total']:.2e} ATP")

    print("\n   Information Metrics:")
    print(f"   - Bits broadcast: {ignition_cost['bits_broadcast']:.1f}")
    print(f"   - Vesicles released: {ignition_cost['vesicles_released']:.2e}")

    print(f"\n   κ (kappa) value: {ignition_cost['kappa_landauer']:.2e}")
    print(
        f"   - This is ~{ignition_cost['kappa_landauer'] / 1e6:.1f} million times the Landauer limit"
    )
    print(f"   - ATP per bit: {ignition_cost['atp_per_bit']:.2e}")

    # Get current dynamic kappa
    kappa = vml.get_dynamic_kappa()
    print(f"\n3. Current dynamic κ for system: {kappa:.2e}")

    # Get metabolic state summary
    print("\n4. Metabolic State Summary:")
    state = vml.get_metabolic_state()
    print(f"   - Total ATP accumulated: {state['accumulated_atp']:.2e}")
    print(f"   - Ignition events: {state['ignition_event_count']}")
    print(f"   - Recent firing rates: {state['recent_firing_rates']}")


def demo_integrated_system():
    """Demonstrate the Integrated Metabolic System."""
    print("\n" + "=" * 60)
    print("Demo 2: Integrated Metabolic System")
    print("=" * 60)

    # Create integrated system with dynamic kappa enabled
    print("\n1. Creating integrated metabolic system...")
    config = {
        "thermodynamic": {
            "total_energy_budget": 100.0,
            "baseline_consumption": 20.0,
            "ignition_cost": 7.5,  # Static fallback
            "use_dynamic_kappa": True,  # Enable NMM-based κ
            "workspace_neurons": 100_000,
            "ignition_duration_ms": 300.0,
        }
    }

    system = IntegratedMetabolicSystem(config)
    print(f"   Dynamic κ enabled: {system.use_dynamic_kappa}")
    print(f"   Workspace neurons: {system.workspace_neurons}")

    # Simulate multiple ignition events
    print("\n2. Simulating 5 ignition events...")
    for i in range(5):
        workspace_content = np.random.randn(256)

        result = system.update(
            ignition_occurred=True,
            ignition_signal=3.0 + np.random.rand(),  # Varying signal
            threshold=2.0,
            workspace_content=workspace_content,
            task_active=True,
            dt_ms=1.0,
        )

        print(
            f"   Event {i + 1}: κ={result['current_kappa']:.2e}, "
            f"reserves={result['reserve_fraction']:.2%}"
        )

    # Get metabolic summary
    print("\n3. Metabolic Summary:")
    summary = system.get_metabolic_summary()
    print(f"   Total ignitions: {summary['ignition_count']}")
    print(f"   Total ATP consumed: {summary['total_atp_consumed']:.2e}")

    if summary["kappa_stats"]["num_samples"] > 0:
        print("   κ statistics:")
        print(f"   - Mean: {summary['kappa_stats']['mean']:.2e}")
        print(f"   - Std: {summary['kappa_stats']['std']:.2e}")
        print(
            f"   - Range: [{summary['kappa_stats']['min']:.2e}, "
            f"{summary['kappa_stats']['max']:.2e}]"
        )


def demo_convenience_function():
    """Demonstrate the convenience function for quick κ estimation."""
    print("\n" + "=" * 60)
    print("Demo 3: Quick κ Estimation (Convenience Function)")
    print("=" * 60)

    print("\n1. Estimating κ for different ignition conditions...")

    # Case 1: Near-threshold ignition
    kappa_near = estimate_kappa_for_ignition(
        ignition_signal=2.1,  # Just above threshold
        threshold=2.0,
        workspace_content=np.random.randn(256) * 0.5,  # Weak content
        ignition_duration_ms=300.0,
    )
    print(f"   Near-threshold ignition: κ = {kappa_near:.2e}")

    # Case 2: Supra-threshold ignition
    kappa_supra = estimate_kappa_for_ignition(
        ignition_signal=5.0,  # Strong signal
        threshold=2.0,
        workspace_content=np.random.randn(256) * 2.0,  # Strong content
        ignition_duration_ms=300.0,
    )
    print(f"   Supra-threshold ignition: κ = {kappa_supra:.2e}")

    # Case 3: Large workspace
    kappa_large = estimate_kappa_for_ignition(
        ignition_signal=4.0,
        threshold=2.0,
        workspace_content=np.random.randn(512),  # Larger workspace
        ignition_duration_ms=400.0,  # Longer duration
    )
    print(f"   Large workspace ignition: κ = {kappa_large:.2e}")

    print("\n   Note: κ varies with signal strength, content magnitude,")
    print("         workspace size, and ignition duration.")


def demo_comparison_with_static():
    """Compare dynamic κ with static order-of-magnitude estimates."""
    print("\n" + "=" * 60)
    print("Demo 4: Dynamic vs Static κ Comparison")
    print("=" * 60)

    print("\n1. Static order-of-magnitude estimate:")
    static_kappa = 1.0e6  # Typical biological estimate
    print(f"   κ_static = {static_kappa:.2e} (order-of-magnitude)")

    print("\n2. Dynamic NMM-based estimates for different conditions:")

    conditions = [
        ("Low signal, small content", 2.5, np.random.randn(256) * 0.5),
        ("Medium signal, medium content", 3.5, np.random.randn(256)),
        ("High signal, large content", 5.0, np.random.randn(256) * 2.0),
    ]

    for desc, signal, content in conditions:
        kappa = estimate_kappa_for_ignition(
            ignition_signal=signal,
            threshold=2.0,
            workspace_content=content,
            ignition_duration_ms=300.0,
        )
        ratio = kappa / static_kappa
        print(f"   {desc}:")
        print(f"     κ_dynamic = {kappa:.2e}")
        print(f"     Ratio to static: {ratio:.2f}x")

    print("\n   The dynamic κ provides context-specific estimates")
    print("   that account for actual neural activity levels.")


def demo_factory_function():
    """Demonstrate the factory function for easy setup."""
    print("\n" + "=" * 60)
    print("Demo 5: Factory Function for Quick Setup")
    print("=" * 60)

    print("\n1. Creating system with factory function...")

    # Quick setup with custom parameters
    system = create_metabolic_system_with_vml(
        workspace_neurons=150_000,  # Custom neuron count
        use_dynamic_kappa=True,
        config_overrides={
            "thermodynamic": {
                "total_energy_budget": 150.0,
                "ignition_duration_ms": 250.0,
            },
            "neural_mass": {
                "excitatory_tau_ms": 12.0,  # Faster excitatory dynamics
            },
        },
    )

    print("   Created system:")
    print(f"   - Workspace neurons: {system.workspace_neurons}")
    print(f"   - Total energy budget: {system.metabolic_budget.total_budget}")
    print(f"   - Dynamic κ enabled: {system.use_dynamic_kappa}")

    # Run a quick test
    print("\n2. Testing with single ignition...")
    result = system.update(
        ignition_occurred=True,
        ignition_signal=3.0,
        threshold=2.0,
        workspace_content=np.random.randn(256),
        task_active=True,
        dt_ms=1.0,
    )

    print("   Result:")
    print(f"   - κ = {result['current_kappa']:.2e}")
    print(f"   - Energy reserves: {result['reserve_fraction']:.2%}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("Virtual Metabolic Layer Demonstration")
    print("=" * 60)
    print("\nThis demo shows the Virtual Metabolic Layer implementation")
    print("using Neural Mass Models for ATP flux estimation.")

    demo_basic_vml()
    demo_integrated_system()
    demo_convenience_function()
    demo_comparison_with_static()
    demo_factory_function()

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. κ (kappa) is computed from biophysical ATP consumption estimates")
    print("2. Neural Mass Models provide population-level firing rate dynamics")
    print("3. ATP costs include glutamate recycling and ion pumping")
    print("4. Dynamic κ varies with ignition conditions (signal, content, duration)")
    print("5. Integrated system connects VML with existing APGI metabolic budget")


if __name__ == "__main__":
    main()
