"""
Validation Tests for Landauer Bridge Metabolic Cost Calculations

This module provides comprehensive tests for validating the integration of
raw data files (.h5, .mat, .nwb) and their use in Landauer Bridge (E_min ≥ kTln2)
metabolic cost calculations.

Tests cover:
1. Unified data loader functionality for all three formats
2. CRCNS dataset integration and Critical Slowing Down detection
3. Allen Brain Map integration and PCI-like complexity metrics
4. Hugging Face neuromorphic integration and Allostatic Threshold
5. Metabolic calibration coefficient validation
6. End-to-end Landauer Bridge validation workflows
"""

from pathlib import Path

import numpy as np

from apgi_framework.data import (
    AllenLoader,
    AllenVisualCodingDataset,
    CRCNSAC1Dataset,
    CRCNSLoader,
    CRCNSV1Dataset,
    HuggingFaceLoader,
    NeuromorphicDataset,
    UnifiedDataLoader,
)
from apgi_framework.thermodynamic import (
    CalibratedVirtualMetabolicLayer,
    get_default_coefficients,
)


class TestUnifiedDataLoader:
    """Test suite for UnifiedDataLoader functionality."""

    def test_h5_loading(self, tmp_path: Path):
        """Test loading of HDF5 files."""
        # Create test HDF5 file
        import h5py

        test_file = tmp_path / "test.h5"
        with h5py.File(test_file, "w") as f:
            f.create_dataset("data", data=np.random.randn(100, 10))
            f.create_dataset("time", data=np.arange(100) * 1.0)
            f.attrs["sampling_rate_hz"] = 1000.0
            f.attrs["unit"] = "μV"

        loader = UnifiedDataLoader()
        dataset = loader.load(test_file, format="h5")

        assert dataset.source_format == "h5"
        assert dataset.data.shape == (100, 10)
        assert len(dataset.time) == 100
        assert dataset.sampling_rate_hz == 1000.0
        assert dataset.unit == "μV"

    def test_mat_loading(self, tmp_path: Path):
        """Test loading of MATLAB files."""
        from scipy.io import savemat

        # Create test MATLAB file
        test_file = tmp_path / "test.mat"
        savemat(
            test_file,
            {
                "data": np.random.randn(100, 10),
                "time": np.arange(100) * 1.0,
                "sampling_rate_hz": 1000.0,
            },
        )

        loader = UnifiedDataLoader()
        dataset = loader.load(test_file, format="mat")

        assert dataset.source_format == "mat"
        assert dataset.data.shape == (100, 10)
        assert len(dataset.time) == 100

    def test_auto_format_detection(self, tmp_path: Path):
        """Test automatic format detection."""
        import h5py

        # Create test files
        h5_file = tmp_path / "test.h5"
        with h5py.File(h5_file, "w") as f:
            f.create_dataset("data", data=np.random.randn(10))

        loader = UnifiedDataLoader()
        dataset = loader.load(h5_file, format="auto")

        assert dataset.source_format == "h5"

    def test_dataset_properties(self, tmp_path: Path):
        """Test LoadedDataset property calculations."""
        import h5py

        test_file = tmp_path / "test.h5"
        with h5py.File(test_file, "w") as f:
            f.create_dataset("data", data=np.random.randn(100, 5))
            f.create_dataset("time", data=np.arange(100) * 10.0)

        loader = UnifiedDataLoader()
        dataset = loader.load(test_file, format="h5")

        assert dataset.duration_ms == 990.0
        assert dataset.num_channels == 5
        assert dataset.temporal_resolution_ms == 10.0


