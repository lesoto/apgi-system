"""
Unit tests for Windows installer script generation utilities.

Tests version extraction, path configuration, and registry entry generation.
Requirements: 13.1, 13.2
"""

import pytest
import tempfile
from pathlib import Path
from utils.installer_utils import (
    extract_version_from_pyproject,
    normalize_path_for_inno,
    generate_registry_entries,
    generate_inno_setup_script,
)


class TestVersionExtraction:
    """Test version string extraction from pyproject.toml."""

    def test_extract_version_from_valid_pyproject(self, tmp_path):
        """Test extracting version from a valid pyproject.toml file."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-app"
version = "1.2.3"
description = "Test application"
""")

        version = extract_version_from_pyproject(pyproject)
        assert version == "1.2.3"

    def test_extract_version_with_single_quotes(self, tmp_path):
        """Test extracting version with single quotes."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-app"
version = '0.5.10'
""")

        version = extract_version_from_pyproject(pyproject)
        assert version == "0.5.10"

    def test_extract_version_with_extra_whitespace(self, tmp_path):
        """Test extracting version with extra whitespace."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-app"
version   =   "2.0.0"
""")

        version = extract_version_from_pyproject(pyproject)
        assert version == "2.0.0"

    def test_extract_version_file_not_found(self, tmp_path):
        """Test error when pyproject.toml doesn't exist."""
        nonexistent = tmp_path / "nonexistent.toml"

        with pytest.raises(ValueError, match="pyproject.toml not found"):
            extract_version_from_pyproject(nonexistent)

    def test_extract_version_missing_version_field(self, tmp_path):
        """Test error when version field is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test-app"
description = "No version here"
""")

        with pytest.raises(ValueError, match="Version not found"):
            extract_version_from_pyproject(pyproject)

    def test_extract_version_invalid_format(self, tmp_path):
        """Test error when version format is invalid."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
version = "invalid"
""")

        with pytest.raises(ValueError, match="Invalid version format"):
            extract_version_from_pyproject(pyproject)

    def test_extract_version_from_real_pyproject(self):
        """Test extracting version from the actual project pyproject.toml."""
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            version = extract_version_from_pyproject(pyproject)
            # Should match semver pattern
            assert len(version.split(".")) >= 3
            assert all(part.isdigit() for part in version.split(".")[:3])


class TestPathNormalization:
    """Test path normalization for Inno Setup."""

    def test_normalize_absolute_path(self, tmp_path):
        """Test normalizing an absolute path."""
        test_path = tmp_path / "test" / "file.exe"
        normalized = normalize_path_for_inno(test_path)

        # Should use backslashes
        assert "\\" in normalized
        assert "/" not in normalized
        # Should be absolute
        assert Path(normalized).is_absolute()

    def test_normalize_relative_path(self):
        """Test normalizing a relative path."""
        test_path = Path("build") / "output" / "app.exe"
        normalized = normalize_path_for_inno(test_path)

        # Should be converted to absolute
        assert Path(normalized).is_absolute()
        # Should use backslashes
        assert "\\" in normalized

    def test_normalize_path_with_forward_slashes(self):
        """Test normalizing a path with forward slashes."""
        test_path = Path("some/path/with/forward/slashes")
        normalized = normalize_path_for_inno(test_path)

        # Should not contain forward slashes
        assert "/" not in normalized
        assert "\\" in normalized


class TestRegistryEntries:
    """Test registry entry generation."""

    def test_generate_basic_registry_entries(self):
        """Test generating basic registry entries."""
        entries = generate_registry_entries("TestApp", "1.0.0", "{app}")

        # Should contain version entry
        assert "Version" in entries
        assert "1.0.0" in entries

        # Should contain install path entry
        assert "InstallPath" in entries
        assert "{app}" in entries

        # Should contain app name in subkey
        assert "TestApp" in entries

        # Should use HKLM root
        assert "HKLM" in entries

        # Should have uninstall flag
        assert "uninsdeletekey" in entries

    def test_registry_entries_format(self):
        """Test that registry entries follow Inno Setup format."""
        entries = generate_registry_entries("MyApp", "2.5.1", "{app}")

        lines = entries.split("\n")

        # Should have multiple entries
        assert len(lines) >= 2

        # Each line should start with Root:
        for line in lines:
            assert line.startswith("Root:")
            assert "Subkey:" in line
            assert "ValueType:" in line
            assert "ValueName:" in line
            assert "ValueData:" in line

    def test_registry_entries_with_special_characters(self):
        """Test registry entries with app names containing special characters."""
        entries = generate_registry_entries("My App 2.0", "1.0.0", "{app}")

        # Should handle spaces in app name
        assert "My App 2.0" in entries


