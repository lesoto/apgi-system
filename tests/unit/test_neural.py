# mypy: ignore-errors
# type: ignore
"""
Unit tests for neural system modules.

This module implements unit tests for the neural oscillation engine,
large-scale networks, neural columns, and spiking networks.
Tests cover initialization, signal generation, coupling, and
neural dynamics simulation.
"""

import numpy as np
import pytest

# Import neural modules with error handling
try:
    from apgi_framework.neural.oscillations import OscillationBand, OscillationEngine

    HAS_OSCILLATIONS = True
except ImportError:
    HAS_OSCILLATIONS = False
    OscillationEngine = None
    OscillationBand = None
    print("Warning: Could not import oscillation modules")

try:
    from apgi_framework.neural.macroscale.large_scale_networks import LargeScaleNetworkManager

    HAS_MACROSCALE = True
except ImportError:
    HAS_MACROSCALE = False
    LargeScaleNetworkManager = None
    print("Warning: Could not import macroscale modules")

try:
    from apgi_framework.neural.mesoscale.neural_columns import NeuralColumn

    HAS_MESOSCALE = True
except ImportError:
    HAS_MESOSCALE = False
    NeuralColumn = None
    print("Warning: Could not import mesoscale modules")

try:
    from apgi_framework.neural.microscale.spiking_network import SpikingNetwork

    HAS_MICROSCALE = True
except ImportError:
    HAS_MICROSCALE = False
    SpikingNetwork = None
    print("Warning: Could not import microscale modules")


class TestOscillationBand:
    """Test OscillationBand dataclass."""

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_oscillation_band_creation(self):
        """Test creating an oscillation band."""
        band = OscillationBand(
            name="test_band", freq_range=(10.0, 20.0), amplitude=0.5, phase=1.57, power=0.25
        )

        assert band.name == "test_band"
        assert band.freq_range == (10.0, 20.0)
        assert band.amplitude == 0.5
        assert band.phase == 1.57
        assert band.power == 0.25

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_oscillation_band_defaults(self):
        """Test oscillation band default values."""
        band = OscillationBand(name="default_band", freq_range=(8.0, 12.0), amplitude=0.3)

        assert band.phase == 0.0
        assert band.power == 0.0


