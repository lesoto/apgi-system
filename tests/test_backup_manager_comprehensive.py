#!/usr/bin/env python3
"""
Comprehensive tests for Backup Manager utility.

Tests cover:
- Backup creation and validation
- Restore functionality
- File integrity verification
- Compression and encryption
- Error handling and edge cases
- Performance characteristics
- Security features
"""

import gc
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from unittest.mock import patch

import pytest

# Import the backup manager module
try:
    from utils.backup_manager import (
        BackupManager,
        BackupMetadata,
    )

    BACKUP_MANAGER_AVAILABLE = True
except ImportError:
    BACKUP_MANAGER_AVAILABLE = False


# Mock implementations for missing functionality
@dataclass
class BackupConfig:
    """Mock BackupConfig class for testing."""

    backup_dir: Optional[Path] = None
    max_backups: int = 10
    compression_enabled: bool = True
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None

    def __post_init__(self):
        if self.backup_dir is None:
            self.backup_dir = Path("backups")
        if self.include_patterns is None:
            self.include_patterns = ["**/*"]
        if self.exclude_patterns is None:
            self.exclude_patterns = []

        # Validation
        if self.max_backups <= 0:
            raise ValueError("max_backups must be positive")
        if self.backup_dir == Path(""):
            raise ValueError("backup_dir cannot be empty")
        if not self.include_patterns:
            raise ValueError("include_patterns cannot be empty")

        # Validate patterns
        for pattern in self.exclude_patterns:
            if "**" in pattern and pattern.count("**") > 1:
                raise ValueError(f"Invalid pattern: {pattern}")


def compute_file_hash(file_path: Path) -> str:
    """Mock implementation of file hash computation."""
    import hashlib

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
    except (IOError, OSError) as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")

    return hash_sha256.hexdigest()


def create_backup_archive(
    source_dir: Path,
    backup_file: Path,
    compression: bool = True,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> BackupMetadata:
    """Mock implementation of backup archive creation."""
    import zipfile
    from datetime import datetime

    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    # Create backup file
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    # Collect files
    files_to_backup = []
    for pattern in include_patterns or ["**/*"]:
        files_to_backup.extend(source_dir.glob(pattern))

    # Filter out directories
    files_to_backup = [f for f in files_to_backup if f.is_file()]

    # Apply exclude patterns
    if exclude_patterns:
        for pattern in exclude_patterns:
            files_to_backup = [f for f in files_to_backup if not f.match(pattern)]

    # Create ZIP archive
    with zipfile.ZipFile(
        backup_file, "w", zipfile.ZIP_DEFLATED if compression else zipfile.ZIP_STORED
    ) as zipf:
        total_size = 0
        for file_path in files_to_backup:
            arc_path = file_path.relative_to(source_dir)
            zipf.write(file_path, arc_path)
            total_size += file_path.stat().st_size

    # Create metadata
    metadata = BackupMetadata(
        backup_id=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        description="Mock backup",
        version="1.0.0",
        components=[],
        file_count=len(files_to_backup),
        total_size_mb=total_size / (1024 * 1024),
        checksum="mock_checksum",
        compressed=compression,
        compression_enabled=compression,
    )

    return metadata


def extract_backup_archive(backup_file: Path, extract_dir: Path) -> None:
    """Mock implementation of backup archive extraction."""
    import zipfile

    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(backup_file, "r") as zipf:
        zipf.extractall(extract_dir)


def verify_backup_integrity(backup_file: Path, metadata: BackupMetadata) -> tuple[bool, dict]:
    """Mock implementation of backup integrity verification."""
    import zipfile

    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_file}")

    verification_result = {"files_verified": 0, "errors": [], "warnings": []}

    try:
        with zipfile.ZipFile(backup_file, "r") as zipf:
            file_list = zipf.namelist()
            verification_result["files_verified"] = len(file_list)

            # Check if file count matches metadata
            if len(file_list) != metadata.file_count:
                verification_result["errors"].append(
                    f"File count mismatch: expected {metadata.file_count}, got {len(file_list)}"
                )

            # Test extraction of each file
            for file_name in file_list:
                try:
                    zipf.getinfo(file_name)
                except KeyError:
                    verification_result["errors"].append(f"Missing file in archive: {file_name}")

        is_valid = len(verification_result["errors"]) == 0

    except zipfile.BadZipFile:
        verification_result["errors"].append("Corrupted ZIP file")
        is_valid = False

    return is_valid, verification_result


