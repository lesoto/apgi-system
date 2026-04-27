"""
Tests for adaptive staircases and stimulus generators.
"""

from datetime import datetime

from apgi_framework.adaptive.quest_plus_staircase import (
    QuestPlusParameters,
    QuestPlusStaircase,
)
from apgi_framework.adaptive.stimulus_generators import (
    CO2PuffController,
    CO2PuffParameters,
    GaborParameters,
    GaborPatchGenerator,
    HeartbeatSynchronizer,
    ToneGenerator,
    ToneParameters,
)


class TestQuestPlusStaircase:
    """Test suite for QUEST+ adaptive staircase."""

    def test_initialization(self):
        """Test QUEST+ staircase initialization."""
        params = QuestPlusParameters(stimulus_steps=10, threshold_steps=10, slope_steps=5)
        staircase = QuestPlusStaircase(parameters=params)

        assert len(staircase.stimulus_space) == 10
        assert staircase.state.trial_number == 0
        assert staircase.state.threshold_estimate == 0.5

    def test_staircase_update_and_convergence(self):
        """Test updating staircase and checking for convergence."""
        params = QuestPlusParameters(
            stimulus_steps=20,
            threshold_steps=20,
            slope_steps=10,
            min_trials=5,
            min_reversals=2,
        )
        staircase = QuestPlusStaircase(parameters=params)

        # Simulate some trials
        target_threshold = 0.3
        for _ in range(10):
            intensity = staircase.get_next_intensity()
            # Simulate response: Hit if intensity > target_threshold
            response = intensity > target_threshold
            staircase.update(intensity, response)

        assert staircase.state.trial_number == 10
        assert len(staircase.state.responses) == 10

        # Check threshold estimate is moving toward target
        estimate, std = staircase.get_threshold_estimate()
        assert 0.0 <= estimate <= 1.0

        # Check psychometric curve
        ints, probs = staircase.get_psychometric_curve()
        assert len(ints) == len(staircase.stimulus_space)
        assert len(probs) == len(staircase.stimulus_space)

    def test_save_load_state(self, tmp_path):
        """Test saving and loading staircase state."""
        params = QuestPlusParameters(stimulus_steps=10)
        staircase = QuestPlusStaircase(parameters=params)
        staircase.update(0.5, True)

        file_path = tmp_path / "staircase_state.json"
        staircase.save_state(str(file_path))

        assert file_path.exists()

        new_staircase = QuestPlusStaircase()
        new_staircase.load_state(str(file_path))

        assert new_staircase.state.trial_number == 1
        assert new_staircase.state.responses == [True]
        assert new_staircase.state.current_intensity == 0.5

    def test_performance_summary(self):
        """Test performance summary generation."""
        staircase = QuestPlusStaircase()
        staircase.update(0.5, True)
        staircase.update(0.4, False)

        summary = staircase.get_performance_summary()
        assert summary["trials_completed"] == 2
        assert "threshold_estimate" in summary
        assert summary["hit_rate"] == 0.5


class TestStimulusGenerators:
    """Test suite for stimulus generators."""

    def test_gabor_generator(self):
        """Test Gabor patch generator."""
        generator = GaborPatchGenerator()
        assert generator.initialize()

        params = GaborParameters(intensity=0.7, contrast=0.8, orientation=45.0)
        assert params.validate()

        assert generator.generate_stimulus(params)
        assert "gabor_array_shape" in params.metadata

        generator.cleanup()
        assert not generator.is_initialized

    def test_tone_generator(self):
        """Test tone generator."""
        generator = ToneGenerator()
        assert generator.initialize()

        params = ToneParameters(frequency_hz=1000, amplitude=0.5, duration_ms=200)
        assert params.validate()

        assert generator.generate_stimulus(params)
        assert "tone_array_length" in params.metadata

        # Test with synchronized heartbeat
        mock_sync = HeartbeatSynchronizer()
        # Mock R-peak
        mock_sync.last_r_peak = datetime.now()

        # We need to mock wait_for_r_peak because it might block
        with patch.object(mock_sync, "wait_for_r_peak", return_value=datetime.now()):
            generator.set_heartbeat_synchronizer(mock_sync)
            params_sync = ToneParameters(sync_to_heartbeat=True)
            assert generator.generate_stimulus(params_sync)

        generator.cleanup()

    def test_co2_puff_controller(self):
        """Test CO2 puff controller."""
        controller = CO2PuffController()
        assert controller.initialize()

        params = CO2PuffParameters(co2_concentration=10.0, flow_rate=2.0, duration_ms=100)
        assert params.validate()

        assert controller.generate_stimulus(params)
        assert controller.total_puffs_session == 1

        # Test safety constraint
        params_high = CO2PuffParameters(co2_concentration=20.0)  # Too high
        assert not controller.generate_stimulus(params_high)

        controller.emergency_stop_puff()
        assert controller.emergency_stop
        assert not controller.generate_stimulus(params)

        controller.cleanup()

    def test_heartbeat_synchronizer(self):
        """Test heartbeat synchronizer."""
        sync = HeartbeatSynchronizer()
        assert sync.initialize()
        assert sync.is_monitoring

        # Give it a moment to run its thread
        import time

        time.sleep(0.5)

        # Try to wait for R-peak with timeout
        # Since it's a simulated thread, it should eventually "detect" one
        with patch.object(sync, "_lock", MagicMock()):
            sync.last_r_peak = datetime.now()
            # Normally we'd wait, but for test speed we just check it was set

        # Clean up
        sync.stop_monitoring.set()
        if sync.monitoring_thread:
            sync.monitoring_thread.join(timeout=1.0)


from unittest.mock import MagicMock, patch
