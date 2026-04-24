"""
Test suite for core data models.
"""

import pytest
from apgi_framework.core.data_models import (
    APGIParameters,
    NeuralSignatures,
    ExperimentalTrial,
    StatisticalSummary,
)


class TestDataModels:
    """Test cases for core data models."""

    def test_apgi_parameters_creation(self):
        """Test APGIParameters creation and validation."""
        # Test default values
        params = APGIParameters()
        assert params.extero_precision == 2.0
        assert params.intero_precision == 1.5
        assert params.threshold == 3.5

        # Test to_dict conversion
        params_dict = params.to_dict()
        assert isinstance(params_dict, dict)
        assert len(params_dict) == 7
        assert params_dict["extero_precision"] == 2.0

    def test_neural_signatures_creation(self):
        """Test NeuralSignatures creation and validation."""
        # Test default values
        neural = NeuralSignatures()
        assert neural.p3b_amplitude == 0.0
        assert neural.p3b_latency == 350.0
        assert neural.gamma_plv == 0.0
        assert isinstance(neural.bold_activations, dict)
        assert neural.bold_activations == {}

    def test_experimental_trial_creation(self):
        """Test ExperimentalTrial creation and validation."""
        # Test with sample data
        trial = ExperimentalTrial(
            participant_id="test_participant",
            condition="test_condition",
            trial_number=1,
        )
        assert trial.participant_id == "test_participant"
        assert trial.condition == "test_condition"
        assert trial.trial_number == 1
        assert isinstance(trial.trial_id, str)
        assert isinstance(trial.apgi_parameters, APGIParameters)
        assert isinstance(trial.neural_signatures, NeuralSignatures)

    def test_statistical_summary_creation(self):
        """Test StatisticalSummary creation and validation."""
        # Test with sample data
        summary = StatisticalSummary(
            mean_effect_size=0.5,
            effect_size_ci_lower=0.3,
            effect_size_ci_upper=0.7,
            statistical_power=0.8,
            total_participants=50,
            total_trials=1000,
        )
        assert summary.mean_effect_size == 0.5
        assert summary.effect_size_ci_lower == 0.3
        assert summary.effect_size_ci_upper == 0.7
        assert summary.statistical_power == 0.8
        assert summary.total_participants == 50
        assert summary.total_trials == 1000


if __name__ == "__main__":
    pytest.main([__file__])
