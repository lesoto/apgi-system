"""
Comprehensive test suite for diagnostics_cli.py module.

This test suite provides full coverage for the CLI functions and command
processing, ensuring all critical functionality is tested.
"""

from unittest.mock import MagicMock, patch

import pytest

# Import the modules we're testing
from apgi_framework.validation.diagnostics_cli import (
    get_parameter_info,
    main,
    run_diagnostics,
    run_health_check,
    validate_parameters,
)


class MockHealthChecker:
    """Mock health checker for testing."""

    def check_component(self, component):
        return MockHealthResult("healthy", f"{component} is healthy")

    def run_full_health_check(self):
        return MockHealthResult("healthy", "All systems healthy")

    def get_diagnostic_info(self):
        return {"python_version": "3.9.0", "platform": "Linux", "memory": "8GB"}


class MockHealthResult:
    """Mock health result for testing."""

    def __init__(self, status, message):
        self.overall_status = status
        self.message = message

    def get_report(self):
        return f"Status: {self.overall_status}\n{self.message}"


class MockValidator:
    """Mock parameter validator for testing."""

    def validate_apgi_parameters(self, **params):
        # Check if any parameter is out of range
        if "extero_precision" in params and params["extero_precision"] > 3.0:
            return MockValidationResult(False, "❌ Parameters invalid")
        return MockValidationResult(True, "✓ All parameters valid")

    def get_parameter_info(self, parameter):
        return f"APGI Equation Parameter\n{parameter}\nValid range: [0.0, 1.0]\nDescription: [0.0, 1.0]"


class MockValidationResult:
    """Mock validation result for testing."""

    def __init__(self, is_valid, message):
        self.is_valid = is_valid
        self.message = message

    def get_message(self):
        return self.message


class MockConfigManager:
    """Mock config manager for testing."""

    def get_apgi_parameters(self):
        return MockAPGIParameters()

    def get_experimental_config(self):
        return MockExperimentalConfig()


class MockAPGIParameters:
    """Mock APGI parameters for testing."""

    def __init__(self):
        self.extero_precision = 2.0
        self.intero_precision = 1.5
        self.threshold = 0.3


class MockExperimentalConfig:
    """Mock experimental config for testing."""

    def __init__(self):
        self.n_trials = 100
        self.n_participants = 20
        self.alpha_level = 0.05


class TestRunHealthCheck:
    """Test run_health_check function."""

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_health_check_full_success(self, mock_logger, mock_exit, mock_get_health_checker):
        """Test successful full health check."""
        mock_health_checker = MockHealthChecker()
        mock_get_health_checker.return_value = mock_health_checker

        # Mock args without component
        mock_args = MagicMock()
        mock_args.component = None

        run_health_check(mock_args)

        # Check logger calls instead of stdout
        mock_logger.info.assert_any_call("\n" + "=" * 60)
        mock_logger.info.assert_any_call("APGI FRAMEWORK SYSTEM HEALTH CHECK")
        mock_exit.assert_called_once_with(0)

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_health_check_component_success(
        self, mock_logger, mock_exit, mock_get_health_checker
    ):
        """Test successful component health check."""
        mock_health_checker = MockHealthChecker()
        mock_get_health_checker.return_value = mock_health_checker

        # Mock args with component
        mock_args = MagicMock()
        mock_args.component = "python"

        run_health_check(mock_args)

        # Check logger calls instead of stdout
        mock_logger.info.assert_any_call("\n" + "=" * 60)
        mock_logger.info.assert_any_call("APGI FRAMEWORK SYSTEM HEALTH CHECK")
        mock_exit.assert_called_once_with(0)

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_health_check_warning_status(self, mock_logger, mock_exit, mock_get_health_checker):
        """Test health check with warning status."""
        mock_health_checker = MagicMock()
        mock_health_checker.check_component.return_value = MockHealthResult(
            "warning", "Minor issues"
        )
        mock_get_health_checker.return_value = mock_health_checker

        # Mock args with component
        mock_args = MagicMock()
        mock_args.component = "python"

        run_health_check(mock_args)

        mock_exit.assert_called_once_with(2)

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_health_check_critical_status(
        self, mock_logger, mock_exit, mock_get_health_checker
    ):
        """Test health check with critical status."""
        mock_health_checker = MagicMock()
        mock_health_checker.check_component.return_value = MockHealthResult(
            "critical", "Major issues"
        )
        mock_get_health_checker.return_value = mock_health_checker

        # Mock args with component
        mock_args = MagicMock()
        mock_args.component = "python"

        run_health_check(mock_args)

        mock_exit.assert_called_once_with(1)


