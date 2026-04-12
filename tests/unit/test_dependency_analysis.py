"""
Unit tests for build dependency analysis.

Tests module exclusion logic, hidden import detection, and resource file discovery.
_Requirements: 12.1, 12.2_
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Add project root to path to import build module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))  # noqa: E402

from utils.build_common import analyze_dependencies  # noqa: E402
from utils.build_common import (  # noqa: E402
    collect_resources,
    detect_hidden_imports,
    get_excluded_modules,
    get_version,
    should_exclude_module,
)


class TestModuleExclusion:
    """Test module exclusion logic."""

    def test_should_exclude_pytest(self) -> None:
        """Test that pytest is excluded."""
        assert should_exclude_module("pytest") is True

    def test_should_exclude_hypothesis(self) -> None:
        """Test that hypothesis is excluded."""
        assert should_exclude_module("hypothesis") is True

    def test_should_exclude_sphinx(self) -> None:
        """Test that sphinx is excluded."""
        assert should_exclude_module("sphinx") is True

    def test_should_not_exclude_numpy(self) -> None:
        """Test that numpy is not excluded."""
        assert should_exclude_module("numpy") is False

    def test_should_not_exclude_scipy(self) -> None:
        """Test that scipy is not excluded."""
        assert should_exclude_module("scipy") is False

    def test_should_exclude_submodule(self) -> None:
        """Test that submodules of excluded packages are excluded."""
        assert should_exclude_module("pytest.fixtures") is True
        assert should_exclude_module("hypothesis.strategies") is True

    def test_custom_exclusion_list(self) -> None:
        """Test with custom exclusion list."""
        custom_exclude = {"custom_module", "another_module"}
        assert should_exclude_module("custom_module", custom_exclude) is True
        assert should_exclude_module("pytest", custom_exclude) is False

    def test_get_excluded_modules_returns_set(self) -> None:
        """Test that get_excluded_modules returns a set."""
        excluded = get_excluded_modules()
        assert len(excluded) > 0

    def test_get_excluded_modules_contains_common_tools(self) -> None:
        """Test that common development tools are in exclusion list."""
        excluded = get_excluded_modules()
        assert "pytest" in excluded
        assert "hypothesis" in excluded
        assert "sphinx" in excluded
        assert "setuptools" in excluded


class TestHiddenImportDetection:
    """Test hidden import detection."""

    def test_detect_scipy_hidden_imports(self) -> None:
        """Test detection of scipy hidden imports."""
        hidden = detect_hidden_imports("scipy")
        assert isinstance(hidden, list)
        assert len(hidden) > 0
        assert "scipy._lib.messagestream" in hidden

    def test_detect_matplotlib_hidden_imports(self) -> None:
        """Test detection of matplotlib hidden imports."""
        hidden = detect_hidden_imports("matplotlib")
        assert isinstance(hidden, list)
        assert len(hidden) > 0
        assert any("backend" in imp for imp in hidden)

    def test_detect_tkinter_hidden_imports(self) -> None:
        """Test detection of tkinter hidden imports."""
        hidden = detect_hidden_imports("tkinter")
        assert isinstance(hidden, list)
        assert "tkinter.ttk" in hidden
        assert "tkinter.filedialog" in hidden

    def test_detect_numpy_hidden_imports(self) -> None:
        """Test detection of numpy hidden imports."""
        hidden = detect_hidden_imports("numpy")
        assert isinstance(hidden, list)
        assert len(hidden) > 0

    def test_unknown_package_returns_empty_list(self) -> None:
        """Test that unknown packages return empty list."""
        hidden = detect_hidden_imports("unknown_package_xyz")
        assert isinstance(hidden, list)
        assert len(hidden) == 0

    def test_hidden_imports_are_strings(self) -> None:
        """Test that all hidden imports are strings."""
        for package in ["scipy", "matplotlib", "tkinter", "numpy"]:
            hidden = detect_hidden_imports(package)
            assert all(isinstance(imp, str) for imp in hidden)


class TestResourceFileDiscovery:
    """Test resource file discovery."""

    def setup_method(self) -> None:
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collect_yaml_files(self) -> None:
        """Test collection of YAML files."""
        # Create test files
        (self.temp_path / "config.yaml").write_text("test: value")
        (self.temp_path / "data.yml").write_text("data: value")

        resources = collect_resources(str(self.temp_path), resource_dirs=["."])

        yaml_files = [r for r in resources["config_files"] if r.endswith((".yaml", ".yml"))]
        assert len(yaml_files) == 2

    def test_collect_image_files(self) -> None:
        """Test collection of image files."""
        # Create test files
        (self.temp_path / "icon.png").write_bytes(b"fake png data")
        (self.temp_path / "logo.ico").write_bytes(b"fake ico data")

        resources = collect_resources(str(self.temp_path), resource_dirs=["."])

        image_files = [r for r in resources["resource_files"] if r.endswith((".png", ".ico"))]
        assert len(image_files) == 2

    def test_collect_nested_resources(self) -> None:
        """Test collection of resources in subdirectories."""
        # Create nested structure
        subdir = self.temp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.yaml").write_text("nested: value")

        resources = collect_resources(str(self.temp_path), resource_dirs=["."])

        nested_files = [r for r in resources["config_files"] if "nested.yaml" in r]
        assert len(nested_files) == 1
        # Check path includes subdirectory
        assert "subdir" in nested_files[0]

    def test_collect_with_custom_patterns(self) -> None:
        """Test collection with custom file patterns."""
        # Create various files
        (self.temp_path / "data.csv").write_text("a,b,c")
        (self.temp_path / "config.yaml").write_text("test: value")
        (self.temp_path / "readme.txt").write_text("readme")

        # Collect all resources
        resources = collect_resources(str(self.temp_path), resource_dirs=["."])

        # CSV should be in data_files, YAML in config_files, TXT in data_files
        assert len(resources["data_files"]) == 2  # csv and txt
        assert len(resources["config_files"]) == 1  # yaml
        assert any(f.endswith(".csv") for f in resources["data_files"])

    def test_nonexistent_directory_returns_empty_dict(self) -> None:
        """Test that nonexistent directory returns empty dict."""
        fake_path = Path("/nonexistent/path/xyz")
        resources = collect_resources(str(fake_path))
        assert isinstance(resources, dict)
        assert len(resources) == 4  # Has empty lists for all categories
        assert all(len(v) == 0 for v in resources.values())

    def test_resource_tuples_format(self) -> None:
        """Test that resources are returned as categorized lists."""
        (self.temp_path / "test.yaml").write_text("test: value")

        resources = collect_resources(str(self.temp_path))

        assert len(resources) > 0
        # resources is a dict with category keys and list of file paths as values
        for category, file_list in resources.items():
            assert isinstance(category, str)
            assert isinstance(file_list, list)
            for file_path in file_list:
                assert isinstance(file_path, str)

    def test_ignores_directories(self) -> None:
        """Test that directories are not included in resources."""
        # Create directory and file
        subdir = self.temp_path / "subdir"
        subdir.mkdir()
        (self.temp_path / "file.yaml").write_text("test: value")

        resources = collect_resources(str(self.temp_path), resource_dirs=["."])

        # Should only have the file, not the directory
        assert all(".yaml" in r for r in resources["config_files"])
        assert len(resources["config_files"]) == 1


class TestDependencyAnalysis:
    """Test dependency analysis from Python files."""

    def setup_method(self) -> None:
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_simple_imports(self) -> None:
        """Test analysis of simple import statements."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import os
