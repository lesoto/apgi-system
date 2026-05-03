"""
Extended Analysis Engine Coverage Tests

Tests AnalysisEngine initialization, analysis methods, and result handling.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apgi_framework.analysis.analysis_engine import AnalysisEngine
from apgi_framework.exceptions import ValidationError


class TestAnalysisEngineInit:
    """Test AnalysisEngine initialization."""

    def test_init_default_output_dir(self):
        """Test initialization with default output directory."""
        engine = AnalysisEngine()

        assert engine.output_dir == Path("apgi_outputs/analysis")

    def test_init_custom_output_dir(self, tmp_path):
        """Test initialization with custom output directory."""
        engine = AnalysisEngine(str(tmp_path))

        assert engine.output_dir == tmp_path

    def test_init_creates_output_directory(self, tmp_path):
        """Test that initialization creates output directory."""
        output_path = tmp_path / "analysis_output"
        _ = AnalysisEngine(str(output_path))

        assert output_path.exists()

    def test_analysis_functions_registered(self):
        """Test that analysis functions are registered."""
        engine = AnalysisEngine()

        assert "descriptive" in engine.analysis_functions
        assert "comparative" in engine.analysis_functions
        assert "correlation" in engine.analysis_functions
        assert "regression" in engine.analysis_functions
        assert "time_series" in engine.analysis_functions
        assert "bayesian" in engine.analysis_functions


class TestAnalysisEngineAnalyze:
    """Test AnalysisEngine analyze method."""

    def test_analyze_unknown_type_raises(self):
        """Test that unknown analysis type raises ValidationError."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        with pytest.raises(ValidationError, match="Unknown analysis type"):
            engine.analyze(data, "unknown_type")

    def test_analyze_empty_data_raises(self):
        """Test that empty data raises ValidationError."""
        engine = AnalysisEngine()
        data = pd.DataFrame()

        with pytest.raises(ValidationError, match="Data cannot be empty"):
            engine.analyze(data, "descriptive")


class TestAnalysisEngineValidateData:
    """Test AnalysisEngine data validation."""

    def test_validate_comparative_requires_grouping(self):
        """Test comparative analysis requires grouping variables."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        with pytest.raises(
            ValidationError, match="Comparative analysis requires grouping variables"
        ):
            engine._validate_data(data, "comparative")

    def test_validate_comparative_with_grouping_passes(self):
        """Test comparative analysis with grouping variables passes."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1, 2, 3], "test_group": ["A", "B", "A"]})

        # Should not raise
        engine._validate_data(data, "comparative")

    def test_validate_correlation_requires_numeric(self):
        """Test correlation analysis requires numeric columns."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": ["a", "b", "c"]})

        with pytest.raises(
            ValidationError, match="Correlation analysis requires at least 2 numeric columns"
        ):
            engine._validate_data(data, "correlation")

    def test_validate_correlation_with_sufficient_numeric_passes(self):
        """Test correlation analysis with sufficient numeric columns passes."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1.0, 2.0, 3.0], "col2": [4.0, 5.0, 6.0]})

        # Should not raise
        engine._validate_data(data, "correlation")

    def test_validate_time_series_requires_time_column(self):
        """Test time series analysis requires time column."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        with pytest.raises(
            ValidationError, match="Time series analysis requires time/timestamp column"
        ):
            engine._validate_data(data, "time_series")

    def test_validate_time_series_with_timestamp_passes(self):
        """Test time series analysis with timestamp column passes."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"value": [1, 2, 3], "timestamp": [1, 2, 3]})

        # Should not raise
        engine._validate_data(data, "time_series")

    def test_validate_time_series_with_time_column_passes(self):
        """Test time series analysis with time column passes."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"value": [1, 2, 3], "time": [1, 2, 3]})

        # Should not raise
        engine._validate_data(data, "time_series")


class TestAnalysisEngineDescriptiveAnalysis:
    """Test AnalysisEngine descriptive analysis."""

    def test_descriptive_analysis_returns_stats(self):
        """Test descriptive analysis returns statistics."""
        engine = AnalysisEngine()
        data = pd.DataFrame(
            {"col1": [1.0, 2.0, 3.0, 4.0, 5.0], "col2": [10.0, 20.0, 30.0, 40.0, 50.0]}
        )

        stats, p_values, effect_sizes, conf_intervals = engine._descriptive_analysis(data, {})

        assert "col1" in stats
        assert "col2" in stats
        assert "mean" in stats["col1"]
        assert "std" in stats["col1"]
        assert "count" in stats["col1"]


class TestAnalysisEngineComparativeAnalysis:
    """Test AnalysisEngine comparative analysis."""

    def test_comparative_analysis_no_groups_returns_empty(self):
        """Test comparative analysis with no groups returns empty results."""
        engine = AnalysisEngine()
        data = pd.DataFrame({"col1": [1.0, 2.0, 3.0], "col2": [4.0, 5.0, 6.0]})

        stats, p_values, effect_sizes, conf_intervals = engine._comparative_analysis(data, {})

        assert stats == {}
        assert p_values == {}


class TestAnalysisEngineCorrelationAnalysis:
    """Test AnalysisEngine correlation analysis."""

    def test_correlation_analysis_returns_correlations(self):
        """Test correlation analysis returns correlation matrix."""
        engine = AnalysisEngine()
        np.random.seed(42)
        data = pd.DataFrame(
            {
                "col1": np.random.normal(0, 1, 100),
                "col2": np.random.normal(0, 1, 100),
                "col3": np.random.normal(0, 1, 100),
            }
        )

        stats, p_values, effect_sizes, conf_intervals = engine._correlation_analysis(data, {})

        assert "correlation_matrix" in stats
        assert "col1" in stats["correlation_matrix"]


class TestAnalysisEngineSummarizeData:
    """Test AnalysisEngine data summarization."""

    def test_summarize_data_returns_summary(self):
        """Test data summarization returns data summary."""
        engine = AnalysisEngine()
        data = pd.DataFrame(
            {
                "numeric": [1.0, 2.0, 3.0, 4.0, 5.0],
                "categorical": ["A", "B", "A", "B", "A"],
                "mixed": [1, "x", 2, "y", 3],
            }
        )

        summary = engine._summarize_data(data)

        assert "shape" in summary
        assert "columns" in summary
        assert summary["shape"] == (5, 3)
        assert len(summary["columns"]) == 3


class TestAnalysisEngineConfidenceInterval:
    """Test AnalysisEngine confidence interval calculation."""

    def test_calculate_confidence_interval_returns_tuple(self):
        """Test confidence interval calculation returns (lower, upper) tuple."""
        engine = AnalysisEngine()
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        ci = engine._calculate_confidence_interval(data)

        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] < ci[1]  # lower < upper


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
