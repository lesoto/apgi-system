"""
Comprehensive tests for apgi_framework/data/data_models.py module.

This test module provides thorough coverage of the data models including:
- DataVersion dataclass
- ExperimentMetadata dataclass
- BackupInfo dataclass
- ExperimentalDataset dataclass

Target: Increase coverage from 0% to 95%+
"""

import uuid
from datetime import datetime
from pathlib import Path

import pytest

from apgi_framework.data.data_models import (
    BackupInfo,
    DataVersion,
    ExperimentalDataset,
    ExperimentMetadata,
)


class TestDataVersion:
    """Comprehensive tests for DataVersion dataclass."""

    def test_default_creation(self):
        """Test DataVersion creation with default values."""
        version = DataVersion()

        assert version.version_id is not None
        assert isinstance(version.version_id, str)
        assert len(version.version_id) == 36  # UUID format
        assert version.version_number == "1.0.0"
        assert isinstance(version.created_at, datetime)
        assert version.created_by == "system"
        assert version.description == ""
        assert version.parent_version is None
        assert version.checksum == ""
        assert version.size_bytes == 0

    def test_custom_creation(self):
        """Test DataVersion creation with custom values."""
        parent_id = str(uuid.uuid4())
        custom_time = datetime(2024, 1, 15, 10, 30, 0)

        version = DataVersion(
            version_id="custom-id-123",
            version_number="2.5.1",
            created_at=custom_time,
            created_by="researcher@institution.edu",
            description="Experimental dataset version",
            parent_version=parent_id,
            checksum="sha256:abc123def456",
            size_bytes=1024 * 1024 * 100,  # 100MB
        )

        assert version.version_id == "custom-id-123"
        assert version.version_number == "2.5.1"
        assert version.created_at == custom_time
        assert version.created_by == "researcher@institution.edu"
        assert version.description == "Experimental dataset version"
        assert version.parent_version == parent_id
        assert version.checksum == "sha256:abc123def456"
        assert version.size_bytes == 104857600

    def test_uuid_generation(self):
        """Test that unique UUIDs are generated for each instance."""
        version1 = DataVersion()
        version2 = DataVersion()

        assert version1.version_id != version2.version_id
        assert uuid.UUID(version1.version_id)
        assert uuid.UUID(version2.version_id)

    def test_timestamp_auto_generation(self):
        """Test that timestamps are auto-generated."""
        before = datetime.now()
        version = DataVersion()
        after = datetime.now()

        assert before <= version.created_at <= after

    def test_field_types(self):
        """Test that all fields have correct types."""
        version = DataVersion()

        assert isinstance(version.version_id, str)
        assert isinstance(version.version_number, str)
        assert isinstance(version.created_at, datetime)
        assert isinstance(version.created_by, str)
        assert isinstance(version.description, str)
        assert version.parent_version is None or isinstance(version.parent_version, str)
        assert isinstance(version.checksum, str)
        assert isinstance(version.size_bytes, int)


