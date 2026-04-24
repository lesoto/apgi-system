"""
Tests for StorageManager in apgi_framework/data/storage_manager.py.
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime
from apgi_framework.data.storage_manager import StorageManager, StorageError
from apgi_framework.data.data_models import (
    ExperimentalDataset,
    ExperimentMetadata,
    QueryFilter,
)


class TestStorageManager:
    @pytest.fixture
    def storage_path(self, tmp_path):
        return tmp_path / "storage"

    @pytest.fixture
    def storage_manager(self, storage_path):
        return StorageManager(storage_path=storage_path, backend="hdf5")

    @pytest.fixture
    def sample_dataset(self):
        dataset = MagicMock(spec=ExperimentalDataset)
        dataset.metadata = ExperimentMetadata(
            experiment_id="test_exp_1",
            experiment_name="Test Experiment",
            researcher="Test Researcher",
            institution="Test Institution",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            n_participants=10,
            n_trials=100,
            conditions=["cond1", "cond2"],
            parameters={},
            data_format="hdf5",
            total_size_mb=1.5,
            current_version="1.0.0",
            tags=["tag1"],
            category="unit_test",
            data_quality_score=0.9,
            completeness_percentage=100.0,
            validation_status="valid",
        )
        dataset.data = {}
        dataset.raw_data = None
        dataset.processed_data = None
        dataset.analysis_results = None
        dataset.backup_info = []
        return dataset

    def test_initialization(self, storage_path):
        manager = StorageManager(storage_path=storage_path)
        assert manager.storage_path == Path(storage_path)
        assert manager.backend == "hdf5"
        assert manager.auto_validate is True
        assert manager.auto_backup is True

    def test_store_dataset_success(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.validator, "validate_dataset") as mock_validate:
            with patch.object(storage_manager.persistence, "store_dataset") as mock_store:
                with patch.object(storage_manager.persistence, "create_backup") as mock_backup:
                    mock_validate.return_value = {
                        "is_valid": True,
                        "errors": [],
                        "warnings": [],
                        "quality_score": 0.9,
                    }
                    mock_store.return_value = "test_exp_1"

                    exp_id = storage_manager.store_dataset(sample_dataset)

                    assert exp_id == "test_exp_1"
                    mock_validate.assert_called_once_with(sample_dataset)
                    mock_store.assert_called_once_with(sample_dataset)
                    mock_backup.assert_called_once_with("test_exp_1")

    def test_store_dataset_validation_failure(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.validator, "validate_dataset") as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "errors": ["Invalid data"],
                "warnings": [],
            }

            with pytest.raises(StorageError, match="Dataset validation failed"):
                storage_manager.store_dataset(sample_dataset)

    def test_load_dataset(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.persistence, "load_dataset") as mock_load:
            mock_load.return_value = sample_dataset

            dataset = storage_manager.load_dataset("test_exp_1")

            assert dataset == sample_dataset
            mock_load.assert_called_once_with("test_exp_1", None)

    def test_query_datasets(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.persistence, "list_experiments") as mock_list:
            with patch.object(storage_manager.persistence, "load_dataset") as mock_load:
                mock_list.return_value = ["test_exp_1"]
                mock_load.return_value = sample_dataset

                results = storage_manager.query_datasets()

                assert len(results) == 1
                assert results[0].experiment_id == "test_exp_1"

    def test_apply_filters(self, storage_manager):
        m1 = MagicMock(spec=ExperimentMetadata)
        m1.experiment_id = "exp1"
        m1.researcher = "Alice"
        m1.institution = "UniA"
        m1.created_at = datetime(2024, 1, 1)
        m1.tags = ["tag1"]
        m1.category = "cat1"
        m1.n_participants = 10
        m1.conditions = ["cond1"]
        m1.validation_status = "valid"
        m1.data_format = "hdf5"

        metadata_list = [m1]

        # Test individual filters
        f1 = QueryFilter(experiment_ids=["exp1"])
        assert len(storage_manager._apply_filters(metadata_list, f1)) == 1

        f2 = QueryFilter(researcher="Alice")
        assert len(storage_manager._apply_filters(metadata_list, f2)) == 1

        f3 = QueryFilter(institution="UniA")
        assert len(storage_manager._apply_filters(metadata_list, f3)) == 1

        f4 = QueryFilter(date_range=(datetime(2023, 1, 1), datetime(2025, 1, 1)))
        assert len(storage_manager._apply_filters(metadata_list, f4)) == 1

        f5 = QueryFilter(tags=["tag1"])
        assert len(storage_manager._apply_filters(metadata_list, f5)) == 1

        f6 = QueryFilter(category="cat1")
        assert len(storage_manager._apply_filters(metadata_list, f6)) == 1

        f7 = QueryFilter(min_participants=5, max_participants=15)
        assert len(storage_manager._apply_filters(metadata_list, f7)) == 1

        f8 = QueryFilter(conditions=["cond1"])
        assert len(storage_manager._apply_filters(metadata_list, f8)) == 1

        f9 = QueryFilter(validation_status="valid")
        assert len(storage_manager._apply_filters(metadata_list, f9)) == 1

        f10 = QueryFilter(data_format="hdf5")
        assert len(storage_manager._apply_filters(metadata_list, f10)) == 1

    def test_update_dataset(self, storage_manager, sample_dataset):
        with patch.object(storage_manager, "load_dataset") as mock_load:
            with patch.object(storage_manager.persistence, "store_dataset") as mock_store:
                with patch.object(storage_manager.persistence, "_store_version") as mock_version:
                    mock_load.return_value = sample_dataset

                    updates = {
                        "metadata": {"experiment_name": "New Name"},
                        "data": {"key": "value"},
                    }

                    storage_manager.update_dataset("test_exp_1", updates)

                    assert sample_dataset.metadata.experiment_name == "New Name"
                    mock_store.assert_called_once()
                    mock_version.assert_called_once()

    def test_delete_dataset_with_confirmation(self, storage_manager):
        with patch.object(storage_manager.persistence, "delete_experiment") as mock_delete:
            res = storage_manager.delete_dataset("test_exp_1", confirm=True)
            assert res is True
            mock_delete.assert_called_once_with("test_exp_1")

    def test_delete_dataset_no_confirmation(self, storage_manager):
        with pytest.raises(StorageError, match="requires explicit confirmation"):
            storage_manager.delete_dataset("test_exp_1", confirm=False)

    def test_get_storage_stats(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.persistence, "list_experiments") as mock_list:
            with patch.object(storage_manager.persistence, "load_dataset") as mock_load:
                mock_list.return_value = ["test_exp_1"]
                mock_load.return_value = sample_dataset

                stats = storage_manager.get_storage_stats(refresh=True)

                assert stats.total_datasets == 1
                assert stats.total_size_mb == 1.5

    def test_validate_all_datasets(self, storage_manager, sample_dataset):
        with patch.object(storage_manager.persistence, "list_experiments") as mock_list:
            with patch.object(storage_manager, "load_dataset") as mock_load:
                with patch.object(storage_manager.validator, "validate_dataset") as mock_validate:
                    mock_list.return_value = ["test_exp_1"]
                    mock_load.return_value = sample_dataset
                    mock_validate.return_value = {
                        "is_valid": True,
                        "errors": [],
                        "warnings": [],
                        "quality_score": 0.9,
                    }

                    summary = storage_manager.validate_all_datasets()

                    assert summary["total_datasets"] == 1
                    assert summary["valid_datasets"] == 1

    def test_export_metadata_json(self, storage_manager, sample_dataset, tmp_path):
        with patch.object(storage_manager, "query_datasets") as mock_query:
            mock_query.return_value = [sample_dataset.metadata]
            output_path = tmp_path / "metadata.json"

            storage_manager.export_metadata(output_path, format="json")

            assert output_path.exists()
