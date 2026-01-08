"""
Unit tests for build dependency analysis.

Tests module exclusion logic, hidden import detection, and resource file discovery.
_Requirements: 12.1, 12.2_
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import sys

# Add project root to path to import build module
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from build_common import (
    analyze_dependencies,
    detect_hidden_imports,
    collect_resources,
    get_version,
    get_excluded_modules,
    should_exclude_module,
)


class TestModuleExclusion:
    """Test module exclusion logic."""

    def test_should_exclude_pytest(self):
        """Test that pytest is excluded."""
        assert should_exclude_module("pytest") is True

    def test_should_exclude_hypothesis(self):
        """Test that hypothesis is excluded."""
        assert should_exclude_module("hypothesis") is True

    def test_should_exclude_sphinx(self):
        """Test that sphinx is excluded."""
        assert should_exclude_module("sphinx") is True

    def test_should_not_exclude_numpy(self):
        """Test that numpy is not excluded."""
        assert should_exclude_module("numpy") is False

    def test_should_not_exclude_scipy(self):
        """Test that scipy is not excluded."""
        assert should_exclude_module("scipy") is False

    def test_should_exclude_submodule(self):
        """Test that submodules of excluded packages are excluded."""
        assert should_exclude_module("pytest.fixtures") is True
        assert should_exclude_module("hypothesis.strategies") is True

    def test_custom_exclusion_list(self):
        """Test with custom exclusion list."""
        custom_exclude = {"custom_module", "another_module"}
        assert should_exclude_module("custom_module", custom_exclude) is True
        assert should_exclude_module("pytest", custom_exclude) is False

    def test_get_excluded_modules_returns_set(self):
        """Test that get_excluded_modules returns a set."""
        excluded = get_excluded_modules()
        assert isinstance(excluded, set)
        assert len(excluded) > 0

    def test_get_excluded_modules_contains_common_tools(self):
        """Test that common development tools are in exclusion list."""
        excluded = get_excluded_modules()
        assert "pytest" in excluded
        assert "hypothesis" in excluded
        assert "sphinx" in excluded
        assert "setuptools" in excluded


class TestHiddenImportDetection:
    """Test hidden import detection."""

    def test_detect_scipy_hidden_imports(self):
        """Test detection of scipy hidden imports."""
        hidden = detect_hidden_imports("scipy")
        assert isinstance(hidden, list)
        assert len(hidden) > 0
        assert "scipy._lib.messagestream" in hidden

    def test_detect_matplotlib_hidden_imports(self):
        """Test detection of matplotlib hidden imports."""
        hidden = detect_hidden_imports("matplotlib")
        assert isinstance(hidden, list)
        assert len(hidden) > 0
        assert any("backend" in imp for imp in hidden)

    def test_detect_tkinter_hidden_imports(self):
        """Test detection of tkinter hidden imports."""
        hidden = detect_hidden_imports("tkinter")
        assert isinstance(hidden, list)
        assert "tkinter.ttk" in hidden
        assert "tkinter.filedialog" in hidden

    def test_detect_numpy_hidden_imports(self):
        """Test detection of numpy hidden imports."""
        hidden = detect_hidden_imports("numpy")
        assert isinstance(hidden, list)
        assert len(hidden) > 0

    def test_unknown_package_returns_empty_list(self):
        """Test that unknown packages return empty list."""
        hidden = detect_hidden_imports("unknown_package_xyz")
        assert isinstance(hidden, list)
        assert len(hidden) == 0

    def test_hidden_imports_are_strings(self):
        """Test that all hidden imports are strings."""
        for package in ["scipy", "matplotlib", "tkinter", "numpy"]:
            hidden = detect_hidden_imports(package)
            assert all(isinstance(imp, str) for imp in hidden)


class TestResourceFileDiscovery:
    """Test resource file discovery."""

    def setup_method(self):
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_collect_yaml_files(self):
        """Test collection of YAML files."""
        # Create test files
        (self.temp_path / "config.yaml").write_text("test: value")
        (self.temp_path / "data.yml").write_text("data: value")

        resources = collect_resources(self.temp_path)

        yaml_files = [r for r in resources if r[0].endswith((".yaml", ".yml"))]
        assert len(yaml_files) == 2

    def test_collect_image_files(self):
        """Test collection of image files."""
        # Create test files
        (self.temp_path / "icon.png").write_bytes(b"fake png data")
        (self.temp_path / "logo.ico").write_bytes(b"fake ico data")

        resources = collect_resources(self.temp_path)

        image_files = [r for r in resources if r[0].endswith((".png", ".ico"))]
        assert len(image_files) == 2

    def test_collect_nested_resources(self):
        """Test collection of resources in subdirectories."""
        # Create nested structure
        subdir = self.temp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.yaml").write_text("nested: value")

        resources = collect_resources(self.temp_path)

        nested_files = [r for r in resources if "nested.yaml" in r[0]]
        assert len(nested_files) == 1
        # Check destination path includes subdirectory
        assert "subdir" in nested_files[0][1]

    def test_collect_with_custom_patterns(self):
        """Test collection with custom file patterns."""
        # Create various files
        (self.temp_path / "data.csv").write_text("a,b,c")
        (self.temp_path / "config.yaml").write_text("test: value")
        (self.temp_path / "readme.txt").write_text("readme")

        # Only collect CSV files
        resources = collect_resources(self.temp_path, patterns=["*.csv"])

        assert len(resources) == 1
        assert resources[0][0].endswith(".csv")

    def test_nonexistent_directory_returns_empty_list(self):
        """Test that nonexistent directory returns empty list."""
        fake_path = Path("/nonexistent/path/xyz")
        resources = collect_resources(fake_path)
        assert isinstance(resources, list)
        assert len(resources) == 0

    def test_resource_tuples_format(self):
        """Test that resources are returned as (source, dest) tuples."""
        (self.temp_path / "test.yaml").write_text("test: value")

        resources = collect_resources(self.temp_path)

        assert len(resources) > 0
        for resource in resources:
            assert isinstance(resource, tuple)
            assert len(resource) == 2
            assert isinstance(resource[0], str)  # source path
            assert isinstance(resource[1], str)  # destination path

    def test_ignores_directories(self):
        """Test that directories are not included in resources."""
        # Create directory and file
        subdir = self.temp_path / "subdir"
        subdir.mkdir()
        (self.temp_path / "file.yaml").write_text("test: value")

        resources = collect_resources(self.temp_path)

        # Should only have the file, not the directory
        assert all(".yaml" in r[0] for r in resources)


class TestDependencyAnalysis:
    """Test dependency analysis from Python files."""

    def setup_method(self):
        """Create temporary directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_simple_imports(self):
        """Test analysis of simple import statements."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import os
import sys
import numpy
""")

        deps = analyze_dependencies(str(test_file))

        assert "os" in deps
        assert "sys" in deps
        assert "numpy" in deps

    def test_analyze_from_imports(self):
        """Test analysis of from...import statements."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
from pathlib import Path
from scipy import stats
""")

        deps = analyze_dependencies(str(test_file))

        assert "pathlib" in deps
        assert "scipy" in deps

    def test_analyze_with_exclusions(self):
        """Test analysis with module exclusions."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import numpy
import pytest
import hypothesis
""")

        exclude = {"pytest", "hypothesis"}
        deps = analyze_dependencies(str(test_file), exclude_modules=exclude)

        assert "numpy" in deps
        assert "pytest" not in deps
        assert "hypothesis" not in deps

    def test_analyze_dotted_imports(self):
        """Test that dotted imports return top-level package."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
import scipy.stats
from matplotlib.pyplot import plot
""")

        deps = analyze_dependencies(str(test_file))

        # Should return top-level packages
        assert "scipy" in deps
        assert "matplotlib" in deps
        # Should not include submodules
        assert "scipy.stats" not in deps

    def test_analyze_nonexistent_file(self):
        """Test analysis of nonexistent file returns empty set."""
        fake_file = self.temp_path / "nonexistent.py"

        deps = analyze_dependencies(str(fake_file))

        assert isinstance(deps, set)
        assert len(deps) == 0

    def test_analyze_invalid_syntax(self):
        """Test that files with syntax errors are handled gracefully."""
        test_file = self.temp_path / "invalid.py"
        test_file.write_text("""
import numpy
this is invalid python syntax!!!
""")

        # Should not raise exception
        deps = analyze_dependencies(str(test_file))

        # May or may not include numpy depending on when parsing fails
        assert isinstance(deps, set)

    def test_returns_set(self):
        """Test that analyze_dependencies returns a set."""
        test_file = self.temp_path / "test.py"
        test_file.write_text("import os")

        deps = analyze_dependencies(str(test_file))

        assert isinstance(deps, set)


class TestVersionExtraction:
    """Test version extraction."""

    def test_get_version_returns_string(self):
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_format(self):
        """Test that version follows semantic versioning format."""
        version = get_version()
        # Should have at least major.minor format
        parts = version.split(".")
        assert len(parts) >= 2
        # First two parts should be numeric
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_get_version_with_init_file(self):
        """Test version extraction from __init__.py file."""
        # This test checks if the function can read from actual init file
        # The actual version depends on what's in the file
        version = get_version()
        assert version is not None
        assert isinstance(version, str)