class TestExperimentMetadata:
    """Comprehensive tests for ExperimentMetadata dataclass."""

    def test_default_creation(self):
        """Test ExperimentMetadata creation with defaults."""
        metadata = ExperimentMetadata()

        assert metadata.experiment_id is not None
        assert isinstance(metadata.experiment_id, str)
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

    def test_custom_creation(self):
        """Test ExperimentMetadata with custom values."""
        version = DataVersion(version_number="1.2.3")

        metadata = ExperimentMetadata(
            experiment_id="exp-001",
            experiment_name="Consciousness Detection Study",
            description="Testing P3b and gamma coherence markers",
            researcher="Dr. Jane Smith",
            institution="Neuroscience Institute",
            n_participants=50,
            n_trials=200,
            conditions=["conscious", "unconscious"],
            parameters={"stimulus_duration": 0.5, "isi": 1.0},
            data_format="csv",
            file_paths=["/data/exp001/subject1.csv", "/data/exp001/subject2.csv"],
            total_size_mb=500.5,
            current_version="1.2.3",
            version_history=[version],
            tags=["consciousness", "eeg", "p3b"],
            category="neural_signatures",
            data_quality_score=0.95,
            completeness_percentage=98.5,
            validation_status="validated",
        )

        assert metadata.experiment_id == "exp-001"
        assert metadata.experiment_name == "Consciousness Detection Study"
        assert metadata.description == "Testing P3b and gamma coherence markers"
        assert metadata.researcher == "Dr. Jane Smith"
        assert metadata.institution == "Neuroscience Institute"
        assert metadata.n_participants == 50
        assert metadata.n_trials == 200
        assert metadata.conditions == ["conscious", "unconscious"]
        assert metadata.parameters == {"stimulus_duration": 0.5, "isi": 1.0}
        assert metadata.data_format == "csv"
        assert metadata.file_paths == [
            "/data/exp001/subject1.csv",
            "/data/exp001/subject2.csv",
        ]
        assert metadata.total_size_mb == 500.5
        assert metadata.current_version == "1.2.3"
        assert len(metadata.version_history) == 1
        assert metadata.tags == ["consciousness", "eeg", "p3b"]
        assert metadata.category == "neural_signatures"
        assert metadata.data_quality_score == 0.95
        assert metadata.completeness_percentage == 98.5
        assert metadata.validation_status == "validated"

    def test_timestamps_distinct(self):
        """Test created_at and updated_at are properly set."""
        metadata = ExperimentMetadata()

        # They should be very close but may not be exactly equal due to timing
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        time_diff = abs((metadata.updated_at - metadata.created_at).total_seconds())
        assert time_diff < 1  # Should be within 1 second

    def test_validation_status_values(self):
        """Test validation status accepts valid values."""
        for status in ["pending", "validated", "failed"]:
            metadata = ExperimentMetadata(validation_status=status)
            assert metadata.validation_status == status

    def test_data_format_values(self):
        """Test data format accepts valid values."""
        for format_type in ["hdf5", "sqlite", "csv"]:
            metadata = ExperimentMetadata(data_format=format_type)
            assert metadata.data_format == format_type


class TestBackupInfo:
    """Comprehensive tests for BackupInfo dataclass."""

    def test_default_creation(self):
        """Test BackupInfo creation with defaults."""
        backup = BackupInfo()

        assert backup.backup_id is not None
        assert isinstance(backup.backup_id, str)
        assert backup.backup_path == ""
        assert isinstance(backup.created_at, datetime)
        assert backup.backup_type == "full"
        assert backup.size_bytes == 0
        assert backup.checksum == ""
        assert backup.compression_ratio == 1.0
        assert backup.retention_days == 30
        assert backup.status == "active"

    def test_custom_creation(self):
        """Test BackupInfo with custom values."""
        backup_time = datetime(2024, 3, 15, 14, 30, 0)

        backup = BackupInfo(
            backup_id="backup-001",
            backup_path="/backups/experiment_2024_03_15.bak",
            created_at=backup_time,
            backup_type="incremental",
            size_bytes=1024 * 1024 * 50,  # 50MB
            checksum="md5:abc123xyz789",
            compression_ratio=0.7,
            retention_days=90,
            status="archived",
        )

        assert backup.backup_id == "backup-001"
        assert backup.backup_path == "/backups/experiment_2024_03_15.bak"
        assert backup.created_at == backup_time
        assert backup.backup_type == "incremental"
        assert backup.size_bytes == 52428800
        assert backup.checksum == "md5:abc123xyz789"
        assert backup.compression_ratio == 0.7
        assert backup.retention_days == 90
        assert backup.status == "archived"

    def test_backup_type_values(self):
        """Test backup type accepts valid values."""
        for btype in ["full", "incremental", "differential"]:
            backup = BackupInfo(backup_type=btype)
            assert backup.backup_type == btype

    def test_status_values(self):
        """Test status accepts valid values."""
        for status in ["active", "archived", "deleted"]:
            backup = BackupInfo(status=status)
            assert backup.status == status

    def test_compression_ratio_range(self):
        """Test compression ratio can be any float value."""
        for ratio in [0.1, 0.5, 1.0, 1.5, 2.0]:
            backup = BackupInfo(compression_ratio=ratio)
            assert backup.compression_ratio == ratio


