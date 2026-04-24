"""
Comprehensive test suite for new APGI Framework components.

Tests for Cross-Species Validation, Clinical Biomarkers, and Threshold Detection Paradigm.
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import components to test
try:
    from apgi_framework.research.cross_species_validation import (
        CrossSpeciesSignature,
        CrossSpeciesValidator,
        NeuralSignatureType,
        Species,
        ValidationResult,
    )

    CROSS_SPECIES_AVAILABLE = True
except ImportError as e:
    CROSS_SPECIES_AVAILABLE = False
    print(f"Warning: Could not import cross-species validation: {e}")

try:
    from research.clinical_biomarkers.experiments.biomarker_analysis import (  # type: ignore[import-untyped, import-not-found]
        BiomarkerAnalyzer,
        BiomarkerType,
        ClinicalBiomarker,
        ClinicalCondition,
        PatientProfile,
    )

    CLINICAL_BIOMARKERS_AVAILABLE = True
except ImportError as e:
    CLINICAL_BIOMARKERS_AVAILABLE = False
    print(f"Warning: Could not import clinical biomarkers: {e}")

try:
    from apgi_framework.research.threshold_detection_paradigm import (
        ModalityType,
        StimulusParameters,
        ThresholdDetectionSystem,
        ThresholdMethod,
        TrialResponse,
    )

    THRESHOLD_DETECTION_AVAILABLE = True
except ImportError as e:
    THRESHOLD_DETECTION_AVAILABLE = False
    print(f"Warning: Could not import threshold detection paradigm: {e}")


@pytest.mark.skipif(not CROSS_SPECIES_AVAILABLE, reason="Cross-species validation not available")
class TestCrossSpeciesValidation:
    """Test suite for Cross-Species Validation component."""

    def test_validator_initialization(self):
        """Test CrossSpeciesValidator initialization."""
        validator = CrossSpeciesValidator(significance_threshold=0.01)

        assert validator.significance_threshold == 0.01
        assert len(validator.species_params) == 6  # All species initialized
        assert Species.HUMAN in validator.species_params
        assert Species.RODENT in validator.species_params

    def test_species_parameters(self):
        """Test species-specific parameters."""
        validator = CrossSpeciesValidator()

        # Test human parameters
        human_params = validator.species_params[Species.HUMAN]
        assert human_params.brain_mass_g == 1350
        assert human_params.heart_rate_bpm == 70
        assert human_params.temporal_scaling == 1.0

        # Test rodent parameters
        rodent_params = validator.species_params[Species.RODENT]
        assert rodent_params.brain_mass_g == 2.0
        assert rodent_params.heart_rate_bpm == 350
        assert rodent_params.temporal_scaling == 0.1

    def test_cross_species_signature_creation(self):
        """Test CrossSpeciesSignature creation and validation."""
        validator = CrossSpeciesValidator()

        # Create valid signature
        signature = CrossSpeciesSignature(
            species=Species.HUMAN,
            signature_type=NeuralSignatureType.P3B,
            participant_id="test_001",
            raw_data=np.random.randn(100),
            timestamps=np.linspace(0, 1, 100),
        )

        # Test signature validation
        validator.add_signature(signature)

        assert signature.amplitude is not None
        assert signature.latency is not None
        assert signature.frequency is not None

    def test_signature_validation_errors(self):
        """Test signature validation error handling."""
        validator = CrossSpeciesValidator()

        # Test invalid species
        with pytest.raises(Exception):
            invalid_signature = CrossSpeciesSignature(
                species="invalid_species",  # Invalid
                signature_type=NeuralSignatureType.P3B,
                participant_id="test_001",
                raw_data=np.random.randn(100),
                timestamps=np.linspace(0, 1, 100),
            )
            validator.add_signature(invalid_signature)

        # Test mismatched data lengths
        with pytest.raises(Exception):
            mismatched_signature = CrossSpeciesSignature(
                species=Species.HUMAN,
                signature_type=NeuralSignatureType.P3B,
                participant_id="test_001",
                raw_data=np.random.randn(100),
                timestamps=np.linspace(0, 1, 50),  # Different length
            )
            validator.add_signature(mismatched_signature)

    def test_amplitude_extraction(self):
        """Test amplitude extraction from different signature types."""
        validator = CrossSpeciesValidator()

        # Test P3B amplitude extraction
        p3b_signature = CrossSpeciesSignature(
            species=Species.HUMAN,
            signature_type=NeuralSignatureType.P3B,
            participant_id="test_001",
            raw_data=np.random.randn(1000),
            timestamps=np.linspace(0, 2, 1000),  # 2 second recording
        )

        amplitude = validator._extract_amplitude(p3b_signature)
        assert isinstance(amplitude, float)
        assert amplitude >= 0

        # Test gamma synchrony extraction
        gamma_signature = CrossSpeciesSignature(
            species=Species.HUMAN,
            signature_type=NeuralSignatureType.GAMMA_SYNC,
            participant_id="test_002",
            raw_data=np.random.randn(1000),
            timestamps=np.linspace(0, 1, 1000),
        )

        amplitude = validator._extract_amplitude(gamma_signature)
        assert isinstance(amplitude, float)
        assert amplitude >= 0

    def test_species_scaling(self):
        """Test species-specific scaling of features."""
        validator = CrossSpeciesValidator()

        # Test human scaling (should be identity)
        human_features = np.array([[1.0, 100.0, 40.0, 0.8, 0.9]])
        scaled_human = validator._apply_species_scaling(human_features, Species.HUMAN)

        np.testing.assert_array_almost_equal(human_features, scaled_human)

        # Test rodent scaling
        rodent_features = np.array([[1.0, 100.0, 40.0, 0.8, 0.9]])
        scaled_rodent = validator._apply_species_scaling(rodent_features, Species.RODENT)

        assert scaled_rodent[0, 0] == 0.1  # Amplitude scaling
        assert scaled_rodent[0, 1] == 10.0  # Temporal scaling
        assert scaled_rodent[0, 2] == 80.0  # Frequency scaling

    def test_validation_result_creation(self):
        """Test ValidationResult creation and properties."""
        result = ValidationResult(
            signature_type=NeuralSignatureType.P3B,
            species_comparison=(Species.HUMAN, Species.RODENT),
            correlation_coefficient=0.75,
            p_value=0.01,
            effect_size=1.2,
            temporal_similarity=0.8,
            amplitude_similarity=0.7,
            frequency_similarity=0.9,
            validation_score=0.8,
            significance_threshold=0.05,
        )

        assert result.is_significant
        assert result.signature_type == NeuralSignatureType.P3B
        assert result.species_comparison == (Species.HUMAN, Species.RODENT)
        assert result.validation_score == 0.8

    def test_validation_score_computation(self):
        """Test validation score computation."""
        validator = CrossSpeciesValidator()

        score = validator._compute_validation_score(
            correlation=0.8, temporal_sim=0.7, amplitude_sim=0.9, frequency_sim=0.6
        )

        assert 0 <= score <= 1
        # Weighted average: 0.4*0.8 + 0.2*0.7 + 0.2*0.9 + 0.2*0.6 = 0.76
        expected_score = 0.4 * 0.8 + 0.2 * 0.7 + 0.2 * 0.9 + 0.2 * 0.6
        assert abs(score - expected_score) < 0.001


@pytest.mark.skipif(not CLINICAL_BIOMARKERS_AVAILABLE, reason="Clinical biomarkers not available")
class TestClinicalBiomarkers:
    """Test suite for Clinical Biomarkers component."""

    def test_analyzer_initialization(self):
        """Test BiomarkerAnalyzer initialization."""
        analyzer = BiomarkerAnalyzer(significance_threshold=0.01)

        assert analyzer.significance_threshold == 0.01
        assert len(analyzer.classifiers) == 3
        assert "random_forest" in analyzer.classifiers
        assert len(analyzer.biomarkers) > 0  # Known biomarkers initialized

    def test_known_biomarkers_initialization(self):
        """Test initialization of known biomarkers."""
        analyzer = BiomarkerAnalyzer()

        # Check that key biomarkers are initialized
        assert "p3b_depression" in analyzer.biomarkers
        assert "hrv_anxiety" in analyzer.biomarkers
        assert "gamma_schizophrenia" in analyzer.biomarkers

        # Check biomarker properties
        p3b_biomarker = analyzer.biomarkers["p3b_depression"]
        assert p3b_biomarker.biomarker_type == BiomarkerType.NEURAL_SIGNATURE
        assert ClinicalCondition.MAJOR_DEPRESSION in p3b_biomarker.target_conditions

    def test_patient_profile_validation(self):
        """Test patient profile validation."""
        analyzer = BiomarkerAnalyzer()

        # Valid patient profile
        valid_patient = PatientProfile(
            patient_id="test_001",
            age=25,
            sex="M",
            clinical_condition=ClinicalCondition.MAJOR_DEPRESSION,
            severity_score=0.7,
            p3b_amplitude_extero=5.0,
            hrv_rmssd=50.0,
        )

        analyzer.add_patient_data(valid_patient)  # Should not raise exception

        # Invalid age
        invalid_patient = PatientProfile(
            patient_id="test_002",
            age=150,  # Invalid age
            sex="F",
            clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
            severity_score=0.0,
        )

        with pytest.raises(Exception):
            analyzer.add_patient_data(invalid_patient)

    def test_biomarker_discovery(self):
        """Test biomarker discovery process."""
        analyzer = BiomarkerAnalyzer()

        # Create mock patient data
        cases = [
            PatientProfile(
                patient_id=f"case_{i}",
                age=30 + i,
                sex="M",
                clinical_condition=ClinicalCondition.MAJOR_DEPRESSION,
                severity_score=0.6 + i * 0.05,
                p3b_amplitude_extero=3.0 - i * 0.1,  # Lower in depression
                hrv_rmssd=40.0 - i * 2.0,  # Lower HRV in depression
            )
            for i in range(15)
        ]

        controls = [
            PatientProfile(
                patient_id=f"control_{i}",
                age=30 + i,
                sex="M",
                clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
                severity_score=0.0,
                p3b_amplitude_extero=6.0 + i * 0.1,  # Normal range
                hrv_rmssd=60.0 + i * 2.0,  # Normal HRV
            )
            for i in range(15)
        ]

        all_patients = cases + controls

        # Discover biomarkers
        discovered = analyzer.discover_biomarkers(all_patients, ClinicalCondition.MAJOR_DEPRESSION)

        assert len(discovered) > 0
        assert all(isinstance(b, ClinicalBiomarker) for b in discovered)

    def test_feature_biomarker_creation(self):
        """Test creation of biomarkers from individual features."""
        analyzer = BiomarkerAnalyzer()

        # Mock case and control values
        case_values = [3.0, 3.2, 2.8, 3.1, 2.9]  # Lower values
        control_values = [6.0, 6.2, 5.8, 6.1, 5.9]  # Higher values

        biomarker = analyzer._create_feature_biomarker(
            "p3b_amplitude_extero",
            case_values,
            control_values,
            ClinicalCondition.MAJOR_DEPRESSION,
            BiomarkerType.NEURAL_SIGNATURE,
        )

        assert biomarker is not None
        assert biomarker.biomarker_type == BiomarkerType.NEURAL_SIGNATURE
        assert ClinicalCondition.MAJOR_DEPRESSION in biomarker.target_conditions
        assert len(biomarker.features) == 1

        feature = biomarker.features[0]
        assert feature.name == "p3b_amplitude_extero"
        assert feature.effect_size < 0  # Negative effect size (lower in cases)
        assert feature.p_value < 0.05

    def test_biomarker_validation(self):
        """Test biomarker validation on independent data."""
        analyzer = BiomarkerAnalyzer()

        # Create a test biomarker
        biomarker = ClinicalBiomarker(
            name="Test Biomarker",
            biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
            category=BiomarkerType.DIAGNOSTIC,
            target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
        )

        # Add a feature
        from research.clinical_biomarkers.experiments.biomarker_analysis import (
            BiomarkerFeature,
        )

        biomarker.features.append(
            BiomarkerFeature(
                name="test_feature",
                value=5.0,
                reference_range=(3.0, 7.0),
                clinical_significance=0.8,
                reliability=0.9,
                validity=0.85,
                effect_size=1.0,
                confidence_interval=(0.5, 1.5),
                p_value=0.01,
                interpretation="Test feature",
                clinical_actionability=0.7,
            )
        )

        # Create validation patients
        validation_patients = [
            PatientProfile(
                patient_id=f"val_{i}",
                age=30 + i,
                sex="F",
                clinical_condition=(
                    ClinicalCondition.MAJOR_DEPRESSION
                    if i < 10
                    else ClinicalCondition.HEALTHY_CONTROL
                ),
                severity_score=0.5 if i < 10 else 0.0,
                p3b_amplitude_extero=4.0 if i < 10 else 6.0,
            )
            for i in range(20)
        ]

        # Validate biomarker
        validated_biomarker = analyzer.validate_biomarker(biomarker, validation_patients)

        assert validated_biomarker.auc_score >= 0.0
        assert validated_biomarker.sensitivity >= 0.0
        assert validated_biomarker.specificity >= 0.0
        assert validated_biomarker.clinical_validity >= 0.0

    def test_patient_classification(self):
        """Test patient classification using biomarkers."""
        analyzer = BiomarkerAnalyzer()

        # Create test biomarker
        biomarker = ClinicalBiomarker(
            name="Classification Test",
            biomarker_type=BiomarkerType.NEURAL_SIGNATURE,
            category=BiomarkerType.DIAGNOSTIC,
            target_conditions=[ClinicalCondition.MAJOR_DEPRESSION],
        )

        # Add feature
        from research.clinical_biomarkers.experiments.biomarker_analysis import (
            BiomarkerFeature,
        )

        biomarker.features.append(
            BiomarkerFeature(
                name="p3b_amplitude_extero",
                value=5.0,
                reference_range=(3.0, 7.0),
                clinical_significance=0.8,
                reliability=0.9,
                validity=0.85,
                effect_size=1.0,
                confidence_interval=(0.5, 1.5),
                p_value=0.01,
                interpretation="Test feature",
                clinical_actionability=0.7,
            )
        )

        # Create test patients
        test_patients = [
            PatientProfile(
                patient_id=f"class_{i}",
                age=30,
                sex="M",
                clinical_condition=ClinicalCondition.HEALTHY_CONTROL,
                severity_score=0.0,
                p3b_amplitude_extero=5.0 + i * 0.5,
            )
            for i in range(10)
        ]

        # Classify patients
        results = analyzer.classify_patients(test_patients, biomarker)

        assert len(results) == 10
        for patient_id, result in results.items():
            assert "predicted_condition" in result
            assert "probability" in result
            assert "confidence" in result
            assert "biomarker_score" in result
            assert "features_used" in result


@pytest.mark.skipif(not THRESHOLD_DETECTION_AVAILABLE, reason="Threshold detection not available")
class TestThresholdDetectionParadigm:
    """Test suite for Threshold Detection Paradigm component."""

    def test_system_initialization(self):
        """Test ThresholdDetectionSystem initialization."""
        system = ThresholdDetectionSystem(significance_threshold=0.01)

        assert system.significance_threshold == 0.01
        assert len(system.psychometric_functions) == 3
        assert "cumulative_gaussian" in system.psychometric_functions
        assert "weibull" in system.psychometric_functions
        assert "logistic" in system.psychometric_functions

    def test_stimulus_parameters(self):
        """Test StimulusParameters creation and serialization."""
        stim_params = StimulusParameters(
            modality=ModalityType.VISUAL,
            intensity=5.0,
            duration=100.0,
            frequency=10.0,
            contrast=0.8,
            gabor_orientation=45.0,
        )

        assert stim_params.modality == ModalityType.VISUAL
        assert stim_params.intensity == 5.0
        assert stim_params.duration == 100.0

        # Test serialization
        params_dict = stim_params.to_dict()
        assert "modality" in params_dict
        assert params_dict["modality"] == "visual"
        assert params_dict["intensity"] == 5.0

    def test_trial_response_creation(self):
        """Test TrialResponse creation."""
        stim_params = StimulusParameters(
            modality=ModalityType.AUDITORY,
            intensity=50.0,
            duration=200.0,
            frequency=1000.0,
        )

        trial = TrialResponse(
            trial_id="test_trial",
            timestamp=datetime.now(),
            stimulus_params=stim_params,
            detection=True,
            confidence=0.8,
            reaction_time=350.0,
            consciousness_level="clear_awareness",
            p3b_amplitude=5.2,
            gamma_power=1.8,
            pupil_dilation=0.3,
        )

        assert trial.detection
        assert trial.confidence == 0.8
        assert trial.p3b_amplitude == 5.2
        assert trial.gamma_power == 1.8

    def test_psychometric_function_fitting(self):
        """Test psychometric function fitting."""
        system = ThresholdDetectionSystem()
        psych_func = system.psychometric_functions["cumulative_gaussian"]

        # Generate test data
        intensities = np.linspace(0, 10, 50)
        true_alpha, true_beta = 5.0, 1.0
        responses = psych_func.cumulative_gaussian(intensities, true_alpha, true_beta, 0.5, 0.05)
        binary_responses = np.random.random(len(responses)) < responses

        # Fit function
        fit_result = psych_func.fit_function(intensities, binary_responses)

        assert "parameters" in fit_result
        assert "r_squared" in fit_result
        assert "aic" in fit_result
        assert "bic" in fit_result

        # Check parameter estimates
        params = fit_result["parameters"]
        assert "alpha" in params
        assert "beta" in params
        assert "gamma" in params
        assert "lambda" in params

        # Check goodness of fit
        assert 0 <= fit_result["r_squared"] <= 1

    def test_adaptive_staircase(self):
        """Test adaptive staircase procedure."""
        from apgi_framework.research.threshold_detection_paradigm import (
            AdaptiveStaircase,
        )

        staircase = AdaptiveStaircase(
            start_intensity=5.0, step_size=0.5, rule="3up_1down", max_trials=20
        )

        assert staircase.current_intensity == 5.0
        assert staircase.up_count == 3
        assert staircase.down_count == 1

        # Test staircase updates
        for i in range(10):
            _ = staircase.get_next_intensity()
            response = i < 5  # First 5 are correct, last 5 are incorrect
            staircase.update_staircase(response)

        assert len(staircase.intensity_history) == 10
        assert len(staircase.response_history) == 10
        assert staircase.trial_count == 10

    def test_threshold_estimation(self):
        """Test complete threshold estimation process."""
        system = ThresholdDetectionSystem()

        # Run threshold estimation
        estimate = system.run_threshold_estimation(
            modality=ModalityType.VISUAL,
            method=ThresholdMethod.ADAPTIVE_STAIRCASE,
            n_trials=50,
        )

        assert estimate.modality == ModalityType.VISUAL
        assert estimate.method == ThresholdMethod.ADAPTIVE_STAIRCASE
        assert estimate.threshold_value >= 0
        assert len(estimate.confidence_interval) == 2
        assert (
            estimate.confidence_interval[0]
            <= estimate.threshold_value
            <= estimate.confidence_interval[1]
        )
        assert estimate.n_trials == 50
        assert 0 <= estimate.goodness_of_fit <= 1

    def test_cross_modal_comparison(self):
        """Test cross-modal threshold comparison."""
        system = ThresholdDetectionSystem()

        # Run threshold estimation for two modalities
        estimate1 = system.run_threshold_estimation(
            modality=ModalityType.VISUAL,
            method=ThresholdMethod.ADAPTIVE_STAIRCASE,
            n_trials=30,
        )

        estimate2 = system.run_threshold_estimation(
            modality=ModalityType.AUDITORY,
            method=ThresholdMethod.ADAPTIVE_STAIRCASE,
            n_trials=30,
        )

        # Compare cross-modal thresholds
        comparison = system.compare_cross_modal_thresholds(
            ModalityType.VISUAL, ModalityType.AUDITORY
        )

        assert comparison.primary_modality == ModalityType.VISUAL
        assert comparison.comparison_modality == ModalityType.AUDITORY
        assert comparison.primary_threshold == estimate1.threshold_value
        assert comparison.comparison_threshold == estimate2.threshold_value
        assert comparison.sensitivity_ratio > 0
        assert -1 <= comparison.cross_modal_correlation <= 1

    def test_neural_validation(self):
        """Test neural validation of thresholds."""
        system = ThresholdDetectionSystem()

        # Create mock trial data with neural responses
        trial_data = []
        for i in range(20):
            stim_params = StimulusParameters(
                modality=ModalityType.VISUAL, intensity=i * 0.5, duration=100.0
            )

            trial = TrialResponse(
                trial_id=f"neural_test_{i}",
                timestamp=datetime.now(),
                stimulus_params=stim_params,
                detection=i > 10,  # Detection after threshold
                confidence=0.5 + (i > 10) * 0.3,
                reaction_time=300 + np.random.normal(0, 50),
                consciousness_level="clear_awareness" if i > 10 else "no_awareness",
                p3b_amplitude=5.0 if i > 10 else 1.0 + np.random.normal(0, 0.5),
                gamma_power=2.0 if i > 10 else 0.5 + np.random.normal(0, 0.2),
            )
            trial_data.append(trial)

        # Test neural validation
        correlation, neural_threshold = system._validate_with_neural_data(trial_data)

        assert -1 <= correlation <= 1
        assert neural_threshold is None or neural_threshold >= 0

    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation."""
        system = ThresholdDetectionSystem()

        # Mock data
        intensities = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        responses = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 1])
        threshold = 5.0

        ci_lower, ci_upper = system._calculate_confidence_interval(
            intensities, responses, threshold
        )

        assert ci_lower <= threshold <= ci_upper
        assert ci_lower >= 0
        assert ci_upper >= threshold

    def test_report_generation(self):
        """Test threshold detection report generation."""
        system = ThresholdDetectionSystem()

        # Run some estimations
        system.run_threshold_estimation(
            ModalityType.VISUAL, ThresholdMethod.ADAPTIVE_STAIRCASE, n_trials=20
        )
        system.run_threshold_estimation(
            ModalityType.AUDITORY, ThresholdMethod.ADAPTIVE_STAIRCASE, n_trials=20
        )

        # Generate report
        report = system.generate_threshold_report()

        assert "Threshold Detection Paradigm Report" in report
        assert "THRESHOLD ESTIMATES" in report
        assert "visual" in report.lower()
        assert "auditory" in report.lower()
        assert len(report) > 100  # Reasonable length


