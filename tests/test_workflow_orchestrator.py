"""
Comprehensive test suite for workflow_orchestrator.py module.

This test suite provides full coverage for the WorkflowOrchestrator class and all
its workflow management methods, ensuring all critical functionality is tested.
"""

import json
import tempfile
import unittest.mock as mock
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import the modules we're testing
from apgi_framework.workflow_orchestrator import (
    WorkflowConfiguration,
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowStage,
    WorkflowStageResult,
    WorkflowStatus,
    run_quick_validation_workflow,
    run_standard_falsification_workflow,
)


class MockController:
    """Mock controller for testing."""

    def __init__(self):
        self.config_manager = mock.Mock()
        self.system_validator = mock.Mock()
        self.falsification_engine = mock.Mock()
        self.statistical_analyzer = mock.Mock()
        self.data_manager = mock.Mock()
        self._initialized = True

        # Mock common method calls
        self.initialize_system = mock.Mock()
        self.run_system_validation = mock.Mock(return_value={"overall": True})
        self.get_falsification_tests = mock.Mock(
            return_value={
                "primary": mock.Mock(),
                "consciousness_without_ignition": mock.Mock(),
                "threshold_insensitivity": mock.Mock(),
                "soma_bias": mock.Mock(),
            }
        )

        # Mock falsification test results
        for test_name, test_mock in self.get_falsification_tests.return_value.items():
            test_mock.run_test.return_value = mock.Mock(
                is_falsified=False, p_value=0.1, effect_size=0.3, confidence_level=0.95
            )

        self.system_validator.run_validation.return_value = mock.Mock()
        self.falsification_engine.run_primary_falsification.return_value = {"results": []}
        self.falsification_engine.run_secondary_falsification.return_value = {"results": []}
        self.statistical_analyzer.run_analysis.return_value = {"statistics": {}}
        self.data_manager.save_results.return_value = True


class TestWorkflowStage:
    """Test WorkflowStage enum."""

    def test_workflow_stage_values(self):
        """Test WorkflowStage enum values."""
        assert WorkflowStage.INITIALIZATION.value == "initialization"
        assert WorkflowStage.SYSTEM_VALIDATION.value == "system_validation"
        assert WorkflowStage.PRIMARY_FALSIFICATION.value == "primary_falsification"
        assert WorkflowStage.SECONDARY_FALSIFICATION.value == "secondary_falsification"
        assert WorkflowStage.STATISTICAL_ANALYSIS.value == "statistical_analysis"
        assert WorkflowStage.RESULT_AGGREGATION.value == "result_aggregation"
        assert WorkflowStage.REPORT_GENERATION.value == "report_generation"
        assert WorkflowStage.CLEANUP.value == "cleanup"


class TestWorkflowStatus:
    """Test WorkflowStatus enum."""

    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.CANCELLED.value == "cancelled"


