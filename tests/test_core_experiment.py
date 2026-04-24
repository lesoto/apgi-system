"""
Test suite for core experiment module.

This provides coverage for the BaseExperiment class and its implementations.
"""

import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.experiment import BaseExperiment


class MockExperiment(BaseExperiment):
    """Mock experiment implementation for testing."""

    def __init__(self, n_participants: int = 20):
        super().__init__(n_participants)
        self.setup_called = False
        self.trials_run: list[Any] = []

    def setup(self, **kwargs):
        """Set up the experimental parameters."""
        self.setup_called = True
        self.experiment_params = kwargs

    def run_trial(self, participant_id: int, trial_params: dict):
        """Run a single trial of the experiment."""
        trial_data = {
            "participant_id": participant_id,
            "trial_type": trial_params.get("type", "default"),
            "response_time": trial_params.get("rt", 500),
            "correct": trial_params.get("correct", True),
        }
        self.trials_run.append(trial_data)
        return trial_data

    def run_block(self, participant_id: int, block_params: dict):
        """Run a block of trials."""
        block_trials = []
        n_trials = block_params.get("n_trials", 10)
        for trial_num in range(n_trials):
            trial = self.run_trial(participant_id, {"type": "block_trial", "trial_num": trial_num})
            block_trials.append(trial)
        return block_trials

    def run_participant(self, participant_id: int):
        """Run the experiment for a single participant."""
        # Simulate running trials for this participant
        trials = []
        for trial_num in range(5):  # 5 trials per participant
            trial_data = {
                "participant_id": participant_id,
                "trial_num": trial_num,
                "accuracy": 0.8 + (participant_id * 0.01),  # Slight learning effect
            }
            trials.append(trial_data)
        return {"trials": trials}


class TestBaseExperiment:
    """Tests for the BaseExperiment abstract class."""

    def test_base_experiment_init(self):
        """Test BaseExperiment initialization."""
        exp = MockExperiment(n_participants=10)

        assert exp.n_participants == 10
        assert exp.data.empty
        assert exp.participant_data == {}

    def test_base_experiment_default_init(self):
        """Test BaseExperiment initialization with defaults."""
        exp = MockExperiment()

        assert exp.n_participants == 20
        assert exp.data.empty

    def test_run_experiment(self):
        """Test running a full experiment."""
        exp = MockExperiment(n_participants=3)
        result = exp.run_experiment(condition="test")

        # Check setup was called
        assert exp.setup_called is True
        assert exp.experiment_params == {"condition": "test"}

        # Check all participants were run
        assert len(exp.participant_data) == 3
        assert 1 in exp.participant_data
        assert 2 in exp.participant_data
        assert 3 in exp.participant_data

        # Check data was compiled
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 15  # 3 participants * 5 trials each

    def test_compile_data_empty(self):
        """Test _compile_data with empty data."""
        exp = MockExperiment(n_participants=0)
        result = exp._compile_data()

        assert result.empty
        assert exp.data.empty

    def test_compile_data_nested(self):
        """Test _compile_data with nested trial structure."""
        exp = MockExperiment(n_participants=2)
        exp.participant_data = {
            1: {"trials": [{"a": 1}, {"a": 2}]},
            2: {"trials": [{"a": 3}, {"a": 4}]},
        }
        result = exp._compile_data()

        assert len(result) == 4

    def test_compile_data_list(self):
        """Test _compile_data with list structure."""
        exp = MockExperiment(n_participants=2)
        exp.participant_data = {
            1: [{"b": 1}, {"b": 2}],
            2: [{"b": 3}, {"b": 4}],
        }
        result = exp._compile_data()

        assert len(result) == 4

    def test_compile_data_single_items(self):
        """Test _compile_data with single item structure."""
        exp = MockExperiment(n_participants=2)
        exp.participant_data = {
            1: {"c": 1},
            2: {"c": 2},
        }
        result = exp._compile_data()

        assert len(result) == 2

    def test_save_data(self):
        """Test saving experiment data."""
        exp = MockExperiment(n_participants=2)
        exp.run_experiment()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            exp.save_data(temp_file)
            assert Path(temp_file).exists()

            # Verify the saved data
            saved_data = pd.read_csv(temp_file)
            assert len(saved_data) == 10  # 2 participants * 5 trials
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_save_empty_data(self):
        """Test saving empty data."""
        exp = MockExperiment(n_participants=0)

        # Should not raise an error
        exp.save_data("/tmp/test_empty.csv")

    def test_run_trial(self):
        """Test running a single trial."""
        exp = MockExperiment()
        exp.setup()

        trial = exp.run_trial(1, {"type": "test", "rt": 600, "correct": True})

        assert trial["participant_id"] == 1
        assert trial["trial_type"] == "test"
        assert trial["response_time"] == 600
        assert trial["correct"] is True

    def test_run_block(self):
        """Test running a block of trials."""
        exp = MockExperiment()
        exp.setup()

        block_trials = exp.run_block(1, {"n_trials": 3})

        assert len(block_trials) == 3
        for trial in block_trials:
            assert trial["participant_id"] == 1
            assert trial["trial_type"] == "block_trial"


class TestExperimentEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_participants(self):
        """Test experiment with zero participants."""
        exp = MockExperiment(n_participants=0)
        result = exp.run_experiment()

        assert result.empty
        assert len(exp.participant_data) == 0

    def test_single_participant(self):
        """Test experiment with single participant."""
        exp = MockExperiment(n_participants=1)
        result = exp.run_experiment()

        assert len(exp.participant_data) == 1
        assert len(result) == 5  # 1 participant * 5 trials

    def test_large_participant_count(self):
        """Test experiment with many participants."""
        exp = MockExperiment(n_participants=100)
        result = exp.run_experiment()

        assert len(exp.participant_data) == 100
        assert len(result) == 500  # 100 participants * 5 trials


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
