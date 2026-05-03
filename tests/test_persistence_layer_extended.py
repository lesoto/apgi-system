"""
Extended Persistence Layer Coverage Tests

Tests PersistenceLayer initialization, data operations, and backend handling.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apgi_framework.data.persistence_layer import PersistenceError, PersistenceLayer


class TestPersistenceLayerInit:
    """Test PersistenceLayer initialization."""

    def test_init_hdf5_backend(self, tmp_path):
        """Test initialization with HDF5 backend."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        assert layer.storage_path == tmp_path
        assert layer.backend == "hdf5"
        assert layer.hdf5_available is True

    def test_init_sqlite_backend(self, tmp_path):
        """Test initialization with SQLite backend."""
        layer = PersistenceLayer(str(tmp_path), backend="sqlite")
        assert layer.backend == "sqlite"
        assert layer.sqlite_available is True

    def test_init_hybrid_backend(self, tmp_path):
        """Test initialization with hybrid backend."""
        layer = PersistenceLayer(str(tmp_path), backend="hybrid")
        assert layer.backend == "hybrid"

    def test_init_creates_directories(self, tmp_path):
        """Test that initialization creates required directories."""
        _ = PersistenceLayer(str(tmp_path))

        assert (tmp_path / "metadata").exists()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "backups").exists()

    def test_init_invalid_backend_raises(self, tmp_path):
        """Test that invalid backend raises PersistenceError."""
        with pytest.raises(PersistenceError, match="Unknown backend"):
            _ = PersistenceLayer(str(tmp_path), backend="invalid")


class TestExperimentIdValidation:
    """Test experiment ID validation."""

    def test_validate_valid_experiment_id(self, tmp_path):
        """Test valid experiment IDs pass validation."""
        layer = PersistenceLayer(str(tmp_path))

        # Should not raise
        layer._validate_experiment_id("valid_id_123")
        layer._validate_experiment_id("test-experiment")
        layer._validate_experiment_id("experiment_2024")

    def test_validate_invalid_experiment_id_raises(self, tmp_path):
        """Test invalid experiment IDs raise error."""
        layer = PersistenceLayer(str(tmp_path))

        with pytest.raises(PersistenceError, match="Invalid experiment_id"):
            layer._validate_experiment_id("../path_traversal")

        with pytest.raises(PersistenceError, match="Invalid experiment_id"):
            layer._validate_experiment_id("id with spaces")

        with pytest.raises(PersistenceError, match="Invalid experiment_id"):
            layer._validate_experiment_id("id;with&special")


class TestPersistenceLayerStorage:
    """Test PersistenceLayer data storage operations."""

    def test_save_and_load_numpy(self, tmp_path):
        """Test saving and loading numpy arrays."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        layer.save_numpy("test_exp", "test_array", test_data)
        loaded = layer.load_numpy("test_exp", "test_array")

        np.testing.assert_array_equal(test_data, loaded)

    def test_save_and_load_dataframe(self, tmp_path):
        """Test saving and loading pandas DataFrames."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

        layer.save_dataframe("test_exp", "test_df", test_df)
        loaded = layer.load_dataframe("test_exp", "test_df")

        pd.testing.assert_frame_equal(test_df, loaded)

    def test_save_and_load_metadata(self, tmp_path):
        """Test saving and loading metadata."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        metadata = {"experiment": "test", "date": "2024-01-01", "version": 1.0}

        layer.save_metadata("test_exp", metadata)
        loaded = layer.load_metadata("test_exp")

        assert metadata == loaded

    def test_exists_returns_true_for_existing(self, tmp_path):
        """Test exists returns True for existing experiment."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_data = np.array([1.0, 2.0])

        layer.save_numpy("exists_test", "data", test_data)
        assert layer.exists("exists_test") is True

    def test_exists_returns_false_for_nonexistent(self, tmp_path):
        """Test exists returns False for non-existent experiment."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        assert layer.exists("nonexistent") is False


class TestPersistenceLayerDeletion:
    """Test PersistenceLayer deletion operations."""

    def test_delete_experiment(self, tmp_path):
        """Test deleting an experiment."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_data = np.array([1.0, 2.0, 3.0])

        layer.save_numpy("delete_test", "data", test_data)
        assert layer.exists("delete_test") is True

        layer.delete_experiment("delete_test")
        assert layer.exists("delete_test") is False


class TestPersistenceLayerListing:
    """Test PersistenceLayer listing operations."""

    def test_list_experiments_empty(self, tmp_path):
        """Test listing experiments when empty."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")

        experiments = layer.list_experiments()
        assert experiments == []

    def test_list_experiments_with_data(self, tmp_path):
        """Test listing experiments with saved data."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")

        layer.save_numpy("exp1", "data", np.array([1, 2, 3]))
        layer.save_numpy("exp2", "data", np.array([4, 5, 6]))

        experiments = layer.list_experiments()
        assert "exp1" in experiments
        assert "exp2" in experiments


class TestPersistenceLayerBackup:
    """Test PersistenceLayer backup operations."""

    def test_create_backup(self, tmp_path):
        """Test creating a backup of experiment."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_data = np.array([1.0, 2.0, 3.0])

        layer.save_numpy("backup_test", "data", test_data)
        backup_path = layer.create_backup("backup_test")

        assert backup_path is not None
        assert Path(backup_path).exists()

    def test_restore_from_backup(self, tmp_path):
        """Test restoring experiment from backup."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")
        test_data = np.array([1.0, 2.0, 3.0])

        layer.save_numpy("restore_test", "data", test_data)
        backup_path = layer.create_backup("restore_test")

        # Delete and restore
        layer.delete_experiment("restore_test")
        assert layer.exists("restore_test") is False

        layer.restore_from_backup("restore_test", backup_path)
        assert layer.exists("restore_test") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
