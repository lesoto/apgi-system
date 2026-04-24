"""
Tests for CLI module coverage - focuses on actual execution paths.
"""

from unittest.mock import MagicMock, patch

import pytest

from apgi_framework.cli import APGIFrameworkCLI

print(
    f"DEBUG: APGIFrameworkCLI imported from {APGIFrameworkCLI.__module__} at {getattr(APGIFrameworkCLI, '__file__', 'unknown')}"
)


class TestCLIExecution:
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
                    args = MagicMock()
                    args.command = "run-test"
                    args.test_type = "primary"
                    args.trials = 100
                    args.participants = 20
                    args.seed = None
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_run.assert_called_once()
                    # run-test handles its own controller initialization, so initialize_controller is NOT called

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
                    args = MagicMock()
                    args.command = "run-batch"
                    args.all_tests = True
                    args.tests = None
                    args.parallel = False
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
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
                args = MagicMock()
                args.command = "generate-config"
                args.output = "test_config.json"
                args.template = "default"
                args.log_level = "INFO"  # Fix the mock
                args.config = None  # Add config mock
                mock_parser.return_value.parse_args.return_value = args

                # CLI run() calls sys.exit(0) which raises SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    cli.run()
                assert exc_info.value.code == 0
                mock_config.assert_called_once()
                # Note: initialize_controller is NOT called for generate-config command

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
                    args = MagicMock()
                    args.command = "validate-system"
                    args.detailed = False
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
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
                    args = MagicMock()
                    args.command = "status"
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
                    mock_parser.return_value.parse_args.return_value = args

                    # CLI run() calls sys.exit(0) which raises SystemExit
                    with pytest.raises(SystemExit) as exc_info:
                        cli.run()
                    assert exc_info.value.code == 0
                    mock_status.assert_called_once()
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
                    args = MagicMock()
                    args.command = "set-params"
                    args.threshold = 3.5
                    args.extero_precision = 2.0
                    args.intero_precision = 1.5
                    args.somatic_gain = 1.2
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
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
            args = MagicMock()
            args.command = "unknown-command"
            args.log_level = "INFO"  # Fix the mock
            args.config = None  # Add config mock
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
                    args = MagicMock()
                    args.command = "run-test"
                    args.test_type = "primary"
                    args.trials = 100
                    args.participants = 20
                    args.seed = None
                    args.log_level = "INFO"  # Fix the mock
                    args.config = None  # Add config mock
                    mock_parser.return_value.parse_args.return_value = args

                    with patch.object(cli.logger, "error") as mock_error:
                        with pytest.raises(SystemExit) as exc_info:
                            cli.run()
                        assert exc_info.value.code == 1
                        mock_error.assert_called_with("Unexpected error: Test error")


if __name__ == "__main__":
    pytest.main([__file__])
