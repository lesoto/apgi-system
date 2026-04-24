"""
Comprehensive tests for data/dashboard.py module.

Tests for ExperimentMonitor class (the actual class in dashboard.py).
"""

import pytest


class TestDashboardImports:
    """Test module imports."""

    def test_module_imports(self):
        """Test that dashboard module can be imported."""
        from apgi_framework.data import dashboard

        assert hasattr(dashboard, "ExperimentMonitor")
        assert hasattr(dashboard, "ExperimentComparator")
        assert hasattr(dashboard, "DashboardServer")


class TestExperimentMonitorInitialization:
    """Test ExperimentMonitor initialization."""

    def test_basic_initialization(self):
        """Test basic monitor initialization."""
        from apgi_framework.data.dashboard import ExperimentMonitor

        monitor = ExperimentMonitor()
        assert monitor.experiments == {}
        assert monitor.is_monitoring is False
        assert monitor.update_interval == 1.0

    def test_initialization_with_custom_interval(self):
        """Test initialization with custom update interval."""
        from apgi_framework.data.dashboard import ExperimentMonitor

        monitor = ExperimentMonitor(update_interval=2.5)
        assert monitor.update_interval == 2.5


class TestExperimentMonitorRegistration:
    """Test experiment registration."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor instance for testing."""
        from apgi_framework.data.dashboard import ExperimentMonitor

        return ExperimentMonitor()

    def test_register_experiment(self, monitor):
        """Test registering an experiment for monitoring."""
        metadata = {
            "experiment_name": "Test Experiment",
            "total_trials": 100,
            "researcher": "Test Researcher",
        }

        monitor.register_experiment("exp_001", metadata)
        assert "exp_001" in monitor.experiments
        assert monitor.experiments["exp_001"]["metadata"] == metadata
        assert monitor.experiments["exp_001"]["status"] == "running"

    def test_update_experiment_progress(self, monitor):
        """Test updating experiment progress."""
        monitor.register_experiment("exp_001", {"total_trials": 100})

        monitor.update_experiment_progress("exp_001", 50)
        assert monitor.experiments["exp_001"]["current_trial"] == 50
        # Progress is calculated as current_trial / total_trials
        assert monitor.experiments["exp_001"]["progress"] == 0.5

    def test_complete_experiment(self, monitor):
        """Test marking experiment as complete."""
        monitor.register_experiment("exp_001", {"total_trials": 100})

        monitor.complete_experiment("exp_001")
        assert monitor.experiments["exp_001"]["status"] == "completed"

    def test_add_trial_result(self, monitor):
        """Test adding trial result to experiment via update_experiment_progress."""
        from apgi_framework.core.data_models import ExperimentalTrial

        monitor.register_experiment("exp_001", {"total_trials": 100})

        trial = ExperimentalTrial(trial_id="trial_001", condition="test")
        monitor.update_experiment_progress("exp_001", 1, new_trials=[trial])

        assert len(monitor.experiments["exp_001"]["trials"]) == 1


class TestExperimentMonitorQueries:
    """Test experiment query methods."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor with sample experiments."""
        from apgi_framework.data.dashboard import ExperimentMonitor

        monitor = ExperimentMonitor()
        monitor.register_experiment(
            "exp_001", {"experiment_name": "Visual Task", "total_trials": 50}
        )
        monitor.register_experiment(
            "exp_002", {"experiment_name": "Memory Task", "total_trials": 100}
        )
        return monitor

    def test_get_experiment_status(self, monitor):
        """Test getting experiment status."""
        status = monitor.get_experiment_status("exp_001")
        assert isinstance(status, dict)
        assert status["id"] == "exp_001"
        assert "status" in status

    def test_get_all_experiments(self, monitor):
        """Test getting all experiments."""
        experiments = monitor.get_all_experiments()
        assert isinstance(experiments, dict)
        assert len(experiments) == 2

    def test_get_running_experiments(self, monitor):
        """Test getting running experiments."""
        # Get all experiments and filter for running status
        all_exps = monitor.get_all_experiments()
        running = [eid for eid, exp in all_exps.items() if exp.get("status") == "running"]
        assert isinstance(running, list)
        assert len(running) == 2  # Both are running initially


class TestExperimentComparator:
    """Test ExperimentComparator functionality."""

    @pytest.fixture
    def comparator(self):
        """Create a comparator instance."""
        from apgi_framework.data.dashboard import ExperimentComparator

        return ExperimentComparator()

    def test_initialization(self, comparator):
        """Test comparator initialization."""
        assert comparator is not None

    def test_compare_experiments(self, comparator):
        """Test comparing experiments."""
        from apgi_framework.core.data_models import FalsificationResult

        exp1 = FalsificationResult(test_id="t1", is_falsified=False)
        exp2 = FalsificationResult(test_id="t2", is_falsified=True)

        experiments = {
            "exp_001": {"status": "completed", "results": [exp1], "metadata": {}},
            "exp_002": {"status": "completed", "results": [exp2], "metadata": {}},
        }

        result = comparator.compare_experiments(experiments)
        assert isinstance(result, dict)
        assert "summary" in result
        assert "statistical_comparison" in result


class TestDashboardServer:
    """Test DashboardServer functionality."""

    def test_server_initialization(self):
        """Test server initialization."""
        from apgi_framework.data.dashboard import DashboardServer

        server = DashboardServer(port=8080)
        assert server.port == 8080
