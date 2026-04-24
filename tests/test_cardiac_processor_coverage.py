"""
Comprehensive tests for apgi_framework.neural.cardiac_processor module.

Covers: RPeakAlgorithm, HRVMetrics, CardiacQualityMetrics, CardiacProcessor,
HRVAnalyzer, HEPExtractor, CardiacQualityAssessor
"""

import numpy as np

from apgi_framework.neural.cardiac_processor import (
    CardiacProcessor,
    CardiacQualityAssessor,
    CardiacQualityMetrics,
    HEPExtractor,
    HRVAnalyzer,
    HRVMetrics,
    RPeakAlgorithm,
)


def _generate_synthetic_ecg(duration=5, fs=1000, bpm=60):
    """Generate a synthetic ECG signal for testing."""
    t = np.linspace(0, duration, int(duration * fs))
    beat_interval = 60.0 / bpm
    ecg = np.zeros_like(t)

    for beat in range(int(duration / beat_interval) + 1):
        beat_time = beat * beat_interval
        # Create R-peak (gaussian peak)
        r_peak = np.exp(-((t - beat_time) ** 2) / (0.001))
        ecg += r_peak

    # Add some noise
    ecg += np.random.randn(len(t)) * 0.05
    return ecg, t


# --- Enums & Dataclasses ---


class TestRPeakAlgorithm:
    def test_all_algorithms(self):
        assert RPeakAlgorithm.SIMPLE_THRESHOLD.value == "simple_threshold"
        assert RPeakAlgorithm.PAN_TOMPKINS.value == "pan_tompkins"
        assert RPeakAlgorithm.WAVELET.value == "wavelet"
        assert RPeakAlgorithm.ADAPTIVE.value == "adaptive"


class TestHRVMetrics:
    def test_creation(self):
        metrics = HRVMetrics(
            mean_hr=72.0,
            sdnn=50.0,
            rmssd=30.0,
            pnn50=15.0,
        )
        assert metrics.mean_hr == 72.0
        assert metrics.lf_power is None
        assert metrics.n_beats == 0
        assert metrics.recording_duration == 0.0

    def test_full_metrics(self):
        metrics = HRVMetrics(
            mean_hr=72.0,
            sdnn=50.0,
            rmssd=30.0,
            pnn50=15.0,
            lf_power=500.0,
            hf_power=300.0,
            lf_hf_ratio=1.67,
            total_power=800.0,
            n_beats=300,
            recording_duration=300.0,
        )
        assert metrics.lf_hf_ratio == 1.67
        assert metrics.n_beats == 300


class TestCardiacQualityMetrics:
    def test_creation(self):
        metrics = CardiacQualityMetrics(
            overall_quality=0.95,
            signal_quality_index=0.9,
            ectopic_beat_percentage=2.0,
            missed_beat_percentage=1.0,
            noise_level=0.05,
            recommendation="Good quality",
        )
        assert metrics.overall_quality == 0.95


# --- CardiacProcessor ---