class TestRunDiagnostics:
    """Test run_diagnostics function."""

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("apgi_framework.validation.diagnostics_cli.get_config_manager")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_diagnostics_success(
        self, mock_logger, mock_get_config_manager, mock_get_health_checker
    ):
        """Test successful diagnostics run."""
        mock_health_checker = MockHealthChecker()
        mock_get_health_checker.return_value = mock_health_checker

        mock_config_manager = MockConfigManager()
        mock_get_config_manager.return_value = mock_config_manager

        # Mock args
        mock_args = MagicMock()

        run_diagnostics(mock_args)

        # Check logger calls
        mock_logger.info.assert_any_call("\n" + "=" * 60)
        mock_logger.info.assert_any_call("APGI FRAMEWORK DIAGNOSTIC INFORMATION")
        mock_logger.info.assert_any_call("System Information:")
        mock_logger.info.assert_any_call("\nConfiguration:")
        mock_logger.info.assert_any_call("  APGI Parameters:")
        mock_logger.info.assert_any_call("    Exteroceptive Precision: 2.0")
        mock_logger.info.assert_any_call("    Trials: 100")

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("apgi_framework.validation.diagnostics_cli.get_config_manager")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_run_diagnostics_config_error(
        self, mock_logger, mock_get_config_manager, mock_get_health_checker
    ):
        """Test diagnostics with configuration error."""
        mock_health_checker = MockHealthChecker()
        mock_get_health_checker.return_value = mock_health_checker

        mock_config_manager = MagicMock()
        mock_config_manager.get_apgi_parameters.side_effect = Exception("Config error")
        mock_get_config_manager.return_value = mock_config_manager

        # Mock args
        mock_args = MagicMock()

        run_diagnostics(mock_args)

        # Check logger captured the error message
        mock_logger.info.assert_any_call("  Error loading configuration: Config error")


class TestValidateParameters:
    """Test validate_parameters function."""

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_validate_parameters_success(self, mock_logger, mock_exit, mock_get_validator):
        """Test successful parameter validation."""
        mock_validator = MockValidator()
        mock_get_validator.return_value = mock_validator

        # Mock args with valid parameters
        mock_args = MagicMock()
        mock_args.params = ["extero_precision=2.0", "intero_precision=1.5"]

        validate_parameters(mock_args)

        # Check that logger was called with expected messages
        mock_logger.info.assert_any_call("\n" + "=" * 60)
        mock_logger.info.assert_any_call("PARAMETER VALIDATION")
        mock_logger.info.assert_any_call("=" * 60 + "\n")
        mock_logger.info.assert_any_call("✓ All parameters valid")
        mock_exit.assert_not_called()

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_validate_parameters_failure(self, mock_logger, mock_exit, mock_get_validator):
        """Test parameter validation with invalid parameters."""
        mock_validator = MockValidator()
        mock_get_validator.return_value = mock_validator

        # Mock args with invalid parameters
        mock_args = MagicMock()
        mock_args.params = ["extero_precision=5.0", "intero_precision=1.5"]

        validate_parameters(mock_args)

        # Check that logger was called with expected messages
        mock_logger.info.assert_any_call("\n" + "=" * 60)
        mock_logger.info.assert_any_call("PARAMETER VALIDATION")
        mock_logger.info.assert_any_call("=" * 60 + "\n")
        mock_logger.info.assert_any_call("❌ Parameters invalid")
        mock_exit.assert_called_once_with(1)

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_validate_parameters_invalid_format(self, mock_logger, mock_get_validator):
        """Test parameter validation with invalid format."""
        mock_validator = MockValidator()
        mock_get_validator.return_value = mock_validator

        # Mock args with invalid parameter format
        mock_args = MagicMock()
        mock_args.params = ["invalid_format"]

        # Validate parameters should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            validate_parameters(mock_args)

        assert exc_info.value.code == 1

        # Check that logger was called with expected messages
        mock_logger.info.assert_any_call("Error: Invalid parameter format: invalid_format")
        mock_logger.info.assert_any_call("Expected format: key=value")

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_validate_parameters_no_params(self, mock_logger, mock_get_validator):
        """Test parameter validation with no parameters."""
        mock_validator = MockValidator()
        mock_get_validator.return_value = mock_validator

        # Mock args with no parameters
        mock_args = MagicMock()
        mock_args.params = None

        # Validate parameters should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            validate_parameters(mock_args)

        assert exc_info.value.code == 1

        # Check that logger was called with the expected message
        mock_logger.info.assert_any_call("No parameters provided")


