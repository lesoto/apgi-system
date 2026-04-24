"""
Command-Line Interface for APGI Framework Testing System.

This module provides a comprehensive CLI for running individual tests,
batch experiment execution, and configuration management.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from apgi_framework.logging.standardized_logging import get_logger
from apgi_framework.main_controller import MainApplicationController
from apgi_framework.testing.batch_runner import BatchTestRunner
from apgi_framework.testing.persistence import TestResultPersistence, store_test_results

logger = get_logger(__name__)


def validate_trials_range(value: str) -> int:
    """Validate trials argument is within documented range (100-10000)."""
    try:
        ivalue = int(value)
        if not 100 <= ivalue <= 10000:
            raise argparse.ArgumentTypeError(
                f"Number of trials must be between 100 and 10000, got {ivalue}"
            )
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value for trials: {value}")


def validate_participants_range(value: str) -> int:
    """Validate participants argument is within documented range (10-1000)."""
    try:
        ivalue = int(value)
        if not 10 <= ivalue <= 1000:
            raise argparse.ArgumentTypeError(
                f"Number of participants must be between 10 and 1000, got {ivalue}"
            )
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value for participants: {value}")


def validate_threshold_range(value: str) -> float:
    """Validate threshold argument is within documented range (0.5-10.0)."""
    try:
        fvalue = float(value)
        if not 0.5 <= fvalue <= 10.0:
            raise argparse.ArgumentTypeError(
                f"Threshold must be between 0.5 and 10.0, got {fvalue}"
            )
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value for threshold: {value}")


def validate_positive_int(value: str) -> int:
    """Validate positive integer argument."""
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"Value must be a positive integer, got {ivalue}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")


def validate_workers_range(value: str) -> int:
    """Validate max-workers argument is within reasonable range (1-64)."""
    try:
        ivalue = int(value)
        if not 1 <= ivalue <= 64:
            raise argparse.ArgumentTypeError(f"Max workers must be between 1 and 64, got {ivalue}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value for max-workers: {value}")


def validate_timeout_range(value: str) -> int:
    """Validate timeout argument is within reasonable range (1-3600 seconds)."""
    try:
        ivalue = int(value)
        if not 1 <= ivalue <= 3600:
            raise argparse.ArgumentTypeError(
                f"Timeout must be between 1 and 3600 seconds, got {ivalue}"
            )
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value for timeout: {value}")


def validate_days_range(value: str) -> int:
    """Validate days argument is within reasonable range (1-365)."""
    try:
        ivalue = int(value)
        if not 1 <= ivalue <= 365:
            raise argparse.ArgumentTypeError(f"Days must be between 1 and 365, got {ivalue}")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value for days: {value}")


def validate_coverage_threshold_range(value: str) -> float:
    """Validate coverage threshold argument is within range (0-100)."""
    try:
        fvalue = float(value)
        if not 0 <= fvalue <= 100:
            raise argparse.ArgumentTypeError(
                f"Coverage threshold must be between 0 and 100, got {fvalue}"
            )
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value for coverage threshold: {value}")


def validate_precision_range(value: str) -> float:
    """Validate precision argument is within reasonable range (0.001-1000)."""
    try:
        fvalue = float(value)
        if not 0.001 <= fvalue <= 1000:
            raise argparse.ArgumentTypeError(
                f"Precision must be between 0.001 and 1000, got {fvalue}"
            )
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value for precision: {value}")


def validate_steepness_range(value: str) -> float:
    """Validate steepness argument is within reasonable range (0.1-50.0)."""
    try:
        fvalue = float(value)
        if not 0.1 <= fvalue <= 50.0:
            raise argparse.ArgumentTypeError(
                f"Steepness must be between 0.1 and 50.0, got {fvalue}"
            )
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value for steepness: {value}")


def validate_gain_range(value: str) -> float:
    """Validate gain argument is within reasonable range (-10.0 to 10.0)."""
    try:
        fvalue = float(value)
        if not -10.0 <= fvalue <= 10.0:
            raise argparse.ArgumentTypeError(f"Gain must be between -10.0 and 10.0, got {fvalue}")
        return fvalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid float value for gain: {value}")


class APGIFrameworkCLI:
    """Command-line interface for the APGI Framework Testing System."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.controller: Optional[MainApplicationController] = None
        self.logger: Optional[Any] = None

    def setup_logging(self, log_level: str = "INFO") -> None:
        """Setup logging for CLI operations."""
        try:
            from apgi_framework.logging.centralized_logging import APGILogManager
        except ImportError:
            # Fallback to standardized logging if centralized logging is not available
            from apgi_framework.logging.standardized_logging import get_logger

            self.logger = get_logger(__name__)
            return

        APGILogManager.setup_logging(level=log_level)
        self.logger = logging.getLogger(__name__)

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="APGI Framework Testing System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run primary falsification test
  python -m apgi_framework.cli run-test primary --trials 1000
  
  # Run all tests in batch mode
  python -m apgi_framework.cli run-batch --config config.json
  
  # Generate default configuration
  python -m apgi_framework.cli generate-config --output config.json
  
  # Validate system components
  python -m apgi_framework.cli validate-system
            """,
        )

        # Global options
        parser.add_argument(
            "--config",
            "-c",
            type=str,
            help="Path to JSON configuration file with APGI parameters",
        )

        parser.add_argument(
            "--log-level",
            "-l",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            help="Set logging level (default: INFO)",
        )

        parser.add_argument(
            "--output-dir",
            "-o",
            type=str,
            help="Output directory for results and reports",
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Run individual test command
        test_parser = subparsers.add_parser("run-test", help="Run individual test")
        test_parser.add_argument(
            "test_type",
            choices=[
                "primary",
                "consciousness-without-ignition",
                "threshold-insensitivity",
                "soma-bias",
            ],
            help="Type of test to run",
        )
        test_parser.add_argument(
            "--trials",
            "-n",
            type=validate_trials_range,
            default=1000,
            help="Number of trials to run (range: 100-10000, default: 1000)",
        )
        test_parser.add_argument(
            "--participants",
            "-p",
            type=validate_participants_range,
            default=100,
            help="Number of participants to simulate (range: 10-1000, default: 100)",
        )
        test_parser.add_argument(
            "--seed",
            type=validate_positive_int,
            help="Random seed for reproducible results",
        )
        test_parser.add_argument("--config", "-c", type=str, help="Path to configuration file")

        batch_parser = subparsers.add_parser("run-batch", help="Run batch experiments")
        batch_parser.add_argument("--all-tests", action="store_true", help="Run all tests")
        batch_parser.add_argument(
            "--tests",
            nargs="+",
            choices=[
                "primary",
                "consciousness-without-ignition",
                "threshold-insensitivity",
                "soma-bias",
            ],
            help="Specific tests to run in batch",
        )
        batch_parser.add_argument(
            "--parallel",
            action="store_true",
            help="Run tests in parallel (experimental)",
        )

        batch_test_parser = subparsers.add_parser(
            "batch-test", help="Advanced batch test execution"
        )
        batch_test_parser.add_argument(
            "--test-paths",
            nargs="+",
            help="Specific test file paths to run (e.g., tests/test_core.py)",
        )
        batch_test_parser.add_argument(
            "--markers",
            nargs="+",
            choices=[
                "unit",
                "integration",
                "research",
                "core",
                "slow",
                "neural",
                "behavioral",
            ],
            help="Run tests with specific markers",
        )
        batch_test_parser.add_argument(
            "--keywords",
            type=str,
            help="Run tests matching keyword patterns in test names",
        )
        batch_test_parser.add_argument(
            "--parallel",
            action="store_true",
            default=True,
            help="Run tests in parallel (default: True)",
        )
        batch_test_parser.add_argument(
            "--sequential", action="store_true", help="Run tests sequentially"
        )
        batch_test_parser.add_argument(
            "--max-workers",
            type=validate_workers_range,
            help="Maximum number of parallel workers (range: 1-64)",
        )
        batch_test_parser.add_argument(
            "--timeout",
            type=validate_timeout_range,
            default=600,
            help="Timeout per test in seconds (range: 1-3600, default: 600)",
        )
        batch_test_parser.add_argument(
            "--failfast", action="store_true", help="Stop on first failure"
        )
        batch_test_parser.add_argument("--report", type=str, help="Output path for HTML report")

        result_parser = subparsers.add_parser("test-results", help="Manage test results")
        result_parser.add_argument("--list", action="store_true", help="List recent test results")
        result_parser.add_argument(
            "--show",
            type=str,
            help="Display detailed results from specific test result file",
        )
        result_parser.add_argument(
            "--rerun-failed",
            type=str,
            help="Re-run only failed tests from specified result file",
        )
        result_parser.add_argument(
            "--clean",
            action="store_true",
            help="Remove old test result files and temporary data",
        )

        # Test analysis and reporting commands
        analysis_parser = subparsers.add_parser(
            "test-analysis", help="Analyze test results and performance"
        )
        analysis_parser.add_argument(
            "--performance-report",
            action="store_true",
            help="Generate performance report",
        )
        analysis_parser.add_argument(
            "--days",
            type=validate_days_range,
            default=30,
            help="Number of days to analyze (range: 1-365, default: 30)",
        )
        analysis_parser.add_argument(
            "--trends", action="store_true", help="Show performance trends"
        )
        analysis_parser.add_argument(
            "--failures", action="store_true", help="Analyze failure patterns"
        )
        analysis_parser.add_argument("--test-name", type=str, help="Analyze specific test")
        analysis_parser.add_argument("--export", type=str, help="Export results to file")
        analysis_parser.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            help="Export format (default: json)",
        )

        # Test generation and coverage commands
        coverage_parser = subparsers.add_parser(
            "test-coverage", help="Analyze and generate test coverage"
        )
        coverage_parser.add_argument(
            "--analyze", action="store_true", help="Analyze test coverage gaps"
        )
        coverage_parser.add_argument(
            "--generate", action="store_true", help="Generate missing tests"
        )
        coverage_parser.add_argument(
            "--report", action="store_true", help="Generate coverage report"
        )
        coverage_parser.add_argument(
            "--output-dir",
            type=str,
            default="generated_tests",
            help="Output directory for generated tests (default: generated_tests)",
        )
        coverage_parser.add_argument(
            "--report-file",
            type=str,
            default="coverage_report.md",
            help="Output file for coverage report (default: coverage_report.md)",
        )
        coverage_parser.add_argument(
            "--root-path",
            type=str,
            help="Root path to analyze (default: current directory)",
        )
        coverage_parser.add_argument(
            "--threshold",
            type=validate_coverage_threshold_range,
            default=90.0,
            help="Coverage threshold percentage (range: 0-100, default: 90.0)",
        )
        coverage_parser.add_argument(
            "--format",
            choices=["html", "xml", "json", "text"],
            default="html",
            help="Coverage report format (default: html)",
        )
        coverage_parser.add_argument(
            "--include-patterns",
            nargs="+",
            help="File patterns to include in coverage analysis",
        )
        coverage_parser.add_argument(
            "--exclude-patterns",
            nargs="+",
            help="File patterns to exclude from coverage analysis",
        )

        # Enhanced test execution commands with GUI feature parity
        test_exec_parser = subparsers.add_parser(
            "run-tests", help="Enhanced test execution with GUI feature parity"
        )
        test_exec_parser.add_argument("--test-paths", nargs="+", help="Specific test paths to run")
        test_exec_parser.add_argument(
            "--categories",
            nargs="+",
            choices=["unit", "integration", "property", "gui", "performance"],
            help="Test categories to run",
        )
        test_exec_parser.add_argument(
            "--modules",
            nargs="+",
            help="Specific modules to test (e.g., core, clinical, neural)",
        )
        test_exec_parser.add_argument("--tags", nargs="+", help="Test tags to filter by")
        test_exec_parser.add_argument("--filter", type=str, help="Test name filter pattern")
        test_exec_parser.add_argument(
            "--parallel",
            action="store_true",
            default=True,
            help="Run tests in parallel (default: True)",
        )
        test_exec_parser.add_argument(
            "--sequential", action="store_true", help="Run tests sequentially"
        )
        test_exec_parser.add_argument(
            "--max-workers",
            type=validate_workers_range,
            help="Maximum number of parallel workers (range: 1-64)",
        )
        test_exec_parser.add_argument(
            "--timeout",
            type=validate_timeout_range,
            default=600,
            help="Timeout per test in seconds (range: 1-3600, default: 600)",
        )
        test_exec_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        test_exec_parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
        test_exec_parser.add_argument(
            "--progress",
            choices=["bar", "dots", "none"],
            default="bar",
            help="Progress display style (default: bar)",
        )
        test_exec_parser.add_argument(
            "--coverage",
            action="store_true",
            help="Collect coverage during test execution",
        )
        test_exec_parser.add_argument(
            "--coverage-report",
            choices=["html", "xml", "json", "text", "none"],
            default="html",
            help="Coverage report format (default: html)",
        )
        test_exec_parser.add_argument(
            "--save-results",
            action="store_true",
            default=True,
            help="Save test results to database (default: True)",
        )
        test_exec_parser.add_argument(
            "--output-format",
            choices=["json", "xml", "html", "text"],
            default="text",
            help="Output format for results (default: text)",
        )
        test_exec_parser.add_argument("--output-file", type=str, help="Output file for results")

        # Test organization and filtering commands
        organize_parser = subparsers.add_parser(
            "organize-tests", help="Organize and categorize tests"
        )
        organize_parser.add_argument("--discover", action="store_true", help="Discover all tests")
        organize_parser.add_argument(
            "--categorize", action="store_true", help="Categorize discovered tests"
        )
        organize_parser.add_argument(
            "--list-categories", action="store_true", help="List test categories"
        )
        organize_parser.add_argument(
            "--list-modules", action="store_true", help="List test modules"
        )
        organize_parser.add_argument(
            "--list-tags", action="store_true", help="List available test tags"
        )
        organize_parser.add_argument(
            "--export-tree",
            type=str,
            help="Export test tree to file (JSON format)",
        )
        organize_parser.add_argument(
            "--root-path",
            type=str,
            help="Root path for test discovery (default: current directory)",
        )

        # Configuration management commands
        config_parser = subparsers.add_parser("generate-config", help="Generate configuration file")
        config_parser.add_argument(
            "--output",
            type=str,
            default="apgi_config.json",
            help="Output path for configuration file (default: apgi_config.json)",
        )
        config_parser.add_argument(
            "--template",
            choices=["default", "minimal", "comprehensive"],
            default="default",
            help="Configuration template to use (default: default)",
        )

        # System validation command
        validate_parser = subparsers.add_parser(
            "validate-system", help="Validate system components"
        )
        validate_parser.add_argument(
            "--detailed", action="store_true", help="Show detailed validation results"
        )

        # Status command
        subparsers.add_parser("status", help="Show system status")

        # Parameter override commands
        param_parser = subparsers.add_parser("set-params", help="Set APGI parameters")
        param_parser.add_argument(
            "--extero-precision",
            type=validate_precision_range,
            help="Exteroceptive precision (range: 0.001-1000)",
        )
        param_parser.add_argument(
            "--intero-precision",
            type=validate_precision_range,
            help="Interoceptive precision (range: 0.001-1000)",
        )
        param_parser.add_argument(
            "--threshold",
            type=validate_threshold_range,
            help="Ignition threshold (range: 0.5-10.0)",
        )
        param_parser.add_argument(
            "--steepness",
            type=validate_steepness_range,
            help="Sigmoid steepness (range: 0.1-50.0)",
        )
        param_parser.add_argument(
            "--somatic-gain",
            type=validate_gain_range,
            help="Somatic marker gain (range: -10.0 to 10.0)",
        )

        return parser

    def initialize_controller(self, config_path: Optional[str] = None) -> None:
        """Initialize the main application controller."""
        # Ensure logger is available
        if self.logger is None:
            self.setup_logging()

        assert self.logger is not None  # for mypy
        try:
            self.controller = MainApplicationController(config_path)
            self.controller.initialize_system()
            self.logger.info("System initialized successfully")
        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Failed to initialize system: {e}")
            sys.exit(1)

    def run_individual_test(self, args: argparse.Namespace) -> None:
        """Run an individual falsification test."""
        assert self.logger is not None  # for mypy
        self.logger.info(f"Running {args.test_type} test with {args.trials} trials")

        try:
            # Initialize controller with config if provided
            if hasattr(args, "config") and args.config:
                self.initialize_controller(args.config)
            elif not self.controller:
                self.initialize_controller(None)
            # Update configuration if parameters provided
            assert self.controller is not None  # for mypy
            if args.trials:
                self.controller.config_manager.update_experimental_config(n_trials=args.trials)
            if args.participants:
                self.controller.config_manager.update_experimental_config(
                    n_participants=args.participants
                )
            if args.seed:
                self.controller.config_manager.update_experimental_config(random_seed=args.seed)

            # Get falsification tests
            tests = self.controller.get_falsification_tests()

            # Run the specified test
            if args.test_type == "primary":
                result = tests["primary"].run_falsification_test(n_trials=args.trials)
            elif args.test_type == "consciousness-without-ignition":
                result = tests[
                    "consciousness_without_ignition"
                ].run_consciousness_without_ignition_test(n_trials=args.trials)
            elif args.test_type == "threshold-insensitivity":
                result = tests["threshold_insensitivity"].run_threshold_insensitivity_test()
            elif args.test_type == "soma-bias":
                result = tests["soma_bias"].run_soma_bias_test(n_participants=args.participants)

            # Display results
            self._display_test_result(result, args.test_type)

            # Save results
            self._save_test_result(result, args.test_type)

        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"Test execution failed: {e}")
            sys.exit(1)

    def run_batch_experiments(self, args: argparse.Namespace) -> None:
        """Run batch experiments."""
        assert self.logger is not None  # for mypy
        assert self.controller is not None  # for mypy
        self.logger.info("Running batch experiments")

        try:
            # Determine which tests to run
            if args.all_tests:
                test_types = [
                    "primary",
                    "consciousness-without-ignition",
                    "threshold-insensitivity",
                    "soma-bias",
                ]
            elif args.tests:
                test_types = args.tests
            else:
                self.logger.error("Must specify either --all-tests or --tests")
                self.logger.error("Example: run-batch --all-tests")
                self.logger.error(
                    "Example: run-batch --tests primary,consciousness-without-ignition"
                )
                sys.exit(2)

            results = {}
            tests = self.controller.get_falsification_tests()

            for test_type in test_types:
                self.logger.info(f"Running {test_type} test...")

                try:
                    if test_type == "primary":
                        result = tests["primary"].run_test()
                    elif test_type == "consciousness-without-ignition":
                        result = tests["consciousness_without_ignition"].run_test()
                    elif test_type == "threshold-insensitivity":
                        result = tests["threshold_insensitivity"].run_test()
                    elif test_type == "soma-bias":
                        result = tests["soma_bias"].run_test()

                    results[test_type] = result
                    self.logger.info(f"Completed {test_type} test")

                except (RuntimeError, ValueError, KeyError) as e:
                    self.logger.error(f"Failed to run {test_type} test: {e}")
                    results[test_type] = {"error": str(e)}

            # Display batch results
            self._display_batch_results(results)

            # Save batch results
            self._save_batch_results(results)

        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Batch execution failed: {e}")
            sys.exit(1)

    def generate_configuration(self, args: argparse.Namespace) -> None:
        """Generate a configuration file."""
        assert self.logger is not None  # for mypy
        self.logger.info(f"Generating {args.template} configuration file: {args.output}")

        try:
            if args.template == "minimal":
                config_data = self._create_minimal_config()
            elif args.template == "comprehensive":
                config_data = self._create_comprehensive_config()
            else:  # default
                config_data = self._create_default_config()

            # Create output directory if needed
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(args.output, "w") as f:
                json.dump(config_data, f, indent=2)

            self.logger.info(f"Configuration saved to {args.output}")

        except (IOError, OSError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to generate configuration: {e}")
            sys.exit(1)

    def validate_system(self, args: argparse.Namespace) -> None:
        """Validate system components."""
        assert self.logger is not None  # for mypy
        assert self.controller is not None  # for mypy
        self.logger.info("Validating system components...")

        try:
            validation_results = self.controller.run_system_validation()

            if args.detailed:
                self._display_detailed_validation(validation_results)
            else:
                self._display_simple_validation(validation_results)

            if not validation_results.get("overall", False):
                sys.exit(1)

        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"System validation failed: {e}")
            sys.exit(1)

    def show_status(self, args: argparse.Namespace) -> None:
        """Show system status."""
        assert self.logger is not None  # for mypy
        assert self.controller is not None  # for mypy
        try:
            status = self.controller.get_system_status()
            self._display_system_status(status)
        except (RuntimeError, AttributeError) as e:
            self.logger.error(f"Failed to get system status: {e}")
            sys.exit(1)

    def set_parameters(self, args: argparse.Namespace) -> None:
        """Set APGI parameters."""
        assert self.logger is not None  # for mypy
        assert self.controller is not None  # for mypy
        try:
            updates = {}
            if args.extero_precision is not None:
                updates["extero_precision"] = args.extero_precision
            if args.intero_precision is not None:
                updates["intero_precision"] = args.intero_precision
            if args.threshold is not None:
                updates["threshold"] = args.threshold
            if args.steepness is not None:
                updates["steepness"] = args.steepness
            if args.somatic_gain is not None:
                updates["somatic_gain"] = args.somatic_gain

            if updates:
                self.controller.config_manager.update_apgi_parameters(**updates)
                self.logger.info(f"Updated parameters: {updates}")
            else:
                self.logger.warning("No parameters specified to update")

        except (RuntimeError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to set parameters: {e}")
            sys.exit(1)

    def run_advanced_batch_tests(self, args: argparse.Namespace) -> None:
        """Run advanced batch tests using the new batch test runner."""
        assert self.logger is not None  # for mypy
        self.logger.info("Running advanced batch tests")

        try:
            # Initialize batch runner
            batch_runner = BatchTestRunner(
                self.controller.config_manager if self.controller else None
            )

            # Set progress callback
            def progress_callback(progress: float, result: Any) -> None:
                assert self.logger is not None  # for mypy
                self.logger.info(f"Progress: {progress:.1%} - {result.test_name}: {result.status}")

            batch_runner.set_progress_callback(progress_callback)  # type: ignore[no-untyped-call]

            # Determine execution mode
            parallel = args.parallel and not args.sequential

            # Run batch tests
            summary = batch_runner.run_batch_tests(
                test_selection=args.test_paths,
                markers=args.markers,
                keywords=args.keywords,
                parallel=parallel,
                max_workers=args.max_workers,
                timeout=args.timeout,
                failfast=args.failfast,
            )

            # Store results in persistence database
            try:
                batch_id = store_test_results(summary)
                self.logger.info(f"Test results stored in database with batch_id: {batch_id}")
            except (RuntimeError, IOError, ValueError) as e:
                self.logger.warning(f"Failed to store results in database: {e}")

            # Display results
            self._display_batch_test_summary(summary)

            # Generate report if requested
            if args.report:
                report_path = batch_runner.generate_report(summary, args.report)
                self.logger.info(f"Test report generated: {report_path}")

            # Save results for potential re-run
            self._save_batch_test_summary(summary)

        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Advanced batch test execution failed: {e}")
            sys.exit(1)

    def manage_test_results(self, args: argparse.Namespace) -> None:
        """Manage test results."""
        assert self.logger is not None  # for mypy
        try:
            if args.list:
                self._list_test_results()
            elif args.show:
                self._show_test_result(args.show)
            elif args.rerun_failed:
                self._rerun_failed_tests(args.rerun_failed)
            elif args.clean:
                self._clean_test_results()
            else:
                self.logger.error("Must specify one of: --list, --show, --rerun-failed, --clean")
                self.logger.error("Example: manage-results --list")
                self.logger.error("Example: manage-results --show session_123")
                sys.exit(2)

        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Test results management failed: {e}")
            sys.exit(1)

    def analyze_test_results(self, args: argparse.Namespace) -> None:
        """Analyze test results and generate reports."""
        assert self.logger is not None  # for mypy
        try:
            persistence = TestResultPersistence()

            if args.performance_report:
                self.logger.info(f"Generating performance report for last {args.days} days")
                report = persistence.generate_performance_report(args.days)
                logger.info(report)

                # Save report to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"performance_report_{timestamp}.md"
                with open(report_file, "w") as f:
                    f.write(report)
                logger.info(f"\nReport saved to: {report_file}")

            elif args.trends:
                self.logger.info(f"Showing performance trends for last {args.days} days")
                trends = persistence.get_performance_trends(args.test_name)

                if not trends:
                    logger.info("No performance trend data found")
                    return

                logger.info(f"\nPerformance Trends (Last {args.days} days):")
                logger.info(f"{'=' * 80}")
                for trend in trends:
                    logger.info(f"\nTest: {trend['test_name']}")
                    logger.info(f"  Success Rate: {trend['success_rate']:.1%}")
                    logger.info(f"  Avg Duration: {trend['avg_duration']:.3f}s")
                    logger.info(
                        f"  Min/Max Duration: {trend['min_duration']:.3f}s / {trend['max_duration']:.3f}s"
                    )
                    logger.info(f"  Total Executions: {trend['total_executions']}")
                    logger.info(f"  Last Execution: {trend['last_execution']}")

            elif args.failures:
                self.logger.info(f"Analyzing failure patterns for last {args.days} days")
                patterns = persistence.analyze_failure_patterns(args.days)

                if not patterns:
                    logger.info("No failure pattern data found")
                    return

                logger.info(f"\nFailure Pattern Analysis (Last {args.days} days):")
                logger.info(f"{'=' * 80}")

                if patterns.get("failed_tests"):
                    logger.info("\nMost Frequently Failing Tests:")
                    for test in patterns["failed_tests"][:10]:
                        logger.info(f"  - {test['test_name']}: {test['failure_count']} failures")
                        if test["error_patterns"]:
                            logger.info(f"    Common errors: {test['error_patterns'][:150]}...")

                if patterns.get("common_errors"):
                    logger.info("\nMost Common Error Messages:")
                    for error in patterns["common_errors"][:5]:
                        logger.info(f"  - {error['count']} occurrences: {error['error_sample']}")

            elif args.export:
                self.logger.info(f"Exporting test results to {args.export}")
                persistence.export_results(args.export, args.format, args.days)
                logger.info(f"Results exported to: {args.export}")

            else:
                self.logger.error(
                    "Must specify one of: --performance-report, --trends, --failures, --export"
                )
                self.logger.error("Example: analyze-results --performance-report")
                self.logger.error("Example: analyze-results --export results.json")
                sys.exit(2)

        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Test analysis failed: {e}")
            sys.exit(1)

    def run_enhanced_tests(self, args: argparse.Namespace) -> None:
        """Run enhanced test execution with GUI feature parity."""
        assert self.logger is not None  # for mypy
        self.logger.info("Running enhanced test execution")

        try:
            from .testing.persistence import store_test_results
            from .utils.framework_test_utils import TestUtilities

            # Initialize test utilities
            test_utils = TestUtilities(args.root_path if hasattr(args, "root_path") else None)

            # Discover tests based on criteria
            from typing import List

            from apgi_framework.utils.framework_test_utils import FrameworkTestSuite

            test_suites: List[FrameworkTestSuite] = []

            if args.test_paths:
                # Run specific test paths
                for path in args.test_paths:
                    discovered = test_utils.discover_tests(Path(path))
                    # discover_tests always returns a list, extend directly
                    test_suites.extend(discovered)
            else:
                # Discover tests by categories, modules, or tags
                all_suites = test_utils.discover_all_tests()

                for suite in all_suites:
                    include_suite = True

                    # Filter by categories
                    if args.categories:
                        suite_categories = {tc.category.value for tc in suite.test_cases}
                        if not any(cat in suite_categories for cat in args.categories):
                            include_suite = False

                    # Filter by modules
                    if args.modules and include_suite:
                        suite_module = self._extract_module_from_suite(suite)
                        if suite_module not in args.modules:
                            include_suite = False

                    # Filter by tags
                    if args.tags and include_suite:
                        suite_tags = set()
                        for tc in suite.test_cases:
                            suite_tags.update(tc.tags)
                        if not any(tag in suite_tags for tag in args.tags):
                            include_suite = False

                    # Filter by name pattern
                    if args.filter and include_suite:
                        if not any(
                            args.filter.lower() in tc.name.lower() for tc in suite.test_cases
                        ):
                            include_suite = False

                    if include_suite:
                        test_suites.append(suite)

            if not test_suites:
                self.logger.warning("No tests found matching the specified criteria")
                return

            # Configure execution
            config = {
                "parallel": args.parallel and not args.sequential,
                "max_workers": args.max_workers,
                "timeout": args.timeout,
                "verbose": args.verbose,
                "quiet": args.quiet,
                "collect_coverage": args.coverage,
                "coverage_report_format": (args.coverage_report if args.coverage else None),
            }

            # Execute tests
            execution = test_utils.execute_tests(test_suites, config)

            # Display results based on output format
            if args.output_format == "json":
                self._display_results_json(execution)
            elif args.output_format == "xml":
                self._display_results_xml(execution)
            elif args.output_format == "html":
                self._display_results_html(execution)
            else:
                self._display_results_text(execution, args.verbose, args.progress)

            # Save results if requested
            if args.save_results:
                try:
                    batch_id = store_test_results(execution)
                    self.logger.info(f"Test results stored with batch_id: {batch_id}")
                except (RuntimeError, IOError, ValueError) as e:
                    self.logger.warning(f"Failed to store results: {e}")

            # Save to output file if specified
            if args.output_file:
                self._save_results_to_file(execution, args.output_file, args.output_format)

            # Generate coverage report if requested
            if args.coverage and hasattr(execution, "coverage_data"):
                self._generate_coverage_report(execution.coverage_data, args.coverage_report)

        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"Enhanced test execution failed: {e}")
            sys.exit(1)

    def organize_tests(self, args: argparse.Namespace) -> None:
        """Organize and categorize tests with GUI feature parity."""
        assert self.logger is not None  # for mypy
        try:
            from .utils.framework_test_utils import TestUtilities

            test_utils = TestUtilities(args.root_path)

            if args.discover:
                self.logger.info("Discovering all tests...")
                test_suites = test_utils.discover_all_tests()

                logger.info(f"\nDiscovered {len(test_suites)} test suites:")
                logger.info(f"{'=' * 60}")

                total_tests = 0
                for suite in test_suites:
                    total_tests += len(suite.test_cases)
                    logger.info(f"Suite: {suite.name}")
                    logger.info(f"  Tests: {len(suite.test_cases)}")
                    logger.info(f"  Estimated Duration: {suite.total_estimated_duration:.2f}s")

                    if args.categorize:
                        categories: Dict[str, int] = {}
                        for tc in suite.test_cases:
                            cat = tc.category.value
                            categories[cat] = categories.get(cat, 0) + 1

                        logger.info(f"  Categories: {dict(categories)}")

                    logger.info("")

                logger.info(f"Total Tests: {total_tests}")
                logger.info(f"{'=' * 60}\n")

            elif args.list_categories:
                all_suites_for_list = test_utils.discover_all_tests()
                categories_set: Set[str] = set()
                category_counts: Dict[str, int] = {}

                for suite in all_suites_for_list:
                    for tc in suite.test_cases:
                        cat = tc.category.value
                        categories_set.add(cat)
                        category_counts[cat] = category_counts.get(cat, 0) + 1

                logger.info("\nAvailable Test Categories:")
                logger.info(f"{'=' * 40}")
                for category in sorted(categories_set):
                    logger.info(f"  {category}: {category_counts[category]} tests")
                logger.info(f"{'=' * 40}\n")

            elif args.list_modules:
                test_suites = test_utils.discover_all_tests()
                modules: Set[str] = set()
                module_counts: Dict[str, int] = {}

                for suite in test_suites:
                    module = self._extract_module_from_suite(suite)
                    modules.add(module)
                    module_counts[module] = module_counts.get(module, 0) + len(suite.test_cases)

                logger.info("\nAvailable Test Modules:")
                logger.info(f"{'=' * 40}")
                for module in sorted(modules):
                    logger.info(f"  {module}: {module_counts[module]} tests")
                logger.info(f"{'=' * 40}\n")

            elif args.list_tags:
                test_suites = test_utils.discover_all_tests()
                all_tags: Set[str] = set()
                tag_counts: Dict[str, int] = {}

                for suite in test_suites:
                    for tc in suite.test_cases:
                        for tag in tc.tags:
                            all_tags.add(tag)
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1

                logger.info("\nAvailable Test Tags:")
                logger.info(f"{'=' * 40}")
                for tag in sorted(all_tags):
                    logger.info(f"  {tag}: {tag_counts[tag]} tests")
                logger.info(f"{'=' * 40}\n")

            elif args.export_tree:
                test_suites = test_utils.discover_all_tests()
                tree_data = self._build_test_tree(test_suites)

                with open(args.export_tree, "w") as f:
                    json.dump(tree_data, f, indent=2, default=str)

                logger.info(f"Test tree exported to: {args.export_tree}")

            else:
                self.logger.error(
                    "Must specify one of: --discover, --list-categories, --list-modules, --list-tags, --export-tree"
                )
                sys.exit(2)

        except (RuntimeError, IOError, ValueError) as e:
            assert self.logger is not None  # for mypy
            self.logger.error(f"Test organization failed: {e}")
            sys.exit(1)

    def manage_enhanced_coverage(self, args: argparse.Namespace) -> None:
        """Enhanced coverage management with additional CLI options."""
        assert self.logger is not None  # for mypy
        try:
            from .testing.test_generator import SuiteGenerator

            generator = SuiteGenerator()  # type: ignore[no-untyped-call]

            if args.analyze:
                self.logger.info("Analyzing test coverage gaps with enhanced options")
                analysis = generator.analyze_codebase(
                    args.root_path,
                    include_patterns=args.include_patterns,
                    exclude_patterns=args.exclude_patterns,
                )

                # Display enhanced analysis
                metrics = analysis["metrics"]
                logger.info(f"\n{'=' * 70}")
                logger.info("Enhanced Test Coverage Analysis Results")
                logger.info(f"{'=' * 70}")
                logger.info(f"Total Modules: {metrics.total_modules}")
                logger.info(f"Tested Modules: {metrics.tested_modules}")
                logger.info(f"Total Functions/Methods: {metrics.total_functions}")
                logger.info(f"Tested Functions/Methods: {metrics.tested_functions}")
                logger.info(f"Coverage Percentage: {metrics.coverage_percentage:.1f}%")
                logger.info(f"Coverage Threshold: {args.threshold}%")
                logger.info(
                    f"Threshold Status: {'PASS' if metrics.coverage_percentage >= args.threshold else 'FAIL'}"
                )
                logger.info(f"Test Quality Score: {metrics.test_quality_score:.1f}/100")
                logger.info(f"Total Coverage Gaps: {len(analysis['coverage_gaps'])}")

                # Show detailed gap analysis
                gaps = analysis["coverage_gaps"]
                if gaps:
                    logger.info("\nCoverage Gap Details:")
                    logger.info(f"{'Module':<30} {'Function':<25} {'Priority':<10} {'Complexity'}")
                    logger.info(f"{'-' * 80}")

                    sorted_gaps = sorted(gaps, key=lambda g: g.complexity_score, reverse=True)
                    for gap in sorted_gaps[:20]:  # Show top 20
                        logger.info(
                            f"{gap.module_name:<30} {gap.function_name:<25} {gap.test_priority:<10} {gap.complexity_score}"
                        )

                logger.info(f"\n{'=' * 70}")

            elif args.generate:
                self.logger.info("Generating missing tests with enhanced options")
                analysis = generator.analyze_codebase(
                    args.root_path,
                    include_patterns=args.include_patterns,
                    exclude_patterns=args.exclude_patterns,
                )
                generated_files = generator.generate_missing_tests(analysis, args.output_dir)

                logger.info(f"\nGenerated {len(generated_files)} test files:")
                for module_name, file_path in generated_files.items():
                    logger.info(f"  - {module_name}: {file_path}")

            elif args.report:
                self.logger.info("Generating enhanced coverage report")
                analysis = generator.analyze_codebase(
                    args.root_path,
                    include_patterns=args.include_patterns,
                    exclude_patterns=args.exclude_patterns,
                )

                # Generate report in specified format
                if args.format == "html":
                    report_path = generator.generate_html_coverage_report(
                        analysis, args.report_file
                    )
                elif args.format == "xml":
                    report_path = generator.generate_xml_coverage_report(analysis, args.report_file)
                elif args.format == "json":
                    report_path = generator.generate_json_coverage_report(
                        analysis, args.report_file
                    )
                else:  # text
                    report_path = generator.generate_coverage_report(analysis, args.report_file)

                logger.info(f"Enhanced coverage report generated: {report_path}")

            else:
                self.logger.error("Must specify one of: --analyze, --generate, --report")
                sys.exit(2)

        except (RuntimeError, IOError, ValueError) as e:
            assert self.logger is not None  # for mypy
            self.logger.error(f"Enhanced coverage management failed: {e}")
            sys.exit(1)

    def manage_test_coverage(self, args: argparse.Namespace) -> None:
        """Manage test coverage analysis and generation."""
        assert self.logger is not None  # for mypy
        try:
            from .testing.test_generator import SuiteGenerator

            generator = SuiteGenerator()  # type: ignore[no-untyped-call]

            if args.analyze:
                self.logger.info("Analyzing test coverage gaps")
                analysis = generator.analyze_codebase(args.root_path)

                # Display summary
                metrics = analysis["metrics"]
                logger.info(f"\n{'=' * 60}")
                logger.info("Test Coverage Analysis Results")
                logger.info(f"{'=' * 60}")
                logger.info(f"Total Modules: {metrics.total_modules}")
                logger.info(f"Tested Modules: {metrics.tested_modules}")
                logger.info(f"Total Functions/Methods: {metrics.total_functions}")
                logger.info(f"Tested Functions/Methods: {metrics.tested_functions}")
                logger.info(f"Coverage Percentage: {metrics.coverage_percentage:.1f}%")
                logger.info(f"Test Quality Score: {metrics.test_quality_score:.1f}/100")
                logger.info(f"Total Coverage Gaps: {len(analysis['coverage_gaps'])}")

                # Show priority breakdown
                gaps = analysis["coverage_gaps"]
                high_priority = len([g for g in gaps if g.test_priority == "high"])
                medium_priority = len([g for g in gaps if g.test_priority == "medium"])
                low_priority = len([g for g in gaps if g.test_priority == "low"])

                logger.info("\nCoverage Gaps by Priority:")
                logger.info(f"  High Priority: {high_priority}")
                logger.info(f"  Medium Priority: {medium_priority}")
                logger.info(f"  Low Priority: {low_priority}")

                # Show top gaps
                if gaps:
                    logger.info("\nTop 10 Coverage Gaps:")
                    sorted_gaps = sorted(gaps, key=lambda g: g.complexity_score, reverse=True)
                    for i, gap in enumerate(sorted_gaps[:10], 1):
                        logger.info(
                            f"  {i:2d}. {gap.module_name}.{gap.function_name} "
                            f"(Complexity: {gap.complexity_score}, Priority: {gap.test_priority})"
                        )

                logger.info(f"\n{'=' * 60}")

            elif args.generate:
                self.logger.info(f"Generating missing tests to {args.output_dir}")
                analysis = generator.analyze_codebase(args.root_path)
                generated_files = generator.generate_missing_tests(analysis, args.output_dir)

                logger.info(f"\nGenerated {len(generated_files)} test files:")
                for module_name, file_path in generated_files.items():
                    logger.info(f"  - {module_name}: {file_path}")

                logger.info("\nTo run the generated tests:")
                logger.info(
                    f"  python -m apgi_framework.cli batch-test --test-paths {args.output_dir}/"
                )

            elif args.report:
                if self.logger:
                    self.logger.info(f"Generating coverage report: {args.report_file}")
                analysis = generator.analyze_codebase(args.root_path)
                report_path = generator.generate_coverage_report(analysis, args.report_file)
                logger.info(f"Coverage report generated: {report_path}")

            else:
                assert self.logger is not None  # for mypy
                self.logger.error("Must specify one of: --analyze, --generate, --report")
                sys.exit(2)

        except (RuntimeError, IOError, ValueError) as e:
            assert self.logger is not None  # for mypy
            self.logger.error(f"Test coverage management failed: {e}")
            sys.exit(1)

    def _display_batch_test_summary(self, summary: Any) -> None:
        """Display batch test execution summary."""
        assert self.logger is not None  # for mypy
        logger.info(f"\n{'=' * 80}")
        logger.info("APGI Framework Advanced Batch Test Results")
        logger.info(f"{'=' * 80}")

        logger.info(f"Total Tests: {summary.total_tests}")
        logger.info(f"Passed: {summary.passed}")
        logger.info(f"Failed: {summary.failed}")
        logger.info(f"Skipped: {summary.skipped}")
        logger.info(f"Errors: {summary.errors}")
        logger.info(f"Success Rate: {(summary.passed / summary.total_tests * 100):.1f}%")
        logger.info(f"Total Duration: {summary.total_duration:.2f} seconds")
        logger.info(f"Start Time: {summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End Time: {summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Show failed tests if any
        failed_tests = [r for r in summary.test_results if r.status in ["failed", "error"]]
        if failed_tests:
            logger.info(f"\nFailed Tests ({len(failed_tests)}):")
            for result in failed_tests[:10]:  # Show first 10
                logger.info(f"  - {result.test_name}: {result.error_message or 'No error message'}")
            if len(failed_tests) > 10:
                logger.info(f"  ... and {len(failed_tests) - 10} more")

        logger.info(f"\n{'=' * 80}\n")

    def _save_batch_test_summary(self, summary: Any) -> None:
        """Save batch test summary to file."""
        assert self.logger is not None  # for mypy
        try:
            output_dir = Path("test_results")
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"batch_test_summary_{timestamp}.json"

            # Convert summary to dictionary for JSON serialization
            summary_dict = {
                "total_tests": summary.total_tests,
                "passed": summary.passed,
                "failed": summary.failed,
                "skipped": summary.skipped,
                "errors": summary.errors,
                "total_duration": summary.total_duration,
                "start_time": (
                    summary.start_time.isoformat()
                    if hasattr(summary.start_time, "isoformat")
                    else str(summary.start_time)
                ),
                "end_time": (
                    summary.end_time.isoformat()
                    if hasattr(summary.end_time, "isoformat")
                    else str(summary.end_time)
                ),
                "test_results": [
                    {
                        "test_name": result.test_name,
                        "test_file": result.test_file,
                        "status": result.status,
                        "duration": result.duration,
                        "output": result.output,
                        "error_message": result.error_message,
                        "traceback": result.traceback,
                        "start_time": (
                            result.start_time.isoformat()
                            if result.start_time and hasattr(result.start_time, "isoformat")
                            else str(result.start_time)
                        ),
                        "end_time": (
                            result.end_time.isoformat()
                            if result.end_time and hasattr(result.end_time, "isoformat")
                            else str(result.end_time)
                        ),
                    }
                    for result in summary.test_results
                ],
                "execution_metadata": summary.execution_metadata,
            }

            with open(filename, "w") as f:
                json.dump(summary_dict, f, indent=2, default=str)

            if self.logger:
                self.logger.info(f"Batch test summary saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            if self.logger:
                self.logger.warning(f"Failed to save batch test summary: {e}")

    def _list_test_results(self) -> None:
        """List recent test result files."""
        results_dir = Path("test_results")
        if not results_dir.exists():
            logger.info("No test results directory found")
            return

        result_files = sorted(
            results_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True
        )

        if not result_files:
            logger.info("No test result files found")
            return

        logger.info("\nRecent Test Results:")
        logger.info(f"{'=' * 60}")
        for i, result_file in enumerate(result_files[:20], 1):  # Show last 20
            mtime = datetime.fromtimestamp(result_file.stat().st_mtime)
            size = result_file.stat().st_size
            logger.info(
                f"{i:2d}. {result_file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')}, {size} bytes)"
            )

    def _show_test_result(self, result_file: str) -> None:
        """Show details of a specific test result file."""
        assert self.logger is not None  # for mypy
        results_dir = Path("test_results")
        file_path = (
            results_dir / result_file if not Path(result_file).is_absolute() else Path(result_file)
        )

        if not file_path.exists():
            self.logger.error(f"Test result file not found: {file_path}")
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            logger.info(f"\nTest Result Details: {result_file}")
            logger.info(f"{'=' * 60}")

            if "summary" in data:
                summary = data["summary"]
                logger.info(f"Total Tests: {summary.get('total_tests', 'N/A')}")
                logger.info(f"Passed: {summary.get('passed', 'N/A')}")
                logger.info(f"Failed: {summary.get('failed', 'N/A')}")
                logger.info(f"Skipped: {summary.get('skipped', 'N/A')}")
                logger.info(f"Errors: {summary.get('errors', 'N/A')}")
                logger.info(f"Duration: {summary.get('total_duration', 'N/A')} seconds")
                logger.info(f"Start Time: {summary.get('start_time', 'N/A')}")
                logger.info(f"End Time: {summary.get('end_time', 'N/A')}")

            if "test_results" in data:
                logger.info("\nTest Results:")
                for result in data["test_results"][:10]:  # Show first 10
                    logger.info(
                        f"  - {result.get('test_name', 'Unknown')}: {result.get('status', 'Unknown')}"
                    )
                    if result.get("error_message"):
                        logger.info(f"    Error: {result['error_message'][:100]}...")

                if len(data["test_results"]) > 10:
                    logger.info(f"  ... and {len(data['test_results']) - 10} more tests")

            logger.info(f"\n{'=' * 60}\n")

        except (IOError, OSError, json.JSONDecodeError) as e:
            assert self.logger is not None  # for mypy
            self.logger.error(f"Failed to read test result file: {e}")

    def _rerun_failed_tests(self, result_file: str) -> None:
        """Re-run failed tests from a previous result file."""
        assert self.logger is not None  # for mypy
        try:
            self.logger.info(f"Re-running failed tests from {result_file}")

            summary = run_failed_tests(result_file, parallel=True)

            # Display results
            self._display_batch_test_summary(summary)

            # Save new results
            self._save_batch_test_summary(summary)

        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Failed to re-run failed tests: {e}")
            sys.exit(1)

    def _clean_test_results(self) -> None:
        """Clean old test result files."""
        assert self.logger is not None  # for mypy
        results_dir = Path("test_results")
        if not results_dir.exists():
            logger.info("No test results directory to clean")
            return

        # Remove files older than 7 days
        import time

        current_time = time.time()
        cutoff_time = current_time - (7 * 24 * 60 * 60)  # 7 days ago

        removed_count = 0
        for result_file in results_dir.glob("*.json"):
            if result_file.stat().st_mtime < cutoff_time:
                result_file.unlink()
                removed_count += 1

        logger.info(f"Cleaned {removed_count} old test result files")

    def _display_test_result(self, result: Any, test_type: str) -> None:
        """Display individual test result."""
        logger.info(f"\n{'=' * 60}")
        logger.info(f"APGI Framework Test Results: {test_type.upper()}")
        logger.info(f"{'=' * 60}")

        if hasattr(result, "is_falsified"):
            logger.info(
                f"Falsification Status: {'FALSIFIED' if result.is_falsified else 'NOT FALSIFIED'}"
            )
            logger.info(f"Confidence Level: {result.confidence_level:.3f}")
            logger.info(f"Effect Size: {result.effect_size:.3f}")
            logger.info(f"P-value: {result.p_value:.6f}")
            logger.info(f"Statistical Power: {result.statistical_power:.3f}")
        else:
            logger.info(f"Result: {result}")

        logger.info(f"{'=' * 60}\n")

    def _display_batch_results(self, results: Dict[str, Any]) -> None:
        """Display batch experiment results."""
        logger.info(f"\n{'=' * 80}")
        logger.info("APGI Framework Batch Falsification Test Results")
        logger.info(f"{'=' * 80}")

        for test_type, result in results.items():
            logger.info(f"\n{test_type.upper()}:")
            if "error" in result:
                logger.info(f"  ERROR: {result['error']}")
            elif hasattr(result, "is_falsified"):
                logger.info(f"  Falsified: {'YES' if result.is_falsified else 'NO'}")
                logger.info(f"  Confidence: {result.confidence_level:.3f}")
                logger.info(f"  Effect Size: {result.effect_size:.3f}")
                logger.info(f"  P-value: {result.p_value:.6f}")
            else:
                logger.info(f"  Result: {result}")

        logger.info(f"\n{'=' * 80}\n")

    def _display_detailed_validation(self, results: Dict[str, Any]) -> None:
        """Display detailed validation results."""
        logger.info(f"\n{'=' * 60}")
        logger.info("System Validation Results (Detailed)")
        logger.info(f"{'=' * 60}")

        for component, status in results.items():
            if component != "overall":
                status_str = "PASS" if status else "FAIL"
                logger.info(f"{component.replace('_', ' ').title()}: {status_str}")

        overall_status = "PASS" if results.get("overall", False) else "FAIL"
        logger.info(f"\nOverall Status: {overall_status}")
        logger.info(f"{'=' * 60}\n")

    def _display_simple_validation(self, results: Dict[str, Any]) -> None:
        """Display simple validation results."""
        overall_status = "PASS" if results.get("overall", False) else "FAIL"
        logger.info(f"System Validation: {overall_status}")

    def _display_system_status(self, status: Dict[str, Any]) -> None:
        """Display system status."""
        logger.info(f"\n{'=' * 50}")
        logger.info("APGI Framework System Status")
        logger.info(f"{'=' * 50}")

        for key, value in status.items():
            if key != "timestamp":
                display_key = key.replace("_", " ").title()
                display_value = "YES" if value else "NO" if isinstance(value, bool) else str(value)
                logger.info(f"{display_key}: {display_value}")

        logger.info(f"Last Updated: {status.get('timestamp', 'Unknown')}")
        logger.info(f"{'=' * 50}\n")

    def _save_test_result(self, result: Any, test_type: str) -> None:
        """Save individual test result to file."""
        try:
            if self.controller is None:
                logger.warning("Controller not initialized, skipping save")
                return
            output_dir = Path(
                self.controller.config_manager.get_experimental_config().output_directory
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"{test_type}_result_{timestamp}.json"

            # Convert result to dictionary for JSON serialization
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
            else:
                result_dict = {"result": str(result)}

            with open(filename, "w") as f:
                json.dump(result_dict, f, indent=2, default=str)

            if self.logger:
                self.logger.info(f"Results saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            if self.logger:
                self.logger.warning(f"Failed to save results: {e}")

    def _save_batch_results(self, results: Dict[str, Any]) -> None:
        """Save batch experiment results to file."""
        try:
            if self.controller is None:
                logger.warning("Controller not initialized, skipping save")
                return
            output_dir = Path(
                self.controller.config_manager.get_experimental_config().output_directory
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"batch_results_{timestamp}.json"

            # Convert results to dictionary for JSON serialization
            results_dict = {}
            for test_type, result in results.items():
                if hasattr(result, "__dict__"):
                    results_dict[test_type] = result.__dict__
                else:
                    results_dict[test_type] = {"result": str(result)}

            with open(filename, "w") as f:
                json.dump(results_dict, f, indent=2, default=str)

            if self.logger:
                self.logger.info(f"Batch results saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            if self.logger:
                self.logger.warning(f"Failed to save batch results: {e}")

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "apgi_parameters": {
                "extero_precision": 2.0,
                "intero_precision": 1.5,
                "extero_error": 1.2,
                "intero_error": 0.8,
                "somatic_gain": 1.3,
                "threshold": 3.5,
                "steepness": 2.0,
            },
            "experimental_config": {
                "n_trials": 1000,
                "n_participants": 100,
                "random_seed": None,
                "output_directory": "results",
                "log_level": "INFO",
                "save_intermediate": True,
                "p3b_threshold": 5.0,
                "gamma_plv_threshold": 0.3,
                "bold_z_threshold": 3.1,
                "pci_threshold": 0.4,
                "alpha_level": 0.05,
                "effect_size_threshold": 0.5,
                "power_threshold": 0.8,
            },
        }

    def _create_minimal_config(self) -> Dict[str, Any]:
        """Create minimal configuration."""
        return {
            "apgi_parameters": {"threshold": 3.5, "steepness": 2.0},
            "experimental_config": {"n_trials": 100, "output_directory": "results"},
        }

    def _extract_module_from_suite(self, suite: Any) -> str:
        """Extract module name from test suite."""
        from typing import cast

        # Extract module from suite name or file path
        if hasattr(suite, "name") and "." in suite.name:
            return cast(str, suite.name.split(".")[0])
        elif hasattr(suite, "test_cases") and suite.test_cases:
            # Extract from first test case file path
            file_path = suite.test_cases[0].file_path
            parts = str(file_path).split("/")
            for part in parts:
                if part in [
                    "core",
                    "clinical",
                    "neural",
                    "adaptive",
                    "gui",
                    "testing",
                    "analysis",
                ]:
                    return part
        return "unknown"

    def _display_results_text(
        self, execution: Any, verbose: bool = False, progress_style: str = "bar"
    ) -> None:
        """Display test results in text format."""
        logger.info(f"\n{'=' * 80}")
        logger.info("Test Execution Results")
        logger.info(f"{'=' * 80}")

        total_tests = len(execution.results)
        passed = len([r for r in execution.results if r.status.value == "passed"])
        failed = len([r for r in execution.results if r.status.value == "failed"])
        skipped = len([r for r in execution.results if r.status.value == "skipped"])
        errors = len([r for r in execution.results if r.status.value == "error"])

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Errors: {errors}")
        logger.info(
            f"Success Rate: {(passed / total_tests * 100):.1f}%" if total_tests > 0 else "N/A"
        )

        if execution.start_time and execution.end_time:
            duration = (execution.end_time - execution.start_time).total_seconds()
            logger.info(f"Total Duration: {duration:.2f} seconds")

        # Show failed tests
        failed_tests = [r for r in execution.results if r.status.value in ["failed", "error"]]
        if failed_tests and verbose:
            logger.info("\nFailed Tests:")
            logger.info(f"{'-' * 60}")
            for result in failed_tests:
                logger.info(
                    f"  {result.test_case.name}: {result.error_message or 'No error message'}"
                )
                if verbose and result.traceback:
                    logger.info(f"    Traceback: {result.traceback[:200]}...")

        logger.info(f"{'=' * 80}\n")

    def _display_results_json(self, execution: Any) -> None:
        """Display test results in JSON format."""
        results_data = {
            "execution_id": execution.execution_id,
            "start_time": (execution.start_time.isoformat() if execution.start_time else None),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "total_tests": len(execution.results),
            "passed": len([r for r in execution.results if r.status.value == "passed"]),
            "failed": len([r for r in execution.results if r.status.value == "failed"]),
            "skipped": len([r for r in execution.results if r.status.value == "skipped"]),
            "errors": len([r for r in execution.results if r.status.value == "error"]),
            "test_results": [
                {
                    "name": result.test_case.name,
                    "status": result.status.value,
                    "duration": result.duration,
                    "error_message": result.error_message,
                    "file_path": str(result.test_case.file_path),
                    "category": result.test_case.category.value,
                }
                for result in execution.results
            ],
        }
        logger.info(json.dumps(results_data, indent=2))

    def _display_results_xml(self, execution: Any) -> None:
        """Display test results in XML format."""
        # Simple XML output - in a real implementation, you'd use xml.etree.ElementTree
        logger.info('<?xml version="1.0" encoding="UTF-8"?>')
        logger.info("<testsuites>")

        for suite in execution.test_suites:
            suite_results = [
                r
                for r in execution.results
                if any(tc.name == r.test_case.name for tc in suite.test_cases)
            ]
            failures = len([r for r in suite_results if r.status.value == "failed"])
            errors = len([r for r in suite_results if r.status.value == "error"])

            logger.info(
                f'  <testsuite name="{suite.name}" tests="{len(suite_results)}" failures="{failures}" errors="{errors}">'
            )

            for result in suite_results:
                logger.info(
                    f'    <testcase name="{result.test_case.name}" time="{result.duration}">'
                )
                if result.status.value == "failed":
                    logger.info(f'      <failure message="{result.error_message or ""}">')
                    logger.info(f'        {result.traceback or ""}')
                    logger.info("      </failure>")
                elif result.status.value == "error":
                    logger.info(f'      <error message="{result.error_message or ""}">')
                    logger.info(f'        {result.traceback or ""}')
                    logger.info("      </error>")
                logger.info("    </testcase>")

            logger.info("  </testsuite>")

        logger.info("</testsuites>")

    def _display_results_html(self, execution: Any) -> None:
        """Display test results in HTML format."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Results - {execution.execution_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        .error {{ color: darkred; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Test Execution Results</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Execution ID: {execution.execution_id}</p>
        <p>Total Tests: {len(execution.results)}</p>
        <p class="passed">Passed: {len([r for r in execution.results if r.status.value == "passed"])}</p>
        <p class="failed">Failed: {len([r for r in execution.results if r.status.value == "failed"])}</p>
        <p class="skipped">Skipped: {len([r for r in execution.results if r.status.value == "skipped"])}</p>
        <p class="error">Errors: {len([r for r in execution.results if r.status.value == "error"])}</p>
    </div>
    
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Category</th>
            <th>Error Message</th>
        </tr>
