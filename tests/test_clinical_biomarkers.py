"""
Extended tests for Clinical Biomarkers component.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import clinical biomarkers components
try:
    from research.clinical_biomarkers.experiments.biomarker_analysis import (  # type: ignore[import-untyped, import-not-found]
        BiomarkerAnalyzer,
        BiomarkerCategory,
        BiomarkerFeature,
        BiomarkerType,
        ClinicalBiomarker,
        ClinicalCondition,
        PatientProfile,
    )

    CLINICAL_BIOMARKERS_AVAILABLE = True
except ImportError as e:
    CLINICAL_BIOMARKERS_AVAILABLE = False
    IMPORT_ERROR_CLINICAL = e


class TestClinicalBiomarkersExtended:
    """Extended tests for Clinical Biomarkers."""

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_all_clinical_conditions(self):
        """Test handling of all clinical conditions."""
        analyzer = BiomarkerAnalyzer()

        for condition in ClinicalCondition:
            # Create patient for each condition
            patient = PatientProfile(
                patient_id=f"test_{condition.value}",
                age=30,
                sex="M",
                clinical_condition=condition,
                severity_score=(0.5 if condition != ClinicalCondition.HEALTHY_CONTROL else 0.0),
            )

            # Should be able to add patient without error
            analyzer.add_patient_data(patient)

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_all_biomarker_types(self):
        """Test all biomarker types."""
        for biomarker_type in BiomarkerType:
            biomarker = ClinicalBiomarker(
                name=f"Test {biomarker_type.value}",
                biomarker_type=biomarker_type,
                category=BiomarkerCategory.DIAGNOSTIC,
                target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
            )

            assert biomarker.biomarker_type == biomarker_type
            assert biomarker.category == BiomarkerCategory.DIAGNOSTIC

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_biomarker_categories(self):
        """Test all biomarker categories."""
        for category in BiomarkerCategory:
            biomarker = ClinicalBiomarker(
                name=f"Test {category.value}",
                biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
                category=category,
                target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
            )

            assert biomarker.category == category

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_comprehensive_feature_analysis(self):
        """Test comprehensive feature analysis for all feature types."""
        analyzer = BiomarkerAnalyzer()

        # Create comprehensive patient data
        cases = [
            PatientProfile(
                patient_id=f"comprehensive_case_{i}",
                age=25 + i,
                sex=["M", "F"][i % 2],
                clinical_condition=ClinicalCondition.GENERALIZED_ANXIETY,
                severity_score=0.4 + i * 0.03,
                # Neural signatures
                p3b_amplitude_extero=4.0 - i * 0.05,
                p3b_amplitude_intero=3.5 - i * 0.04,
                p3b_latency_extero=320 + i * 2,
                p3b_latency_intero=340 + i * 3,
                gamma_power_frontal=1.5 - i * 0.02,
                gamma_power_posterior=1.8 - i * 0.03,
                gamma_coherence=0.6 - i * 0.01,
                microstate_duration=80 + i * 1,
                microstate_transitions=12 - i * 0.1,
                # Pupillometry
                pupil_diameter_intero=3.0 + i * 0.02,
                pupil_diameter_extero=2.8 + i * 0.01,
                pupil_latency_intero=250 - i * 2,
                pupil_latency_extero=230 - i * 1,
                # Cardiac metrics
                hrv_rmssd=35.0 - i * 1.0,
                hrv_hf_power=0.3 - i * 0.01,
                heart_rate=85 + i * 1,
                # Behavioral metrics
                reaction_time=400 + i * 10,
                accuracy=0.7 - i * 0.01,
                confidence_rating=0.6 - i * 0.02,
                # Clinical questionnaires
                anxiety_score=15 + i * 2,
                depression_score=8 + i * 1,
                ptsd_score=5 + i * 0.5,
            )
            for i in range(20)
        ]

        controls = [
            PatientProfile(
                patient_id=f"comprehensive_control_{i}",
                age=25 + i,
                sex=["M", "F"][i % 2],
                clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
                severity_score=0.0,
                # Normal ranges
                p3b_amplitude_extero=6.0 + i * 0.02,
                p3b_amplitude_intero=5.5 + i * 0.01,
                p3b_latency_extero=300 + i * 1,
                p3b_latency_intero=320 + i * 1,
                gamma_power_frontal=2.0 + i * 0.01,
                gamma_power_posterior=2.3 + i * 0.02,
                gamma_coherence=0.8 + i * 0.01,
                microstate_duration=90 + i * 0.5,
                microstate_transitions=10 + i * 0.05,
                pupil_diameter_intero=2.5 + i * 0.01,
                pupil_diameter_extero=2.3 + i * 0.01,
                pupil_latency_intero=200 + i * 1,
                pupil_latency_extero=180 + i * 1,
                hrv_rmssd=50.0 + i * 1.5,
                hrv_hf_power=0.5 + i * 0.02,
                heart_rate=70 + i * 0.5,
                reaction_time=300 + i * 5,
                accuracy=0.9 - i * 0.005,
                confidence_rating=0.8 - i * 0.01,
                anxiety_score=2 + i * 0.5,
                depression_score=1 + i * 0.2,
                ptsd_score=1 + i * 0.1,
            )
            for i in range(20)
        ]

        all_patients = cases + controls

        # Discover biomarkers
        discovered = analyzer.discover_biomarkers(
            all_patients, ClinicalCondition.GENERALIZED_ANXIETY
        )

        assert len(discovered) > 0

        # Check that different biomarker types are discovered
        discovered_types = {b.biomarker_type for b in discovered}
        assert len(discovered_types) > 1  # Should discover multiple types

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_biomarker_validation_statistics(self):
        """Test statistical validation of biomarkers."""
        analyzer = BiomarkerAnalyzer()

        # Create biomarker with known properties
        biomarker = ClinicalBiomarker(
            name="Statistical Test",
            biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
            category=BiomarkerCategory.DIAGNOSTIC,
            target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
        )

        # Add feature with known statistics
        biomarker.features.append(
            BiomarkerFeature(
                name="statistical_feature",
                value=5.0,
                reference_range=(3.0, 7.0),
                clinical_significance=0.9,
                reliability=0.95,
                validity=0.9,
                effect_size=1.5,
                confidence_interval=(1.0, 2.0),
                p_value=0.001,
                interpretation="Strong effect",
                clinical_actionability=0.8,
            )
        )

        # Create validation data with clear separation
        validation_patients = []
        for i in range(30):
            if i < 15:  # Cases
                patient = PatientProfile(
                    patient_id=f"stat_case_{i}",
                    age=30 + i,
                    sex="F",
                    clinical_condition=ClinicalCondition.MAJOR_DEPRESSION,
                    severity_score=0.6,
                    statistical_feature=3.0,  # Lower in cases
                )
            else:  # Controls
                patient = PatientProfile(
                    patient_id=f"stat_control_{i - 15}",
                    age=30 + i,
                    sex="F",
                    clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
                    severity_score=0.0,
                    statistical_feature=7.0,  # Higher in controls
                )
            validation_patients.append(patient)

        # Validate biomarker
        validated = analyzer.validate_biomarker(biomarker, validation_patients)

        # Should show good performance
        assert validated.auc_score > 0.7
        assert validated.sensitivity > 0.5
        assert validated.specificity > 0.5
        assert validated.clinical_validity > 0.5

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_multi_condition_biomarkers(self):
        """Test biomarkers that work across multiple conditions."""
        analyzer = BiomarkerAnalyzer()

        # Create biomarker for multiple anxiety disorders
        multi_condition_biomarker = ClinicalBiomarker(
            name="Anxiety Spectrum Biomarker",
            biomarker_type=BiomarkerType.HEART_RATE_VARIABILITY,
            category=BiomarkerCategory.SCREENING,
            target_conditions=[
                ClinicalCondition.GENERALIZED_ANXIETY,
                ClinicalCondition.PANIC_DISORDER,
                ClinicalCondition.SOCIAL_ANXIETY,
                ClinicalCondition.PTSD,
            ],
        )

        # Add HRV feature
        multi_condition_biomarker.features.append(
            BiomarkerFeature(
                name="hrv_rmssd",
                value=35.0,
                reference_range=(40.0, 80.0),
                clinical_significance=0.7,
                reliability=0.85,
                validity=0.8,
                effect_size=-0.8,  # Lower HRV in anxiety
                confidence_interval=(-1.2, -0.4),
                p_value=0.01,
                interpretation="Reduced HRV across anxiety disorders",
                clinical_actionability=0.6,
            )
        )

        # Test with multiple conditions
        validation_patients = []
        conditions = [
            ClinicalCondition.GENERALIZED_ANXIETY,
            ClinicalCondition.PANIC_DISORDER,
            ClinicalCondition.SOCIAL_ANXIETY,
            ClinicalCondition.PTSD,
            ClinicalCondition.HEALTHY_CONTROL,
        ]

        for condition in conditions:
            for i in range(10):
                if condition == ClinicalCondition.HEALTHY_CONTROL:
                    hrv_value = 60.0 + np.random.normal(0, 5)
                else:
                    hrv_value = 35.0 + np.random.normal(0, 5)

                patient = PatientProfile(
                    patient_id=f"multi_{condition.value}_{i}",
                    age=30 + i,
                    sex="M",
                    clinical_condition=condition,
                    severity_score=(0.5 if condition != ClinicalCondition.HEALTHY_CONTROL else 0.0),
                    hrv_rmssd=hrv_value,
                )
                validation_patients.append(patient)

        # Validate multi-condition biomarker
        validated = analyzer.validate_biomarker(multi_condition_biomarker, validation_patients)

        # Should work for multiple conditions
        assert validated.auc_score > 0.5
        assert len(validated.target_conditions) == 4

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_biomarker_report_generation(self):
        """Test comprehensive biomarker report generation."""
        analyzer = BiomarkerAnalyzer()

        # Create multiple biomarkers with different performance levels
        biomarkers = []

        # High performance biomarker
        high_perf = ClinicalBiomarker(
            name="High Performance Biomarker",
            biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
            category=BiomarkerCategory.DIAGNOSTIC,
            target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
            auc_score=0.92,
            sensitivity=0.88,
            specificity=0.90,
            clinical_validity=0.89,
            clinical_utility=0.91,
            implementation_feasibility=0.85,
        )
        biomarkers.append(high_perf)

        # Moderate performance biomarker
        mod_perf = ClinicalBiomarker(
            name="Moderate Performance Biomarker",
            biomarker_type=BiomarkerType.HEART_RATE_VARIABILITY,
            category=BiomarkerCategory.MONITORING,
            target_conditions=[ClinicalCondition.GENERALIZED_ANXIETY],
            auc_score=0.75,
            sensitivity=0.72,
            specificity=0.78,
            clinical_validity=0.75,
            clinical_utility=0.73,
            implementation_feasibility=0.90,
        )
        biomarkers.append(mod_perf)

        # Low performance biomarker
        low_perf = ClinicalBiomarker(
            name="Low Performance Biomarker",
            biomarker_type=BiomarkerType.PUPILLOMETRY,
            category=BiomarkerCategory.SCREENING,
            target_conditions=[ClinicalCondition.ADHD],
            auc_score=0.62,
            sensitivity=0.58,
            specificity=0.66,
            clinical_validity=0.62,
            clinical_utility=0.60,
            implementation_feasibility=0.95,
        )
        biomarkers.append(low_perf)

        # Generate report
        report = analyzer.generate_biomarker_report(biomarkers)

        # Check report content
        assert "Clinical Biomarker Analysis Report" in report
        assert "SUMMARY" in report
        assert "Total biomarkers analyzed: 3" in report
        assert "High performance (AUC ≥ 0.8): 1" in report
        assert "Moderate performance (0.7 ≤ AUC < 0.8): 1" in report
        assert "Low performance (AUC < 0.7): 1" in report

        # Check detailed biomarker information
        assert "High Performance Biomarker" in report
        assert "Moderate Performance Biomarker" in report
        assert "Low Performance Biomarker" in report

        # Check performance metrics
        assert "AUC Score: 0.92" in report
        assert "AUC Score: 0.75" in report
        assert "AUC Score: 0.62" in report

        # Check clinical utility section
        assert "Clinical Validity: 0.89" in report
        assert "Clinical Utility: 0.91" in report
        assert "Implementation Feasibility: 0.85" in report

    @pytest.mark.skipif(
        not CLINICAL_BIOMARKERS_AVAILABLE,
        reason=f"Clinical biomarkers not available: {IMPORT_ERROR_CLINICAL if not CLINICAL_BIOMARKERS_AVAILABLE else ''}",
    )
    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling."""
        analyzer = BiomarkerAnalyzer()

        # Test with empty patient list
        with pytest.raises(Exception):
            analyzer.discover_biomarkers([], ClinicalCondition.MAJOR_DEPRESSION)

        # Test with insufficient data
        few_cases = [
            PatientProfile(
                patient_id="few_cases",
                age=30,
                sex="M",
                clinical_condition=ClinicalCondition.MAJOR_DEPRESSION,
                severity_score=0.5,
            )
        ]

        few_controls = [
            PatientProfile(
                patient_id="few_controls",
                age=30,
                sex="M",
                clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
                severity_score=0.0,
            )
        ]

        with pytest.raises(Exception):
            analyzer.discover_biomarkers(
                few_cases + few_controls, ClinicalCondition.MAJOR_DEPRESSION
            )

        # Test biomarker validation with insufficient data
        biomarker = ClinicalBiomarker(
            name="Insufficient Data Test",
            biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
            category=BiomarkerCategory.DIAGNOSTIC,
            target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
        )

        insufficient_validation = [
            PatientProfile(
                patient_id="insufficient_val",
                age=30,
                sex="F",
                clinical_condition=ClinicalCondition.MAJOR_DEPRESSION,
                severity_score=0.5,
            )
        ]

        # Should handle insufficient data gracefully
        result = analyzer.validate_biomarker(biomarker, insufficient_validation)
        assert result is not None  # Should return biomarker even with limited data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
