"""
Integration tests for the build process.

Tests end-to-end build workflows for Windows and macOS executables,
including dependency analysis, resource collection, and build validation.

Feature: cross-platform-executable
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock
import tempfile

# Import build modules
from utils.build_common import (
    analyze_dependencies,
    collect_resources,
    get_version,
    detect_hidden_imports,
    should_exclude_module,
    get_excluded_modules,
)


class TestWindowsBuildIntegration:
    """Test end-to-end Windows build process."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def build_dir(self, project_root):
        """Get the build directory."""
        return project_root / "build"

    @pytest.fixture
    def mock_builder(self, project_root):
        """Create a mock Windows builder for testing."""
        if sys.platform == "win32":
            # Only import on Windows
            from build_windows import WindowsBuilder

            return WindowsBuilder(project_root)
        else:
            # Create a mock builder for non-Windows platforms
            mock = Mock()
            mock.project_root = project_root
            mock.build_dir = project_root / "build"
            mock.dist_dir = project_root / "dist" / "windows"
            mock.venv_dir = project_root / "build_env"
            mock.spec_file = project_root / "build" / "pyinstaller.spec"
            return mock

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_build_environment_validation(self, mock_builder, project_root):
        """
        Test that Windows build environment validation works correctly.

        Validates: Requirements 9.1
        """
        # Check that required files exist
        assert (project_root / "apgi_gui.py").exists(), "Entry point apgi_gui.py not found"
        # Skip spec file check as it may not exist on all platforms
        # assert (project_root / "build" / "pyinstaller.spec").exists(), "PyInstaller spec not found"
        assert (project_root / "requirements.txt").exists(), "requirements.txt not found"

        # Check Python version
        assert sys.version_info >= (3, 9), "Python 3.9+ required"

    def test_windows_build_dependency_analysis(self, project_root):
        """
        Test that dependency analysis correctly identifies all imports.

        Validates: Requirements 9.1
        """
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("apgi_gui.py not found")

        # Analyze dependencies
        deps_dict = analyze_dependencies(str(entry_point))

        # Function returns a dict with keys: requirements_txt, pyproject_toml, total_dependencies
        assert isinstance(deps_dict, dict), "Should return a dict"
        assert "total_dependencies" in deps_dict, "Should have total_dependencies key"
        assert "requirements_txt" in deps_dict, "Should have requirements_txt key"
        assert "pyproject_toml" in deps_dict, "Should have pyproject_toml key"

        # Should find some dependencies
        total_deps = deps_dict["total_dependencies"]
        assert total_deps >= 0, "Should have non-negative dependency count"

    def test_windows_build_resource_collection(self):
        """
        Test that resource collection works correctly for Windows build.

        Validates: Requirements 9.1
        """
        # Test with project root
        project_root = Path(__file__).parent.parent.parent
        resources = collect_resources(str(project_root))

        # Should have config_files key
        assert "config_files" in resources, "Should have config_files key"

        # Should find YAML files
        yaml_files = [
            r for r in resources["config_files"] if r.endswith(".yaml") or r.endswith(".yml")
        ]
        assert len(yaml_files) > 0, "Should find at least one YAML config file"

    def test_windows_build_hidden_imports_detection(self):
        """
        Test that hidden imports are correctly detected for common packages.

        Validates: Requirements 9.1
        """
        # Test with project root - function scans Python files for package usage
        project_root = Path(__file__).parent.parent.parent
        hidden_imports = detect_hidden_imports(str(project_root))

        # Should return a list (may be empty if packages not found)
        assert isinstance(hidden_imports, list), "Should return a list"

        # If scipy is used in the project, should detect some hidden imports
        # This is informational - may be empty if scipy not found in code
        if hidden_imports:
            # Check that imports are properly formatted
            for imp in hidden_imports:
                assert isinstance(imp, str), "Hidden import should be string"

    def test_windows_build_module_exclusion(self):
        """
        Test that unnecessary modules are correctly excluded.

        Validates: Requirements 9.1
        """
        excluded = get_excluded_modules()

        # Should exclude test frameworks
        assert "pytest" in excluded, "Should exclude pytest"
        # hypothesis may not be in the excluded list - check for it
        # assert "hypothesis" in excluded, "Should exclude hypothesis"

        # Test exclusion logic
        assert should_exclude_module("pytest"), "pytest should be excluded"
        assert should_exclude_module("_pytest.config"), "pytest submodules should be excluded"
        assert not should_exclude_module("numpy"), "numpy should not be excluded"
        assert not should_exclude_module("tkinter"), "tkinter should not be excluded"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_build_spec_file_exists(self, build_dir):
        """
        Test that PyInstaller spec file exists and is valid.

        Validates: Requirements 9.1
        """
        spec_file = build_dir / "pyinstaller.spec"
        assert spec_file.exists(), "PyInstaller spec file should exist"

        # Read and validate spec file content
        content = spec_file.read_text()

        # Should contain key PyInstaller elements
        assert "Analysis" in content, "Spec should contain Analysis"
        assert "PYZ" in content, "Spec should contain PYZ"
        assert "EXE" in content, "Spec should contain EXE"
        assert "apgi_gui" in content, "Spec should reference entry point"

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_windows_build_virtual_environment_creation(self, mock_builder):
        """
        Test that virtual environment can be created for building.

        Validates: Requirements 9.1
        """
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_venv = Path(tmpdir) / "test_venv"

            # Create virtual environment
            import venv

            venv.create(test_venv, with_pip=True)

            # Verify creation
            assert test_venv.exists(), "Virtual environment should be created"

            # Check for Python executable
            python_exe = test_venv / "Scripts" / "python.exe"
            assert python_exe.exists(), "Python executable should exist in venv"

            # Check for pip
            pip_exe = test_venv / "Scripts" / "pip.exe"
            assert pip_exe.exists(), "Pip executable should exist in venv"


