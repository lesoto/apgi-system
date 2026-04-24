# Example Data for APGI Framework

This directory contains sample datasets for testing the APGI framework components.

## Data Structure

### EEG Data (`examples/data/eeg/`)

- Multi-channel EEG recordings
- Sampling rate: 1000 Hz
- Duration: 60 seconds per recording
- Channels: Fz, Cz, Pz, Oz, F3, F4, P3, P4
- Format: CSV files with metadata JSON files

### Pupillometry Data (`examples/data/pupillometry/`)

- Binocular pupil diameter measurements
- Sampling rate: 250 Hz
- Duration: 60 seconds per recording
- Units: millimeters
- Format: CSV files with metadata JSON files

### Cardiac Data (`examples/data/cardiac/`)

- Heart rate and heart rate variability
- Sampling rate: 4 Hz
- Duration: 60 seconds per recording
- Heart rate units: bpm
- HRV units: milliseconds (RMSSD)
- Format: CSV files with metadata JSON files

### Behavioral Data (`examples/data/behavioral/`)

- Reaction time task performance
- 100 trials per subject
- Reaction time units: milliseconds
- Conditions: easy, medium, hard
- Format: CSV files with metadata JSON files

## Usage

```python
from apgi_framework.data import load_example_data

# Load EEG data
eeg_data = load_example_data('eeg', subject_id='subject_001')

# Load pupillometry data
pupil_data = load_example_data('pupillometry', subject_id='subject_001')

# Load cardiac data
cardiac_data = load_example_data('cardiac', subject_id='subject_001')

# Load behavioral data
behavioral_data = load_example_data('behavioral', subject_id='subject_001')
```

## Data Quality

All data is simulated but designed to be realistic for:

- Testing analysis pipelines
- Developing new features
- Demonstrating framework capabilities
- Educational purposes

## Data Categories

### Standard Datasets (`examples/data/{modality}/`)

Basic simulated datasets for each modality:

- **EEG Data**: Clean recordings with normal patterns
- **Pupillometry Data**: Normal pupil responses
- **Cardiac Data**: Regular heart rate and HRV
- **Behavioral Data**: Standard reaction time tasks

### Multimodal Datasets (`examples/data/multimodal/{modality}/`)

Synchronized multimodal recordings with event-related responses:

- **Synchronized Events**: Cross-modality stimulus responses at 30s, 60s, and 90s
- **Event-Related Potentials**: P300-like responses in EEG
- **Task-Evoked Dilation**: Pupil responses synchronized with stimuli
- **Behavioral Correlates**: Reaction time data linked to physiological events

### Pathological Datasets (`examples/data/pathological/{modality}/`)

Simulated pathological patterns for testing detection algorithms:

- **EEG Abnormalities**: Spike-and-wave discharges (epileptiform activity)
- **Pupillometry Abnormalities**: Unusual dilation episodes
- **Cardiac Abnormalities**: Tachycardia episodes and arrhythmia
- **Annotated Events**: Precise timing and description of abnormalities

## Subjects

### Standard Datasets

- subject_001, subject_002, subject_003

### Multimodal Datasets

- multimodal_001, multimodal_002, multimodal_003

### Pathological Datasets

- pathological_001, pathological_002

Each subject has complete data for all modalities within their category.
