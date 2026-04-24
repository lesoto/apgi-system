# Clinical Parameter Extraction Guide

## Overview

The Clinical Parameter Extraction module provides a rapid 30-minute assessment battery for extracting individual APGI parameters from experimental data. This system is designed for clinical research and precision medicine applications.

## Core Features

### 1. Standard 30-Minute Assessment Battery

The battery includes 6 standardized tasks:

1. **Visual Threshold Detection** (5 min, 40 trials)
   - Gabor patch detection with adaptive staircase
   - Estimates exteroceptive threshold

2. **Auditory Threshold Detection** (5 min, 40 trials)
   - Tone detection with adaptive staircase
   - Estimates exteroceptive threshold

3. **Heartbeat Detection** (5 min, 30 trials)
   - Mental tracking method
   - Estimates interoceptive awareness

4. **Visual Oddball with ERP** (7 min, 200 trials)
   - P3b extraction for ignition signatures
   - Estimates threshold dynamics

5. **Interoceptive Oddball** (5 min, 10 trials)
   - Breath hold challenges
   - Estimates interoceptive precision

6. **Emotional Stroop** (3 min, 60 trials)
   - Emotional interference measurement
   - Estimates somatic bias

### 2. Extracted Parameters

The system extracts four core APGI parameters:

- **θₜ (Ignition Threshold)**: Range 1.0-6.0
  - Lower values indicate heightened sensitivity
  - Associated with anxiety disorders
  
- **Πₑ (Exteroceptive Precision)**: Range 0.5-4.0
  - Higher values indicate better sensory processing
  - Related to attention and perceptual accuracy
  
- **Πᵢ (Interoceptive Precision)**: Range 0.3-3.5
  - Higher values indicate greater body awareness
  - Elevated in anxiety, reduced in depression
  
- **β (Somatic Bias Weight)**: Range 0.5-3.0
  - Higher values indicate stronger emotional-somatic coupling
  - Elevated in panic disorder and PTSD

### 3. Reliability and Validity Metrics

The system provides comprehensive psychometric evaluation:

- **Test-Retest Reliability**: ICC for each parameter
- **Internal Consistency**: Cronbach's alpha
- **Split-Half Reliability**: Spearman-Brown corrected
- **Criterion Validity**: Correlations with clinical scales
- **Classification Accuracy**: Disorder prediction performance

## Usage Examples

### Basic Parameter Extraction

```python
from apgi_framework.clinical.parameter_extraction import ClinicalParameterExtractor

# Initialize extractor

extractor = ClinicalParameterExtractor(participant_id="P001")

# Create standard battery

battery = extractor.create_standard_battery()

# After data collection, extract parameters

behavioral_data = {
    'visual_threshold': 0.45,
    'auditory_threshold': 0.50,
    'interoceptive_threshold': 0.55,
    'visual_accuracy': 0.80,
    'auditory_accuracy': 0.75,
    'rt_variability': 95.0,
    'heartbeat_accuracy': 0.65,
    'breath_awareness': 0.60,
    'emotional_stroop_interference': 60.0
}

neural_data = {
    'p3b_amplitude': 6.5,
    'gamma_power': 0.6
}

params = extractor.extract_parameters_from_battery(
    battery, behavioral_data, neural_data
)

print(f"Threshold: {params.theta_t:.2f}")
print(f"Interoceptive Precision: {params.pi_i:.2f}")
```json

### Quick Extraction

For rapid assessment without full battery setup:

```python
from apgi_framework.clinical.parameter_extraction import extract_parameters_quick

params = extract_parameters_quick(
    participant_id="P001",
    behavioral_data=behavioral_data,
    neural_data=neural_data
)
```python

### Generate Clinical Report

```python

# Generate comprehensive clinical report

report = extractor.generate_clinical_report(params, reliability_metrics)
print(report)
```python

### Longitudinal Tracking

```python

# Track parameter changes over time

parameter_history = [params_week0, params_week4, params_week8, params_week12]

trends = extractor.track_longitudinal_changes(parameter_history)

for param, stats in trends.items():
    print(f"{param}: {stats['change']:.2f} ({stats['percent_change']:.1f}%)")
```json

### Calculate Reliability Metrics

```python

# Test-retest reliability

reliability = extractor.calculate_reliability_metrics(
    params_time1, 
    params_time2,
    time_interval=timedelta(weeks=1)
)

print(f"Test-retest ICC: {reliability.test_retest_icc}")
```json

## Clinical Interpretation Guidelines

### Threshold (θₜ)

- **< 2.5**: Very low - High risk for anxiety/panic
- **2.5-3.0**: Low - Elevated anxiety sensitivity
- **3.0-4.0**: Normal - Adaptive range
- **> 4.0**: High - Possible anhedonia/depression

### Interoceptive Precision (Πᵢ)

- **< 1.0**: Low - Reduced body awareness
- **1.0-2.0**: Normal - Balanced awareness
- **> 2.5**: High - Heightened body awareness (anxiety)

### Somatic Bias (β)

- **< 0.8**: Low - Reduced emotional processing
- **0.8-1.5**: Normal - Adaptive emotional regulation
- **> 1.8**: High - Strong emotional-somatic coupling

## Treatment Recommendations

Based on parameter profiles:

1. **Low θₜ + High Πᵢ**: Consider SNRI for anxiety with interoceptive focus
2. **High θₜ + Low Πᵢ**: Target interoceptive awareness interventions
3. **High β**: Consider beta-blocker augmentation for somatic symptoms
4. **Normal range**: Monitor longitudinally

## Data Quality Requirements

For reliable parameter extraction:

- **Completion Rate**: ≥ 80% of trials
- **Data Quality**: ≥ 0.70 (scale 0-1)
- **Assessment Duration**: 25-35 minutes
- **Test-Retest Interval**: 1-2 weeks for reliability assessment

## File I/O

### Save Parameters

```python
extractor.save_parameters(params, "participant_P001_params.json")
```json

### Load Parameters

```python
params = extractor.load_parameters("participant_P001_params.json")
```json

## Integration with Other Modules

The parameter extraction module integrates with:

- **Disorder Classification**: Provides features for ML classification
- **Treatment Prediction**: Baseline parameters for response prediction
- **Experimental Control**: Real-time parameter estimation during tasks
- **Statistical Framework**: Validation against evidential standards

## References

See the APGI Framework requirements and design documents for theoretical background and validation criteria.
