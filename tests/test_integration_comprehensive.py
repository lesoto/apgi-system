"""
Comprehensive integration tests for the APGI Framework.

Tests integration between major components including:
- End-to-end workflow execution
- Component interaction and data flow
- Configuration propagation across modules
- Error propagation and handling
- Performance under realistic workloads
- Recovery and failover scenarios
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apgi_framework.config import ConfigManager
from apgi_framework.exceptions import APGIFrameworkError
from apgi_framework.main_controller import MainApplicationController


class TestFrameworkIntegration:
    """Test integration between framework components."""

    @pytest.fixture
    def temp_workspace(self):
        """Fixture providing a temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "workspace": Path(temp_dir),
                "data_dir": Path(temp_dir) / "data",
                "config_dir": Path(temp_dir) / "config",
                "output_dir": Path(temp_dir) / "output",
            }

    @pytest.fixture
    def mock_config(self, temp_workspace):
        """Fixture providing a mock configuration."""
        config = {
            "data_directory": temp_workspace["data_dir"],
            "log_level": "INFO",
            "experimental_mode": True,
            "backup_enabled": True,
        }
        return config

    def test_complete_workflow_execution(self, temp_workspace, mock_config):
        """Test complete workflow from start to finish."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Mock all major components
            with patch("apgi_framework.main_controller.APGIEquation") as mock_equation:
                with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                    with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                        # Configure mocks
                        mock_equation.calculate.return_value = {
                            "result": 42.0,
                            "confidence": 0.95,
                            "metadata": {"algorithm": "test"},
                        }
                        mock_validator.validate.return_value = True
                        mock_storage.save.return_value = True

                        # Execute workflow
                        result = controller.execute_complete_workflow(
                            experiment_id="integration_test_001",
                            parameters={"test_param": "test_value"},
                            output_path=temp_workspace["output_dir"],
                        )

                        # Verify workflow completion
                        assert result["success"] is True
                        assert result["experiment_id"] == "integration_test_001"
                        assert "output_files" in result

                        # Verify component interactions
                        mock_equation.calculate.assert_called_once()
                        mock_validator.validate.assert_called_once()
                        mock_storage.save.assert_called_once()

    def test_component_data_flow(self, temp_workspace, mock_config):
        """Test data flow between components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Mock components with realistic data flow
            test_data = {"input_data": [1, 2, 3, 4, 5]}

            with patch("apgi_framework.main_controller.APGIEquation") as mock_equation:
                with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                    with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                        # Configure data flow mocks
                        mock_equation.process.return_value = {"processed_data": [2, 4, 6, 8, 10]}
                        mock_validator.validate_batch.return_value = True
                        mock_storage.store_batch.return_value = True

                        # Execute data flow
                        result = controller.process_data_flow(test_data)

                        # Verify data transformation
                        assert result["output_data"] == [2, 4, 6, 8, 10]
                        assert mock_equation.process.assert_called_once_with(test_data)
                        mock_validator.validate_batch.assert_called_once()
                        mock_storage.store_batch.assert_called_once()

    def test_configuration_propagation(self, temp_workspace, mock_config):
        """Test configuration propagation to all components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Update configuration
            new_config = mock_config.copy()
            new_config["experimental_mode"] = False
            new_config["new_parameter"] = "test_value"

            controller.update_configuration(new_config)

            # Verify all components received updated config
            components = controller.get_all_components()
            for component in components.values():
                assert hasattr(component, "config")
                # Check if component was notified of config change
                component.handle_config_update.assert_called_once_with(new_config)

    def test_error_propagation_chain(self, temp_workspace, mock_config):
        """Test error propagation through component chain."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Mock error in one component
            with patch("apgi_framework.main_controller.APGIEquation") as mock_equation:
                with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                    with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                        # Configure error propagation
                        mock_equation.calculate.side_effect = Exception("Equation error")
                        mock_validator.validate.return_value = True
                        mock_storage.save.return_value = True

                        # Execute workflow expecting error
                        with pytest.raises(APGIFrameworkError) as exc_info:
                            controller.execute_complete_workflow(
                                experiment_id="error_test",
                                parameters={},
                                output_path=temp_workspace["output_dir"],
                            )

                        # Verify error propagation
                        assert "Equation error" in str(exc_info.value)
                        mock_equation.calculate.assert_called_once()
                        mock_storage.save.assert_not_called()  # Should not be called due to error

    def test_parallel_component_execution(self, temp_workspace, mock_config):
        """Test parallel execution of multiple components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Mock parallel-capable components
            with patch("apgi_framework.main_controller.APGIEquation") as mock_equation:
                with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                    with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                        # Configure parallel execution
                        mock_equation.calculate_parallel.return_value = {
                            "result": "parallel_complete"
                        }
                        mock_validator.validate_parallel.return_value = True
                        mock_storage.save_parallel.return_value = True

                        # Execute parallel workflow
                        result = controller.execute_parallel_workflow(
                            experiment_id="parallel_test",
                            parameters={"parallel_param": True},
                            max_workers=4,
                        )

                        # Verify parallel execution
                        assert result["success"] is True
                        assert result["worker_count"] == 4
                        mock_equation.calculate_parallel.assert_called_once()
                        mock_validator.validate_parallel.assert_called_once()
                        mock_storage.save_parallel.assert_called_once()


class TestComponentInteraction:
    """Test specific component interactions."""

    @pytest.fixture
    def temp_workspace(self):
        """Fixture providing a temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "workspace": Path(temp_dir),
                "data_dir": Path(temp_dir) / "data",
                "config_dir": Path(temp_dir) / "config",
                "output_dir": Path(temp_dir) / "output",
            }

    @pytest.fixture
    def mock_config(self, temp_workspace):
        """Fixture providing a mock configuration."""
        config = {
            "data_directory": temp_workspace["data_dir"],
            "log_level": "INFO",
            "experimental_mode": True,
            "component_timeout": 30,
        }
        return config

    def test_equation_validator_interaction(self, temp_workspace, mock_config):
        """Test interaction between equation and validator components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            test_equation_data = {
                "equation_type": "test",
                "parameters": {"a": 1, "b": 2},
            }

            with patch("apgi_framework.main_controller.APGIEquation") as mock_equation:
                with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                    # Configure interaction
                    mock_equation.solve.return_value = {
                        "solution": 42,
                        "steps": [1, 2, 3],
                    }
                    mock_validator.validate_solution.return_value = True

                    # Execute interaction
                    result = controller.solve_and_validate(test_equation_data)

                    # Verify interaction
                    assert result["solution"] == 42
                    assert result["validation_passed"] is True
                    mock_equation.solve.assert_called_once_with(test_equation_data)
                    mock_validator.validate_solution.assert_called_once_with(
                        {"solution": 42, "steps": [1, 2, 3]}
                    )

    def test_data_storage_integration(self, temp_workspace, mock_config):
        """Test integration between data processing and storage."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            test_datasets = [
                {"dataset_id": "ds1", "data": [1, 2, 3]},
                {"dataset_id": "ds2", "data": [4, 5, 6]},
            ]

            with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                    # Configure integration
                    mock_validator.validate_datasets.return_value = True
                    mock_storage.store_datasets.return_value = {"stored_count": 2}

                    # Execute integration
                    result = controller.store_validated_datasets(test_datasets)

                    # Verify integration
                    assert result["success"] is True
                    assert result["stored_count"] == 2
                    mock_validator.validate_datasets.assert_called_once_with(test_datasets)
                    mock_storage.store_datasets.assert_called_once()

    def test_gui_backend_communication(self, temp_workspace, mock_config):
        """Test communication between GUI and backend components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            gui_requests = [
                {"action": "update_status", "data": "processing"},
                {"action": "get_results", "data": None},
                {"action": "save_config", "data": {"new_setting": True}},
            ]

            with patch("apgi_framework.gui.components.MainGUIController") as mock_gui:
                with patch("apgi_framework.backend.DataProcessor") as mock_backend:
                    # Configure communication
                    mock_gui.get_requests.return_value = gui_requests
                    mock_backend.process_requests.return_value = {
                        "processed": 3,
                        "responses": [
                            "status_updated",
                            "results_retrieved",
                            "config_saved",
                        ],
                    }

                    # Execute communication
                    result = controller.process_gui_backend_communication()

                    # Verify communication
                    assert result["processed_requests"] == 3
                    assert len(result["responses"]) == 3
                    mock_gui.get_requests.assert_called_once()
                    mock_backend.process_requests.assert_called_once_with(gui_requests)

    def test_falsification_integration(self, temp_workspace, mock_config):
        """Test integration with falsification testing components."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            falsification_tests = [
                {"test_type": "consciousness", "expected_result": False},
                {"test_type": "threshold", "expected_result": True},
            ]

            with patch(
                "apgi_framework.falsification.ConsciousnessWithoutIgnitionTest"
            ) as mock_conscious:
                with patch(
                    "apgi_framework.falsification.ThresholdInsensitivityTest"
                ) as mock_threshold:
                    # Configure falsification
                    mock_conscious.execute.return_value = {
                        "passed": True,
                        "details": "test",
                    }
                    mock_threshold.execute.return_value = {
                        "passed": True,
                        "details": "test",
                    }

                    # Execute falsification tests
                    result = controller.run_falsification_suite(falsification_tests)

                    # Verify integration
                    assert result["total_tests"] == 2
                    assert result["passed_tests"] == 2
                    mock_conscious.execute.assert_called_once()
                    mock_threshold.execute.assert_called_once()