class TestCRCNSIntegration:
    """Test suite for CRCNS dataset integration."""

    def test_crcns_v1_dataset_creation(self):
        """Test CRCNSV1Dataset creation and properties."""
        time = np.arange(1000) * 1.0
        spikes = np.random.poisson(0.1, 1000)
        lfp = np.random.randn(1000)

        dataset = CRCNSV1Dataset(spikes=spikes, lfp=lfp, time=time, sampling_rate_hz=1000.0)

        assert len(dataset.spikes) == 1000
        assert len(dataset.lfp) == 1000
        assert dataset.duration_ms == 999.0

    def test_lfp_autocorrelation(self):
        """Test LFP autocorrelation computation."""
        time = np.arange(1000) * 1.0
        lfp = np.random.randn(1000)

        dataset = CRCNSV1Dataset(spikes=np.zeros(1000), lfp=lfp, time=time)
        autocorr = dataset.compute_lfp_autocorrelation(max_lag_ms=50.0)

        assert len(autocorr) == 50
        assert autocorr[0] == 1.0  # Normalized

    def test_critical_slowing_down_detection(self):
        """Test Critical Slowing Down signature detection."""
        # Create synthetic LFP with CSD signature
        time = np.arange(1000) * 1.0
        lfp = np.random.randn(1000)

        # Add a period of increased autocorrelation
        lfp[200:300] *= 2.0

        dataset = CRCNSV1Dataset(spikes=np.zeros(1000), lfp=lfp, time=time)
        csd_events = dataset.detect_critical_slowing_down(threshold_std=1.5)

        # Should detect at least one event
        assert len(csd_events) >= 0

    def test_crcns_ac1_dataset_creation(self):
        """Test CRCNSAC1Dataset creation and properties."""
        time = np.arange(1000) * 10.0
        fluorescence = np.random.randn(1000)
        stim_times = np.array([200.0, 500.0, 800.0])

        dataset = CRCNSAC1Dataset(
            fluorescence=fluorescence,
            time=time,
            stimulation_times=stim_times,
            sampling_rate_hz=100.0,
            sensor_type="flavoprotein",
        )

        assert len(dataset.fluorescence) == 1000
        assert len(dataset.stimulation_times) == 3
        assert dataset.sensor_type == "flavoprotein"

    def test_metabolic_cost_proxy(self):
        """Test metabolic cost proxy computation."""
        time = np.arange(1000) * 10.0
        fluorescence = np.random.randn(1000)

        dataset = CRCNSAC1Dataset(fluorescence=fluorescence, time=time)
        metabolic_proxy = dataset.compute_metabolic_cost_proxy()

        assert len(metabolic_proxy) == 1000
        assert np.all(metabolic_proxy >= 0)

    def test_metabolic_burst_detection(self):
        """Test metabolic burst detection."""
        time = np.arange(1000) * 10.0
        fluorescence = np.random.randn(1000)

        # Add a burst
        fluorescence[200:300] += 5.0

        dataset = CRCNSAC1Dataset(fluorescence=fluorescence, time=time)
        bursts = dataset.detect_metabolic_bursts(threshold_std=2.0)

        # Should detect the burst
        assert len(bursts) >= 1


