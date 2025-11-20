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

```python
from apgi_system.core import APGISystem

# Initialize the system
system = APGISystem(config_path="config/default.yaml")

# Run a simulation
results = system.run(duration=10.0, task="attentional_blink")

# Visualize results
system.visualize(results)
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
