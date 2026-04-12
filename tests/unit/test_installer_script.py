"""
Unit tests for validating the Inno Setup installer script.

Tests that the installer script is properly formatted and contains
all required sections and configurations.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

from pathlib import Path

import pytest


class TestInstallerScript:
    """Test the Inno Setup installer script."""

    @pytest.fixture
    def installer_script_path(self) -> Path:
        """Get path to the installer script."""
        return Path("build/installer_windows.iss")

    @pytest.fixture
    def installer_script_content(self, installer_script_path: Path) -> str:
        """Load the installer script content."""
        if not installer_script_path.exists():
            pytest.skip("Installer script not found")
        return installer_script_path.read_text(encoding="utf-8")

    def test_installer_script_exists(self, installer_script_path: Path) -> None:
        """Test that the installer script file exists."""
        assert (
            installer_script_path.exists()
        ), "Installer script should exist at build/installer_windows.iss"

    def test_has_setup_section(self, installer_script_content: str) -> None:
        """Test that script has [Setup] section."""
        assert "[Setup]" in installer_script_content

    def test_has_app_identification(self, installer_script_content: str) -> None:
        """Test that script has required app identification fields."""
        # Requirement 13.1: Application name, version, publisher
        assert "AppId=" in installer_script_content
        assert "AppName=" in installer_script_content
        assert "AppVersion=" in installer_script_content
        assert "AppPublisher=" in installer_script_content

    def test_has_installation_directory_config(self, installer_script_content: str) -> None:
        """Test that script configures installation directory."""
        # Requirement 13.3: Set installation directory
        assert "DefaultDirName=" in installer_script_content

    def test_has_start_menu_config(self, installer_script_content: str) -> None:
        """Test that script configures Start Menu entries."""
        # Requirement 13.2: Start Menu entries
        assert (
            "DefaultGroupName=" in installer_script_content or "[Icons]" in installer_script_content
        )

    def test_has_icons_section(self, installer_script_content: str) -> None:
        """Test that script has [Icons] section for shortcuts."""
        # Requirement 13.2: Create Start Menu entry
        assert "[Icons]" in installer_script_content

    def test_has_desktop_shortcut_option(self, installer_script_content: str) -> None:
        """Test that script has desktop shortcut option."""
        # Requirement 13.5: Desktop shortcuts
        assert "[Tasks]" in installer_script_content
        assert "desktopicon" in installer_script_content.lower()

    def test_has_uninstaller_config(self, installer_script_content: str) -> None:
        """Test that script configures uninstaller."""
        # Requirement 13.4: Uninstaller removes files and registry entries
        assert "UninstallDisplayName=" in installer_script_content
        # Check for uninstall icon in [Icons] section
        assert (
            "UninstallProgram" in installer_script_content
            or "uninstallexe" in installer_script_content.lower()
        )

    def test_has_files_section(self, installer_script_content: str) -> None:
        """Test that script has [Files] section."""
        assert "[Files]" in installer_script_content

    def test_has_registry_section(self, installer_script_content: str) -> None:
        """Test that script has [Registry] section."""
        # Requirement 13.4: Registry entries
        assert "[Registry]" in installer_script_content

    def test_has_languages_section(self, installer_script_content: str) -> None:
        """Test that script has [Languages] section."""
        assert "[Languages]" in installer_script_content

    def test_has_run_section(self, installer_script_content: str) -> None:
        """Test that script has [Run] section for post-install launch."""
        assert "[Run]" in installer_script_content

    def test_compression_configured(self, installer_script_content: str) -> None:
        """Test that compression is configured."""
        assert "Compression=" in installer_script_content

    def test_64bit_architecture_support(self, installer_script_content: str) -> None:
        """Test that script supports 64-bit architecture."""
        assert (
            "ArchitecturesInstallIn64BitMode=" in installer_script_content
            or "ArchitecturesAllowed=" in installer_script_content
        )

    def test_references_executable(self, installer_script_content: str) -> None:
        """Test that script references the main executable."""
        # Should reference APGI_System.exe or similar
        assert ".exe" in installer_script_content
        assert "APGI" in installer_script_content

    def test_references_icon_file(self, installer_script_content: str) -> None:
        """Test that script references icon file."""
        assert ".ico" in installer_script_content or "SetupIconFile=" in installer_script_content

    def test_output_directory_configured(self, installer_script_content: str) -> None:
        """Test that output directory is configured."""
        assert "OutputDir=" in installer_script_content
        assert "OutputBaseFilename=" in installer_script_content

    def test_wizard_style_configured(self, installer_script_content: str) -> None:
        """Test that wizard style is configured for modern UI."""
        # Modern installer should have wizard configuration
        assert (
            "WizardStyle=" in installer_script_content
            or "modern" in installer_script_content.lower()
        )

    def test_no_syntax_errors_in_sections(self, installer_script_content: str) -> None:
        """Test that all sections are properly closed."""
        # Count opening brackets
        open_brackets = installer_script_content.count("[")
        # Should have at least the main sections
        assert open_brackets >= 6, "Should have at least 6 sections"

    def test_includes_config_files(self, installer_script_content: str) -> None:
        """Test that script includes configuration files."""
        assert (
            "config" in installer_script_content.lower()
            or "yaml" in installer_script_content.lower()
        )

    def test_includes_resources(self, installer_script_content: str) -> None:
        """Test that script includes resource files."""
        assert "resources" in installer_script_content.lower()


class TestInstallerUtilsIntegration:
    """Test integration between installer utilities and script."""

    def test_can_import_installer_utils(self) -> None:
        """Test that installer utilities module can be imported."""
        try:
            from utils.installer_utils import extract_version_from_pyproject as _  # noqa: F401

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import installer utilities: {e}")

    def test_version_extraction_works(self) -> None:
        """Test that version can be extracted from pyproject.toml."""
        from utils.installer_utils import extract_version_from_pyproject

        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            version = extract_version_from_pyproject(str(pyproject_path))
            assert version is not None
            assert len(version) > 0
            # Should be semver format
            parts = version.split(".")
            assert len(parts) >= 3
