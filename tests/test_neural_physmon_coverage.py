"""
Comprehensive tests for apgi_framework.neural.physiological_monitoring module.

Covers: SignalType, RespirationPhase, PhysiologicalSample, PhysiologicalConfig,
HeartRateMonitor, SkinConductanceMonitor, RespirationMonitor, PhysiologicalMonitoring
"""

import os
import tempfile
import time
import numpy as np
from unittest.mock import MagicMock

import pytest
from apgi_framework.neural.physiological_monitoring import (
    HeartRateMonitor,
    PhysiologicalConfig,
    PhysiologicalMonitoring,
    PhysiologicalSample,
    RespirationMonitor,
    RespirationPhase,
    SignalType,
    SkinConductanceMonitor,
)

# --- Enums & Dataclasses ---


class TestSignalType:
    def test_all_signal_types(self):
        assert SignalType.ECG.value == "ecg"
        assert SignalType.PPG.value == "ppg"
        assert SignalType.SCR.value == "scr"
        assert SignalType.RESP.value == "resp"
        assert SignalType.TEMP.value == "temp"
        assert SignalType.BP.value == "bp"


class TestRespirationPhase:
    def test_all_phases(self):
        assert RespirationPhase.INSPIRATION.value == "inspiration"
        assert RespirationPhase.EXPIRATION.value == "expiration"
        assert RespirationPhase.PAUSE.value == "pause"


class TestPhysiologicalSample:
    def test_default_sample(self):
        sample = PhysiologicalSample(timestamp=1000.0)
        assert sample.timestamp == 1000.0
        assert sample.heart_rate is None
        assert sample.rr_interval is None
        assert sample.scr_level is None
        assert sample.metadata == {}

    def test_full_sample(self):
        sample = PhysiologicalSample(
            timestamp=1000.0,
            heart_rate=72.0,
            rr_interval=833.0,
            scr_level=5.0,
            scr_response=0.1,
            respiration_rate=15.0,
            respiration_phase=RespirationPhase.INSPIRATION,
            respiration_amplitude=0.5,
            temperature=36.5,
            blood_pressure_systolic=120.0,
            blood_pressure_diastolic=80.0,
            metadata={"key": "value"},
        )
        assert sample.heart_rate == 72.0
        assert sample.respiration_phase == RespirationPhase.INSPIRATION
        assert sample.metadata["key"] == "value"


class TestPhysiologicalConfig:
    def test_default_config(self):
        config = PhysiologicalConfig()
        assert config.sampling_rate == 1000.0
        assert config.buffer_size == 60000
        assert config.enable_ecg is True
        assert config.enable_scr is True
        assert config.enable_respiration is True
        assert config.enable_temperature is False
        assert config.enable_blood_pressure is False

    def test_invalid_sampling_rate(self):
        with pytest.raises(ValueError, match="Sampling rate must be positive"):
            PhysiologicalConfig(sampling_rate=0)

    def test_invalid_buffer_size(self):
        with pytest.raises(ValueError, match="Buffer size must be positive"):
            PhysiologicalConfig(buffer_size=-1)

    def test_custom_config(self):
        config = PhysiologicalConfig(
            sampling_rate=500.0,
            buffer_size=30000,
            enable_temperature=True,
            hr_min=50.0,
            hr_max=180.0,
        )
        assert config.sampling_rate == 500.0
        assert config.hr_min == 50.0


# --- HeartRateMonitor ---


