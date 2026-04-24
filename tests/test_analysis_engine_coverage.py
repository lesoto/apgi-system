"""
Tests for AnalysisEngine module coverage.
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from apgi_framework.analysis.analysis_engine import AnalysisEngine, AnalysisResult


class TestAnalysisEngine:
    """Test suite for the AnalysisEngine."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create a temporary output directory."""
        return str(tmp_path / "analysis_output")

    @pytest.fixture
    def engine(self, output_dir):
        """Create an AnalysisEngine instance."""
        return AnalysisEngine(output_dir=output_dir)

    @pytest.fixture
    def sample_data(self):
        """Create sample experimental data for testing."""
        np.random.seed(42)
        n_samples = 100

        data = pd.DataFrame(
            {
                "subject_id": range(n_samples),
                "age": np.random.normal(30, 5, n_samples),
                "score_pre": np.random.normal(50, 10, n_samples),
                "score_post": np.random.normal(55, 12, n_samples),
                "condition_group": np.random.choice(["control", "experimental"], n_samples),
                "timestamp": pd.date_range("2024-01-01", periods=n_samples, freq="h"),
            }
        )
        return data

    def test_initialization(self, engine, output_dir):
        """Test AnalysisEngine initialization."""
        assert engine.output_dir == Path(output_dir)
        assert engine.output_dir.exists()
        assert "descriptive" in engine.analysis_functions

    def test_descriptive_analysis(self, engine, sample_data):
        """Test descriptive analysis."""
        result = engine.analyze(sample_data, "descriptive", generate_plots=True)

        assert isinstance(result, AnalysisResult)
        assert "age" in result.statistics
        assert "score_pre" in result.statistics
        assert len(result.plots) > 0

        # Verify files were saved
        analysis_id = result.analysis_id
        assert (engine.output_dir / "results" / f"{analysis_id}_summary.json").exists()

    def test_comparative_analysis(self, engine, sample_data):
        """Test comparative analysis (t-tests)."""
        result = engine.analyze(sample_data, "comparative", generate_plots=True)

        assert isinstance(result, AnalysisResult)
        # Should have t-tests for numeric columns by condition_group
        assert any("ttest" in k for k in result.statistics.keys())

    def test_correlation_analysis(self, engine, sample_data):
        """Test correlation analysis."""
        result = engine.analyze(sample_data, "correlation", generate_plots=True)

        assert isinstance(result, AnalysisResult)
        assert any("pearson" in k for k in result.statistics.keys())
        assert "correlation_heatmap" in result.plots

    def test_regression_analysis(self, engine, sample_data):
        """Test regression analysis."""
        result = engine.analyze(sample_data, "regression", generate_plots=False)

        assert isinstance(result, AnalysisResult)
        assert any("regression" in k for k in result.statistics.keys())

    def test_time_series_analysis(self, engine, sample_data):
        """Test time series analysis."""
        result = engine.analyze(sample_data, "time_series", generate_plots=False)

        assert isinstance(result, AnalysisResult)
        assert any("autocorr" in k for k in result.statistics.keys())

    def test_bayesian_analysis(self, engine, sample_data):
        """Test Bayesian analysis."""
        result = engine.analyze(sample_data, "bayesian", generate_plots=False)

        assert isinstance(result, AnalysisResult)
        assert any("bayesian" in k for k in result.statistics.keys())

    def test_invalid_analysis_type(self, engine, sample_data):
        """Test invalid analysis type raises ValidationError."""
        from apgi_framework.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Unknown analysis type"):
            engine.analyze(sample_data, "invalid_type")

    def test_empty_data(self, engine):
        """Test empty data raises ValidationError."""
        from apgi_framework.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Data cannot be empty"):
            engine.analyze(pd.DataFrame(), "descriptive")

    def test_list_and_get_summary(self, engine, sample_data):
        """Test listing analyses and retrieving summary."""
        result = engine.analyze(sample_data, "descriptive", generate_plots=False)
        analysis_id = result.analysis_id

        analyses = engine.list_analyses()
        assert analysis_id in analyses

        summary = engine.get_analysis_summary(analysis_id)
        assert summary["analysis_id"] == analysis_id
        assert summary["analysis_type"] == "descriptive"

    def test_get_summary_not_found(self, engine):
        """Test retrieving non-existent summary raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            engine.get_analysis_summary("non_existent_id")
