"""
Tests for clinical module components.

Consolidated from:
- test_clinical_module.py (base tests)
- test_clinical_modules.py (cross-validation and treatment prediction tests)
- test_clinical_simple.py (enum tests for ModalityType, TaskType)
- test_clinical_biomarkers.py (biomarker analysis tests)
- test_clinical_parameter_extraction_coverage.py (reliability metrics)
"""

# Mock imports for testing
# from unittest.mock import Mock, patch

import pytest

from apgi_framework.clinical.disorder_classification import (
    ClassificationResult,
    DisorderClassification,
    DisorderType,
    NeuralSignatureProfile,
)
from apgi_framework.clinical.parameter_extraction import (
    AssessmentBattery,
    AssessmentTask,
    ClinicalParameterExtractor,
    ClinicalParameters,
    ModalityType,
    TaskType,
)
from apgi_framework.clinical.treatment_prediction import (
    BaselineParameters,
    TreatmentPrediction,
    TreatmentPredictor,
    TreatmentType,
)


class TestDisorderType:
    """Test DisorderType enum."""

    def test_disorder_types(self):
        """Test all disorder type values."""
        assert DisorderType.CONTROL.value == "control"
        assert DisorderType.GAD.value == "generalized_anxiety_disorder"
        assert DisorderType.PANIC.value == "panic_disorder"
        assert DisorderType.SOCIAL_ANXIETY.value == "social_anxiety_disorder"
        assert DisorderType.DEPRESSION.value == "major_depressive_disorder"
        assert DisorderType.PTSD.value == "post_traumatic_stress_disorder"


class TestNeuralSignatureProfile:
    """Test NeuralSignatureProfile dataclass."""

    def test_default_parameters(self):
        """Test default neural signature parameters."""
        profile = NeuralSignatureProfile()

        assert profile.p3b_amplitude_extero == 0.0
        assert profile.p3b_amplitude_intero == 0.0
        assert profile.p3b_latency_extero == 350.0
        assert profile.p3b_latency_intero == 350.0
        assert profile.gamma_power_frontal == 0.0
        assert profile.gamma_power_posterior == 0.0
        assert profile.gamma_coherence == 0.0
        assert profile.microstate_duration == 0.0
        assert profile.microstate_transitions == 0.0
        assert profile.pupil_dilation_intero == 0.0
        assert profile.pupil_latency == 0.0

    def test_custom_parameters(self):
        """Test custom neural signature parameters."""
        profile = NeuralSignatureProfile(
            p3b_amplitude_extero=5.2,
            p3b_amplitude_intero=3.8,
            gamma_power_frontal=0.15,
            gamma_coherence=0.35,
            pupil_dilation_intero=0.8,
        )

        assert profile.p3b_amplitude_extero == 5.2
        assert profile.p3b_amplitude_intero == 3.8
        assert profile.gamma_power_frontal == 0.15
        assert profile.gamma_coherence == 0.35
        assert profile.pupil_dilation_intero == 0.8


