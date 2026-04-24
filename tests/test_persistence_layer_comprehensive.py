"""
Comprehensive test suite for apgi_framework.data.persistence_layer module.

This module provides complete coverage for:
- PersistenceLayer initialization with different backends
- Data storage and retrieval operations
- Versioning and backup functionality
- SQLite, HDF5, and PostgreSQL backends
- Error handling and edge cases
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apgi_framework.data.persistence_layer import PersistenceError, PersistenceLayer
from apgi_framework.data.data_models import ExperimentMetadata


class TestPersistenceLayerInitialization:
    """Tests for PersistenceLayer initialization."""

    def test_default_hdf5_initialization(self):
        """Test initialization with default HDF5 backend."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            assert layer.storage_path == Path(temp_dir)
            assert layer.backend == "hdf5"
            assert layer.hdf5_available is True
            assert layer.sqlite_available is True
            assert Path(temp_dir).exists()
            assert (Path(temp_dir) / "metadata").exists()
            assert (Path(temp_dir) / "data").exists()
            assert (Path(temp_dir) / "backups").exists()

    def test_sqlite_initialization(self):
        """Test initialization with SQLite backend."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            assert layer.backend == "sqlite"
            assert Path(temp_dir).exists()
            # Check that SQLite database was created
            assert (Path(temp_dir) / "metadata" / "experiments.db").exists()

    def test_invalid_backend_error(self):
        """Test that invalid backend raises PersistenceError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(PersistenceError, match="Unknown backend"):
                PersistenceLayer(storage_path=temp_dir, backend="invalid")

    def test_directory_creation(self):
        """Test that storage directories are created on initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "new_storage"
            PersistenceLayer(storage_path=storage_path, backend="hdf5")

            assert storage_path.exists()
            assert (storage_path / "metadata").exists()
            assert (storage_path / "data").exists()
            assert (storage_path / "backups").exists()


class TestSQLiteBackend:
    """Tests for SQLite backend operations."""

    def test_sqlite_schema_creation(self):
        """Test that SQLite schema is created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            # Verify tables exist
            with sqlite3.connect(layer.db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]

                assert "experiments" in tables
                assert "versions" in tables
                assert "backups" in tables

    def test_sqlite_experiments_table_schema(self):
        """Test experiments table has correct columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            with sqlite3.connect(layer.db_path) as conn:
                cursor = conn.execute("PRAGMA table_info(experiments)")
                columns = {row[1] for row in cursor.fetchall()}

                assert "experiment_id" in columns
                assert "experiment_name" in columns
                assert "created_at" in columns
                assert "updated_at" in columns
                assert "n_participants" in columns


class TestExperimentIdValidation:
    """Tests for experiment ID validation."""

    def test_valid_experiment_id(self):
        """Test that valid experiment IDs pass validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            # Should not raise
            layer._validate_experiment_id("valid_id_123")
            layer._validate_experiment_id("experiment-1")
            layer._validate_experiment_id("test_ABC")

    def test_invalid_experiment_id_characters(self):
        """Test that invalid characters raise PersistenceError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            with pytest.raises(PersistenceError, match="Invalid experiment_id"):
                layer._validate_experiment_id("invalid/path")

            with pytest.raises(PersistenceError, match="Invalid experiment_id"):
                layer._validate_experiment_id("test.id")

            with pytest.raises(PersistenceError, match="Invalid experiment_id"):
                layer._validate_experiment_id("test@id")


class TestHDF5Operations:
    """Tests for HDF5 storage operations."""

    def test_store_and_retrieve_data(self):
        """Test storing and retrieving data with HDF5."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            # Create test data
            data = pd.DataFrame(
                {
                    "col1": [1, 2, 3, 4, 5],
                    "col2": ["a", "b", "c", "d", "e"],
                }
            )

            # Store data
            experiment_id = "test_exp_001"
            layer.store_data(experiment_id, data, format="hdf5")

            # Retrieve data
            retrieved = layer.retrieve_data(experiment_id)

            assert retrieved is not None
            assert len(retrieved) == len(data)
            assert list(retrieved.columns) == list(data.columns)
            pd.testing.assert_frame_equal(retrieved.reset_index(drop=True), data)

    def test_store_numpy_array(self):
        """Test storing and retrieving numpy arrays."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            # Create test array
            arr = np.random.randn(100, 10)

            experiment_id = "test_numpy_001"
            dataset_name = "features"

            layer.store_numpy_array(experiment_id, dataset_name, arr)

            # Retrieve array
            retrieved = layer.retrieve_numpy_array(experiment_id, dataset_name)

            assert retrieved is not None
            assert retrieved.shape == arr.shape
            np.testing.assert_array_almost_equal(retrieved, arr)


class TestDataVersioning:
    """Tests for data versioning operations."""

    def test_create_version(self):
        """Test creating a new data version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_version_exp"

            # Create initial version
            version = layer.create_version(
                experiment_id=experiment_id,
                version_number="1.0.0",
                description="Initial version",
            )

            assert version is not None
            assert version.experiment_id == experiment_id
            assert version.version_number == "1.0.0"

    def test_list_versions(self):
        """Test listing all versions for an experiment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_list_versions"

            # Create multiple versions
            layer.create_version(experiment_id, "1.0.0", "First")
            layer.create_version(experiment_id, "1.1.0", "Second")
            layer.create_version(experiment_id, "2.0.0", "Third")

            versions = layer.list_versions(experiment_id)

            assert len(versions) == 3
            version_numbers = [v.version_number for v in versions]
            assert "1.0.0" in version_numbers
            assert "1.1.0" in version_numbers
            assert "2.0.0" in version_numbers

    def test_get_version(self):
        """Test retrieving a specific version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_get_version"

            # Create version
            created = layer.create_version(experiment_id, "1.0.0", "Test version")

            # Retrieve it
            retrieved = layer.get_version(experiment_id, "1.0.0")

            assert retrieved is not None
            assert retrieved.version_id == created.version_id
            assert retrieved.version_number == "1.0.0"


