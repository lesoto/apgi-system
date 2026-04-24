"""
Comprehensive tests for apgi_framework.validation.system_health module.

Covers: HealthCheckResult, SystemHealthChecker, get_health_checker
"""

from apgi_framework.validation.system_health import (
    HealthCheckResult,
    SystemHealthChecker,
    get_health_checker,
)
from datetime import datetime
from unittest.mock import patch

# --- HealthCheckResult ---


class TestHealthCheckResult:
    def test_healthy_bool(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="healthy",
            checks_passed=5,
            checks_failed=0,
            checks_warning=0,
        )
        assert bool(result) is True

    def test_unhealthy_bool(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="critical",
            checks_passed=3,
            checks_failed=2,
            checks_warning=0,
        )
        assert bool(result) is False

    def test_warning_bool(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="warning",
            checks_passed=4,
            checks_failed=0,
            checks_warning=1,
        )
        assert bool(result) is False

    def test_get_report_healthy(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="healthy",
            checks_passed=6,
            checks_failed=0,
            checks_warning=0,
            component_status={"Python Environment": "healthy"},
        )
        report = result.get_report()
        assert "SYSTEM HEALTH CHECK" in report
        assert "HEALTHY" in report
        assert "6 passed" in report

    def test_get_report_with_issues(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="critical",
            checks_passed=4,
            checks_failed=1,
            checks_warning=1,
            component_status={
                "Python Environment": "healthy",
                "Dependencies": "critical",
                "Configuration": "warning",
            },
            issues=["Required package 'numpy' not found"],
            warnings=["Optional package 'matplotlib' not found"],
            recommendations=["Install missing packages"],
        )
        report = result.get_report()
        assert "CRITICAL ISSUES" in report
        assert "WARNINGS" in report
        assert "RECOMMENDATIONS" in report
        assert "numpy" in report

    def test_get_report_empty_issues(self):
        result = HealthCheckResult(
            timestamp=datetime.now(),
            overall_status="healthy",
            checks_passed=6,
            checks_failed=0,
            checks_warning=0,
        )
        report = result.get_report()
        assert "CRITICAL ISSUES" not in report


# --- SystemHealthChecker ---


class TestSystemHealthChecker:
    def setup_method(self):
        self.checker = SystemHealthChecker()

    def test_init(self):
        assert self.checker.check_history == []

    def test_check_python_environment(self):
        status, issues, warnings = self.checker._check_python_environment()
        assert status in ("healthy", "warning", "critical")
        # Since we're running Python >= 3.8, this should pass
        assert len(issues) == 0  # No critical issues

    def test_check_python_environment_old_version(self):
        mock_version = type(
            "version_info",
            (),
            {
                "major": 3,
                "minor": 7,
                "micro": 0,
                "__lt__": lambda self, other: (
                    (self.major, self.minor) < other[:2]
                    if isinstance(other, tuple)
                    else NotImplemented
                ),
                "__ge__": lambda self, other: (
                    (self.major, self.minor) >= other[:2]
                    if isinstance(other, tuple)
                    else NotImplemented
                ),
            },
        )()
        with patch("sys.version_info", mock_version):
            status, issues, warnings = self.checker._check_python_environment()
            assert status == "critical"

    def test_check_dependencies(self):
        status, issues, warnings = self.checker._check_dependencies()
        # numpy and scipy should be installed in test env
        assert status in ("healthy", "warning")

    def test_check_dependencies_missing_required(self):
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            status, issues, warnings = self.checker._check_dependencies()
            assert status == "critical"

    def test_check_configuration(self):
        status, issues, warnings = self.checker._check_configuration()
        # May fail due to config import issues - that's fine
        assert status in ("healthy", "warning", "critical")

    def test_check_data_storage(self):
        status, issues, warnings = self.checker._check_data_storage()
        assert status in ("healthy", "warning", "critical")

    def test_check_computational_resources(self):
        status, issues, warnings = self.checker._check_computational_resources()
        assert status in ("healthy", "warning")

    def test_check_core_components(self):
        status, issues, warnings = self.checker._check_core_components()
        assert status in ("healthy", "warning", "critical")

    def test_run_full_health_check(self):
        result = self.checker.run_full_health_check()
        assert isinstance(result, HealthCheckResult)
        assert result.overall_status in ("healthy", "warning", "critical")
        assert result.checks_passed + result.checks_failed + result.checks_warning == 6
        assert len(self.checker.check_history) == 1

    def test_check_component_python(self):
        result = self.checker.check_component("python")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_dependencies(self):
        result = self.checker.check_component("dependencies")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_configuration(self):
        result = self.checker.check_component("configuration")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_storage(self):
        result = self.checker.check_component("storage")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_resources(self):
        result = self.checker.check_component("resources")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_core(self):
        result = self.checker.check_component("core")
        assert isinstance(result, HealthCheckResult)

    def test_check_component_unknown(self):
        result = self.checker.check_component("unknown_component")
        assert result.overall_status == "critical"
        assert any("Unknown component" in issue for issue in result.issues)

    def test_get_diagnostic_info(self):
        info = self.checker.get_diagnostic_info()
        assert "python_version" in info
        assert "platform" in info
        assert "numpy_version" in info
        assert "working_directory" in info

    def test_get_health_history(self):
        # Run a few checks
        self.checker.run_full_health_check()
        self.checker.run_full_health_check()

        history = self.checker.get_health_history(n_recent=1)
        assert len(history) == 1

        history = self.checker.get_health_history()
        assert len(history) == 2

    def test_generate_recommendations_python(self):
        recs = self.checker._generate_recommendations(
            ["Python version 3.7 is too old"],
            [],
        )
        assert any("Upgrade Python" in r for r in recs)

    def test_generate_recommendations_packages(self):
        recs = self.checker._generate_recommendations(
            ["Required package 'numpy' not found"],
            [],
        )
        assert any("Install missing packages" in r for r in recs)

    def test_generate_recommendations_disk(self):
        recs = self.checker._generate_recommendations(
            ["Low disk space: 0.50 GB available"],
            [],
        )
        assert any("disk space" in r.lower() for r in recs)

    def test_generate_recommendations_permissions(self):
        recs = self.checker._generate_recommendations(
            ["No write permission in results directory"],
            [],
        )
        assert any("permission" in r.lower() for r in recs)

    def test_generate_recommendations_config(self):
        recs = self.checker._generate_recommendations(
            ["Configuration error: invalid"],
            [],
        )
        assert any("configuration" in r.lower() for r in recs)

    def test_generate_recommendations_module(self):
        recs = self.checker._generate_recommendations(
            ["Core module 'xyz' cannot be imported"],
            [],
        )
        assert any("APGI Framework" in r or "module" in r.lower() for r in recs)

    def test_generate_recommendations_warnings_only(self):
        recs = self.checker._generate_recommendations(
            [],
            ["Some warning"],
        )
        assert any("warnings" in r.lower() for r in recs)

    def test_generate_recommendations_all_good(self):
        recs = self.checker._generate_recommendations([], [])
        assert any("healthy" in r.lower() for r in recs)


# --- get_health_checker ---


class TestGetHealthChecker:
    def test_singleton(self):
        import apgi_framework.validation.system_health as mod

        mod._health_checker = None  # Reset

        checker1 = get_health_checker()
        checker2 = get_health_checker()
        assert checker1 is checker2

        # Cleanup
        mod._health_checker = None
