#!/usr/bin/env python3
"""Test script for Masking Paradigm Task."""

from apgi_system.system import APGISystem
from apgi_system.experiments import MaskingParadigmTask


def test_masking_paradigm():
    """Test the masking paradigm task."""
    print("=" * 80)
    print("Testing Masking Paradigm Task")
    print("=" * 80)

    # Initialize APGI system
    print("\n1. Initializing APGI system...")
    system = APGISystem()
    print("   ✓ System initialized")

    # Create masking task with reduced parameters for quick testing
    print("\n2. Creating Masking Paradigm task...")
    task = MaskingParadigmTask(
        target_duration_ms=50.0,
        soas=[0, 50, 100, 200],  # Reduced SOAs for testing
        mask_duration_ms=100.0,
        num_trials_per_condition=5,  # Reduced trials for testing
        target_strength=2.0,
        mask_strength=3.0,
    )
    print("   ✓ Task created")

    # Run all trials
    print("\n3. Running trials...")
    results = task.run_all_trials(system)
    print("   ✓ All trials completed")

    # Print results
    print("\n4. Results:")
    task.print_results(results)

    # Save results
    print("\n5. Saving results...")
    task.save_results("test_masking_results.json")
    print("   ✓ Results saved")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)

    return results


if __name__ == "__main__":
    test_masking_paradigm()
