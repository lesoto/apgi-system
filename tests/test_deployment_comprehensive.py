"""
Comprehensive tests for deployment module.

Tests deployment validation, system requirements validation,
dependency installation, hardware configuration, and all validation phases.
"""

from unittest.mock import Mock, patch
from pathlib import Path
import json
from datetime import datetime

from apgi_framework.deployment.deployment_validator import (
    DeploymentValidator,
    DeploymentValidationReport,
    ValidationResult,
    ValidationPhase,
)


class TestDeploymentValidator:
    """Test suite for DeploymentValidator."""

    def setup_method(self):
        """Set up test environment."""
        import tempfile

        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = DeploymentValidator(install_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_default_directory(self):
        """Test validator initialization with default directory."""
        validator = DeploymentValidator()
        assert validator.install_dir.name == ".apgi_framework"
        assert validator.system_validator is not None
        assert validator.installation_manager is not None
        assert validator.hardware_manager is not None

    def test_init_custom_directory(self):
        """Test validator initialization with custom directory."""
        custom_dir = Path("/tmp/test_apgi")
        validator = DeploymentValidator(install_dir=custom_dir)
        assert validator.install_dir == custom_dir

    def test_validate_deployment_success(self):
        """Test successful deployment validation."""
        # Mock the validation phases directly
        with patch.object(
            self.validator,
            "system_validator",
            Mock(
                validate_system=Mock(
                    can_run=True,
                    passed_count=5,
                    warning_count=1,
                    failed_count=0,
                    overall_status="pass",
                )
            ),
        ):
            with patch.object(
                self.validator,
                "installation_manager",
                Mock(
                    install_all_dependencies=Mock(
                        success=True,
                        installed_count=10,
                        failed_count=0,
                        skipped_count=2,
                        dependencies={},
                    )
                ),
            ):
                with patch.object(
                    self.validator,
                    "hardware_manager",
                    Mock(
                        list_available_configs=Mock(return_value=["eeg", "pupil"]),
                        devices=[],
                    ),
                ):
                    # Run validation with performance tests enabled
                    report = self.validator.validate_deployment(run_performance_tests=True)

                    # Verify results
                    assert report.overall_passed is True
                    assert report.passed_phases == 6  # All phases passed
                    assert report.failed_phases == 0
                    assert len(report.results) == 6  # 6 phases

    def test_validate_deployment_with_optional_skip(self):
        """Test deployment validation with optional components skipped."""
        with patch.object(
            self.validator,
            "system_validator",
            Mock(
                validate_system=Mock(
                    can_run=True,
                    passed_count=3,
                    warning_count=2,
                    failed_count=0,
                    overall_status="pass",
                )
            ),
        ):
            with patch.object(
                self.validator,
                "installation_manager",
                Mock(
                    install_all_dependencies=Mock(
                        success=False,  # Some dependencies failed
                        installed_count=8,
                        failed_count=2,
                        skipped_count=0,
                        dependencies={},
                    )
                ),
            ):
                # Run validation with skip optional
                report = self.validator.validate_deployment(skip_optional=True)

                # Verify results
                assert report.overall_passed is False  # Overall should fail
                assert report.passed_phases == 3  # Only 3 phases passed
                assert (
                    len([r for r in report.results if r.phase == ValidationPhase.DEPENDENCIES]) == 1
                )

    def test_validate_deployment_with_performance_tests(self):
        """Test deployment validation with performance tests enabled."""
        with patch.object(
            self.validator,
            "system_validator",
            Mock(
                validate_system=Mock(
                    can_run=True,
                    passed_count=4,
                    warning_count=0,
                    failed_count=0,
                    overall_status="pass",
                )
            ),
        ):
            with patch.object(
                self.validator,
                "installation_manager",
                Mock(
                    install_all_dependencies=Mock(
                        success=True,
                        installed_count=10,
                        failed_count=0,
                        skipped_count=0,
                        dependencies={},
                    )
                ),
            ):
                with patch.object(
                    self.validator,
                    "hardware_manager",
                    Mock(
                        list_available_configs=Mock(return_value=["eeg"]),
                        devices=["device1"],
                    ),
                ):
                    # Mock performance test timing
                    with patch("time.time") as mock_time:
                        mock_time.side_effect = [0.0, 0.5, 1.0]  # Fast operations

                    report = self.validator.validate_deployment(run_performance_tests=True)

                    # Verify performance test phase was included
                    performance_results = [
                        r for r in report.results if r.phase == ValidationPhase.PERFORMANCE_TESTS
                    ]
                    assert len(performance_results) == 1
                    assert performance_results[0].passed is True

    def test_validate_deployment_system_requirements_failure(self):
        """Test deployment validation with system requirements failure."""
        with patch.object(
            self.validator,
            "system_validator",
            Mock(
                validate_system=Mock(
                    can_run=False,
                    passed_count=2,
                    warning_count=0,
                    failed_count=3,
                    overall_status="fail",
                )
            ),
        ):
            report = self.validator.validate_deployment()

            # Verify failure
            assert report.overall_passed is False
            assert report.system_requirements_report is not None
            assert any(
                r.phase == ValidationPhase.SYSTEM_REQUIREMENTS and not r.passed
                for r in report.results
            )

    def test_validate_deployment_dependency_failure(self):
        """Test deployment validation with dependency installation failure."""
        with patch.object(
            self.validator,
            "installation_manager",
            Mock(
                install_all_dependencies=Mock(
                    success=False,
                    installed_count=5,
                    failed_count=3,
                    skipped_count=0,
                    dependencies={"numpy": {"error": "Version conflict"}},
                )
            ),
        ):
            report = self.validator.validate_deployment()

            # Verify failure
            assert report.overall_passed is False
            assert report.installation_report is not None
            assert any(
                r.phase == ValidationPhase.DEPENDENCIES and not r.passed for r in report.results
            )

    def test_validate_deployment_hardware_config(self):
        """Test hardware configuration validation."""
        with patch.object(
            self.validator,
            "hardware_manager",
            Mock(
                list_available_configs=Mock(
                    return_value=[
                        "eeg_32chan",
                        "eeg_64chan",
                        "pupil",
                        "cardiac",
                    ]
                ),
                devices=["eeg_device_1", "pupil_device_1"],
            ),
        ):
            report = self.validator.validate_deployment()

            # Verify hardware validation phase
            hw_results = [r for r in report.results if r.phase == ValidationPhase.HARDWARE_CONFIG]
            assert len(hw_results) == 1
            assert hw_results[0].passed is True
            assert "available_configs" in hw_results[0].details
            assert "configured_devices" in hw_results[0].details

    def test_validate_deployment_functional_tests(self):
        """Test functional test phase."""
        with patch("builtins.__import__") as mock_import:
            # Configure import mock - all succeed
            mock_import.return_value = None

            report = self.validator.validate_deployment()

            # Verify functional tests
            func_results = [
                r for r in report.results if r.phase == ValidationPhase.FUNCTIONAL_TESTS
            ]
            assert len(func_results) == 1
            assert func_results[0].passed is True
            assert func_results[0].details["passed"] == 5  # All imports succeeded

    def test_validate_deployment_functional_tests_import_failure(self):
        """Test functional test phase with import failures."""
        with patch("builtins.__import__") as mock_import:
            # Configure import mock - some fail
            def import_side_effect(module_name, *args, **kwargs):
                if module_name in ["numpy", "pandas"]:
                    raise ImportError(f"Cannot import {module_name}")
                return None

            mock_import.side_effect = import_side_effect

            report = self.validator.validate_deployment()

            # Verify partial failure
            func_results = [
                r for r in report.results if r.phase == ValidationPhase.FUNCTIONAL_TESTS
            ]
            assert len(func_results) == 1
            assert func_results[0].passed is False
            assert func_results[0].details["failed"] == 2  # numpy and pandas failed

    def test_validate_deployment_integration_tests(self):
        """Test integration test phase."""
        with patch("builtins.__import__") as mock_import:
            # Configure import mock for integration tests
            mock_import.return_value = None

            report = self.validator.validate_deployment()

            # Verify integration tests
            integ_results = [
                r for r in report.results if r.phase == ValidationPhase.INTEGRATION_TESTS
            ]
            assert len(integ_results) == 1
            assert integ_results[0].passed is True

    def test_save_report(self):
        """Test saving deployment validation report."""
        # Create a mock report
        self.validator.current_report = DeploymentValidationReport(
            validation_id="test_validation",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            results=[
                ValidationResult(
                    phase=ValidationPhase.SYSTEM_REQUIREMENTS,
                    passed=True,
                    message="System requirements OK",
                    details={"test": "value"},
                )
            ],
        )
        self.validator.current_report.overall_passed = True

        # Test saving
        output_path = self.temp_dir / "test_report.json"
        self.validator.save_report(output_path)

        # Verify file was created and contains correct data
        assert output_path.exists()
        with open(output_path, "r") as f:
            saved_data = json.load(f)
            assert saved_data["validation_id"] == "test_validation"
            assert saved_data["overall_passed"] is True
            assert len(saved_data["results"]) == 1

    def test_save_report_no_current_report(self):
        """Test saving report when no current report exists."""
        # Test with no current report
        self.validator.current_report = None

        output_path = self.temp_dir / "test_report.json"
        self.validator.save_report(output_path)

        # Verify file was not created
        assert not output_path.exists()

    def test_generate_summary(self):
        """Test generating human-readable summary."""
        # Create a mock report
        self.validator.current_report = DeploymentValidationReport(
            validation_id="test_summary",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            end_time=datetime(2023, 1, 1, 12, 30),
            results=[
                ValidationResult(
                    phase=ValidationPhase.SYSTEM_REQUIREMENTS,
                    passed=True,
                    message="System requirements OK",
                ),
                ValidationResult(
                    phase=ValidationPhase.DEPENDENCIES,
                    passed=False,
                    message="Dependencies failed",
                ),
                ValidationResult(
                    phase=ValidationPhase.FUNCTIONAL_TESTS,
                    passed=True,
                    message="Functional tests passed",
                ),
            ],
        )
        self.validator.current_report.overall_passed = False

        summary = self.validator.generate_summary()

        # Verify summary content
        assert "APGI Framework Deployment Validation Summary" in summary
        assert "test_summary" in summary
        assert "Overall Status: FAILED" in summary
        assert "Phases Passed: 2" in summary
        assert "Phases Failed: 1" in summary
        assert "✓ PASS | SYSTEM_REQUIREMENTS: System requirements OK" in summary
        assert "✗ FAIL | DEPENDENCIES: Dependencies failed" in summary

    def test_generate_summary_no_report(self):
        """Test generating summary when no report exists."""
        summary = self.validator.generate_summary()
        assert summary == "No validation report available"

    def test_validation_result_dataclass(self):
        """Test ValidationResult dataclass functionality."""
        result = ValidationResult(
            phase=ValidationPhase.SYSTEM_REQUIREMENTS,
            passed=True,
            message="Test message",
            details={"key": "value", "nested": {"data": "test"}},
        )

        assert result.phase == ValidationPhase.SYSTEM_REQUIREMENTS
        assert result.passed is True
        assert result.message == "Test message"
        assert result.details["key"] == "value"
        assert result.details["nested"]["data"] == "test"
        assert isinstance(result.timestamp, datetime)

    def test_deployment_validation_report_dataclass(self):
        """Test DeploymentValidationReport dataclass functionality."""
        report = DeploymentValidationReport(
            validation_id="test_report",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            results=[
                ValidationResult(
                    phase=ValidationPhase.SYSTEM_REQUIREMENTS,
                    passed=True,
                    message="Test",
                )
            ],
        )

        # Test initial state
        assert report.validation_id == "test_report"
        assert report.overall_passed is False  # Default
        assert len(report.results) == 1
        assert report.system_requirements_report is None
        assert report.installation_report is None

        # Test adding results
        result2 = ValidationResult(
            phase=ValidationPhase.DEPENDENCIES, passed=False, message="Test 2"
        )
        report.add_result(result2)

        assert len(report.results) == 2
        assert report.passed_phases == 1
        assert report.failed_phases == 1

        # Test properties
        assert report.passed_phases == 1
        assert report.failed_phases == 1
