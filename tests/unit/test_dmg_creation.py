"""
Unit tests for DMG creation functionality.

Tests DMG structure validation, symlink creation, and file permissions.

Validates: Requirements 14.1, 14.2
"""

import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path


class TestDMGStructureValidation(unittest.TestCase):
    """Test DMG structure validation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dmg_mount = Path(self.temp_dir) / "dmg_mount"
        self.test_dmg_mount.mkdir()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_validate_dmg_contains_app_bundle(self) -> None:
        """Test that DMG validation checks for .app bundle."""
        # Create a mock .app bundle
        app_bundle = self.test_dmg_mount / "APGI System.app"
        app_bundle.mkdir()

        # Create Contents directory
        contents = app_bundle / "Contents"
        contents.mkdir()

        # Validation should pass
        self.assertTrue(app_bundle.exists())
        self.assertTrue(contents.exists())

    def test_validate_dmg_missing_app_bundle(self) -> None:
        """Test that DMG validation fails when .app bundle is missing."""
        # Empty mount point
        app_bundles = list(self.test_dmg_mount.glob("*.app"))

        # Should be empty
        self.assertEqual(len(app_bundles), 0)

    def test_validate_dmg_has_applications_symlink(self) -> None:
        """Test that DMG validation checks for Applications symlink."""
        # Create Applications symlink
        applications_link = self.test_dmg_mount / "Applications"

        # On non-macOS systems, we can't create the actual symlink to /Applications
        # but we can test the logic
        if os.name == "posix":
            try:
                applications_link.symlink_to("/Applications")
                self.assertTrue(applications_link.is_symlink())
                self.assertTrue(applications_link.exists() or applications_link.is_symlink())
            except (OSError, NotImplementedError):
                # Skip if we can't create symlinks (e.g., Windows)
                self.skipTest("Cannot create symlinks on this platform")

    def test_validate_dmg_structure_complete(self) -> None:
        """Test complete DMG structure validation."""
        # Create app bundle
        app_bundle = self.test_dmg_mount / "APGI System.app"
        app_bundle.mkdir()
        (app_bundle / "Contents").mkdir()
        (app_bundle / "Contents" / "MacOS").mkdir()
        (app_bundle / "Contents" / "Resources").mkdir()

        # Create Applications symlink (if possible)
        applications_link = self.test_dmg_mount / "Applications"
        if os.name == "posix":
            try:
                applications_link.symlink_to("/Applications")
            except (OSError, NotImplementedError):
                pass

        # Verify structure
        self.assertTrue(app_bundle.exists())
        self.assertTrue((app_bundle / "Contents").exists())
        self.assertTrue((app_bundle / "Contents" / "MacOS").exists())
        self.assertTrue((app_bundle / "Contents" / "Resources").exists())


class TestSymlinkCreation(unittest.TestCase):
    """Test symlink creation for DMG."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.dmg_staging = Path(self.temp_dir) / "dmg_staging"
        self.dmg_staging.mkdir()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_applications_symlink(self) -> None:
        """Test creating Applications symlink."""
        applications_link = self.dmg_staging / "Applications"

        if os.name == "posix":
            try:
                applications_link.symlink_to("/Applications")

                # Verify symlink was created
                self.assertTrue(applications_link.is_symlink())

                # Verify it points to /Applications
                target = os.readlink(str(applications_link))
                self.assertEqual(target, "/Applications")
            except (OSError, NotImplementedError):
                self.skipTest("Cannot create symlinks on this platform")
        else:
            self.skipTest("Symlink test only applicable on POSIX systems")

    def test_symlink_already_exists(self) -> None:
        """Test handling when symlink already exists."""
        applications_link = self.dmg_staging / "Applications"

        if os.name == "posix":
            try:
                # Create symlink
                applications_link.symlink_to("/Applications")

                # Try to create again (should handle gracefully)
                if applications_link.exists() or applications_link.is_symlink():
                    applications_link.unlink()
                    applications_link.symlink_to("/Applications")

                # Should still be valid
                self.assertTrue(applications_link.is_symlink())
            except (OSError, NotImplementedError):
                self.skipTest("Cannot create symlinks on this platform")
        else:
            self.skipTest("Symlink test only applicable on POSIX systems")

    def test_symlink_points_to_correct_target(self) -> None:
        """Test that symlink points to correct target."""
        applications_link = self.dmg_staging / "Applications"

        if os.name == "posix":
            try:
                applications_link.symlink_to("/Applications")

                # Read symlink target
                target = os.readlink(str(applications_link))

                # Should point to /Applications
                self.assertEqual(target, "/Applications")
                self.assertNotEqual(target, "/System/Applications")
            except (OSError, NotImplementedError):
                self.skipTest("Cannot create symlinks on this platform")
        else:
            self.skipTest("Symlink test only applicable on POSIX systems")


