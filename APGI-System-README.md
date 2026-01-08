# APGI System: Allostatic Precision-Gated Ignition Framework

A computational implementation of consciousness based on active inference, predictive processing, and allostatic regulation.

## Overview

The APGI framework integrates:

- **Active Inference**: Variational free energy minimization and Bayesian inference
- **Predictive Processing**: Hierarchical prediction error minimization
- **Allostatic Regulation**: Interoceptive predictive processing and homeostatic control
- **Ignition Dynamics**: Threshold-based global workspace broadcasting
- **Self-Modeling**: Minimal and narrative self-representations

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

See [docs/gui/GUI_README.md](docs/gui/GUI_README.md) for complete GUI documentation.

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

## APGI System: Comprehensive Analysis

### System Overview

The **APGI (Allostatic Precision-Gated Ignition) System** is a sophisticated computational framework for modeling consciousness based on active inference, predictive processing, and allostatic regulation. It implements a biologically-inspired model of cognitive function with multiple interacting subsystems.

### Core Architecture

The system is organized into several key modules:

### **Core Systems** (`apgi_system/core/`)

- **Active Inference Engine**: Variational free energy minimization and Bayesian inference
- **Hierarchical Predictor**: Multi-level predictive processing (4 levels: sensory → feature → category → abstract)
- **Precision Weighting**: Dynamic precision modulation of prediction errors
- **Free Energy Calculator**: Tracks system-wide variational free energy

### **Neural Systems** (`apgi_system/neural/`)

- **Microscale**: Spiking neural networks
- **Mesoscale**: Neural column dynamics
- **Macroscale**: Large-scale brain networks
- **Oscillations**: Multi-band neural oscillations (delta, theta, alpha, beta, gamma)

### **Interoception** (`apgi_system/interoception/`)

- **Body Model**: Simulates physiological states (heart rate, respiration, temperature, glucose, cortisol)
- **Allostatic Regulator**: Maintains homeostatic balance
- **Somatic Marker System**: Emotion-like signals for decision-making

### **Ignition Dynamics** (`apgi_system/ignition/`)

- **Ignition Threshold**: Dynamic threshold for global broadcasting
- **Global Workspace**: Information sharing across subsystems
- **Temporal Dynamics**: Timing of ignition events (300-500ms timeline)

### **Self-Model** (`apgi_system/self_model/`)

- **Minimal Self**: Basic self-representation and coherence tracking
- **Narrative Self**: Episodic memory and autobiographical processing
- **Coherence Maintenance**: Self-model integrity monitoring

### **Thermodynamic** (`apgi_system/thermodynamic/`)

- **Metabolic Budget**: Energy constraints and consumption tracking
- **Entropy Tracker**: Information entropy and thermodynamic costs

## Entry Points

### **1. GUI Application** (Primary Interface)

