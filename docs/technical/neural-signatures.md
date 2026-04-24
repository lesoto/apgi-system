# Neural Data Acquisition and Processing Pipeline

This module provides comprehensive neural data acquisition and processing capabilities for the APGI framework, including EEG/MEG interfaces, ERP analysis, microstate analysis, and gamma synchrony detection.

## Components

### 1. EEG/MEG Interface (`eeg_interface.py`)

Real-time EEG/MEG data acquisition with streaming, buffering, and artifact detection.

**Key Classes:**

- `EEGInterface`: Main interface for data acquisition
- `EEGConfig`: Configuration for sampling rate, channels, filtering
- `ArtifactDetector`: Real-time artifact detection (amplitude, gradient, flatline)
- `ChannelInfo`: Channel metadata and impedance tracking

#### EEG Interface Features

- Real-time data streaming with configurable callbacks
- Multi-channel buffering with timestamp synchronization
- Automatic artifact detection and rejection
- Channel impedance monitoring
- Reference scheme configuration (average, mastoid, custom)
- Data export (NumPy, CSV formats)

#### EEG Interface Example Usage

```python
from apgi_framework.neural import EEGInterface, EEGConfig, ChannelInfo, ChannelType

# Configure EEG system

channels = [
    ChannelInfo("Fz", ChannelType.EEG, position=(0, 0.5, 0.8)),
    ChannelInfo("Cz", ChannelType.EEG, position=(0, 0, 1.0)),
    ChannelInfo("Pz", ChannelType.EEG, position=(0, -0.5, 0.8)),
]

config = EEGConfig(
    sampling_rate=1000.0,
    channels=channels,
    reference_type="average",
    artifact_threshold=100.0
)

# Initialize interface

eeg = EEGInterface(config)

# Register callback for real-time processing

def process_data(data, timestamp, artifacts):
    print(f"Received {data.shape[1]} samples at {timestamp}")
    if artifacts['any'].any():
        print("Artifacts detected!")

eeg.register_callback(process_data)

# Start streaming

eeg.start_streaming()

# ... run experiment 

# Stop and export

eeg.stop_streaming()
eeg.export_data("experiment_data.npz", format="numpy")
```json

### 2. ERP Analysis (`erp_analysis.py`)

Event-Related Potential extraction with P3b and early component analysis.

#### ERP Key Classes

- `ERPAnalysis`: Main ERP analysis engine
- `ERPComponents`: Container for all extracted components
- `P3bMetrics`: Detailed P3b measurements

#### ERP Features

- P3b peak detection with area-under-curve calculation
- Early component extraction (P1, N1, N170)
- Single-trial ERP estimation (wavelet, adaptive, matched filter)
- Baseline correction and filtering
- Grand average computation with artifact rejection
- Bootstrap confidence intervals

#### ERP Example Usage

```python
from apgi_framework.neural import ERPAnalysis

# Initialize analyzer

erp = ERPAnalysis(sampling_rate=1000.0)

# Extract components from averaged ERP

components = erp.extract_all_components(
    data=averaged_erp,
    time_zero_idx=200,  # Stimulus at 200ms
    channel="Pz"
)

print(f"P3b amplitude: {components.p3b_amplitude:.2f} µV")
print(f"P3b latency: {components.p3b_latency:.2f} ms")
print(f"P3b area: {components.p3b_area:.2f} µV·ms")

# Single-trial estimation

single_trial_erp = erp.single_trial_estimation(
    trial_data=raw_trial,
    time_zero_idx=200,
    method='wavelet'
)

# Compute grand average with artifact rejection

grand_avg, n_accepted = erp.compute_grand_average(
    trials=all_trials,
    reject_threshold=100.0
)
```python

### 3. Microstate Analysis (`microstate_analysis.py`)

Scalp topography clustering and temporal dynamics analysis.

#### Microstate Key Classes

- `MicrostateAnalysis`: Microstate clustering and analysis
- `MicrostateSequence`: Container for sequence data and metrics

#### Microstate Features

- Modified K-means clustering for microstate templates
- Global Field Power (GFP) computation
- Polarity-invariant template matching
- Temporal metrics (duration, occurrence, coverage)
- Transition probability matrices
- Posterior-to-anterior transition detection