class TestExperimentalDataset:
    """Comprehensive tests for ExperimentalDataset dataclass."""

    def test_default_creation(self):
        """Test ExperimentalDataset creation with defaults."""
        metadata = ExperimentMetadata(experiment_name="Test Experiment")
        dataset = ExperimentalDataset(metadata=metadata)

        assert dataset.metadata is metadata
        assert dataset.data == {}
        assert dataset.raw_data is None
        assert dataset.processed_data is None
        assert dataset.analysis_results is None
        assert dataset.storage_path is None
        assert dataset.backup_info == []
        assert dataset.access_permissions == {}
        assert not dataset.is_locked
        assert dataset.lock_reason == ""

    def test_full_creation(self):
        """Test ExperimentalDataset with all fields populated."""
        metadata = ExperimentMetadata(
            experiment_name="Full Test",
            n_participants=25,
        )
        backup = BackupInfo(backup_type="full")

        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"trials": [1, 2, 3], "subjects": ["A", "B", "C"]},
            raw_data={"eeg": [[1, 2, 3], [4, 5, 6]]},
            processed_data={"features": [0.5, 0.6, 0.7]},
            analysis_results={"p_value": 0.03, "significant": True},
            storage_path=Path("/data/experiments/exp001"),
            backup_info=[backup],
            access_permissions={"read": ["user1", "user2"], "write": ["admin"]},
            is_locked=True,
            lock_reason="Data integrity verification in progress",
        )

        assert dataset.metadata.experiment_name == "Full Test"
        assert dataset.data == {"trials": [1, 2, 3], "subjects": ["A", "B", "C"]}
        assert dataset.raw_data == {"eeg": [[1, 2, 3], [4, 5, 6]]}
        assert dataset.processed_data == {"features": [0.5, 0.6, 0.7]}
        assert dataset.analysis_results == {"p_value": 0.03, "significant": True}
        assert dataset.storage_path == Path("/data/experiments/exp001")
        assert len(dataset.backup_info) == 1
        assert dataset.backup_info[0].backup_type == "full"
        assert dataset.access_permissions == {
            "read": ["user1", "user2"],
            "write": ["admin"],
        }
        assert dataset.is_locked is True
        assert dataset.lock_reason == "Data integrity verification in progress"

    def test_post_init_metadata_validation(self):
        """Test __post_init__ validates and sets metadata fields."""
        # Should work with proper metadata
        metadata = ExperimentMetadata(experiment_name="Valid")
        dataset = ExperimentalDataset(metadata=metadata)
        assert dataset.metadata is metadata
        # Verify metadata gets experiment_id if not set
        assert dataset.metadata.experiment_id is not None

    def test_storage_path_types(self):
        """Test storage_path can be string or Path object."""
        metadata = ExperimentMetadata()

        # Test with string path
        dataset1 = ExperimentalDataset(metadata=metadata, storage_path="/tmp/test")
        assert dataset1.storage_path == "/tmp/test"

        dataset2 = ExperimentalDataset(metadata=metadata, storage_path=Path("/tmp/test2"))
        assert isinstance(dataset2.storage_path, Path)
        assert str(dataset2.storage_path) == "/tmp/test2"

    def test_post_init_none_storage_path(self):
        """Test __post_init__ handles None storage_path."""
        metadata = ExperimentMetadata()
        dataset = ExperimentalDataset(metadata=metadata, storage_path=None)
        assert dataset.storage_path is None

    def test_lock_unlock_cycle(self):
        """Test dataset locking and unlocking."""
        metadata = ExperimentMetadata()
        dataset = ExperimentalDataset(metadata=metadata)

        # Initially unlocked
        assert not dataset.is_locked
        assert dataset.lock_reason == ""

        # Lock the dataset
        dataset.is_locked = True
        dataset.lock_reason = "Processing data"

        assert dataset.is_locked
        assert dataset.lock_reason == "Processing data"

        # Unlock the dataset
        dataset.is_locked = False
        dataset.lock_reason = ""

        assert not dataset.is_locked
        assert dataset.lock_reason == ""