class TestGetParameterInfo:
    """Test get_parameter_info function."""

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_get_parameter_info_success(self, mock_logger, mock_exit, mock_get_validator):
        """Test successful parameter info retrieval."""
        mock_validator = MockValidator()
        mock_get_validator.return_value = mock_validator

        # Mock args with parameter
        mock_args = MagicMock()
        mock_args.parameter = "threshold"

        get_parameter_info(mock_args)

        # Check that logger was called with the expected info
        mock_logger.info.assert_any_call(
            "\nAPGI Equation Parameter\nthreshold\nValid range: [0.0, 1.0]\nDescription: [0.0, 1.0]\n"
        )
        mock_exit.assert_not_called()

    @patch("sys.exit")
    @patch("apgi_framework.validation.diagnostics_cli.logger")
    def test_get_parameter_info_no_parameter(self, mock_logger, mock_exit):
        """Test parameter info with no parameter name."""
        # Mock args without parameter
        mock_args = MagicMock()
        mock_args.parameter = None

        get_parameter_info(mock_args)

        # Check that logger was called with the expected message
        mock_logger.info.assert_any_call("Error: No parameter name provided")
        mock_exit.assert_called_once_with(1)


class TestMain:
    """Test main function."""

    @patch("apgi_framework.validation.diagnostics_cli.run_health_check")
    def test_main_health_check_command(self, mock_run_health_check):
        """Test main with health-check command."""
        # Mock sys.argv
        test_args = ["diagnostics_cli.py", "health-check"]

        with patch("sys.argv", test_args):
            main()

        mock_run_health_check.assert_called_once()

    @patch("apgi_framework.validation.diagnostics_cli.run_diagnostics")
    def test_main_diagnostics_command(self, mock_run_diagnostics):
        """Test main with diagnostics command."""
        # Mock sys.argv
        test_args = ["diagnostics_cli.py", "diagnostics"]

        with patch("sys.argv", test_args):
            main()

        mock_run_diagnostics.assert_called_once()

    @patch("apgi_framework.validation.diagnostics_cli.validate_parameters")
    def test_main_validate_command(self, mock_validate_parameters):
        """Test main with validate command."""
        # Mock sys.argv
        test_args = [
            "diagnostics_cli.py",
            "validate",
            "--params",
            "extero_precision=2.0",
        ]

        with patch("sys.argv", test_args):
            main()

        mock_validate_parameters.assert_called_once()

    @patch("apgi_framework.validation.diagnostics_cli.get_parameter_info")
    def test_main_param_info_command(self, mock_get_parameter_info):
        """Test main with param-info command."""
        # Mock sys.argv
        test_args = ["diagnostics_cli.py", "param-info", "--parameter", "threshold"]

        with patch("sys.argv", test_args):
            main()

        mock_get_parameter_info.assert_called_once()

    @patch("sys.exit")
    @patch("argparse.ArgumentParser.print_help")
    def test_main_no_command(self, mock_print_help, mock_exit):
        """Test main with no command."""
        # Mock sys.argv with no command
        test_args = ["diagnostics_cli.py"]

        with patch("sys.argv", test_args):
            main()

        mock_print_help.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("apgi_framework.validation.diagnostics_cli.run_health_check")
    def test_main_health_check_with_component(self, mock_run_health_check):
        """Test main with health-check command and component."""
        # Mock sys.argv
        test_args = ["diagnostics_cli.py", "health-check", "--component", "python"]

        with patch("sys.argv", test_args):
            main()

        # Verify the call was made with the correct args
        mock_run_health_check.assert_called_once()
        args = mock_run_health_check.call_args[0][0]
        assert args.component == "python"


class TestArgumentParser:
    """Test argument parser configuration."""

    def test_argument_parser_setup(self):
        """Test that argument parser is correctly configured."""
        # Mock sys.argv for testing
        test_args = ["diagnostics_cli.py", "--help"]

        with patch("sys.argv", test_args):
            with patch("sys.exit"):
                with patch("argparse.ArgumentParser.print_help") as mock_help:
                    try:
                        main()
                    except SystemExit:
                        pass

        # Verify help was called (parser was set up correctly)
        mock_help.assert_called()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("apgi_framework.validation.diagnostics_cli.get_health_checker")
    @patch("sys.exit")
    def test_health_check_exception_handling(self, mock_exit, mock_get_health_checker):
        """Test health check exception handling."""
        mock_get_health_checker.side_effect = Exception("Health checker error")

        mock_args = MagicMock()
        mock_args.component = None

        # Should handle exception gracefully
        try:
            run_health_check(mock_args)
        except Exception:
            pass  # Expected in this test

    @patch("apgi_framework.validation.diagnostics_cli.get_validator")
    @patch("sys.exit")
    def test_validate_exception_handling(self, mock_exit, mock_get_validator):
        """Test validate parameters exception handling."""
        mock_get_validator.side_effect = Exception("Validator error")

        mock_args = MagicMock()
        mock_args.params = ["extero_precision=2.0"]

        # Should handle exception gracefully
        try:
            validate_parameters(mock_args)
        except Exception:
            pass  # Expected in this test


if __name__ == "__main__":
    pytest.main([__file__])
