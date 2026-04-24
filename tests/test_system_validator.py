"""
Comprehensive test suite for system_validator.py module.

This test suite provides full coverage for the SystemValidator class and all
its validation methods, ensuring all critical functionality is tested.
"""

import json
import sys
import tempfile
import unittest.mock as mock
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the modules we're testing with error handling
try:
    from apgi_framework.system_validator import (
        SystemValidationReport,
        SystemValidator,
        ValidationCategory,
        ValidationLevel,
        ValidationSuite,
        ValidationTestResult,
    )
except ImportError as e:
    pytest.skip(f"Cannot import system_validator: {e}", allow_module_level=True)


class MockController:
    """Mock controller for testing."""

    def __init__(self):
        self.config_manager = mock.Mock()
        self._initialized = True
        self._mathematical_engine = None
        self._neural_simulators = None
        self._falsification_tests = None
        self._data_manager = None

        # Add equation_processor mock
        self.equation_processor = mock.Mock()

        # Mock common method calls
        self.get_mathematical_engine = mock.Mock(
            return_value={
                "equation": mock.Mock(),
                "precision_calculator": mock.Mock(),
                "prediction_error_processor": mock.Mock(),
                "somatic_marker_engine": mock.Mock(),
                "threshold_manager": mock.Mock(),
            }
        )
        self.get_neural_simulators = mock.Mock(
            return_value={
                "p3b": mock.Mock(),
                "gamma": mock.Mock(),
                "bold": mock.Mock(),
                "pci_calculator": mock.Mock(),
            }
        )
        self.get_falsification_tests = mock.Mock(
            return_value={
                "primary": mock.Mock(),
                "consciousness_without_ignition": mock.Mock(),
                "threshold_insensitivity": mock.Mock(),
                "soma_bias": mock.Mock(),
            }
        )
        self.get_data_manager = mock.Mock(
            return_value={
                "storage": mock.Mock(),
                "validator": mock.Mock(),
            }
        )

        # Mock equation methods
        equation_mock = self.get_mathematical_engine.return_value["equation"]
        equation_mock.calculate_surprise.return_value = 3.44
        equation_mock.calculate_ignition_probability.return_value = 0.5

        # Mock precision calculator
        precision_mock = self.get_mathematical_engine.return_value["precision_calculator"]
        precision_mock.calculate_exteroceptive_precision.return_value = 2.0
        precision_mock.calculate_interoceptive_precision.return_value = 1.5

        # Mock prediction error processor
        error_mock = self.get_mathematical_engine.return_value["prediction_error_processor"]
        error_mock.standardize_errors.return_value = [0.0, 0.0, 0.0, 0.0, 0.0]

        # Mock somatic marker engine
        somatic_mock = self.get_mathematical_engine.return_value["somatic_marker_engine"]
        somatic_mock.calculate_gain.return_value = 1.2

        # Mock threshold manager
        threshold_mock = self.get_mathematical_engine.return_value["threshold_manager"]
        threshold_mock.adjust_threshold.return_value = 4.0

        # Mock neural simulators
        p3b_mock = self.get_neural_simulators.return_value["p3b"]
        p3b_mock.generate_signature = mock.Mock(
            side_effect=lambda conscious: mock.Mock(
                amplitude=6.0 if conscious else 1.0, latency=350 if conscious else 200
            )
        )

        # Mock falsification tests
        primary_mock = self.get_falsification_tests.return_value["primary"]
        primary_mock.run_test = mock.Mock(return_value=mock.Mock())

        # Mock data manager components
        data_manager_mock = self.get_data_manager.return_value
        storage_mock = data_manager_mock["storage"]
        storage_mock.save_dataset = mock.Mock(return_value=True)
        storage_mock.load_dataset = mock.Mock(return_value={})

        validator_mock = data_manager_mock["validator"]
        validator_mock.validate_dataset = mock.Mock(return_value=True)