class TestPerformanceIntegration:
    """Test performance under realistic workloads."""

    @pytest.fixture
    def temp_workspace(self):
        """Fixture providing a temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "workspace": Path(temp_dir),
                "data_dir": Path(temp_dir) / "data",
                "config_dir": Path(temp_dir) / "config",
                "output_dir": Path(temp_dir) / "output",
            }

    @pytest.fixture
    def mock_config(self, temp_workspace):
        """Fixture providing a mock configuration."""
        config = {
            "data_directory": temp_workspace["data_dir"],
            "log_level": "INFO",
            "performance_monitoring": True,
            "max_memory_usage": 1024,
        }
        return config

    def test_large_dataset_processing(self, temp_workspace, mock_config):
        """Test processing of large datasets."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Create large test dataset
            large_dataset = {
                "dataset_id": "large_test",
                "data": list(range(10000)),  # 10k items
                "metadata": {"size": "large", "complexity": "high"},
            }

            with patch("apgi_framework.main_controller.DataProcessor") as mock_processor:
                with patch("apgi_framework.main_controller.StorageManager") as mock_storage:
                    # Configure performance monitoring
                    mock_processor.process_large_dataset.return_value = {
                        "processed_count": 10000,
                        "processing_time": 2.5,
                    }
                    mock_storage.store_large_result.return_value = True

                    # Execute with performance tracking
                    start_time = time.time()
                    result = controller.process_large_dataset(large_dataset)
                    processing_time = time.time() - start_time

                    # Verify performance
                    assert result["success"] is True
                    assert result["processed_count"] == 10000
                    assert processing_time < 5.0  # Should complete within 5 seconds
                    mock_processor.process_large_dataset.assert_called_once()
                    mock_storage.store_large_result.assert_called_once()

    def test_memory_usage_monitoring(self, temp_workspace, mock_config):
        """Test memory usage during intensive operations."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            with patch("psutil.Process") as mock_process:
                mock_process.return_value.memory_info.return_value.rss = 500000  # 500MB

                # Execute memory-intensive operation
                result = controller.execute_memory_intensive_task(
                    task_data={"size": "large"}, memory_limit=600000  # 600MB limit
                )

                # Verify memory monitoring
                assert result["within_limit"] is True
                assert result["peak_memory"] == 500000
                mock_process.assert_called()

    def test_concurrent_workload_handling(self, temp_workspace, mock_config):
        """Test handling of concurrent workloads."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            concurrent_tasks = [
                {"task_id": "task_1", "data": [1, 2, 3]},
                {"task_id": "task_2", "data": [4, 5, 6]},
                {"task_id": "task_3", "data": [7, 8, 9]},
            ]

            with patch("apgi_framework.main_controller.TaskScheduler") as mock_scheduler:
                with patch("apgi_framework.main_controller.WorkerManager") as mock_workers:
                    # Configure concurrent execution
                    mock_scheduler.schedule_tasks.return_value = {"scheduled_count": 3}
                    mock_workers.execute_parallel.return_value = {
                        "completed_tasks": 3,
                        "execution_time": 3.0,
                    }

                    # Execute concurrent workload
                    start_time = time.time()
                    result = controller.execute_concurrent_workload(concurrent_tasks)
                    execution_time = time.time() - start_time

                    # Verify concurrent execution
                    assert result["success"] is True
                    assert result["completed_tasks"] == 3
                    assert execution_time < 10.0  # Should complete within 10 seconds
                    mock_scheduler.schedule_tasks.assert_called_once()
                    mock_workers.execute_parallel.assert_called_once()


