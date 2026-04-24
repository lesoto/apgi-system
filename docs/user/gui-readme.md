# APGI Parameter Estimation GUI

Comprehensive graphical user interface for running parameter estimation experiments in the APGI Framework.

## Overview

The GUI provides a unified interface for conducting parameter estimation experiments that extract three core APGI parameters:

- **θ₀** (Baseline Ignition Threshold) - via detection task
- **Πᵢ** (Interoceptive Precision) - via heartbeat detection task
- **β** (Somatic Bias) - via dual-modality oddball task

## Features

### 1. Session Management

- Create and manage experimental sessions
- Track participant information
- Configure protocol parameters
- Session history and retrieval

### 2. Task Control

- **Detection Task**: Visual/auditory detection with adaptive staircase
- **Heartbeat Detection Task**: Cardiac-locked tone presentation with confidence ratings
- **Oddball Task**: Precision-matched interoceptive/exteroceptive deviants

### 3. Real-Time Monitoring

- **EEG Monitoring**: Signal quality, artifact rates, P3b/HEP amplitudes
- **Pupillometry**: Pupil diameter, blink rate, data loss tracking
- **Cardiac Monitoring**: Heart rate, HRV, R-peak detection quality
- **Parameter Estimates**: Live Bayesian parameter updates

### 4. Data Quality Management

- Automated quality alerts for all modalities
- Real-time quality scoring
- Artifact detection and reporting
- Hardware failure detection

### 5. Reporting & Export

- Comprehensive session reports
- Parameter visualization with credible intervals
- Data export in multiple formats (CSV, JSON, HDF5, BIDS)
- Quality summaries across all modalities

### 6. Error Handling & Recovery

- Graceful hardware failure handling
- Session pause/resume with state preservation
- Automatic data backup
- User-friendly error guidance

## Usage

### Basic Usage

```python
from pathlib import Path
from apgi_framework.gui import launch_gui

# Launch GUI with database path
db_path = Path("data/parameter_estimation.db")
launch_gui(db_path)
```

### Advanced Usage

```python
from pathlib import Path
from apgi_framework.gui import (
    ParameterEstimationGUI,
    SessionSetupManager,
    TaskParameterConfigurator
)
from apgi_framework.data.parameter_estimation_dao import ParameterEstimationDAO

# Initialize components
db_path = Path("data/parameter_estimation.db")
dao = ParameterEstimationDAO(db_path)

# Create GUI
gui = ParameterEstimationGUI(db_path, title="My Experiment")

# Configure tasks
gui.task_configurator.update_detection_config(
    n_trials=250,
    modality="visual"
)

# Run GUI
gui.run()
```

## Architecture

### Main Components

1. **ParameterEstimationGUI**: Main application window with tabbed interface
2. **SessionSetupManager**: Session creation and management
3. **ParticipantManager**: Participant tracking and metadata
4. **TaskParameterConfigurator**: Task parameter configuration
5. **RealTimeProgressMonitor**: Progress tracking and ETA calculation

### Monitoring Components

1. **LiveEEGMonitor**: Real-time EEG quality and neural signatures
2. **PupillometryMonitor**: Pupil measurements and quality
3. **CardiacMonitor**: Heart rate and HRV monitoring
4. **RealTimeParameterEstimateUpdater**: Live Bayesian estimates
5. **QualityAlertSystem**: Automated quality issue detection

### Reporting Components

1. **SessionReportGenerator**: Comprehensive session reports
2. **ParameterVisualizationEngine**: Parameter plots and distributions
3. **DataQualitySummarizer**: Quality metrics aggregation
4. **DataExporter**: Multi-format data export

### Error Handling Components

1. **HardwareFailureHandler**: Hardware failure detection and recovery
2. **SessionStateManager**: State preservation for pause/resume
3. **AutomaticBackupSystem**: Real-time data backup
4. **UserGuidanceSystem**: Error messages and recovery instructions

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- numpy
- matplotlib (optional, for visualizations)
- scipy (for signal processing)

## Configuration

Task parameters can be configured through the GUI or programmatically:

```python
# Detection task configuration
gui.task_configurator.update_detection_config(
    n_trials=200,
    modality="visual",
    stimulus_min=0.01,
    stimulus_max=1.0
)

# Heartbeat task configuration
gui.task_configurator.update_heartbeat_config(
    n_trials=60,
    initial_asynchrony_ms=300.0
)

# Oddball task configuration
gui.task_configurator.update_oddball_config(
    n_trials=120,
    deviant_probability=0.2
)
```

## Data Storage

All data is stored in SQLite database with the following structure:

- `parameter_estimation_sessions`: Session metadata
- `parameter_estimation_trials`: Trial-level data
- `detection_trials`: Detection task specific data
- `heartbeat_trials`: Heartbeat task specific data
- `oddball_trials`: Oddball task specific data
- `parameter_estimates`: Bayesian parameter estimates

## Error Recovery

The system provides multiple levels of error recovery:

1. **Hardware Failures**: Automatic detection and graceful degradation
2. **Session Interruptions**: State preservation and resume capability
3. **Data Loss**: Automatic backups every 5 minutes
4. **User Guidance**: Step-by-step recovery instructions

## Best Practices

1. **Before Starting**:
   - Verify all hardware connections
   - Check electrode impedances
   - Calibrate eye tracker
   - Test cardiac sensor

2. **During Session**:
   - Monitor data quality indicators
   - Respond to quality alerts promptly
   - Save session state periodically

3. **After Session**:
   - Review session report
   - Export data for analysis
   - Check parameter convergence
   - Archive session data

## Troubleshooting

### EEG Issues

- Check electrode impedances (should be < 10 kΩ)
- Verify amplifier connection
- Check for electrical interference

### Eye Tracker Issues

- Recalibrate if tracking quality drops
- Check lighting conditions
- Verify participant positioning

### Cardiac Issues

- Check sensor placement
- Verify cable connections
- Try repositioning sensor

## Future Enhancements

### Potential Improvements

1. **Advanced Visualizations**: Real-time EEG/pupil waveforms
2. **Remote Monitoring**: Web-based monitoring dashboard
3. **Automated Analysis**: Post-session parameter estimation pipeline
4. **Multi-Session Analysis**: Longitudinal parameter tracking
5. **Hardware Auto-Detection**: Automatic hardware configuration
6. **Cloud Backup**: Remote data backup and synchronization
