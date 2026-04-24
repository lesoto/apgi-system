"""
Comprehensive tests for apgi_framework.data.data_manager module.

This module provides test coverage for the IntegratedDataManager class.
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
                    enable_dashboard=False,
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
                IntegratedDataManager(
                    base_output_dir=temp_dir,
                    enable_dashboard=False,
                )

                assert Path(temp_dir).exists()
                assert (Path(temp_dir) / "reports").exists()
                assert (Path(temp_dir) / "exports").exists()
                assert (Path(temp_dir) / "figures").exists()

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
                metadata = {"name": "Test Experiment", "type": "psychophysical"}

                result = manager.register_experiment(experiment_id, metadata)

                assert result == experiment_id
                assert experiment_id in manager.active_experiments

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

                manager.register_experiment(experiment_id, metadata)

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
                manager.update_experiment_status(experiment_id, "running")

                assert manager.active_experiments[experiment_id]["status"] == "running"

        except ImportError as e:
            pytest.skip(f"IntegratedDataManager not available: {e}")

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

                with pytest.raises(DataManagementError):
                    manager.update_experiment_status("non_existent", "running")

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
