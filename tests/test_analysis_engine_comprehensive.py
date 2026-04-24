"""
Comprehensive test suite for apgi_framework.analysis.analysis_engine module.

This module provides complete coverage for:
- AnalysisEngine initialization and configuration
- All analysis types (descriptive, comparative, correlation, regression, time_series, bayesian)
- Data validation
- Visualization generation
- Results saving and loading
- Edge cases and error handling
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apgi_framework.analysis.analysis_engine import AnalysisEngine, AnalysisResult
from apgi_framework.exceptions import AnalysisError, ValidationError


class TestAnalysisResultDataclass:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_creation(self):
        """Test AnalysisResult can be created with all fields."""
        result = AnalysisResult(
            analysis_id="test_001",
            timestamp=datetime.now(),
            analysis_type="descriptive",
            statistics={"mean": 10.0, "std": 2.0},
            p_values={"test": 0.05},
            effect_sizes={"cohens_d": 0.5},
            confidence_intervals={"mean": (8.0, 12.0)},
            plots={"histogram": "/path/to/plot.png"},
            figure_data={"raw_data": [1, 2, 3]},
            parameters={"alpha": 0.05},
            data_summary={"n": 100},
            notes=["Test note"],
        )

        assert result.analysis_id == "test_001"
        assert result.analysis_type == "descriptive"
        assert result.statistics["mean"] == 10.0

    def test_analysis_result_optional_fields(self):
        """Test AnalysisResult with minimal fields."""
        result = AnalysisResult(
            analysis_id="minimal_test",
            timestamp=datetime.now(),
            analysis_type="test",
            statistics={},
            p_values={},
            effect_sizes={},
            confidence_intervals={},
            plots={},
            figure_data={},
            parameters={},
            data_summary={},
            notes=[],
        )

        assert result.analysis_id == "minimal_test"
        assert result.plots == {}
        assert result.notes == []


class TestAnalysisEngineInitialization:
    """Tests for AnalysisEngine initialization."""

    def test_default_initialization(self, tmp_path):
        """Test AnalysisEngine with default output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            assert engine.output_dir.exists()
            assert engine.output_dir == Path(temp_dir)
            assert "descriptive" in engine.analysis_functions
            assert "comparative" in engine.analysis_functions
            assert "correlation" in engine.analysis_functions
            assert "regression" in engine.analysis_functions
            assert "time_series" in engine.analysis_functions
            assert "bayesian" in engine.analysis_functions

    def test_custom_output_directory(self, tmp_path):
        """Test AnalysisEngine with custom output directory."""
        custom_dir = tmp_path / "custom_analysis"
        engine = AnalysisEngine(output_dir=str(custom_dir))

        assert engine.output_dir == custom_dir
        assert custom_dir.exists()

    def test_analysis_functions_registry(self):
        """Test that all analysis functions are properly registered."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            expected_functions = [
                "descriptive",
                "comparative",
                "correlation",
                "regression",
                "time_series",
                "bayesian",
            ]

            for func_name in expected_functions:
                assert func_name in engine.analysis_functions
                assert callable(engine.analysis_functions[func_name])


class TestDataValidation:
    """Tests for data validation methods."""

    def test_validate_data_comparative_without_groups(self):
        """Test validation fails for comparative analysis without grouping variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "value": [1, 2, 3, 4, 5],
                    "score": [10, 20, 30, 40, 50],
                }
            )

            with pytest.raises(ValidationError, match="grouping variables"):
                engine._validate_data(data, "comparative")

    def test_validate_data_comparative_with_groups(self):
        """Test validation passes for comparative analysis with grouping variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "value": [1, 2, 3, 4, 5],
                    "condition_group": ["A", "A", "B", "B", "B"],
                }
            )

            # Should not raise
            engine._validate_data(data, "comparative")

    def test_validate_data_correlation_insufficient_numeric(self):
        """Test validation fails for correlation with less than 2 numeric columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "value": [1, 2, 3, 4, 5],
                    "category": ["A", "B", "A", "B", "A"],
                }
            )

            with pytest.raises(ValidationError, match="at least 2 numeric columns"):
                engine._validate_data(data, "correlation")

    def test_validate_data_correlation_sufficient_numeric(self):
        """Test validation passes for correlation with 2+ numeric columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "x": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "y": [5.0, 4.0, 3.0, 2.0, 1.0],
                }
            )

            # Should not raise
            engine._validate_data(data, "correlation")

    def test_validate_data_time_series_without_time(self):
        """Test validation fails for time series without time column."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "value": [1, 2, 3, 4, 5],
                }
            )

            with pytest.raises(ValidationError, match="time/timestamp column"):
                engine._validate_data(data, "time_series")

    def test_validate_data_time_series_with_time(self):
        """Test validation passes for time series with time column."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "value": [1, 2, 3, 4, 5],
                    "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                }
            )

            # Should not raise
            engine._validate_data(data, "time_series")


class TestDescriptiveAnalysis:
    """Tests for descriptive statistical analysis."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "normal_dist": np.random.normal(100, 15, 100),
                "skewed_dist": np.random.exponential(2, 100),
                "uniform_dist": np.random.uniform(0, 10, 100),
            }
        )

    def test_descriptive_analysis_output(self, sample_data):
        """Test descriptive analysis returns expected statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            result = engine.analyze(sample_data, "descriptive", generate_plots=False)

            assert result.analysis_type == "descriptive"
            assert "normal_dist" in result.statistics
            assert "skewed_dist" in result.statistics
            assert "uniform_dist" in result.statistics

            # Check statistics structure
            for col in sample_data.columns:
                stats = result.statistics[col]
                assert "mean" in stats
                assert "median" in stats
                assert "std" in stats
                assert "min" in stats
                assert "max" in stats
                assert "count" in stats
                assert "missing" in stats

    def test_descriptive_confidence_intervals(self, sample_data):
        """Test that confidence intervals are calculated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            result = engine.analyze(sample_data, "descriptive", generate_plots=False)

            assert len(result.confidence_intervals) > 0
            for col in sample_data.columns:
                assert col in result.confidence_intervals
                ci = result.confidence_intervals[col]
                assert len(ci) == 2
                assert ci[0] < ci[1]  # Lower bound < upper bound

    def test_descriptive_p_values(self, sample_data):
        """Test that normality p-values are calculated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            result = engine.analyze(sample_data, "descriptive", generate_plots=False)

            assert len(result.p_values) > 0
            for col in sample_data.columns:
                assert f"{col}_normality" in result.p_values
                assert 0 <= result.p_values[f"{col}_normality"] <= 1

    def test_descriptive_effect_sizes(self, sample_data):
        """Test that effect sizes (skewness, kurtosis) are calculated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            result = engine.analyze(sample_data, "descriptive", generate_plots=False)

            assert len(result.effect_sizes) > 0
            for col in sample_data.columns:
                assert f"{col}_skewness" in result.effect_sizes
                assert f"{col}_kurtosis" in result.effect_sizes