class TestWorkflowStageResult:
    """Test WorkflowStageResult dataclass."""

    def test_workflow_stage_result_creation(self):
        """Test creating a WorkflowStageResult."""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)

        result = WorkflowStageResult(
            stage=WorkflowStage.INITIALIZATION,
            status=WorkflowStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            result_data={"test": "data"},
            error_message=None,
        )

        assert result.stage == WorkflowStage.INITIALIZATION
        assert result.status == WorkflowStatus.COMPLETED
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.result_data == {"test": "data"}
        assert result.error_message is None

    def test_workflow_stage_result_duration(self):
        """Test duration property calculation."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        result = WorkflowStageResult(
            stage=WorkflowStage.INITIALIZATION,
            status=WorkflowStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
        )

        assert result.duration == timedelta(hours=1)

        # Test without end_time
        result_no_end = WorkflowStageResult(
            stage=WorkflowStage.INITIALIZATION,
            status=WorkflowStatus.RUNNING,
            start_time=start_time,
        )
        assert result_no_end.duration is None


class TestWorkflowResult:
    """Test WorkflowResult dataclass."""

    def test_workflow_result_creation(self):
        """Test creating a WorkflowResult."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=2)

        stage_result = WorkflowStageResult(
            stage=WorkflowStage.INITIALIZATION,
            status=WorkflowStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
        )

        result = WorkflowResult(
            workflow_id="test_workflow",
            start_time=start_time,
            end_time=end_time,
            overall_status=WorkflowStatus.COMPLETED,
            stage_results={WorkflowStage.INITIALIZATION: stage_result},
        )

        assert result.workflow_id == "test_workflow"
        assert result.start_time == start_time
        assert result.end_time == end_time
        assert result.overall_status == WorkflowStatus.COMPLETED
        assert len(result.stage_results) == 1
        assert result.falsification_conclusion is None

    def test_workflow_result_properties(self):
        """Test WorkflowResult properties."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        stage1 = WorkflowStageResult(
            WorkflowStage.INITIALIZATION, WorkflowStatus.COMPLETED, start_time, end_time
        )
        stage2 = WorkflowStageResult(
            WorkflowStage.SYSTEM_VALIDATION,
            WorkflowStatus.COMPLETED,
            start_time,
            end_time,
        )

        result = WorkflowResult(
            workflow_id="test",
            start_time=start_time,
            end_time=end_time,
            overall_status=WorkflowStatus.COMPLETED,
            stage_results={
                WorkflowStage.INITIALIZATION: stage1,
                WorkflowStage.SYSTEM_VALIDATION: stage2,
            },
        )

        assert result.total_duration == timedelta(hours=1)
        assert len(result.stage_results) == 2


class TestWorkflowConfiguration:
    """Test WorkflowConfiguration dataclass."""

    def test_workflow_configuration_creation(self):
        """Test creating a WorkflowConfiguration."""
        config = WorkflowConfiguration(
            parallel_execution=True,
            max_workers=4,
            timeout_minutes=120,
            save_intermediate_results=True,
            generate_detailed_reports=True,
        )

        assert config.parallel_execution is True
        assert config.max_workers == 4
        assert config.timeout_minutes == 120
        assert config.save_intermediate_results is True
        assert config.generate_detailed_reports is True

    def test_workflow_configuration_defaults(self):
        """Test WorkflowConfiguration default values."""
        config = WorkflowConfiguration()

        assert config.run_primary_tests is True
        assert config.run_secondary_tests is True
        assert config.run_statistical_analysis is True
        assert config.generate_detailed_reports is True
        assert config.parallel_execution is False
        assert config.max_workers == 4
        assert config.timeout_minutes == 60


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = MockController()
        self.config = WorkflowConfiguration()
        self.orchestrator = WorkflowOrchestrator(self.mock_controller, self.config)

    def test_workflow_orchestrator_initialization(self):
        """Test WorkflowOrchestrator initialization."""
        assert self.orchestrator.controller == self.mock_controller
        assert self.orchestrator.config == self.config
        assert self.orchestrator.current_workflow is None
        assert self.orchestrator.stage_callbacks == {}

    def test_register_stage_callback(self):
        """Test registering stage callbacks."""

        def test_callback(stage_result):
            pass

        self.orchestrator.register_stage_callback(WorkflowStage.INITIALIZATION, test_callback)

        assert WorkflowStage.INITIALIZATION in self.orchestrator.stage_callbacks
        assert test_callback in self.orchestrator.stage_callbacks[WorkflowStage.INITIALIZATION]

    def test_run_complete_workflow(self):
        """Test running complete workflow."""
        with mock.patch.object(self.orchestrator, "_run_initialization") as mock_init:
            with mock.patch.object(self.orchestrator, "_run_system_validation") as mock_validation:
                with mock.patch.object(self.orchestrator, "_run_primary_tests") as mock_primary:
                    with mock.patch.object(
                        self.orchestrator, "_run_statistical_analysis"
                    ) as mock_analysis:
                        with mock.patch.object(
                            self.orchestrator, "_run_result_aggregation"
                        ) as mock_aggregation:
                            with mock.patch.object(
                                self.orchestrator, "_run_report_generation"
                            ) as mock_report:
                                with mock.patch.object(
                                    self.orchestrator, "_run_cleanup"
                                ) as mock_cleanup:
                                    mock_init.return_value = {"status": "completed"}
                                    mock_validation.return_value = {"status": "completed"}
                                    mock_primary.return_value = {"status": "completed"}
                                    mock_analysis.return_value = {"status": "completed"}
                                    mock_aggregation.return_value = {"status": "completed"}
                                    mock_report.return_value = {"status": "completed"}
                                    mock_cleanup.return_value = {"status": "completed"}

                                    result = self.orchestrator.run_complete_workflow()

                                    assert isinstance(result, WorkflowResult)
                                    assert result.overall_status == WorkflowStatus.COMPLETED
                                    assert result.workflow_id is not None

    def test_run_parallel_workflow(self):
        """Test running parallel workflow."""
        with mock.patch.object(self.orchestrator, "_run_initialization"):
            with mock.patch.object(self.orchestrator, "_run_parallel_falsification_tests"):
                with mock.patch.object(self.orchestrator, "_run_statistical_analysis"):
                    with mock.patch.object(self.orchestrator, "_run_result_aggregation"):
                        with mock.patch.object(self.orchestrator, "_run_report_generation"):
                            with mock.patch.object(self.orchestrator, "_run_cleanup"):
                                result = self.orchestrator.run_parallel_workflow()

                                assert isinstance(result, WorkflowResult)
                                assert result.overall_status == WorkflowStatus.COMPLETED

    def test_execute_stage(self):
        """Test stage execution."""

        def mock_stage_function():
            return {"result": "success"}

        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )

        self.orchestrator._execute_stage(WorkflowStage.INITIALIZATION, mock_stage_function)

        assert WorkflowStage.INITIALIZATION in self.orchestrator.current_workflow.stage_results

    def test_run_initialization(self):
        """Test initialization stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_initialization()

        assert isinstance(result, dict)
        assert "system_initialized" in result

    def test_run_system_validation(self):
        """Test system validation stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_system_validation()

        assert isinstance(result, dict)

    def test_run_primary_tests(self):
        """Test primary falsification tests stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_primary_tests()

        assert isinstance(result, dict)

    def test_run_secondary_tests(self):
        """Test secondary falsification tests stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_secondary_tests()

        assert isinstance(result, dict)

    def test_run_statistical_analysis(self):
        """Test statistical analysis stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_statistical_analysis()

        assert isinstance(result, dict)

    def test_run_result_aggregation(self):
        """Test result aggregation stage."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_result_aggregation()

        assert isinstance(result, dict)

    def test_run_report_generation(self):
        """Test report generation stage."""
        self.orchestrator.controller.config_manager.get_experimental_config.return_value.output_directory = (
            "/tmp/test"
        )
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )
        result = self.orchestrator._run_report_generation()

        assert isinstance(result, dict)

    def test_run_cleanup(self):
        """Test cleanup stage."""
        result = self.orchestrator._run_cleanup()

        assert isinstance(result, dict)
        assert "cleanup_completed" in result

    def test_save_json_report(self):
        """Test saving JSON report."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.COMPLETED,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            self.orchestrator._save_json_report(temp_path)

            # Verify file was created and contains valid JSON
            assert temp_path.exists()

            with open(temp_path, "r") as f:
                saved_data = json.load(f)

            assert "workflow_id" in saved_data
            assert saved_data["workflow_id"] == "test"
        finally:
            # Clean up
            temp_path.unlink(missing_ok=True)

    def test_save_summary_report(self):
        """Test saving summary report."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.COMPLETED,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            self.orchestrator._save_summary_report(temp_path)

            # Verify file was created
            assert temp_path.exists()

            with open(temp_path, "r") as f:
                content = f.read()

            assert "WORKFLOW SUMMARY" in content
            assert "test" in content
        finally:
            # Clean up
            temp_path.unlink(missing_ok=True)

    def test_serialize_test_results(self):
        """Test serializing test results."""
        test_results = {
            "primary_tests": {
                "falsification_results": [
                    {"test": "test1", "passed": True},
                    {"test": "test2", "passed": False},
                ]
            },
            "statistics": {"mean": 0.5, "std": 0.1},
        }

        serialized = self.orchestrator._serialize_test_results(test_results)

        assert isinstance(serialized, dict)
        assert "primary_tests" in serialized
        assert "statistics" in serialized

    def test_cancel_workflow(self):
        """Test cancelling workflow."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )

        self.orchestrator.cancel_workflow()

        assert self.orchestrator.current_workflow.overall_status == WorkflowStatus.CANCELLED

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        # Test with no current workflow
        status = self.orchestrator.get_workflow_status()
        assert status is None

        # Test with current workflow
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )

        status = self.orchestrator.get_workflow_status()
        assert status == self.orchestrator.current_workflow

    def test_run_parallel_falsification_tests(self):
        """Test running parallel falsification tests."""
        self.orchestrator.current_workflow = WorkflowResult(
            workflow_id="test",
            start_time=datetime.now(),
            overall_status=WorkflowStatus.RUNNING,
        )

        mock_executor = mock.Mock()
        mock_future = mock.Mock()
        mock_executor.submit.return_value = mock_future
        mock_future.result.return_value = {"results": []}
        self.orchestrator.executor = mock_executor

        self.orchestrator._run_parallel_falsification_tests()

        # Verify that parallel execution was attempted
        assert mock_executor.submit.call_count == 2


