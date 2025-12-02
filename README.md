# APGI System: Allostatic Precision-Gated Ignition Framework

A computational implementation of consciousness based on active inference, predictive processing, and allostatic regulation.

## Overview

The APGI framework integrates:

- **Active Inference**: Variational free energy minimization and Bayesian inference
- **Predictive Processing**: Hierarchical prediction error minimization
- **Allostatic Regulation**: Interoceptive predictive processing and homeostatic control
- **Ignition Dynamics**: Threshold-based global workspace broadcasting
- **Self-Modeling**: Minimal and narrative self-representations

# APGI System - Application Validation Report

**Date:** December 2, 2025  
**System:** APGI v0.1.0  
**Platform:** Windows (Python 3.12.9)

### APGI System  ✅

The core APGI system with all subsystems:
- Active Inference Engine
- Hierarchical Predictor
- Precision Weighting
- Body Model
- Allostatic Regulator
- Somatic Marker System
- Ignition Threshold
- Global Workspace
- Self-Model (Minimal & Narrative)
- Metabolic Budget
- Neural Oscillations

### System Step Execution ✅

The system successfully executes simulation steps:
- Processes exteroceptive input (256-dimensional)
- Updates all subsystems
- Returns complete state dictionary
- Tracks ignition events
- Manages workspace broadcasting
- Updates precision and free energy
- Tracks system metrics

### Experimental Tasks ✅

All experimental paradigms are importable and functional:
- Attentional Blink Task
- Change Blindness Task
- Binocular Rivalry Task
- Iowa Gambling Task
- Masking Paradigm Task


### GUI Features Validation ✅

#### Control Panel
- ✓ Start/Pause/Stop/Reset buttons
- ✓ Speed control slider (0.1x - 10x)
- ✓ System status display
- ✓ Quick parameter adjustments (8 sliders)
- ✓ Event log with timestamps

#### Visualization Tabs (6 tabs)
1. ✓ Neural Activity - Ignition events, workspace, precision, free energy
2. ✓ Interoception - Heart rate, cortisol, allostatic load, metabolic reserves
3. ✓ System Metrics - Somatic markers, gamma/beta power
4. ✓ Self-Model - Coherence tracking with thresholds
5. ✓ Oscillations - Signal and power spectrum
6. ✓ State Space - 3D trajectory visualization

#### Menu System
- ✓ File Menu (8 items) - New, Load, Save, Export, Auto-save, Exit
- ✓ Edit Menu (4 items) - Parameters, Precision, Threshold, Reset
- ✓ Simulation Menu (5 items) - Start, Pause, Stop, Reset, Preset Tasks
- ✓ View Menu (7 items) - Panel toggles, Zoom controls
- ✓ Tools Menu (6 items) - Trigger ignition, Induce stressor, Modulate precision
- ✓ Analysis Menu (5 items) - Statistics, Reports, Analysis tools
- ✓ Help Menu (3 items) - Documentation, Shortcuts, About

#### Keyboard Shortcuts
- ✓ Ctrl+N - New Session
- ✓ Ctrl+O - Load Configuration
- ✓ Ctrl+S - Save Configuration
- ✓ Ctrl+E - Export Data
- ✓ Ctrl+Q - Exit
- ✓ F5 - Start Simulation
- ✓ F6 - Pause/Resume
- ✓ F7 - Stop Simulation
- ✓ F8 - Reset System

---

## Functional Testing

### Real-Time Simulation ✅

**Test:** Start simulation and observe updates
- ✓ Simulation thread starts successfully
- ✓ System steps execute at ~1000 Hz
- ✓ GUI updates at 10 Hz (100ms intervals)
- ✓ FPS counter displays correctly
- ✓ Status labels update in real-time

### Parameter Adjustment ✅

**Test:** Modify parameters during simulation
- ✓ Sliders respond immediately
- ✓ Values apply to running system
- ✓ Changes reflected in plots
- ✓ No crashes or errors

### Data Export ✅

**Test:** Export simulation data
- ✓ CSV export format available
- ✓ JSON export format available
- ✓ All metrics included in export
- ✓ Timestamps accurate

### Experimental Tasks ✅

**Test:** Run preset experimental paradigms
- ✓ Task selection dialog works
- ✓ Progress tracking functional
- ✓ Results display correctly
- ✓ Data saved to files
- ✓ Analysis reports generated


## Conclusion


All core features work as documented:
- ✅ Real-time simulation with multi-threaded architecture
- ✅ Comprehensive visualization across 6 tabs
- ✅ Interactive parameter adjustment
- ✅ Complete menu system with all features
- ✅ Data export (CSV/JSON)
- ✅ Experimental task execution
- ✅ Analysis and reporting tools

The application successfully demonstrates:
- Active inference and predictive processing
- Allostatic regulation and interoception
- Ignition dynamics and global workspace
- Self-model coherence tracking
- Metabolic constraints
- Neural oscillations

**Launch Command:**
```bash
python run_gui.py
```

or

```bash
python apgi_gui.py
```


## Architecture

```text
apgi_system/
├── core/               # Active inference and predictive processing
├── neural/             # Multi-scale neural networks
├── interoception/      # Body state modeling and allostasis
├── ignition/           # Global workspace and ignition dynamics
├── self_model/         # Minimal and narrative self
├── thermodynamic/      # Energy budget and entropy tracking
├── experiments/        # Tasks and validation
└── visualization/      # Real-time monitoring
```

## Installation

```bash
pip install -e .
```

## Quick Start

### GUI Application (Recommended)

```bash
# Launch the comprehensive GUI
python run_gui.py

# Or directly
python apgi_gui.py
```

**Features:**

- Real-time visualization of all subsystems
- Interactive parameter adjustment
- Multi-panel displays (6 tabs)
- Complete menu system with all controls
- Data export (CSV/JSON)
- Preset experimental tasks

See [GUI_README.md](GUI_README.md) for complete GUI documentation.

### Programmatic Usage

```python
from apgi_system.system import APGISystem

# Initialize the system
system = APGISystem(config_path="config/default.yaml")

# Run a simulation
results = system.run(duration_ms=10000.0)

# Access results
print(f"Ignition events: {results['ignition_count']}")
print(f"Final state: {results['final_state']}")
```

### Command Line Examples

```bash
# Run basic simulation example
python examples/basic_simulation.py

# Run experimental tasks
python apgi_system/experiments/test_iowa_gambling.py
python apgi_system/experiments/test_masking.py

# Run tests
pytest tests/test_core.py -v
```

## Key Features

- **Multi-scale neural dynamics** (micro, meso, macro)
- **Hierarchical predictive coding** (3-4 layers)
- **Precision-weighted prediction errors**
- **Somatic marker learning** and retrieval
- **Dynamic ignition thresholds**
- **Thermodynamic constraint tracking**
- **Neural oscillations** (gamma, beta, alpha, theta, delta)

## Success Criteria

### Minimal

- Ignition dynamics match 300-500ms timeline
- Metabolic costs align with 5-10% overhead
- Reproduces attentional blink and masking phenomena

### Target

- Human-comparable performance on benchmark tasks
- Neural signatures match empirical data
- Pathology models reproduce clinical phenotypes
