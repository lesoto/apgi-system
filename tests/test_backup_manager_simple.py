#!/usr/bin/env python3
"""
Simple tests for backup manager utility.

Tests cover the actual functionality available in the module.
"""

import tempfile
from pathlib import Path

import pytest

# Import the modules we're testing
try:
    from utils.backup_manager import (
        BackupManager,
        BackupMetadata,
        cleanup_backups_cli,
        create_backup_cli,
        delete_backup_cli,
        list_backups_cli,
        restore_backup_cli,
    )

    BACKUP_MANAGER_AVAILABLE = True
except ImportError:
    BACKUP_MANAGER_AVAILABLE = False


class TestBackupManager:
    """Test BackupManager class."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_manager_initialization(self):
        """Test BackupManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            assert manager.backup_dir == backup_dir
            assert backup_dir.exists()
            assert hasattr(manager, "backup_components")
            assert hasattr(manager, "project_root")
            assert hasattr(manager, "_lock")

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_manager_default_dir(self):
        """Test BackupManager with default directory."""
        manager = BackupManager()

        assert manager.backup_dir.name == "backups"
        assert manager.backup_dir.exists()

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_basic(self):
        """Test basic backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()

            # Create config file
            config_dir = test_dir / "config"
            config_dir.mkdir()
            (config_dir / "test_config.json").write_text('{"setting": "value"}')

            # Create some data files
            data_dir = test_dir / "data"
            data_dir.mkdir()
            (data_dir / "test_data.txt").write_text("test data")

            # Create backup manager
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Mock project root to point to our test directory
            manager.project_root = test_dir

            # Create backup
            backup_id = manager.create_backup(
                components=["config", "data"], description="Test backup"
            )

            assert isinstance(backup_id, str)
            assert backup_id.startswith("backup_")

            # Check backup file was created (excluding metadata)
            backup_files = list(backup_dir.glob(f"{backup_id}.zip"))
            assert len(backup_files) == 1

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_all_components(self):
        """Test backup creation with all components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal project structure
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()

            # Create some directories that match backup components
            (test_dir / "config").mkdir()
            (test_dir / "data").mkdir()
            (test_dir / "logs").mkdir()

            # Create backup manager
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)
            manager.project_root = test_dir

            # Create backup with all components (default)
            backup_id = manager.create_backup(description="Full backup")

            assert isinstance(backup_id, str)
            backup_files = list(backup_dir.glob(f"{backup_id}.zip"))
            assert len(backup_files) == 1

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_list_backups(self):
        """Test listing backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Initially no backups
            backups = manager.list_backups()
            assert isinstance(backups, list)
            assert len(backups) == 0

            # Create a backup
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            (test_dir / "config" / "test_config.json").write_text('{"setting": "value"}')
            manager.project_root = test_dir

            backup_id = manager.create_backup(components=["config"], description="Test backup")

            # List backups
            backups = manager.list_backups()
            assert len(backups) == 1
            assert backups[0]["backup_id"] == backup_id
            assert backups[0]["description"] == "Test backup"

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_delete_backup(self):
        """Test backup deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Create a backup first
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            (test_dir / "config" / "test_config.json").write_text('{"setting": "value"}')
            manager.project_root = test_dir

            backup_id = manager.create_backup(components=["config"])

            # Verify backup exists
            backup_files = list(backup_dir.glob(f"{backup_id}.zip"))
            assert len(backup_files) == 1

            # Delete backup
            result = manager.delete_backup(backup_id)
            assert result is True

            # Verify backup is gone
            backup_files = list(backup_dir.glob(f"{backup_id}*"))
            assert len(backup_files) == 0

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_delete_nonexistent_backup(self):
        """Test deleting non-existent backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Try to delete non-existent backup
            result = manager.delete_backup("nonexistent_backup")
            assert result is False

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_cleanup_old_backups(self):
        """Test cleanup of old backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Create multiple backups
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            (test_dir / "config" / "test_config.json").write_text('{"setting": "value"}')
            manager.project_root = test_dir

            backup_ids = []
            for i in range(5):
                backup_id = manager.create_backup(components=["config"], description=f"Backup {i}")
                backup_ids.append(backup_id)

            # Should have 5 backups
            backups = manager.list_backups()
            assert len(backups) == 5

            # Cleanup keeping only 2 most recent
            deleted_count = manager.cleanup_old_backups(keep_count=2)
            assert deleted_count == 3

            # Should have only 2 backups left
            backups = manager.list_backups()
            assert len(backups) == 2

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_verify_backup(self):
        """Test backup verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Create a backup
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            (test_dir / "config" / "test.json").write_text('{"test": "data"}')
            manager.project_root = test_dir

            backup_id = manager.create_backup(components=["config"])

            # Verify backup
            result = manager.verify_backup(backup_id)
            assert result is True

            # Corrupt the backup file and verify again
            backup_files = list(backup_dir.glob(f"{backup_id}*"))
            if backup_files:
                backup_file = backup_files[0]
                # Corrupt the file by truncating it
                with open(backup_file, "w") as f:
                    f.write("corrupted")

                # Verification should fail
                result = manager.verify_backup(backup_id)
                assert result is False

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_verify_nonexistent_backup(self):
        """Test verification of non-existent backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Try to verify non-existent backup
            result = manager.verify_backup("nonexistent_backup")
            assert result is False


