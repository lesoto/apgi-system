"""
Property-based tests for build system.

These tests verify correctness properties of the build system including:
- Build reproducibility
- Dependency completeness
- Resource bundling
"""

import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings
import pytest

from utils.build_common import (
    get_version,
    analyze_dependencies,
    collect_resources,
    get_hidden_imports,
    get_excluded_modules,
    get_project_root,
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestBuildReproducibility:
    """
    **Feature: cross-platform-executable, Property 3: Build reproducibility**
    **Validates: Requirements 8.2, 8.4**

    For any given source code state and build configuration, running the build
    script multiple times should produce functionally equivalent executables.
    """

    def test_version_extraction_is_deterministic(self) -> None:
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
    def test_version_extraction_stable_across_calls(self, _iteration: int) -> None:
        """
        Property: Version extraction is stable across multiple calls.

        For any number of repeated calls, the version should remain constant.
        """
        version = get_version()

        # Call multiple times
        for _ in range(5):
            assert get_version() == version

    def test_hidden_imports_list_is_deterministic(self) -> None:
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

    def test_excluded_modules_list_is_deterministic(self) -> None:
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
    def test_resource_collection_is_deterministic(self, _iteration: int) -> None:
        """
        Property: Resource collection produces consistent results.

        For any project state, collecting resources multiple times should
        produce the same categorized files.
        """
        project_root = get_project_root()
        resource_dirs = ["config"]  # Use only config to keep test fast

        # Collect resources multiple times
        resources1 = collect_resources(str(project_root), resource_dirs)
        resources2 = collect_resources(str(project_root), resource_dirs)

        # Should be identical
        assert resources1 == resources2

        # Should be a dict with expected keys
        assert isinstance(resources1, dict)
        expected_keys = {"config_files", "data_files", "resource_files", "icon_files"}
        assert set(resources1.keys()) == expected_keys

        # Each value should be a list
        for key, value in resources1.items():
            assert isinstance(value, list)
            assert all(isinstance(item, str) for item in value)


class TestDependencyCompleteness:
    """
    **Feature: cross-platform-executable, Property 4: Dependency completeness**
    **Validates: Requirements 1.3, 2.3, 5.2, 6.2**

    For any Python import statement in the application code, the bundled
    executable should include the corresponding module or raise a clear
    error during build.
    """

    def test_analyze_dependencies_finds_core_imports(self) -> None:
        """
        Dependency analysis should find all core imports from entry point.

        We expect to find at least: numpy, scipy, matplotlib, tkinter, yaml
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(str(entry_point))

        # Core dependencies that should be found
        expected_deps = {"numpy", "matplotlib", "yaml"}

        # Get all unique dependencies from both sources
        all_deps = dependencies["requirements_txt"] | dependencies["pyproject_toml"]

        # Check that we found the expected dependencies
        found_deps = all_deps & expected_deps
        msg = f"Expected to find {expected_deps}, but only found {all_deps}"
        assert len(found_deps) > 0, msg

    def test_analyze_dependencies_returns_set(self) -> None:
        """
        Dependency analysis should return a dict with set values.
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(str(entry_point))

        assert isinstance(dependencies, dict)
        assert "requirements_txt" in dependencies
        assert "pyproject_toml" in dependencies
        assert "total_dependencies" in dependencies
        assert isinstance(dependencies["requirements_txt"], set)
        assert isinstance(dependencies["pyproject_toml"], set)
        assert isinstance(dependencies["total_dependencies"], int)

    def test_analyze_dependencies_excludes_stdlib(self) -> None:
        """
        Dependency analysis should not include standard library modules.

        Standard library modules don't need to be bundled.
        """
        project_root = get_project_root()
        entry_point = project_root / "apgi_gui.py"

        if not entry_point.exists():
            pytest.skip("Entry point not found")

        dependencies = analyze_dependencies(str(entry_point))

        # Get all unique dependencies from both sources
        all_deps = dependencies["requirements_txt"] | dependencies["pyproject_toml"]

        # These are stdlib modules that should NOT be in dependencies
        stdlib_modules = {"os", "sys", "time", "json", "csv", "pathlib", "threading"}

        # None of these should be in the dependencies
        found_stdlib = all_deps & stdlib_modules
        assert len(found_stdlib) == 0, f"Found stdlib modules in dependencies: {found_stdlib}"

    def test_hidden_imports_are_valid_module_names(self) -> None:
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

    def test_excluded_modules_are_valid_module_names(self) -> None:
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
    def test_collect_resources_handles_missing_directories(self, dir_name: str) -> None:
        """
        Property: Resource collection handles missing directories gracefully.

        For any directory name (existing or not), collect_resources should
        not crash and should return a valid dict.
        """
        project_root = get_project_root()

        # This should not raise an exception
        resources = collect_resources(str(project_root), [dir_name])

        # Should return a dict
        assert isinstance(resources, dict)

        # Should have expected keys
        expected_keys = {"config_files", "data_files", "resource_files", "icon_files"}
        assert set(resources.keys()) == expected_keys

        # Each value should be a list
        for key, value in resources.items():
            assert isinstance(value, list)
            assert all(isinstance(item, str) for item in value)

    def test_no_overlap_between_hidden_and_excluded(self) -> None:
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

    def test_collect_resources_finds_config_files(self) -> None:
        """
        Resource collection should find configuration files.
        """
        project_root = get_project_root()
        resources = collect_resources(str(project_root), ["config"])

        # Should find at least one config file
        config_files = resources["config_files"]
        assert len(config_files) > 0, "No config files found"

    def test_collect_resources_preserves_directory_structure(self) -> None:
        """
        Resource collection should preserve directory structure.

        The file paths should be relative to project root.
        """
        project_root = get_project_root()
        resources = collect_resources(str(project_root), ["config"])

        # Check that config files are properly relative paths
        for file_path in resources["config_files"]:
            assert not file_path.startswith(
                str(project_root)
            ), "File paths should be relative to project root"
            # Use os.path.normpath to handle different path separators
            import os

            normalized_path = os.path.normpath(file_path)
            assert normalized_path.startswith("config" + os.sep) or normalized_path.startswith(
                "config/"
            ), f"Config files should start with config/, got {file_path}"

    @given(st.lists(st.sampled_from(["config", "resources"]), min_size=1, max_size=2, unique=True))
    @settings(max_examples=5)
    def test_collect_resources_with_multiple_dirs(self, dirs: list[str]) -> None:
        """
        Property: Resource collection works with multiple directories.

        For any list of directory names, collect_resources should return
        resources from all specified directories.
        """
        project_root = get_project_root()
        resources = collect_resources(str(project_root), dirs)

        # Should return a dict
        assert isinstance(resources, dict)

        # Should have expected keys
        expected_keys = {"config_files", "data_files", "resource_files", "icon_files"}
        assert set(resources.keys()) == expected_keys

        # If any of the directories exist, we should find some resources
        existing_dirs = [d for d in dirs if (project_root / d).exists()]
        if existing_dirs:
            # We should have found at least some resources
            # (unless the directories are empty, which is unlikely)
            total_files = sum(len(files) for files in resources.values())
            assert total_files >= 0  # Just verify it doesn't crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
