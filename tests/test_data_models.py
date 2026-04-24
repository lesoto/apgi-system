"""
Test suite for apgi_framework.data.data_models module.

Provides coverage for data model classes including DataVersion, ExperimentMetadata,
BackupInfo, and ExperimentalDataset.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from apgi_framework.data.data_models import (
    DataVersion,
    ExperimentMetadata,
    BackupInfo,
    ExperimentalDataset,
)


class TestDataVersion:
    """Tests for DataVersion dataclass."""

    def test_data_version_default_init(self):
        """Test DataVersion initialization with defaults."""
        version = DataVersion()

        assert version.version_id is not None
        assert version.version_number == "1.0.0"
        assert isinstance(version.created_at, datetime)
        assert version.created_by == "system"
        assert version.description == ""
        assert version.parent_version is None
        assert version.checksum == ""
        assert version.size_bytes == 0

    def test_data_version_custom_init(self):
        """Test DataVersion initialization with custom values."""
        version = DataVersion(
            version_number="2.0.0",
            created_by="test_user",
            description="Test version",
            parent_version="1.0.0",
            checksum="abc123",
            size_bytes=1024,
        )

        assert version.version_number == "2.0.0"
        assert version.created_by == "test_user"
        assert version.description == "Test version"
        assert version.parent_version == "1.0.0"
        assert version.checksum == "abc123"
        assert version.size_bytes == 1024

    def test_data_version_uuid_generation(self):
        """Test that DataVersion generates unique UUIDs."""
        version1 = DataVersion()
        version2 = DataVersion()

        assert version1.version_id != version2.version_id
        assert len(version1.version_id) == 36  # UUID length


class TestExperimentMetadata:
    """Tests for ExperimentMetadata dataclass."""

    def test_experiment_metadata_default_init(self):
        """Test ExperimentMetadata initialization with defaults."""
        metadata = ExperimentMetadata()

        assert metadata.experiment_id is not None
        assert metadata.experiment_name == ""
        assert metadata.description == ""
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        assert metadata.researcher == ""
        assert metadata.institution == ""
        assert metadata.n_participants == 0
        assert metadata.n_trials == 0
        assert metadata.conditions == []
        assert metadata.parameters == {}
        assert metadata.data_format == "hdf5"
        assert metadata.file_paths == []
        assert metadata.total_size_mb == 0.0
        assert metadata.current_version == "1.0.0"
        assert metadata.version_history == []
        assert metadata.tags == []
        assert metadata.category == "falsification_test"
        assert metadata.data_quality_score == 1.0
        assert metadata.completeness_percentage == 100.0
        assert metadata.validation_status == "pending"

    def test_experiment_metadata_custom_init(self):
        """Test ExperimentMetadata initialization with custom values."""
        metadata = ExperimentMetadata(
            experiment_name="Test Experiment",
            description="A test experiment",
            researcher="Dr. Test",
            institution="Test University",
            n_participants=50,
            n_trials=100,
            conditions=["condition_a", "condition_b"],
            parameters={"param1": 1.0, "param2": 2.0},
            data_format="csv",
            tags=["test", "experiment"],
            category="test_category",
        )

        assert metadata.experiment_name == "Test Experiment"
        assert metadata.description == "A test experiment"
        assert metadata.researcher == "Dr. Test"
        assert metadata.institution == "Test University"
        assert metadata.n_participants == 50
        assert metadata.n_trials == 100
        assert metadata.conditions == ["condition_a", "condition_b"]
        assert metadata.parameters == {"param1": 1.0, "param2": 2.0}
        assert metadata.data_format == "csv"
        assert metadata.tags == ["test", "experiment"]
        assert metadata.category == "test_category"

    def test_experiment_metadata_uuid_generation(self):
        """Test that ExperimentMetadata generates unique UUIDs."""
        metadata1 = ExperimentMetadata()
        metadata2 = ExperimentMetadata()

        assert metadata1.experiment_id != metadata2.experiment_id


class TestBackupInfo:
    """Tests for BackupInfo dataclass."""

    def test_backup_info_default_init(self):
        """Test BackupInfo initialization with defaults."""
        backup = BackupInfo()

        assert backup.backup_id is not None
        assert backup.backup_path == ""
        assert isinstance(backup.created_at, datetime)
        assert backup.backup_type == "full"
        assert backup.size_bytes == 0
        assert backup.checksum == ""
        assert backup.compression_ratio == 1.0
        assert backup.retention_days == 30
        assert backup.status == "active"

    def test_backup_info_custom_init(self):
        """Test BackupInfo initialization with custom values."""
        backup = BackupInfo(
            backup_path="/path/to/backup",
            backup_type="incremental",
            size_bytes=1024000,
            checksum="def456",
            compression_ratio=0.5,
            retention_days=90,
            status="archived",
        )

        assert backup.backup_path == "/path/to/backup"
        assert backup.backup_type == "incremental"
        assert backup.size_bytes == 1024000
        assert backup.checksum == "def456"
        assert backup.compression_ratio == 0.5
        assert backup.retention_days == 90
        assert backup.status == "archived"


class TestExperimentalDataset:
    """Tests for ExperimentalDataset dataclass."""

    def test_experimental_dataset_default_init(self):
        """Test ExperimentalDataset initialization with defaults."""
        metadata = ExperimentMetadata()
        dataset = ExperimentalDataset(metadata=metadata)

        assert dataset.metadata == metadata
        assert dataset.data == {}
        assert dataset.raw_data is None
        assert dataset.processed_data is None
        assert dataset.analysis_results is None
        assert dataset.storage_path is None
        assert dataset.backup_info == []
        assert dataset.access_permissions == {}
        assert dataset.is_locked is False
        assert dataset.lock_reason == ""

    def test_experimental_dataset_custom_init(self):
        """Test ExperimentalDataset initialization with custom values."""
        metadata = ExperimentMetadata(experiment_name="Test")
        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"trials": [1, 2, 3]},
            raw_data={"raw": "data"},
            processed_data={"processed": "data"},
            analysis_results={"results": "analysis"},
            storage_path=Path("/test/path"),
            is_locked=True,
            lock_reason="Maintenance",
        )

        assert dataset.metadata.experiment_name == "Test"
        assert dataset.data == {"trials": [1, 2, 3]}
        assert dataset.raw_data == {"raw": "data"}
        assert dataset.processed_data == {"processed": "data"}
        assert dataset.analysis_results == {"results": "analysis"}
        assert dataset.storage_path == Path("/test/path")
        assert dataset.is_locked is True
        assert dataset.lock_reason == "Maintenance"

    def test_experimental_dataset_post_init(self):
        """Test that __post_init__ sets metadata fields correctly."""
        metadata = ExperimentMetadata()
        # Clear the experiment_id to test __post_init__ generation
        metadata.experiment_id = ""

        dataset = ExperimentalDataset(metadata=metadata)
        # __post_init__ should generate experiment_id if empty
        assert dataset.metadata.experiment_id is not None
        assert len(dataset.metadata.experiment_id) > 0
        # updated_at should be set to now
        assert dataset.metadata.updated_at is not None


class TestDataModelIntegration:
    """Integration tests for data models working together."""

    def test_full_experiment_workflow(self):
        """Test creating a complete experiment with all data models."""
        # Create version history
        version1 = DataVersion(version_number="1.0.0", description="Initial version")
        version2 = DataVersion(
            version_number="2.0.0",
            description="Updated version",
            parent_version=version1.version_id,
        )

        # Create metadata with version history
        metadata = ExperimentMetadata(
            experiment_name="Full Test Experiment",
            researcher="Dr. Integration",
            n_participants=100,
            version_history=[version1, version2],
            current_version="2.0.0",
        )

        # Create backup info
        backup = BackupInfo(
            backup_path="/backup/experiment",
            size_bytes=1048576,
            backup_type="full",
        )

        # Create dataset
        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"participants": list(range(100))},
            backup_info=[backup],
        )

        # Verify relationships
        assert len(dataset.metadata.version_history) == 2
        assert dataset.metadata.version_history[0].version_number == "1.0.0"
        assert dataset.metadata.version_history[1].version_number == "2.0.0"
        assert len(dataset.backup_info) == 1
        assert dataset.backup_info[0].backup_path == "/backup/experiment"

    def test_dataset_locking(self):
        """Test dataset locking mechanism."""
        metadata = ExperimentMetadata()
        dataset = ExperimentalDataset(metadata=metadata)

        # Initially unlocked
        assert not dataset.is_locked
        assert dataset.lock_reason == ""

        # Lock the dataset
        dataset.is_locked = True
        dataset.lock_reason = "Data integrity check"

        assert dataset.is_locked
        assert dataset.lock_reason == "Data integrity check"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