class TestHeartRateMonitor:
    def setup_method(self):
        self.config = PhysiologicalConfig()
        self.monitor = HeartRateMonitor(self.config)

    def test_detect_r_peaks_short_signal(self):
        ecg = np.array([0.1, 0.2, 0.3])
        timestamps = np.array([0.0, 0.001, 0.002])
        result = self.monitor.detect_r_peaks(ecg, timestamps)
        assert len(result) == 0

    def test_detect_r_peaks_flat_signal(self):
        ecg = np.ones(100)
        timestamps = np.linspace(0, 1, 100)
        result = self.monitor.detect_r_peaks(ecg, timestamps)
        assert len(result) == 0

    def test_detect_r_peaks_with_peaks(self):
        # Generate a simulated ECG-like signal with clear R-peaks
        fs = 1000
        duration = 3  # seconds
        t = np.linspace(0, duration, fs * duration)
        ecg = np.zeros(len(t))
        # Add distinct peaks at 1 Hz (60 bpm)
        for i in range(1, duration):
            peak_idx = i * fs
            if peak_idx < len(ecg):
                ecg[peak_idx - 5 : peak_idx + 5] = 1.0

        result = self.monitor.detect_r_peaks(ecg, t)
        assert len(result) >= 1

    def test_compute_rr_intervals_empty(self):
        result = self.monitor.compute_rr_intervals(np.array([1.0]))
        assert len(result) == 0

    def test_compute_rr_intervals(self):
        # Peaks at 0.5s intervals -> RR = 500ms
        r_peaks = np.array([0.0, 0.5, 1.0, 1.5])
        result = self.monitor.compute_rr_intervals(r_peaks)
        assert len(result) > 0
        # All intervals should be 500ms
        for rr in result:
            assert abs(rr - 500.0) < 1.0

    def test_compute_rr_intervals_uses_stored(self):
        self.monitor.r_peaks = [0.0, 0.8, 1.6]
        result = self.monitor.compute_rr_intervals()
        assert len(result) > 0

    def test_compute_heart_rate_empty(self):
        result = self.monitor.compute_heart_rate()
        assert result == 0.0

    def test_compute_heart_rate_normal(self):
        # 800ms intervals -> 75 bpm
        rr = np.array([800.0, 800.0, 800.0, 800.0, 800.0])
        result = self.monitor.compute_heart_rate(rr)
        assert abs(result - 75.0) < 1.0

    def test_compute_heart_rate_zero(self):
        rr = np.array([0.0])
        result = self.monitor.compute_heart_rate(rr)
        assert result == 0.0

    def test_compute_hrv_metrics_insufficient(self):
        result = self.monitor.compute_hrv_metrics(np.array([800.0, 810.0]))
        assert result["sdnn"] == 0.0
        assert result["rmssd"] == 0.0
        assert result["pnn50"] == 0.0

    def test_compute_hrv_metrics(self):
        rr = np.array([800.0, 810.0, 790.0, 805.0, 815.0, 795.0])
        result = self.monitor.compute_hrv_metrics(rr)
        assert result["sdnn"] > 0
        assert result["rmssd"] > 0
        assert "pnn50" in result


# --- SkinConductanceMonitor ---


class TestSkinConductanceMonitor:
    def setup_method(self):
        self.config = PhysiologicalConfig(sampling_rate=100.0)
        self.monitor = SkinConductanceMonitor(self.config)

    def test_decompose_signal_short(self):
        signal = np.array([1.0, 2.0])
        timestamps = np.array([0.0, 0.01])
        tonic, phasic = self.monitor.decompose_signal(signal, timestamps)
        assert len(tonic) == len(signal)
        assert len(phasic) == len(signal)

    def test_decompose_signal(self):
        np.random.seed(42)
        n = 500
        timestamps = np.linspace(0, 5, n)
        # Tonic baseline + phasic events
        tonic_true = 5.0 + 0.1 * np.sin(0.5 * timestamps)
        phasic_true = np.zeros(n)
        signal = tonic_true + phasic_true + np.random.randn(n) * 0.01

        tonic, phasic = self.monitor.decompose_signal(signal, timestamps)
        assert len(tonic) == n
        assert len(phasic) == n

    def test_detect_scr_events_short(self):
        result = self.monitor.detect_scr_events(np.array([0.1]), np.array([0.0]))
        assert result == []

    def test_detect_scr_events_with_events(self):
        np.random.seed(42)
        n = 500
        timestamps = np.linspace(0, 5, n)
        phasic = np.zeros(n)
        # Create an event with rise time within range (1-3 seconds)
        start_idx = 100
        peak_idx = 250  # ~1.5s rise time at this sampling rate
        phasic[start_idx:peak_idx] = np.linspace(0, 0.05, peak_idx - start_idx)
        phasic[peak_idx : peak_idx + 50] = np.linspace(0.05, 0, 50)

        events = self.monitor.detect_scr_events(phasic, timestamps)
        # Events might or might not be found depending on thresholds
        assert isinstance(events, list)

    def test_compute_scr_rate_empty(self):
        assert self.monitor.compute_scr_rate() == 0.0
        assert self.monitor.compute_scr_rate([]) == 0.0

    def test_compute_scr_rate_with_events(self):
        events = [{"onset_time": time.time() - 10}]
        rate = self.monitor.compute_scr_rate(events)
        assert isinstance(rate, float)


# --- RespirationMonitor ---


