"""
Extended Storage Manager Coverage Tests

Tests StorageManager initialization, dataset operations, querying, and error handling.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from apgi_framework.data.data_models import ExperimentalDataset, ExperimentMetadata
from apgi_framework.data.storage_manager import StorageError, StorageManager


class TestStorageManagerInit:
    """Test StorageManager initialization."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_init_default_path(self, mock_validator_class, mock_persistence_class):
        """Test initialization with default storage path."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()

        assert manager.storage_path == Path("./data")
        assert manager.backend == "hdf5"
        assert manager.auto_validate is True
        assert manager.auto_backup is True

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_init_custom_path(self, mock_validator_class, mock_persistence_class):
        """Test initialization with custom storage path."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager("/custom/path", backend="sqlite")

        assert manager.storage_path == Path("/custom/path")
        assert manager.backend == "sqlite"

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_init_hybrid_backend(self, mock_validator_class, mock_persistence_class):
        """Test initialization with hybrid backend."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager(backend="hybrid")

        assert manager.backend == "hybrid"

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_init_disables_auto_validate(self, mock_validator_class, mock_persistence_class):
        """Test initialization with auto_validate disabled."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager(auto_validate=False, auto_backup=False)

        assert manager.auto_validate is False
        assert manager.auto_backup is False


class TestStorageManagerStatsCache:
    """Test StorageManager statistics caching."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_stats_cache_initialized_none(self, mock_validator_class, mock_persistence_class):
        """Test that stats cache is initialized as None."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()

        assert manager._stats_cache is None
        assert manager._stats_cache_time is None


class TestStorageManagerStoreDataset:
    """Test StorageManager dataset storage."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_store_dataset_with_validation(self, mock_validator_class, mock_persistence_class):
        """Test storing dataset with validation enabled."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_persistence.store_dataset.return_value = "exp_123"

        mock_validator = Mock()
        mock_validator.validate_dataset.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": ["minor warning"],
        }
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        dataset = Mock(spec=ExperimentalDataset)

        result = manager.store_dataset(dataset, validate=True)

        assert result == "exp_123"
        mock_validator.validate_dataset.assert_called_once_with(dataset)

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_store_dataset_validation_failure(self, mock_validator_class, mock_persistence_class):
        """Test storing dataset with validation failure."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator.validate_dataset.return_value = {
            "is_valid": False,
            "errors": ["Invalid data format"],
            "warnings": [],
        }
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        dataset = Mock(spec=ExperimentalDataset)

        with pytest.raises(StorageError, match="Dataset validation failed"):
            manager.store_dataset(dataset, validate=True)

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_store_dataset_without_validation(self, mock_validator_class, mock_persistence_class):
        """Test storing dataset without validation."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence
        mock_persistence.store_dataset.return_value = "exp_456"

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        dataset = Mock(spec=ExperimentalDataset)

        result = manager.store_dataset(dataset, validate=False)

        assert result == "exp_456"
        mock_validator.validate_dataset.assert_not_called()


class TestStorageManagerLoadDataset:
    """Test StorageManager dataset loading."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_load_dataset_success(self, mock_validator_class, mock_persistence_class):
        """Test successful dataset loading."""
        mock_persistence = Mock()
        mock_dataset = Mock(spec=ExperimentalDataset)
        mock_persistence.load_dataset.return_value = mock_dataset
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        result = manager.load_dataset("exp_123")

        assert result is mock_dataset
        mock_persistence.load_dataset.assert_called_once_with("exp_123", None)

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_load_dataset_with_version(self, mock_validator_class, mock_persistence_class):
        """Test loading specific dataset version."""
        mock_persistence = Mock()
        mock_dataset = Mock(spec=ExperimentalDataset)
        mock_persistence.load_dataset.return_value = mock_dataset
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        result = manager.load_dataset("exp_123", version="v1.0")

        assert result is mock_dataset
        mock_persistence.load_dataset.assert_called_once_with("exp_123", "v1.0")


class TestStorageManagerQueryDatasets:
    """Test StorageManager dataset querying."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_query_datasets_no_filter(self, mock_validator_class, mock_persistence_class):
        """Test querying datasets without filter."""
        mock_persistence = Mock()
        mock_persistence.list_experiments.return_value = ["exp_1", "exp_2"]

        mock_metadata1 = Mock(spec=ExperimentMetadata)
        mock_metadata2 = Mock(spec=ExperimentMetadata)

        mock_dataset1 = Mock(spec=ExperimentalDataset)
        mock_dataset1.metadata = mock_metadata1
        mock_dataset2 = Mock(spec=ExperimentalDataset)
        mock_dataset2.metadata = mock_metadata2

        mock_persistence.load_dataset.side_effect = [mock_dataset1, mock_dataset2]
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        result = manager.query_datasets()

        assert len(result) == 2


class TestStorageManagerDeleteDataset:
    """Test StorageManager dataset deletion."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_delete_dataset_success(self, mock_validator_class, mock_persistence_class):
        """Test successful dataset deletion."""
        mock_persistence = Mock()
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        manager.delete_dataset("exp_123")

        mock_persistence.delete_experiment.assert_called_once_with("exp_123")


class TestStorageManagerExists:
    """Test StorageManager dataset existence check."""

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_exists_returns_true(self, mock_validator_class, mock_persistence_class):
        """Test exists returns True for existing dataset."""
        mock_persistence = Mock()
        mock_persistence.exists.return_value = True
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        result = manager.exists("exp_123")

        assert result is True

    @patch("apgi_framework.data.storage_manager.PersistenceLayer")
    @patch("apgi_framework.data.storage_manager.DataValidator")
    def test_exists_returns_false(self, mock_validator_class, mock_persistence_class):
        """Test exists returns False for non-existent dataset."""
        mock_persistence = Mock()
        mock_persistence.exists.return_value = False
        mock_persistence_class.return_value = mock_persistence

        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        manager = StorageManager()
        result = manager.exists("exp_123")

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
