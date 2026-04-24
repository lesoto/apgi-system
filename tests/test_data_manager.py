"""
Comprehensive tests for apgi_framework.data.data_manager module.

This module provides test coverage for the IntegratedDataManager class
and related data management functionality.
"""

import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestIntegratedDataManager:
    """Test cases for IntegratedDataManager class."""

    def test_init_with_default_params(self):
        """Test initialization with default parameters."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,  # Skip dashboard for testing
                    dashboard_port=8080,
                )

                assert manager.base_output_dir == Path(temp_dir)
                assert manager.enable_dashboard is False
                assert manager.active_experiments == {}

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")

    def test_init_creates_directories(self):
        """Test that initialization creates necessary directories."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                # Check that base directory was created
                assert Path(temp_dir).exists()

                # Check that subdirectories were set up
                assert (Path(temp_dir) / "reports").exists()
                assert (Path(temp_dir) / "exports").exists()
                assert (Path(temp_dir) / "figures").exists()

                # Check manager properties
                assert manager.base_output_dir == Path(temp_dir)
                assert not manager.enable_dashboard

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")

    def test_register_experiment(self):
        """Test experiment registration."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                experiment_id = "test_experiment_001"
                metadata = {
                    "name": "Test Experiment",
                    "type": "psychophysical",
                    "participants": 20,
                }

                result = manager.register_experiment(experiment_id, metadata)

                assert result == experiment_id
                assert experiment_id in manager.active_experiments
                assert manager.active_experiments[experiment_id]["status"] == "registered"

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")

    def test_register_duplicate_experiment(self):
        """Test registering duplicate experiment raises error."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager
            from apgi_framework.exceptions import DataManagementError

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                experiment_id = "duplicate_test"
                metadata = {"name": "Test"}

                # First registration should succeed
                manager.register_experiment(experiment_id, metadata)

                # Second registration should raise error
                with pytest.raises(DataManagementError):
                    manager.register_experiment(experiment_id, metadata)

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_update_experiment_status(self):
        """Test updating experiment status."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                experiment_id = "status_test"
                metadata = {"name": "Status Test"}

                manager.register_experiment(experiment_id, metadata)

                # Update status
                manager.update_experiment_status(experiment_id, "running")
                assert manager.active_experiments[experiment_id]["status"] == "running"

                # Update progress
                manager.update_experiment_progress(experiment_id, 50)
                assert manager.active_experiments[experiment_id]["progress"] == 50

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")

    def test_complete_experiment(self):
        """Test completing an experiment."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                experiment_id = "complete_test"
                metadata = {"name": "Complete Test"}
                results = {"accuracy": 0.95, "trials": 100}

                manager.register_experiment(experiment_id, metadata)
                manager.complete_experiment(experiment_id, results)

                assert manager.active_experiments[experiment_id]["status"] == "completed"
                assert "results" in manager.active_experiments[experiment_id]
                assert manager.active_experiments[experiment_id]["results"] == results

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")


class TestDataManagerComponents:
    """Test individual data manager components."""

    def test_data_exporter_initialization(self):
        """Test DataExporter component initialization."""
        try:
            from apgi_framework.data.data_exporter import DataExporter

            with tempfile.TemporaryDirectory() as temp_dir:
                exporter = DataExporter(temp_dir)
                assert exporter is not None
                assert exporter.export_dir == Path(temp_dir)

        except ImportError as e:
            pytest.skip(f"DataExporter not available: {e}")

    def test_report_generator_initialization(self):
        """Test ReportGenerator component initialization."""
        try:
            from apgi_framework.data.report_generator import ReportGenerator

            with tempfile.TemporaryDirectory() as temp_dir:
                generator = ReportGenerator(temp_dir)
                assert generator is not None
                assert generator.output_dir == Path(temp_dir)

        except ImportError as e:
            pytest.skip(f"ReportGenerator not available: {e}")

    def test_visualizer_initialization(self):
        """Test APGIVisualizer component initialization."""
        try:
            from apgi_framework.data.visualizer import APGIVisualizer

            with tempfile.TemporaryDirectory() as temp_dir:
                visualizer = APGIVisualizer(temp_dir)
                assert visualizer is not None
                assert visualizer.output_dir == Path(temp_dir)

        except ImportError as e:
            pytest.skip(f"APGIVizualizer not available: {e}")


class TestDataManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_experiment_id(self):
        """Test handling of invalid experiment IDs."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager
            from apgi_framework.exceptions import DataManagementError

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                # Empty experiment ID should raise error
                with pytest.raises(DataManagementError):
                    manager.register_experiment("", {"name": "Test"})

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_experiment_not_found(self):
        """Test handling of non-existent experiment."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager
            from apgi_framework.exceptions import DataManagementError

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                # Updating non-existent experiment should raise error
                with pytest.raises(DataManagementError):
                    manager.update_experiment_status("non_existent", "running")

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_invalid_metadata(self):
        """Test handling of invalid metadata."""
        try:
            from apgi_framework.data.data_manager import IntegratedDataManager

            with tempfile.TemporaryDirectory() as temp_dir:
                manager = IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                # None metadata should be handled gracefully
                experiment_id = "invalid_meta"
                result = manager.register_experiment(experiment_id, None)

                assert result == experiment_id
                assert experiment_id in manager.active_experiments

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")


class TestDataExportOperations:
    """Test data export operations."""

    def test_export_to_csv(self):
        """Test CSV export functionality."""
        try:
            import pandas as pd
            from apgi_framework.data.data_exporter import DataExporter

            with tempfile.TemporaryDirectory() as temp_dir:
                exporter = DataExporter(temp_dir)

                # Create test data
                test_data = pd.DataFrame(
                    {
                        "participant_id": [1, 2, 3],
                        "accuracy": [0.9, 0.85, 0.92],
                        "reaction_time": [500, 600, 450],
                    }
                )

                result = exporter.export_to_csv(test_data, "test_export.csv")

                assert result is not None
                export_path = Path(temp_dir) / "test_export.csv"
                assert export_path.exists()

                # Verify exported data
                imported_data = pd.read_csv(export_path)
                assert len(imported_data) == 3
                assert list(imported_data.columns) == [
                    "participant_id",
                    "accuracy",
                    "reaction_time",
                ]

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_export_to_json(self):
        """Test JSON export functionality."""
        try:
            import pandas as pd
            import json
            from apgi_framework.data.data_exporter import DataExporter

            with tempfile.TemporaryDirectory() as temp_dir:
                exporter = DataExporter(temp_dir)

                test_data = pd.DataFrame(
                    {
                        "participant_id": [1, 2],
                        "score": [95, 87],
                    }
                )

                result = exporter.export_to_json(
                    test_data.to_dict(orient="records"), "test_export.json"
                )

                assert result is not None
                export_path = Path(temp_dir) / "test_export.json"
                assert export_path.exists()

                # Verify JSON structure
                with open(export_path, "r") as f:
                    loaded_data = json.load(f)
                    assert len(loaded_data) == 2

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")

    def test_export_empty_dataframe(self):
        """Test exporting empty DataFrame."""
        try:
            import pandas as pd
            from apgi_framework.data.data_exporter import DataExporter

            with tempfile.TemporaryDirectory() as temp_dir:
                exporter = DataExporter(temp_dir)

                empty_df = pd.DataFrame()
                result = exporter.export_to_csv(empty_df, "empty.csv")

                # Should handle empty DataFrame gracefully (returns filepath)
                assert result is not None

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
