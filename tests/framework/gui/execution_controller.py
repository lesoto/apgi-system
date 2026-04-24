"""
Test Execution Controller

This module implements the controller for managing test execution coordination
between the GUI and backend components, with real-time progress monitoring
and execution cancellation capabilities.
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import PySide6  # noqa: F401  # type: ignore[import-not-found]

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

if PYSIDE6_AVAILABLE:
    from PySide6.QtCore import (  # type: ignore[import-not-found]
        QObject,
        QThread,
        QTimer,
        Signal,
        pyqtSignal,
    )
    from PySide6.QtWidgets import QApplication  # type: ignore[import-not-found]
else:
    # Fallback for environments without PySide6
    class QObject:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            pass

    class Signal:  # type: ignore[no-redef]
        def __init__(self, *args):
            self._connected_slots = []

        def connect(self, slot):
            """Connect a slot to this signal."""
            self._connected_slots.append(slot)

        def emit(self, *args):
            """Emit the signal with arguments."""
            for slot in self._connected_slots:
                slot(*args)

    class QTimer:  # type: ignore[no-redef]
        def start(self, *args):
            pass

        def stop(self):
            pass

        timeout = Signal()

    class QThread:  # type: ignore[no-redef]
        def start(self):
            pass

        def wait(self, timeout=None):
            pass

        def isRunning(self):
            return False

    class QApplication:  # type: ignore[no-redef]
        pass

    pyqtSignal = Signal

from apgi_framework.utils.framework_test_utils import (
    FrameworkConfiguration,
    FrameworkExecution,
    FrameworkFailure,
    FrameworkFailureCategory,
    FrameworkResults,
    FrameworkRunCategory,
    FrameworkRunStatus,
    FrameworkTestCase,
)


class TestExecutionWorker(QThread):
    """Worker thread for executing tests without blocking the GUI."""

    # Signals for communication with GUI
    progress_updated = Signal(int, int, str)  # current, total, current_test
    test_completed = Signal(str, str, float)  # test_name, status, execution_time
    execution_finished = Signal(object)  # FrameworkResults
    execution_error = Signal(str)  # error_message

    def __init__(
        self,
        selected_tests: List[FrameworkTestCase],
        config: FrameworkConfiguration,
        parent=None,
    ):
        super().__init__(parent)
        self.selected_tests = selected_tests
        self.config = config
        self.execution_id = str(uuid.uuid4())
        self._cancelled = False
        self._paused = False

        # Mock test executor - in real implementation, this would use actual test runners
        self._test_executor = MockTestExecutor()

    def run(self):
        """Execute tests in the worker thread."""
        try:
            results = self._execute_tests()
            self.execution_finished.emit(results)
        except Exception as e:
            self.execution_error.emit(str(e))

    def cancel(self):
        """Cancel test execution."""
        self._cancelled = True

    def pause(self):
        """Pause test execution."""
        self._paused = True

    def resume(self):
        """Resume test execution."""
        self._paused = False

    def _execute_tests(self) -> FrameworkResults:
        """Execute the selected tests and return results."""
        total_tests = len(self.selected_tests)
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        error_tests = 0
        failures = []
        total_execution_time = 0.0

        for i, test_case in enumerate(self.selected_tests):
            if self._cancelled:
                break

            # Handle pause
            while self._paused and not self._cancelled:
                time.sleep(0.1)

            if self._cancelled:
                return  # type: ignore[unreachable]

            # Emit progress update
            self.progress_updated.emit(i + 1, total_tests, test_case.name)

            # Execute the test
            test_start = time.time()
            try:
                result = self._test_executor.execute_test(test_case, self.config)
                test_execution_time = time.time() - test_start
                total_execution_time += test_execution_time

                # Update test status based on result
                if result["status"] == "passed":
                    passed_tests += 1
                    status = FrameworkRunStatus.PASSED
                elif result["status"] == "failed":
                    failed_tests += 1
                    status = FrameworkRunStatus.FAILED
                    # Create failure record
                    failure = FrameworkFailure(
                        test_name=test_case.name,
                        failure_category=FrameworkFailureCategory.ASSERTION_ERROR,
                        error_message=result.get("error_message", ""),
                        stack_trace=result.get("stack_trace", ""),
                        failure_context=result.get("context", {}),
                        file_path=test_case.file_path,
                    )
                    failures.append(failure)
                elif result["status"] == "skipped":
                    skipped_tests += 1
                    status = FrameworkRunStatus.SKIPPED
                else:
                    error_tests += 1
                    status = FrameworkRunStatus.ERROR

                # Emit test completion
                self.test_completed.emit(test_case.name, status.value, test_execution_time)

            except Exception as e:
                error_tests += 1
                test_execution_time = time.time() - test_start
                total_execution_time += test_execution_time

                # Create error failure record
                failure = FrameworkFailure(
                    test_name=test_case.name,
                    failure_category=FrameworkFailureCategory.FRAMEWORK_ERROR,
                    error_message=str(e),
                    stack_trace="",
                    failure_context={},
                    file_path=test_case.file_path,
                )
                failures.append(failure)

                self.test_completed.emit(
                    test_case.name,
                    FrameworkRunStatus.ERROR.value,
                    test_execution_time,
                )

        # Create test results
        end_time = datetime.now()
        results = FrameworkResults(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            execution_time=total_execution_time,
            failures=failures,
            timestamp=end_time,
        )

        return results


class MockTestExecutor:
    """Mock test executor for demonstration purposes."""

    def execute_test(
        self, test_case: FrameworkTestCase, config: FrameworkConfiguration
    ) -> Dict[str, Any]:
        """Execute a single test case (mock implementation)."""
        # Simulate test execution time
        execution_time = 0.1 + (hash(test_case.name) % 20) / 100.0  # 0.1 to 0.3 seconds
        time.sleep(execution_time)

        # Simulate test results (90% pass rate)
        import random

        random.seed(hash(test_case.name))  # Deterministic results for same test

        if random.random() < 0.9:  # 90% pass rate
            return {"status": "passed", "execution_time": execution_time}
        elif random.random() < 0.95:  # 5% fail rate
            return {
                "status": "failed",
                "execution_time": execution_time,
                "error_message": f"Assertion failed in {test_case.name}",
                "stack_trace": f'File "{test_case.file_path}", line 42, in {test_case.name}\n    assert False',
                "context": {"assertion": "assert False"},
            }
        else:  # 5% skip rate
            return {
                "status": "skipped",
                "execution_time": execution_time,
                "skip_reason": "Test skipped due to missing dependency",
            }


class TestExecutionController(QObject):
    """Controller for managing test execution coordination between GUI and backend."""

    # Signals for GUI communication
    execution_started = Signal(str)  # execution_id
    progress_updated = Signal(int, int, str)  # current, total, current_test
    test_completed = Signal(str, str, float)  # test_name, status, execution_time
    execution_finished = Signal(object)  # FrameworkResults
    execution_cancelled = Signal()
    execution_error = Signal(str)  # error_message

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_execution: Optional[FrameworkExecution] = None
        self._worker_thread: Optional[TestExecutionWorker] = None
        self._execution_history: List[FrameworkExecution] = []
        self._is_executing = False
        self._is_paused = False

        # Progress monitoring
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress_monitoring)

    def start_execution(
        self,
        selected_tests: List[FrameworkTestCase],
        config: FrameworkConfiguration,
    ) -> str:
        """Start test execution with the given tests and configuration."""
        if self._is_executing:
            raise RuntimeError("Test execution is already in progress")

        if not selected_tests:
            raise ValueError("No tests selected for execution")

        # Create execution record
        execution_id = str(uuid.uuid4())
        self._current_execution = FrameworkExecution(
            execution_id=execution_id,
            test_suites=[],  # Will be populated during execution
            start_time=datetime.now(),
            configuration=config.__dict__ if hasattr(config, "__dict__") else {},
        )

        # Create and start worker thread
        self._worker_thread = TestExecutionWorker(selected_tests, config)
        self._setup_worker_connections()

        self._is_executing = True
        self._is_paused = False

        # Start progress monitoring
        self._progress_timer.start(100)  # Update every 100ms

        # Start execution
        self._worker_thread.start()

        # Emit started signal
        self.execution_started.emit(execution_id)

        return execution_id

    def cancel_execution(self):
        """Cancel the current test execution."""
        if not self._is_executing or not self._worker_thread:
            return

        # Cancel the worker thread
        self._worker_thread.cancel()

        # Wait for thread to finish (with timeout)
        if self._worker_thread.isRunning():
            self._worker_thread.wait(5000)  # 5 second timeout

        self._cleanup_execution()
        self.execution_cancelled.emit()

    def pause_execution(self):
        """Pause the current test execution."""
        if not self._is_executing or not self._worker_thread or self._is_paused:
            return

        self._worker_thread.pause()
        self._is_paused = True

        if self._current_execution:
            self._current_execution.status = "paused"

    def resume_execution(self):
        """Resume the paused test execution."""
        if not self._is_executing or not self._worker_thread or not self._is_paused:
            return

        self._worker_thread.resume()
        self._is_paused = False

        if self._current_execution:
            self._current_execution.status = "running"

    def get_current_execution(self) -> Optional[FrameworkExecution]:
        """Get the current execution information."""
        return self._current_execution

    def get_execution_history(self) -> List[FrameworkExecution]:
        """Get the history of test executions."""
        return self._execution_history.copy()

    def is_executing(self) -> bool:
        """Check if test execution is currently in progress."""
        return self._is_executing

    def is_paused(self) -> bool:
        """Check if test execution is currently paused."""
        return self._is_paused

    def _setup_worker_connections(self) -> None:
        """Set up signal connections with the worker thread."""
        if not self._worker_thread:
            return

        self._worker_thread.progress_updated.connect(self._on_progress_updated)
        self._worker_thread.test_completed.connect(self._on_test_completed)
        self._worker_thread.execution_finished.connect(self._on_execution_finished)
        self._worker_thread.execution_error.connect(self._on_execution_error)

    def _on_progress_updated(self, current: int, total: int, current_test: str) -> None:
        """Handle progress update from worker thread."""
        self.progress_updated.emit(current, total, current_test)

    def _on_test_completed(self, test_name: str, status: str, execution_time: float) -> None:
        """Handle test completion from worker thread."""
        self.test_completed.emit(test_name, status, execution_time)

    def _on_execution_finished(self, results: FrameworkResults) -> None:
        """Handle execution completion from worker thread."""
        if self._current_execution:
            self._current_execution.end_time = datetime.now()
            self._current_execution.results = results
            self._current_execution.status = "completed"

            # Add to history
            self._execution_history.append(self._current_execution)

        self._cleanup_execution()
        self.execution_finished.emit(results)

    def _on_execution_error(self, error_message: str) -> None:
        """Handle execution error from worker thread."""
        if self._current_execution:
            self._current_execution.status = "error"
            self._execution_history.append(self._current_execution)

        self._cleanup_execution()
        self.execution_error.emit(error_message)

    def _cleanup_execution(self) -> None:
        """Clean up after execution completion or cancellation."""
        self._is_executing = False
        self._is_paused = False
        self._progress_timer.stop()

        if self._worker_thread:
            if self._worker_thread.isRunning():
                self._worker_thread.wait()
            self._worker_thread = None

        self._current_execution = None

    def _update_progress_monitoring(self) -> None:
        """Update progress monitoring (called by timer)."""
        # This could be used for additional monitoring tasks
        # like memory usage, system resources, etc.

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get statistics about test executions."""
        if not self._execution_history:
            return {
                "total_executions": 0,
                "total_tests_run": 0,
                "average_pass_rate": 0.0,
                "average_execution_time": 0.0,
            }

        total_executions = len(self._execution_history)
        total_tests_run = sum(
            exec.results.total_tests for exec in self._execution_history if exec.results
        )
        total_passed = sum(
            exec.results.passed_tests for exec in self._execution_history if exec.results
        )
        total_execution_time = sum(
            exec.results.execution_time for exec in self._execution_history if exec.results
        )

        average_pass_rate = (total_passed / total_tests_run * 100) if total_tests_run > 0 else 0.0
        average_execution_time = (
            total_execution_time / total_executions if total_executions > 0 else 0.0
        )

        return {
            "total_executions": total_executions,
            "total_tests_run": total_tests_run,
            "average_pass_rate": average_pass_rate,
            "average_execution_time": average_execution_time,
            "last_execution": (self._execution_history[-1] if self._execution_history else None),
        }