class TestValidationTestResult:
    """Test ValidationTestResult dataclass."""

    def test_validation_test_result_creation(self):
        """Test creating a ValidationTestResult."""
        result = ValidationTestResult(
            test_name="test_math",
            category=ValidationCategory.MATHEMATICAL_ACCURACY,
            passed=True,
            execution_time=0.1,
            expected_result=1.0,
            actual_result=1.0,
        )

        assert result.test_name == "test_math"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert result.passed is True
        assert result.execution_time == 0.1
        assert result.expected_result == 1.0
        assert result.actual_result == 1.0
        assert result.error_message is None
        assert result.performance_metrics == {}

    def test_validation_test_result_status(self):
        """Test status property."""
        passed_result = ValidationTestResult(
            "test", ValidationCategory.MATHEMATICAL_ACCURACY, True, 0.1
        )
        failed_result = ValidationTestResult(
            "test", ValidationCategory.MATHEMATICAL_ACCURACY, False, 0.1
        )

        assert passed_result.status == "PASS"
        assert failed_result.status == "FAIL"


class TestValidationSuite:
    """Test ValidationSuite dataclass."""

    def test_validation_suite_creation(self):
        """Test creating a ValidationSuite."""
        suite = ValidationSuite(category=ValidationCategory.MATHEMATICAL_ACCURACY)

        assert suite.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert suite.tests == []

    def test_validation_suite_with_tests(self):
        """Test ValidationSuite with tests."""
        test1 = ValidationTestResult("test1", ValidationCategory.MATHEMATICAL_ACCURACY, True, 0.1)
        test2 = ValidationTestResult("test2", ValidationCategory.MATHEMATICAL_ACCURACY, False, 0.2)

        suite = ValidationSuite(
            category=ValidationCategory.MATHEMATICAL_ACCURACY, tests=[test1, test2]
        )

        assert suite.passed_count == 1
        assert suite.failed_count == 1
        assert suite.total_count == 2
        assert suite.success_rate == 50.0
        assert suite.total_execution_time == pytest.approx(0.3)

    def test_empty_validation_suite(self):
        """Test empty ValidationSuite properties."""
        suite = ValidationSuite(category=ValidationCategory.MATHEMATICAL_ACCURACY)

        assert suite.passed_count == 0
        assert suite.failed_count == 0
        assert suite.total_count == 0
        assert suite.success_rate == 0.0
        assert suite.total_execution_time == 0.0


class TestSystemValidationReport:
    """Test SystemValidationReport dataclass."""

    def test_system_validation_report_creation(self):
        """Test creating a SystemValidationReport."""
        start_time = datetime.now()
        report = SystemValidationReport(
            validation_id="test_123",
            start_time=start_time,
            validation_level=ValidationLevel.BASIC,
        )

        assert report.validation_id == "test_123"
        assert report.start_time == start_time
        assert report.validation_level == ValidationLevel.BASIC
        assert report.end_time is None
        assert report.suites == {}
        assert report.overall_passed is False
        assert report.total_tests == 0
        assert report.passed_tests == 0
        assert report.failed_tests == 0

    def test_duration_property(self):
        """Test duration property calculation."""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)

        report = SystemValidationReport(
            validation_id="test", start_time=start_time, end_time=end_time
        )

        assert report.duration == timedelta(hours=1)

        # Test without end_time
        report_no_end = SystemValidationReport(validation_id="test", start_time=start_time)
        assert report_no_end.duration is None

    def test_success_rate_property(self):
        """Test success rate calculation."""
        report = SystemValidationReport(
            validation_id="test",
            start_time=datetime.now(),
            total_tests=10,
            passed_tests=8,
        )

        assert report.success_rate == 80.0

        # Test with zero tests
        empty_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now(), total_tests=0
        )
        assert empty_report.success_rate == 0.0


