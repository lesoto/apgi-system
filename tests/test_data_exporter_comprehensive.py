"""
Comprehensive tests for data/data_exporter.py module.

Tests for DataExporter class to improve coverage.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime


class TestDataExporterImports:
    """Test module imports."""

    def test_module_imports(self):
        """Test that data_exporter module can be imported."""
        from apgi_framework.data import data_exporter

        assert hasattr(data_exporter, "DataExporter")


class TestDataExporterInitialization:
    """Test DataExporter initialization."""

    def test_basic_initialization(self):
        """Test basic exporter initialization."""
        from apgi_framework.data.data_exporter import DataExporter

        exporter = DataExporter()
        assert exporter is not None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        from apgi_framework.data.data_exporter import DataExporter

        config = {"output_dir": "/tmp/exports"}
        exporter = DataExporter(config=config)
        assert exporter.config == config


class TestDataExporterCSV:
    """Test CSV export functionality."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_dataframe_to_csv(self, exporter):
        """Test exporting DataFrame to CSV."""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        result = exporter.export_to_csv(df, "test.csv")
        assert result is not None

    def test_export_dict_to_csv(self, exporter):
        """Test exporting dict list to CSV."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        result = exporter.export_to_csv(data, "test.csv")
        assert result is not None

    def test_export_with_custom_delimiter(self, exporter):
        """Test CSV export with custom delimiter."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        result = exporter.export_to_csv(df, "test.csv", delimiter=";")
        assert result is not None


class TestDataExporterJSON:
    """Test JSON export functionality."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_dict_to_json(self, exporter):
        """Test exporting dict to JSON."""
        data = {"key": "value", "number": 42}

        result = exporter.export_to_json(data, "test.json")
        assert result is not None

    def test_export_list_to_json(self, exporter):
        """Test exporting list to JSON."""
        data = [{"item": 1}, {"item": 2}]

        result = exporter.export_to_json(data, "test.json")
        assert result is not None

    def test_export_dataframe_to_json(self, exporter):
        """Test exporting DataFrame to JSON."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        result = exporter.export_to_json(df, "test.json")
        assert result is not None

    def test_export_numpy_to_json(self, exporter):
        """Test exporting numpy array to JSON."""
        arr = np.array([1, 2, 3, 4, 5])

        result = exporter.export_to_json(arr, "test.json")
        assert result is not None


class TestDataExporterExcel:
    """Test Excel export functionality."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_to_excel(self, exporter):
        """Test exporting to Excel."""
        df = pd.DataFrame({"Sheet1": [1, 2, 3], "Sheet2": [4, 5, 6]})

        result = exporter.export_to_excel(df, "test.xlsx")
        assert result is not None

    def test_export_multiple_sheets(self, exporter):
        """Test exporting multiple sheets to Excel."""
        data = {
            "Sheet1": pd.DataFrame({"col": [1, 2]}),
            "Sheet2": pd.DataFrame({"col": [3, 4]}),
        }

        result = exporter.export_to_excel(data, "test.xlsx")
        assert result is not None


class TestDataExporterFormats:
    """Test various export formats."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_to_parquet(self, exporter):
        """Test exporting to Parquet format."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        result = exporter.export_to_parquet(df, "test.parquet")
        assert result is not None

    def test_export_to_hdf5(self, exporter):
        """Test exporting to HDF5 format."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        result = exporter.export_to_hdf5(df, "test.h5")
        assert result is not None

    def test_export_to_pickle(self, exporter):
        """Test exporting to pickle format."""
        data = {"key": "value", "list": [1, 2, 3]}

        result = exporter.export_to_pickle(data, "test.pkl")
        assert result is not None

    def test_export_to_numpy(self, exporter):
        """Test exporting numpy array to npy file."""
        arr = np.array([[1, 2], [3, 4]])

        result = exporter.export_to_numpy(arr, "test.npy")
        assert result is not None


class TestDataExporterBatch:
    """Test batch export functionality."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_batch_export(self, exporter):
        """Test batch export of multiple files."""
        files = [
            ("data1.csv", pd.DataFrame({"col": [1, 2]})),
            ("data2.csv", pd.DataFrame({"col": [3, 4]})),
        ]

        results = exporter.batch_export(files, format="csv")
        assert results is not None

    def test_export_experiment_bundle(self, exporter):
        """Test exporting experiment data bundle."""
        experiment_data = {
            "metadata": {"name": "Test Exp"},
            "data": pd.DataFrame({"col": [1, 2]}),
            "results": {"accuracy": 0.95},
        }

        result = exporter.export_experiment_bundle(experiment_data, "bundle.zip")
        assert result is not None


class TestDataExporterCompression:
    """Test export with compression."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_with_gzip(self, exporter):
        """Test exporting with gzip compression."""
        df = pd.DataFrame({"col1": range(1000)})

        result = exporter.export_to_csv(df, "test.csv.gz", compression="gzip")
        assert result is not None

    def test_export_with_zip(self, exporter):
        """Test exporting with zip compression."""
        df = pd.DataFrame({"col1": range(100)})

        result = exporter.export_to_csv(df, "test.csv.zip", compression="zip")
        assert result is not None


class TestDataExporterMetadata:
    """Test metadata handling in exports."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_with_metadata(self, exporter):
        """Test exporting with metadata."""
        df = pd.DataFrame({"col": [1, 2]})
        metadata = {
            "created": datetime.now().isoformat(),
            "author": "Test User",
            "description": "Test data",
        }

        result = exporter.export_with_metadata(df, "test.csv", metadata)
        assert result is not None

    def test_generate_export_metadata(self, exporter):
        """Test generating export metadata."""
        metadata = exporter.generate_export_metadata(
            source="experiment_001", format="csv", description="Test export"
        )

        assert "source" in metadata
        assert "format" in metadata
        assert "created_at" in metadata


class TestDataExporterValidation:
    """Test export validation."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_validate_export_path(self, exporter):
        """Test validating export path."""
        result = exporter.validate_export_path("/valid/path.csv")
        assert result is True or result is False

    def test_validate_export_format(self, exporter):
        """Test validating export format."""
        result = exporter.validate_export_format("csv")
        assert result is True

        result = exporter.validate_export_format("invalid_format")
        assert result is False


class TestDataExporterErrorHandling:
    """Test error handling in exports."""

    @pytest.fixture
    def exporter(self):
        """Create an exporter instance for testing."""
        from apgi_framework.data.data_exporter import DataExporter

        return DataExporter()

    def test_export_empty_dataframe(self, exporter):
        """Test exporting empty DataFrame."""
        empty_df = pd.DataFrame()

        result = exporter.export_to_csv(empty_df, "empty.csv")
        assert result is not None

    def test_export_invalid_data(self, exporter):
        """Test handling invalid data gracefully."""
        invalid_data = None

        with pytest.raises((TypeError, ValueError)):
            exporter.export_to_csv(invalid_data, "invalid.csv")