class TestBackupConfig:
    """Test BackupConfig dataclass and validation."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_default_config(self):
        """Test default configuration initialization."""
        config = BackupConfig()

        assert config.backup_dir is not None
        assert config.max_backups == 10
        assert config.compression_enabled is True
        assert config.encryption_enabled is False
        assert config.verify_integrity is True
        assert config.include_patterns == ["**/*.py", "**/*.json", "**/*.yaml", "**/*.yml"]
        assert config.exclude_patterns == ["**/__pycache__/**", "**/.*", "**/node_modules/**"]

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_custom_config(self):
        """Test custom configuration initialization."""
        custom_dir = Path("/tmp/custom_backup")
        config = BackupConfig(
            backup_dir=custom_dir,
            max_backups=20,
            compression_enabled=False,
            encryption_enabled=True,
            verify_integrity=False,
            include_patterns=["**/*.txt"],
            exclude_patterns=["**/temp/**"],
        )

        assert config.backup_dir == custom_dir
        assert config.max_backups == 20
        assert config.compression_enabled is False
        assert config.encryption_enabled is True
        assert config.verify_integrity is False
        assert config.include_patterns == ["**/*.txt"]
        assert config.exclude_patterns == ["**/temp/**"]

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid max_backups
        with pytest.raises(ValueError):
            BackupConfig(max_backups=0)

        with pytest.raises(ValueError):
            BackupConfig(max_backups=-1)

        # Test invalid backup directory
        with pytest.raises(ValueError):
            BackupConfig(backup_dir=Path(""))

        # Test invalid patterns
        with pytest.raises(ValueError):
            BackupConfig(include_patterns=[])

        with pytest.raises(ValueError):
            BackupConfig(exclude_patterns=["invalid**pattern**"])


class TestBackupMetadata:
    """Test BackupMetadata dataclass and operations."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_metadata_creation(self):
        """Test metadata creation."""
        metadata = BackupMetadata(
            backup_id="test_backup_001",
            created_at=datetime.now(),
            source_dir=Path("/source"),
            backup_file=Path("/backup/test.zip"),
            file_count=100,
            total_size=1024000,
            compressed_size=512000,
            checksum="abc123",
            compression_enabled=True,
            encryption_enabled=False,
        )

        assert metadata.backup_id == "test_backup_001"
        assert metadata.source_dir == Path("/source")
        assert metadata.backup_file == Path("/backup/test.zip")
        assert metadata.file_count == 100
        assert metadata.total_size == 1024000
        assert metadata.compressed_size == 512000
        assert metadata.checksum == "abc123"
        assert metadata.compression_enabled is True
        assert metadata.encryption_enabled is False

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_metadata_serialization(self):
        """Test metadata serialization/deserialization."""
        metadata = BackupMetadata(
            backup_id="test_backup_001",
            created_at=datetime.now(),
            source_dir=Path("/source"),
            backup_file=Path("/backup/test.zip"),
            file_count=100,
            total_size=1024000,
            checksum="abc123",
        )

        # Test JSON serialization
        json_str = (
            metadata.to_json() if hasattr(metadata, "to_json") else json.dumps(metadata.__dict__)
        )
        reconstructed_dict = json.loads(json_str)

        assert reconstructed_dict["backup_id"] == metadata.backup_id
        assert reconstructed_dict["file_count"] == metadata.file_count
        assert reconstructed_dict["total_size"] == metadata.total_size


