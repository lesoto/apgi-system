# APGI System: Allostatic Precision-Gated Ignition Framework

A computational implementation of consciousness based on active inference, predictive processing, and allostatic regulation.

## Overview

The APGI framework integrates:
- **Active Inference**: Variational free energy minimization and Bayesian inference
- **Predictive Processing**: Hierarchical prediction error minimization
- **Allostatic Regulation**: Interoceptive predictive processing and homeostatic control
- **Ignition Dynamics**: Threshold-based global workspace broadcasting
- **Self-Modeling**: Minimal and narrative self-representations

## Architecture

```
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