"""
        for result in execution.results:
            status_class = result.status.value
            html_content += f"""
        <tr>
            <td>{result.test_case.name}</td>
            <td class="{status_class}">{result.status.value.upper()}</td>
            <td>{result.duration:.3f}s</td>
            <td>{result.test_case.category.value}</td>
            <td>{result.error_message or ""}</td>
        </tr>
"""

        html_content += """
    </table>
</body>
</html>
"""
        logger.info(html_content)

    def _save_results_to_file(self, execution: Any, output_file: str, format_type: str) -> None:
        """Save test results to specified file."""
        try:
            with open(output_file, "w") as f:
                if format_type == "json":
                    results_data = {
                        "execution_id": execution.execution_id,
                        "start_time": (
                            execution.start_time.isoformat() if execution.start_time else None
                        ),
                        "end_time": (
                            execution.end_time.isoformat() if execution.end_time else None
                        ),
                        "results": [
                            {
                                "name": result.test_case.name,
                                "status": result.status.value,
                                "duration": result.duration,
                                "error_message": result.error_message,
                            }
                            for result in execution.results
                        ],
                    }
                    json.dump(results_data, f, indent=2)
                elif format_type == "xml":
                    # Write XML content to file
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write("<testsuites>\n")
                    # ... XML content generation similar to _display_results_xml
                    f.write("</testsuites>\n")
                else:  # text or html
                    # Redirect stdout to file temporarily
                    import sys

                    original_stdout = sys.stdout
                    sys.stdout = f

                    if format_type == "html":
                        self._display_results_html(execution)
                    else:
                        self._display_results_text(execution, verbose=True)

                    sys.stdout = original_stdout

            if self.logger:
                self.logger.info(f"Results saved to {output_file}")

        except (IOError, OSError, ValueError) as e:
            if self.logger:
                self.logger.error(f"Failed to save results to file: {e}")

    def _generate_coverage_report(self, coverage_data: Any, report_format: str) -> None:
        """Generate coverage report in specified format."""
        try:
            if report_format == "html":
                # Generate HTML coverage report
                if self.logger:
                    self.logger.info("Generating HTML coverage report...")
                # Implementation would use coverage.py HTML reporter
            elif report_format == "xml":
                # Generate XML coverage report
                if self.logger:
                    self.logger.info("Generating XML coverage report...")
                # Implementation would use coverage.py XML reporter
            elif report_format == "json":
                # Generate JSON coverage report
                if self.logger:
                    self.logger.info("Generating JSON coverage report...")
                # Implementation would use coverage.py JSON reporter
            else:
                # Generate text coverage report
                if self.logger:
                    self.logger.info("Generating text coverage report...")
                # Implementation would use coverage.py text reporter

        except (IOError, OSError, ValueError) as e:
            if self.logger:
                self.logger.warning(f"Failed to generate coverage report: {e}")

    def _build_test_tree(self, test_suites: Any) -> Dict[str, Any]:
        """Build hierarchical test tree structure."""
        tree: Dict[str, Any] = {
            "name": "Test Tree",
            "type": "root",
            "children": [],
            "metadata": {
                "total_suites": len(test_suites),
                "total_tests": sum(len(suite.test_cases) for suite in test_suites),
                "generated_at": datetime.now().isoformat(),
            },
        }

        # Group by modules
        modules: Dict[str, List[Any]] = {}
        for suite in test_suites:
            module = self._extract_module_from_suite(suite)
            if module not in modules:
                modules[module] = []
            modules[module].append(suite)

        # Build tree structure
        for module_name, module_suites in modules.items():
            module_node: Dict[str, Any] = {
                "name": module_name,
                "type": "module",
                "children": [],
                "metadata": {
                    "suite_count": len(module_suites),
                    "test_count": sum(len(suite.test_cases) for suite in module_suites),
                },
            }

            for suite in module_suites:
                suite_node: Dict[str, Any] = {
                    "name": suite.name,
                    "type": "suite",
                    "children": [],
                    "metadata": {
                        "test_count": len(suite.test_cases),
                        "estimated_duration": suite.total_estimated_duration,
                    },
                }

                for test_case in suite.test_cases:
                    test_node = {
                        "name": test_case.name,
                        "type": "test",
                        "metadata": {
                            "category": test_case.category.value,
                            "file_path": str(test_case.file_path),
                            "line_number": test_case.line_number,
                            "estimated_duration": test_case.estimated_duration,
                            "tags": list(test_case.tags),
                        },
                    }
                    suite_node["children"].append(test_node)

                module_node["children"].append(suite_node)

            tree["children"].append(module_node)

        return tree

    def _create_comprehensive_config(self) -> Dict[str, Any]:
        """Create comprehensive configuration."""
        config = self._create_default_config()

        # Add additional comprehensive options
        config["experimental_config"].update(
            {
                "detailed_logging": True,
                "save_raw_data": True,
                "generate_plots": True,
                "statistical_corrections": ["fdr", "bonferroni"],
                "bootstrap_iterations": 10000,
                "confidence_interval": 0.95,
            }
        )

        return config

    def manage_test_coverage_legacy(self, args: argparse.Namespace) -> None:
        """Manage test coverage analysis and generation (legacy method for compatibility)."""
        # Redirect to enhanced coverage management
        self.manage_enhanced_coverage(args)

    def run(self, args: Optional[List[str]] = None) -> None:
        """Main entry point for the CLI."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        # Setup logging
        self.setup_logging(parsed_args.log_level)

        # Handle case where no command is provided
        if not parsed_args.command:
            parser.print_help()
            return

        # Initialize controller for commands that need it
        if parsed_args.command not in [
            "generate-config",
            "batch-test",
            "test-results",
            "test-analysis",
            "test-coverage",
            "run-test",  # run-test handles its own controller initialization
            "run-tests",  # Enhanced test execution
            "organize-tests",  # Test organization
        ]:
            self.initialize_controller(parsed_args.config)

        # Override output directory if provided
        if parsed_args.output_dir and self.controller:
            self.controller.config_manager.update_experimental_config(
                output_directory=parsed_args.output_dir
            )

        # Execute the requested command
        try:
            if parsed_args.command == "run-test":
                self.run_individual_test(parsed_args)
            elif parsed_args.command == "run-batch":
                self.run_batch_experiments(parsed_args)
            elif parsed_args.command == "batch-test":
                self.run_advanced_batch_tests(parsed_args)
            elif parsed_args.command == "run-tests":
                self.run_enhanced_tests(parsed_args)
            elif parsed_args.command == "organize-tests":
                self.organize_tests(parsed_args)
            elif parsed_args.command == "test-results":
                self.manage_test_results(parsed_args)
            elif parsed_args.command == "test-analysis":
                self.analyze_test_results(parsed_args)
            elif parsed_args.command == "test-coverage":
                self.manage_enhanced_coverage(parsed_args)
            elif parsed_args.command == "generate-config":
                self.generate_configuration(parsed_args)
            elif parsed_args.command == "validate-system":
                self.validate_system(parsed_args)
            elif parsed_args.command == "status":
                self.show_status(parsed_args)
            elif parsed_args.command == "set-params":
                self.set_parameters(parsed_args)
            else:
                if self.logger:
                    self.logger.error(f"Unknown command: {parsed_args.command}")
                sys.exit(2)

        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Operation cancelled by user")
            sys.exit(0)
        except (RuntimeError, IOError, ValueError) as e:
            if self.logger:
                self.logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected error: {e}")
            sys.exit(1)
        finally:
            # Cleanup
            if self.controller:
                try:
                    self.controller.shutdown_system()
                except (RuntimeError, AttributeError) as e:
                    if self.logger:
                        self.logger.warning(f"Error during cleanup: {e}")

        # If we reach here, command executed successfully
        sys.exit(0)


