import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from apgi_framework.commands.base import BaseCommand
from apgi_framework.testing.batch_runner import BatchTestRunner
from apgi_framework.testing.persistence import store_test_results


class RunTestCommand(BaseCommand):
    """Handles running individual falsification tests."""

    def execute(self, args: argparse.Namespace) -> None:
        if not self.controller:
            self.logger.error("Controller not initialized")
            return

        self.logger.info(f"Running {args.test_type} test with {args.trials} trials")

        try:
            # Update configuration if parameters provided
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
            else:
                self.logger.error(f"Unknown test type: {args.test_type}")
                return

            # Display results
            self._display_test_result(result, args.test_type)

            # Save results
            self._save_test_result(result, args.test_type)

        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"Test execution failed: {e}")
            sys.exit(1)


class RunBatchCommand(BaseCommand):
    """Handles running batch experiments."""

    def execute(self, args: argparse.Namespace) -> None:
        if not self.controller:
            self.logger.error("Controller not initialized")
            return

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

    def _display_batch_results(self, results: Dict[str, Any]) -> None:
        """Display batch experiment results."""
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("APGI Framework Batch Falsification Test Results")
        self.logger.info(f"{'=' * 80}")

        for test_type, result in results.items():
            self.logger.info(f"\n{test_type.upper()}:")
            if "error" in result:
                self.logger.info(f"  ERROR: {result['error']}")
            elif hasattr(result, "is_falsified"):
                self.logger.info(f"  Falsified: {'YES' if result.is_falsified else 'NO'}")
                self.logger.info(f"  Confidence: {result.confidence_level:.3f}")
                self.logger.info(f"  Effect Size: {result.effect_size:.3f}")
                self.logger.info(f"  P-value: {result.p_value:.6f}")
            else:
                self.logger.info(f"  Result: {result}")

        self.logger.info(f"\n{'=' * 80}\n")

    def _save_batch_results(self, results: Dict[str, Any]) -> None:
        """Save batch experiment results to file."""
        try:
            if self.controller is None:
                self.logger.warning("Controller not initialized, skipping save")
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

            self.logger.info(f"Batch results saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to save batch results: {e}")


class BatchTestCommand(BaseCommand):
    """Handles advanced batch test execution."""

    def execute(self, args: argparse.Namespace) -> None:
        self.logger.info("Running advanced batch tests")

        try:
            # Initialize batch runner
            batch_runner = BatchTestRunner(
                self.controller.config_manager if self.controller else None
            )

            # Set progress callback
            def progress_callback(progress: float, result: Any) -> None:
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

    def _display_batch_test_summary(self, summary: Any) -> None:
        """Display batch test execution summary."""
        self.logger.info(f"\n{'=' * 80}")
        self.logger.info("APGI Framework Advanced Batch Test Results")
        self.logger.info(f"{'=' * 80}")

        self.logger.info(f"Total Tests: {summary.total_tests}")
        self.logger.info(f"Passed: {summary.passed}")
        self.logger.info(f"Failed: {summary.failed}")
        self.logger.info(f"Skipped: {summary.skipped}")
        self.logger.info(f"Errors: {summary.errors}")
        self.logger.info(f"Success Rate: {(summary.passed / summary.total_tests * 100):.1f}%")
        self.logger.info(f"Total Duration: {summary.total_duration:.2f} seconds")
        self.logger.info(f"Start Time: {summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"End Time: {summary.end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Show failed tests if any
        failed_tests = [r for r in summary.test_results if r.status in ["failed", "error"]]
        if failed_tests:
            self.logger.info(f"\nFailed Tests ({len(failed_tests)}):")
            for result in failed_tests[:10]:  # Show first 10
                self.logger.info(
                    f"  - {result.test_name}: {result.error_message or 'No error message'}"
                )
            if len(failed_tests) > 10:
                self.logger.info(f"  ... and {len(failed_tests) - 10} more")

        self.logger.info(f"\n{'=' * 80}\n")

    def _save_batch_test_summary(self, summary: Any) -> None:
        """Save batch test summary to file."""
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

            self.logger.info(f"Batch test summary saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to save batch test summary: {e}")


class RunEnhancedTestsCommand(BaseCommand):
    """Handles enhanced test execution with GUI feature parity."""

    def execute(self, args: argparse.Namespace) -> None:
        self.logger.info("Running enhanced test execution")

        try:
            from apgi_framework.utils.framework_test_utils import TestUtilities

            # Initialize test utilities
            test_utils = TestUtilities(args.root_path if hasattr(args, "root_path") else None)

            # Discover tests based on criteria
            from apgi_framework.utils.framework_test_utils import FrameworkTestSuite

            test_suites: List[FrameworkTestSuite] = []

            if args.test_paths:
                # Run specific test paths
                for path in args.test_paths:
                    discovered = test_utils.discover_tests(Path(path))
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

        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"Enhanced test execution failed: {e}")
            sys.exit(1)

    def _extract_module_from_suite(self, suite: Any) -> str:
        if hasattr(suite, "name") and "." in suite.name:
            return str(suite.name.split(".")[0])
        return "unknown"

    def _display_results_text(self, execution: Any, verbose: bool, progress: str) -> None:
        # Simplified version for now
        self.logger.info("Enhanced Test Results (Text)")

    def _display_results_json(self, execution: Any) -> None:
        pass

    def _display_results_xml(self, execution: Any) -> None:
        pass

    def _display_results_html(self, execution: Any) -> None:
        pass

    def _save_results_to_file(self, execution: Any, output_file: str, format_type: str) -> None:
        pass


class OrganizeTestsCommand(BaseCommand):
    """Handles test organization and categorization."""

    def execute(self, args: argparse.Namespace) -> None:
        try:
            from apgi_framework.utils.framework_test_utils import TestUtilities

            test_utils = TestUtilities(args.root_path)

            if args.discover:
                self.logger.info("Discovering all tests...")
                test_suites = test_utils.discover_all_tests()
                self.logger.info(f"Discovered {len(test_suites)} test suites")
            elif args.list_categories:
                # ... implementation ...
                pass
            # ... other organize subcommands ...
        except (RuntimeError, IOError, ValueError) as e:
            self.logger.error(f"Test organization failed: {e}")
            sys.exit(1)