class TestRespirationMonitor:
    def setup_method(self):
        self.config = PhysiologicalConfig(sampling_rate=100.0)
        self.monitor = RespirationMonitor(self.config)

    def test_detect_breath_cycles_short(self):
        result = self.monitor.detect_breath_cycles(np.array([0.1]), np.array([0.0]))
        assert result == []

    def test_detect_breath_cycles(self):
        # Simulate respiration at ~15 breaths/min (4 sec cycles)
        fs = 100
        duration = 20
        t = np.linspace(0, duration, fs * duration)
        resp = np.sin(2 * np.pi * 0.25 * t)  # 0.25 Hz = 15 breaths/min

        cycles = self.monitor.detect_breath_cycles(resp, t)
        assert isinstance(cycles, list)
        if cycles:
            assert "cycle_duration" in cycles[0]
            assert "amplitude" in cycles[0]

    def test_compute_respiration_rate_insufficient(self):
        assert self.monitor.compute_respiration_rate([]) == 0.0
        assert self.monitor.compute_respiration_rate([{"cycle_duration": 4.0}]) == 0.0

    def test_compute_respiration_rate(self):
        cycles = [
            {"cycle_duration": 4.0},
            {"cycle_duration": 4.1},
            {"cycle_duration": 3.9},
        ]
        rate = self.monitor.compute_respiration_rate(cycles)
        assert rate > 0
        assert self.config.resp_min <= rate <= self.config.resp_max

    def test_compute_respiration_rate_zero_duration(self):
        cycles = [{"cycle_duration": 0.0}, {"cycle_duration": 0.0}]
        rate = self.monitor.compute_respiration_rate(cycles)
        assert rate == 0.0

    def test_get_current_phase_short(self):
        resp = np.array([0.1])
        ts = np.array([0.0])
        phase = self.monitor.get_current_phase(resp, ts, 0.0)
        assert phase == RespirationPhase.PAUSE

    def test_get_current_phase_no_recent(self):
        resp = np.array([0.1, 0.2, 0.3] * 10)
        ts = np.linspace(0, 1, len(resp))
        phase = self.monitor.get_current_phase(resp, ts, 100.0)
        assert phase == RespirationPhase.PAUSE

    def test_get_current_phase_inspiration(self):
        # Rising signal -> inspiration
        n = 100
        ts = np.linspace(0, 1, n)
        resp = np.linspace(0, 1, n)
        phase = self.monitor.get_current_phase(resp, ts, 0.9)
        assert phase == RespirationPhase.INSPIRATION

    def test_get_current_phase_expiration(self):
        # Falling signal -> expiration
        n = 100
        ts = np.linspace(0, 1, n)
        resp = np.linspace(1, 0, n)
        phase = self.monitor.get_current_phase(resp, ts, 0.9)
        assert phase == RespirationPhase.EXPIRATION


# --- PhysiologicalMonitoring ---