class ResourceMonitor(QObject):
    """Monitor for tracking execution metrics and system resources."""

    resource_warning = Signal(str)  # warning_message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._monitoring_active = False
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._check_resources)

        # Resource thresholds
        self._memory_threshold_mb = 1000  # 1GB
        self._cpu_threshold_percent = 80

    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        self._monitoring_active = True
        self._monitor_timer.start(5000)  # Check every 5 seconds

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self._monitoring_active = False
        self._monitor_timer.stop()

    def _check_resources(self) -> None:
        """Check system resources and emit warnings if needed."""
        if not self._monitoring_active:
            return

        try:
            import psutil

            # Check memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)

            if memory_used_mb > self._memory_threshold_mb:
                self.resource_warning.emit(f"High memory usage: {memory_used_mb:.0f}MB used")

            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self._cpu_threshold_percent:
                self.resource_warning.emit(f"High CPU usage: {cpu_percent:.1f}%")

        except ImportError:
            # psutil not available, skip resource monitoring
            pass
        except Exception:
            # Log error but don't stop monitoring
            pass


def create_test_execution_controller() -> TestExecutionController:
    """Factory function to create a test execution controller."""
    return TestExecutionController()


# Example usage and testing
if __name__ == "__main__":
    # Create sample test cases for testing
    sample_tests = [
        FrameworkTestCase(
            name="test_example_1",
            file_path=Path("tests/test_example.py"),
            module="example",
            class_name=None,
            method_name="test_example_1",
            category=FrameworkRunCategory.UNIT,
            line_number=10,
            docstring="Example test 1",
        ),
        FrameworkTestCase(
            name="test_example_2",
            file_path=Path("tests/test_example.py"),
            module="example",
            class_name=None,
            method_name="test_example_2",
            category=FrameworkRunCategory.UNIT,
            line_number=20,
            docstring="Example test 2",
        ),
    ]

    # Create configuration
    config = FrameworkConfiguration(parallel=False, max_workers=1, timeout=30)

    # Test the controller (basic functionality)
    controller = TestExecutionController()

    print("Test execution controller created successfully")
    print(f"Is executing: {controller.is_executing()}")
    print(f"Execution history: {len(controller.get_execution_history())} items")
