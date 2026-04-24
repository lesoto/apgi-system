# Pupillometry and Physiological Monitoring Systems

This document describes the pupillometry and physiological monitoring systems implemented for the APGI framework.

## Overview

The APGI framework now includes comprehensive support for:

- **High-speed pupillometry** with blink detection, artifact correction, and luminance-independent measurements
- **Multi-modal physiological monitoring** including heart rate, skin conductance, and respiration

## PupillometryInterface

### Features

- **High-speed eye tracking** at configurable sampling rates (up to 1000+ Hz)
- **Blink detection** using velocity-based, missing data, or combined methods
- **Artifact interpolation** with linear or cubic spline methods
- **Baseline correction** with multiple methods (median, mean, mode)
- **Luminance-independent dilation** measurement to isolate cognitive effects
- **Real-time streaming** with callback support
- **Data quality assessment** and export capabilities

### Basic Usage

```python
from apgi_framework.neural import (
    PupillometryInterface,
    PupillometryConfig,
    EyeType,
    BlinkDetectionMethod
)

# Configure pupillometry

config = PupillometryConfig(
    sampling_rate=1000.0,  # Hz
    eye_tracked=EyeType.BOTH,
    blink_detection_method=BlinkDetectionMethod.COMBINED,
    enable_luminance_correction=True
)

# Initialize interface

pupil_interface = PupillometryInterface(config)

# Start streaming (with your eye tracker data source)

pupil_interface.start_streaming(data_source=your_eye_tracker_callback)

# Process data

processed = pupil_interface.process_data(
    apply_blink_detection=True,
    apply_artifact_correction=True,
    apply_baseline_correction=True,
    apply_luminance_correction=True
)

# Get quality metrics

quality = pupil_interface.get_quality_metrics()
print(f"Data quality: {quality['status']}")

# Export data

pupil_interface.export_data("pupil_data.npz", format="numpy")

# Stop streaming

pupil_interface.stop_streaming()
```python

### Pupillometry Key Components

- **BlinkDetector**: Detects blinks using velocity or missing data methods
- **ArtifactInterpolator**: Interpolates artifacts and blinks in pupil data
- **BaselineCorrector**: Applies baseline correction and percent change calculations
- **LuminanceCorrector**: Removes luminance-driven pupil changes to isolate cognitive dilation

## PhysiologicalMonitoring

### Physiological Monitoring Features

- **Heart rate monitoring** with R-peak detection and HRV metrics (SDNN, RMSSD, pNN50)
- **Skin conductance** with tonic/phasic decomposition and SCR event detection
- **Respiration monitoring** with breath cycle detection and phase identification
- **Temperature and blood pressure** support
- **Synchronized multi-modal streaming** with configurable sampling rates
- **Real-time callbacks** for online processing
- **Temporal synchronization** with external events (e.g., stimulus presentation)

### Physiological Monitoring Usage

```python
from apgi_framework.neural import (
    PhysiologicalMonitoring,
    PhysiologicalConfig,
    SignalType
)

# Configure physiological monitoring

config = PhysiologicalConfig(
    sampling_rate=1000.0,  # Hz
    enable_ecg=True,
    enable_scr=True,
    enable_respiration=True,
    enable_synchronization=True
)

# Initialize monitoring system

physio_monitor = PhysiologicalMonitoring(config)

# Register callback for real-time processing

def process_sample(sample):
    if sample.heart_rate:
        print(f"HR: {sample.heart_rate:.1f} bpm")

physio_monitor.register_callback(process_sample)

# Start streaming (with your biosignal data sources)

data_sources = {
    SignalType.ECG: your_ecg_callback,
    SignalType.SCR: your_scr_callback,
    SignalType.RESP: your_resp_callback
}
physio_monitor.start_streaming(data_sources=data_sources)

# Get comprehensive metrics

metrics = physio_monitor.compute_comprehensive_metrics()
print(f"Heart rate: {metrics['heart_rate']:.1f} bpm")
print(f"HRV SDNN: {metrics['hrv']['sdnn']:.2f} ms")
print(f"SCR rate: {metrics['scr_rate']:.2f} events/min")
print(f"Respiration rate: {metrics['respiration_rate']:.1f} breaths/min")

# Synchronize with external event

stimulus_time = time.time()
synced_sample = physio_monitor.synchronize_with_external(stimulus_time)

# Export data

physio_monitor.export_data("physio_data.npz", format="numpy")

# Stop streaming

physio_monitor.stop_streaming()
```python

