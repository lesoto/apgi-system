"""
OpenNeuro DS-12 Integration Usage Examples

This file demonstrates how to use the OpenNeuro DS-12 classes programmatically
outside of the GUI context.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np  # noqa: E402

from Psychological_States_GUI import (  # noqa: E402
    OpenNeuroDS003478Analyzer,
    OpenNeuroDS003478Visualizer,
)

# =============================================================================
# Example 1: Create a Single EEG Depression Profile
# =============================================================================


def example_1_create_profile() -> None:
    """Create a single EEG depression profile"""
    print("=" * 70)
    print("Example 1: Create a Single EEG Depression Profile")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()

    # Create a profile for a medicated MDD patient with moderate severity
    profile = analyzer.create_eeg_depression_profile(
        group="MDD",
        severity="moderate",
        medication="medicated",
    )

    print(f"\nParticipant ID: {profile.participant_id}")
    print(f"Group: {profile.group}")
    print(f"Age: {profile.age:.1f} years")
    print(f"Sex: {profile.sex}")
    print(f"Medication Status: {profile.medication_status}")
    print("\nEEG Measures (Eyes Open):")
    print(f"  Alpha Power: {profile.alpha_power_eo:.3f}")
    print(f"  Theta Power: {profile.theta_power_eo:.3f}")
    print(f"  Aperiodic Exponent: {profile.aperiodic_exponent_eo:.2f}")
    print("\nEEG Measures (Eyes Closed):")
    print(f"  Alpha Power: {profile.alpha_power_ec:.3f}")
    print(f"  Theta Power: {profile.theta_power_ec:.3f}")
    print(f"  Aperiodic Exponent: {profile.aperiodic_exponent_ec:.2f}")
    print("\nDerived Measures:")
    print(f"  Alpha Power (Mean): {profile.alpha_power_mean:.3f}")
    print(f"  Aperiodic Exponent (Mean): {profile.aperiodic_exponent_mean:.2f}")
    print(f"  Frontal Alpha Asymmetry: {profile.frontal_alpha_asymmetry:+.3f}")
    print(f"  Spectral Flattening: {profile.spectral_flattening:.1%}")
    print("\nClinical Measures:")
    print(f"  PHQ-9 Score: {profile.phq9_score:.0f}")
    print(f"  Depression Severity: {profile.depression_severity:.1%}")
    print("\nAPGI Measures:")
    print(f"  Precision Weighting Index: {profile.precision_weighting_index:.3f}")
    print(f"  Depression Specifier Score: {profile.depression_specifier_score:.3f}")
    print(f"  Aperiodic Blunting: {profile.aperiodic_blunting:.3f}")
    print(f"  APGI Depression Index: {profile.apgi_depression_index:.3f}")


# =============================================================================
# Example 2: Compare MDD vs. Healthy Controls
# =============================================================================


def example_2_mdd_vs_hc() -> None:
    """Compare EEG measures between MDD and healthy controls"""
    print("\n" + "=" * 70)
    print("Example 2: MDD vs. Healthy Controls Comparison")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()

    # Generate profiles for each group
    mdd_profiles = [
        analyzer.create_eeg_depression_profile(group="MDD", severity="moderate") for _ in range(50)
    ]

    hc_profiles = [analyzer.create_eeg_depression_profile(group="HC") for _ in range(50)]

    # Compare key measures
    print("\nMajor Depressive Disorder (N=50):")
    print(f"  Mean Alpha Power: {np.mean([p.alpha_power_mean for p in mdd_profiles]):.3f}")
    print(
        f"  Mean Aperiodic Exponent: {np.mean([p.aperiodic_exponent_mean for p in mdd_profiles]):.2f}"
    )
    print(
        f"  Mean Frontal Asymmetry: {np.mean([p.frontal_alpha_asymmetry for p in mdd_profiles]):+.3f}"
    )
    print(f"  Mean PHQ-9: {np.mean([p.phq9_score for p in mdd_profiles]):.1f}")
    print(f"  Mean APGI Index: {np.mean([p.apgi_depression_index for p in mdd_profiles]):.3f}")

    print("\nHealthy Controls (N=50):")
    print(f"  Mean Alpha Power: {np.mean([p.alpha_power_mean for p in hc_profiles]):.3f}")
    print(
        f"  Mean Aperiodic Exponent: {np.mean([p.aperiodic_exponent_mean for p in hc_profiles]):.2f}"
    )
    print(
        f"  Mean Frontal Asymmetry: {np.mean([p.frontal_alpha_asymmetry for p in hc_profiles]):+.3f}"
    )
    print(f"  Mean PHQ-9: {np.mean([p.phq9_score for p in hc_profiles]):.1f}")
    print(f"  Mean APGI Index: {np.mean([p.apgi_depression_index for p in hc_profiles]):.3f}")

    print("\nKey Differences:")
    print("  • MDD has lower alpha power")
    print("  • MDD has flatter aperiodic exponent (spectral flattening)")
    print("  • MDD has greater frontal asymmetry")
    print("  • MDD has higher APGI depression index")


# =============================================================================
# Example 3: Depression Severity Spectrum
# =============================================================================


def example_3_severity_spectrum() -> None:
    """Show how EEG measures change with depression severity"""
    print("\n" + "=" * 70)
    print("Example 3: Depression Severity Spectrum")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()
    severities = ["mild", "moderate", "severe"]

    for severity in severities:
        profiles = [
            analyzer.create_eeg_depression_profile(group="MDD", severity=severity)
            for _ in range(30)
        ]

        alpha_powers = [p.alpha_power_mean for p in profiles]
        aperiodic_exponents = [p.aperiodic_exponent_mean for p in profiles]
        phq9_scores = [p.phq9_score for p in profiles]
        apgi_indices = [p.apgi_depression_index for p in profiles]

        print(f"\n{severity.capitalize()} Depression (N=30):")
        print(f"  PHQ-9: {np.mean(phq9_scores):.1f} ± {np.std(phq9_scores):.1f}")
        print(f"  Alpha Power: {np.mean(alpha_powers):.3f} ± {np.std(alpha_powers):.3f}")
        print(
            f"  Aperiodic Exponent: {np.mean(aperiodic_exponents):.2f} ± {np.std(aperiodic_exponents):.2f}"
        )
        print(f"  APGI Index: {np.mean(apgi_indices):.3f} ± {np.std(apgi_indices):.3f}")


# =============================================================================
# Example 4: Medication Effects
# =============================================================================


def example_4_medication_effects() -> None:
    """Compare medicated vs. unmedicated MDD patients"""
    print("\n" + "=" * 70)
    print("Example 4: Medication Effects on EEG")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()

    # Generate profiles for each medication group
    medicated = [
        analyzer.create_eeg_depression_profile(
            group="MDD", severity="moderate", medication="medicated"
        )
        for _ in range(30)
    ]

    unmedicated = [
        analyzer.create_eeg_depression_profile(
            group="MDD", severity="moderate", medication="unmedicated"
        )
        for _ in range(30)
    ]

    print("\nMediated MDD (N=30):")
    print(f"  Mean Alpha Power: {np.mean([p.alpha_power_mean for p in medicated]):.3f}")
    print(
        f"  Mean Aperiodic Exponent: {np.mean([p.aperiodic_exponent_mean for p in medicated]):.2f}"
    )
    print(
        f"  Mean Frontal Asymmetry: {np.mean([p.frontal_alpha_asymmetry for p in medicated]):+.3f}"
    )
    print(f"  Mean APGI Index: {np.mean([p.apgi_depression_index for p in medicated]):.3f}")

    print("\nUnmedicated MDD (N=30):")
    print(f"  Mean Alpha Power: {np.mean([p.alpha_power_mean for p in unmedicated]):.3f}")
    print(
        f"  Mean Aperiodic Exponent: {np.mean([p.aperiodic_exponent_mean for p in unmedicated]):.2f}"
    )
    print(
        f"  Mean Frontal Asymmetry: {np.mean([p.frontal_alpha_asymmetry for p in unmedicated]):+.3f}"
    )
    print(f"  Mean APGI Index: {np.mean([p.apgi_depression_index for p in unmedicated]):.3f}")

    print("\nMedication Effects:")
    print("  • Medicated shows higher alpha power")
    print("  • Medicated shows steeper aperiodic exponent")
    print("  • Medicated shows reduced frontal asymmetry")
    print("  • Medicated shows lower APGI depression index")


# =============================================================================
# Example 5: Frontal Alpha Asymmetry Analysis
# =============================================================================


def example_5_asymmetry_analysis() -> None:
    """Analyze frontal alpha asymmetry patterns"""
    print("\n" + "=" * 70)
    print("Example 5: Frontal Alpha Asymmetry Analysis")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()

    # Generate profiles
    mdd_profiles = [
        analyzer.create_eeg_depression_profile(group="MDD", severity="moderate") for _ in range(50)
    ]

    hc_profiles = [analyzer.create_eeg_depression_profile(group="HC") for _ in range(50)]

    mdd_asymmetries = [p.frontal_alpha_asymmetry for p in mdd_profiles]
    hc_asymmetries = [p.frontal_alpha_asymmetry for p in hc_profiles]

    print("\nMDD Frontal Alpha Asymmetry (N=50):")
    print(f"  Mean: {np.mean(mdd_asymmetries):+.3f}")
    print(f"  Std Dev: {np.std(mdd_asymmetries):.3f}")
    print(f"  Range: {np.min(mdd_asymmetries):+.3f} to {np.max(mdd_asymmetries):+.3f}")
    print(f"  Left-dominant (negative): {sum(1 for x in mdd_asymmetries if x < -0.1)} / 50")
    print(f"  Symmetric: {sum(1 for x in mdd_asymmetries if -0.1 <= x <= 0.1)} / 50")
    print(f"  Right-dominant (positive): {sum(1 for x in mdd_asymmetries if x > 0.1)} / 50")

    print("\nHealthy Control Frontal Alpha Asymmetry (N=50):")
    print(f"  Mean: {np.mean(hc_asymmetries):+.3f}")
    print(f"  Std Dev: {np.std(hc_asymmetries):.3f}")
    print(f"  Range: {np.min(hc_asymmetries):+.3f} to {np.max(hc_asymmetries):+.3f}")
    print(f"  Left-dominant (negative): {sum(1 for x in hc_asymmetries if x < -0.1)} / 50")
    print(f"  Symmetric: {sum(1 for x in hc_asymmetries if -0.1 <= x <= 0.1)} / 50")
    print(f"  Right-dominant (positive): {sum(1 for x in hc_asymmetries if x > 0.1)} / 50")


# =============================================================================
# Example 6: Generate Visualizations Programmatically
# =============================================================================


def example_6_generate_visualizations() -> None:
    """Generate visualizations programmatically"""
    print("\n" + "=" * 70)
    print("Example 6: Generate Visualizations")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()
    visualizer = OpenNeuroDS003478Visualizer(analyzer)

    # Generate each visualization type
    print("\nGenerating visualizations...")

    fig1 = visualizer.plot_mdd_vs_hc_comparison(n_samples=50)
    if fig1:
        print("✓ MDD vs. HC Comparison plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig1, "mdd_vs_hc.html")
        print(f"  Saved to: {filepath}")

    fig2 = visualizer.plot_depression_severity_spectrum(n_samples=100)
    if fig2:
        print("✓ Depression Severity Spectrum plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig2, "severity_spectrum.html")
        print(f"  Saved to: {filepath}")

    fig3 = visualizer.plot_alpha_asymmetry_depression(n_samples=100)
    if fig3:
        print("✓ Alpha Asymmetry Distribution plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig3, "asymmetry_dist.html")
        print(f"  Saved to: {filepath}")

    fig4 = visualizer.plot_medication_effects(n_samples=50)
    if fig4:
        print("✓ Medication Effects plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig4, "medication_effects.html")
        print(f"  Saved to: {filepath}")

    fig5 = visualizer.plot_apgi_depression_index(n_samples=100)
    if fig5:
        print("✓ APGI Depression Index plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig5, "apgi_index.html")
        print(f"  Saved to: {filepath}")


# =============================================================================
# Example 7: Dataset Information
# =============================================================================


def example_7_dataset_info() -> None:
    """Display comprehensive dataset information"""
    print("\n" + "=" * 70)
    print("Example 7: Dataset Information")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()
    info = analyzer.get_dataset_info()

    print(f"\nDataset: {info['dataset_name']}")
    print(f"Title: {info['title']}")
    print(f"URL: {info['url']}")
    print(
        f"Sample Size: MDD N={info['sample_size_mdd']}, HC N={info['sample_size_hc']}, Total N={info['total_sample']}"
    )
    print(f"Age Range: {info['age_range'][0]}-{info['age_range'][1]} years")
    print(f"Conditions: {', '.join(info['conditions'])}")
    print(f"Access Status: {info['access_status']}")
    print(f"BIDS Compliant: {'Yes' if info['bids_compliant'] else 'No'}")

    print("\nKey Measures:")
    for measure in info["key_measures"]:
        print(f"  • {measure}")

    print("\nAPGI Innovations:")
    for innovation in info["apgi_innovations"]:
        print(f"  • {innovation}")

    print("\nStrengths:")
    for strength in info["strengths"]:
        print(f"  • {strength}")

    print("\nLimitations:")
    for limitation in info["limitations"]:
        print(f"  • {limitation}")


# =============================================================================
# Example 8: Profile to Dictionary Conversion
# =============================================================================


def example_8_profile_to_dict() -> None:
    """Convert profile to dictionary for data export"""
    print("\n" + "=" * 70)
    print("Example 8: Profile to Dictionary Conversion")
    print("=" * 70)

    analyzer = OpenNeuroDS003478Analyzer()
    profile = analyzer.create_eeg_depression_profile()

    # Convert to dictionary
    profile_dict = profile.to_dict()

    print("\nProfile as Dictionary:")
    for key, value in profile_dict.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        elif isinstance(value, bool):
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("OpenNeuro DS-12 Integration - Usage Examples")
    print("=" * 70)

    # Run all examples
    example_1_create_profile()
    example_2_mdd_vs_hc()
    example_3_severity_spectrum()
    example_4_medication_effects()
    example_5_asymmetry_analysis()
    example_6_generate_visualizations()
    example_7_dataset_info()
    example_8_profile_to_dict()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
