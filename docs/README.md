# APGI Framework

## Overview

The APGI Framework is a comprehensive research platform for consciousness studies, neural signal processing, and adaptive intelligence systems. It provides tools for:

- **Neural Signal Processing**: EEG, ECG, pupillometry data analysis
- **Consciousness Research**: Threshold detection paradigms, phase transitions
- **Adaptive Testing**: Bayesian parameter estimation, falsification testing
- **Machine Learning**: Classification tools, biomarker discovery
- **Data Visualization**: Interactive dashboards, real-time monitoring

## Features

### Core Capabilities

- Multi-modal physiological data processing
- Real-time signal analysis and monitoring
- Adaptive experimental paradigms
- Comprehensive test coverage and validation
- Modern GUI interfaces for experiment control

### Research Applications

- Consciousness threshold detection
- Cross-species validation studies
- Clinical biomarker identification
- Neural dynamics analysis
- Active inference modeling

### CLI Usage

```bash
# Run tests
python -m apgi_framework.cli test --all

# Run with coverage
pytest --cov=apgi_framework

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m gui
```

### GUI Usage

```bash
python GUI-Launcher.py          # Recommended entry point
python GUI.py                   # Direct main GUI
python GUI-Experiment-Registry.py
```

### Development Installation

```bash
git clone https://github.com/apgi-research/apgi-framework.git
cd apgi-framework
pip install -e ".[dev]"
```

### Optional Dependencies

```bash
# GUI components
pip install -e ".[gui]"

# Machine learning tools
pip install -e ".[ml]"

# Neural signal processing
pip install -e ".[neural]"

# All optional dependencies
pip install -e ".[all]"
```

## Quick Start

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=apgi_framework --cov-report=html
```

### Using the Framework

```python
from apgi_framework import APGIAgent
from apgi_framework.data import DataProcessor

# Initialize the framework
agent = APGIAgent(config_file="config.yaml")

# Process neural data
processor = DataProcessor()
results = processor.analyze_eeg(data_file="eeg_data.csv")
```

### GUI Applications

```bash
# Launch the main GUI
python GUI-Launcher.py

# Interactive dashboard
python -m apgi_framework.gui.interactive_dashboard
```

## Project Structure

```text
apgi-experiments/
├── apgi_framework/          # Core framework code
│   ├── adaptive/            # Adaptive testing modules
│   ├── analysis/            # Analysis tools
│   ├── clinical/            # Clinical applications
│   ├── config/              # Configuration management
│   ├── gui/                 # GUI components
│   ├── neural/              # Neural signal processing
│   └── testing/            # Test framework
├── tests/                   # Test suite
├── examples/                # Usage examples
├── docs/                    # Documentation
├── research/                # Research modules
└── utils/                   # Utility scripts
```

## Documentation

- [API Documentation](docs/api/)
- [Examples](docs/examples/)
- [Developer Guide](docs/developer/)
- [Research Applications](docs/research/)

## Testing

The framework includes comprehensive testing:

- **Unit Tests**: Fast isolated tests for individual components
- **Integration Tests**: Tests for component interactions
- **Performance Tests**: Benchmarks and profiling
- **GUI Tests**: User interface validation
- **Research Tests**: Domain-specific validation

Run tests with:

```bash
# All tests
pytest

# With coverage
pytest --cov=apgi_framework --cov-report=html

# Specific categories
pytest -m unit
pytest -m integration
pytest -m performance
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

If you use this framework in your research, please cite:

```bibtex
APGI Framework: Adaptive Precision and Generalized Intelligence for Consciousness Research
APGI Research Team (2026)
https://github.com/apgi-research/apgi-framework
```

### 🖥️ GUI Applications

#### Main GUI Applications

- GUI.py - Main comprehensive GUI application (244KB)
- GUI-Launcher.py - Centralized GUI launcher for all applications

#### Apps Directory GUIs

- apps/apgi_falsification_gui.py - Falsification testing GUI (74KB)
- apps/apgi_falsification_gui_refactored.py - Refactored falsification GUI
- apps/gui_template.py - GUI template (241KB)

