"""
Tests for Bayesian models module coverage.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from apgi_framework.analysis.bayesian_models import (
    SurpriseAccumulator,
    IgnitionProbabilityCalculator,
    ParameterDistribution,
    HierarchicalBayesianModel,
    StanModelCompiler,
)


class TestBayesianUtils:
    """Test utility classes and functions in Bayesian models."""

    def test_parameter_distribution(self):
        """Test ParameterDistribution data class."""
        samples = np.random.normal(0.5, 0.1, 1000)
        dist = ParameterDistribution(
            mean=0.5,
            std=0.1,
            credible_interval_95=(0.3, 0.7),
            posterior_samples=samples,
        )
        assert dist.mean == 0.5
        assert "mean=0.5000" in repr(dist)

    def test_surprise_accumulator(self):
        """Test SurpriseAccumulator integration."""
        acc = SurpriseAccumulator(tau=1.0, dt=0.1)

        # Test weighted PE computation
        pe = acc.compute_weighted_prediction_error(
            pi_e=1.0, epsilon_e=0.5, pi_i=2.0, epsilon_i=0.1, beta=1.5
        )
        # 1.0*0.5 + 1.5*2.0*0.1 = 0.5 + 0.3 = 0.8
        assert pytest.approx(pe) == 0.8

        # Test single step
        surprise = acc.step(1.0, 0.5, 2.0, 0.1, 1.5)
        # dS/dt = -0/1 + 0.8 = 0.8
        # S = 0 + 0.8*0.1 = 0.08
        assert pytest.approx(surprise) == 0.08

        # Test full integration
        duration = 1.0  # 10 steps
        pe_series = np.ones(10) * 0.5
        trace = acc.integrate(pe_series, pe_series, pe_series, pe_series, 1.0, duration)
        assert len(trace) == 10
        assert np.all(trace >= 0)

    def test_ignition_probability_calculator(self):
        """Test IgnitionProbabilityCalculator."""
        calc = IgnitionProbabilityCalculator(alpha=10.0)

        # Test sigmoid
        assert calc.sigmoid(0) == 0.5
        assert calc.sigmoid(100) == 1.0
        assert pytest.approx(calc.sigmoid(-100)) == 0.0

        # Test probability computation
        prob = calc.compute_probability(surprise=0.6, threshold=0.5)
        # alpha*(S-T) = 10*(0.6-0.5) = 1.0
        # sigmoid(1.0) approx 0.73
        assert 0.7 < prob < 0.8

        # Test ignition time
        trace = np.linspace(0, 1, 100)
        time = calc.find_ignition_time(trace, threshold=0.5, dt=0.01)
        assert time is not None
        assert 0.4 <= time <= 0.6


class TestHierarchicalModel:
    """Test HierarchicalBayesianModel and compiler (with mocking)."""

    @patch("apgi_framework.analysis.bayesian_models.safe_pickle_dump")
    @patch("apgi_framework.analysis.bayesian_models.safe_pickle_load")
    @patch("os.path.exists")
    def test_stan_compiler_mock(self, mock_exists, mock_load, mock_dump, tmp_path):
        """Test Stan compiler with mocked pystan."""
        # Mock pystan
        mock_pystan = MagicMock()
        with patch.dict("sys.modules", {"pystan": mock_pystan}):
            # Clear compiled models explicitly if needed
            compiler = StanModelCompiler(cache_dir=str(tmp_path))

            # Use force_recompile=True to bypass all cache checks
            compiler.compile_stan_model("model code", force_recompile=True)
            assert mock_pystan.StanModel.called

            # Test memory cache
            compiler.compile_stan_model("model code", force_recompile=False)
            assert mock_pystan.StanModel.call_count == 1

    def test_hierarchical_model_structure(self):
        """Test hierarchical model methods."""
        model = HierarchicalBayesianModel()
        code = model.get_stan_model_code()
        assert "data" in code
        assert "parameters" in code
        assert "theta0" in code

        data = model.prepare_data(
            detection_data={
                "subject_id": [1],
                "stimulus_intensity": [0.5],
                "detected": [1],
                "p3b_amplitude": [10.0],
            },
            heartbeat_data={
                "subject_id": [1],
                "synchronous": [1],
                "response_sync": [1],
                "confidence": [5.0],
                "hep_amplitude": [2.0],
                "pupil_response": [1.0],
            },
            oddball_data={
                "subject_id": [1],
                "trial_type": [1],
                "p3b_intero": [15.0],
                "p3b_extero": [12.0],
            },
            n_subjects=1,
        )
        assert data["N_subjects"] == 1
        assert data["N_trials_detection"] == 1
