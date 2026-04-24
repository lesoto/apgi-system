"""
Tests for SystemValidator module - covering system validation runs.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from apgi_framework.system_validator import (
    SystemValidator,
    ValidationLevel,
)
from apgi_framework.main_controller import MainApplicationController


class TestSystemValidator:
    """Focus on coverage of the validation logic and report generation."""

    @pytest.fixture
    def controller(self):
        """Create a mocked controller for the validator."""
        controller = MagicMock(spec=MainApplicationController)
        controller._initialized = True
        controller._mathematical_engine = {}
        controller._neural_simulators = {}
        controller._falsification_tests = {}
        controller._data_manager = {}
        controller.config_manager = MagicMock()
        return controller

    def test_run_basic_validation(self, controller):
        """Test running basic validation level."""
        validator = SystemValidator(controller)

        # Mock individual test methods to avoid calling deep logic
        with patch.object(validator, "_run_mathematical_validation") as mock_math:
            with patch.object(validator, "_run_neural_simulation_validation") as mock_neural:
                report = validator.run_validation(level=ValidationLevel.BASIC)

                assert report is not None
                assert report.validation_level == ValidationLevel.BASIC
                mock_math.assert_called_once()
                mock_neural.assert_called_once()

    def test_collect_system_info(self, controller):
        """Test system info collection."""
        validator = SystemValidator(controller)
        validator.run_validation(level=ValidationLevel.BASIC)

        info = validator.current_report.system_info
        assert info["controller_initialized"] is True
        assert info["config_loaded"] is True

    def test_mathematical_validation_paths(self, controller):
        """Test execution of mathematical validation suite."""
        validator = SystemValidator(controller)

        # Initialize report first as _run_mathematical_validation expects it
        from apgi_framework.system_validator import SystemValidationReport

        validator.current_report = SystemValidationReport("test", datetime.now())

        # Mock the specific test methods called by _run_mathematical_validation
        with patch.object(validator, "_test_apgi_equation_accuracy") as mock_eq:
            mock_eq.return_value = MagicMock()
            validator._run_mathematical_validation()
            mock_eq.assert_called_once()

    def test_validation_error_handling(self, controller):
        """Test how validator handles exceptions during validation."""
        validator = SystemValidator(controller)

        with patch.object(validator, "_collect_system_info", side_effect=Exception("Crash")):
            from apgi_framework.system_validator import ValidationError

            with pytest.raises(ValidationError, match="System validation failed"):
                validator.run_validation()

    def test_report_properties(self):
        """Test SystemValidationReport computed properties."""
        from apgi_framework.system_validator import SystemValidationReport

        report = SystemValidationReport(
            validation_id="test",
            start_time=datetime.now(),
            total_tests=10,
            passed_tests=8,
        )
        assert report.success_rate == 80.0
        assert report.duration is None  # end_time not set

        report.end_time = datetime.now()
        assert report.duration is not None


if __name__ == "__main__":
    pytest.main([__file__])