class TestRecoveryAndFailover:
    """Test recovery and failover scenarios."""

    @pytest.fixture
    def temp_workspace(self):
        """Fixture providing a temporary workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "workspace": Path(temp_dir),
                "data_dir": Path(temp_dir) / "data",
                "config_dir": Path(temp_dir) / "config",
                "output_dir": Path(temp_dir) / "output",
            }

    @pytest.fixture
    def mock_config(self, temp_workspace):
        """Fixture providing a mock configuration."""
        config = {
            "data_directory": temp_workspace["data_dir"],
            "log_level": "INFO",
            "failover_enabled": True,
            "backup_systems": ["primary", "secondary"],
        }
        return config

    def test_component_failure_recovery(self, temp_workspace, mock_config):
        """Test recovery from component failures."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Simulate component failure
            with patch("apgi_framework.main_controller.DataProcessor") as mock_processor:
                with patch("apgi_framework.main_controller.BackupProcessor") as mock_backup:
                    # Configure failure and recovery
                    mock_processor.process.side_effect = Exception("Processor failed")
                    mock_backup.is_available.return_value = True
                    mock_backup.activate.return_value = {"backup_active": True}

                    # Execute with failure recovery
                    result = controller.execute_with_recovery(
                        task_data={"test": "data"}, recovery_enabled=True
                    )

                    # Verify recovery activation
                    assert result["recovery_activated"] is True
                    assert result["primary_failed"] is True
                    assert result["backup_successful"] is True
                    mock_backup.activate.assert_called_once()

    def test_data_corruption_handling(self, temp_workspace, mock_config):
        """Test handling of data corruption scenarios."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Create corrupted data scenario
            corrupted_data = {
                "experiment_id": "corruption_test",
                "data": "intact_data",
                "checksum": "valid_checksum",
            }

            with patch("apgi_framework.main_controller.DataValidator") as mock_validator:
                with patch("apgi_framework.main_controller.DataRecovery") as mock_recovery:
                    # Configure corruption detection
                    mock_validator.validate_checksum.return_value = False  # Checksum mismatch
                    mock_recovery.restore_from_backup.return_value = {
                        "restored": True,
                        "restored_data": "original_intact_data",
                    }

                    # Execute with corruption handling
                    result = controller.execute_with_corruption_detection(corrupted_data)

                    # Verify corruption handling
                    assert result["corruption_detected"] is True
                    assert result["recovery_successful"] is True
                    assert result["final_data"] == "original_intact_data"
                    mock_validator.validate_checksum.assert_called_once()
                    mock_recovery.restore_from_backup.assert_called_once()

    def test_network_interruption_recovery(self, temp_workspace, mock_config):
        """Test recovery from network interruptions."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            with patch("apgi_framework.main_controller.NetworkManager") as mock_network:
                with patch("apgi_framework.main_controller.CacheManager") as mock_cache:
                    # Configure network interruption
                    mock_network.is_connected.return_value = False
                    mock_cache.has_cached_data.return_value = True
                    mock_cache.get_cached_data.return_value = {"cached_results": "test_data"}

                    # Execute with network interruption
                    result = controller.execute_with_network_resilience()

                    # Verify network resilience
                    assert result["network_available"] is False
                    assert result["using_cache"] is True
                    assert result["cached_data_available"] is True
                    mock_network.is_connected.assert_called_once()
                    mock_cache.has_cached_data.assert_called_once()

    def test_graceful_degradation(self, temp_workspace, mock_config):
        """Test graceful degradation under load."""
        with patch(
            "apgi_framework.main_controller.get_config_manager",
            return_value=Mock(spec=ConfigManager),
        ):
            controller = MainApplicationController()

            # Simulate system under load
            load_scenarios = [
                {"component": "memory", "load_level": 0.9, "status": "warning"},
                {"component": "cpu", "load_level": 0.8, "status": "acceptable"},
                {"component": "disk", "load_level": 0.95, "status": "critical"},
            ]

            with patch("apgi_framework.main_controller.LoadManager") as mock_load:
                with patch("apgi_framework.main_controller.PerformanceManager") as mock_perf:
                    # Configure degradation handling
                    mock_load.get_system_load.return_value = load_scenarios
                    mock_perf.adjust_performance.return_value = {
                        "degradation_applied": True,
                        "adjusted_components": ["memory", "disk"],
                    }

                    # Execute with degradation
                    result = controller.execute_under_load(load_scenarios)

                    # Verify degradation handling
                    assert result["degradation_detected"] is True
                    assert result["critical_components"] == ["disk"]
                    assert result["performance_adjusted"] is True
                    mock_load.get_system_load.assert_called_once()
                    mock_perf.adjust_performance.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