class TestComparativeAnalysis:
    """Tests for comparative analysis (t-tests and ANOVA)."""

    def test_comparative_ttest_two_groups(self):
        """Test comparative analysis with two groups (t-test)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "score": np.concatenate(
                        [
                            np.random.normal(100, 10, 50),
                            np.random.normal(110, 10, 50),
                        ]
                    ),
                    "group": ["control"] * 50 + ["experimental"] * 50,
                }
            )
            data.rename(columns={"group": "condition_group"}, inplace=True)

            result = engine.analyze(data, "comparative", generate_plots=False)

            assert result.analysis_type == "comparative"
            # Check for t-test results
            assert any("ttest" in key for key in result.statistics.keys())

    def test_comparative_anova_three_groups(self):
        """Test comparative analysis with three groups (ANOVA)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "score": np.concatenate(
                        [
                            np.random.normal(100, 10, 30),
                            np.random.normal(105, 10, 30),
                            np.random.normal(110, 10, 30),
                        ]
                    ),
                    "condition_group": ["A"] * 30 + ["B"] * 30 + ["C"] * 30,
                }
            )

            result = engine.analyze(data, "comparative", generate_plots=False)

            assert result.analysis_type == "comparative"
            # Check for ANOVA results
            assert any("anova" in key for key in result.statistics.keys())

    def test_comparative_cohens_d_calculation(self):
        """Test that Cohen's d effect size is calculated for t-tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "metric": np.concatenate(
                        [
                            np.random.normal(100, 10, 30),
                            np.random.normal(110, 10, 30),
                        ]
                    ),
                    "group_var": ["control"] * 30 + ["treatment"] * 30,
                }
            )
            data.rename(columns={"group_var": "group_var_group"}, inplace=True)

            result = engine.analyze(data, "comparative", generate_plots=False)

            # Check for Cohen's d
            assert any("cohens_d" in key for key in result.effect_sizes.keys())

    def test_comparative_eta_squared_calculation(self):
        """Test that eta squared is calculated for ANOVA."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "outcome": np.concatenate(
                        [
                            np.random.normal(100, 10, 20),
                            np.random.normal(105, 10, 20),
                            np.random.normal(110, 10, 20),
                        ]
                    ),
                    "condition_group": ["low"] * 20 + ["medium"] * 20 + ["high"] * 20,
                }
            )

            result = engine.analyze(data, "comparative", generate_plots=False)

            # Check for eta squared
            assert any("eta_squared" in key for key in result.effect_sizes.keys())