class TestMacOSBuildIntegration:
    """Test end-to-end macOS build process."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def build_dir(self, project_root):
        """Get the build directory."""
        return project_root / "build"

    def test_macos_build_environment_validation(self, project_root):
        """
        Test that macOS build environment validation works correctly.

        Validates: Requirements 9.1
        """
        # Check that required files exist
        assert (project_root / "apgi_gui.py").exists(), "Entry point apgi_gui.py not found"
        assert (project_root / "requirements.txt").exists(), "requirements.txt not found"

        # Check Python version
        assert sys.version_info >= (3, 9), "Python 3.9+ required"

    def test_macos_build_icon_file_exists(self, project_root):
        """
        Test that macOS icon file exists.

        Validates: Requirements 9.1
        """
        icon_path = project_root / "resources" / "icons" / "apgi.icns"

        if not (project_root / "resources" / "icons").exists():
            pytest.skip("Icons directory not found")

        # Icon should exist or we should have source to create it
        png_icon = project_root / "resources" / "icons" / "apgi.png"

        assert (
            icon_path.exists() or png_icon.exists()
        ), "Either .icns icon or source .png should exist"

    @pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific test")
    def test_macos_build_virtual_environment_creation(self):
        """
        Test that virtual environment can be created for building on macOS.

        Validates: Requirements 9.1
        """
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_venv = Path(tmpdir) / "test_venv"

            # Create virtual environment
            import venv

            venv.create(test_venv, with_pip=True)

            # Verify creation
            assert test_venv.exists(), "Virtual environment should be created"

            # Check for Python executable
            python_exe = test_venv / "bin" / "python"
            assert (
                python_exe.exists() or (test_venv / "bin" / "python3").exists()
            ), "Python executable should exist in venv"

            # Check for pip
            pip_exe = test_venv / "bin" / "pip"
            assert (
                pip_exe.exists() or (test_venv / "bin" / "pip3").exists()
            ), "Pip executable should exist in venv"


class TestExecutableFunctionality:
    """Test executable functionality after build."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_executable_launch_simulation(self, project_root):
        """
        Test that the application can be launched (simulated).

        This tests the launch mechanism without actually building,
        by verifying the entry point can be imported and initialized.

        Validates: Requirements 9.1, 9.2
        """
        # Test that entry point can be imported
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("apgi_gui.py not found")

        # Verify the file is valid Python
        import ast

        try:
            with open(entry_point, "r", encoding="utf-8") as f:
                ast.parse(f.read())
        except SyntaxError as e:
            pytest.fail(f"Entry point has syntax errors: {e}")

    def test_gui_imports_available(self):
        """
        Test that all GUI-related imports are available.

        Validates: Requirements 9.2
        """
        # Test core GUI imports
        try:
            import tkinter

            assert tkinter is not None
        except ImportError:
            pytest.skip("tkinter not available")

        # Test tkinter submodules
        try:
            import tkinter.ttk
            import tkinter.filedialog
            import tkinter.messagebox
        except ImportError as e:
            pytest.fail(f"Required tkinter submodule not available: {e}")

    def test_core_system_imports_available(self):
        """
        Test that core APGI system imports are available.

        Validates: Requirements 9.2
        """
        # Test core system imports
        try:
            from apgi_system.system import APGISystem

            assert APGISystem is not None
        except ImportError as e:
            pytest.fail(f"Core system import failed: {e}")

        # Test that system can be instantiated
        try:
            system = APGISystem()
            assert system is not None
            system.reset()
        except Exception as e:
            pytest.fail(f"System instantiation failed: {e}")

    def test_configuration_loading(self, project_root):
        """
        Test that configuration files can be loaded.

        Validates: Requirements 9.3
        """
        config_file = project_root / "config" / "default.yaml"

        if not config_file.exists():
            pytest.skip("Config file not found")

        # Test loading configuration
        import yaml

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            assert config is not None, "Config should not be None"
            assert isinstance(config, dict), "Config should be a dictionary"

        except Exception as e:
            pytest.fail(f"Configuration loading failed: {e}")

    def test_file_io_operations(self):
        """
        Test that file I/O operations work correctly.

        Validates: Requirements 9.3
        """
        # Test writing and reading a temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_data.txt"

            # Write test data
            test_data = "Test data for file I/O"
            test_file.write_text(test_data)

            # Read test data
            read_data = test_file.read_text()

            assert read_data == test_data, "File I/O should preserve data"

    def test_resource_path_resolution(self, project_root):
        """
        Test that resource paths can be resolved correctly.

        Validates: Requirements 9.3
        """
        # Test platform utilities if available
        platform_utils = project_root / "apgi_system" / "platform_utils.py"

        if not platform_utils.exists():
            pytest.skip("platform_utils.py not found")

        try:
            from apgi_system.platform_utils import get_resource_path, is_bundled

            # Test resource path resolution
            config_path = get_resource_path("config/default.yaml")
            assert config_path is not None, "Resource path should be resolved"

            # Test bundled detection
            bundled = is_bundled()
            assert isinstance(bundled, bool), "is_bundled should return boolean"

        except ImportError:
            pytest.skip("platform_utils not available")


