"""
Comprehensive tests for persistence_layer.py

Provides test coverage for the PersistenceLayer class with SQLite, HDF5, and backup functionality.
"""

import sqlite3

import numpy as np
import pytest

# Skip all tests if h5py is not available
try:
    import h5py

    HDF5_AVAILABLE = True
except ImportError:
    HDF5_AVAILABLE = False

try:
    from apgi_framework.data.persistence_layer import (
        PersistenceLayer,
        PersistenceError,
    )
    from apgi_framework.data.data_models import (
        DataVersion,
        ExperimentalDataset,
        ExperimentMetadata,
    )

    PERSISTENCE_AVAILABLE = True
except ImportError as e:
    PERSISTENCE_AVAILABLE = False
    print(f"Persistence layer not available: {e}")


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerInitialization:
    """Test PersistenceLayer initialization and backend setup."""

    def test_init_with_hdf5_backend(self, tmp_path):
        """Test initialization with HDF5 backend."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="hdf5")

        assert layer.storage_path == storage_path
        assert layer.backend == "hdf5"
        assert layer.hdf5_available is True
        assert layer.sqlite_available is True

        # Check directory structure
        assert (storage_path / "metadata").exists()
        assert (storage_path / "data").exists()
        assert (storage_path / "backups").exists()

        # Check HDF5 file creation
        if HDF5_AVAILABLE:
            assert (storage_path / "data" / "experiments.h5").exists()

    def test_init_with_sqlite_backend(self, tmp_path):
        """Test initialization with SQLite backend."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        assert layer.backend == "sqlite"
        assert (storage_path / "metadata" / "experiments.db").exists()

    def test_init_creates_directory_structure(self, tmp_path):
        """Test that initialization creates all required directories."""
        storage_path = tmp_path / "new_storage" / "nested"
        PersistenceLayer(str(storage_path), backend="hdf5")

        assert storage_path.exists()
        assert (storage_path / "metadata").is_dir()
        assert (storage_path / "data").is_dir()
        assert (storage_path / "backups").is_dir()

    def test_init_invalid_backend_raises_error(self, tmp_path):
        """Test that invalid backend raises PersistenceError."""
        with pytest.raises(PersistenceError):
            PersistenceLayer(str(tmp_path), backend="invalid")

    def test_validate_experiment_id_valid(self, tmp_path):
        """Test validation of valid experiment IDs."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")

        # Should not raise for valid IDs
        layer._validate_experiment_id("exp_001")
        layer._validate_experiment_id("Experiment-123")
        layer._validate_experiment_id("test_2024_01")

    def test_validate_experiment_id_invalid(self, tmp_path):
        """Test validation rejects invalid experiment IDs."""
        layer = PersistenceLayer(str(tmp_path), backend="hdf5")

        # Should raise for invalid IDs
        with pytest.raises(PersistenceError):
            layer._validate_experiment_id("../etc/passwd")  # Path traversal

        with pytest.raises(PersistenceError):
            layer._validate_experiment_id("exp;id")  # Semicolon

        with pytest.raises(PersistenceError):
            layer._validate_experiment_id("exp id")  # Space


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerSQLiteBackend:
    """Test SQLite backend functionality."""

    def test_sqlite_tables_created(self, tmp_path):
        """Test that SQLite creates required tables."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        # Connect and check tables exist
        conn = sqlite3.connect(layer.db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert "experiments" in tables
        assert "versions" in tables
        assert "backups" in tables
        conn.close()

    def test_store_and_load_metadata_sqlite(self, tmp_path):
        """Test storing and loading experiment metadata with SQLite."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        # Create test metadata
        metadata = ExperimentMetadata(
            experiment_id="test_exp_001",
            experiment_name="Test Experiment",
            description="A test experiment",
            researcher="Test Researcher",
            institution="Test Institution",
            n_participants=10,
            n_trials=100,
            conditions={"condition": "test"},
            parameters={"param": 1.0},
        )

        # Store metadata
        layer._store_metadata_sqlite(metadata)

        # Load metadata
        loaded = layer._load_metadata_sqlite("test_exp_001")

        assert loaded is not None
        assert loaded.experiment_id == "test_exp_001"
        assert loaded.experiment_name == "Test Experiment"
        assert loaded.researcher == "Test Researcher"

    def test_load_nonexistent_metadata_returns_none(self, tmp_path):
        """Test loading metadata for non-existent experiment returns None."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        result = layer._load_metadata_sqlite("nonexistent")
        assert result is None


@pytest.mark.skipif(
    not PERSISTENCE_AVAILABLE or not HDF5_AVAILABLE,
    reason="Persistence layer or HDF5 not available",
)
class TestPersistenceLayerHDF5Backend:
    """Test HDF5 backend functionality."""

    def test_hdf5_file_created(self, tmp_path):
        """Test that HDF5 file is created during initialization."""
        storage_path = tmp_path / "storage"
        PersistenceLayer(str(storage_path), backend="hdf5")

        hdf5_path = storage_path / "data" / "experiments.h5"
        assert hdf5_path.exists()

        # Verify attributes
        with h5py.File(hdf5_path, "r") as f:
            assert "created_at" in f.attrs
            assert "version" in f.attrs

    def test_store_and_load_dict_hdf5(self, tmp_path):
        """Test storing and loading dictionary data in HDF5."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="hdf5")

        # Create test dataset
        metadata = ExperimentMetadata(
            experiment_id="hdf5_test_001",
            experiment_name="HDF5 Test",
        )

        dataset = ExperimentalDataset(
            metadata=metadata,
            data={
                "signal": np.array([1.0, 2.0, 3.0]),
                "labels": ["a", "b", "c"],
                "nested": {"key": "value"},
            },
        )

        # Store dataset
        layer._store_data_hdf5(dataset)

        # Load data
        loaded = layer._load_data_hdf5("hdf5_test_001")

        assert "data" in loaded
        loaded_data = loaded["data"]
        assert np.array_equal(loaded_data["signal"], np.array([1.0, 2.0, 3.0]))
        assert loaded_data["labels"] == ["a", "b", "c"]


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerDatasetOperations:
    """Test dataset storage and loading operations."""

    def test_store_dataset_hdf5(self, tmp_path):
        """Test storing a complete dataset with hybrid backend (HDF5 + SQLite)."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="hybrid")

        metadata = ExperimentMetadata(
            experiment_id="store_test_001",
            experiment_name="Store Test",
        )

        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"test": "data"},
        )

        # Store dataset
        exp_id = layer.store_dataset(dataset)
        assert exp_id == "store_test_001"

        # Verify metadata stored via _load_metadata
        loaded_meta = layer._load_metadata("store_test_001")
        assert loaded_meta is not None

    def test_load_nonexistent_dataset_raises_error(self, tmp_path):
        """Test loading non-existent dataset raises PersistenceError."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        with pytest.raises(PersistenceError):
            layer.load_dataset("nonexistent_experiment")


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerVersioning:
    """Test data versioning functionality."""

    def test_store_version(self, tmp_path):
        """Test storing version information."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        version = DataVersion(
            version_number="1.0.0",
            description="Initial version",
            checksum="abc123",
        )

        layer._store_version("test_exp", version)

        # Verify version stored
        conn = sqlite3.connect(layer.db_path)
        cursor = conn.execute("SELECT * FROM versions WHERE experiment_id = ?", ("test_exp",))
        row = cursor.fetchone()
        assert row is not None
        assert row[2] == "1.0.0"  # version_number
        conn.close()


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerChecksum:
    """Test checksum functionality."""

    def test_calculate_checksum(self, tmp_path):
        """Test checksum calculation for datasets."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="hdf5")

        metadata = ExperimentMetadata(
            experiment_id="checksum_test",
            experiment_name="Checksum Test",
        )

        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"key": "value"},
        )

        checksum = layer._calculate_checksum(dataset)

        # Checksum should be a valid SHA-256 hash
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in checksum)


@pytest.mark.skipif(not PERSISTENCE_AVAILABLE, reason="Persistence layer not available")
class TestPersistenceLayerBackupInfo:
    """Test backup information loading."""

    def test_load_empty_backup_info(self, tmp_path):
        """Test loading backup info when no backups exist."""
        storage_path = tmp_path / "storage"
        layer = PersistenceLayer(str(storage_path), backend="sqlite")

        backups = layer._load_backup_info("test_exp")
        assert backups == []