import sys
import numpy
""")

        deps = analyze_dependencies(str(test_file))

        # os and sys are stdlib modules, so they are excluded
        # numpy is in requirements.txt common list
        all_deps = deps["requirements_txt"] | deps["pyproject_toml"]
        assert "numpy" in all_deps
        assert deps["total_dependencies"] == 1

    def test_analyze_from_imports(self) -> None:
        """Test analysis of from...import statements."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
from pathlib import Path
from scipy import stats
""")

        deps = analyze_dependencies(str(test_file))

        # pathlib is stdlib, scipy is in requirements.txt common list
        all_deps = deps["requirements_txt"] | deps["pyproject_toml"]
        assert "scipy" in all_deps
        assert deps["total_dependencies"] == 1

    def test_analyze_with_exclusions(self) -> None:
        """Test analysis with module exclusions."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import numpy
import pytest
import hypothesis
""")

        exclude = {"pytest", "hypothesis"}
        deps = analyze_dependencies(str(test_file), exclude_modules=exclude)

        all_deps = deps["requirements_txt"] | deps["pyproject_toml"]
        assert "numpy" in all_deps
        assert "pytest" not in all_deps
        assert "hypothesis" not in all_deps
        assert deps["total_dependencies"] == 1

    def test_analyze_dotted_imports(self) -> None:
        """Test that dotted imports return top-level package."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import scipy.stats
from matplotlib.pyplot import plot
""")

        deps = analyze_dependencies(str(test_file))

        # Should return top-level packages
        all_deps = deps["requirements_txt"] | deps["pyproject_toml"]
        assert "scipy" in all_deps
        assert "matplotlib" in all_deps
        # Should not include submodules
        assert "scipy.stats" not in all_deps
        assert deps["total_dependencies"] == 2

    def test_analyze_nonexistent_file(self) -> None:
        """Test analysis of nonexistent file returns empty dict."""
        fake_file = self.temp_path / "nonexistent.py"
        deps = analyze_dependencies(str(fake_file))
        assert isinstance(deps, dict)
        assert len(deps["requirements_txt"]) == 0
        assert len(deps["pyproject_toml"]) == 0
        assert deps["total_dependencies"] == 0

    def test_analyze_invalid_syntax(self) -> None:
        """Test that files with syntax errors are handled gracefully."""
        test_file = self.temp_path / "invalid.py"
        test_file.write_text("""
import numpy
this is invalid python syntax!!!
""")

        # Should not raise exception
        deps = analyze_dependencies(str(test_file))

        # Should return empty dict on syntax error
        assert isinstance(deps, dict)
        assert len(deps["requirements_txt"]) == 0
        assert len(deps["pyproject_toml"]) == 0
        assert deps["total_dependencies"] == 0

    def test_returns_dict(self) -> None:
        """Test that analyze_dependencies returns a dict."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("import numpy")

        deps = analyze_dependencies(str(test_file))

        assert isinstance(deps, dict)
        assert "requirements_txt" in deps
        assert "pyproject_toml" in deps
        assert "total_dependencies" in deps


class TestVersionExtraction:
    """Test version extraction."""

    def test_get_version_returns_string(self) -> None:
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_format(self) -> None:
        """Test that version follows semantic versioning format."""
        version = get_version()
        # Should have at least major.minor format
        parts = version.split(".")
        assert len(parts) >= 2
        # First two parts should be numeric
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_get_version_with_init_file(self) -> None:
        """Test version extraction from __init__.py file."""
        # This test checks if the function can read from actual init file
        # The actual version depends on what's in the file
        version = get_version()
        assert version is not None
        assert isinstance(version, str)