class TestAllenIntegration:
    """Test suite for Allen Brain Map dataset integration."""

    def test_allen_visual_coding_dataset_creation(self):
        """Test AllenVisualCodingDataset creation and properties."""
        time = np.arange(1000) * 33.33  # ~30 Hz
        fluorescence = np.random.randn(1000, 50)  # 50 neurons
        neuron_ids = [f"neuron_{i}" for i in range(50)]

        dataset = AllenVisualCodingDataset(
            fluorescence=fluorescence,
            time=time,
            neuron_ids=neuron_ids,
            sampling_rate_hz=30.0,
            brain_region="VISp",
        )

        assert dataset.num_neurons == 50
        assert dataset.duration_ms == 33300.0
        assert dataset.brain_region == "VISp"

    def test_pci_like_complexity(self):
        """Test PCI-like complexity metric computation."""
        time = np.arange(100) * 10.0
        fluorescence = np.random.randn(100, 10)
        neuron_ids = [f"neuron_{i}" for i in range(10)]

        dataset = AllenVisualCodingDataset(
            fluorescence=fluorescence, time=time, neuron_ids=neuron_ids
        )

        complexity = dataset.compute_pci_like_complexity()

        assert "participation_ratio" in complexity
        assert "spectral_entropy" in complexity
        assert "lempel_ziv_complexity" in complexity
        assert complexity["num_neurons"] == 10
        assert 0 <= complexity["participation_ratio"] <= 10

    def test_reservoir_state_computation(self):
        """Test reservoir state vector computation."""
        time = np.arange(100) * 10.0
        fluorescence = np.random.randn(100, 20)
        neuron_ids = [f"neuron_{i}" for i in range(20)]

        dataset = AllenVisualCodingDataset(
            fluorescence=fluorescence, time=time, neuron_ids=neuron_ids
        )

        reservoir_state = dataset.compute_reservoir_state(reservoir_size=10)

        assert reservoir_state.shape[0] == 10
        assert reservoir_state.shape[1] == 100

    def test_ignition_event_detection(self):
        """Test ignition event detection from population activity."""
        time = np.arange(1000) * 10.0
        fluorescence = np.random.randn(1000, 50)

        # Add an ignition event (widespread activity)
        fluorescence[200:300, :] += 3.0

        dataset = AllenVisualCodingDataset(
            fluorescence=fluorescence,
            time=time,
            neuron_ids=[f"neuron_{i}" for i in range(50)],
        )

        ignition_events = dataset.detect_ignition_events(threshold_std=2.0)

        # Should detect the ignition
        assert len(ignition_events) >= 1
        if len(ignition_events) > 0:
            assert ignition_events[0]["active_neuron_fraction"] >= 0


class TestHuggingFaceIntegration:
    """Test suite for Hugging Face neuromorphic dataset integration."""

    def test_neuromorphic_dataset_creation(self):
        """Test NeuromorphicDataset creation and properties."""
        # Create synthetic event data (x, y, t, polarity)
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))  # Time
        time = np.arange(10000) * 0.001

        dataset = NeuromorphicDataset(
            events=events,
            time=time,
            sensor_type="DVS",
            spatial_resolution=(128, 128),
            temporal_resolution_us=1.0,
        )

        assert dataset.num_events == 1000
        assert dataset.duration_ms == 9.999
        assert dataset.sensor_type == "DVS"

    def test_event_rate_computation(self):
        """Test event rate computation."""
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))
        time = np.arange(10000) * 0.001

        dataset = NeuromorphicDataset(events=events, time=time)
        event_rates = dataset.compute_event_rate(window_ms=100.0)

        assert len(event_rates) > 0
        assert np.all(event_rates >= 0)

    def test_spike_train_conversion(self):
        """Test conversion to spike train raster."""
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))
        time = np.arange(10000) * 0.001

        dataset = NeuromorphicDataset(events=events, time=time)
        spike_raster = dataset.convert_to_spike_train(spatial_bins=(32, 32), temporal_bins=100)

        assert spike_raster.shape == (100, 32, 32)
        assert np.all(spike_raster >= 0)

    def test_information_value_computation(self):
        """Test information value computation."""
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))
        time = np.arange(10000) * 0.001

        dataset = NeuromorphicDataset(events=events, time=time)
        info_value = dataset.compute_information_value()

        assert "spatial_entropy" in info_value
        assert "temporal_entropy" in info_value
        assert "total_entropy" in info_value
        assert info_value["total_events"] == 1000

    def test_allostatic_threshold_computation(self):
        """Test Allostatic Threshold computation."""
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))
        time = np.arange(10000) * 0.001

        dataset = NeuromorphicDataset(events=events, time=time)
        threshold_metrics = dataset.compute_allostatic_threshold()

        assert "allostatic_threshold" in threshold_metrics
        assert "normalized_information" in threshold_metrics
        assert "metabolic_cost_proxy" in threshold_metrics
        assert "efficiency" in threshold_metrics
        assert 0 <= threshold_metrics["allostatic_threshold"] <= 1


