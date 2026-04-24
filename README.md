# APGI Framework - Test Enhancement

Comprehensive Test Enhancement for APGI Framework - Advanced Platform for General Intelligence Research.

## Overview

The APGI Framework provides tools for consciousness research, experimental paradigms, and falsification testing of consciousness theories. This repository contains enhanced testing infrastructure and comprehensive test coverage improvements.

## Features

- Advanced consciousness modeling and simulation
- Falsification testing protocols
- Real-time monitoring and visualization
- Cross-species validation paradigms
- Comprehensive test suite with high coverage

## Installation

### Basic Installation

```bash
pip install -e .
```

### Development Installation

```bash
pip install -e .[dev]
```

### All Dependencies

```bash
pip install -e .[all]
```

## Usage

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apgi_framework

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
pytest -m "gui"
```

### GUI Applications

```bash
# Launch main GUI
python GUI-Launcher.py
```

## Project Structure

- `apgi_framework/` - Core framework modules
- `tests/` - Comprehensive test suite
- `examples/` - Usage examples
- `docs/` - Documentation
- `utils/` - Utility scripts and tools

## Entry Points Ordered by Importance

### 1. Main CLI (`apgi_framework/cli.py`)

**Type**: Command-line interface
**Purpose**: Primary command-line interface for running tests, experiments, and configuration

### 2. Main GUI Application (`GUI.py`)

**Type**: Desktop GUI
**Purpose**: Main graphical user interface for the framework

### 3. GUI Launcher (`GUI-Launcher.py`)

**Type**: Desktop GUI
**Purpose**: Launcher application for GUI components

### 4. Run Tests Script (`run_tests.py`)

**Type**: Script
**Purpose**: Test execution and reporting

### 5. Tests GUI (`Tests-GUI.py`)

**Type**: Desktop GUI
**Purpose**: GUI for running and monitoring tests

### 6. Utils GUI (`Utils-GUI.py`)

**Type**: Desktop GUI
**Purpose**: Utility interface for framework tools

### 7. Quick Deploy Script (`quick_deploy.py`)

**Type**: Deployment script
**Purpose**: One-click deployment for non-technical users

### 8. Setup Script (`setup.sh`)

**Type**: Installation script
**Purpose**: Environment setup and dependency installation

### 9. Deploy Script (`deploy.sh`)

**Type**: Deployment script
**Purpose**: Production deployment and configuration

### 10. Falsification GUI (`apps/apgi_falsification_gui.py`)

**Type**: Desktop GUI
**Purpose**: Interface for falsification testing

### 12. Real-time Monitoring Dashboard (`apgi_framework/gui/monitoring_dashboard.py`)

**Type**: Desktop GUI
**Purpose**: Live monitoring of EEG, pupillometry, cardiac signals

## Utils Scripts

### 1. CI/CD Pipeline (`utils/cicd_pipeline.py`)

**Type**: Automation script
**Purpose**: Comprehensive CI/CD pipeline for testing, building, and deployment

### 2. Dependency Checker (`utils/check_dependencies.py`)

**Type**: Validation script
**Purpose**: Check and validate all required dependencies

### 3. Performance Profiler (`utils/performance_profiler.py`)

**Type**: Analysis tool
**Purpose**: Profile and analyze application performance

### 4. Data Validation (`utils/data_validation.py`)

**Type**: Data quality tool
**Purpose**: Validate and assess data quality and integrity

### 5. Backup Manager (`utils/backup_manager.py`)

**Type**: Utility script
**Purpose**: Automated backup and recovery system

### 6. Batch Processor (`utils/batch_processor.py`)

**Type**: Processing tool
**Purpose**: Batch processing of experiments and data

### 7. Error Handler (`utils/error_handler.py`)

**Type**: Error management
**Purpose**: Centralized error handling and reporting

### 8. Cache Manager (`utils/cache_manager.py`)

**Type**: Performance utility
**Purpose**: Manage application cache and temporary data

### 9. Report Generator (`utils/report_generator.py`)

**Type**: Documentation tool
**Purpose**: Generate comprehensive reports from test results

### 10. Sample Data Generator (`utils/sample_data_generator.py`)

**Type**: Data utility
**Purpose**: Generate sample data for testing and development

### 11. GUI Testing Framework (`utils/gui_testing_framework.py`)

**Type**: Testing tool
**Purpose**: Framework for testing GUI components and interactions

### 12. Parameter Validator (`utils/parameter_validator.py`)

**Type**: Validation tool
**Purpose**: Validate framework parameters and configurations

### 13. Release Manager (`utils/release.py`)

**Type**: Deployment tool
**Purpose**: Automated release management and versioning

### 14. Performance Dashboard (`utils/performance_dashboard.py`)

**Type**: Monitoring tool
**Purpose**: Real-time performance monitoring dashboard

### 15. Data Quality Assessment (`utils/data_quality_assessment.py`)

**Type**: Analysis tool
**Purpose**: Comprehensive data quality assessment and reporting