#### Framework GUI Components

- apgi_framework/gui/coverage_visualization.py - Test coverage visualization
- apgi_framework/gui/enhanced_monitoring_dashboard.py - Enhanced monitoring dashboard
- apgi_framework/gui/interactive_dashboard.py - Interactive dashboard
- apgi_framework/gui/monitoring_dashboard.py - Basic monitoring dashboard
- apgi_framework/gui/parameter_estimation_gui.py - Parameter estimation GUI
- apgi_framework/gui/progress_monitoring.py - Progress monitoring GUI
- apgi_framework/gui/reporting_visualization.py - Reporting visualization
- apgi_framework/gui/results_viewer.py - Results viewer GUI
- apgi_framework/gui/session_management.py - Session management GUI
- apgi_framework/gui/task_configuration.py - Task configuration GUI

### ⌨️ CLI Interfaces

#### Primary CLI Entry Points

- apgi_framework/cli.py - Main command-line interface
- apgi_framework/main.py - Module entry point (python -m apgi_framework)
- apgi_framework/deployment/cli.py - Deployment CLI
- apgi_framework/validation/diagnostics_cli.py - Diagnostics CLI

#### CLI Tools

- tools/run_tests.py - Test runner CLI

### 🔧 Standalone Tools & Scripts

#### Setup & Deployment

- setup.py - Installation and setup script
- setup.sh - Unix/Linux setup script
- deploy.bat - Windows deployment script
- deploy.sh - Unix/Linux deployment script
- quick_deploy.py - Quick deployment tool
- delete_pycache.py - Cache cleanup utility

#### Analysis & Processing

- examples/data_loader.py - Data loading utility
- examples/coverage_collector_demo.py - Coverage collection demo

### 🧪 Testing Suites

#### Main Test Runner

- run_tests.py - Comprehensive test runner with GUI integration

#### Test Categories

- Unit Tests - Fast, isolated component tests
- Integration Tests - Cross-component integration tests
- Framework Tests - Core framework functionality tests
- Falsification Tests - Falsification testing validation
- GUI Tests - GUI component testing
- Performance Tests - Benchmark and performance tests
- Research Tests - Domain-specific experiment tests

#### Test Configuration

- pytest.ini - Pytest configuration (61 lines)
- pyproject.toml - Modern testing configuration (225 lines)

#### Key Test Files

- tests/test_gui_components.py - GUI component tests
- tests/test_cli_module.py - CLI module tests
- tests/test_falsification_coverage.py - Falsification coverage tests
- tests/framework/ - Framework-specific tests (9 files)
- tests/falsification/ - Falsification tests (7 files)
- tests/integration/ - Integration tests (4 files)

### 🚀 Module Entry Points

#### Framework Module

- python -m apgi_framework - Main framework module execution

#### Package Entry Points

- `apgi_framework/__init__.py` - Package initialization

## Quick Start (5 minutes)

**New to the system?** See the [Quick Start Guide](docs/QUICK_START_GUIDE.md) for a 5-minute introduction.

**Using GUI?** Check out the [GUI Visual Guide](docs/GUI_VISUAL_GUIDE.md) for a visual walkthrough.

**Using Web Interface?** Visit [APGI-Experiments.html](../../apgi-web/APGI-Experiments.html) for interactive web-based experiments and visualizations.

**Need help?** See the [Documentation Index](docs/DOCUMENTATION_INDEX.md) for complete documentation.

### Installation Guide

