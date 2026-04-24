# APGI Framework Examples

This directory contains example code demonstrating how to use various components of the APGI Framework.

## Available Examples

### Analysis Examples

- **example_bayesian_parameter_estimation.py**: Demonstrates Bayesian parameter estimation methods for APGI models

### GUI Examples

- **example_gui_usage.py**: Shows how to integrate and use the APGI GUI components

### Neural Interface Examples

- **example_signal_processing.py**: Examples of neural signal processing and analysis
- **example_usage.py**: Comprehensive examples of neural interface usage

## Running Examples

Each example can be run independently:

```bash
cd examples/framework_examples
python example_bayesian_parameter_estimation.py  # Working
python simple_gui_demo.py                    # Working (Simple GUI demo)
python example_usage.py                      # Working (Neural processing)
python example_gui_usage.py                   # Complex GUI (missing dependencies)
python example_signal_processing.py           # Missing dependencies
```

## Prerequisites

Make sure you have APGI Framework properly installed with all dependencies:

```bash
# From project root
pip install -e . --break-system-packages

# For full functionality, also install:
pip install scikit-learn tensorflow torch
```

## Example Structure

Each example follows this pattern:

1. Import necessary modules
2. Setup configuration
3. Initialize components
4. Run demonstration
5. Display results

## Contributing

When adding new examples:

1. Place them in the appropriate subdirectory
2. Follow the existing naming convention (`example_*.py`)
3. Include comprehensive documentation
4. Add error handling
5. Test with different configurations

## Note

These examples are for educational and demonstration purposes. For production use, refer to the main framework documentation and configuration guides.