class TestInnoSetupScriptGeneration:
    """Test complete Inno Setup script generation."""

    def test_generate_minimal_script(self, tmp_path):
        """Test generating a minimal Inno Setup script."""
        # Create a dummy executable
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        script = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
        )

        # Should contain all required sections
        assert "[Setup]" in script
        assert "[Languages]" in script
        assert "[Tasks]" in script
        assert "[Files]" in script
        assert "[Icons]" in script
        assert "[Run]" in script
        assert "[Registry]" in script

        # Should contain app information
        assert "AppName=TestApp" in script
        assert "AppVersion=1.0.0" in script
        assert "AppPublisher=Test Publisher" in script

    def test_generate_script_with_icon(self, tmp_path):
        """Test generating script with custom icon."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        icon_path = tmp_path / "icon.ico"
        icon_path.write_text("dummy icon")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        script = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
            icon_path=icon_path,
        )

        # Should reference icon file
        assert "SetupIconFile=" in script
        assert "icon.ico" in script

    def test_generate_script_with_license(self, tmp_path):
        """Test generating script with license file."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        license_path = tmp_path / "LICENSE.txt"
        license_path.write_text("MIT License")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        script = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
            license_file=license_path,
        )

        # Should reference license file
        assert "LicenseFile=" in script
        assert "LICENSE.txt" in script

    def test_generate_script_desktop_icon_option(self, tmp_path):
        """Test desktop icon creation option."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Test with desktop icon enabled
        script_with_icon = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
            create_desktop_icon=True,
        )

        assert "desktopicon" in script_with_icon
        assert "Flags: checked" in script_with_icon or "Tasks: desktopicon" in script_with_icon

        # Test with desktop icon disabled
        script_without_icon = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
            create_desktop_icon=False,
        )

        assert "Flags: unchecked" in script_without_icon

    def test_generate_script_nonexistent_exe(self, tmp_path):
        """Test error when executable doesn't exist."""
        exe_path = tmp_path / "nonexistent.exe"
        output_dir = tmp_path / "output"

        with pytest.raises(ValueError, match="Executable not found"):
            generate_inno_setup_script(
                app_name="TestApp",
                version="1.0.0",
                publisher="Test Publisher",
                exe_path=exe_path,
                output_dir=output_dir,
            )

    def test_generate_script_output_filename(self, tmp_path):
        """Test that output filename is correctly formatted."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        script = generate_inno_setup_script(
            app_name="My Test App",
            version="2.1.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
        )

        # Should contain properly formatted output filename
        assert "OutputBaseFilename=My_Test_App_Setup_2.1.0" in script

    def test_generate_script_uninstall_configuration(self, tmp_path):
        """Test uninstaller configuration in script."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        script = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
        )

        # Should configure uninstaller
        assert "UninstallDisplayName=" in script
        assert "UninstallDisplayIcon=" in script
        assert "{cm:UninstallProgram" in script

    def test_generate_script_with_custom_app_id(self, tmp_path):
        """Test generating script with custom app ID."""
        exe_path = tmp_path / "app.exe"
        exe_path.write_text("dummy")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        custom_id = "{12345678-1234-1234-1234-123456789012}"

        script = generate_inno_setup_script(
            app_name="TestApp",
            version="1.0.0",
            publisher="Test Publisher",
            exe_path=exe_path,
            output_dir=output_dir,
            app_id=custom_id,
        )

        # Should use custom app ID
        assert f"AppId={custom_id}" in script