def run_failed_tests(result_file: str, parallel: bool = True) -> Any:
    """
    Re-run failed tests from a previous test result file.

    Args:
        result_file: Path to the JSON result file
        parallel: Whether to run tests in parallel

    Returns:
        Test execution summary
    """
    try:
        # Load the result file
        results_path = Path("test_results") / result_file
        if not results_path.exists():
            results_path = Path(result_file)

        if not results_path.exists():
            raise FileNotFoundError(f"Result file not found: {result_file}")

        with open(results_path, "r") as f:
            data = json.load(f)

        # Extract failed tests
        failed_tests = []
        if "test_results" in data:
            for result in data["test_results"]:
                if result.get("status") in ["failed", "error"]:
                    failed_tests.append(result.get("test_name"))

        if not failed_tests:
            logger.info("No failed tests found in result file")
            return None

        logger.info(f"Found {len(failed_tests)} failed tests to re-run")

        # Run the failed tests using pytest
        import subprocess
        import sys

        cmd = [sys.executable, "-m", "pytest"]
        cmd.extend(failed_tests)

        if parallel:
            cmd.extend(["-n", "auto"])  # Use pytest-xdist for parallel execution

        cmd.extend(
            [
                "--tb=short",
                "--verbose",
                "--json-report",
                "--json-report-file=re_run_results.json",
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse results
        results_file = Path("re_run_results.json")
        if results_file.exists():
            with open(results_file, "r") as f:
                summary_data = json.load(f)

            # Clean up
            results_file.unlink()

            return summary_data.get("summary", {})

        return {"error": "Failed to parse re-run results"}

    except (IOError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as e:
        logger.info(f"Error re-running failed tests: {e}")
        return {"error": str(e)}


def main() -> None:
    """Entry point for the CLI when run as a module."""
    cli = APGIFrameworkCLI()  # type: ignore[no-untyped-call]
    cli.run()


if __name__ == "__main__":
    main()