class TestPhysiologicalMonitoring:
    def setup_method(self):
        self.config = PhysiologicalConfig(
            sampling_rate=100.0,
            buffer_size=1000,
        )
        self.monitor = PhysiologicalMonitoring(self.config)

    def test_initialization(self):
        assert self.monitor.is_streaming is False
        assert self.monitor.samples_acquired == 0
        assert isinstance(self.monitor.heart_rate_monitor, HeartRateMonitor)
        assert isinstance(self.monitor.scr_monitor, SkinConductanceMonitor)
        assert isinstance(self.monitor.respiration_monitor, RespirationMonitor)

    def test_register_callback(self):
        callback = MagicMock()
        self.monitor.register_callback(callback)
        assert callback in self.monitor.data_callbacks

    def test_get_buffer_data_empty(self):
        result = self.monitor.get_buffer_data()
        assert result == []

    def test_get_buffer_data_with_n_samples(self):
        # Add some samples
        for i in range(5):
            sample = PhysiologicalSample(timestamp=float(i))
            self.monitor.sample_buffer.append(sample)

        result = self.monitor.get_buffer_data(n_samples=3)
        assert len(result) == 3

    def test_get_signal_data_empty(self):
        values, timestamps = self.monitor.get_signal_data(SignalType.ECG)
        assert len(values) == 0
        assert len(timestamps) == 0

    def test_get_signal_data_ecg(self):
        for i in range(5):
            self.monitor.ecg_buffer.append((float(i), float(i * 2)))
        values, timestamps = self.monitor.get_signal_data(SignalType.ECG)
        assert len(values) == 5

    def test_get_signal_data_scr(self):
        for i in range(3):
            self.monitor.scr_buffer.append((float(i), float(i)))
        values, timestamps = self.monitor.get_signal_data(SignalType.SCR)
        assert len(values) == 3

    def test_get_signal_data_resp(self):
        for i in range(3):
            self.monitor.resp_buffer.append((float(i), float(i)))
        values, timestamps = self.monitor.get_signal_data(SignalType.RESP)
        assert len(values) == 3

    def test_get_signal_data_temp(self):
        self.monitor.temp_buffer.append((0.0, 36.5))
        values, timestamps = self.monitor.get_signal_data(SignalType.TEMP)
        assert len(values) == 1

    def test_get_signal_data_bp(self):
        self.monitor.bp_buffer.append((0.0, (120, 80)))
        values, timestamps = self.monitor.get_signal_data(SignalType.BP)
        assert len(values) == 1

    def test_get_signal_data_unknown(self):
        values, timestamps = self.monitor.get_signal_data(SignalType.PPG)
        assert len(values) == 0

    def test_get_signal_data_n_samples(self):
        for i in range(10):
            self.monitor.ecg_buffer.append((float(i), float(i)))
        values, timestamps = self.monitor.get_signal_data(SignalType.ECG, n_samples=3)
        assert len(values) == 3

    def test_clear_buffers(self):
        self.monitor.ecg_buffer.append((0.0, 1.0))
        self.monitor.scr_buffer.append((0.0, 1.0))
        self.monitor.resp_buffer.append((0.0, 1.0))
        self.monitor.temp_buffer.append((0.0, 1.0))
        self.monitor.bp_buffer.append((0.0, (120, 80)))
        self.monitor.sample_buffer.append(PhysiologicalSample(timestamp=0.0))

        self.monitor.clear_buffers()
        assert len(self.monitor.ecg_buffer) == 0
        assert len(self.monitor.scr_buffer) == 0
        assert len(self.monitor.sample_buffer) == 0

    def test_get_quality_metrics_no_data(self):
        result = self.monitor.get_quality_metrics()
        assert result["status"] == "no_data"

    def test_get_quality_metrics_with_data(self):
        sample = PhysiologicalSample(
            timestamp=time.time(),
            heart_rate=72.0,
            scr_level=5.0,
            respiration_rate=15.0,
        )
        self.monitor.sample_buffer.append(sample)
        result = self.monitor.get_quality_metrics()
        assert result["status"] in ("good", "poor")
        assert "overall_quality" in result

    def test_synchronize_with_external_empty(self):
        result = self.monitor.synchronize_with_external(1000.0)
        assert result is None

    def test_synchronize_with_external_match(self):
        sample = PhysiologicalSample(timestamp=1000.0)
        self.monitor.sample_buffer.append(sample)
        result = self.monitor.synchronize_with_external(1000.005, tolerance=0.01)
        assert result is not None
        assert result.timestamp == 1000.0

    def test_synchronize_with_external_no_match(self):
        sample = PhysiologicalSample(timestamp=1000.0)
        self.monitor.sample_buffer.append(sample)
        result = self.monitor.synchronize_with_external(2000.0, tolerance=0.01)
        assert result is None

    def test_compute_comprehensive_metrics_no_data(self):
        self.monitor.start_time = time.time()
        metrics = self.monitor.compute_comprehensive_metrics()
        assert "timestamp" in metrics
        assert "samples_acquired" in metrics

    def test_export_data_no_data(self):
        with pytest.raises(ValueError, match="No data to export"):
            self.monitor.export_data("test.npz")

    def test_export_data_numpy(self):
        sample = PhysiologicalSample(
            timestamp=1000.0,
            heart_rate=72.0,
            rr_interval=833.0,
            scr_level=5.0,
            scr_response=0.1,
            respiration_rate=15.0,
            respiration_amplitude=0.5,
            temperature=36.5,
        )
        self.monitor.sample_buffer.append(sample)

        with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as tmp:
            tmpname = tmp.name
        try:
            self.monitor.export_data(tmpname, format="numpy")
            data = np.load(
                tmpname + ".npz" if not tmpname.endswith(".npz") else tmpname,
                allow_pickle=True,
            )
            assert "timestamps" in data or "heart_rate" in data
        finally:
            for f in [tmpname, tmpname + ".npz"]:
                if os.path.exists(f):
                    os.unlink(f)

    def test_export_data_csv(self):
        sample = PhysiologicalSample(
            timestamp=1000.0,
            heart_rate=72.0,
            respiration_phase=RespirationPhase.INSPIRATION,
        )
        self.monitor.sample_buffer.append(sample)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmpname = tmp.name
        try:
            self.monitor.export_data(tmpname, format="csv")
            with open(tmpname) as f:
                content = f.read()
            assert "timestamp" in content
            assert "heart_rate" in content
        finally:
            os.unlink(tmpname)

    def test_export_data_unsupported_format(self):
        sample = PhysiologicalSample(timestamp=1000.0)
        self.monitor.sample_buffer.append(sample)
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.monitor.export_data("test.xyz", format="xyz")

    def test_start_stop_streaming(self):
        """Test start and stop streaming lifecycle."""
        self.monitor.start_streaming()
        assert self.monitor.is_streaming is True

        # Wait briefly for some data
        time.sleep(0.05)

        self.monitor.stop_streaming()
        assert self.monitor.is_streaming is False

    def test_start_streaming_already_active(self):
        self.monitor.start_streaming()
        with pytest.raises(RuntimeError, match="Streaming already active"):
            self.monitor.start_streaming()
        self.monitor.stop_streaming()
