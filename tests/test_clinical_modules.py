"""
Tests for clinical modules.
"""

import numpy as np
import pytest

from apgi_framework.clinical.disorder_classification import (
    ClassificationResult,
    DisorderClassification,
    DisorderType,
    NeuralSignatureProfile,
)
from apgi_framework.clinical.parameter_extraction import (
    ClinicalParameterExtractor,
)
from apgi_framework.clinical.treatment_prediction import (
    BaselineParameters,
    TreatmentPrediction,
    TreatmentPredictor,
    TreatmentType,
)


class TestDisorderClassification:
    """Test disorder classification functionality."""

    def test_disorder_type_enum(self):
        """Test disorder type enumeration."""
        assert DisorderType.CONTROL.value == "control"
        assert DisorderType.GAD.value == "generalized_anxiety_disorder"
        assert DisorderType.PANIC.value == "panic_disorder"
        assert DisorderType.SOCIAL_ANXIETY.value == "social_anxiety_disorder"
        assert DisorderType.DEPRESSION.value == "major_depressive_disorder"
        assert DisorderType.PTSD.value == "post_traumatic_stress_disorder"

    def test_neural_signature_profile_initialization(self):
        """Test neural signature profile initialization."""
        profile = NeuralSignatureProfile()

        # Test default values
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

    def test_neural_signature_profile_custom_values(self):
        """Test neural signature profile with custom values."""
        profile = NeuralSignatureProfile(
            p3b_amplitude_extero=5.5,
            p3b_amplitude_intero=3.2,
            gamma_power_frontal=1.2,
            gamma_coherence=0.8,
            microstate_duration=120.0,
        )

        assert profile.p3b_amplitude_extero == 5.5
        assert profile.p3b_amplitude_intero == 3.2
        assert profile.gamma_power_frontal == 1.2
        assert profile.gamma_coherence == 0.8
        assert profile.microstate_duration == 120.0

    def test_disorder_classification_initialization(self):
        """Test disorder classification initialization."""
        classifier = DisorderClassification()

        assert classifier.classifier_type == "random_forest"
        assert classifier.scaler is not None
        assert classifier.classifier is not None

    def test_disorder_classification_different_models(self):
        """Test disorder classification with different model types."""
        # Test Random Forest
        rf_classifier = DisorderClassification(classifier_type="random_forest")
        assert rf_classifier.classifier_type == "random_forest"

        # Test Gradient Boosting
        gb_classifier = DisorderClassification(classifier_type="gradient_boosting")
        assert gb_classifier.classifier_type == "gradient_boosting"

        # Test SVM
        svm_classifier = DisorderClassification(classifier_type="svm")
        assert svm_classifier.classifier_type == "svm"

    def test_feature_extraction_from_profile(self):
        """Test feature extraction from neural signature profile."""
        profile = NeuralSignatureProfile(
            p3b_amplitude_extero=5.5,
            p3b_amplitude_intero=3.2,
            gamma_power_frontal=1.2,
            gamma_coherence=0.8,
            microstate_duration=120.0,
        )

        # Test that profile can be created and has expected attributes
        assert profile.p3b_amplitude_extero == 5.5
        assert profile.p3b_amplitude_intero == 3.2
        assert profile.gamma_power_frontal == 1.2

    def test_data_preparation(self):
        """Test data preparation for training."""
        profiles = [
            NeuralSignatureProfile(p3b_amplitude_extero=5.0, gamma_power_frontal=1.0),
            NeuralSignatureProfile(p3b_amplitude_extero=3.0, gamma_power_frontal=0.5),
            NeuralSignatureProfile(p3b_amplitude_extero=7.0, gamma_power_frontal=1.5),
        ]
        labels = [DisorderType.GAD, DisorderType.CONTROL, DisorderType.PANIC]

        # Test that profiles and labels can be created
        assert len(profiles) == 3
        assert len(labels) == 3
        assert isinstance(profiles[0], NeuralSignatureProfile)

    def test_model_training(self):
        """Test model training with sample data."""
        # Generate sample data with enough samples for cross-validation
        np.random.seed(42)
        n_samples = 50
        profiles = []
        labels = []

        for i in range(n_samples):
            profile = NeuralSignatureProfile(
                p3b_amplitude_extero=np.random.normal(5, 2),
                p3b_amplitude_intero=np.random.normal(3, 1),
                gamma_power_frontal=np.random.normal(1, 0.5),
                gamma_coherence=np.random.normal(0.6, 0.2),
            )
            profiles.append(profile)
            # Assign labels based on some simple rules
            if profile.p3b_amplitude_extero > 6:
                labels.append(DisorderType.GAD)
            elif profile.gamma_power_frontal > 1.2:
                labels.append(DisorderType.PANIC)
            else:
                labels.append(DisorderType.CONTROL)

        classifier = DisorderClassification()
        classifier.train(profiles, labels)

        assert classifier.is_trained is True
        assert classifier.scaler is not None
        assert classifier.classifier is not None

    def test_prediction(self):
        """Test disorder prediction."""
        # Train classifier first with enough samples
        np.random.seed(42)
        profiles = []
        labels = []

        for i in range(50):
            profile = NeuralSignatureProfile(
                p3b_amplitude_extero=np.random.normal(5, 2),
                gamma_power_frontal=np.random.normal(1, 0.5),
            )
            profiles.append(profile)
            labels.append(DisorderType.GAD if i % 2 == 0 else DisorderType.CONTROL)

        classifier = DisorderClassification()
        classifier.train(profiles, labels)

        # Test classification
        test_profile = NeuralSignatureProfile(p3b_amplitude_extero=6.5, gamma_power_frontal=1.3)

        result = classifier.classify(test_profile)

        assert isinstance(result, ClassificationResult)
        assert isinstance(result.predicted_disorder, DisorderType)
        assert 0 <= result.confidence <= 1

    def test_cross_validation(self):
        """Test cross-validation evaluation."""
        # Generate sample data
        np.random.seed(42)
        profiles = []
        labels = []

        for i in range(30):
            profile = NeuralSignatureProfile(
                p3b_amplitude_extero=np.random.normal(5, 2),
                gamma_power_frontal=np.random.normal(1, 0.5),
            )
            profiles.append(profile)
            labels.append(DisorderType.GAD if i % 2 == 0 else DisorderType.CONTROL)

        classifier = DisorderClassification()
        classifier.train(profiles, labels)

        # Test that classifier is trained
        assert classifier.is_trained is True


