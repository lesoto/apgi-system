"""
HCP-EP Integration Usage Examples

This file demonstrates how to use the HCP-EP classes programmatically
outside of the GUI context.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np  # noqa: E402

from Psychological_States_GUI import (  # noqa: E402
    HCPEPAnalyzer,
    HCPEPVisualizer,
)

# =============================================================================
# Example 1: Create a Single Clinical Profile
# =============================================================================


def example_1_create_profile() -> None:
    """Create a single HCP-EP clinical profile"""
    print("=" * 70)
    print("Example 1: Create a Single Clinical Profile")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()

    # Create a profile for a treated non-affective psychosis patient with moderate severity
    profile = analyzer.create_hcp_ep_profile(
        psychosis_type="non-affective",
        treatment_status="treated",
        severity="moderate",
    )

    print(f"\nParticipant ID: {profile.participant_id}")
    print(f"Age: {profile.age:.1f} years")
    print(f"Psychosis Type: {profile.psychosis_type}")
    print(f"Years Since Onset: {profile.years_since_onset:.1f}")
    print(f"Treatment Status: {profile.treatment_history}")
    print("\nPANSS Scores:")
    print(f"  Positive: {profile.panss_positive:.1f}")
    print(f"  Negative: {profile.panss_negative:.1f}")
    print(f"  General: {profile.panss_general:.1f}")
    print(f"  Total: {profile.panss_total:.1f}")
    print("\nConnectivity Measures:")
    print(f"  Functional: {profile.functional_connectivity:.3f}")
    print(f"  Structural: {profile.structural_connectivity:.3f}")
    print(f"  Disruption: {profile.connectivity_disruption:.1%}")
    print(f"\nCognitive Performance: {profile.cognitive_performance:.1%}")
    print(f"Cognitive Impairment: {profile.cognitive_impairment:.1%}")
    print("\nAPGI Measures:")
    print(f"  Precision Gating Failure: {profile.precision_gating_failure:.3f}")
    print(f"  Threshold Dysregulation: {profile.threshold_dysregulation:.3f}")
    print(f"  Allostatic Failure Index: {profile.allostatic_failure_index:.3f}")
    print(f"  Ignition Threshold Shift: {profile.ignition_threshold_shift:+.3f}")
    print(f"\nAPGI Biotype Score: {profile.apgi_biotype_score:.3f}")
    print(f"Symptom Severity: {profile.symptom_severity:.1%}")


# =============================================================================
# Example 2: Generate Multiple Profiles and Analyze Distribution
# =============================================================================


def example_2_profile_distribution() -> None:
    """Generate multiple profiles and analyze their distribution"""
    print("\n" + "=" * 70)
    print("Example 2: Profile Distribution Analysis")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()

    # Generate 50 profiles for each psychosis type
    affective_profiles = []
    non_affective_profiles = []

    for _ in range(50):
        affective = analyzer.create_hcp_ep_profile(
            psychosis_type="affective",
            severity="moderate",
        )
        affective_profiles.append(affective)

        non_affective = analyzer.create_hcp_ep_profile(
            psychosis_type="non-affective",
            severity="moderate",
        )
        non_affective_profiles.append(non_affective)

    # Analyze biotype scores
    affective_biotypes = [p.apgi_biotype_score for p in affective_profiles]
    non_affective_biotypes = [p.apgi_biotype_score for p in non_affective_profiles]

    print("\nAffective Psychosis (N=50):")
    print(f"  Mean APGI Biotype: {np.mean(affective_biotypes):.3f}")
    print(f"  Std Dev: {np.std(affective_biotypes):.3f}")
    print(f"  Range: {np.min(affective_biotypes):.3f} - {np.max(affective_biotypes):.3f}")

    print("\nNon-Affective Psychosis (N=50):")
    print(f"  Mean APGI Biotype: {np.mean(non_affective_biotypes):.3f}")
    print(f"  Std Dev: {np.std(non_affective_biotypes):.3f}")
    print(f"  Range: {np.min(non_affective_biotypes):.3f} - {np.max(non_affective_biotypes):.3f}")

    # Statistical comparison
    t_stat = (np.mean(non_affective_biotypes) - np.mean(affective_biotypes)) / np.sqrt(
        np.var(affective_biotypes) / 50 + np.var(non_affective_biotypes) / 50
    )
    print(f"\nT-statistic (non-affective vs. affective): {t_stat:.3f}")


# =============================================================================
# Example 3: Compare Treatment Groups
# =============================================================================


def example_3_treatment_comparison() -> None:
    """Compare APGI measures across treatment groups"""
    print("\n" + "=" * 70)
    print("Example 3: Treatment Group Comparison")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()
    treatment_groups = ["antipsychotic_naive", "treated", "resistant"]

    for treatment in treatment_groups:
        profiles = []
        for _ in range(30):
            profile = analyzer.create_hcp_ep_profile(
                treatment_status=treatment,
                severity="moderate",
            )
            profiles.append(profile)

        biotypes = [p.apgi_biotype_score for p in profiles]
        connectivity = [p.connectivity_disruption for p in profiles]
        cognition = [p.cognitive_impairment for p in profiles]

        print(f"\n{treatment.replace('_', ' ').title()} (N=30):")
        print(f"  APGI Biotype: {np.mean(biotypes):.3f} ± {np.std(biotypes):.3f}")
        print(
            f"  Connectivity Disruption: {np.mean(connectivity):.1%} ± {np.std(connectivity):.1%}"
        )
        print(f"  Cognitive Impairment: {np.mean(cognition):.1%} ± {np.std(cognition):.1%}")


# =============================================================================
# Example 4: Severity Progression
# =============================================================================


def example_4_severity_progression() -> None:
    """Show how APGI measures change with symptom severity"""
    print("\n" + "=" * 70)
    print("Example 4: Severity Progression")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()
    severities = ["mild", "moderate", "severe"]

    for severity in severities:
        profiles = []
        for _ in range(30):
            profile = analyzer.create_hcp_ep_profile(
                severity=severity,
            )
            profiles.append(profile)

        biotypes = [p.apgi_biotype_score for p in profiles]
        panss_totals = [p.panss_total for p in profiles]
        precision_failures = [p.precision_gating_failure for p in profiles]

        print(f"\n{severity.capitalize()} Severity (N=30):")
        print(f"  PANSS Total: {np.mean(panss_totals):.1f} ± {np.std(panss_totals):.1f}")
        print(f"  APGI Biotype: {np.mean(biotypes):.3f} ± {np.std(biotypes):.3f}")
        print(
            f"  Precision Gating Failure: {np.mean(precision_failures):.3f} ± {np.std(precision_failures):.3f}"
        )


# =============================================================================
# Example 5: Psychosis Type Differences
# =============================================================================


def example_5_psychosis_type_differences() -> None:
    """Highlight differences between affective and non-affective psychosis"""
    print("\n" + "=" * 70)
    print("Example 5: Psychosis Type Differences")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()

    # Generate profiles for each type
    affective_profiles = [
        analyzer.create_hcp_ep_profile(psychosis_type="affective", severity="moderate")
        for _ in range(50)
    ]

    non_affective_profiles = [
        analyzer.create_hcp_ep_profile(psychosis_type="non-affective", severity="moderate")
        for _ in range(50)
    ]

    # Compare key measures
    print("\nAffective Psychosis (N=50):")
    print(f"  Mean PANSS Negative: {np.mean([p.panss_negative for p in affective_profiles]):.1f}")
    print(
        f"  Mean Cognitive Performance: {np.mean([p.cognitive_performance for p in affective_profiles]):.1%}"
    )
    print(f"  Mean APGI Biotype: {np.mean([p.apgi_biotype_score for p in affective_profiles]):.3f}")

    print("\nNon-Affective Psychosis (N=50):")
    print(
        f"  Mean PANSS Negative: {np.mean([p.panss_negative for p in non_affective_profiles]):.1f}"
    )
    print(
        f"  Mean Cognitive Performance: {np.mean([p.cognitive_performance for p in non_affective_profiles]):.1%}"
    )
    print(
        f"  Mean APGI Biotype: {np.mean([p.apgi_biotype_score for p in non_affective_profiles]):.3f}"
    )

    print("\nKey Differences:")
    print("  • Non-affective has higher negative symptoms")
    print("  • Affective has better cognitive performance")
    print("  • Non-affective has higher APGI biotype scores")


# =============================================================================
# Example 6: Generate Visualizations Programmatically
# =============================================================================


def example_6_generate_visualizations() -> None:
    """Generate visualizations programmatically"""
    print("\n" + "=" * 70)
    print("Example 6: Generate Visualizations")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()
    visualizer = HCPEPVisualizer(analyzer)

    # Generate each visualization type
    print("\nGenerating visualizations...")

    fig1 = visualizer.plot_apgi_biotype_distribution(n_samples=100)
    if fig1:
        print("✓ APGI Biotype Distribution plot created")
        # Save to HTML
        filepath = visualizer.renderer.render_figure_to_html(fig1, "biotype_dist.html")
        print(f"  Saved to: {filepath}")

    fig2 = visualizer.plot_precision_gating_failure_landscape(n_samples=50)
    if fig2:
        print("✓ Precision Gating Failure plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig2, "precision_gating.html")
        print(f"  Saved to: {filepath}")

    fig3 = visualizer.plot_symptom_connectivity_relationship(n_samples=100)
    if fig3:
        print("✓ Symptom-Connectivity plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig3, "symptom_connectivity.html")
        print(f"  Saved to: {filepath}")

    fig4 = visualizer.plot_treatment_response_prediction(n_samples=100)
    if fig4:
        print("✓ Treatment Response plot created")
        filepath = visualizer.renderer.render_figure_to_html(fig4, "treatment_response.html")
        print(f"  Saved to: {filepath}")


# =============================================================================
# Example 7: Dataset Information
# =============================================================================


def example_7_dataset_info() -> None:
    """Display comprehensive dataset information"""
    print("\n" + "=" * 70)
    print("Example 7: Dataset Information")
    print("=" * 70)

    analyzer = HCPEPAnalyzer()
    info = analyzer.get_dataset_info()

    print(f"\nDataset: {info['dataset_name']}")
    print(f"Title: {info['title']}")
    print(f"URL: {info['url']}")
    print(f"Sample Size: {info['sample_size']} participants")
    print(f"Age Range: {info['age_range'][0]}-{info['age_range'][1]} years")
    print(f"Access Status: {info['access_status']}")

    print("\nData Types:")
    for dtype in info["data_types"]:
        print(f"  • {dtype}")

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

    analyzer = HCPEPAnalyzer()
    profile = analyzer.create_hcp_ep_profile()

    # Convert to dictionary
    profile_dict = profile.to_dict()

    print("\nProfile as Dictionary:")
    for key, value in profile_dict.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HCP-EP Integration - Usage Examples")
    print("=" * 70)

    # Run all examples
    example_1_create_profile()
    example_2_profile_distribution()
    example_3_treatment_comparison()
    example_4_severity_progression()
    example_5_psychosis_type_differences()
    example_6_generate_visualizations()
    example_7_dataset_info()
    example_8_profile_to_dict()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