1. **Set up the environment**

   ```bash
   # Create and activate virtual environment
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix/macOS
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Validate installation**

   ```bash
   python -m apgi_framework.cli validate-system
   ```

3. **Run the APGI Agent example**

   ```bash
   python -m core.models.apgi_agent
   ```

4. **Run the Somatic Agent example**

   ```bash
   python -m core.models.phase_transition
   ```

5. **Run experiments via GUI**

   ```bash
   python GUI-Launcher.py
   ```

## Currently Implemented

### Core Models

1. **APGI Agent** (`core/models/apgi_agent.py`)
   - Implements the core APGI framework with interoceptive and exteroceptive processing
   - Dynamic threshold mechanism for conscious access
   - Precision-weighted prediction errors
   - Somatic marker integration

2. **Phase Transition Model** (`core/models/phase_transition.py`)
   - Somatic marker-based decision making
   - Conscious vs unconscious processing modes
   - Expected free energy calculations

3. **Base Experiment Framework** (`core/experiment.py`)
   - Abstract base class for all experiments
   - Standardized data collection and analysis

### Implemented Experiments

1. **Interoceptive Gating Paradigm** (`experiments/interoceptive_gating/`)
   - Tests how interoceptive precision gates conscious access
   - Cardiac discrimination task simulation
   - Three conditions: interoceptive focus, exteroceptive focus, control
   - Threshold tracking and detection rate analysis

2. **AI Benchmarking** (`experiments/ai_benchmarking/`)
   - Compares different agent architectures in survival environments
   - Includes Random, Reactive, DQN, and APGI agents
   - Grid world environment with food, obstacles, and predators
   - Performance metrics: survival time, energy efficiency, food consumption

3. **GUI Interface** (`GUI-Launcher.py`)
   - Tkinter-based interface for running experiments
   - Parameter configuration and real-time logging
   - Supports all implemented experiments

4. **Web Interface** (`../../apgi-web/APGI-Experiments.html`)
   - Interactive web-based experiments and visualizations
   - Modern responsive design with real-time particle animations
   - Neural network visualizations and interactive parameter controls
   - Cross-platform accessibility through web browser

## Key Features

- **Modular Architecture**: Clean separation between models, experiments, and utilities
- **Standardized Experiments**: All experiments inherit from `BaseExperiment` for consistency
- **Multiple Interfaces**: Command-line, GUI, web interface, and programmatic access
- **Data Management**: Automatic data saving and visualization
- **Extensible Design**: Easy to add new models and experiments
- **Web-Based Visualization**: Interactive experiments with real-time neural animations

## Example Usage

### Running Falsification Tests

**Using the GUI:**

```bash
python GUI-Launcher.py
```

**Using the CLI:**

```bash

# Run primary falsification test

python -m apgi_framework.cli run-test primary --trials 1000

# Run all tests

python -m apgi_framework.cli run-batch --all-tests
```

**Using Python API:**

```python
from apgi_framework.main_controller import MainApplicationController

# Initialize system

controller = MainApplicationController()
controller.initialize_system()

# Run test

tests = controller.get_falsification_tests()
result = tests['primary'].run_test(n_trials=1000)
print(f"Falsified: {result.is_falsified}")
print(f"Confidence: {result.confidence_level:.2f}")

# Cleanup

controller.shutdown_system()
```

## Running the APGI Agent

```python
from core.models.apgi_agent import APGIAgent

# Create and run agent with default parameters

agent = APGIAgent()
agent.run_example()  # Runs simulation and shows plots
```

### Running an Experiment

```python
from research.interoceptive_gating.experiments.experiment import run_interoceptive_gating_experiment

# Run experiment with custom parameters

experiment = run_interoceptive_gating_experiment(
    n_participants=20,
    n_trials_per_condition=100
)
```

## Complete Documentation

Complete documentation is available in the `docs/` directory and web interface:

- **[APGI-Experiments.html](../../apgi-web/APGI-Experiments.html)** - Interactive web-based experiments and visualizations
- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Get started in 5 minutes
- **[GUI Visual Guide](docs/GUI_VISUAL_GUIDE.md)** - Visual walkthrough of GUI
- **[User Guide](docs/USER_GUIDE.md)** - Complete user manual
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Command-line interface documentation
- **[Results Interpretation Guide](docs/RESULTS_INTERPRETATION_GUIDE.md)** - Understanding test results
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete documentation index

See [docs/README.md](docs/README.md) for a complete documentation overview.
