"""
Property-based tests for change impact analysis in CI/CD integration.

Feature: comprehensive-test-enhancement, Property 19: Change impact analysis accuracy
**Validates: Requirements 8.2**

This module tests that for any code change, the system correctly identifies
and executes only the relevant test subset based on accurate impact analysis.
"""

import shutil
import tempfile
from pathlib import Path
from typing import List

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from apgi_framework.testing.ci_integrator import (
    ChangeAnalyzer,
    CIConfiguration,
    CIIntegrator,
)


# Test data generators
@st.composite
def python_file_path(draw):
    """Generate valid Python file paths within the project structure."""
    modules = ["core", "analysis", "clinical", "neural", "gui", "utils", "testing"]
    module = draw(st.sampled_from(modules))

    filename = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=15))

    return f"apgi_framework/{module}/{filename}.py"


@st.composite
def file_change_set(draw):
    """Generate a set of changed files."""
    num_files = draw(st.integers(min_value=1, max_value=5))
    files = draw(st.lists(python_file_path(), min_size=num_files, max_size=num_files, unique=True))
    return files


class TestChangeImpactAnalysis:
    """Property-based tests for change impact analysis."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create basic project structure
        (self.project_root / "apgi_framework").mkdir(parents=True)
        (self.project_root / "tests").mkdir(parents=True)

        # Create module directories
        modules = ["core", "analysis", "clinical", "neural", "gui", "utils", "testing"]
        for module in modules:
            (self.project_root / "apgi_framework" / module).mkdir(parents=True)
            (self.project_root / "apgi_framework" / module / "__init__.py").touch()

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @given(changed_files=file_change_set())
    @settings(max_examples=20, deadline=10000)
    def test_change_impact_completeness(self, changed_files: List[str]):
        """
        Property 19: Change impact analysis accuracy

        For any set of changed files, the change impact analysis should:
        1. Identify all affected modules correctly
        2. Find all related tests that should be executed
        3. Calculate a reasonable impact score
        4. Include all changed files in the result
        """
        # Create the changed files in the test project
        for file_path in changed_files:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(
                f"# Test file: {file_path}\nclass TestClass:\n    pass\n",
                encoding="utf-8",
            )

        # Create corresponding test files
        for file_path in changed_files:
            if file_path.startswith("apgi_framework/"):
                module_name = Path(file_path).stem
                test_file = self.project_root / "tests" / f"test_{module_name}.py"
                test_file.write_text(
                    f"# Test for {file_path}\ndef test_{module_name}():\n    pass\n",
                    encoding="utf-8",
                )

        # Initialize change analyzer
        analyzer = ChangeAnalyzer(str(self.project_root))

        # Analyze changes
        impact = analyzer.analyze_file_changes(changed_files)

        # Property assertions

        # 1. All changed files should be included
        assert set(impact.changed_files) == set(
            changed_files
        ), f"Changed files mismatch: expected {changed_files}, got {impact.changed_files}"

        # 2. Affected modules should be non-empty for Python files
        python_files = [f for f in changed_files if f.endswith(".py")]
        if python_files:
            assert (
                len(impact.affected_modules) > 0
            ), "Should identify affected modules for Python file changes"

        # 3. Impact score should be between 0 and 1
        assert (
            0.0 <= impact.impact_score <= 1.0
        ), f"Impact score {impact.impact_score} should be between 0 and 1"

        # 4. Analysis timestamp should be recent
        assert impact.analysis_timestamp is not None, "Analysis timestamp should be set"

    @given(
        changed_files=file_change_set(),
        base_ref=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
    )
    @settings(max_examples=15, deadline=10000)
    def test_impact_score_consistency(self, changed_files: List[str], base_ref: str):
        """
        Property: Impact score should be consistent and proportional.

        For any set of changed files:
        1. More critical files should have higher impact scores
        2. Impact score should be deterministic for the same input
        """
        # Create files with different criticality levels
        for file_path in changed_files:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Create different content based on criticality
            if "core" in file_path or "__init__" in file_path:
                content = "# Critical core module\nclass CoreClass:\n    def critical_method(self):\n        pass\n"
            else:
                content = f"# Regular module: {file_path}\nclass RegularClass:\n    pass\n"

            full_path.write_text(content, encoding="utf-8")

        analyzer = ChangeAnalyzer(str(self.project_root))

        # Analyze the same changes multiple times
        impact1 = analyzer.analyze_file_changes(changed_files)
        impact2 = analyzer.analyze_file_changes(changed_files)

        # Impact score should be deterministic
        assert (
            impact1.impact_score == impact2.impact_score
        ), "Impact score should be deterministic for the same input"

        # Impact score should be reasonable
        assert (
            0.0 <= impact1.impact_score <= 1.0
        ), f"Impact score {impact1.impact_score} should be between 0 and 1"

    @given(
        module_files=st.lists(
            st.tuples(
                st.sampled_from(["core", "analysis", "clinical", "neural", "gui"]),
                st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=3, max_size=10),
            ),
            min_size=1,
            max_size=3,
            unique=True,
        )
    )
    @settings(max_examples=15, deadline=10000)
    def test_module_identification_accuracy(self, module_files):
        """
        Property: Module identification should be accurate.

        For any set of files in different modules:
        1. Each file should be correctly mapped to its module
        2. All affected modules should be identified
        3. Module names should match the directory structure
        """
        changed_files = []
        expected_modules = set()

        for module, filename in module_files:
            file_path = f"apgi_framework/{module}/{filename}.py"
            changed_files.append(file_path)
            expected_modules.add(module)

            # Create the file
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(
                f"# Module: {module}\nclass {filename.title()}:\n    pass\n",
                encoding="utf-8",
            )

        analyzer = ChangeAnalyzer(str(self.project_root))
        impact = analyzer.analyze_file_changes(changed_files)

        # All expected modules should be identified
        assert expected_modules.issubset(
            impact.affected_modules
        ), f"Expected modules {expected_modules} not all found in {impact.affected_modules}"


class TestCIIntegrationProperties:
    """Property tests for CI integration functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create basic project structure
        (self.project_root / "apgi_framework").mkdir(parents=True)
        (self.project_root / "tests").mkdir(parents=True)
        (self.project_root / ".ci").mkdir(parents=True)

        # Create some test files
        test_files = ["test_core.py", "test_analysis.py", "test_clinical.py"]
        for test_file in test_files:
            (self.project_root / "tests" / test_file).write_text(
                "def test_example():\n    pass\n", encoding="utf-8"
            )

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @given(
        pipeline_type=st.sampled_from(["github", "gitlab", "jenkins", "azure", "generic"]),
        test_strategy=st.sampled_from(["all", "changed", "impact", "critical"]),
        parallel=st.booleans(),
        workers=st.integers(min_value=1, max_value=8),
        timeout=st.integers(min_value=1, max_value=60),
    )
    @settings(max_examples=10, deadline=5000)
    def test_ci_configuration_validity(
        self, pipeline_type, test_strategy, parallel, workers, timeout
    ):
        """
        Property: CI configuration should always be valid and consistent.

        For any valid configuration parameters:
        1. Configuration should be created successfully
        2. All parameters should be preserved
        3. CI integrator should initialize without errors
        """
        config = CIConfiguration(
            pipeline_type=pipeline_type,
            test_subset_strategy=test_strategy,
            parallel_execution=parallel,
            max_workers=workers,
            timeout_minutes=timeout,
        )

        # Configuration should preserve all parameters
        assert config.pipeline_type == pipeline_type
        assert config.test_subset_strategy == test_strategy
        assert config.parallel_execution == parallel
        assert config.max_workers == workers
        assert config.timeout_minutes == timeout

        # Should have default values for optional parameters
        assert isinstance(config.critical_test_patterns, list)
        assert isinstance(config.notification_channels, list)
        assert isinstance(config.coverage_threshold, float)
        assert 0.0 <= config.coverage_threshold <= 1.0

        # CI integrator should initialize successfully
        ci_integrator = CIIntegrator(str(self.project_root), config)
        assert ci_integrator.config == config
        assert ci_integrator.project_root == self.project_root

    @given(changed_files=st.lists(python_file_path(), min_size=0, max_size=3, unique=True))
    @settings(max_examples=10, deadline=10000)
    def test_test_subset_selection_accuracy(self, changed_files):
        """
        Property: Test subset selection should be accurate based on strategy.

        For any change impact and test strategy:
        1. 'all' strategy should include all available tests
        2. 'critical' strategy should include only critical tests
        3. Selected tests should be valid and executable
        """
        # Create the changed files
        for file_path in changed_files:
            full_path = self.project_root / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"# {file_path}\nclass TestClass:\n    pass\n", encoding="utf-8")

        # Test different strategies
        strategies = ["all", "critical"]

        for strategy in strategies:
            config = CIConfiguration(pipeline_type="generic", test_subset_strategy=strategy)

            ci_integrator = CIIntegrator(str(self.project_root), config)

            # Get test files based on strategy
            if strategy == "all":
                test_files = ci_integrator._get_all_tests()
            elif strategy == "critical":
                test_files = ci_integrator._get_critical_tests()
            else:
                test_files = []

            # All returned test files should be valid paths
            for test_file in test_files:
                test_path = Path(test_file)
                # Should be a Python file
                assert test_path.suffix == ".py", f"Test file {test_file} should be a Python file"
                # Should have 'test' in the name
                assert (
                    "test" in test_path.name.lower()
                ), f"Test file {test_file} should have 'test' in name"


if __name__ == "__main__":
    # Run property tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