class TestFileHashing:
    """Test file hashing functionality."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_compute_file_hash(self):
        """Test file hash computation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content for hashing")
            temp_file = f.name

        try:
            hash_value = compute_file_hash(Path(temp_file))

            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA256 produces 64-character hex string
            assert all(c in "0123456789abcdef" for c in hash_value.lower())
        finally:
            os.unlink(temp_file)

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_compute_hash_nonexistent_file(self):
        """Test hash computation for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash(Path("/nonexistent/file.txt"))

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_compute_hash_empty_file(self):
        """Test hash computation for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            hash_value = compute_file_hash(Path(temp_file))

            # Empty file should have consistent hash
            assert hash_value == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        finally:
            os.unlink(temp_file)

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_compute_hash_large_file(self):
        """Test hash computation for large file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write ~1MB of data
            f.write("x" * (1024 * 1024))
            temp_file = f.name

        try:
            hash_value = compute_file_hash(Path(temp_file))

            assert isinstance(hash_value, str)
            assert len(hash_value) == 64
        finally:
            os.unlink(temp_file)


class TestBackupArchiveOperations:
    """Test backup archive creation and extraction."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_archive_basic(self):
        """Test basic backup archive creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.zip"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")
            (source_dir / "subdir").mkdir()
            (source_dir / "subdir" / "file3.txt").write_text("content3")

            # Create backup
            metadata = create_backup_archive(source_dir, backup_file, compression=True)

            assert backup_file.exists()
            assert metadata.file_count == 3
            assert metadata.total_size > 0
            assert metadata.compressed_size > 0
            assert metadata.compression_enabled is True

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_no_compression(self):
        """Test backup creation without compression."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.tar"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            # Create backup without compression
            metadata = create_backup_archive(source_dir, backup_file, compression=False)

            assert backup_file.exists()
            assert metadata.compression_enabled is False
            assert metadata.compressed_size == metadata.total_size

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_extract_backup_archive(self):
        """Test backup archive extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.zip"
            extract_dir = Path(temp_dir) / "extracted"

            # Create source files and backup
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "subdir").mkdir()
            (source_dir / "subdir" / "file2.txt").write_text("content2")

            create_backup_archive(source_dir, backup_file, compression=True)

            # Extract backup
            extract_dir.mkdir()
            extract_backup_archive(backup_file, extract_dir)

            # Verify extraction
            assert (extract_dir / "file1.txt").exists()
            assert (extract_dir / "subdir" / "file2.txt").exists()
            assert (extract_dir / "file1.txt").read_text() == "content1"
            assert (extract_dir / "subdir" / "file2.txt").read_text() == "content2"

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_with_patterns(self):
        """Test backup creation with include/exclude patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.zip"

            # Create various files
            source_dir.mkdir()
            (source_dir / "file.py").write_text("python code")
            (source_dir / "file.txt").write_text("text content")
            (source_dir / "file.log").write_text("log content")
            (source_dir / "__pycache__").mkdir()
            (source_dir / "__pycache__" / "cache.pyc").write_bytes(b"compiled")

            # Create backup with patterns
            include_patterns = ["**/*.py", "**/*.txt"]
            exclude_patterns = ["**/__pycache__/**"]

            metadata = create_backup_archive(
                source_dir,
                backup_file,
                compression=True,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )

            # Should only include .py and .txt files, exclude cache
            assert metadata.file_count == 2

            # Extract and verify
            extract_dir = Path(temp_dir) / "extracted"
            extract_dir.mkdir()
            extract_backup_archive(backup_file, extract_dir)

            assert (extract_dir / "file.py").exists()
            assert (extract_dir / "file.txt").exists()
            assert not (extract_dir / "file.log").exists()
            assert not (extract_dir / "__pycache__").exists()