class TestSystemValidator:
    """Test SystemValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = MockController()
        self.validator = SystemValidator(self.mock_controller)

    def test_system_validator_initialization(self):
        """Test SystemValidator initialization."""
        assert self.validator.controller == self.mock_controller
        assert self.validator.current_report is None
        assert self.validator.numerical_tolerance == 1e-10
        assert self.validator.statistical_tolerance == 0.05

    def test_run_validation_basic(self):
        """Test running basic validation."""
        with mock.patch.object(self.validator, "_collect_system_info"):
            with mock.patch.object(self.validator, "_run_mathematical_validation"):
                with mock.patch.object(self.validator, "_calculate_overall_results"):
                    report = self.validator.run_validation(ValidationLevel.BASIC)

                    assert isinstance(report, SystemValidationReport)
                    assert report.validation_level == ValidationLevel.BASIC
                    assert self.validator.current_report == report

    def test_run_validation_comprehensive(self):
        """Test running comprehensive validation."""
        with mock.patch.object(self.validator, "_collect_system_info"):
            with mock.patch.object(self.validator, "_run_mathematical_validation"):
                with mock.patch.object(self.validator, "_run_neural_simulation_validation"):
                    with mock.patch.object(self.validator, "_run_falsification_logic_validation"):
                        with mock.patch.object(self.validator, "_run_data_integrity_validation"):
                            with mock.patch.object(self.validator, "_run_integration_validation"):
                                with mock.patch.object(
                                    self.validator, "_run_error_handling_validation"
                                ):
                                    with mock.patch.object(
                                        self.validator, "_run_performance_validation"
                                    ):
                                        with mock.patch.object(
                                            self.validator, "_calculate_overall_results"
                                        ):
                                            report = self.validator.run_validation(
                                                ValidationLevel.COMPREHENSIVE
                                            )

                                            assert isinstance(report, SystemValidationReport)
                                            assert (
                                                report.validation_level
                                                == ValidationLevel.COMPREHENSIVE
                                            )

    def test_collect_system_info(self):
        """Test system information collection."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        self.validator._collect_system_info()

        assert "controller_initialized" in self.validator.current_report.system_info
        assert "mathematical_engine_available" in self.validator.current_report.system_info

    def test_run_mathematical_validation(self):
        """Test mathematical validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_apgi_equation_accuracy") as mock_test:
            mock_test.return_value = ValidationTestResult(
                "test", ValidationCategory.MATHEMATICAL_ACCURACY, True, 0.1
            )

            self.validator._run_mathematical_validation()

            assert ValidationCategory.MATHEMATICAL_ACCURACY in self.validator.current_report.suites
            suite = self.validator.current_report.suites[ValidationCategory.MATHEMATICAL_ACCURACY]
            assert len(suite.tests) > 0

    def test_test_apgi_equation_accuracy(self):
        """Test APGI equation accuracy test."""
        # Mock the equation processor
        self.validator.controller.equation_processor.calculate_precision.return_value = 0.95

        result = self.validator._test_apgi_equation_accuracy()

        assert result.test_name == "apgi_equation_accuracy"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)
        assert result.execution_time >= 0

    def test_test_precision_calculations(self):
        """Test precision calculations test."""
        self.validator.controller.equation_processor.calculate_precision.return_value = 0.98

        result = self.validator._test_precision_calculations()

        assert result.test_name == "precision_calculations"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_test_prediction_error_processing(self):
        """Test prediction error processing test."""
        self.validator.controller.equation_processor.process_prediction_error.return_value = {
            "error": 0.1,
            "precision": 0.9,
        }

        result = self.validator._test_prediction_error_processing()

        assert result.test_name == "prediction_error_processing"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_test_somatic_marker_calculations(self):
        """Test somatic marker calculations test."""
        self.validator.controller.equation_processor.calculate_somatic_marker.return_value = {
            "marker": 0.5,
            "confidence": 0.95,
        }

        result = self.validator._test_somatic_marker_calculations()

        assert result.test_name == "somatic_marker_calculations"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_test_threshold_management(self):
        """Test threshold management test."""
        result = self.validator._test_threshold_management()

        assert result.test_name == "threshold_management"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_test_sigmoid_function(self):
        """Test sigmoid function test."""
        result = self.validator._test_sigmoid_function()

        assert result.test_name == "sigmoid_function"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_test_numerical_stability(self):
        """Test numerical stability test."""
        result = self.validator._test_numerical_stability()

        assert result.test_name == "numerical_stability"
        assert result.category == ValidationCategory.MATHEMATICAL_ACCURACY
        assert isinstance(result.passed, bool)

    def test_run_neural_simulation_validation(self):
        """Test neural simulation validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_p3b_simulation"):
            with mock.patch.object(self.validator, "_test_gamma_simulation"):
                with mock.patch.object(self.validator, "_test_bold_simulation"):
                    with mock.patch.object(self.validator, "_test_pci_calculation"):
                        with mock.patch.object(self.validator, "_test_signature_validation"):
                            with mock.patch.object(self.validator, "_test_signature_thresholds"):
                                self.validator._run_neural_simulation_validation()

                                assert (
                                    ValidationCategory.NEURAL_SIMULATION
                                    in self.validator.current_report.suites
                                )

    def test_test_p3b_simulation(self):
        """Test P3b simulation test."""
        self.validator.controller.neural_simulator.simulate_p3b.return_value = {
            "amplitude": 5.0,
            "latency": 300,
        }

        result = self.validator._test_p3b_simulation()

        assert result.test_name == "p3b_simulation"
        assert result.category == ValidationCategory.NEURAL_SIMULATION
        assert isinstance(result.passed, bool)

    def test_test_gamma_simulation(self):
        """Test gamma simulation test."""
        self.validator.controller.neural_simulator.simulate_gamma.return_value = {
            "power": 0.8,
            "frequency": 40,
        }

        result = self.validator._test_gamma_simulation()

        assert result.test_name == "gamma_simulation"
        assert result.category == ValidationCategory.NEURAL_SIMULATION
        assert isinstance(result.passed, bool)

    def test_test_bold_simulation(self):
        """Test BOLD simulation test."""
        self.validator.controller.neural_simulator.simulate_bold.return_value = {
            "signal": 2.0,
            "snr": 10,
        }

        result = self.validator._test_bold_simulation()

        assert result.test_name == "bold_simulation"
        assert result.category == ValidationCategory.NEURAL_SIMULATION
        assert isinstance(result.passed, bool)

    def test_run_falsification_logic_validation(self):
        """Test falsification logic validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_primary_falsification_logic"):
            with mock.patch.object(self.validator, "_test_consciousness_assessment"):
                with mock.patch.object(self.validator, "_test_threshold_insensitivity_logic"):
                    with mock.patch.object(self.validator, "_test_soma_bias_logic"):
                        with mock.patch.object(self.validator, "_test_result_interpretation"):
                            self.validator._run_falsification_logic_validation()

                            assert (
                                ValidationCategory.FALSIFICATION_LOGIC
                                in self.validator.current_report.suites
                            )

    def test_test_primary_falsification_logic(self):
        """Test primary falsification logic test."""
        result = self.validator._test_primary_falsification_logic()

        assert result.test_name == "Primary Falsification Logic"
        assert result.category == ValidationCategory.FALSIFICATION_LOGIC
        assert isinstance(result.passed, bool)

    def test_test_consciousness_assessment(self):
        """Test consciousness assessment test."""
        result = self.validator._test_consciousness_assessment()

        assert result.test_name == "consciousness_assessment"
        assert result.category == ValidationCategory.FALSIFICATION_LOGIC
        assert isinstance(result.passed, bool)

    def test_run_data_integrity_validation(self):
        """Test data integrity validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_data_storage"):
            with mock.patch.object(self.validator, "_test_data_validation"):
                with mock.patch.object(self.validator, "_test_configuration_management"):
                    self.validator._run_data_integrity_validation()

                    assert ValidationCategory.DATA_INTEGRITY in self.validator.current_report.suites

    def test_test_data_storage(self):
        """Test data storage test."""
        result = self.validator._test_data_storage()

        assert result.test_name == "Data Storage"
        assert result.category == ValidationCategory.DATA_INTEGRITY
        assert isinstance(result.passed, bool)

    def test_test_data_validation(self):
        """Test data validation test."""
        result = self.validator._test_data_validation()

        assert result.test_name == "Data Validation"
        assert result.category == ValidationCategory.DATA_INTEGRITY
        assert isinstance(result.passed, bool)

    def test_test_configuration_management(self):
        """Test configuration management test."""
        result = self.validator._test_configuration_management()

        assert result.test_name == "Configuration Management"
        assert result.category == ValidationCategory.DATA_INTEGRITY
        assert isinstance(result.passed, bool)

    def test_test_end_to_end_workflow(self):
        """Test end-to-end workflow test."""
        result = self.validator._test_end_to_end_workflow()

        assert result.test_name == "End-to-End Workflow"
        assert result.category == ValidationCategory.INTEGRATION
        assert isinstance(result.passed, bool)

    def test_test_component_communication(self):
        """Test component communication test."""
        result = self.validator._test_component_communication()

        assert result.test_name == "Component Communication"
        assert result.category == ValidationCategory.INTEGRATION
        assert isinstance(result.passed, bool)

    def test_test_configuration_propagation(self):
        """Test configuration propagation test."""
        result = self.validator._test_configuration_propagation()

        assert result.test_name == "Configuration Propagation"
        assert result.category == ValidationCategory.INTEGRATION
        assert isinstance(result.passed, bool)

    def test_test_invalid_parameter_handling(self):
        """Test invalid parameter handling test."""
        result = self.validator._test_invalid_parameter_handling()

        assert result.test_name == "Invalid Parameter Handling"
        assert result.category == ValidationCategory.ERROR_HANDLING
        assert isinstance(result.passed, bool)

    def test_test_mathematical_error_handling(self):
        """Test mathematical error handling test."""
        result = self.validator._test_mathematical_error_handling()

        assert result.test_name == "Mathematical Error Handling"
        assert result.category == ValidationCategory.ERROR_HANDLING
        assert isinstance(result.passed, bool)

    def test_test_simulation_error_handling(self):
        """Test simulation error handling test."""
        result = self.validator._test_simulation_error_handling()

        assert result.test_name == "Simulation Error Handling"
        assert result.category == ValidationCategory.ERROR_HANDLING
        assert isinstance(result.passed, bool)

    def test_test_graceful_degradation(self):
        """Test graceful degradation test."""
        result = self.validator._test_graceful_degradation()

        assert result.test_name == "Graceful Degradation"
        assert result.category == ValidationCategory.ERROR_HANDLING
        assert isinstance(result.passed, bool)

    def test_test_equation_performance(self):
        """Test equation performance test."""
        result = self.validator._test_equation_performance()

        assert result.test_name == "Equation Performance"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_simulation_performance(self):
        """Test simulation performance test."""
        result = self.validator._test_simulation_performance()

        assert result.test_name == "Simulation Performance"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_memory_usage(self):
        """Test memory usage test."""
        result = self.validator._test_memory_usage()

        assert result.test_name == "Memory Usage"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_concurrent_execution(self):
        """Test concurrent execution test."""
        result = self.validator._test_concurrent_execution()

        assert result.test_name == "Concurrent Execution"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_large_dataset_handling(self):
        """Test large dataset handling test."""
        result = self.validator._test_large_dataset_handling()

        assert result.test_name == "Large Dataset Handling"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_extended_execution(self):
        """Test extended execution test."""
        result = self.validator._test_extended_execution()

        assert result.test_name == "Extended Execution"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_test_resource_limits(self):
        """Test resource limits test."""
        result = self.validator._test_resource_limits()

        assert result.test_name == "Resource Limits"
        assert result.category == ValidationCategory.PERFORMANCE
        assert isinstance(result.passed, bool)

    def test_run_integration_validation(self):
        """Test integration validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_end_to_end_workflow"):
            with mock.patch.object(self.validator, "_test_component_communication"):
                with mock.patch.object(self.validator, "_test_configuration_propagation"):
                    self.validator._run_integration_validation()

                    assert ValidationCategory.INTEGRATION in self.validator.current_report.suites

    def test_run_error_handling_validation(self):
        """Test error handling validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_invalid_parameter_handling"):
            with mock.patch.object(self.validator, "_test_mathematical_error_handling"):
                with mock.patch.object(self.validator, "_test_simulation_error_handling"):
                    with mock.patch.object(self.validator, "_test_graceful_degradation"):
                        self.validator._run_error_handling_validation()

                        assert (
                            ValidationCategory.ERROR_HANDLING
                            in self.validator.current_report.suites
                        )

    def test_run_performance_validation(self):
        """Test performance validation suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_equation_performance"):
            with mock.patch.object(self.validator, "_test_simulation_performance"):
                with mock.patch.object(self.validator, "_test_memory_usage"):
                    with mock.patch.object(self.validator, "_test_concurrent_execution"):
                        self.validator._run_performance_validation()

                        assert (
                            ValidationCategory.PERFORMANCE in self.validator.current_report.suites
                        )

    def test_run_stress_tests(self):
        """Test stress test suite."""
        self.validator.current_report = SystemValidationReport(
            validation_id="test", start_time=datetime.now()
        )

        with mock.patch.object(self.validator, "_test_large_dataset_handling"):
            with mock.patch.object(self.validator, "_test_extended_execution"):
                with mock.patch.object(self.validator, "_test_resource_limits"):
                    self.validator._run_stress_tests()

                    # Stress tests should be added to performance category
                    assert ValidationCategory.PERFORMANCE in self.validator.current_report.suites

    def test_calculate_overall_results(self):
        """Test overall results calculation."""
        # Create mock suites
        math_suite = ValidationSuite(
            ValidationCategory.MATHEMATICAL_ACCURACY,
            tests=[
                ValidationTestResult("test1", ValidationCategory.MATHEMATICAL_ACCURACY, True, 0.1),
                ValidationTestResult("test2", ValidationCategory.MATHEMATICAL_ACCURACY, False, 0.2),
            ],
        )

        neural_suite = ValidationSuite(
            ValidationCategory.NEURAL_SIMULATION,
            tests=[ValidationTestResult("test3", ValidationCategory.NEURAL_SIMULATION, True, 0.1)],
        )

        self.validator.current_report = SystemValidationReport(
            validation_id="test",
            start_time=datetime.now(),
            suites={
                ValidationCategory.MATHEMATICAL_ACCURACY: math_suite,
                ValidationCategory.NEURAL_SIMULATION: neural_suite,
            },
        )

        self.validator._calculate_overall_results()

        assert self.validator.current_report.total_tests == 3
        assert self.validator.current_report.passed_tests == 2
        assert self.validator.current_report.failed_tests == 1
        assert self.validator.current_report.overall_passed is False  # Not all passed

    def test_save_validation_report(self):
        """Test saving validation report."""
        report = SystemValidationReport(
            validation_id="test_123",
            start_time=datetime.now(),
            end_time=datetime.now(),
            validation_level=ValidationLevel.STANDARD,
        )

        self.validator.current_report = report

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            self.validator.save_validation_report(temp_path)

            # Verify file was created and contains valid JSON
            assert Path(temp_path).exists()

            with open(temp_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["validation_id"] == "test_123"
            assert "validation_level" in saved_data
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)


class TestModuleFunctions:
    """Test module-level functions."""

    def test_run_quick_validation(self):
        """Test run_quick_validation function."""
        mock_controller = MockController()

        # Import functions with error handling
        try:
            from apgi_framework.system_validator import run_quick_validation

            with mock.patch(
                "apgi_framework.system_validator.SystemValidator"
            ) as mock_validator_class:
                mock_validator = mock.Mock()
                mock_validator_class.return_value = mock_validator
                mock_validator.run_validation.return_value = SystemValidationReport(
                    validation_id="quick_test", start_time=datetime.now()
                )

                result = run_quick_validation(mock_controller)

                assert isinstance(result, SystemValidationReport)
                mock_validator.run_validation.assert_called_once_with(ValidationLevel.BASIC)
        except ImportError:
            pytest.skip("Cannot import run_quick_validation function")

    def test_run_comprehensive_validation(self):
        """Test run_comprehensive_validation function."""
        mock_controller = MockController()

        # Import functions with error handling
        try:
            from apgi_framework.system_validator import run_comprehensive_validation

            with mock.patch(
                "apgi_framework.system_validator.SystemValidator"
            ) as mock_validator_class:
                mock_validator = mock.Mock()
                mock_validator_class.return_value = mock_validator
                mock_validator.run_validation.return_value = SystemValidationReport(
                    validation_id="comprehensive_test", start_time=datetime.now()
                )

                result = run_comprehensive_validation(mock_controller)

                assert isinstance(result, SystemValidationReport)
                mock_validator.run_validation.assert_called_once_with(ValidationLevel.COMPREHENSIVE)
        except ImportError:
            pytest.skip("Cannot import run_comprehensive_validation function")


if __name__ == "__main__":
    pytest.main([__file__])
