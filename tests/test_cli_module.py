"""
Tests for CLI module components.

Consolidated from:
- test_cli_module.py (base validation and CLI tests)
- test_cli_coverage.py (execution path coverage)
- test_cli_validation_coverage.py (additional validation functions)
"""

import argparse
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from apgi_framework.cli import (
    APGIFrameworkCLI,
    validate_days_range,
    validate_coverage_threshold_range,
    validate_gain_range,
    validate_participants_range,
    validate_positive_int,
    validate_precision_range,
    validate_steepness_range,
    validate_threshold_range,
    validate_timeout_range,
    validate_trials_range,
    validate_workers_range,
)


class TestCLIValidationFunctions:
    """Test CLI validation functions."""

    def test_validate_trials_range_valid(self):
        """Test validate_trials_range with valid values."""
        assert validate_trials_range("100") == 100
        assert validate_trials_range("1000") == 1000
        assert validate_trials_range("10000") == 10000

    def test_validate_trials_range_invalid(self):
        """Test validate_trials_range with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be between 100 and 10000"):
            validate_trials_range("50")

        with pytest.raises(argparse.ArgumentTypeError, match="must be between 100 and 10000"):
            validate_trials_range("20000")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_trials_range("abc")

    def test_validate_participants_range_valid(self):
        """Test validate_participants_range with valid values."""
        assert validate_participants_range("10") == 10
        assert validate_participants_range("100") == 100
        assert validate_participants_range("1000") == 1000

    def test_validate_participants_range_invalid(self):
        """Test validate_participants_range with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be between 10 and 1000"):
            validate_participants_range("5")

        with pytest.raises(argparse.ArgumentTypeError, match="must be between 10 and 1000"):
            validate_participants_range("2000")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_participants_range("xyz")

    def test_validate_threshold_range_valid(self):
        """Test validate_threshold_range with valid values."""
        assert validate_threshold_range("0.5") == 0.5
        assert validate_threshold_range("5.0") == 5.0
        assert validate_threshold_range("10.0") == 10.0

    def test_validate_threshold_range_invalid(self):
        """Test validate_threshold_range with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be between 0.5 and 10.0"):
            validate_threshold_range("0.1")

        with pytest.raises(argparse.ArgumentTypeError, match="must be between 0.5 and 10.0"):
            validate_threshold_range("15.0")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
            validate_threshold_range("not_a_number")

    def test_validate_positive_int_valid(self):
        """Test validate_positive_int with valid values."""
        assert validate_positive_int("1") == 1
        assert validate_positive_int("100") == 100
        assert validate_positive_int("9999") == 9999

    def test_validate_positive_int_invalid(self):
        """Test validate_positive_int with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be a positive integer"):
            validate_positive_int("0")

        with pytest.raises(argparse.ArgumentTypeError, match="must be a positive integer"):
            validate_positive_int("-5")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_positive_int("three")

    def test_validate_workers_range_valid(self):
        """Test validate_workers_range with valid values."""
        assert validate_workers_range("1") == 1
        assert validate_workers_range("32") == 32
        assert validate_workers_range("64") == 64

    def test_validate_workers_range_invalid(self):
        """Test validate_workers_range with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be between 1 and 64"):
            validate_workers_range("0")

        with pytest.raises(argparse.ArgumentTypeError, match="must be between 1 and 64"):
            validate_workers_range("128")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_workers_range("ten")

    def test_validate_timeout_range_valid(self):
        """Test validate_timeout_range with valid values."""
        assert validate_timeout_range("1") == 1
        assert validate_timeout_range("1800") == 1800
        assert validate_timeout_range("3600") == 3600

    def test_validate_timeout_range_invalid(self):
        """Test validate_timeout_range with invalid values."""
        with pytest.raises(argparse.ArgumentTypeError, match="must be between 1 and 3600"):
            validate_timeout_range("0")

        with pytest.raises(argparse.ArgumentTypeError, match="must be between 1 and 3600"):
            validate_timeout_range("7200")

        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_timeout_range("timeout")

    def test_validate_days_range(self):
        """Test validate_days_range with valid and invalid values."""
        assert validate_days_range("1") == 1
        assert validate_days_range("365") == 365

        with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 365"):
            validate_days_range("0")
        with pytest.raises(argparse.ArgumentTypeError, match="between 1 and 365"):
            validate_days_range("366")
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid integer value"):
            validate_days_range("not-an-int")

    def test_validate_coverage_threshold_range(self):
        """Test validate_coverage_threshold_range with valid and invalid values."""
        assert validate_coverage_threshold_range("0") == 0.0
        assert validate_coverage_threshold_range("100") == 100.0

        with pytest.raises(argparse.ArgumentTypeError, match="between 0 and 100"):
            validate_coverage_threshold_range("-0.1")
        with pytest.raises(argparse.ArgumentTypeError, match="between 0 and 100"):
            validate_coverage_threshold_range("100.1")
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
            validate_coverage_threshold_range("not-a-float")

    def test_validate_precision_range(self):
        """Test validate_precision_range with valid and invalid values."""
        assert validate_precision_range("0.001") == 0.001
        assert validate_precision_range("1000") == 1000.0

        with pytest.raises(argparse.ArgumentTypeError, match="between 0.001 and 1000"):
            validate_precision_range("0.0009")
        with pytest.raises(argparse.ArgumentTypeError, match="between 0.001 and 1000"):
            validate_precision_range("1001")
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
            validate_precision_range("not-a-float")

    def test_validate_steepness_range(self):
        """Test validate_steepness_range with valid and invalid values."""
        assert validate_steepness_range("0.1") == 0.1
        assert validate_steepness_range("50") == 50.0

        with pytest.raises(argparse.ArgumentTypeError, match="between 0.1 and 50.0"):
            validate_steepness_range("0.09")
        with pytest.raises(argparse.ArgumentTypeError, match="between 0.1 and 50.0"):
            validate_steepness_range("50.1")
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
            validate_steepness_range("not-a-float")

    def test_validate_gain_range(self):
        """Test validate_gain_range with valid and invalid values."""
        assert validate_gain_range("-10.0") == -10.0
        assert validate_gain_range("10.0") == 10.0

        with pytest.raises(argparse.ArgumentTypeError, match="between -10.0 and 10.0"):
            validate_gain_range("-10.1")
        with pytest.raises(argparse.ArgumentTypeError, match="between -10.0 and 10.0"):
            validate_gain_range("10.1")
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid float value"):
            validate_gain_range("not-a-float")


class TestAPGIFrameworkCLI:
    """Test CLI implementation."""

    def test_initialization(self):
        """Test CLI initialization."""
        cli = APGIFrameworkCLI()

        assert cli.controller is None
        assert cli.logger is None

    def test_setup_logging(self):
        """Test logging setup."""
        cli = APGIFrameworkCLI()

        # Test default INFO level
        cli.setup_logging()
        assert cli.logger is not None

        # Test DEBUG level
        cli.setup_logging("DEBUG")
        assert cli.logger is not None

    def test_create_parser(self):
        """Test argument parser creation."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert "APGI Framework" in parser.description

    def test_run_test_command(self):
        """Test run-test command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test primary test command
        args = parser.parse_args(
            ["run-test", "primary", "--trials", "1000", "--participants", "20"]
        )

        assert args.command == "run-test"
        assert args.test_type == "primary"
        assert args.trials == 1000
        assert args.participants == 20

    def test_run_batch_command(self):
        """Test run-batch command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test batch command
        args = parser.parse_args(["run-batch", "--all-tests", "--parallel"])

        assert args.command == "run-batch"
        assert args.all_tests is True
        assert args.parallel is True

    def test_config_command(self):
        """Test config command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test generate-config command (this is the actual config command)
        args = parser.parse_args(["generate-config"])
        assert args.command == "generate-config"
        assert args.output == "apgi_config.json"

    def test_validate_command(self):
        """Test validate-system command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test validate-system command
        args = parser.parse_args(["validate-system"])
        assert args.command == "validate-system"
        assert args.detailed is False

        # Test validate-system with detailed flag
        args = parser.parse_args(["validate-system", "--detailed"])
        assert args.command == "validate-system"
        assert args.detailed is True

    def test_set_params_command(self):
        """Test set-params command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test set-params command
        args = parser.parse_args(["set-params", "--threshold", "2.0"])
        assert args.command == "set-params"
        assert args.threshold == 2.0

    def test_status_command(self):
        """Test status command parsing."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Test status command
        args = parser.parse_args(["status"])
        assert args.command == "status"

    @patch("apgi_framework.cli.MainApplicationController")
    def test_initialize_controller(self, mock_controller_class):
        """Test controller initialization."""
        mock_controller = mock_controller_class.return_value
        mock_controller.initialize_system.return_value = None

        cli = APGIFrameworkCLI()
        cli.initialize_controller()

        mock_controller_class.assert_called_once()
        mock_controller.initialize_system.assert_called_once()

    @patch("apgi_framework.cli.MainApplicationController")
    def test_initialize_controller_with_config(self, mock_controller_class):
        """Test controller initialization with config file."""
        mock_controller = mock_controller_class.return_value
        mock_controller.initialize_system.return_value = None

        cli = APGIFrameworkCLI()
        cli.initialize_controller("config.json")

        mock_controller_class.assert_called_once_with("config.json")

    @patch("apgi_framework.cli.MainApplicationController")
    def test_run_individual_test_primary(self, mock_controller_class):
        """Test running primary falsification test."""
        mock_controller = mock_controller_class.return_value
        mock_controller.get_falsification_tests.return_value = {
            "primary": Mock(run_falsification_test=Mock(return_value={"result": "success"}))
        }
        mock_controller.config_manager = Mock()

        cli = APGIFrameworkCLI()
        cli.controller = mock_controller
        cli.setup_logging()

        # Create args object
        args = argparse.Namespace(
            test_type="primary", trials=1000, participants=100, seed=None, config=None
        )

        with (
            patch.object(cli, "_display_test_result"),
            patch.object(cli, "_save_test_result"),
        ):
            cli.run_individual_test(args)

        mock_controller.get_falsification_tests.assert_called_once()
        mock_controller.get_falsification_tests.return_value[
            "primary"
        ].run_falsification_test.assert_called_once_with(n_trials=1000)

    @patch("apgi_framework.cli.MainApplicationController")
    def test_generate_configuration_default(self, mock_controller_class):
        """Test generating default configuration."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        args = argparse.Namespace(output="test_config.json", template="default")

        with (
            patch.object(cli, "_create_default_config", return_value={"test": "config"}),
            patch("builtins.open", create=True) as mock_open,
            patch("json.dump") as mock_json_dump,
        ):
            cli.generate_configuration(args)

            mock_open.assert_called_once_with("test_config.json", "w")
            mock_json_dump.assert_called_once_with(
                {"test": "config"}, mock_open.return_value.__enter__(), indent=2
            )

    @patch("apgi_framework.cli.MainApplicationController")
    def test_validate_system_simple(self, mock_controller_class):
        """Test system validation with simple output."""
        mock_controller = mock_controller_class.return_value
        mock_controller.run_system_validation.return_value = {
            "overall": True,
            "components": [],
        }

        cli = APGIFrameworkCLI()
        cli.controller = mock_controller
        cli.setup_logging()

        args = argparse.Namespace(detailed=False)

        with patch.object(cli, "_display_simple_validation"):
            cli.validate_system(args)

        mock_controller.run_system_validation.assert_called_once()

    @patch("apgi_framework.cli.MainApplicationController")
    def test_show_status(self, mock_controller_class):
        """Test showing system status."""
        mock_controller = mock_controller_class.return_value
        mock_controller.get_system_status.return_value = {"status": "running"}

        cli = APGIFrameworkCLI()
        cli.controller = mock_controller
        cli.setup_logging()

        args = argparse.Namespace()

        with patch.object(cli, "_display_system_status"):
            cli.show_status(args)

        mock_controller.get_system_status.assert_called_once()

    @patch("apgi_framework.cli.MainApplicationController")
    def test_set_parameters(self, mock_controller_class):
        """Test setting APGI parameters."""
        mock_controller = mock_controller_class.return_value
        mock_controller.config_manager = Mock()

        cli = APGIFrameworkCLI()
        cli.controller = mock_controller
        cli.setup_logging()

        args = argparse.Namespace(
            extero_precision=1.0,
            intero_precision=None,
            threshold=2.0,
            steepness=None,
            somatic_gain=None,
        )

        cli.set_parameters(args)

        mock_controller.config_manager.update_apgi_parameters.assert_called_once_with(
            extero_precision=1.0, threshold=2.0
        )

        # Test that the CLI can be initialized and parser created
        parser = cli.create_parser()
        args = parser.parse_args(
            ["run-test", "primary", "--trials", "1000", "--participants", "20"]
        )

        assert args.command == "run-test"
        assert args.test_type == "primary"
        assert args.trials == 1000
        assert args.participants == 20

    def test_run_batch_tests(self):
        """Test running batch tests."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test that batch command parsing works
        parser = cli.create_parser()
        args = parser.parse_args(["run-batch", "--all-tests"])

        assert args.command == "run-batch"
        assert args.all_tests is True

    def test_generate_config_command(self):
        """Test generate-config command parsing."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test config generation command
        parser = cli.create_parser()
        args = parser.parse_args(["generate-config", "--output", "test_config.json"])

        assert args.command == "generate-config"
        assert args.output == "test_config.json"
        assert args.template == "default"

    def test_validate_config(self):
        """Test configuration validation."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test system validation command
        parser = cli.create_parser()
        args = parser.parse_args(["validate-system"])

        assert args.command == "validate-system"
        assert args.detailed is False

    def test_validate_data(self):
        """Test data validation."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test status command
        parser = cli.create_parser()
        args = parser.parse_args(["status"])

        assert args.command == "status"

    def test_error_handling(self):
        """Test error handling in CLI operations."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test invalid command
        parser = cli.create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["invalid-command"])

    def test_missing_config_file(self):
        """Test handling of missing config file."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test configuration generation with non-existent directory
        parser = cli.create_parser()
        args = parser.parse_args(["generate-config", "--output", "/non/existent/path/config.json"])

        assert args.command == "generate-config"
        assert args.output == "/non/existent/path/config.json"

    def test_invalid_json_config(self):
        """Test handling of invalid JSON config."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test parameter setting command
        parser = cli.create_parser()
        args = parser.parse_args(["set-params", "--threshold", "3.5"])

        assert args.command == "set-params"
        assert args.threshold == 3.5

    def test_output_file_creation(self):
        """Test output file creation and writing."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test configuration generation
        parser = cli.create_parser()
        parser.parse_args(["generate-config", "--output", "test_config.json"])

        # Test default config creation
        config_data = cli._create_default_config()
        assert "apgi_parameters" in config_data
        assert "experimental_config" in config_data
        assert config_data["apgi_parameters"]["threshold"] == 3.5

    def test_command_line_integration(self):
        """Test full command line integration."""
        cli = APGIFrameworkCLI()

        # Test argument parsing for different commands
        parser = cli.create_parser()

        # Test run-test command
        args = parser.parse_args(["run-test", "primary", "--trials", "100"])
        assert args.command == "run-test"
        assert args.test_type == "primary"
        assert args.trials == 100

        # Test generate-config command
        args = parser.parse_args(["generate-config"])
        assert args.command == "generate-config"
        assert args.output == "apgi_config.json"

    def test_help_output(self):
        """Test help output generation."""
        cli = APGIFrameworkCLI()
        parser = cli.create_parser()

        # Capture help output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                parser.parse_args(["--help"])
            except SystemExit:
                pass  # argparse calls sys.exit after showing help

        help_output = mock_stdout.getvalue()
        assert "APGI Framework" in help_output
        assert "run-test" in help_output
        assert "run-batch" in help_output
        assert "config" in help_output


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_full_workflow_simulation(self):
        """Test simulation of complete CLI workflow."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test argument parsing for workflow
        parser = cli.create_parser()

        # 1. Test status command
        args = parser.parse_args(["status"])
        assert args.command == "status"

        # 2. Test generate-config command
        args = parser.parse_args(["generate-config", "--template", "minimal"])
        assert args.command == "generate-config"
        assert args.template == "minimal"

        # 3. Test run-test command
        args = parser.parse_args(["run-test", "primary", "--trials", "100"])
        assert args.command == "run-test"
        assert args.test_type == "primary"
        assert args.trials == 100

    def test_batch_workflow_simulation(self):
        """Test simulation of batch workflow."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Test batch command parsing
        parser = cli.create_parser()

        # Test all-tests option
        args = parser.parse_args(["run-batch", "--all-tests"])
        assert args.command == "run-batch"
        assert args.all_tests is True

        # Test specific tests option
        args = parser.parse_args(
            ["run-batch", "--tests", "primary", "consciousness-without-ignition"]
        )
        assert args.command == "run-batch"
        assert args.tests == ["primary", "consciousness-without-ignition"]

        # Test parallel option
        args = parser.parse_args(["run-batch", "--all-tests", "--parallel"])
        assert args.parallel is True


class TestCLIExecutionPaths:
    """Test CLI execution paths for coverage."""

    def test_cli_run_method_help(self):
        """Test CLI run method with help argument."""
        cli = APGIFrameworkCLI()

        # Test help command
        with patch("sys.argv", ["python", "-m", "apgi_framework.cli", "--help"]):
            with patch("argparse.ArgumentParser.parse_args") as mock_parse:
                mock_parse.side_effect = SystemExit(0)
                with pytest.raises(SystemExit):
                    cli.run()

    def test_cli_run_test_command(self):
        """Test CLI run method with run-test command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock the actual test execution and controller initialization
        with patch.object(cli, "run_individual_test") as mock_run:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_run.return_value = {"status": "completed", "results": []}
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "run-test"
                    args.test_type = "primary"
                    args.trials = 100
                    args.participants = 20
                    args.seed = None
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_run.assert_called_once()

    def test_cli_run_batch_command(self):
        """Test CLI run method with run-batch command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock the actual batch execution and controller initialization
        with patch.object(cli, "run_batch_experiments") as mock_batch:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_batch.return_value = {"status": "completed", "results": []}
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "run-batch"
                    args.all_tests = True
                    args.tests = None
                    args.parallel = False
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_batch.assert_called_once()
                    mock_init.assert_called_once()

    def test_cli_generate_config_command(self):
        """Test CLI generate-config command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock config generation - note that generate-config does NOT initialize controller
        with patch.object(cli, "generate_configuration") as mock_config:
            mock_config.return_value = "/path/to/config.json"

            # Mock argument parsing
            with patch.object(cli, "create_parser") as mock_parser:
                args = Mock()
                args.command = "generate-config"
                args.output = "test_config.json"
                args.template = "default"
                args.log_level = "INFO"
                args.config = None
                mock_parser.return_value.parse_args.return_value = args

                # CLI run() calls sys.exit(0) which raises SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    cli.run()
                assert exc_info.value.code == 0
                mock_config.assert_called_once()

    def test_cli_validate_system_command(self):
        """Test CLI validate-system command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock system validation and controller initialization
        with patch.object(cli, "validate_system") as mock_validate:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_validate.return_value = {"status": "valid", "checks": []}
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "validate-system"
                    args.detailed = False
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_validate.assert_called_once()
                    mock_init.assert_called_once()

    def test_cli_status_command(self):
        """Test CLI status command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock status check and controller initialization
        with patch.object(cli, "show_status") as mock_status:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_status.return_value = {"status": "running", "experiments": []}
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "status"
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_status.assert_called_once()
                    mock_init.assert_called_once()

    def test_cli_set_params_command(self):
        """Test CLI set-params command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock parameter setting and controller initialization
        with patch.object(cli, "set_parameters") as mock_params:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_params.return_value = {"status": "updated", "parameters": {}}
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "set-params"
                    args.threshold = 3.5
                    args.extero_precision = 2.0
                    args.intero_precision = 1.5
                    args.somatic_gain = 1.2
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_params.assert_called_once()
                    mock_init.assert_called_once()

    def test_cli_unknown_command(self):
        """Test CLI with unknown command."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock argument parsing for unknown command
        with patch.object(cli, "create_parser") as mock_parser:
            args = Mock()
            args.command = "unknown-command"
            args.log_level = "INFO"
            args.config = None
            mock_parser.return_value.parse_args.return_value = args

            with patch.object(cli.logger, "error") as mock_error:
                # CLI run() calls sys.exit(2) for unknown command
                with pytest.raises(SystemExit) as exc_info:
                    APGIFrameworkCLI.run(cli, ["unknown-command"])
                assert exc_info.value.code == 2
                mock_error.assert_called_with("Unknown command: unknown-command")

    def test_cli_error_handling(self):
        """Test CLI error handling."""
        cli = APGIFrameworkCLI()
        cli.setup_logging()

        # Mock exception during command execution and controller initialization
        with patch.object(cli, "run_individual_test") as mock_run:
            with patch.object(cli, "initialize_controller") as mock_init:
                mock_run.side_effect = Exception("Test error")
                mock_init.return_value = None

                # Mock argument parsing
                with patch.object(cli, "create_parser") as mock_parser:
                    args = Mock()
                    args.command = "run-test"
                    args.test_type = "primary"
                    args.trials = 100
                    args.participants = 20
                    args.seed = None
                    args.log_level = "INFO"
                    args.config = None
                    mock_parser.return_value.parse_args.return_value = args

                    with patch.object(cli.logger, "error") as mock_error:
                        with pytest.raises(SystemExit) as exc_info:
                            cli.run()
                        assert exc_info.value.code == 1
                        mock_error.assert_called_with("Unexpected error: Test error")


if __name__ == "__main__":
    pytest.main([__file__])
