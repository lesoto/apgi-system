"""
Basic tests for deployment module core functionality.

Tests only the DeploymentValidator class without dependencies on missing modules.
"""

from pathlib import Path
import tempfile
import json
from datetime import datetime

from apgi_framework.deployment.deployment_validator import (
    DeploymentValidator,
    DeploymentValidationReport,
    ValidationResult,
    ValidationPhase,
)


class TestDeploymentValidatorBasic:
    """Test suite for DeploymentValidator core functionality."""

    def setup_method(self):
        """Set up test environment."""
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

    def test_init_custom_directory(self):
        """Test validator initialization with custom directory."""
        custom_dir = Path("/tmp/test_apgi")
        validator = DeploymentValidator(install_dir=custom_dir)
        assert validator.install_dir == custom_dir

    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            phase=ValidationPhase.SYSTEM_REQUIREMENTS,
            passed=True,
            message="Test passed",
            details={"test": "value"},
        )

        assert result.phase == ValidationPhase.SYSTEM_REQUIREMENTS
        assert result.passed is True
        assert result.message == "Test passed"
        assert result.details["test"] == "value"
        assert isinstance(result.timestamp, datetime)

    def test_deployment_validation_report_creation(self):
        """Test DeploymentValidationReport creation."""
        report = DeploymentValidationReport(
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

        assert report.validation_id == "test_validation"
        assert report.start_time == datetime(2023, 1, 1, 12, 0, 0)
        assert len(report.results) == 1
        assert report.overall_passed is False  # Default
        assert report.system_requirements_report is None
        assert report.installation_report is None

    def test_deployment_validation_report_add_result(self):
        """Test adding results to DeploymentValidationReport."""
        report = DeploymentValidationReport(
            validation_id="test_validation", start_time=datetime(2023, 1, 1, 12, 0, 0)
        )

        result1 = ValidationResult(
            phase=ValidationPhase.SYSTEM_REQUIREMENTS, passed=True, message="System OK"
        )
        result2 = ValidationResult(
            phase=ValidationPhase.DEPENDENCIES,
            passed=False,
            message="Dependencies failed",
        )

        report.add_result(result1)
        report.add_result(result2)

        assert len(report.results) == 2
        assert report.passed_phases == 1
        assert report.failed_phases == 1

    def test_deployment_validation_report_properties(self):
        """Test DeploymentValidationReport properties."""
        report = DeploymentValidationReport(
            validation_id="test_validation",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            results=[
                ValidationResult(
                    phase=ValidationPhase.SYSTEM_REQUIREMENTS,
                    passed=True,
                    message="System OK",
                ),
                ValidationResult(
                    phase=ValidationPhase.DEPENDENCIES,
                    passed=False,
                    message="Dependencies failed",
                ),
            ],
        )

        # Test passed_phases property
        assert report.passed_phases == 1

        # Test failed_phases property
        assert report.failed_phases == 1

        # Test overall_passed property (should be False since one failed)
        assert report.overall_passed is False

    def test_generate_summary(self):
        """Test summary generation."""
        report = DeploymentValidationReport(
            validation_id="test_validation",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            end_time=datetime(2023, 1, 1, 12, 30, 0),
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
            ],
        )
        report.overall_passed = False

        # Assign report to validator
        self.validator.current_report = report

        summary = self.validator.generate_summary()

        assert "APGI Framework Deployment Validation Summary" in summary
        assert "test_validation" in summary
        assert "Overall Status: FAILED" in summary
        assert "Phases Passed: 1" in summary
        assert "Phases Failed: 1" in summary

    def test_save_report(self):
        """Test saving report to file."""
        # Create mock report
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