class TestBackupOperations:
    """Tests for backup operations."""

    def test_create_backup(self):
        """Test creating a backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_backup_exp"

            # Create some data first
            data = pd.DataFrame({"value": [1, 2, 3]})
            layer.store_data(experiment_id, data)

            # Create backup
            backup = layer.create_backup(
                experiment_id=experiment_id,
                backup_type="full",
                retention_days=30,
            )

            assert backup is not None
            assert backup.experiment_id == experiment_id
            assert backup.backup_type == "full"

    def test_list_backups(self):
        """Test listing backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_list_backups"

            # Create data and backups
            data = pd.DataFrame({"value": [1, 2, 3]})
            layer.store_data(experiment_id, data)

            layer.create_backup(experiment_id, "full", 30)
            layer.create_backup(experiment_id, "incremental", 7)

            backups = layer.list_backups(experiment_id)

            assert len(backups) == 2

    def test_restore_backup(self):
        """Test restoring from backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_restore"

            # Create original data
            original_data = pd.DataFrame({"value": [1, 2, 3]})
            layer.store_data(experiment_id, original_data)

            # Create backup
            backup = layer.create_backup(experiment_id, "full", 30)

            # Modify data
            modified_data = pd.DataFrame({"value": [4, 5, 6]})
            layer.store_data(experiment_id, modified_data)

            # Restore from backup
            layer.restore_backup(backup.backup_id)

            # Verify data was restored
            restored = layer.retrieve_data(experiment_id)
            pd.testing.assert_frame_equal(restored, original_data)


class TestMetadataOperations:
    """Tests for experiment metadata operations."""

    def test_save_and_retrieve_metadata(self):
        """Test saving and retrieving experiment metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_metadata_exp"

            metadata = ExperimentMetadata(
                experiment_id=experiment_id,
                experiment_name="Test Experiment",
                description="A test experiment",
                researcher="Test Researcher",
                institution="Test Institution",
                n_participants=100,
                n_trials=50,
                created_at=datetime.now(),
            )

            # Save metadata
            layer.save_metadata(experiment_id, metadata)

            # Retrieve metadata
            retrieved = layer.get_metadata(experiment_id)

            assert retrieved is not None
            assert retrieved.experiment_id == experiment_id
            assert retrieved.experiment_name == "Test Experiment"
            assert retrieved.n_participants == 100

    def test_update_metadata(self):
        """Test updating experiment metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_update_metadata"

            # Create initial metadata
            metadata = ExperimentMetadata(
                experiment_id=experiment_id,
                experiment_name="Original Name",
                n_participants=50,
                created_at=datetime.now(),
            )
            layer.save_metadata(experiment_id, metadata)

            # Update metadata
            metadata.experiment_name = "Updated Name"
            metadata.n_participants = 100
            layer.save_metadata(experiment_id, metadata)

            # Verify update
            retrieved = layer.get_metadata(experiment_id)
            assert retrieved.experiment_name == "Updated Name"
            assert retrieved.n_participants == 100

    def test_list_experiments(self):
        """Test listing all experiments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            # Create multiple experiments
            for i in range(3):
                metadata = ExperimentMetadata(
                    experiment_id=f"exp_{i}",
                    experiment_name=f"Experiment {i}",
                    created_at=datetime.now(),
                )
                layer.save_metadata(f"exp_{i}", metadata)

            experiments = layer.list_experiments_with_metadata()

            assert len(experiments) == 3
            experiment_ids = [e.experiment_id for e in experiments]
            assert "exp_0" in experiment_ids
            assert "exp_1" in experiment_ids
            assert "exp_2" in experiment_ids