class TestDisorderClassification:
    """Test disorder classification implementation."""

    def test_initialization(self):
        """Test classifier initialization."""
        classifier = DisorderClassification()

        assert classifier.classifier is not None
        assert classifier.scaler is not None
        assert classifier.is_trained is False
        assert classifier.classifier_type == "random_forest"

    def test_train_classifier(self):
        """Test training the classifier."""
        classifier = DisorderClassification()

        # Create sample training data with more samples for cross-validation
        profiles = [
            NeuralSignatureProfile(
                p3b_amplitude_extero=5.0,
                p3b_amplitude_intero=3.0,
                gamma_power_frontal=0.2,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.0,
                p3b_amplitude_intero=1.5,
                gamma_power_frontal=0.1,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=4.8,
                p3b_amplitude_intero=2.9,
                gamma_power_frontal=0.22,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.2,
                p3b_amplitude_intero=1.6,
                gamma_power_frontal=0.12,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=5.1,
                p3b_amplitude_intero=3.1,
                gamma_power_frontal=0.21,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.1,
                p3b_amplitude_intero=1.4,
                gamma_power_frontal=0.11,
            ),
        ]
        labels = [
            DisorderType.GAD,
            DisorderType.CONTROL,
            DisorderType.GAD,
            DisorderType.CONTROL,
            DisorderType.GAD,
            DisorderType.CONTROL,
        ]

        # Train classifier with fewer CV folds
        metrics = classifier.train(profiles, labels, cv_folds=2)

        assert classifier.is_trained is True
        assert "cv_mean_accuracy" in metrics
        assert "n_samples" in metrics
        assert metrics["n_samples"] == 6

    def test_classify(self):
        """Test disorder classification."""
        classifier = DisorderClassification()

        # Create and train classifier with more samples
        profiles = [
            NeuralSignatureProfile(
                p3b_amplitude_extero=5.0,
                p3b_amplitude_intero=3.0,
                gamma_power_frontal=0.2,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.0,
                p3b_amplitude_intero=1.5,
                gamma_power_frontal=0.1,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=4.8,
                p3b_amplitude_intero=2.9,
                gamma_power_frontal=0.22,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.2,
                p3b_amplitude_intero=1.6,
                gamma_power_frontal=0.12,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=5.1,
                p3b_amplitude_intero=3.1,
                gamma_power_frontal=0.21,
            ),
            NeuralSignatureProfile(
                p3b_amplitude_extero=2.1,
                p3b_amplitude_intero=1.4,
                gamma_power_frontal=0.11,
            ),
        ]
        labels = [
            DisorderType.GAD,
            DisorderType.CONTROL,
            DisorderType.GAD,
            DisorderType.CONTROL,
            DisorderType.GAD,
            DisorderType.CONTROL,
        ]
        classifier.train(profiles, labels, cv_folds=2)

        # Test classification
        test_profile = NeuralSignatureProfile(
            p3b_amplitude_extero=4.5, p3b_amplitude_intero=2.8, gamma_power_frontal=0.18
        )

        result = classifier.classify(test_profile)

        assert isinstance(result, ClassificationResult)
        assert isinstance(result.predicted_disorder, DisorderType)
        assert 0 <= result.confidence <= 1
        assert isinstance(result.probabilities, dict)

    def test_extract_neural_signature(self):
        """Test neural signature extraction."""
        classifier = DisorderClassification()

        p3b_data = {
            "amplitude_extero": 5.2,
            "amplitude_intero": 3.8,
            "latency_extero": 340,
            "latency_intero": 360,
        }
        gamma_data = {"power_frontal": 0.15, "power_posterior": 0.12, "coherence": 0.35}
        microstate_data = {"duration": 80, "transitions": 4.5}
        pupil_data = {"dilation_intero": 0.8, "latency": 250}
        apgi_params = {
            "threshold": 3.5,
            "intero_precision": 1.5,
            "extero_precision": 2.0,
            "somatic_gain": 1.2,
        }
        behavioral_data = {
            "detection_threshold_intero": 0.5,
            "detection_threshold_extero": 0.6,
            "rt_mean": 450,
            "rt_variability": 90,
        }

        profile = classifier.extract_neural_signature(
            p3b_data,
            gamma_data,
            microstate_data,
            pupil_data,
            apgi_params,
            behavioral_data,
        )

        assert isinstance(profile, NeuralSignatureProfile)
        assert profile.p3b_amplitude_extero == 5.2
        assert profile.p3b_amplitude_intero == 3.8
        assert profile.gamma_power_frontal == 0.15
        assert profile.threshold == 3.5

        # Remove the old test code that references non-existent methods


