"""
Comprehensive tests for apgi_framework.adaptive.stimulus_generators module.

Covers: StimulusType, StimulusParameters, GaborParameters, ToneParameters,
CO2PuffParameters, GaborPatchGenerator, ToneGenerator, CO2PuffController,
HeartbeatSynchronizer
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import numpy as np

from apgi_framework.adaptive.stimulus_generators import (
    CO2PuffController,
    CO2PuffParameters,
    GaborParameters,
    GaborPatchGenerator,
    HeartbeatSynchronizer,
    StimulusParameters,
    StimulusType,
    ToneGenerator,
    ToneParameters,
)

# --- Enums & Dataclasses ---


class TestStimulusType:
    def test_all_types(self):
        assert StimulusType.GABOR_PATCH.value == "gabor_patch"
        assert StimulusType.TONE.value == "tone"
        assert StimulusType.CO2_PUFF.value == "co2_puff"
        assert StimulusType.HEARTBEAT_FLASH.value == "heartbeat_flash"


class TestStimulusParameters:
    def test_default(self):
        params = StimulusParameters(stimulus_type=StimulusType.GABOR_PATCH)
        assert params.intensity == 0.5
        assert params.duration_ms == 500.0

    def test_validate_valid(self):
        params = StimulusParameters(
            stimulus_type=StimulusType.TONE, intensity=0.5, duration_ms=100.0
        )
        assert params.validate() is True

    def test_validate_invalid_intensity(self):
        params = StimulusParameters(stimulus_type=StimulusType.TONE, intensity=1.5)
        assert params.validate() is False

    def test_validate_invalid_duration(self):
        params = StimulusParameters(stimulus_type=StimulusType.TONE, duration_ms=-10)
        assert params.validate() is False


class TestGaborParameters:
    def test_default(self):
        params = GaborParameters()
        assert params.stimulus_type == StimulusType.GABOR_PATCH
        assert params.contrast == 0.5
        assert params.spatial_frequency == 2.0
        assert params.orientation == 0.0

    def test_validate_valid(self):
        params = GaborParameters()
        assert params.validate() is True

    def test_validate_invalid_contrast(self):
        params = GaborParameters(contrast=1.5)
        assert params.validate() is False

    def test_validate_invalid_spatial_freq(self):
        params = GaborParameters(spatial_frequency=-1)
        assert params.validate() is False

    def test_validate_invalid_orientation(self):
        params = GaborParameters(orientation=400)
        assert params.validate() is False

    def test_validate_invalid_size(self):
        params = GaborParameters(size_degrees=-1)
        assert params.validate() is False


class TestToneParameters:
    def test_default(self):
        params = ToneParameters()
        assert params.stimulus_type == StimulusType.TONE
        assert params.frequency_hz == 1000.0
        assert params.amplitude == 0.5

    def test_validate_valid(self):
        params = ToneParameters()
        assert params.validate() is True

    def test_validate_invalid_frequency(self):
        params = ToneParameters(frequency_hz=10.0)
        assert params.validate() is False

    def test_validate_invalid_amplitude(self):
        params = ToneParameters(amplitude=2.0)
        assert params.validate() is False

    def test_validate_invalid_ramp(self):
        params = ToneParameters(onset_ramp_ms=-5)
        assert params.validate() is False


class TestCO2PuffParameters:
    def test_default(self):
        params = CO2PuffParameters()
        assert params.stimulus_type == StimulusType.CO2_PUFF
        assert params.co2_concentration == 10.0

    def test_validate_valid(self):
        params = CO2PuffParameters(duration_ms=200.0)
        assert params.validate() is True

    def test_validate_invalid_concentration(self):
        params = CO2PuffParameters(co2_concentration=110.0)
        assert params.validate() is False

    def test_validate_invalid_flow_rate(self):
        params = CO2PuffParameters(flow_rate=-1)
        assert params.validate() is False

    def test_validate_duration_over_max(self):
        params = CO2PuffParameters(duration_ms=600.0, max_duration_ms=500.0)
        assert params.validate() is False

    def test_validate_invalid_nozzle(self):
        params = CO2PuffParameters(nozzle_distance_cm=-1)
        assert params.validate() is False


# --- GaborPatchGenerator ---


class TestGaborPatchGenerator:
    def test_init(self):
        gen = GaborPatchGenerator()
        assert gen.generator_id == "gabor_generator"
        assert gen.is_initialized is False

    def test_initialize(self):
        gen = GaborPatchGenerator()
        result = gen.initialize()
        assert result is True
        assert gen.is_initialized is True
        assert gen.pixels_per_degree is not None

    def test_create_gabor_patch(self):
        gen = GaborPatchGenerator()
        gen.initialize()
        params = GaborParameters(contrast=0.5, orientation=45.0)
        patch_array = gen._create_gabor_patch(params)
        assert patch_array.shape[0] > 0
        assert patch_array.shape[1] > 0
        assert np.all(patch_array >= 0)
        assert np.all(patch_array <= 1)

    def test_generate_stimulus_not_initialized(self):
        gen = GaborPatchGenerator()
        params = GaborParameters()
        result = gen.generate_stimulus(params)
        assert result is False

    def test_generate_stimulus_invalid_params(self):
        gen = GaborPatchGenerator()
        gen.initialize()
        params = GaborParameters(contrast=2.0)  # Invalid
        result = gen.generate_stimulus(params)
        assert result is False

    def test_generate_stimulus(self):
        gen = GaborPatchGenerator()
        gen.initialize()
        params = GaborParameters(duration_ms=1.0)  # Very short for testing
        result = gen.generate_stimulus(params)
        assert result is True
        assert gen.last_stimulus_time is not None
        assert params.metadata.get("gabor_array_shape") is not None

    def test_cleanup(self):
        gen = GaborPatchGenerator()
        gen.initialize()
        gen.cleanup()
        assert gen.is_initialized is False
        assert gen.display_initialized is False

    def test_validate_timing(self):
        gen = GaborPatchGenerator()
        assert gen.validate_timing(100.0) is True  # No previous stimulus

        gen.last_stimulus_time = datetime.now()
        assert gen.validate_timing(10000.0) is False  # Too soon


# --- ToneGenerator ---


class TestToneGenerator:
    def test_init(self):
        gen = ToneGenerator()
        assert gen.generator_id == "tone_generator"
        assert gen.sample_rate == 44100

    def test_initialize(self):
        gen = ToneGenerator()
        result = gen.initialize()
        assert result is True
        assert gen.is_initialized is True

    def test_create_tone_linear(self):
        gen = ToneGenerator(sample_rate=44100)
        params = ToneParameters(frequency_hz=440.0, duration_ms=100.0, envelope="linear")
        tone = gen._create_tone(params)
        assert len(tone) > 0

    def test_create_tone_gaussian(self):
        gen = ToneGenerator(sample_rate=44100)
        params = ToneParameters(frequency_hz=440.0, duration_ms=100.0, envelope="gaussian")
        tone = gen._create_tone(params)
        assert len(tone) > 0

    def test_generate_stimulus_not_initialized(self):
        gen = ToneGenerator()
        params = ToneParameters()
        assert gen.generate_stimulus(params) is False

    def test_generate_stimulus_invalid(self):
        gen = ToneGenerator()
        gen.initialize()
        params = ToneParameters(frequency_hz=5.0)  # Invalid
        assert gen.generate_stimulus(params) is False

    def test_generate_stimulus(self):
        gen = ToneGenerator()
        gen.initialize()
        params = ToneParameters(duration_ms=50.0, onset_ramp_ms=1.0, offset_ramp_ms=1.0)
        result = gen.generate_stimulus(params)
        assert result is True
        assert params.metadata.get("sample_rate") == 44100

    def test_generate_stimulus_heartbeat_sync_no_synchronizer(self):
        gen = ToneGenerator()
        gen.initialize()
        params = ToneParameters(duration_ms=1.0, sync_to_heartbeat=True)
        result = gen.generate_stimulus(params)
        assert result is False

    def test_set_heartbeat_synchronizer(self):
        gen = ToneGenerator()
        sync = MagicMock()
        gen.set_heartbeat_synchronizer(sync)
        assert gen.heartbeat_synchronizer == sync

    def test_cleanup(self):
        gen = ToneGenerator()
        gen.initialize()
        gen.cleanup()
        assert gen.is_initialized is False


# --- CO2PuffController ---


class TestCO2PuffController:
    def test_init(self):
        ctrl = CO2PuffController()
        assert ctrl.generator_id == "co2_controller"
        assert ctrl.safety_enabled is True

    def test_initialize(self):
        ctrl = CO2PuffController()
        result = ctrl.initialize()
        assert result is True
        assert ctrl.is_initialized is True

    def test_initialize_no_safety(self):
        ctrl = CO2PuffController(safety_enabled=False)
        result = ctrl.initialize()
        assert result is True

    def test_generate_stimulus_not_initialized(self):
        ctrl = CO2PuffController()
        params = CO2PuffParameters(duration_ms=100.0)
        assert ctrl.generate_stimulus(params) is False

    def test_generate_stimulus_invalid(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        params = CO2PuffParameters(co2_concentration=150.0)
        assert ctrl.generate_stimulus(params) is False

    def test_generate_stimulus(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        params = CO2PuffParameters(duration_ms=1.0, co2_concentration=5.0)
        result = ctrl.generate_stimulus(params)
        assert result is True
        assert ctrl.total_puffs_session == 1

    def test_safety_constraints_emergency_stop(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        ctrl.emergency_stop = True
        params = CO2PuffParameters(duration_ms=100.0)
        assert ctrl._check_safety_constraints(params) is False

    def test_safety_constraints_session_limit(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        ctrl.total_puffs_session = 100
        params = CO2PuffParameters(duration_ms=100.0)
        assert ctrl._check_safety_constraints(params) is False

    def test_safety_constraints_min_interval(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        ctrl.last_puff_time = datetime.now()
        params = CO2PuffParameters(duration_ms=100.0, min_interval_ms=10000)
        assert ctrl._check_safety_constraints(params) is False

    def test_safety_constraints_concentration_high(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        params = CO2PuffParameters(duration_ms=100.0, co2_concentration=20.0)
        assert ctrl._check_safety_constraints(params) is False

    def test_safety_constraints_duration_over_max(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        params = CO2PuffParameters(duration_ms=600.0, max_duration_ms=500.0)
        assert ctrl._check_safety_constraints(params) is False

    def test_emergency_stop(self):
        ctrl = CO2PuffController()
        ctrl.emergency_stop_puff()
        assert ctrl.emergency_stop is True

    def test_reset_emergency_stop(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        ctrl.emergency_stop_puff()
        ctrl.reset_emergency_stop()
        assert ctrl.emergency_stop is False

    def test_cleanup(self):
        ctrl = CO2PuffController()
        ctrl.initialize()
        ctrl.total_puffs_session = 5
        ctrl.cleanup()
        assert ctrl.is_initialized is False
        assert ctrl.total_puffs_session == 0
        assert ctrl.emergency_stop is True


# --- HeartbeatSynchronizer ---


class TestHeartbeatSynchronizer:
    def test_init(self):
        sync = HeartbeatSynchronizer()
        assert sync.synchronizer_id == "heartbeat_sync"
        assert sync.is_monitoring is False

    def test_initialize(self):
        sync = HeartbeatSynchronizer()
        result = sync.initialize()
        assert result is True
        assert sync.is_monitoring is True
        sync.cleanup()

    def test_wait_for_r_peak_not_monitoring(self):
        sync = HeartbeatSynchronizer()
        result = sync.wait_for_r_peak(timeout_ms=10)
        assert result is None

    def test_wait_for_r_peak_with_peak(self):
        sync = HeartbeatSynchronizer()
        sync.is_monitoring = True
        sync.last_r_peak = datetime.now()
        result = sync.wait_for_r_peak(timeout_ms=10)
        assert result is not None

    def test_wait_for_r_peak_timeout(self):
        sync = HeartbeatSynchronizer()
        sync.is_monitoring = True
        sync.last_r_peak = None
        result = sync.wait_for_r_peak(timeout_ms=5)
        assert result is None

    def test_get_heart_rate_insufficient(self):
        sync = HeartbeatSynchronizer()
        assert sync.get_heart_rate() is None
        sync.r_peak_history = [datetime.now()]
        assert sync.get_heart_rate() is None

    def test_get_heart_rate(self):
        sync = HeartbeatSynchronizer()
        now = datetime.now()
        # Simulate 60 bpm (1 beat per second)
        sync.r_peak_history = [
            now - timedelta(seconds=2),
            now - timedelta(seconds=1),
            now,
        ]
        hr = sync.get_heart_rate()
        assert hr is not None
        assert 55 < hr < 65

    def test_get_rr_interval_insufficient(self):
        sync = HeartbeatSynchronizer()
        assert sync.get_rr_interval() is None

    def test_get_rr_interval(self):
        sync = HeartbeatSynchronizer()
        now = datetime.now()
        sync.r_peak_history = [
            now - timedelta(seconds=1),
            now,
        ]
        rr = sync.get_rr_interval()
        assert rr is not None
        assert abs(rr - 1000.0) < 50

    def test_predict_next_r_peak_insufficient(self):
        sync = HeartbeatSynchronizer()
        assert sync.predict_next_r_peak() is None

    def test_predict_next_r_peak(self):
        sync = HeartbeatSynchronizer()
        now = datetime.now()
        sync.r_peak_history = [
            now - timedelta(seconds=3),
            now - timedelta(seconds=2),
            now - timedelta(seconds=1),
            now,
        ]
        predicted = sync.predict_next_r_peak()
        assert predicted is not None
        assert predicted > now

    def test_cleanup(self):
        sync = HeartbeatSynchronizer()
        sync.initialize()
        sync.cleanup()
        assert sync.is_monitoring is False
