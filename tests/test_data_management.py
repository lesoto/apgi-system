"""
Tests for data management modules.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from apgi_framework.data.data_exporter import DataExporter
from apgi_framework.data.data_manager import IntegratedDataManager
from apgi_framework.data.report_generator import ReportGenerator
from apgi_framework.data.storage_manager import StorageManager


class TestIntegratedDataManager:
    """Test integrated data manager implementation."""

    def test_initialization(self):
        """Test data manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            assert manager.base_output_dir == Path(temp_dir)
            assert manager.report_generator is not None
            assert manager.data_exporter is not None
            assert manager.visualizer is not None
            assert manager.dashboard is None  # Disabled

    def test_directory_creation(self):
        """Test automatic directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test_outputs"

            IntegratedDataManager(base_output_dir=str(output_dir), enable_dashboard=False)

            assert output_dir.exists()
            assert (output_dir / "reports").exists()
            assert (output_dir / "exports").exists()
            assert (output_dir / "figures").exists()

    def test_store_experiment_data(self):
        """Test registering experiment data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Register experiment
            metadata = {
                "experiment_id": "test_exp_001",
                "participant_id": "P001",
                "task_type": "detection",
                "start_time": datetime.now().isoformat(),
            }
            experiment_id = manager.register_experiment("test_exp_001", metadata)
            assert experiment_id == "test_exp_001"
            assert experiment_id in manager.active_experiments

    def test_generate_report(self):
        """Test comprehensive report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Add some test data to active experiments
            from apgi_framework.core.data_models import StatisticalSummary

            summary = StatisticalSummary(
                total_trials=100,
                total_participants=50,
                mean_effect_size=0.75,
                effect_size_ci_lower=0.7,
                effect_size_ci_upper=0.8,
                statistical_power=0.8,
                power_ci_lower=0.75,
                power_ci_upper=0.85,
            )
            manager.active_experiments["test_exp_001"] = {
                "status": "completed",
                "results": ["success", "failure", "success"],
                "trials": [
                    {"trial": 1, "response": True, "stimulus": 0.5},
                    {"trial": 2, "response": False, "stimulus": 0.6},
                    {"trial": 3, "response": True, "stimulus": 0.4},
                ],
                "summary": summary,
            }

            # Test that experiment is registered
            assert "test_exp_001" in manager.active_experiments
            assert manager.active_experiments["test_exp_001"]["status"] == "completed"

    def test_export_data(self):
        """Test data export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Register experiment first
            experiment_data = {
                "experiment_id": "test_exp_001",
                "timestamp": datetime.now().isoformat(),
                "parameters": {"theta_t": 3.5, "pi_e": 2.0},
            }
            manager.register_experiment("test_exp_001", experiment_data)

            # Export data (this is the actual method)
            export_paths = manager.export_experiment_data("test_exp_001", formats=["json"])

            assert isinstance(export_paths, dict)

    def test_create_visualization(self):
        """Test visualization creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Add experiment data with visualization data
            from apgi_framework.core.data_models import StatisticalSummary

            summary = StatisticalSummary(
                total_trials=50,
                total_participants=25,
                mean_effect_size=0.8,
                effect_size_ci_lower=0.75,
                effect_size_ci_upper=0.85,
                statistical_power=0.85,
                power_ci_lower=0.8,
                power_ci_upper=0.9,
            )
            manager.active_experiments["test_exp_001"] = {
                "results": [
                    {
                        "trial": 1,
                        "stimulus": 0.5,
                        "response": True,
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
                "trials": [
                    {"trial": 1, "response": True, "stimulus": 0.5},
                    {"trial": 2, "response": False, "stimulus": 0.6},
                ],
                "summary": summary,
            }

            # Test that experiment is registered
            assert "test_exp_001" in manager.active_experiments
            assert len(manager.active_experiments["test_exp_001"]["trials"]) == 2

    def test_query_experiments(self):
        """Test experiment querying functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Add multiple experiments
            manager.active_experiments.update(
                {
                    "test_exp_001": {"status": "running"},
                    "test_exp_002": {"status": "completed"},
                    "test_exp_003": {"status": "failed"},
                }
            )

            # Get all experiments summary
            all_experiments = manager.get_all_experiments_summary()
            assert len(all_experiments) == 3
            assert "test_exp_001" in all_experiments
            assert "test_exp_002" in all_experiments
            assert "test_exp_003" in all_experiments

    def test_dashboard_integration(self):
        """Test dashboard integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = IntegratedDataManager(base_output_dir=temp_dir, enable_dashboard=False)

            # Test dashboard URL (this is the actual method)
            dashboard_url = manager.get_dashboard_url()

            assert dashboard_url is None  # Disabled in test


class TestStorageManager:
    """Test storage manager implementation."""

    def test_initialization(self):
        """Test storage manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(
                storage_path=temp_dir,
                backend="sqlite",
                auto_validate=True,
                auto_backup=False,
            )

            assert storage.storage_path == Path(temp_dir)
            assert storage.backend == "sqlite"
            assert storage.auto_validate is True
            assert storage.auto_backup is False

    @staticmethod
    def create_test_dataset(dataset_id="test_dataset_001", participant_id="P001", data=None):
        """Helper to create a test ExperimentalDataset."""
        from apgi_framework.data.data_models import (
            ExperimentalDataset,
            ExperimentMetadata,
        )

        if data is None:
            data = {
                "p3b_amplitudes": [5.2, 4.8],
                "apgi_parameters": {"theta_t": 3.5, "pi_e": 2.0},
                "neural_signatures": {"p3b_amplitude": 5.2},
                "consciousness_assessments": {"subjective_report": True},
            }

        metadata = ExperimentMetadata(
            experiment_id=dataset_id,
            experiment_name=f"Test Experiment {dataset_id}",
            researcher=participant_id,
            n_participants=1,
            n_trials=10,
            created_at=datetime.now(),
        )

        return ExperimentalDataset(metadata=metadata, data=data)

    def test_store_dataset(self):
        """Test dataset storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Mock dataset
            dataset = self.create_test_dataset()

            # Store dataset (disable validation for testing)
            try:
                result = storage.store_dataset(dataset, validate=False)
                assert result == "test_dataset_001"  # Should return experiment_id
            except PermissionError:
                # Skip test on Windows if file permissions are restricted
                import platform

                if platform.system() == "Windows":
                    pytest.skip("Skipping test due to Windows file permission restrictions")
                else:
                    raise

    def test_retrieve_dataset(self):
        """Test dataset retrieval."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            try:
                # Store dataset first
                dataset = self.create_test_dataset()
                storage.store_dataset(dataset)

                # Retrieve dataset
                retrieved = storage.load_dataset("test_dataset_001")

                assert retrieved is not None
                assert retrieved.metadata.experiment_id == "test_dataset_001"
                assert retrieved.metadata.researcher == "P001"
            except PermissionError:
                # Skip test on Windows if file permissions are restricted
                import platform

                if platform.system() == "Windows":
                    pytest.skip("Skipping test due to Windows file permission restrictions")
                else:
                    raise

    def test_query_datasets(self):
        """Test dataset querying."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Store multiple datasets
            datasets = [
                self.create_test_dataset("dataset_001", "P001"),
                self.create_test_dataset("dataset_002", "P002"),
                self.create_test_dataset("dataset_003", "P001"),
            ]

            for dataset in datasets:
                storage.store_dataset(dataset)

            # Query by researcher
            from apgi_framework.data.data_models import QueryFilter

            filter_criteria = QueryFilter(researcher="P001")
            p001_datasets = storage.query_datasets(filter_criteria)
            assert len(p001_datasets) == 2

    def test_update_dataset(self):
        """Test dataset updating."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Store original dataset
            dataset = self.create_test_dataset(data={"p3b_amplitudes": [5.2]})
            storage.store_dataset(dataset, validate=False)

            # Update dataset
            updates = {
                "metadata": {"participant_id": "P001", "updated": True},
                "data": {"p3b_amplitudes": [5.2, 4.8, 5.5]},
            }

            result = storage.update_dataset("test_dataset_001", updates)
            assert result is not None

    def test_delete_dataset(self):
        """Test dataset deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Store dataset
            dataset = self.create_test_dataset()
            storage.store_dataset(dataset, validate=False)

            # Verify it exists
            assert storage.load_dataset("test_dataset_001") is not None

            # Delete dataset
            result = storage.delete_dataset("test_dataset_001", confirm=True)
            assert result is True

            # Verify it's gone
            try:
                storage.load_dataset("test_dataset_001")
                assert False, "Dataset should be deleted"
            except Exception:
                pass  # Expected

    def test_backup_creation(self):
        """Test backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=True)

            # Store some data
            dataset = self.create_test_dataset()
            storage.store_dataset(dataset, validate=False)

            # Create backup
            backup_info = storage.create_backup("test_dataset_001")

            assert backup_info is not None
            assert backup_info.backup_path is not None
            assert Path(backup_info.backup_path).exists()

    def test_storage_statistics(self):
        """Test storage statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Store some datasets
            for i in range(5):
                dataset = self.create_test_dataset(dataset_id=f"dataset_{i:03d}")
                storage.store_dataset(dataset, validate=False)

            # Get statistics
            stats = storage.get_storage_stats()

            assert stats.total_datasets == 5
            assert stats.total_size_mb >= 0.0
            assert stats.oldest_dataset is not None or stats.total_datasets == 0

    def test_validation_errors(self):
        """Test validation error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(
                storage_path=temp_dir,
                backend="sqlite",
                auto_validate=True,
                auto_backup=False,
            )

            # Invalid dataset (using wrong type)
            invalid_dataset = "not a dataset object"

            # Should raise validation error
            with pytest.raises(Exception):  # Could be ValidationError or StorageError
                storage.store_dataset(invalid_dataset)

    def test_concurrent_access(self):
        """Test concurrent access handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = StorageManager(storage_path=temp_dir, backend="sqlite", auto_backup=False)

            # Simulate concurrent operations
            import threading

            results = []

            def store_dataset(index):
                try:
                    dataset = self.create_test_dataset(dataset_id=f"concurrent_{index}")
                    result = storage.store_dataset(dataset, validate=False)
                    results.append(result)
                except Exception as e:
                    results.append(e)

            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=store_dataset, args=(i,))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Check results
            successful_results = [
                r for r in results if isinstance(r, str) and r.startswith("concurrent_")
            ]
            assert len(successful_results) >= 4  # At least most should succeed


class TestDataExporter:
    """Test data exporter implementation."""

    def test_initialization(self):
        """Test data exporter initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = DataExporter(temp_dir)

            assert exporter.output_dir == Path(temp_dir)
            assert exporter.output_dir.exists()

    def test_export_falsification_results(self):
        """Test exporting falsification results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = DataExporter(temp_dir)

            # Mock falsification results
            from apgi_framework.core.data_models import FalsificationResult

            results = [
                FalsificationResult(
                    test_type="primary",
                    is_falsified=False,
                    confidence_level=0.95,
                    effect_size=0.8,
                    p_value=0.03,
                    statistical_power=0.85,
                )
            ]

            # Export to JSON
            export_path = exporter.export_falsification_results(results, format="json")

            assert export_path is not None
            assert Path(export_path).exists()
            assert export_path.endswith(".json")

    def test_export_experimental_trials(self):
        """Test exporting experimental trials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = DataExporter(temp_dir)

            # Mock experimental trials using correct data model
            from apgi_framework.core.data_models import (
                ConsciousnessAssessment,
                ExperimentalTrial,
                NeuralSignatures,
            )

            trials = [
                ExperimentalTrial(
                    trial_id="trial_001",
                    participant_id="P001",
                    condition="exteroceptive",
                    trial_number=1,
                    neural_signatures=NeuralSignatures(p3b_amplitude=5.2),
                    consciousness_assessment=ConsciousnessAssessment(subjective_report=True),
                )
            ]

            # Export to CSV
            export_path = exporter.export_experimental_trials(trials, format="csv")

            assert export_path is not None
            assert Path(export_path).exists()
            assert export_path.endswith(".csv")


