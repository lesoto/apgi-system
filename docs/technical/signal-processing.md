# Real-Time Signal Processing Pipeline

This module implements a comprehensive real-time signal processing pipeline for multi-modal data acquisition in APGI parameter estimation experiments.

## Overview

The signal processing pipeline integrates:

- **EEG Processing**: Filtering, artifact detection (FASTER algorithm), and ERP extraction (P3b, HEP)
- **Pupillometry Processing**: Blink detection, artifact interpolation, and feature extraction
- **Cardiac Processing**: R-peak detection, HRV analysis, and HEP extraction
- **Quality Control**: Real-time quality monitoring, adaptive protocol management, and operator notifications

## Components

### 1. EEG Signal Processing (`eeg_processor.py`)

#### EEGProcessor

Real-time EEG signal processor with bandpass filtering (0.1-30 Hz) and notch filtering for power line noise.

```python
from apgi_framework.neural import EEGProcessor

processor = EEGProcessor(
    sampling_rate=1000.0,
    highpass=0.1,
    lowpass=30.0,
    notch_freq=60.0
)

# Process real-time data

processed = processor.process_realtime(raw_eeg_data, timestamps, channels)
```

#### FASTERArtifactDetector

Fully Automated Statistical Thresholding for EEG artifact Rejection.

```python
from apgi_framework.neural import FASTERArtifactDetector

detector = FASTERArtifactDetector(z_threshold=3.0)
cleaned_data, artifact_report = detector.clean(eeg_data)
```

#### ERPExtractor

Extract event-related potentials (P3b at Pz: 250-500ms, HEP: 250-400ms post R-peak).

```python
from apgi_framework.neural import ERPExtractor

erp_extractor = ERPExtractor(sampling_rate=1000.0)

# Extract P3b features

features = erp_extractor.extract_features(
    eeg_data,
    event_times,
    timestamps,
    pz_channel_idx,
    r_peak_times
)

print(f"P3b amplitude: {features.p3b_amplitude} µV")
print(f"HEP amplitude: {features.hep_amplitude} µV")
```

### 2. Pupillometry Signal Processing (`pupillometry_processor.py`)

#### PupillometryProcessor

Integrates blink detection and artifact interpolation for clean pupil signals.

```python
from apgi_framework.neural import PupillometryProcessor

processor = PupillometryProcessor(sampling_rate=1000.0)

# Process trial data

processed = processor.process_trial(
    pupil_data,
    timestamps,
    confidence,
    baseline_window=(-0.5, 0.0),
    stimulus_time=0.0
)
```

#### PupilFeatureExtractor

Extract pupil dilation features from post-stimulus windows (200-500ms).

```python
from apgi_framework.neural import PupilFeatureExtractor

extractor = PupilFeatureExtractor(sampling_rate=1000.0)

features = extractor.extract_window_features(
    pupil_data,
    timestamps,
    stimulus_time,
    window=(0.2, 0.5)
)

print(f"Peak dilation: {features.peak_dilation} mm")
print(f"Time to peak: {features.time_to_peak} ms")
print(f"Percent change: {features.percent_change}%")
```

#### PupilQualityScorer

Comprehensive data quality assessment for pupillometry.

```python
from apgi_framework.neural import PupilQualityScorer

scorer = PupilQualityScorer(sampling_rate=1000.0)

quality = scorer.assess_quality(
    pupil_data,
    confidence,
    blinks,
    artifacts
)

print(f"Overall quality: {quality.overall_quality}")
print(f"Recommendation: {quality.recommendation}")
```

### 3. Cardiac Signal Processing (`cardiac_processor.py`)

#### CardiacProcessor

Multi-algorithm R-peak detection (Pan-Tompkins, adaptive threshold).

```python
from apgi_framework.neural import CardiacProcessor, RPeakAlgorithm

processor = CardiacProcessor(
    sampling_rate=1000.0,
    algorithm=RPeakAlgorithm.PAN_TOMPKINS
)

# Detect R-peaks
r_peaks = processor.detect_r_peaks(ecg_signal, timestamps)
```