@pytest.mark.skipif(
    not (CROSS_SPECIES_AVAILABLE and CLINICAL_BIOMARKERS_AVAILABLE),
    reason="Both cross-species and clinical biomarkers required",
)
class TestIntegration:
    """Integration tests for all new components."""

    def test_cross_species_clinical_integration(self):
        """Test integration between cross-species validation and clinical biomarkers."""
        # This would test how cross-species findings inform clinical biomarker development
        # For now, just test that both components can be used together

        cross_species_validator = CrossSpeciesValidator()
        biomarker_analyzer = BiomarkerAnalyzer()

        # Both should initialize without conflicts
        assert cross_species_validator is not None
        assert biomarker_analyzer is not None
        assert len(cross_species_validator.species_params) > 0
        assert len(biomarker_analyzer.biomarkers) > 0

    @pytest.mark.skipif(
        not (CLINICAL_BIOMARKERS_AVAILABLE and THRESHOLD_DETECTION_AVAILABLE),
        reason="Both clinical biomarkers and threshold detection required",
    )
    def test_threshold_clinical_integration(self):
        """Test integration between threshold detection and clinical biomarkers."""
        # Test how threshold measurements can be used as clinical biomarkers

        threshold_system = ThresholdDetectionSystem()
        biomarker_analyzer = BiomarkerAnalyzer()

        # Both should work independently
        assert threshold_system is not None
        assert biomarker_analyzer is not None

        # Threshold estimation should produce data that could inform biomarkers
        estimate = threshold_system.run_threshold_estimation(
            ModalityType.VISUAL, ThresholdMethod.ADAPTIVE_STAIRCASE, n_trials=20
        )

        assert estimate.threshold_value >= 0
        assert estimate.neural_correlation >= -1 and estimate.neural_correlation <= 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