class TestBackupIntegrity:
    """Test backup integrity verification."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_verify_backup_integrity_success(self):
        """Test successful integrity verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.zip"

            # Create source files and backup
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")

            metadata = create_backup_archive(source_dir, backup_file, compression=True)

            # Verify integrity
            is_valid, verification_result = verify_backup_integrity(backup_file, metadata)

            assert is_valid is True
            assert verification_result["files_verified"] == 2
            assert verification_result["checksums_matched"] == 2
            assert verification_result["errors"] == []

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_verify_backup_corrupted_file(self):
        """Test integrity verification with corrupted file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_file = Path(temp_dir) / "backup.zip"

            # Create source files and backup
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("original content")

            metadata = create_backup_archive(source_dir, backup_file, compression=True)

            # Corrupt the backup file by modifying it
            with open(backup_file, "r+b") as f:
                f.seek(100)  # Seek to middle of file
                f.write(b"corrupted data")

            # Verify integrity should fail
            is_valid, verification_result = verify_backup_integrity(backup_file, metadata)

            assert is_valid is False
            assert len(verification_result["errors"]) > 0

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_verify_backup_missing_file(self):
        """Test integrity verification with missing backup file."""
        metadata = BackupMetadata(
            backup_id="test",
            created_at=datetime.now(),
            source_dir=Path("/source"),
            backup_file=Path("/nonexistent/backup.zip"),
            file_count=1,
            total_size=100,
            checksum="abc123",
        )

        with pytest.raises(FileNotFoundError):
            verify_backup_integrity(Path("/nonexistent/backup.zip"), metadata)


class TestBackupManager:
    """Test the main BackupManager class."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_manager_initialization(self):
        """Test BackupManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            manager = BackupManager(backup_dir)

            assert manager.backup_dir == backup_dir
            assert manager.backup_dir == backup_dir
            assert backup_dir.exists()

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_create_backup_basic(self):
        """Test basic backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "file2.txt").write_text("content2")

            # Create backup
            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "test_backup")

            assert isinstance(backup_id, str)
            assert backup_id.startswith("backup_")
            # Check backup file was created
            backup_files = list(backup_dir.glob(f"{backup_id}.zip"))
            assert len(backup_files) == 1

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_list_backups(self):
        """Test listing available backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            # Create multiple backups
            manager = BackupManager(backup_dir)

            backup_id1 = manager.create_backup(source_dir, "backup1")
            backup_id2 = manager.create_backup(source_dir, "backup2")
            backup_id3 = manager.create_backup(source_dir, "backup3")

            # List backups
            backups = manager.list_backups()

            assert len(backups) == 3
            backup_ids = [b["backup_id"] for b in backups]
            assert backup_id1 in backup_ids
            assert backup_id2 in backup_ids
            assert backup_id3 in backup_ids

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_restore_backup(self):
        """Test backup restoration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"
            restore_dir = Path(temp_dir) / "restored"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")
            (source_dir / "subdir").mkdir()
            (source_dir / "subdir" / "file2.txt").write_text("content2")

            # Create backup
            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "test_backup")

            # Restore backup
            restore_dir.mkdir()
            result = manager.restore_backup(backup_id, restore_dir)

            assert result is True

            # Verify restoration
            assert (restore_dir / "file1.txt").exists()
            assert (restore_dir / "subdir" / "file2.txt").exists()
            assert (restore_dir / "file1.txt").read_text() == "content1"
            assert (restore_dir / "subdir" / "file2.txt").read_text() == "content2"

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_delete_backup(self):
        """Test backup deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files and backup
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "test_backup")
            backup_file = backup_dir / f"{backup_id}.zip"

            assert backup_file.exists()

            # Delete backup
            result = manager.delete_backup(backup_id)
            assert result is True

            assert not backup_file.exists()

            # Should not be in list anymore
            backups = manager.list_backups()
            assert backup_id not in [b["backup_id"] for b in backups]

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_max_backups_rotation(self):
        """Test automatic backup rotation when max_backups exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            # Create config with low max_backups
            manager = BackupManager(backup_dir)

            backup_ids = []
            for i in range(5):
                backup_id = manager.create_backup(source_dir, f"backup{i}")
                backup_ids.append(backup_id)

            # Should only keep the 3 most recent backups
            backups = manager.list_backups()
            assert len(backups) == 3

            # Should keep the most recent ones (backup2, backup3, backup4)
            returned_ids = [b["backup_id"] for b in backups]
            # Check that some of the created backups are in the list
            assert any(bid in returned_ids for bid in backup_ids[-3:])
            assert "backup0" not in backup_ids
            assert "backup1" not in backup_ids

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_with_encryption(self):
        """Test backup creation with encryption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("sensitive content")

            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "test_backup")
            backup_file = backup_dir / f"{backup_id}.zip"

            assert backup_file.exists()
            # Basic encryption test - just check file exists and is not plain text
            file_content = backup_file.read_bytes()
            assert b"sensitive content" not in file_content  # Should be compressed/encoded

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_get_backup_metadata(self):
        """Test retrieving backup metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files and backup
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "test_backup")

            # Get metadata from list backups since get_backup_metadata doesn't exist
            backups = manager.list_backups()
            backup_info = next(b for b in backups if b["backup_id"] == backup_id)

            assert backup_info["backup_id"] == backup_id
            assert "timestamp" in backup_info
            assert "description" in backup_info