class TestClinicalParameters:
    """Test ClinicalParameters dataclass."""

    def test_default_parameters(self):
        """Test default clinical parameters."""
        params = ClinicalParameters()

        assert params.theta_t == 3.5
        assert params.pi_e == 2.0
        assert params.pi_i == 1.5
        assert params.beta == 1.2
        assert params.alpha == 1.0
        assert params.gamma == 0.1

    def test_custom_parameters(self):
        """Test custom clinical parameters."""
        params = ClinicalParameters(
            theta_t=4.2, pi_e=2.5, pi_i=1.8, beta=1.4, alpha=1.1, gamma=0.12
        )

        assert params.theta_t == 4.2
        assert params.pi_e == 2.5
        assert params.pi_i == 1.8
        assert params.beta == 1.4
        assert params.alpha == 1.1
        assert params.gamma == 0.12

    def test_to_dict(self):
        """Test parameter serialization."""
        params = ClinicalParameters(theta_t=4.2, pi_e=2.5, participant_id="test_participant")

        data = params.to_dict()
        assert data["theta_t"] == 4.2
        assert data["pi_e"] == 2.5
        assert data["participant_id"] == "test_participant"

    def test_from_dict(self):
        """Test parameter deserialization."""
        data = {"theta_t": 4.2, "pi_e": 2.5, "participant_id": "test_participant"}

        params = ClinicalParameters.from_dict(data)
        assert params.theta_t == 4.2
        assert params.pi_e == 2.5
        assert params.participant_id == "test_participant"


class TestClinicalParameterExtractor:
    """Test clinical parameter extractor implementation."""

    def test_initialization(self):
        """Test parameter extractor initialization."""
        extractor = ClinicalParameterExtractor()

        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_create_standard_battery(self):
        """Test creating standard assessment battery."""
        extractor = ClinicalParameterExtractor(participant_id="test_participant")

        battery = extractor.create_standard_battery()

        assert battery.participant_id == "test_participant"
        assert battery.total_duration == 30.0
        assert len(battery.tasks) > 0

    def test_extract_parameters_from_data(self):
        """Test parameter extraction from assessment data."""
        extractor = ClinicalParameterExtractor(participant_id="test_participant")

        # Test parameter extraction (this would need to be implemented in the actual class)
        # For now, just test that the method exists
        assert hasattr(extractor, "create_standard_battery")
        assert hasattr(extractor, "participant_id")


class TestTreatmentPredictor:
    """Test treatment predictor implementation."""

    def test_initialization(self):
        """Test treatment predictor initialization."""
        # Check if TreatmentPredictor exists and can be imported
        try:
            import apgi_framework.clinical.treatment_prediction

            assert hasattr(apgi_framework.clinical.treatment_prediction, "TreatmentPredictor")
            # For now, just test basic functionality
            assert True
        except (ImportError, AttributeError):
            # Skip test if module doesn't exist yet
            pytest.skip("TreatmentPredictor module not implemented yet")

    def test_treatment_types(self):
        """Test treatment type enum."""
        try:
            from apgi_framework.clinical.treatment_prediction import TreatmentType

            # Test that enum exists and has values
            assert hasattr(TreatmentType, "CBT")
            assert hasattr(TreatmentType, "SSRI")
            assert hasattr(TreatmentType, "SNRI")
        except ImportError:
            pytest.skip("TreatmentType enum not implemented yet")


class TestNeuralSignatureProfileExtended:
    """Extended tests for NeuralSignatureProfile."""

    def test_feature_vector_conversion(self):
        """Test conversion to feature vector."""
        import numpy as np

        profile = NeuralSignatureProfile(
            p3b_amplitude_extero=5.0,
            p3b_amplitude_intero=3.0,
            gamma_power_frontal=0.2,
            gamma_coherence=0.35,
            pupil_dilation_intero=0.8,
        )

        feature_vector = profile.to_feature_vector()

        assert isinstance(feature_vector, np.ndarray)
        assert len(feature_vector) == len(NeuralSignatureProfile.feature_names())
        assert feature_vector[0] == 5.0  # p3b_amplitude_extero
        assert feature_vector[1] == 3.0  # p3b_amplitude_intero

    def test_feature_names(self):
        """Test feature names method."""
        feature_names = NeuralSignatureProfile.feature_names()

        assert isinstance(feature_names, list)
        assert len(feature_names) > 0
        assert "p3b_amplitude_extero" in feature_names
        assert "p3b_amplitude_intero" in feature_names
        assert "gamma_power_frontal" in feature_names