class TestModuleFunctions:
    """Test module-level functions."""

    def test_run_standard_falsification_workflow(self):
        """Test run_standard_falsification_workflow function."""
        mock_controller = MockController()

        with mock.patch(
            "apgi_framework.workflow_orchestrator.WorkflowOrchestrator"
        ) as mock_orchestrator_class:
            mock_orchestrator = mock.Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator.run_complete_workflow.return_value = WorkflowResult(
                workflow_id="standard_test",
                start_time=datetime.now(),
                overall_status=WorkflowStatus.COMPLETED,
            )

            result = run_standard_falsification_workflow(controller=mock_controller)

            assert isinstance(result, WorkflowResult)
            mock_orchestrator.run_complete_workflow.assert_called_once()

    def test_run_quick_validation_workflow(self):
        """Test run_quick_validation_workflow function."""

        with mock.patch(
            "apgi_framework.workflow_orchestrator.WorkflowOrchestrator"
        ) as mock_orchestrator_class:
            mock_orchestrator = mock.Mock()
            mock_orchestrator_class.return_value = mock_orchestrator
            mock_orchestrator.run_complete_workflow.return_value = WorkflowResult(
                workflow_id="quick_test",
                start_time=datetime.now(),
                overall_status=WorkflowStatus.COMPLETED,
            )

            result = run_quick_validation_workflow()

            assert isinstance(result, WorkflowResult)
            mock_orchestrator.run_complete_workflow.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