class TestCorrelationAnalysis:
    """Tests for correlation analysis."""

    def test_correlation_pearson_calculation(self):
        """Test Pearson correlation calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            x = np.random.normal(0, 1, 100)
            y = 2 * x + np.random.normal(0, 0.5, 100)  # Strong positive correlation

            data = pd.DataFrame({"x": x, "y": y})

            result = engine.analyze(data, "correlation", generate_plots=False)

            assert result.analysis_type == "correlation"
            assert any("pearson" in key for key in result.statistics.keys())

            # Find the correlation key
            corr_key = [k for k in result.statistics.keys() if "pearson" in k][0]
            corr_value = result.statistics[corr_key]["correlation"]

            # Should be strongly positive
            assert corr_value > 0.7

    def test_correlation_p_values(self):
        """Test that p-values are calculated for correlations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "a": np.random.normal(0, 1, 100),
                    "b": np.random.normal(0, 1, 100),
                    "c": np.random.normal(0, 1, 100),
                }
            )

            result = engine.analyze(data, "correlation", generate_plots=False)

            # Should have p-values for each pair
            expected_pairs = 3  # a-b, a-c, b-c
            assert len(result.p_values) >= expected_pairs

    def test_correlation_confidence_intervals(self):
        """Test that confidence intervals are calculated for correlations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "var1": np.random.normal(0, 1, 100),
                    "var2": np.random.normal(0, 1, 100),
                }
            )

            result = engine.analyze(data, "correlation", generate_plots=False)

            assert len(result.confidence_intervals) > 0
            for key, ci in result.confidence_intervals.items():
                assert len(ci) == 2
                assert -1 <= ci[0] <= 1  # Correlation bounds
                assert -1 <= ci[1] <= 1
                assert ci[0] < ci[1]

    def test_correlation_effect_sizes(self):
        """Test that effect sizes (|r|) are calculated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "x": np.random.normal(0, 1, 100),
                    "y": np.random.normal(0, 1, 100),
                }
            )

            result = engine.analyze(data, "correlation", generate_plots=False)

            # Effect sizes should be absolute values of correlations
            for key, effect in result.effect_sizes.items():
                assert 0 <= effect <= 1


class TestRegressionAnalysis:
    """Tests for regression analysis."""

    def test_regression_simple_linear(self):
        """Test simple linear regression."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            x = np.linspace(0, 10, 100)
            y = 2 * x + 1 + np.random.normal(0, 1, 100)

            data = pd.DataFrame({"x": x, "y": y})

            result = engine.analyze(data, "regression", generate_plots=False)

            assert result.analysis_type == "regression"
            assert any("regression" in key for key in result.statistics.keys())

    def test_regression_coefficients(self):
        """Test that regression coefficients are calculated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            x = np.linspace(0, 10, 100)
            y = 3 * x + 5 + np.random.normal(0, 0.5, 100)

            data = pd.DataFrame({"predictor": x, "outcome": y})

            result = engine.analyze(data, "regression", generate_plots=False)

            # Find regression results
            reg_key = [k for k in result.statistics.keys() if "regression" in k][0]
            stats = result.statistics[reg_key]

            assert "slope" in stats
            assert "intercept" in stats
            assert "r_squared" in stats
            assert "rmse" in stats
            assert "n" in stats

    def test_regression_r_squared_as_effect_size(self):
        """Test that R-squared is used as effect size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            x = np.linspace(0, 10, 100)
            y = 2 * x + 1 + np.random.normal(0, 0.5, 100)  # Strong relationship

            data = pd.DataFrame({"x": x, "y": y})

            result = engine.analyze(data, "regression", generate_plots=False)

            # Effect sizes should be R-squared values
            for key, effect in result.effect_sizes.items():
                assert 0 <= effect <= 1


class TestTimeSeriesAnalysis:
    """Tests for time series analysis."""

    def test_time_series_autocorrelation(self):
        """Test autocorrelation calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            # Create time series data
            dates = pd.date_range("2024-01-01", periods=50, freq="D")
            values = np.cumsum(np.random.normal(0, 1, 50))  # Random walk

            data = pd.DataFrame(
                {
                    "timestamp": dates,
                    "value": values,
                }
            )

            result = engine.analyze(data, "time_series", generate_plots=False)

            assert result.analysis_type == "time_series"
            assert any("autocorr" in key for key in result.statistics.keys())

    def test_time_series_trend_calculation(self):
        """Test linear trend calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            dates = pd.date_range("2024-01-01", periods=50, freq="D")
            trend = np.linspace(0, 10, 50)
            noise = np.random.normal(0, 0.5, 50)
            values = trend + noise

            data = pd.DataFrame(
                {
                    "time_col": dates,
                    "metric": values,
                }
            )

            result = engine.analyze(data, "time_series", generate_plots=False)

            # Check for trend in statistics
            for key, stats in result.statistics.items():
                if "autocorr" in key:
                    assert "trend" in stats

    def test_time_series_stationarity_effect_size(self):
        """Test stationarity ratio as effect size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            dates = pd.date_range("2024-01-01", periods=50, freq="D")
            values = np.cumsum(np.random.normal(0, 1, 50))

            data = pd.DataFrame(
                {
                    "timestamp": dates,
                    "series": values,
                }
            )

            result = engine.analyze(data, "time_series", generate_plots=False)

            assert len(result.effect_sizes) > 0
            assert any("stationarity" in key for key in result.effect_sizes.keys())