class TestDataModelIntegration:
    """Integration tests for data models working together."""

    def test_full_experiment_workflow(self):
        """Test complete experiment data workflow."""
        # Create initial version
        version1 = DataVersion(version_number="1.0.0", description="Initial data collection")

        # Create experiment metadata
        metadata = ExperimentMetadata(
            experiment_name="Consciousness Study",
            description="Testing neural correlates of consciousness",
            researcher="Dr. Researcher",
            n_participants=30,
            n_trials=300,
            current_version="1.0.0",
            version_history=[version1],
        )

        # Create dataset
        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"subjects": list(range(30))},
            storage_path="/data/consciousness_study",
        )

        # Create backup
        backup = BackupInfo(backup_type="full", size_bytes=1024 * 1024 * 200)
        dataset.backup_info.append(backup)

        # Verify complete workflow
        assert dataset.metadata.experiment_name == "Consciousness Study"
        assert len(dataset.metadata.version_history) == 1
        assert dataset.metadata.version_history[0].version_number == "1.0.0"
        assert len(dataset.backup_info) == 1
        assert dataset.backup_info[0].backup_type == "full"

    def test_version_history_management(self):
        """Test managing version history in metadata."""
        versions = [
            DataVersion(version_number="1.0.0", description="Initial"),
            DataVersion(version_number="1.1.0", description="Added participants"),
            DataVersion(version_number="2.0.0", description="Major revision"),
        ]

        metadata = ExperimentMetadata(experiment_name="Versioned Study", version_history=versions)

        assert len(metadata.version_history) == 3
        assert metadata.version_history[0].version_number == "1.0.0"
        assert metadata.version_history[1].version_number == "1.1.0"
        assert metadata.version_history[2].version_number == "2.0.0"

    def test_backup_lifecycle(self):
        """Test backup lifecycle within dataset."""
        metadata = ExperimentMetadata(experiment_name="Backup Test")
        dataset = ExperimentalDataset(metadata=metadata)

        # Add initial backup
        backup1 = BackupInfo(backup_type="full", status="active")
        dataset.backup_info.append(backup1)

        # Add incremental backup
        backup2 = BackupInfo(backup_type="incremental", status="active")
        dataset.backup_info.append(backup2)

        # Archive first backup
        dataset.backup_info[0].status = "archived"

        assert len(dataset.backup_info) == 2
        assert dataset.backup_info[0].status == "archived"
        assert dataset.backup_info[0].backup_type == "full"
        assert dataset.backup_info[1].status == "active"
        assert dataset.backup_info[1].backup_type == "incremental"


class TestDataModelEdgeCases:
    """Edge case tests for data models."""

    def test_empty_experiment_metadata(self):
        """Test ExperimentMetadata with minimal data."""
        metadata = ExperimentMetadata()

        assert metadata.n_participants == 0
        assert metadata.n_trials == 0
        assert metadata.conditions == []
        assert metadata.tags == []

    def test_dataversion_with_large_size(self):
        """Test DataVersion with very large size."""
        large_size = 1024 * 1024 * 1024 * 100  # 100GB
        version = DataVersion(size_bytes=large_size)

        assert version.size_bytes == large_size

    def test_backup_with_zero_retention(self):
        """Test BackupInfo with zero retention days."""
        backup = BackupInfo(retention_days=0)

        assert backup.retention_days == 0

    def test_dataset_with_empty_permissions(self):
        """Test ExperimentalDataset with empty permissions dict."""
        metadata = ExperimentMetadata()
        dataset = ExperimentalDataset(metadata=metadata, access_permissions={})

        assert dataset.access_permissions == {}

    def test_nested_data_structures(self):
        """Test handling nested data structures."""
        metadata = ExperimentMetadata(
            parameters={
                "nested": {
                    "level1": {"level2": [1, 2, 3]},
                    "array": [{"a": 1}, {"b": 2}],
                }
            }
        )

        dataset = ExperimentalDataset(
            metadata=metadata,
            data={"complex": {"nested": {"data": [1, 2, 3]}}},
        )

        assert "nested" in dataset.metadata.parameters
        assert "complex" in dataset.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