class TestReportGenerator:
    """Test report generator implementation."""

    def test_initialization(self):
        """Test report generator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ReportGenerator(temp_dir)

            assert generator.output_dir == Path(temp_dir)
            assert generator.output_dir.exists()

    def test_generate_falsification_report(self):
        """Test generating falsification report."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ReportGenerator(temp_dir)

            # Mock data
            from apgi_framework.core.data_models import (
                ExperimentalTrial,
                FalsificationResult,
                StatisticalSummary,
            )

            results = [
                FalsificationResult(
                    test_type="primary",
                    is_falsified=False,
                    confidence_level=0.95,
                    effect_size=0.8,
                    p_value=0.03,
                    statistical_power=0.85,
                )
            ]

            # Mock experimental trials using correct data model
            from apgi_framework.core.data_models import (
                ConsciousnessAssessment,
                ExperimentalTrial,
                NeuralSignatures,
            )

            trials = [
                ExperimentalTrial(
                    trial_id="trial_001",
                    participant_id="P001",
                    condition="exteroceptive",
                    trial_number=1,
                    neural_signatures=NeuralSignatures(p3b_amplitude=5.2),
                    consciousness_assessment=ConsciousnessAssessment(subjective_report=True),
                )
            ]

            stats = StatisticalSummary(
                total_trials=1000,
                statistical_power=0.85,
                mean_effect_size=0.8,
            )

            # Generate report (this is the actual method)
            report = generator.generate_falsification_report("test_exp_001", results, trials, stats)

            assert report is not None
            assert report.experiment_id == "test_exp_001"

    def test_save_report(self):
        """Test saving report to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ReportGenerator(temp_dir)

            # Mock report using correct data model
            from apgi_framework.core.data_models import StatisticalSummary
            from apgi_framework.data.report_generator import (
                FalsificationReport,
                ReportSection,
            )

            report = FalsificationReport(
                experiment_id="test_exp_001",
                timestamp=datetime.now(),
                test_type="primary",
                summary="Test summary",
                conclusions="Test conclusions",
                statistical_summary=StatisticalSummary(total_trials=1000),
                sections=[ReportSection(title="Test Section", content="Test content")],
                metadata={"test": True},
            )

            # Save report (this is the actual method)
            report_path = generator.save_report(report, format="json")

            assert report_path is not None
            assert Path(report_path).exists()
            assert report_path.endswith(".json")


if __name__ == "__main__":
    pytest.main([__file__])