class TestBayesianAnalysis:
    """Tests for Bayesian analysis."""

    def test_bayesian_posterior_mean(self):
        """Test Bayesian posterior mean calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "measurement": np.random.normal(50, 10, 100),
                }
            )

            result = engine.analyze(data, "bayesian", generate_plots=False)

            assert result.analysis_type == "bayesian"
            assert any("bayesian" in key for key in result.statistics.keys())

    def test_bayesian_credible_intervals(self):
        """Test Bayesian credible interval calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "variable": np.random.normal(100, 15, 100),
                }
            )

            result = engine.analyze(data, "bayesian", generate_plots=False)

            # Check for credible intervals
            for key, stats in result.statistics.items():
                if "bayesian" in key:
                    assert "credible_interval_95" in stats
                    ci = stats["credible_interval_95"]
                    assert len(ci) == 2
                    assert ci[0] < ci[1]

            # Check confidence intervals dict
            assert len(result.confidence_intervals) > 0


class TestVisualizationGeneration:
    """Tests for visualization generation."""

    def test_generate_distribution_plots(self):
        """Test distribution plot generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "var1": np.random.normal(0, 1, 50),
                    "var2": np.random.normal(10, 2, 50),
                }
            )

            result = engine.analyze(data, "descriptive", generate_plots=True)

            assert len(result.plots) > 0
            for plot_name, plot_path in result.plots.items():
                assert Path(plot_path).exists()

    def test_generate_correlation_heatmap(self):
        """Test correlation heatmap generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "a": np.random.normal(0, 1, 50),
                    "b": np.random.normal(0, 1, 50),
                    "c": np.random.normal(0, 1, 50),
                }
            )

            result = engine.analyze(data, "correlation", generate_plots=True)

            assert "correlation_heatmap" in result.plots
            assert Path(result.plots["correlation_heatmap"]).exists()

    def test_figure_data_storage(self):
        """Test that raw figure data is stored for interactive plots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "x": np.random.normal(0, 1, 50),
                    "y": np.random.normal(0, 1, 50),
                }
            )

            result = engine.analyze(data, "correlation", generate_plots=True)

            assert len(result.figure_data) > 0
            assert "correlation_matrix" in result.figure_data

    def test_plots_without_generation(self):
        """Test that no plots are generated when generate_plots=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "value": np.random.normal(0, 1, 50),
                }
            )

            result = engine.analyze(data, "descriptive", generate_plots=False)

            assert len(result.plots) == 0
            assert len(result.figure_data) == 0