class TestBackupMetadata:
    """Test BackupMetadata dataclass."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_metadata_creation(self):
        """Test metadata creation."""
        metadata = BackupMetadata(
            backup_id="test_backup_001",
            timestamp="2023-12-01T10:00:00",
            description="Test backup",
            version="1.0.0",
            components=["config", "data"],
            file_count=10,
            total_size_mb=25.5,
            checksum="abc123def456",
            compressed=True,
        )

        assert metadata.backup_id == "test_backup_001"
        assert metadata.timestamp == "2023-12-01T10:00:00"
        assert metadata.description == "Test backup"
        assert metadata.version == "1.0.0"
        assert metadata.components == ["config", "data"]
        assert metadata.file_count == 10
        assert metadata.total_size_mb == 25.5
        assert metadata.checksum == "abc123def456"
        assert metadata.compressed is True

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_metadata_defaults(self):
        """Test metadata default values."""
        metadata = BackupMetadata(
            backup_id="test",
            timestamp="2023-12-01T10:00:00",
            description="Test",
            version="1.0",
            components=["config"],
            file_count=5,
            total_size_mb=10.0,
            checksum="hash123",
        )

        # compressed should default to True
        assert metadata.compressed is True


class TestCLICommands:
    """Test CLI command functions."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_cli(self):
        """Test CLI backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            (test_dir / "config" / "test_config.json").write_text('{"setting": "value"}')

            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Mock the global backup manager
            import utils.backup_manager

            original_manager = getattr(utils.backup_manager, "backup_manager", None)
            utils.backup_manager.backup_manager = BackupManager(backup_dir)
            utils.backup_manager.backup_manager.project_root = test_dir

            try:
                # Test CLI command
                result = create_backup_cli("config", "Test CLI backup")
                assert isinstance(result, str)
                assert result.startswith("backup_")
            finally:
                # Restore original manager
                if original_manager is not None:
                    utils.backup_manager.backup_manager = original_manager

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_list_backups_cli(self):
        """Test CLI list backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Mock the global backup manager
            import utils.backup_manager

            original_manager = getattr(utils.backup_manager, "backup_manager", None)
            utils.backup_manager.backup_manager = BackupManager(backup_dir)

            try:
                # Test CLI command
                result = list_backups_cli()
                assert isinstance(result, list)
                assert len(result) == 0  # No backups initially
            finally:
                # Restore original manager
                if original_manager is not None:
                    utils.backup_manager.backup_manager = original_manager

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_restore_backup_cli(self):
        """Test CLI restore backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Mock the global backup manager
            import utils.backup_manager

            original_manager = getattr(utils.backup_manager, "backup_manager", None)
            utils.backup_manager.backup_manager = BackupManager(backup_dir)

            try:
                # Test CLI command with non-existent backup
                result = restore_backup_cli("nonexistent_backup")
                assert result is False
            finally:
                # Restore original manager
                if original_manager is not None:
                    utils.backup_manager.backup_manager = original_manager

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_delete_backup_cli(self):
        """Test CLI delete backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Mock the global backup manager
            import utils.backup_manager

            original_manager = getattr(utils.backup_manager, "backup_manager", None)
            utils.backup_manager.backup_manager = BackupManager(backup_dir)
            utils.backup_manager.backup_manager.project_root = Path(temp_dir) / "test_project"

            try:
                # Test CLI command with non-existent backup
                result = delete_backup_cli("nonexistent_backup")
                assert result is False
            finally:
                # Restore original manager
                if original_manager is not None:
                    utils.backup_manager.backup_manager = original_manager

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_cleanup_backups_cli(self):
        """Test CLI cleanup backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Mock the global backup manager
            import utils.backup_manager

            original_manager = getattr(utils.backup_manager, "backup_manager", None)
            utils.backup_manager.backup_manager = BackupManager(backup_dir)

            try:
                # Test CLI command
                result = cleanup_backups_cli(5)
                assert isinstance(result, int)
                assert result == 0  # No backups to clean up
            finally:
                # Restore original manager
                if original_manager is not None:
                    utils.backup_manager.backup_manager = original_manager


class TestBackupManagerErrorHandling:
    """Test error handling in BackupManager."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_with_invalid_components(self):
        """Test backup creation with invalid components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            # Try to create backup with non-existent components
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            manager.project_root = test_dir

            # Should handle gracefully
            backup_id = manager.create_backup(components=["nonexistent"], description="Test")
            assert isinstance(backup_id, str)

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_with_permission_error(self):
        """Test backup creation with permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()

            # Create backup manager
            manager = BackupManager(backup_dir)

            # Create test project
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            (test_dir / "config").mkdir()
            manager.project_root = test_dir

            # Make backup directory read-only to simulate permission error
            backup_dir.chmod(0o444)

            try:
                # Should handle permission error gracefully
                backup_id = manager.create_backup(components=["config"])
                # May or may not succeed depending on system
                assert isinstance(backup_id, str)
            finally:
                # Restore permissions
                backup_dir.chmod(0o755)


# Mock tests for when backup manager is not available
class TestBackupManagerMock:
    """Mock tests when backup manager is not available."""

    @pytest.mark.skipif(BACKUP_MANAGER_AVAILABLE, reason="Backup manager is available")
    def test_module_unavailable(self):
        """Test behavior when backup manager is not available."""
        with pytest.raises(ImportError):
            pass


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