### Key Components

- **HeartRateMonitor**: R-peak detection, RR interval computation, and HRV metrics
- **SkinConductanceMonitor**: Tonic/phasic decomposition and SCR event detection
- **RespirationMonitor**: Breath cycle detection and respiration phase identification

## APGI Experiment Integration

Both systems are designed to integrate seamlessly with APGI experimental paradigms:

### Multi-Modal Recording Setup

```python
from apgi_framework.neural import (
    PupillometryInterface,
    PhysiologicalMonitoring,
    PupillometryConfig,
    PhysiologicalConfig
)

# Create both systems with matched sampling rates

pupil_config = PupillometryConfig(sampling_rate=1000.0)
physio_config = PhysiologicalConfig(sampling_rate=1000.0)

pupil_interface = PupillometryInterface(pupil_config)
physio_monitor = PhysiologicalMonitoring(physio_config)

# Start synchronized streaming

pupil_interface.start_streaming(data_source=eye_tracker)
physio_monitor.start_streaming(data_sources=biosignal_sources)

# During experiment, synchronize with stimulus events

stimulus_time = present_stimulus()

# Get synchronized measurements

pupil_data = pupil_interface.process_data()
physio_sample = physio_monitor.synchronize_with_external(stimulus_time)

# Analyze interoceptive precision modulation

if physio_sample and physio_sample.heart_rate:
    pupil_dilation = pupil_data['percent_change'][-1]
    hr_change = physio_sample.heart_rate - baseline_hr
    
    # Compute interoceptive precision marker
    interoceptive_precision = compute_apgi_precision(
        pupil_dilation, hr_change, physio_sample.scr_response
    )
```python

### Implementation Requirements

This implementation addresses the following APGI framework requirements:

- **Requirement 3.1**: Neural data integration with real-time processing
- **Requirement 5.3**: Physiological monitoring for interoceptive tasks
- **Requirement 6.2**: Pupillometry for precision estimation
- **Requirement 8.3**: Synchronized multi-modal data streaming

## Quality Assurance

Both systems include comprehensive quality assessment:

```python

# Pupillometry quality

pupil_quality = pupil_interface.get_quality_metrics()

# Returns: status, quality_score, mean_confidence, blink_rate, artifact_rate

# Physiological quality

physio_quality = physio_monitor.get_quality_metrics()

# Returns: status, overall_quality, heart_rate_quality, scr_quality, respiration_quality

```python

## System Testing

Run the test suite to verify functionality:

```bash
python apgi_framework/neural/test_physiological_systems.py
```python

This will test:

- Pupillometry interface with simulated data
- Physiological monitoring with simulated biosignals
- Integrated multi-modal synchronization

## Planned Enhancements

Future development may include:

- Integration with specific eye tracker hardware (Tobii, EyeLink, etc.)
- Integration with biosignal acquisition systems (BIOPAC, g.tec, etc.)
- Advanced HRV frequency domain analysis
- Respiratory sinus arrhythmia (RSA) computation
- Real-time adaptive filtering for motion artifacts
- Machine learning-based artifact detection

## References

- **Pupillometry**: Beatty, J., & Lucero-Wagoner, B. (2000). The pupillary system. Handbook of psychophysiology, 2, 142-162.
- **Heart Rate Variability**: Task Force (1996). Heart rate variability: standards of measurement, physiological interpretation and clinical use.
- Skin Conductance: Boucsein, W. (2012). Electrodermal activity. Springer Science & Business Media.
- Respiration: Homma, I., & Masaoka, Y. (2008). Breathing rhythms and emotions. Experimental physiology, 93(9), 1011-1021.