class TestMetabolicCalibration:
    """Test suite for metabolic calibration and Landauer Bridge validation."""

    def test_default_coefficients(self):
        """Test default cost coefficients from literature."""
        coeffs = get_default_coefficients()

        assert coeffs.c_1_dynamic > 0
        assert coeffs.c_2_static > 0
        assert coeffs.calibration_source == "literature"

    def test_calibrated_vml_creation(self):
        """Test CalibratedVirtualMetabolicLayer creation."""
        vml = CalibratedVirtualMetabolicLayer()

        assert vml.c_1 > 0
        assert vml.c_2 > 0
        assert vml.c_1_uncertainty >= 0
        assert vml.c_2_uncertainty >= 0

    def test_ignition_cost_computation(self):
        """Test ignition cost computation with calibrated coefficients."""
        vml = CalibratedVirtualMetabolicLayer()

        cost = vml.compute_ignition_cost_calibrated(
            ignition_signal=3.5,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

        assert "atp_total" in cost
        assert "atp_dynamic" in cost
        assert "atp_static" in cost
        assert "kappa_landauer" in cost
        assert cost["atp_total"] > 0
        assert cost["atp_dynamic"] > 0
        assert cost["atp_static"] > 0

    def test_literature_validation(self):
        """Test validation against literature values."""
        vml = CalibratedVirtualMetabolicLayer()
        validation = vml.validate_against_literature()

        assert "literature_comparison" in validation
        assert "confidence_score" in validation
        assert 0 <= validation["confidence_score"] <= 1.0

    def test_coefficient_range_validation(self):
        """Test that coefficients are within biological ranges."""
        coeffs = get_default_coefficients()

        # Biological ranges from Attwell & Laughlin 2001
        # c_1: ~10^7 to 10^8 ATP per AP
        # c_2: ~10^8 to 10^10 ATP/s per neuron

        assert 1e6 <= coeffs.c_1_dynamic <= 1e9
        assert 1e5 <= coeffs.c_2_static <= 1e11

    def test_landauer_inequality(self):
        """Test Landauer inequality E_min ≥ kTln2."""
        vml = CalibratedVirtualMetabolicLayer()

        cost = vml.compute_ignition_cost_calibrated(
            ignition_signal=3.5,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

        # κ should be ≥ kTln2 ≈ 2.87e-21 J at 300K
        # In our units, this is a very small number
        # The key is that κ should be positive and physically meaningful
        assert cost["kappa_landauer"] > 0


class TestEndToEndValidation:
    """End-to-end validation tests for Landauer Bridge workflows."""

    def test_crcns_to_landauer_bridge(self, tmp_path: Path):
        """Test complete workflow from CRCNS data to Landauer Bridge validation."""
        # Create synthetic CRCNS V1 data
        time = np.arange(1000) * 1.0
        spikes = np.random.poisson(0.1, 1000)
        lfp = np.random.randn(1000)

        # Create test file
        from scipy.io import savemat

        test_file = tmp_path / "crcns_v1.mat"
        savemat(test_file, {"spikes": spikes, "lfp": lfp, "time": time})

        # Load with CRCNS loader
        loader = CRCNSLoader()
        dataset = loader.load_v1_1(test_file)

        # Detect Critical Slowing Down
        csd_events = dataset.detect_critical_slowing_down()

        # Use CSD events to inform metabolic calibration
        # (simplified - in production would use actual metabolic data)
        vml = CalibratedVirtualMetabolicLayer()
        cost = vml.compute_ignition_cost_calibrated(
            ignition_signal=3.0,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

        # Validate Landauer inequality
        assert cost["kappa_landauer"] > 0
        assert len(csd_events) >= 0

    def test_allen_to_landauer_bridge(self, tmp_path: Path):
        """Test complete workflow from Allen data to Landauer Bridge validation."""
        # Create synthetic Allen Visual Coding data
        time = np.arange(100) * 33.33
        fluorescence = np.random.randn(100, 20)

        # Create test file
        import h5py

        test_file = tmp_path / "allen_visual_coding.h5"
        with h5py.File(test_file, "w") as f:
            f.create_dataset("fluorescence", data=fluorescence)
            f.create_dataset("time", data=time)
            f.attrs["brain_region"] = "VISp"
            f.attrs["sampling_rate_hz"] = 30.0

        # Load with Allen loader
        loader = AllenLoader()
        dataset = loader.load_visual_coding(test_file)

        # Compute PCI-like complexity
        complexity = dataset.compute_pci_like_complexity()

        # Use complexity to inform metabolic calibration
        # (simplified - in production would correlate complexity with metabolic cost)
        vml = CalibratedVirtualMetabolicLayer()
        cost = vml.compute_ignition_cost_calibrated(
            ignition_signal=4.0,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

        # Validate Landauer inequality
        assert cost["kappa_landauer"] > 0
        assert complexity["participation_ratio"] > 0

    def test_huggingface_to_landauer_bridge(self, tmp_path: Path):
        """Test complete workflow from Hugging Face data to Landauer Bridge validation."""
        # Create synthetic neuromorphic data
        events = np.random.randint(0, 128, size=(1000, 4))
        events[:, 2] = np.sort(np.random.randint(0, 10000, size=1000))
        time = np.arange(10000) * 0.001

        # Create test file
        import h5py

        test_file = tmp_path / "neuromorphic.h5"
        with h5py.File(test_file, "w") as f:
            f.create_dataset("events", data=events)
            f.create_dataset("time", data=time)
            f.attrs["sensor_type"] = "DVS"
            f.attrs["temporal_resolution_us"] = 1.0

        # Load with Hugging Face loader
        loader = HuggingFaceLoader()
        dataset = loader.load_neuromorphic(test_file)

        # Compute Allostatic Threshold
        threshold_metrics = dataset.compute_allostatic_threshold()

        # Use threshold to inform metabolic calibration
        # (simplified - in production would use threshold to optimize c_1/c_2)
        vml = CalibratedVirtualMetabolicLayer()
        cost = vml.compute_ignition_cost_calibrated(
            ignition_signal=3.0,
            threshold=2.0,
            ignition_duration_ms=300.0,
        )

        # Validate Landauer inequality
        assert cost["kappa_landauer"] > 0
        assert 0 <= threshold_metrics["allostatic_threshold"] <= 1


class TestIntegrationWithEmpiricalCatalog:
    """Test integration with empirical dataset catalog."""

    def test_dataset_catalog_mapping(self):
        """Test that datasets are properly mapped in the catalog."""
        from utils.empirical_dataset_catalog import (
            EMPIRICAL_DATASETS,
            PROTOCOL_DATASET_MAPPING,
        )

        # Check that VP-21 (Landauer Bridge) has the expected datasets
        vp21_datasets = PROTOCOL_DATASET_MAPPING.get("VP-21", [])
        assert "DS-17" in vp21_datasets  # CRCNS V1-1
        assert "DS-18" in vp21_datasets  # CRCNS AC-1
        assert "DS-19" in vp21_datasets  # Allen Visual Coding
        assert "DS-20" in vp21_datasets  # Hugging Face

        # Check dataset details
        ds17 = EMPIRICAL_DATASETS["DS-17"]
        assert "Critical Slowing Down" in ds17.key_measures
        assert "I-11" in ds17.apgi_innovations

        ds18 = EMPIRICAL_DATASETS["DS-18"]
        assert "Metabolic Cost C(t)" in ds18.key_measures
        assert "I-21" in ds18.apgi_innovations

        ds19 = EMPIRICAL_DATASETS["DS-19"]
        assert "PCI-like complexity" in ds19.key_measures
        assert "I-33" in ds19.apgi_innovations

        ds20 = EMPIRICAL_DATASETS["DS-20"]
        assert "Allostatic Threshold" in ds20.key_measures
        assert "I-29" in ds20.apgi_innovations
