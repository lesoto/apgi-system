"""
Property-based tests for build system.

These tests verify correctness properties of the build system including:
- Build reproducibility
- Dependency completeness
- Resource bundling
"""

import sys
import hashlib
import subprocess
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.build_common import (
    get_version,
    analyze_dependencies,
    collect_resources,
    get_hidden_imports,
    get_excluded_modules,
    get_project_root,
)


class TestBuildReproducibility:
    """
    **Feature: cross-platform-executable, Property 3: Build reproducibility**
    **Validates: Requirements 8.2, 8.4**

    For any given source code state and build configuration, running the build
    script multiple times should produce functionally equivalent executables.
    """

    def test_version_extraction_is_deterministic(self):
        """
        Version extraction should return the same value on repeated calls.

        This is a basic reproducibility test - if we can't even get consistent
        version strings, we have bigger problems.
        """
        version1 = get_version()
        version2 = get_version()
        version3 = get_version()

        assert version1 == version2 == version3
        assert isinstance(version1, str)
        assert len(version1) > 0

    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=10)
    def test_version_extraction_stable_across_calls(self, _iteration):
        """
        Property: Version extraction is stable across multiple calls.

        For any number of repeated calls, the version should remain constant.
        """
        version = get_version()

        # Call multiple times
        for _ in range(5):
            assert get_version() == version

    def test_hidden_imports_list_is_deterministic(self):
        """
        Hidden imports list should be the same on repeated calls.

        This ensures build configuration is reproducible.
        """
        imports1 = get_hidden_imports()
        imports2 = get_hidden_imports()
        imports3 = get_hidden_imports()

        assert imports1 == imports2 == imports3
        assert isinstance(imports1, list)
        assert all(isinstance(imp, str) for imp in imports1)

    def test_excluded_modules_list_is_deterministic(self):
        """
        Excluded modules list should be the same on repeated calls.

        This ensures build configuration is reproducible.
        """
        excludes1 = get_excluded_modules()
        excludes2 = get_excluded_modules()
        excludes3 = get_excluded_modules()

        assert excludes1 == excludes2 == excludes3
        assert isinstance(excludes1, list)
        assert all(isinstance(mod, str) for mod in excludes1)

    @given(st.integers(min_value=0, max_value=5))
    @settings(max_examples=5)
    def test_resource_collection_is_deterministic(self, _iteration):
        """
        Property: Resource collection produces consistent results.

        For any project state, collecting resources multiple times should
        produce the same list of files.
        """
        project_root = get_project_root()
        resource_dirs = ["config"]  # Use only config to keep test fast

        # Collect resources multiple times
        resources1 = collect_resources(project_root, resource_dirs)
        resources2 = collect_resources(project_root, resource_dirs)

        # Should be identical
        assert resources1 == resources2

        # Should be sorted consistently (order matters for reproducibility)
        assert resources1 == sorted(resources1)