class TestResultsSavingAndLoading:
    """Tests for saving and loading analysis results."""

    def test_save_results_json(self):
        """Test saving results to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame({"x": range(10)})
            result = engine.analyze(data, "descriptive", generate_plots=False)

            # Check that JSON file was created (directly in output_dir/results)
            results_dir = Path(temp_dir) / "results"
            json_file = results_dir / f"{result.analysis_id}_summary.json"
            assert json_file.exists(), f"JSON file not found at {json_file}"

            # Verify JSON content
            with open(json_file) as f:
                saved = json.load(f)
                assert saved["analysis_id"] == result.analysis_id
                assert saved["analysis_type"] == "descriptive"
                assert "statistics" in saved

    def test_save_results_csv(self):
        """Test saving results to CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame({"x": range(10)})
            result = engine.analyze(data, "descriptive", generate_plots=False)

            # Check that CSV file was created (directly in output_dir/results)
            results_dir = Path(temp_dir) / "results"
            csv_file = results_dir / f"{result.analysis_id}_data.csv"
            assert csv_file.exists(), f"CSV file not found at {csv_file}"

    def test_get_analysis_summary(self):
        """Test retrieving saved analysis summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame({"value": np.random.normal(0, 1, 50)})
            result = engine.analyze(data, "descriptive", generate_plots=False)

            loaded = engine.get_analysis_summary(result.analysis_id)

            assert loaded["analysis_id"] == result.analysis_id
            assert loaded["analysis_type"] == "descriptive"
            assert "statistics" in loaded
            assert "p_values" in loaded
            assert "effect_sizes" in loaded

    def test_get_summary_not_found(self):
        """Test retrieving non-existent summary raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            with pytest.raises(FileNotFoundError):
                engine.get_analysis_summary("non_existent_id_12345")

    def test_list_analyses(self):
        """Test listing all analyses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            # Use data with 2+ numeric columns for correlation analysis
            data = pd.DataFrame({"x": range(10), "y": range(10, 20)})
            result1 = engine.analyze(data, "descriptive", generate_plots=False)
            result2 = engine.analyze(data, "correlation", generate_plots=False)

            analyses = engine.list_analyses()

            assert len(analyses) >= 2
            assert result1.analysis_id in analyses
            assert result2.analysis_id in analyses

    def test_list_analyses_empty(self):
        """Test listing analyses when none exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            analyses = engine.list_analyses()

            assert analyses == []


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_empty_data_error(self):
        """Test that empty DataFrame raises ValidationError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            with pytest.raises(ValidationError, match="Data cannot be empty"):
                engine.analyze(pd.DataFrame(), "descriptive")

    def test_invalid_analysis_type(self):
        """Test that invalid analysis type raises ValidationError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame({"x": [1, 2, 3]})

            with pytest.raises(ValidationError, match="Unknown analysis type"):
                engine.analyze(data, "nonexistent_type")

    def test_data_with_missing_values(self):
        """Test analysis handles missing values gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "value": [1.0, 2.0, np.nan, 4.0, 5.0],
                }
            )

            # Should not raise
            result = engine.analyze(data, "descriptive", generate_plots=False)
            assert result is not None

    def test_single_row_data(self):
        """Test analysis with single row data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame({"x": [1.0], "y": [2.0]})

            # Should handle gracefully or raise appropriate error
            try:
                result = engine.analyze(data, "descriptive", generate_plots=False)
                assert result is not None
            except (AnalysisError, ValueError):
                pass  # Also acceptable if it raises an error

    def test_numpy_type_conversion(self):
        """Test that numpy types are converted for JSON serialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "int_col": np.array([1, 2, 3], dtype=np.int32),
                    "float_col": np.array([1.5, 2.5, 3.5], dtype=np.float32),
                }
            )

            result = engine.analyze(data, "descriptive", generate_plots=False)

            # Verify JSON was saved successfully (no numpy type errors)
            loaded = engine.get_analysis_summary(result.analysis_id)
            assert loaded is not None


class TestConfidenceIntervalCalculations:
    """Tests for confidence interval calculation methods."""

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation for mean."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
            ci = engine._calculate_confidence_interval(data, confidence=0.95)

            assert len(ci) == 2
            assert ci[0] < ci[1]
            # CI should contain the mean (5.5)
            assert ci[0] < 5.5 < ci[1]

    def test_correlation_confidence_interval(self):
        """Test confidence interval calculation for correlation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            r = 0.7
            n = 100
            ci = engine._correlation_confidence_interval(r, n, confidence=0.95)

            assert len(ci) == 2
            assert -1 <= ci[0] <= 1
            assert -1 <= ci[1] <= 1
            assert ci[0] < ci[1]
            # CI should contain the correlation
            assert ci[0] < r < ci[1]


class TestDataSummarization:
    """Tests for data summarization."""

    def test_summarize_data(self):
        """Test data summary creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)

            data = pd.DataFrame(
                {
                    "numeric": [1, 2, 3, 4, 5],
                    "categorical": ["A", "B", "A", "B", "A"],
                }
            )

            summary = engine._summarize_data(data)

            assert summary["shape"] == (5, 2)
            assert "numeric" in summary["columns"]
            assert "categorical" in summary["columns"]
            assert "numeric" in summary["numeric_columns"]
            assert "categorical" in summary["categorical_columns"]
            assert summary["missing_values"]["numeric"] == 0
            assert summary["memory_usage"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