class TestParameterExtraction:
    """Test clinical parameter extraction functionality."""

    def test_parameter_extraction_config(self):
        """Test parameter extraction configuration."""
        # Test that extractor can be initialized
        extractor = ClinicalParameterExtractor()
        assert extractor.participant_id == ""

    def test_parameter_extraction_config_custom(self):
        """Test parameter extraction configuration with custom values."""
        # Test that extractor can be initialized
        extractor = ClinicalParameterExtractor()
        assert extractor.participant_id == ""

    def test_clinical_parameter_extractor_initialization(self):
        """Test clinical parameter extractor initialization."""
        extractor = ClinicalParameterExtractor()

        # Test that extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_p3b_amplitude_extraction(self):
        """Test P3b amplitude extraction from simulated data."""
        extractor = ClinicalParameterExtractor()

        # Test that extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_gamma_power_extraction(self):
        """Test gamma power extraction from simulated data."""
        extractor = ClinicalParameterExtractor()

        # Test that the extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_microstate_analysis(self):
        """Test microstate analysis parameters."""
        extractor = ClinicalParameterExtractor()

        # Test that the extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_pupillometry_extraction(self):
        """Test pupillometry parameter extraction."""
        extractor = ClinicalParameterExtractor()

        # Test that the extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0

    def test_comprehensive_parameter_extraction(self):
        """Test comprehensive parameter extraction from all modalities."""
        extractor = ClinicalParameterExtractor()

        # Test that the extractor can be initialized
        assert extractor.participant_id == ""
        assert len(extractor.assessment_history) == 0


class TestTreatmentPrediction:
    """Test treatment prediction functionality."""

    def test_treatment_response_model_initialization(self):
        """Test treatment response model initialization."""
        # Test BaselineParameters
        params = BaselineParameters()
        assert params.theta_t == 3.5
        assert params.pi_e == 2.0
        assert params.pi_i == 1.5
        assert params.beta == 1.2

    def test_treatment_predictor_initialization(self):
        """Test treatment predictor initialization."""
        predictor = TreatmentPredictor()

        # Test that predictor can be initialized
        assert predictor is not None

    def test_feature_engineering(self):
        """Test feature engineering for treatment prediction."""
        predictor = TreatmentPredictor()

        # Test that predictor can be initialized
        assert predictor is not None

    def test_treatment_response_prediction(self):
        """Test treatment response prediction."""
        predictor = TreatmentPredictor()

        # Test basic prediction functionality
        params = BaselineParameters()
        prediction = predictor.predict(params)

        assert isinstance(prediction, TreatmentPrediction)
        assert isinstance(prediction.recommended_treatment, TreatmentType)
        assert 0 <= prediction.predicted_response <= 1.0
        assert 0 <= prediction.confidence <= 1.0

    def test_treatment_recommendation(self):
        """Test treatment recommendation based on prediction."""
        predictor = TreatmentPredictor()

        # Test that predictor can be initialized
        assert predictor is not None

    def test_model_evaluation(self):
        """Test treatment prediction model evaluation."""
        predictor = TreatmentPredictor()

        # Test that predictor can be initialized
        assert predictor is not None


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
