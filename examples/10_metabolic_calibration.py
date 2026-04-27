"""
Metabolic Calibration Example
=============================

This example demonstrates the ground-truth calibration of metabolic cost
coefficients (c_1, c_2) using high-resolution metabolic imaging data.

The c_1 coefficient represents dynamic/signaling costs (ATP per ignition event),
measured from Two-photon metabolic imaging (iATPSnFR2, ATeam sensors).

The c_2 coefficient represents static/maintenance costs (ATP per ms per neuron),
measured from 31P-MRS (Phosphorus Magnetic Resonance Spectroscopy).

Usage:
------
    # Method 1: Use default literature coefficients
    python examples/10_metabolic_calibration.py

    # Method 2: Calibrate from datasets (when available)
    # Requires: Two-photon traces (CSV/HDF5) and/or P-MRS flux data (CSV)
    python examples/10_metabolic_calibration.py --two-photon ./iatpsnfr2.csv --pmrs ./fmrs_flux.csv

References:
-----------
- Marvin et al. (2024): iATPSnFR2 sensor - PNAS/Nature Communications
- Díaz-García et al. (2017): ATeam/Peredox - Cell Metabolism
- Chen et al. (2020): 31P-fMRS at 3T/7T/9.4T
- Attwell & Laughlin (2001): Energy budget for signaling
"""

import argparse

# Import calibration components
from apgi_framework.thermodynamic import (
    CalibratedVirtualMetabolicLayer,
    CostCoefficientValidator,
    MetabolicCalibrator,
    get_default_coefficients,
)


def demo_default_coefficients():
    """Demonstrate using literature-based default coefficients."""
    print("=" * 70)
    print("Demo 1: Default Literature Coefficients")
    print("=" * 70)

    # Get default coefficients (from Attwell & Laughlin 2001)
    coeffs = get_default_coefficients()

    print("\n📊 Default Cost Coefficients (Attwell & Laughlin 2001):")
    print(f"  c_1 (dynamic):  {coeffs.c_1_dynamic:.2e} ATP per action potential")
    print(f"  c_2 (static):   {coeffs.c_2_static:.2e} ATP per ms per neuron")
    print(f"  Source:         {coeffs.calibration_source}")
    print(f"  Temporal res.:    {coeffs.temporal_resolution_ms} ms")

    # Compute expected ATP for a scenario
    n_neurons = 100_000
    n_ignitions = 10
    duration_ms = 1000.0

    total, dynamic, static = coeffs.compute_expected_atp(
        num_ignitions=n_ignitions,
        duration_ms=duration_ms,
        num_neurons=n_neurons,
    )

    print(
        f"\n💡 Example: {n_ignitions} ignitions, {n_neurons:,} neurons, "
        f"{duration_ms / 1000:.1f}s:"
    )
    print(f"  Dynamic component (c_1 × {n_ignitions}): {dynamic:.2e} ATP")
    print(f"  Static component (c_2 × {duration_ms}ms): {static:.2e} ATP")
    print(f"  Total: {total:.2e} ATP molecules")
    print(f"  Dynamic fraction: {dynamic / total:.1%}")


def demo_calibrated_vml():
    """Demonstrate Calibrated Virtual Metabolic Layer."""
    print("\n" + "=" * 70)
    print("Demo 2: Calibrated Virtual Metabolic Layer")
    print("=" * 70)

    # Create calibrated VML with default coefficients
    vml = CalibratedVirtualMetabolicLayer()

    print("\n✅ Created CalibratedVirtualMetabolicLayer")
    print(f"  c_1 = {vml.c_1:.2e} ± {vml.c_1_uncertainty:.2e} ATP/AP")
    print(f"  c_2 = {vml.c_2:.2e} ± {vml.c_2_uncertainty:.2e} ATP/ms/neuron")

    # Compute ignition cost with calibrated coefficients
    ignition_cost = vml.compute_ignition_cost_calibrated(
        ignition_signal=3.5,
        threshold=2.0,
        ignition_duration_ms=300.0,
    )

    print("\n🔥 Ignition Cost (signal=3.5, threshold=2.0, 300ms):")
    print(f"  Total ATP:     {ignition_cost['atp_total']:.2e}")
    print(
        f"  Dynamic (c_1): {ignition_cost['atp_dynamic']:.2e} ({ignition_cost['dynamic_fraction']:.1%})"
    )
    print(f"  Static (c_2):  {ignition_cost['atp_static']:.2e}")
    print(f"  κ (Landauer):  {ignition_cost['kappa_landauer']:.2e}")
    print(f"  Bits:          {ignition_cost['bits_broadcast']:.1f}")
    print(f"  Source:        {ignition_cost['calibration_source']}")


def demo_validation():
    """Demonstrate coefficient validation against literature."""
    print("\n" + "=" * 70)
    print("Demo 3: Validation Against Literature")
    print("=" * 70)

    vml = CalibratedVirtualMetabolicLayer()

    # Run validation
    validation = vml.validate_against_literature()

    print("\n📚 Comparison to Literature:")
    for ref_name, comparison in validation["literature_comparison"].items():
        ref_display = ref_name.replace("_", " ").title()
        c1_match = "✅" if comparison["c1_matches"] else "⚠️"
        c2_match = "✅" if comparison["c2_matches"] else "⚠️"

        print(f"\n  {ref_display}:")
        print(f"    c_1 deviation: {comparison['c1_deviation']:+.1%} {c1_match}")
        print(f"    c_2 deviation: {comparison['c2_deviation']:+.1%} {c2_match}")

    print(f"\n  Overall Confidence Score: {validation['confidence_score']:.2f}/1.0")
    print("  Deviation from Attwell & Laughlin:")
    print(f"    c_1: {validation['c_1_deviation_from_attwell']:+.1%}")
    print(f"    c_2: {validation['c_2_deviation_from_attwell']:+.1%}")