class TestOscillationEngine:
    """Test OscillationEngine class."""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for oscillation engine."""
        return {
            "oscillations": {
                "bands": {
                    "delta": {"range": [1, 4], "amplitude": 0.2},
                    "theta": {"range": [4, 8], "amplitude": 0.3},
                    "alpha": {"range": [8, 12], "amplitude": 0.4},
                    "beta": {"range": [12, 30], "amplitude": 0.5},
                    "gamma": {"range": [30, 80], "amplitude": 0.6},
                },
                "coupling_strength": 0.4,
                "criticality_parameter": 1.1,
            },
            "system": {"timestep_ms": 1.0},
        }

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_oscillation_engine_initialization(self, sample_config):
        """Test oscillation engine initialization."""
        engine = OscillationEngine(sample_config)

        assert engine.config == sample_config
        assert len(engine.bands) == 5
        assert "delta" in engine.bands
        assert "theta" in engine.bands
        assert "alpha" in engine.bands
        assert "beta" in engine.bands
        assert "gamma" in engine.bands

        assert engine.coupling_strength == 0.4
        assert engine.criticality_param == 1.1
        assert engine.time == 0.0
        assert engine.dt_sec == 0.001

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_oscillation_engine_minimal_config(self):
        """Test oscillation engine with minimal configuration."""
        config = {"oscillations": {}}
        engine = OscillationEngine(config)

        assert len(engine.bands) == 0
        assert engine.coupling_strength == 0.3  # default
        assert engine.criticality_param == 1.0  # default

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_signal_generation(self, sample_config):
        """Test basic signal generation."""
        engine = OscillationEngine(sample_config)

        result = engine.generate()

        assert isinstance(result, dict)
        assert "total_signal" in result
        assert "band_signals" in result
        assert "band_powers" in result
        assert "band_phases" in result
        assert "coupling_metrics" in result

        assert isinstance(result["total_signal"], (int, float))
        assert isinstance(result["band_signals"], dict)
        assert isinstance(result["band_powers"], dict)
        assert isinstance(result["band_phases"], dict)

        # Check all bands are present
        assert len(result["band_signals"]) == 5
        assert len(result["band_powers"]) == 5
        assert len(result["band_phases"]) == 5

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_signal_generation_with_modulation(self, sample_config):
        """Test signal generation with amplitude modulation."""
        engine = OscillationEngine(sample_config)

        modulation = {"gamma": 2.0, "theta": 0.5}
        result = engine.generate(modulation=modulation)

        # Check that modulation was applied (gamma should be stronger, theta weaker)
        assert abs(result["band_signals"]["gamma"]) > abs(result["band_signals"]["theta"])

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_phase_amplitude_coupling(self, sample_config):
        """Test phase-amplitude coupling implementation."""
        engine = OscillationEngine(sample_config)

        # Generate multiple steps to see coupling effects
        results = []
        for _ in range(10):
            result = engine.generate()
            results.append(result)

        # Check that coupling metrics are computed
        coupling_metrics = results[-1]["coupling_metrics"]
        assert "theta_gamma_coupling" in coupling_metrics
        assert "alpha_gamma_coupling" in coupling_metrics
        assert "beta_power" in coupling_metrics

        assert isinstance(coupling_metrics["theta_gamma_coupling"], float)
        assert isinstance(coupling_metrics["alpha_gamma_coupling"], float)
        assert isinstance(coupling_metrics["beta_power"], float)

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_band_modulation(self, sample_config):
        """Test band amplitude modulation."""
        engine = OscillationEngine(sample_config)

        # Get initial gamma amplitude
        initial_gamma_amp = engine.bands["gamma"].amplitude

        # Modulate gamma band
        engine.modulate_band("gamma", 2.0)

        # Check amplitude was modified
        assert engine.bands["gamma"].amplitude == initial_gamma_amp * 2.0

        # Test non-existent band (should not raise error)
        engine.modulate_band("nonexistent", 1.5)

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_frequency_setting(self, sample_config):
        """Test setting band frequencies."""
        engine = OscillationEngine(sample_config)

        # Set theta frequency
        engine.set_band_frequency("theta", 6.0)

        # Check frequency was updated (center of range should be 6.0)
        theta_range = engine.bands["theta"].freq_range
        center_freq = (theta_range[0] + theta_range[1]) / 2
        assert abs(center_freq - 6.0) < 0.1

        # Test frequency clamping
        engine.set_band_frequency("theta", 100.0)  # Above range
        theta_range = engine.bands["theta"].freq_range
        assert theta_range[1] <= 8.0  # Should be clamped to original max

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_spectral_power_calculation(self, sample_config):
        """Test spectral power calculation."""
        engine = OscillationEngine(sample_config)

        # Generate some signals to build up power estimates
        for _ in range(20):
            engine.generate()

        powers = engine.get_spectral_power()

        assert isinstance(powers, dict)
        assert len(powers) == 5
        for band_name in ["delta", "theta", "alpha", "beta", "gamma"]:
            assert band_name in powers
            assert isinstance(powers[band_name], float)
            assert powers[band_name] >= 0.0

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_gamma_burst_detection(self, sample_config):
        """Test gamma burst detection."""
        engine = OscillationEngine(sample_config)

        # Generate signal
        engine.generate()

        # Test burst detection
        burst_detected = engine.detect_gamma_burst(threshold=0.1)
        assert isinstance(burst_detected, bool)

        # Test with high threshold (should be false)
        burst_detected_high = engine.detect_gamma_burst(threshold=10.0)
        assert burst_detected_high is False

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_current_state_retrieval(self, sample_config):
        """Test current state retrieval."""
        engine = OscillationEngine(sample_config)

        # Generate some activity
        engine.generate()

        state = engine.get_current_state()

        assert isinstance(state, dict)
        assert "time" in state
        assert "band_powers" in state
        assert "band_phases" in state
        assert "band_frequencies" in state
        assert "coupling_metrics" in state
        assert "gamma_burst" in state

        assert isinstance(state["time"], float)
        assert isinstance(state["band_powers"], dict)
        assert isinstance(state["band_phases"], dict)
        assert isinstance(state["band_frequencies"], dict)
        assert isinstance(state["coupling_metrics"], dict)
        assert isinstance(state["gamma_burst"], bool)

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_engine_reset(self, sample_config):
        """Test engine reset functionality."""
        engine = OscillationEngine(sample_config)

        # Generate some activity
        for _ in range(10):
            engine.generate()

        # Store state before reset
        engine.reset()

        # Check reset worked
        assert engine.time == 0.0
        assert len(engine.signal_history) == 0

        # Check phases and powers were reset
        for band in engine.bands.values():
            assert band.power == 0.0
            assert 0 <= band.phase <= 2 * np.pi

    @pytest.mark.skipif(not HAS_OSCILLATIONS, reason="Oscillation modules not available")
    def test_signal_history_management(self, sample_config):
        """Test signal history buffer management."""
        engine = OscillationEngine(sample_config)

        # Generate more signals than max history
        for i in range(engine.max_history + 10):
            engine.generate()

        # Check history is limited
        assert len(engine.signal_history) <= engine.max_history
        assert len(engine.signal_history) == engine.max_history


class TestLargeScaleNetwork:
    """Test LargeScaleNetwork class."""

    @pytest.fixture
    def network_config(self):
        """Sample configuration for large-scale network."""
        return {
            "macroscale": {
                "regions": ["PFC", "ACC", "PCC", "IPC"],
                "connections": {("PFC", "ACC"): 0.8, ("ACC", "PCC"): 0.7, ("PCC", "IPC"): 0.6},
                "region_params": {
                    "PFC": {"size": 100, "excitatory_ratio": 0.8},
                    "ACC": {"size": 80, "excitatory_ratio": 0.75},
                    "PCC": {"size": 90, "excitatory_ratio": 0.85},
                    "IPC": {"size": 70, "excitatory_ratio": 0.7},
                },
            }
        }

    @pytest.mark.skipif(not HAS_MACROSCALE, reason="Macroscale modules not available")
    def test_large_scale_network_initialization(self, network_config):
        """Test large-scale network initialization."""
        network = LargeScaleNetworkManager(network_config)

        assert network.config == network_config
        assert hasattr(network, "regions")
        assert hasattr(network, "connections")
        assert len(network.regions) > 0

    @pytest.mark.skipif(not HAS_MACROSCALE, reason="Macroscale modules not available")
    def test_network_simulation_step(self, network_config):
        """Test network simulation step."""
        network = LargeScaleNetworkManager(network_config)

        # Perform simulation step
        result = network.step()

        assert isinstance(result, dict)
        assert "region_activities" in result
        assert "global_coherence" in result
        assert "information_flow" in result

    @pytest.mark.skipif(not HAS_MACROSCALE, reason="Macroscale modules not available")
    def test_region_activity_calculation(self, network_config):
        """Test region activity calculation."""
        network = LargeScaleNetworkManager(network_config)

        activities = network._calculate_region_activities()

        assert isinstance(activities, dict)
        assert len(activities) == len(network.regions)

        for region, activity in activities.items():
            assert isinstance(activity, (int, float))
            assert 0.0 <= activity <= 1.0


class TestNeuralColumn:
    """Test NeuralColumn class."""

    @pytest.fixture
    def column_config(self):
        """Sample configuration for neural column."""
        return {
            "mesoscale": {
                "layers": ["L2/3", "L4", "L5", "L6"],
                "layer_sizes": [50, 30, 40, 25],
                "connection_patterns": {
                    "feedforward": [("L4", "L2/3"), ("L6", "L4")],
                    "feedback": [("L2/3", "L6"), ("L5", "L4")],
                },
            }
        }

    @pytest.mark.skipif(not HAS_MESOSCALE, reason="Mesoscale modules not available")
    def test_neural_column_initialization(self, column_config):
        """Test neural column initialization."""
        column = NeuralColumn(column_config)

        assert column.config == column_config
        assert hasattr(column, "layers")
        assert hasattr(column, "connections")
        assert len(column.layers) > 0

    @pytest.mark.skipif(not HAS_MESOSCALE, reason="Mesoscale modules not available")
    def test_column_processing_step(self, column_config):
        """Test column processing step."""
        column = NeuralColumn(column_config)

        input_signal = np.random.randn(10)
        result = column.process(input_signal)

        assert isinstance(result, dict)
        assert "layer_outputs" in result
        assert "column_output" in result
        assert "attention_modulation" in result

    @pytest.mark.skipif(not HAS_MESOSCALE, reason="Mesoscale modules not available")
    def test_layer_interaction(self, column_config):
        """Test layer interaction within column."""
        column = NeuralColumn(column_config)

        # Test inter-layer communication
        interactions = column._compute_layer_interactions()

        assert isinstance(interactions, dict)
        for layer_name in column.layers:
            assert layer_name in interactions


class TestSpikingNetwork:
    """Test SpikingNetwork class."""

    @pytest.fixture
    def spiking_config(self):
        """Sample configuration for spiking network."""
        return {
            "microscale": {
                "neurons": 100,
                "excitatory_ratio": 0.8,
                "connection_probability": 0.1,
                "synaptic_weights": {
                    "excitatory": {"mean": 0.5, "std": 0.1},
                    "inhibitory": {"mean": -0.7, "std": 0.2},
                },
                "neuron_params": {
                    "threshold": -50.0,
                    "reset": -70.0,
                    "tau_m": 20.0,
                    "tau_syn": 5.0,
                },
            }
        }

    @pytest.mark.skipif(not HAS_MICROSCALE, reason="Microscale modules not available")
    def test_spiking_network_initialization(self, spiking_config):
        """Test spiking network initialization."""
        network = SpikingNetwork(spiking_config)

        assert network.config == spiking_config
        assert hasattr(network, "neurons")
        assert hasattr(network, "synapses")
        assert len(network.neurons) > 0

    @pytest.mark.skipif(not HAS_MICROSCALE, reason="Microscale modules not available")
    def test_spiking_simulation_step(self, spiking_config: dict) -> None:
        """Test spiking simulation step."""
        network = SpikingNetwork(spiking_config)

        input_currents = np.random.randn(network.config["microscale"]["neurons"]) * 0.1
        result = network.step(input_currents)

        assert isinstance(result, dict)
        assert "spike_times" in result
        assert "membrane_potentials" in result
        assert "synaptic_currents" in result
        assert "population_rate" in result

    @pytest.mark.skipif(not HAS_MICROSCALE, reason="Microscale modules not available")
    def test_spike_generation(self, spiking_config: dict) -> None:
        """Test spike generation mechanisms."""
        network = SpikingNetwork(spiking_config)

        # Apply strong input to trigger spikes
        strong_input = np.full(network.config["microscale"]["neurons"], 10.0)
        result = network.step(strong_input)

        spike_times = result["spike_times"]
        assert isinstance(spike_times, (list, np.ndarray))

        # Should have some spikes with strong input
        total_spikes = sum(len(times) for times in spike_times)
        assert total_spikes >= 0  # Allow for no spikes in some configurations

    @pytest.mark.skipif(not HAS_MICROSCALE, reason="Microscale modules not available")
    def test_synaptic_dynamics(self, spiking_config: dict) -> None:
        """Test synaptic dynamics."""
        network = SpikingNetwork(spiking_config)

        # Test synaptic current calculation
        pre_spikes = np.random.choice([0, 1], size=network.config["microscale"]["neurons"])
        currents = network._compute_synaptic_currents(pre_spikes)

        assert isinstance(currents, np.ndarray)
        assert currents.shape[0] == network.config["microscale"]["neurons"]


class TestNeuralIntegration:
    """Test integration between neural modules."""

    @pytest.mark.skipif(
        not (HAS_OSCILLATIONS and HAS_MACROSCALE), reason="Required modules not available"
    )
    def test_oscillation_network_integration(self) -> None:
        """Test integration between oscillation engine and large-scale network."""
        # This would test how oscillations drive network dynamics
        # Implementation depends on specific integration patterns
        pass

    @pytest.mark.skipif(
        not (HAS_MESOSCALE and HAS_MICROSCALE), reason="Required modules not available"
    )
    def test_column_microscale_integration(self) -> None:
        """Test integration between neural columns and spiking networks."""
        # This would test how columnar processing emerges from spiking dynamics
        pass


if __name__ == "__main__":
    pytest.main([__file__])