#### HRVAnalyzer

Comprehensive HRV analysis with time and frequency domain metrics.

```python
from apgi_framework.neural import HRVAnalyzer

analyzer = HRVAnalyzer(sampling_rate=1000.0)
hrv_metrics = analyzer.analyze_hrv(r_peaks, timestamps)

print(f"SDNN: {hrv_metrics.sdnn} ms")
print(f"RMSSD: {hrv_metrics.rmssd} ms")
print(f"LF/HF ratio: {hrv_metrics.lf_hf_ratio}")
```

#### HEPExtractor

Extract heartbeat-evoked potentials from EEG data.

```python
from apgi_framework.neural import HEPExtractor

extractor = HEPExtractor(sampling_rate=1000.0)
hep_features = extractor.extract_hep(
    eeg_data,
    eeg_timestamps,
    r_peak_times
)
```

### 4. Quality Control System (`quality_control.py`)

#### SignalQualityMonitor

Real-time quality monitoring integrating all modalities.

```python
from apgi_framework.neural import SignalQualityMonitor

monitor = SignalQualityMonitor(update_interval=1.0)

# Update quality metrics

quality_metrics = monitor.update_quality_metrics(
    eeg_metrics,
    pupil_metrics,
    cardiac_metrics
)

print(f"Overall quality: {quality_metrics.overall_quality}")
print(f"Quality level: {quality_metrics.quality_level.value}")
print(f"Continue recording: {quality_metrics.continue_recording}")
```

#### OperatorNotificationSystem

Real-time alerts and recovery suggestions for operators.

```python
from apgi_framework.neural import OperatorNotificationSystem

notification_system = OperatorNotificationSystem()

def handle_notification(notification):
    print(f"Alert: {notification['message']}")
    print(f"Suggestion: {notification.get('recovery_suggestion', 'N/A')}")

notification_system.register_callback(handle_notification)

# Send quality update

notification_system.send_quality_update(quality_metrics)
```

#### AdaptiveProtocolManager

Automatically adjust protocols based on quality metrics.

```python
from apgi_framework.neural import AdaptiveProtocolManager

manager = AdaptiveProtocolManager()

# Evaluate adjustments

adjustments = manager.evaluate_protocol_adjustments(quality_metrics)

if adjustments['adjustments_needed']:
    for recommendation in adjustments['recommendations']:
        print(f"Action: {recommendation['action']}")
        print(f"Reason: {recommendation['reason']}")
```

## Integrated Workflow

### Complete Parameter Estimation Pipeline

```python
from apgi_framework.neural import (
    EEGProcessor, PupillometryProcessor, CardiacProcessor,
    ERPExtractor, PupilFeatureExtractor, HRVAnalyzer,
    SignalQualityMonitor, OperatorNotificationSystem
)

# Initialize processors

eeg_processor = EEGProcessor(sampling_rate=1000.0)
pupil_processor = PupillometryProcessor(sampling_rate=1000.0)
cardiac_processor = CardiacProcessor(sampling_rate=1000.0)

# Initialize quality control

quality_monitor = SignalQualityMonitor()
notification_system = OperatorNotificationSystem()

# Process data in real-time

while recording:
    # Acquire data
    eeg_data, eeg_timestamps = acquire_eeg()
    pupil_data, pupil_timestamps = acquire_pupil()
    ecg_data, ecg_timestamps = acquire_ecg()
    
    # Process signals
    processed_eeg = eeg_processor.process_realtime(eeg_data, eeg_timestamps, channels)
    processed_pupil = pupil_processor.process_trial(pupil_data, pupil_timestamps, confidence)
    r_peaks = cardiac_processor.detect_r_peaks(ecg_data, ecg_timestamps)
    
    # Extract features
    erp_features = erp_extractor.extract_features(processed_eeg.data, event_times, ...)
    pupil_features = pupil_extractor.extract_window_features(processed_pupil['clean_data'], ...)
    hrv_metrics = hrv_analyzer.compute_comprehensive_hrv(rr_intervals, r_peaks)
    
    # Monitor quality
    quality_metrics = quality_monitor.update_quality_metrics(
        eeg_quality_metrics,
        pupil_quality_metrics,
        cardiac_quality_metrics
    )
    
    # Send notifications if needed
    if quality_metrics.active_alerts > 0:
        notification_system.send_quality_update(quality_metrics)
    
    # Check if recording should continue
    if not quality_metrics.continue_recording:
        print("Quality too low - pausing recording")
        break
```