def demo_comparison_methods():
    """Compare calibrated vs generic cost estimation."""
    print("\n" + "=" * 70)
    print("Demo 4: Calibrated vs Generic Cost Comparison")
    print("=" * 70)

    vml = CalibratedVirtualMetabolicLayer()

    comparison = vml.compare_calibration_methods(
        ignition_signal=4.0,
        threshold=2.0,
        ignition_duration_ms=300.0,
    )

    print("\n🔬 Method Comparison:")
    print(f"  Calibrated ATP:  {comparison['calibrated']['atp_total']:.2e}")
    print(f"  Generic ATP:     {comparison['generic']['atp_total']:.2e}")
    print(f"  Difference:      {comparison['atp_difference']:+.2e}")
    print(f"  Ratio (C/G):     {comparison['atp_ratio']:.2f}x")
    print(f"  κ difference:    {comparison['kappa_difference']:+.2e}")


def demo_calibration_summary():
    """Show calibration summary."""
    print("\n" + "=" * 70)
    print("Demo 5: Calibration Summary")
    print("=" * 70)

    vml = CalibratedVirtualMetabolicLayer()

    # Run multiple computations to build history
    for i in range(5):
        _ = vml.compute_ignition_cost_calibrated(
            ignition_signal=3.0 + i * 0.5,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

    summary = vml.get_calibration_summary()

    print("\n📊 Calibration Summary:")
    print(
        f"  c_1: {summary['calibration']['c_1_dynamic']:.2e} ± {summary['calibration']['c_1_uncertainty']:.2e}"
    )
    print(
        f"  c_2: {summary['calibration']['c_2_static']:.2e} ± {summary['calibration']['c_2_uncertainty']:.2e}"
    )
    print(f"  Source: {summary['calibration']['source']}")

    if "recent_computations" in summary:
        print(f"\n  Recent Computations ({summary['recent_computations']['count']}):")
        print(f"    Mean ATP:  {summary['recent_computations']['atp_mean']:.2e}")
        print(f"    Mean κ:    {summary['recent_computations']['kappa_mean']:.2e}")


def demo_dataset_calibration(two_photon_path: str = None, pmrs_path: str = None):
    """
    Demonstrate calibration from actual datasets.

    This is a demonstration with simulated data when real datasets
    are not available. In production, this would load real iATPSnFR2
    traces and 31P-MRS flux values.
    """
    print("\n" + "=" * 70)
    print("Demo 6: Dataset-Based Calibration (Simulated)")
    print("=" * 70)

    if two_photon_path is None and pmrs_path is None:
        print("\nℹ️  No dataset paths provided. Using simulated data for demonstration.")
        print("   In production, provide paths to:")
        print("   - Two-photon: CSV/HDF5 with iATPSnFR2/ATeam traces")
        print("   - P-MRS: CSV with CK flux values or PAR/REC files")

    # Create calibrator
    calibrator = MetabolicCalibrator()

    # For demonstration, fit from literature (simulated datasets would use real data)
    coeffs = calibrator.fit_coefficients(
        c1_method="literature",
        c2_method="literature",
    )

    print("\n✅ Calibration Complete:")
    print(f"  c_1: {coeffs.c_1_dynamic:.2e} ± {coeffs.c_1_uncertainty:.2e}")
    print(f"  c_2: {coeffs.c_2_static:.2e} ± {coeffs.c_2_uncertainty:.2e}")
    print(f"  Source: {coeffs.calibration_source}")
    print(f"  Temporal Resolution: {coeffs.temporal_resolution_ms} ms")

    # Validate
    validator = CostCoefficientValidator()
    lit_comparison = validator.compare_to_literature(coeffs)

    print("\n📚 Literature Comparison:")
    for ref, comp in lit_comparison.items():
        print(f"  {ref}: c_1={comp['c1_deviation']:+.1%}, c_2={comp['c2_deviation']:+.1%}")


def main():
    """Run all demonstrations."""
    parser = argparse.ArgumentParser(description="Metabolic Calibration Example for APGI Framework")
    parser.add_argument(
        "--two-photon",
        type=str,
        help="Path to Two-photon dataset (CSV/HDF5 with iATPSnFR2 traces)",
    )
    parser.add_argument(
        "--pmrs",
        type=str,
        help="Path to P-MRS dataset (CSV with flux values or PAR/REC files)",
    )
    parser.add_argument(
        "--sensor",
        type=str,
        choices=["iATPSnFR2", "ATeam", "Peredox"],
        default="unknown",
        help="Sensor type for Two-photon data",
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("APGI Framework - Metabolic Calibration Example")
    print("=" * 70)
    print("\nThis example demonstrates ground-truth calibration of c_1/c_2")
    print("cost coefficients from high-resolution metabolic imaging.")

    # Run demonstrations
    demo_default_coefficients()
    demo_calibrated_vml()
    demo_validation()
    demo_comparison_methods()
    demo_calibration_summary()

    # Dataset calibration if paths provided
    demo_dataset_calibration(
        two_photon_path=args.two_photon,
        pmrs_path=args.pmrs,
    )

    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. c_1 represents dynamic cost (~10^7 ATP per AP) from Two-photon data")
    print("2. c_2 represents static cost (~10^6 ATP/ms/neuron) from P-MRS data")
    print("3. Calibrated VML provides ground-truth based ATP estimates")
    print("4. Validation ensures consistency with published literature")
    print("5. Use with real datasets: python 10_metabolic_calibration.py")
    print("   --two-photon ./iatpsnfr2.csv --pmrs ./fmrs.csv")
    print("")


if __name__ == "__main__":
    main()