**File**: [apgi_gui.py](cci:7://file:///Users/lesoto/Sites/PYTHON/apgi-system/apgi_gui.py:0:0-0:0) (83,840 bytes)
**Launch**:

```bash
python apgi_gui.py
# or
python utils/run_gui.py
```

**Features**:

- **Real-time visualization** with 6 tabs:
  1. Neural Activity (ignition events, workspace, precision, free energy)
  2. Interoception (heart rate, cortisol, allostatic load, metabolic reserves)
  3. System Metrics (somatic markers, gamma/beta power)
  4. Self-Model (coherence tracking with thresholds)
  5. Oscillations (signal and power spectrum)
  6. State Space (3D trajectory visualization)
- **Complete menu system** (File, Edit, Simulation, View, Tools, Analysis, Help)
- **Interactive controls** (Start/Pause/Stop/Reset, speed control, parameter sliders)
- **Data export** (CSV/JSON formats)
- **Experimental task execution** with progress tracking
- **Keyboard shortcuts** (Ctrl+N/O/S/E/Q, F5-F8)

### **2. REST API** (Web Interface)

**File**: [api/main.py](cci:7://file:///Users/lesoto/Sites/PYTHON/apgi-system/api/main.py:0:0-0:0)
**Framework**: FastAPI with comprehensive middleware
**Features**:

- RESTful endpoints for system control
- Authentication and rate limiting
- Database integration with Alembic migrations
- Prometheus metrics and structured logging
- Redis for session management
- CORS support for web clients

### **3. Programmatic Interface**

**File**: [apgi_system/system.py](cci:7://file:///Users/lesoto/Sites/PYTHON/apgi-system/apgi_system/system.py:0:0-0:0)
**Usage**:

```python
from apgi_system.system import APGISystem

system = APGISystem(config_path="config/default.yaml")
results = system.run(duration_ms=10000.0)
```

### **4. Experimental Tasks**

**Location**: `apgi_system/experiments/tasks/`
**Available Tasks**:

- **Iowa Gambling Task**: Decision-making under uncertainty
- **Attentional Blink Task**: Temporal attention limitations
- **Change Blindness Task**: Visual perception failures
- **Binocular Rivalry Task**: Competitive perception
- **Masking Paradigm Task**: Subliminal processing

## Key Functionality

### **Real-Time Simulation**

- **Timestep**: 1ms microscale resolution
- **Update Rate**: ~1000 Hz system, 10 Hz GUI
- **Multi-threaded architecture** for responsive UI
- **State tracking** with comprehensive history

### **Hierarchical Processing**

- **4-level hierarchy**: 256→128→64→32 nodes
- **Different timescales**: 10ms→50ms→200ms→500ms
- **Predictive coding** with error minimization
- **Precision weighting** with neuromodulator effects

### **Physiological Modeling**

- **Body states**: Heart rate, respiration, temperature, glucose, cortisol
- **Allostatic ranges**: Tight (10%), moderate (20%), wide (30%)
- **Metabolic constraints**: 5-10% ignition overhead, 25-30% task overhead
- **Energy budgeting** with recovery dynamics

### **Consciousness Metrics**

- **Ignition events**: Global workspace broadcasting
- **Phi integration**: IIT consciousness measure
- **PCI complexity**: Perturbational complexity index
- **Coherence tracking**: Self-model integrity
- **Somatic markers**: Decision-making signals

## Configuration

**File**: [config/default.yaml](cci:7://file:///Users/lesoto/Sites/PYTHON/apgi-system/config/default.yaml:0:0-0:0)
**Sections**:

- System parameters (timestep, random seed)
- Hierarchy structure (levels, nodes, timescales)
- Active inference (learning rates, thresholds)
- Precision weighting (baselines, neuromodulators)
- Ignition dynamics (thresholds, timing)
- Interoception (body states, allostatic ranges)
- Neural oscillations (frequency bands, coupling)
- Thermodynamic constraints (energy budgets)
- Validation metrics (phi, PCI, ERPs)

## Dependencies

**Core**: NumPy, SciPy, JAX, PyTorch, Matplotlib, Pandas
**GUI**: Tkinter (built-in), Matplotlib backend
**API**: FastAPI, Redis, Alembic, Prometheus
**Testing**: Pytest, Hypothesis
**Development**: Black, Flake8, MyPy

## Validation & Testing

The system includes comprehensive validation:

- **Unit tests** for individual components
- **Integration tests** for subsystem interactions
- **Property-based tests** using Hypothesis
- **Experimental paradigms** reproducing known phenomena
- **Performance monitoring** with FPS counters and metrics

## Research Applications

This system models:

- **Attentional blink** and perceptual limitations
- **Change blindness** and visual awareness
- **Decision-making** under uncertainty (Iowa Gambling)
- **Binocular rivalry** and competitive perception
- **Somatic marker hypothesis** in decision-making
- **Neural oscillations** and consciousness correlates
- **Metabolic constraints** on cognitive processing

The APGI framework provides a comprehensive platform for studying consciousness through computational modeling, integrating multiple theoretical perspectives into a unified, testable system.

## Next Steps

To explore the system further:

1. **Start the GUI**: Run `python apgi_gui.py` to launch the interactive interface
2. **Review the API**: Check `docs/api/REST-API.md` for web service endpoints
3. **Examine the core**: Look at `apgi_system/system.py` for the main simulation logic
4. **Check experiments**: Explore `apgi_system/experiments/` for task implementations
5. **Review configuration**: Study `config/default.yaml` for system parameters