## Quality Thresholds

Default quality thresholds (configurable):

| Metric | Threshold | Description | Units |
| --- | --- | --- | --- |
| EEG Quality | >= 0.6 | Minimum acceptable EEG quality | - |
| EEG Artifact Rate | <= 15% | Maximum artifact percentage | % |
| EEG Bad Channels | <= 5 | Maximum number of bad channels | count |
| Pupil Quality | >= 0.6 | Minimum pupillometry quality | - |
| Pupil Data Loss | <= 20% | Maximum data loss percentage | % |
| Pupil Tracking Confidence | >= 0.7 | Minimum tracking confidence | - |
| Cardiac Quality | >= 0.6 | Minimum cardiac signal quality | - |
| Cardiac SQI | >= 0.7 | Minimum signal quality index | - |
| Cardiac Ectopic Rate | <= 5% | Maximum ectopic beat percentage | % |
| Overall Quality | >= 0.5 | Minimum overall quality to continue | - |

## Quality Levels

- **Excellent** (≥ 0.8): Optimal data quality
- **Good** (0.6-0.8): Acceptable quality with minor issues
- **Acceptable** (0.4-0.6): Usable but with quality concerns
- **Poor** (0.2-0.4): Significant quality issues
- **Critical** (< 0.2): Unusable data quality

## Examples

See `example_signal_processing.py` for complete working examples of:

1. EEG processing with artifact detection and ERP extraction
2. Pupillometry processing with feature extraction
3. Cardiac processing with HRV analysis
4. Integrated quality control across all modalities

Run the examples:

```bash
python -m apgi_framework.neural.example_signal_processing
```

## Requirements

The signal processing pipeline requires:

- `numpy`: Array operations and numerical computing
- `scipy`: Signal filtering and spectral analysis
- Python 3.7+

## Integration with Parameter Estimation

This signal processing pipeline is designed to support the three core parameter estimation tasks:

1. **Baseline Ignition Threshold (θ₀)**: P3b amplitude extraction from detection tasks
2. **Interoceptive Precision (Πᵢ)**: HEP and pupil dilation features from heartbeat detection
3. **Somatic Bias (β)**: P3b ratio computation from dual-modality oddball tasks

The extracted features feed directly into the hierarchical Bayesian modeling pipeline for parameter estimation.

## Performance Considerations

- **Real-time Processing**: All processors support streaming data with minimal latency
- **Memory Efficiency**: Circular buffers prevent memory growth during long recordings
- **Computational Load**: Filtering and artifact detection optimized for real-time performance
- **Quality Monitoring**: Lightweight quality checks run at configurable intervals (default: 1 Hz)

## Troubleshooting

### High Artifact Rates

- Check electrode impedances (EEG)
- Minimize participant movement
- Adjust artifact detection thresholds

### Poor Pupil Tracking

- Recalibrate eye tracker
- Adjust lighting conditions
- Check participant head position

### Cardiac Signal Issues

- Verify electrode placement
- Check skin contact quality
- Reduce movement artifacts

### Quality Alerts

- Follow recovery suggestions in notifications
- Use adaptive protocol manager for automatic adjustments
- Consider pausing recording if quality is critical

## Citation

If you use this signal processing pipeline in your research, please cite:

```text
[APGI Framework Parameter Estimation Pipeline]
Real-time multi-modal signal processing for interoceptive parameter estimation
```