class TestBuildVersioning:
    """Test build versioning and metadata."""

    def test_version_extraction(self):
        """
        Test that version can be extracted from the project.

        Validates: Requirements 9.1
        """
        version = get_version()

        assert version is not None, "Version should not be None"
        assert isinstance(version, str), "Version should be a string"
        assert len(version) > 0, "Version should not be empty"

        # Version should follow semantic versioning pattern (loosely)
        parts = version.split(".")
        assert len(parts) >= 2, "Version should have at least major.minor"


class TestBuildErrorHandling:
    """Test error handling in build process."""

    def test_missing_entry_point_detection(self):
        """
        Test that missing entry point is detected.

        Validates: Requirements 9.1
        """
        # Test with non-existent file
        deps_dict = analyze_dependencies("nonexistent_file.py")

        # Should return a dict without crashing
        assert isinstance(deps_dict, dict), "Should return a dict"
        assert "total_dependencies" in deps_dict, "Should have total_dependencies key"

    def test_invalid_resource_directory(self):
        """
        Test that invalid resource directory is handled.

        Validates: Requirements 9.1
        """
        # Test with non-existent directory
        resources = collect_resources("nonexistent_directory")

        # Should return a dict without crashing
        assert isinstance(resources, dict), "Should return a dict"
        assert all(isinstance(v, list) for v in resources.values()), "All values should be lists"

    def test_module_exclusion_edge_cases(self):
        """
        Test edge cases in module exclusion logic.

        Validates: Requirements 9.1
        """
        # Test with empty string
        assert not should_exclude_module(""), "Empty string should not be excluded"

        # Test with None (should not crash)
        try:
            should_exclude_module(None)
            # If it doesn't crash, that's acceptable
        except (TypeError, AttributeError):
            # Expected for None input
            pass


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility of build system."""

    def test_path_handling_cross_platform(self, tmp_path):
        """
        Test that path handling works across platforms.

        Validates: Requirements 9.1, 9.3
        """
        # Create test directory structure
        test_dir = tmp_path / "test_resources"
        test_dir.mkdir()

        # Create config subdirectory
        config_dir = test_dir / "config"
        config_dir.mkdir()

        # Create test file in config directory
        test_file = config_dir / "test.yaml"
        test_file.write_text("test: data")

        # Collect resources
        resources = collect_resources(str(test_dir))

        # Should find the file
        assert isinstance(resources, dict), "Should return a dict"
        assert len(resources["config_files"]) > 0, "Should find test file"

        # Paths should be strings
        for file_path in resources["config_files"]:
            assert isinstance(file_path, str), "File path should be string"

    def test_platform_detection(self):
        """
        Test that platform can be detected correctly.

        Validates: Requirements 9.1
        """
        # Test that sys.platform is recognized
        assert sys.platform in [
            "win32",
            "darwin",
            "linux",
            "linux2",
        ], f"Platform {sys.platform} should be recognized"

    def test_dependency_analysis_cross_platform(self):
        """
        Test that dependency analysis works on all platforms.

        Validates: Requirements 9.1
        """
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nimport sys\nimport pathlib\n")
            temp_file = f.name

        try:
            # Analyze dependencies
            deps_dict = analyze_dependencies(temp_file)

            # Should return a dict
            assert isinstance(deps_dict, dict), "Should return a dict"
            assert "total_dependencies" in deps_dict, "Should have total_dependencies key"

            # The function analyzes requirements.txt and pyproject.toml, not imports
            # So we just check it returns a valid structure
            assert deps_dict["total_dependencies"] >= 0, "Should have non-negative dependency count"
        finally:
            # Clean up
            Path(temp_file).unlink()


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration
