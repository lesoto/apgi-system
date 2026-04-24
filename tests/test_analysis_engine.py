"""
Test suite for apgi_framework.analysis.analysis_engine module.

Provides coverage for the AnalysisEngine and AnalysisResult classes.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apgi_framework.analysis.analysis_engine import AnalysisEngine, AnalysisResult
from apgi_framework.exceptions import ValidationError


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_init(self):
        """Test AnalysisResult initialization."""
        result = AnalysisResult(
            analysis_id="test_001",
            timestamp=datetime.now(),
            analysis_type="descriptive",
            statistics={"mean": 10.0},
            p_values={"test": 0.05},
            effect_sizes={"cohens_d": 0.5},
            confidence_intervals={"mean": (9.0, 11.0)},
            plots={"hist": "/path/to/plot.png"},
            figure_data={},
            parameters={"alpha": 0.05},
            data_summary={"n": 100},
            notes=["Test completed"],
        )

        assert result.analysis_id == "test_001"
        assert result.analysis_type == "descriptive"
        assert isinstance(result.timestamp, datetime)
        assert result.statistics["mean"] == 10.0


class TestAnalysisEngineInit:
    """Tests for AnalysisEngine initialization."""

    def test_analysis_engine_default_init(self):
        """Test AnalysisEngine initialization with default output directory."""
        engine = AnalysisEngine()

        assert engine.output_dir.exists()
        assert engine.output_dir.name == "analysis"
        assert "descriptive" in engine.analysis_functions
        assert "comparative" in engine.analysis_functions

    def test_analysis_engine_custom_init(self):
        """Test AnalysisEngine initialization with custom output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            assert engine.output_dir == Path(temp_dir)


class TestAnalysisEngineAnalyze:
    """Tests for the main analyze() method."""

    def test_descriptive_analysis(self):
        """Test descriptive analysis on numeric data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame(
                {
                    "score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    "value": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                }
            )

            result = engine.analyze(data, analysis_type="descriptive", generate_plots=False)
            assert result is not None
            assert result.analysis_type == "descriptive"
            assert "score" in result.statistics

    def test_correlation_analysis(self):
        """Test correlation analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            x = np.random.normal(0, 1, 50)
            y = x + np.random.normal(0, 0.1, 50)
            data = pd.DataFrame({"x": x, "y": y})

            result = engine.analyze(data, analysis_type="correlation", generate_plots=False)
            assert result is not None
            assert result.analysis_type == "correlation"

    def test_invalid_analysis_type(self):
        """Test that invalid analysis type raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame({"x": [1, 2, 3]})

            with pytest.raises(ValidationError):
                engine.analyze(data, analysis_type="invalid_type")

    def test_empty_data_error(self):
        """Test that empty data raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame()

            with pytest.raises(ValidationError):
                engine.analyze(data, analysis_type="descriptive")


class TestAnalysisEngineSaveAndLoad:
    """Tests for saving and loading analysis results."""

    def test_save_and_load_results(self):
        """Test saving and loading analysis results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame({"x": range(20), "y": range(20, 40)})
            result = engine.analyze(data, analysis_type="descriptive", generate_plots=False)

            loaded = engine.get_analysis_summary(result.analysis_id)
            assert loaded is not None
            assert loaded["analysis_id"] == result.analysis_id

    def test_list_analyses(self):
        """Test listing all analyses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = AnalysisEngine(output_dir=temp_dir)
            data = pd.DataFrame({"x": range(20), "y": range(20, 40)})
            engine.analyze(data, analysis_type="descriptive", generate_plots=False)
            engine.analyze(data, analysis_type="correlation", generate_plots=False)

            analyses = engine.list_analyses()
            assert len(analyses) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
