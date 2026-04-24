"""
Tests for PersistenceLayer - verifying initialization and core operations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from apgi_framework.data.persistence_layer import PersistenceLayer, PersistenceError
from apgi_framework.data.data_models import ExperimentMetadata


class TestPersistenceLayer:
    """Focus on actual implementation coverage, not just mocking."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization_hdf5(self, temp_storage):
        """Test initialization with HDF5 backend (the fix we just made)."""
        persistence = PersistenceLayer(temp_storage, backend="hdf5")

        # Verify directories were created
        assert (temp_storage / "metadata").exists()
        assert (temp_storage / "data").exists()
        assert (temp_storage / "backups").exists()

        # Verify HDF5 file exists
        assert (temp_storage / "data" / "experiments.h5").exists()
        assert persistence.data_path == temp_storage / "data"

    def test_initialization_sqlite(self, temp_storage):
        """Test initialization with SQLite backend."""
        persistence = PersistenceLayer(temp_storage, backend="sqlite")
        _ = persistence
        assert persistence.backend == "sqlite"
        assert (temp_storage / "metadata" / "experiments.db").exists()

    def test_store_and_load_metadata_sqlite(self, temp_storage):
        """Test storing and loading metadata using SQLite."""
        persistence = PersistenceLayer(temp_storage, backend="sqlite")

        metadata = ExperimentMetadata(
            experiment_id="test_exp_001",
            experiment_name="Integration Test",
            researcher="Antigravity",
            n_participants=10,
            n_trials=100,
        )

        persistence._store_metadata_sqlite(metadata)
        loaded = persistence._load_metadata_sqlite("test_exp_001")

        assert loaded.experiment_id == "test_exp_001"
        assert loaded.experiment_name == "Integration Test"
        assert loaded.n_participants == 10

    def test_invalid_backend(self, temp_storage):
        """Test that invalid backend raises PersistenceError."""
        with pytest.raises(PersistenceError, match="Unknown backend"):
            PersistenceLayer(temp_storage, backend="invalid_backend")

    def test_experiment_id_validation(self, temp_storage):
        """Test validation of experiment IDs."""
        persistence = PersistenceLayer(temp_storage)

        # Valid IDs
        persistence._validate_experiment_id("valid-id_123")

        # Invalid IDs
        with pytest.raises(PersistenceError):
            persistence._validate_experiment_id("invalid/id")
        with pytest.raises(PersistenceError):
            persistence._validate_experiment_id("id with spaces")


if __name__ == "__main__":
    pytest.main([__file__])
