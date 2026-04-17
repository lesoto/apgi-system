"""
Property-based tests for cross-platform executable functionality.

This module implements property-based tests using Hypothesis to verify
universal properties that should hold across all valid inputs for the
platform utilities and executable build system.

Each test is tagged with the corresponding property from the design document
and validates specific requirements from the requirements document.
"""

import platform
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from apgi_simulation.platform_utils import (
    get_config_dir,
    get_data_dir,
    get_platform,
    get_resource_path,
    is_bundled,
)

# Configure Hypothesis for property-based testing
settings.register_profile(
    "property_tests",
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
    ],
)
settings.load_profile("property_tests")


class TestPlatformDetectionProperties:
    """Property-based tests for platform detection and utilities."""

    def test_property_platform_detection_accuracy(self) -> None:
        """
        **Feature: cross-platform-executable, Property 2: Platform detection accuracy**

        For any execution environment, get_platform() should return the correct
        platform identifier that matches the actual operating system.

        **Validates: Requirements 3.4**
        """
        detected_platform = get_platform()
        actual_system = platform.system().lower()

        # Map actual system to expected platform identifier
        expected_mapping = {
            "windows": "windows",
            "darwin": "macos",
            "linux": "linux",
        }

        expected_platform = expected_mapping.get(actual_system, "unknown")

        assert (
            detected_platform == expected_platform
        ), f"Platform detection mismatch: detected={detected_platform}, expected={expected_platform}, actual_system={actual_system}"

        # Platform should be one of the known values
        assert detected_platform in [
            "windows",
            "macos",
            "linux",
            "unknown",
        ], f"Invalid platform identifier: {detected_platform}"

    @given(
        relative_paths=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-."
                ),
                min_size=1,
                max_size=20,
            ),
            min_size=1,
            max_size=3,
        )
    )
    def test_property_resource_path_resolution_consistency(self, relative_paths: list[str]) -> None:
        """
        **Feature: cross-platform-executable, Property 1: Resource path resolution consistency**

        For any resource file path, calling get_resource_path() should return a valid
        absolute path that exists in both development and bundled environments.

        **Validates: Requirements 3.4, 4.2**
        """
        # Filter out invalid path components
        relative_paths = [p for p in relative_paths if p and p not in [".", ".."]]
        assume(len(relative_paths) > 0)

        # Create a valid relative path
        relative_path = "/".join(relative_paths)

        # Get the resource path
        resource_path = get_resource_path(relative_path)

        # Should return a Path object
        assert isinstance(
            resource_path, Path
        ), f"get_resource_path should return Path object, got {type(resource_path)}"

        # Should be an absolute path
        assert resource_path.is_absolute(), f"Resource path should be absolute: {resource_path}"

        # Path should be valid (no invalid characters for the platform)
        path_str = str(resource_path)
        assert len(path_str) > 0, "Resource path should not be empty"

        # Should contain the relative path components
        for component in relative_paths:
            if component:  # Skip empty components
                assert (
                    component in path_str
                ), f"Resource path should contain component '{component}': {path_str}"

    @given(
        path_components=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
                ),
                min_size=1,
                max_size=15,
            ),
            min_size=1,
            max_size=4,
        )
    )
    def test_property_cross_platform_path_compatibility(self, path_components: list[str]) -> None:
        """
        **Feature: cross-platform-executable, Property 6: Cross-platform path compatibility**

        For any file path constructed in the code, it should work correctly on both
        Windows and macOS without modification.

        **Validates: Requirements 3.1**
        """
        # Filter out invalid components
        path_components = [p for p in path_components if p and p not in [".", ".."]]
        assume(len(path_components) > 0)

        # Construct path using pathlib (cross-platform)
        constructed_path = Path(*path_components)

        # Path should be valid
        assert constructed_path is not None, "Constructed path should not be None"

        # Convert to string - should work on any platform
        path_str = str(constructed_path)
        assert len(path_str) > 0, "Path string should not be empty"

        # Should contain all components
        for component in path_components:
            if component:
                assert (
                    component in path_str
                ), f"Path should contain component '{component}': {path_str}"

        # Path separators should be platform-appropriate
        if get_platform() == "windows":
            # Windows can use both / and \, but Path normalizes to \
            assert "\\" in path_str or "/" in path_str or len(path_components) == 1
        else:
            # Unix-like systems use /
            assert "/" in path_str or len(path_components) == 1

        # Reconstruct using get_resource_path to ensure consistency
        relative_path = "/".join(path_components)
        resource_path = get_resource_path(relative_path)

        # Should be absolute
        assert resource_path.is_absolute(), f"Resource path should be absolute: {resource_path}"

    def test_property_config_dir_writable(self) -> None:
        """
        Test that config directory is writable.

        For any execution environment, get_config_dir() should return a directory
        that exists and is writable.

        **Validates: Requirements 4.2**
        """
        config_dir = get_config_dir()

        # Should return a Path object
        assert isinstance(config_dir, Path), "get_config_dir should return Path object"

        # Should be an absolute path
        assert config_dir.is_absolute(), f"Config dir should be absolute: {config_dir}"

        # Directory should exist (created by the function)
        assert config_dir.exists(), f"Config directory should exist: {config_dir}"
        assert config_dir.is_dir(), f"Config path should be a directory: {config_dir}"

        # Should be writable - test by creating a temp file
        test_file = config_dir / ".test_write"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Should be able to write to config directory"
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"Config directory should be writable: {e}")

    def test_property_data_dir_writable(self) -> None:
        """
        Test that data directory is writable.

        For any execution environment, get_data_dir() should return a directory
        that exists and is writable.

        **Validates: Requirements 4.2**
        """
        data_dir = get_data_dir()

        # Should return a Path object
        assert isinstance(data_dir, Path), "get_data_dir should return Path object"

        # Should be an absolute path
        assert data_dir.is_absolute(), f"Data dir should be absolute: {data_dir}"

        # Directory should exist (created by the function)
        assert data_dir.exists(), f"Data directory should exist: {data_dir}"
        assert data_dir.is_dir(), f"Data path should be a directory: {data_dir}"

        # Should be writable - test by creating a temp file
        test_file = data_dir / ".test_write"
        try:
            test_file.write_text("test")
            assert test_file.exists(), "Should be able to write to data directory"
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"Data directory should be writable: {e}")

    def test_property_bundled_detection_consistency(self) -> None:
        """
        Test that is_bundled() returns consistent results.

        For any execution environment, is_bundled() should return a boolean
        that accurately reflects whether the code is running as a bundled executable.

        **Validates: Requirements 3.4**
        """
        bundled = is_bundled()

        # Should return a boolean
        assert isinstance(bundled, bool), f"is_bundled should return bool, got {type(bundled)}"

        # In development (running tests), should be False
        # (unless tests are run from a bundled executable, which is unlikely)
        assert bundled is False, "Should not be bundled when running tests from source"

        # Check consistency with sys attributes
        has_frozen = getattr(sys, "frozen", False)
        has_meipass = hasattr(sys, "_MEIPASS")

        expected_bundled = has_frozen and has_meipass

        assert (
            bundled == expected_bundled
        ), f"is_bundled() result should match sys attributes: bundled={bundled}, frozen={has_frozen}, meipass={has_meipass}"

    @given(num_calls=st.integers(min_value=1, max_value=10))
    def test_property_platform_detection_idempotent(self, num_calls: int) -> None:
        """
        Test that platform detection is idempotent.

        For any number of calls, get_platform() should always return the same value.

        **Validates: Requirements 3.4**
        """
        results = [get_platform() for _ in range(num_calls)]

        # All results should be identical
        assert all(
            r == results[0] for r in results
        ), f"get_platform() should return consistent results: {results}"

    @given(num_calls=st.integers(min_value=1, max_value=10))
    def test_property_config_dir_idempotent(self, num_calls: int) -> None:
        """
        Test that config directory resolution is idempotent.

        For any number of calls, get_config_dir() should always return the same path.

        **Validates: Requirements 4.2**
        """
        results = [get_config_dir() for _ in range(num_calls)]

        # All results should be identical
        assert all(
            r == results[0] for r in results
        ), f"get_config_dir() should return consistent results: {results}"

    @given(num_calls=st.integers(min_value=1, max_value=10))
    def test_property_data_dir_idempotent(self, num_calls: int) -> None:
        """
        Test that data directory resolution is idempotent.

        For any number of calls, get_data_dir() should always return the same path.

        **Validates: Requirements 4.2**
        """
        results = [get_data_dir() for _ in range(num_calls)]

        # All results should be identical
        assert all(
            r == results[0] for r in results
        ), f"get_data_dir() should return consistent results: {results}"