class TestCardiacProcessor:
    def setup_method(self):
        self.processor = CardiacProcessor(sampling_rate=1000.0)

    def test_init_default(self):
        p = CardiacProcessor()
        assert p.sampling_rate == 1000.0
        assert p.algorithm == RPeakAlgorithm.ADAPTIVE

    def test_init_custom(self):
        p = CardiacProcessor(
            sampling_rate=500.0,
            algorithm=RPeakAlgorithm.PAN_TOMPKINS,
        )
        assert p.sampling_rate == 500.0
        assert p.algorithm == RPeakAlgorithm.PAN_TOMPKINS

    def test_preprocess_ecg(self):
        ecg, t = _generate_synthetic_ecg(duration=2, fs=1000)
        filtered = self.processor.preprocess_ecg(ecg)
        assert len(filtered) == len(ecg)

    def test_detect_r_peaks_pan_tompkins(self):
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000, bpm=60)
        peaks = self.processor.detect_r_peaks_pan_tompkins(ecg, t)
        assert isinstance(peaks, np.ndarray)
        # Should detect approximately 5 peaks for 5 seconds at 60 BPM
        assert len(peaks) >= 2

    def test_detect_r_peaks_adaptive(self):
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000, bpm=60)
        preprocessed = self.processor.preprocess_ecg(ecg)
        peaks = self.processor.detect_r_peaks_adaptive(preprocessed, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_default(self):
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000, bpm=60)
        peaks = self.processor.detect_r_peaks(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_pan_tompkins_algorithm(self):
        p = CardiacProcessor(algorithm=RPeakAlgorithm.PAN_TOMPKINS)
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000, bpm=60)
        peaks = p.detect_r_peaks(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_simple_threshold_with_monitor(self):
        mock_monitor = type(
            "MockMonitor",
            (),
            {"detect_r_peaks": lambda self, s, t: np.array([1.0, 2.0, 3.0])},
        )()
        p = CardiacProcessor(
            algorithm=RPeakAlgorithm.SIMPLE_THRESHOLD,
            heart_rate_monitor=mock_monitor,
        )
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000)
        peaks = p.detect_r_peaks(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_simple_threshold_no_monitor(self):
        p = CardiacProcessor(algorithm=RPeakAlgorithm.SIMPLE_THRESHOLD)
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000)
        peaks = p.detect_r_peaks(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_wavelet_fallback(self):
        p = CardiacProcessor(algorithm=RPeakAlgorithm.WAVELET)
        ecg, t = _generate_synthetic_ecg(duration=5, fs=1000)
        peaks = p.detect_r_peaks(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_correct_ectopic_beats_short(self):
        rr = np.array([800.0, 810.0])
        corrected, ectopic = self.processor.correct_ectopic_beats(rr)
        assert len(corrected) == 2
        assert not np.any(ectopic)

    def test_correct_ectopic_beats(self):
        rr = np.array([800.0, 810.0, 400.0, 790.0, 810.0])
        corrected, ectopic = self.processor.correct_ectopic_beats(rr, threshold=0.2)
        assert len(corrected) == 5
        # The 400ms interval is an ectopic beat
        assert np.any(ectopic)
        # Ectopic beat should be corrected
        assert corrected[2] != 400.0

    def test_correct_ectopic_beats_none(self):
        rr = np.array([800.0, 810.0, 800.0, 790.0, 810.0])
        corrected, ectopic = self.processor.correct_ectopic_beats(rr, threshold=0.2)
        assert not np.any(ectopic)


# --- HRVAnalyzer ---


class TestHRVAnalyzer:
    def setup_method(self):
        self.analyzer = HRVAnalyzer()

    def test_init(self):
        assert self.analyzer.sampling_rate == 1000.0

    def test_time_domain_insufficient(self):
        result = self.analyzer.compute_time_domain_metrics(np.array([800.0]))
        assert result["mean_hr"] == 0.0

    def test_time_domain_metrics(self):
        rr = np.array([800.0, 810.0, 790.0, 805.0, 815.0, 795.0, 800.0])
        result = self.analyzer.compute_time_domain_metrics(rr)
        assert result["mean_hr"] > 0
        assert result["sdnn"] > 0
        assert result["rmssd"] > 0
        assert "pnn50" in result

    def test_frequency_domain_insufficient(self):
        rr = np.array([800.0, 810.0])
        r_peaks = np.array([0.0, 0.8, 1.61])
        result = self.analyzer.compute_frequency_domain_metrics(rr, r_peaks)
        assert result["lf_power"] == 0.0
        assert result["hf_power"] == 0.0

    def test_frequency_domain_metrics(self):
        # Generate longer RR data for frequency analysis
        np.random.seed(42)
        n_beats = 200
        rr = 800.0 + np.random.randn(n_beats) * 20
        r_peaks = np.cumsum(rr / 1000.0)
        r_peaks = np.insert(r_peaks, 0, 0.0)

        result = self.analyzer.compute_frequency_domain_metrics(rr, r_peaks)
        assert "lf_power" in result
        assert "hf_power" in result
        assert "total_power" in result
        assert result["total_power"] >= 0

    def test_comprehensive_hrv(self):
        np.random.seed(42)
        n_beats = 50
        rr = 800.0 + np.random.randn(n_beats) * 20
        r_peaks = np.cumsum(rr / 1000.0)
        r_peaks = np.insert(r_peaks, 0, 0.0)

        hrv = self.analyzer.compute_comprehensive_hrv(rr, r_peaks)
        assert isinstance(hrv, HRVMetrics)
        assert hrv.mean_hr > 0
        assert hrv.n_beats == n_beats + 1
        assert hrv.recording_duration > 0


# --- HEPExtractor ---


class TestHEPExtractor:
    def setup_method(self):
        self.extractor = HEPExtractor(sampling_rate=1000.0)

    def test_init(self):
        assert self.extractor.sampling_rate == 1000.0

    def test_extract_hep_epochs_empty(self):
        eeg = np.random.randn(32, 5000)
        r_peaks = np.array([])
        timestamps = np.linspace(0, 5, 5000)

        epochs = self.extractor.extract_hep_epochs(eeg, r_peaks, timestamps)
        assert epochs.size == 0

    def test_extract_hep_epochs(self):
        n_channels = 4
        n_samples = 5000
        eeg = np.random.randn(n_channels, n_samples)
        timestamps = np.linspace(0, 5, n_samples)
        r_peaks = np.array([1.0, 2.0, 3.0])  # 3 R-peaks

        epochs = self.extractor.extract_hep_epochs(eeg, r_peaks, timestamps)
        assert len(epochs.shape) == 3
        assert epochs.shape[1] == n_channels

    def test_compute_hep_amplitude_empty(self):
        result = self.extractor.compute_hep_amplitude(np.array([]))
        assert result.size == 0

    def test_compute_hep_amplitude(self):
        # Create mock epochs
        n_epochs = 5
        n_channels = 4
        n_samples = 1000
        epochs = np.random.randn(n_epochs, n_channels, n_samples)

        amplitudes = self.extractor.compute_hep_amplitude(epochs)
        assert amplitudes.shape == (n_epochs, n_channels)

    def test_apply_baseline_correction_empty(self):
        result = self.extractor.apply_baseline_correction(np.array([]))
        assert result.size == 0

    def test_apply_baseline_correction(self):
        n_epochs = 5
        n_channels = 4
        n_samples = 1000
        epochs = np.random.randn(n_epochs, n_channels, n_samples) + 10.0

        corrected = self.extractor.apply_baseline_correction(epochs)
        assert corrected.shape == epochs.shape
        # Baseline should be closer to zero after correction
        baseline_mean = np.mean(corrected[:, :, :200], axis=2)
        assert np.all(np.abs(baseline_mean) < 1.0)


# --- CardiacQualityAssessor ---


class TestCardiacQualityAssessor:
    def setup_method(self):
        self.assessor = CardiacQualityAssessor(sampling_rate=1000.0)

    def test_init(self):
        assert self.assessor.sampling_rate == 1000.0

    def test_preprocess_ecg(self):
        ecg, t = _generate_synthetic_ecg(duration=2)
        filtered = self.assessor.preprocess_ecg(ecg)
        assert len(filtered) == len(ecg)

    def test_detect_r_peaks_pan_tompkins(self):
        ecg, t = _generate_synthetic_ecg(duration=5, bpm=60)
        peaks = self.assessor.detect_r_peaks_pan_tompkins(ecg, t)
        assert isinstance(peaks, np.ndarray)

    def test_detect_r_peaks_adaptive(self):
        ecg, t = _generate_synthetic_ecg(duration=5, bpm=60)
        preprocessed = self.assessor.preprocess_ecg(ecg)
        peaks = self.assessor.detect_r_peaks_adaptive(preprocessed, t)
        assert isinstance(peaks, np.ndarray)