class TestDataExportImport:
    """Tests for data export and import operations."""

    def test_export_to_csv(self):
        """Test exporting data to CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            experiment_id = "test_export"
            data = pd.DataFrame(
                {
                    "col1": [1, 2, 3],
                    "col2": ["a", "b", "c"],
                }
            )

            layer.store_data(experiment_id, data)

            # Export to CSV
            export_path = Path(temp_dir) / "export.csv"
            layer.export_data(experiment_id, str(export_path), format="csv")

            assert export_path.exists()

            # Verify CSV content
            exported = pd.read_csv(export_path)
            pd.testing.assert_frame_equal(exported, data)

    def test_export_to_json(self):
        """Test exporting data to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            experiment_id = "test_export_json"
            data = pd.DataFrame(
                {
                    "col1": [1, 2, 3],
                    "col2": ["a", "b", "c"],
                }
            )

            layer.store_data(experiment_id, data)

            # Export to JSON
            export_path = Path(temp_dir) / "export.json"
            layer.export_data(experiment_id, str(export_path), format="json")

            assert export_path.exists()

            # Verify JSON content
            with open(export_path) as f:
                exported = json.load(f)
            assert len(exported) == 3

    def test_import_from_csv(self):
        """Test importing data from CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            # Create CSV file
            import_path = Path(temp_dir) / "import.csv"
            data = pd.DataFrame(
                {
                    "value": [10, 20, 30],
                    "label": ["x", "y", "z"],
                }
            )
            data.to_csv(import_path, index=False)

            experiment_id = "test_import"
            layer.import_data(experiment_id, str(import_path), format="csv")

            # Verify import
            retrieved = layer.retrieve_data(experiment_id)
            pd.testing.assert_frame_equal(retrieved, data)


class TestStorageStatistics:
    """Tests for storage statistics."""

    def test_get_storage_stats(self):
        """Test getting storage statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            # Create some data
            for i in range(3):
                data = pd.DataFrame({"value": range(100)})
                layer.store_data(f"exp_{i}", data)

            stats = layer.get_storage_stats()

            assert "total_experiments" in stats
            assert stats["total_experiments"] == 3
            assert "total_size_bytes" in stats
            assert "backend" in stats

    def test_get_experiment_size(self):
        """Test getting size of specific experiment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            experiment_id = "test_size_exp"
            data = pd.DataFrame({"value": range(1000)})
            layer.store_data(experiment_id, data)

            size = layer.get_experiment_size(experiment_id)

            assert size > 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_retrieve_nonexistent_data(self):
        """Test retrieving non-existent data raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="hdf5")

            with pytest.raises((PersistenceError, FileNotFoundError)):
                layer.retrieve_data("nonexistent_experiment")

    def test_get_nonexistent_metadata(self):
        """Test retrieving non-existent metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            result = layer.get_metadata("nonexistent")
            assert result is None

    def test_restore_nonexistent_backup(self):
        """Test restoring non-existent backup raises error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            with pytest.raises((PersistenceError, FileNotFoundError)):
                layer.restore_backup("nonexistent_backup_id")


class TestDataDeletion:
    """Tests for data deletion operations."""

    def test_delete_experiment(self):
        """Test deleting an experiment and all its data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_delete"

            # Create data
            data = pd.DataFrame({"value": [1, 2, 3]})
            layer.store_data(experiment_id, data)

            metadata = ExperimentMetadata(
                experiment_id=experiment_id,
                experiment_name="To Delete",
                created_at=datetime.now(),
            )
            layer.save_metadata(experiment_id, metadata)

            # Delete
            layer.delete_experiment(experiment_id)

            # Verify deletion
            with pytest.raises((PersistenceError, FileNotFoundError)):
                layer.retrieve_data(experiment_id)

            assert layer.get_metadata(experiment_id) is None

    def test_delete_version(self):
        """Test deleting a specific version."""
        with tempfile.TemporaryDirectory() as temp_dir:
            layer = PersistenceLayer(storage_path=temp_dir, backend="sqlite")

            experiment_id = "test_delete_version"

            # Create version
            version = layer.create_version(experiment_id, "1.0.0", "Test")

            # Delete version
            layer.delete_version(version.version_id)

            # Verify deletion
            versions = layer.list_versions(experiment_id)
            assert len(versions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