#### Microstate Example Usage

```python
from apgi_framework.neural import MicrostateAnalysis

# Initialize analyzer

ms = MicrostateAnalysis(n_states=4, sampling_rate=1000.0)

# Fit microstate templates from data

templates = ms.fit_microstates(eeg_data, use_gfp_peaks=True)

# Analyze sequence

sequence = ms.analyze_sequence(eeg_data, smooth=True)

print(f"Microstate coverage: {sequence.coverage}")
print(f"Transition matrix:\n{sequence.transition_matrix}")

# Detect ignition-relevant transitions

transitions = ms.detect_posterior_to_anterior_transitions(
    sequence, channel_positions
)
print(f"Found {len(transitions)} posterior-to-anterior transitions")
```json

### 4. Gamma Synchrony Analysis (`gamma_synchrony.py`)

Long-range coherence and cross-frequency coupling analysis.

#### Gamma Synchrony Key Classes

- `GammaSynchronyAnalysis`: Gamma-band analysis engine
- `CoherenceMetrics`: Coherence measurements
- `NetworkConnectivity`: Network-level connectivity metrics

#### Gamma Synchrony Features

- Gamma-band coherence computation
- Phase-amplitude coupling (PAC) detection
- Cross-frequency coupling (CFC) analysis
- Frontal-posterior coherence measurement
- Network connectivity matrices
- Graph metrics (clustering, path length, small-worldness)
- Gamma burst detection

#### Gamma Synchrony Example Usage

```python
from apgi_framework.neural import GammaSynchronyAnalysis

# Initialize analyzer

gamma = GammaSynchronyAnalysis(sampling_rate=1000.0)

### Compute coherence between two channels

metrics = gamma.compute_gamma_coherence(
    signal1=eeg_data[frontal_channel],
    signal2=eeg_data[posterior_channel],
    channel_pair=("Fz", "Pz")
)

print(f"Gamma coherence: {metrics.gamma_coherence:.3f}")
print(f"Peak frequency: {metrics.gamma_peak_freq:.1f} Hz")
print(f"Phase locking value: {metrics.phase_locking_value:.3f}")

### Compute phase-amplitude coupling

pac = gamma.compute_phase_amplitude_coupling(
    low_freq_signal=eeg_data[0],
    high_freq_signal=eeg_data[0],
    phase_band=(4, 8),  # Theta
    amp_band=(30, 80)   # Gamma
)
print(f"Theta-gamma PAC: {pac:.3f}")

### Network analysis

network = gamma.analyze_network_connectivity(
    data=eeg_data,
    channel_names=channel_names,
    frontal_channels=[0, 1, 2],
    posterior_channels=[10, 11, 12]
)

print(f"Frontal-posterior coherence: {network.frontal_posterior_coherence:.3f}")
print(f"Small-worldness: {network.small_worldness:.3f}")

### Detect gamma bursts

bursts = gamma.detect_gamma_bursts(
    data=eeg_data[0],
    threshold=2.0,
    min_duration=50.0
)
print(f"Detected {len(bursts)} gamma bursts")
```json

## Integration with APGI Framework

The neural processing pipeline integrates with the APGI framework to validate key predictions:

1. **Threshold Estimation**: ERP analysis validates ignition threshold predictions
2. **Ignition Cascade**: Microstate analysis detects posterior-to-anterior transitions
3. **Long-range Integration**: Gamma synchrony measures frontal-posterior coherence
4. **Neuromodulation**: ERP changes under pharmacological manipulation

## Requirements

- NumPy
- SciPy
- scikit-learn

## Testing

Unit tests are marked as optional in the implementation plan. To run tests if implemented:

```bash
pytest apgi_framework/tests/test_neural_*.py
```python

## References

- P3b component: Polich, J. (2007). Updating P300: An integrative theory
- Microstates: Michel, C. M., & Koenig, T. (2018). EEG microstates
- Gamma synchrony: Fries, P. (2015). Rhythms for cognition
- Phase-amplitude coupling: Tort et al. (2010). Measuring PAC