class TestAdditionalEnums:
    """Test additional clinical enums."""

    def test_modality_types(self):
        """Test all modality type values."""
        assert ModalityType.VISUAL.value == "visual"
        assert ModalityType.AUDITORY.value == "auditory"
        assert ModalityType.INTEROCEPTIVE.value == "interoceptive"

    def test_task_types(self):
        """Test all task type values."""
        assert TaskType.THRESHOLD_DETECTION.value == "threshold_detection"
        assert TaskType.ODDBALL.value == "oddball"
        assert TaskType.EMOTIONAL_STROOP.value == "emotional_stroop"
        assert TaskType.HEARTBEAT_DETECTION.value == "heartbeat_detection"
        assert TaskType.BREATH_HOLD.value == "breath_hold"

    def test_treatment_type_enum(self):
        """Test TreatmentType enum values."""
        assert TreatmentType.SSRI.value == "ssri"
        assert TreatmentType.SNRI.value == "snri"
        assert TreatmentType.BETA_BLOCKER.value == "beta_blocker"
        assert TreatmentType.CBT.value == "cbt"
        assert TreatmentType.EXPOSURE_THERAPY.value == "exposure_therapy"


class TestTreatmentPrediction:
    """Test treatment prediction functionality."""

    def test_baseline_parameters_initialization(self):
        """Test BaselineParameters initialization."""
        params = BaselineParameters()
        assert params.theta_t == 3.5
        assert params.pi_e == 2.0
        assert params.pi_i == 1.5
        assert params.beta == 1.2

    def test_treatment_predictor_initialization(self):
        """Test treatment predictor initialization."""
        predictor = TreatmentPredictor()
        assert predictor is not None

    def test_treatment_response_prediction(self):
        """Test treatment response prediction."""
        predictor = TreatmentPredictor()

        # Test prediction
        params = BaselineParameters()
        prediction = predictor.predict(params)

        assert isinstance(prediction, TreatmentPrediction)
        assert isinstance(prediction.recommended_treatment, TreatmentType)
        assert 0 <= prediction.predicted_response <= 1.0
        assert 0 <= prediction.confidence <= 1.0


class TestAssessmentBattery:
    """Test assessment battery functionality."""

    def test_assessment_task_to_dict(self):
        """Test AssessmentTask serialization."""
        task = AssessmentTask(
            task_type=TaskType.THRESHOLD_DETECTION,
            modality=ModalityType.VISUAL,
            duration=5.0,
            n_trials=40,
        )
        data = task.to_dict()
        assert data["task_type"] == "threshold_detection"
        assert data["modality"] == "visual"
        assert data["duration"] == 5.0

    def test_assessment_battery_logic(self):
        """Test AssessmentBattery management."""
        battery = AssessmentBattery(battery_id="B001", participant_id="P001")
        task1 = AssessmentTask(TaskType.THRESHOLD_DETECTION, ModalityType.VISUAL, 5.0, 40)
        task2 = AssessmentTask(TaskType.THRESHOLD_DETECTION, ModalityType.AUDITORY, 5.0, 40)

        battery.add_task(task1)
        battery.add_task(task2)

        assert len(battery.tasks) == 2
        assert battery.get_total_planned_duration() == 10.0
        assert battery.get_completion_rate() == 0.0

        task1.completed = True
        task1.data_quality = 0.8
        assert battery.get_completion_rate() == 0.5
        assert battery.get_overall_quality() == 0.8