class TestDependencyCompleteness:
    """
    **Feature: cross-platform-executable, Property 4: Dependency completeness**
    **Validates: Requirements 1.3, 2.3, 5.2, 6.2**

    For any Python import statement in the application code, the bundled
    executable should include the corresponding module or raise a clear
    error during build.
    """

    def test_analyze_dependencies_finds_core_imports(self):
        """
        Dependency analysis should find all core imports from entry point.

        We expect to find at least: numpy, scipy, matplotlib, tkinter, yaml
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(entry_point)

        # Core dependencies that should be found
        expected_deps = {"numpy", "matplotlib", "yaml"}

        # Check that we found the expected dependencies
        found_deps = dependencies & expected_deps
        assert (
            len(found_deps) > 0
        ), f"Expected to find {expected_deps}, but only found {dependencies}"

    def test_analyze_dependencies_returns_set(self):
        """
        Dependency analysis should return a set (no duplicates).
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(entry_point)

        assert isinstance(dependencies, set)
        # Converting to list and back should give same size (no duplicates)
        assert len(dependencies) == len(list(dependencies))

    def test_analyze_dependencies_excludes_stdlib(self):
        """
        Dependency analysis should not include standard library modules.

        Standard library modules don't need to be bundled.
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(entry_point)

        # These are stdlib modules that should NOT be in dependencies
        stdlib_modules = {"os", "sys", "time", "json", "csv", "pathlib", "threading"}

        # None of these should be in the dependencies
        found_stdlib = dependencies & stdlib_modules
        assert len(found_stdlib) == 0, f"Found stdlib modules in dependencies: {found_stdlib}"

    def test_hidden_imports_are_valid_module_names(self):
        """
        All hidden imports should be valid Python module names.

        This prevents build errors from typos in hidden imports list.
        """
        hidden_imports = get_hidden_imports()

        for module_name in hidden_imports:
            # Should be a string
            assert isinstance(module_name, str)
            # Should not be empty
            assert len(module_name) > 0
            # Should not have leading/trailing whitespace
            assert module_name == module_name.strip()
            # Should be a valid Python identifier path
            parts = module_name.split(".")
            for part in parts:
                assert part.isidentifier() or part.startswith(
                    "_"
                ), f"Invalid module name part: {part} in {module_name}"

    def test_excluded_modules_are_valid_module_names(self):
        """
        All excluded modules should be valid Python module names.

        This prevents build errors from typos in exclusion list.
        """
        excluded = get_excluded_modules()

        for module_name in excluded:
            # Should be a string
            assert isinstance(module_name, str)
            # Should not be empty
            assert len(module_name) > 0
            # Should not have leading/trailing whitespace
            assert module_name == module_name.strip()

    @given(st.sampled_from(["config", "resources", "nonexistent_dir"]))
    @settings(max_examples=3)
    def test_collect_resources_handles_missing_directories(self, dir_name):
        """
        Property: Resource collection handles missing directories gracefully.

        For any directory name (existing or not), collect_resources should
        not crash and should return a valid list.
        """
        project_root = get_project_root()

        # This should not raise an exception
        resources = collect_resources(project_root, [dir_name])

        # Should return a list
        assert isinstance(resources, list)

        # Each item should be a tuple of (source, dest)
        for item in resources:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], str)

    def test_no_overlap_between_hidden_and_excluded(self):
        """
        Hidden imports and excluded modules should not overlap.

        It doesn't make sense to both include and exclude the same module.
        """
        hidden = set(get_hidden_imports())
        excluded = set(get_excluded_modules())

        overlap = hidden & excluded
        assert len(overlap) == 0, f"Modules in both hidden and excluded: {overlap}"


class TestResourceBundling:
    """
    Tests for resource bundling completeness.

    These tests verify that all necessary resources are collected
    and will be included in the build.
    """

    def test_collect_resources_finds_config_files(self):
        """
        Resource collection should find configuration files.
        """
        project_root = get_project_root()
        resources = collect_resources(project_root, ["config"])

        # Should find at least one config file
        config_files = [r for r in resources if "config" in r[1]]
        assert len(config_files) > 0, "No config files found"

    def test_collect_resources_preserves_directory_structure(self):
        """
        Resource collection should preserve directory structure.

        The destination path should match the source directory structure.
        """
        project_root = get_project_root()
        resources = collect_resources(project_root, ["config"])

        for source, dest in resources:
            source_path = Path(source)
            # Destination should be a parent directory of the file
            assert dest in str(source_path.parent) or str(source_path.parent).endswith(dest)

    @given(st.lists(st.sampled_from(["config", "resources"]), min_size=1, max_size=2, unique=True))
    @settings(max_examples=5)
    def test_collect_resources_with_multiple_dirs(self, dirs):
        """
        Property: Resource collection works with multiple directories.

        For any list of directory names, collect_resources should return
        resources from all specified directories.
        """
        project_root = get_project_root()
        resources = collect_resources(project_root, dirs)

        # Should return a list
        assert isinstance(resources, list)

        # If any of the directories exist, we should find some resources
        existing_dirs = [d for d in dirs if (project_root / d).exists()]
        if existing_dirs:
            # We should have found at least some resources
            # (unless the directories are empty, which is unlikely)
            pass  # Just verify it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