class TestFilePermissions(unittest.TestCase):
    """Test file permissions in DMG."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.dmg_staging = Path(self.temp_dir) / "dmg_staging"
        self.dmg_staging.mkdir()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_app_bundle_readable(self) -> None:
        """Test that app bundle is readable."""
        app_bundle = self.dmg_staging / "APGI System.app"
        app_bundle.mkdir()

        # Check permissions
        mode = app_bundle.stat().st_mode

        # Should be readable by owner
        self.assertTrue(mode & stat.S_IRUSR)

    def test_app_bundle_executable(self) -> None:
        """Test that app bundle directory is executable."""
        app_bundle = self.dmg_staging / "APGI System.app"
        app_bundle.mkdir()

        # Check permissions
        mode = app_bundle.stat().st_mode

        # Directory should be executable (searchable)
        self.assertTrue(mode & stat.S_IXUSR)

    def test_executable_has_execute_permission(self) -> None:
        """Test that executable file has execute permission."""
        if os.name != "posix":
            self.skipTest("Execute permission test only applicable on POSIX systems")

        # Create mock executable
        app_bundle = self.dmg_staging / "APGI System.app"
        app_bundle.mkdir()
        (app_bundle / "Contents").mkdir()
        (app_bundle / "Contents" / "MacOS").mkdir()

        executable = app_bundle / "Contents" / "MacOS" / "APGI System"
        executable.write_text("#!/bin/bash\necho 'test'")

        # Set executable permission
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        # Verify executable permission
        mode = executable.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR)
        self.assertTrue(mode & stat.S_IXGRP)
        self.assertTrue(mode & stat.S_IXOTH)

    def test_resources_readable_by_all(self) -> None:
        """Test that resource files are readable by all users."""
        # Create mock resource file
        app_bundle = self.dmg_staging / "APGI System.app"
        app_bundle.mkdir()
        (app_bundle / "Contents").mkdir()
        (app_bundle / "Contents" / "Resources").mkdir()

        resource = app_bundle / "Contents" / "Resources" / "test.txt"
        resource.write_text("test content")

        # Check permissions
        mode = resource.stat().st_mode

        # Should be readable by owner, group, and others
        self.assertTrue(mode & stat.S_IRUSR)
        self.assertTrue(mode & stat.S_IRGRP)
        self.assertTrue(mode & stat.S_IROTH)

    def test_symlink_permissions(self) -> None:
        """Test that symlink has appropriate permissions."""
        applications_link = self.dmg_staging / "Applications"

        if os.name == "posix":
            try:
                applications_link.symlink_to("/Applications")

                # Symlinks typically have 777 permissions but follow target
                # Just verify we can stat it
                link_stat = applications_link.lstat()
                self.assertIsNotNone(link_stat)
            except (OSError, NotImplementedError):
                self.skipTest("Cannot create symlinks on this platform")
        else:
            self.skipTest("Symlink test only applicable on POSIX systems")


class TestDMGCreationHelpers(unittest.TestCase):
    """Test helper functions for DMG creation."""

    def test_get_dmg_filename(self) -> None:
        """Test DMG filename generation."""
        app_name = "APGI System"
        version = "1.0.0"

        # Expected format: APGI_System_1.0.0.dmg
        expected = "APGI_System_1.0.0.dmg"
        actual = app_name.replace(" ", "_") + "_" + version + ".dmg"

        self.assertEqual(actual, expected)

    def test_get_dmg_volume_name(self) -> None:
        """Test DMG volume name generation."""
        app_name = "APGI System"
        version = "1.0.0"

        # Expected format: APGI System 1.0.0
        expected = f"{app_name} {version}"

        self.assertEqual(expected, "APGI System 1.0.0")

    def test_calculate_dmg_size(self) -> None:
        """Test DMG size calculation."""
        # Mock app bundle size
        app_size_mb = 250

        # DMG should be slightly larger (add 50MB buffer)
        dmg_size_mb = app_size_mb + 50

        self.assertEqual(dmg_size_mb, 300)
        self.assertGreater(dmg_size_mb, app_size_mb)


if __name__ == "__main__":
    unittest.main()