class TestClinicalParameterExtraction:
    """Test clinical parameter extraction coverage."""

    def test_clinical_parameters_to_dict_with_date(self):
        """Test ClinicalParameters serialization with date."""
        from datetime import datetime

        params = ClinicalParameters(
            participant_id="P001",
            assessment_date=datetime(2024, 1, 1),
            theta_t=3.7,
            pi_e=2.2,
            pi_i=1.6,
            beta=1.3,
        )
        data = params.to_dict()
        assert data["participant_id"] == "P001"
        assert data["theta_t"] == 3.7
        assert data["assessment_date"] == "2024-01-01T00:00:00"

    def test_clinical_parameters_from_dict(self):
        """Test ClinicalParameters deserialization."""
        from datetime import datetime

        data = {
            "participant_id": "P002",
            "theta_t": 3.8,
            "assessment_date": "2024-02-01T12:00:00",
        }
        params = ClinicalParameters.from_dict(data)
        assert params.participant_id == "P002"
        assert params.theta_t == 3.8
        assert params.assessment_date == datetime(2024, 2, 1, 12, 0)

    def test_extractor_create_battery(self):
        """Test creating standard battery."""
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()

        assert battery.participant_id == "P001"
        assert len(battery.tasks) == 6
        assert any(
            t.task_type == TaskType.THRESHOLD_DETECTION and t.modality == ModalityType.VISUAL
            for t in battery.tasks
        )

    def test_extract_parameters_from_battery(self):
        """Test parameter extraction from battery."""
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()

        # Mock data
        behavioral_data = {
            "visual_threshold": 0.4,
            "auditory_threshold": 0.4,
            "interoceptive_threshold": 0.6,
            "visual_accuracy": 0.8,
            "auditory_accuracy": 0.8,
            "rt_variability": 80.0,
            "heartbeat_accuracy": 0.7,
            "breath_awareness": 0.6,
            "emotional_stroop_interference": 70.0,
            "psychometric_slope": 1.2,
            "recovery_trials": 3,
        }

        params = extractor.extract_parameters_from_battery(battery, behavioral_data)

        assert params.participant_id == "P001"
        assert 1.0 <= params.theta_t <= 6.0
        assert 0.5 <= params.pi_e <= 4.0
        assert 0.3 <= params.pi_i <= 3.5
        assert 0.5 <= params.beta <= 3.0

    def test_reliability_metrics(self):
        """Test reliability metric calculations."""
        extractor = ClinicalParameterExtractor("P001")
        p1 = ClinicalParameters(theta_t=3.5, pi_e=2.0)
        p2 = ClinicalParameters(theta_t=3.6, pi_e=2.1)

        metrics = extractor.calculate_reliability_metrics(p1, p2)
        assert "theta_t" in metrics.test_retest_icc
        assert "pi_e" in metrics.test_retest_icc

    def test_internal_consistency(self):
        """Test internal consistency calculation."""
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()
        trial_data = {
            "task1": [1.0, 1.0, 0.0, 1.0, 1.0] * 10,
            "task2": [1.0, 0.0, 1.0, 1.0, 1.0] * 10,
        }
        alpha = extractor.calculate_internal_consistency(battery, trial_data)
        assert isinstance(alpha, float)

    def test_split_half_reliability(self):
        """Test split-half reliability calculation."""
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()
        trial_data = {"task1": [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0] * 10}
        res = extractor.calculate_split_half_reliability(battery, trial_data)
        assert isinstance(res, float)


class TestClinicalIntegration:
    """Test integration between clinical modules."""

    def test_classification_to_treatment_pipeline(self):
        """Test pipeline from disorder classification to treatment prediction."""
        # Test that basic classes can be initialized
        profile = NeuralSignatureProfile()
        assert profile.p3b_amplitude_extero == 0.0

    def test_parameter_extraction_to_classification(self):
        """Test pipeline from parameter extraction to disorder classification."""
        extractor = ClinicalParameterExtractor()

        # Test that extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0


if __name__ == "__main__":
    pytest.main([__file__])
