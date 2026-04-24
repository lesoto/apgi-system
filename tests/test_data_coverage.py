"""
Tests for data management modules.

This module contains comprehensive tests for data management functionality,
including data validation, export, and storage management.
"""

import pytest
import json
import os
import tempfile
import numpy as np

from apgi_framework.data.data_validator import DataValidator
from apgi_framework.data.data_exporter import DataExporter
from apgi_framework.data.storage_manager import StorageManager


class TestDataValidator:
    """Tests for DataValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a DataValidator instance."""
        return DataValidator()

    def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None

    def test_validate_numeric_array(self, validator):
        """Test validating numeric arrays."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        is_valid, errors = validator.validate_numeric_array(data)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_empty_array(self, validator):
        """Test validating empty arrays."""
        data = np.array([])
        is_valid, errors = validator.validate_numeric_array(data)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_with_nan_values(self, validator):
        """Test validation with NaN values."""
        data = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        is_valid, errors = validator.validate_numeric_array(data)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_with_inf_values(self, validator):
        """Test validation with infinity values."""
        data = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        is_valid, errors = validator.validate_numeric_array(data)

        assert isinstance(is_valid, bool)

    def test_validate_data_structure(self, validator):
        """Test validating data structures."""
        data = {
            "trial_id": "test_001",
            "timestamp": 1234567890.0,
            "values": [1.0, 2.0, 3.0],
        }
        result = validator.validate_data_structure(data)

        assert isinstance(result, dict)
        assert "is_valid" in result
        assert "errors" in result
        assert isinstance(result["is_valid"], bool)
        assert isinstance(result["errors"], list)

    def test_validate_missing_required_fields(self, validator):
        """Test validation with missing required fields."""
        required_fields = ["trial_id", "timestamp", "values"]
        data = {"trial_id": "test_001", "values": [1.0, 2.0, 3.0]}
        is_valid, errors = validator.validate_required_fields(data, required_fields)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_data_types(self, validator):
        """Test validating data types."""
        data = {"id": "test_001", "count": 100, "value": 3.14, "active": True}
        type_schema = {"id": str, "count": int, "value": float, "active": bool}
        is_valid, errors = validator.validate_types(data, type_schema)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_range(self, validator):
        """Test validating value ranges."""
        data = {"confidence": 0.95, "threshold": 0.5}
        ranges = {"confidence": (0.0, 1.0), "threshold": (0.0, 1.0)}
        is_valid, errors = validator.validate_ranges(data, ranges)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

    def test_validate_out_of_range_values(self, validator):
        """Test validation with out of range values."""
        data = {"confidence": 1.5, "threshold": 0.5}  # Out of 0-1 range
        ranges = {"confidence": (0.0, 1.0), "threshold": (0.0, 1.0)}
        is_valid, errors = validator.validate_ranges(data, ranges)

        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


class TestDataExporter:
    """Tests for DataExporter class."""

    @pytest.fixture
    def exporter(self):
        """Create a DataExporter instance."""
        return DataExporter()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialization(self, exporter):
        """Test exporter initialization."""
        assert exporter is not None

    def test_export_to_json(self, exporter, temp_dir):
        """Test exporting data to JSON."""
        data = {
            "experiment_id": "exp_001",
            "results": [1.0, 2.0, 3.0],
            "metadata": {"subject": "S001"},
        }
        filepath = os.path.join(temp_dir, "test_export.json")

        exporter.export_to_json(data, filepath)

        assert os.path.exists(filepath)

        # Verify content
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data["experiment_id"] == "exp_001"

    def test_export_to_csv(self, exporter, temp_dir):
        """Test exporting data to CSV."""
        import pandas as pd

        data = pd.DataFrame(
            {
                "trial": [1, 2, 3],
                "value": [1.5, 2.5, 3.5],
                "correct": [True, False, True],
            }
        )
        filepath = os.path.join(temp_dir, "test_export.csv")

        exporter.export_to_csv(data, filepath)

        assert os.path.exists(filepath)

    def test_export_numpy_array(self, exporter, temp_dir):
        """Test exporting numpy array."""
        data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        filepath = os.path.join(temp_dir, "test_array.npy")

        exporter.export_numpy(data, filepath)

        assert os.path.exists(filepath)

    def test_export_formats(self, exporter):
        """Test supported export formats."""
        formats = exporter.get_supported_formats()

        assert isinstance(formats, list)
        assert len(formats) > 0


class TestStorageManager:
    """Tests for StorageManager class."""

    @pytest.fixture
    def storage_manager(self):
        """Create a StorageManager instance."""
        return StorageManager()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialization(self, storage_manager):
        """Test storage manager initialization."""
        assert storage_manager is not None

    def test_save_and_load_data(self, storage_manager, temp_dir):
        """Test saving and loading data."""
        data = {"experiment_id": "exp_001", "results": [1.0, 2.0, 3.0]}
        filepath = os.path.join(temp_dir, "test_data.json")

        storage_manager.save(data, filepath)
        loaded_data = storage_manager.load(filepath)

        assert loaded_data["experiment_id"] == "exp_001"
        assert loaded_data["results"] == [1.0, 2.0, 3.0]

    def test_exists_check(self, storage_manager, temp_dir):
        """Test file existence check."""
        filepath = os.path.join(temp_dir, "nonexistent.json")

        assert not storage_manager.exists(filepath)

        # Create file and check again
        with open(filepath, "w") as f:
            f.write("{}")

        assert storage_manager.exists(filepath)

    def test_delete_data(self, storage_manager, temp_dir):
        """Test deleting stored data."""
        filepath = os.path.join(temp_dir, "to_delete.json")

        with open(filepath, "w") as f:
            json.dump({"data": "test"}, f)

        assert os.path.exists(filepath)

        storage_manager.delete(filepath)

        assert not os.path.exists(filepath)

    def test_list_files(self, storage_manager, temp_dir):
        """Test listing files in directory."""
        # Create test files
        for i in range(3):
            filepath = os.path.join(temp_dir, f"file_{i}.json")
            with open(filepath, "w") as f:
                f.write("{}")

        files = storage_manager.list_files(temp_dir, pattern="*.json")

        assert isinstance(files, list)
        assert len(files) == 3

    def test_get_file_info(self, storage_manager, temp_dir):
        """Test getting file information."""
        filepath = os.path.join(temp_dir, "test_info.json")

        with open(filepath, "w") as f:
            json.dump({"key": "value"}, f)

        info = storage_manager.get_file_info(filepath)

        assert isinstance(info, dict)
        assert "size" in info
        assert "modified" in info

    def test_batch_save(self, storage_manager, temp_dir):
        """Test batch save operation."""
        datasets = {"data1": {"value": 1}, "data2": {"value": 2}, "data3": {"value": 3}}

        results = storage_manager.batch_save(datasets, temp_dir)

        assert isinstance(results, dict)
        assert all(results.values())  # All saves should succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