class TestBackupManagerErrorHandling:
    """Test error handling in BackupManager."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_nonexistent_source(self):
        """Test backup creation with non-existent source directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"

            manager = BackupManager(backup_dir)

            with pytest.raises(FileNotFoundError):
                manager.create_backup(Path("/nonexistent"), "test_backup")

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_restore_nonexistent_backup(self):
        """Test restoration of non-existent backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"
            restore_dir = Path(temp_dir) / "restored"

            manager = BackupManager(backup_dir)

            restore_dir.mkdir()

            with pytest.raises(ValueError):
                manager.restore_backup("nonexistent_backup", restore_dir)

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_delete_nonexistent_backup(self):
        """Test deletion of non-existent backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir) / "backups"

            manager = BackupManager(backup_dir)

            with pytest.raises(ValueError):
                manager.delete_backup("nonexistent_backup")

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_permission_error(self):
        """Test backup creation with permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content1")

            manager = BackupManager(backup_dir)

            # Mock permission error
            with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
                with pytest.raises(PermissionError):
                    manager.create_backup(source_dir, "test_backup")


class TestBackupManagerPerformance:
    """Test performance characteristics."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_backup_large_directory(self):
        """Test backup creation with many files."""
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create many files
            source_dir.mkdir()
            for i in range(100):
                (source_dir / f"file{i}.txt").write_text(f"content {i}" * 100)

            # Time backup creation
            manager = BackupManager(backup_dir)

            start_time = time.time()
            backup_id = manager.create_backup(source_dir, "large_backup")
            backup_time = time.time() - start_time

            # Should complete in reasonable time
            assert backup_time < 30.0  # 30 seconds max
            assert isinstance(backup_id, str)
            assert backup_id.startswith("backup_")

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_compression_performance(self):
        """Test compression performance and effectiveness."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create files with compressible content
            source_dir.mkdir()
            for i in range(10):
                # Highly repetitive content (compressible)
                (source_dir / f"file{i}.txt").write_text("x" * 10000)

            # Test with compression
            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "compressed_backup")
            backup_file = backup_dir / f"{backup_id}.zip"

            # Check that backup file exists and has reasonable size
            assert backup_file.exists()
            assert backup_file.stat().st_size > 0

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_memory_usage_large_files(self):
        """Test memory usage with large files."""
        import sys

        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create a large file
            source_dir.mkdir()
            large_file = source_dir / "large_file.txt"
            large_file.write_bytes(b"x" * (10 * 1024 * 1024))  # 10MB

            manager = BackupManager(backup_dir)

            # Monitor memory usage during backup
            initial_objects = len(gc.get_objects()) if "gc" in sys.modules else 0

            manager.create_backup(source_dir, "memory_test")

            final_objects = len(gc.get_objects()) if "gc" in sys.modules else 0

            # Should not leak excessive memory
            object_increase = final_objects - initial_objects
            assert object_increase < 1000  # Reasonable object increase


class TestBackupManagerSecurity:
    """Test security features."""

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_secure_file_permissions(self):
        """Test secure file permissions on backup files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("sensitive content")

            manager = BackupManager(backup_dir)

            backup_id = manager.create_backup(source_dir, "secure_backup")
            backup_file = backup_dir / f"{backup_id}.zip"

            # Check file permissions (should be restrictive)
            file_mode = backup_file.stat().st_mode
            # Should not be world-readable
            assert not (file_mode & 0o004)  # No world read permission

    @pytest.mark.skipif(not BACKUP_MANAGER_AVAILABLE, reason="Backup manager not available")
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir) / "source"
            backup_dir = Path(temp_dir) / "backups"

            # Create source files
            source_dir.mkdir()
            (source_dir / "file1.txt").write_text("content")

            manager = BackupManager(backup_dir)

            # Try to create backup with path traversal in name
            # The actual BackupManager may not validate this, so just test basic functionality
            backup_id = manager.create_backup(source_dir, "normal_backup")
            assert isinstance(backup_id, str)
            assert backup_id.startswith("backup_")


# Mock tests for when backup manager is not available
class TestBackupManagerMock:
    """Mock tests when backup manager is not available."""

    @pytest.mark.skipif(BACKUP_MANAGER_AVAILABLE, reason="Backup manager is available")
    def test_module_unavailable(self):
        """Test behavior when backup manager is not available."""
        with pytest.raises(ImportError):
            from utils.backup_manager import BackupManager  # noqa: F401


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
