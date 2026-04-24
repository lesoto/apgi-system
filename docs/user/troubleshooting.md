# APGI Framework Troubleshooting Guide

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [System Initialization Errors](#system-initialization-errors)
3. [Test Execution Problems](#test-execution-problems)
4. [Results and Data Issues](#results-and-data-issues)
5. [Performance Problems](#performance-problems)
6. [GUI Issues](#gui-issues)
7. [CLI Issues](#cli-issues)
8. [Configuration Problems](#configuration-problems)
9. [Statistical Issues](#statistical-issues)
10. [Getting Additional Help](#getting-additional-help)

## Installation Issues

### Problem: pip install fails with dependency errors

**Symptoms**:

```text
ERROR: Could not find a version that satisfies the requirement...
```

**Causes**:

- Incompatible Python version
- Missing system dependencies
- Network issues

**Solutions**:

1. **Check Python version**:

   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Upgrade pip**:

   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install dependencies individually**:

   1. **Check dependencies**:

   ```bash
   pip install numpy scipy matplotlib pandas
   pip install -r requirements.txt
   ```

4. **Use virtual environment**:

   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix/macOS:
   # source venv/bin/activate
   pip install -r requirements.txt
   ```

```bash
python --version
```

### Problem: Import errors after installation

**Symptoms**:

```text
ModuleNotFoundError: No module named 'apgi_framework'
```

**Causes**:

- Package not in Python path
- Wrong Python interpreter
- Installation in different environment

**Solutions**:

1. **Add to Python path**:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

1. **Check Python interpreter**:

```bash
which python  # On Windows: where python
python -c "import sys; print(sys.executable)"
```

1. **Reinstall in correct environment**:

```python
pip uninstall apgi-framework
pip install -e .  # Install in development mode
```

### Problem: Missing system dependencies

**Symptoms**:

```text
ImportError: libGL.so.1: cannot open shared object file
```

**Causes**:

- Missing system libraries (especially for GUI)

**Solutions**:

**Ubuntu/Debian**:

```bash
sudo apt-get update
sudo apt-get install python3-pyqt5 libgl1-mesa-glx
```

**macOS**:

```bash
brew install python-tk
```

**Windows**:

- Usually no additional dependencies needed
- If issues persist, install Visual C++ Redistributable

## System Initialization Errors

### Problem: "System not initialized" error

**Symptoms**:

```python
APGIFrameworkError: System not initialized. Call initialize_system() first.
```

**Cause**:

- Forgot to call `initialize_system()`

**Solution**:

```python
from apgi_framework.main_controller import MainApplicationController
controller = MainApplicationController()
controller.initialize_system()  # Don't forget this!
# Now you can use the system
tests = controller.get_falsification_tests()
```

### Problem: Component initialization fails

**Symptoms**:

```python
APGIFrameworkError: Failed to initialize system: ...
```

**Causes**:

- Invalid configuration
- Missing dependencies
- Corrupted files

**Solutions**:

1. **Run system validation**:

```bash
python -m apgi_framework.cli validate-system --detailed
```

1. **Check configuration**:

```python
from apgi_framework.config import ConfigManager
config_manager = ConfigManager()
apgi_params = config_manager.get_apgi_parameters()
print(apgi_params)  # Verify parameters are valid
```

1. **Reset to defaults**:

```bash
python -m apgi_framework.cli generate-config --output config.json
python -m apgi_framework.cli --config config.json validate-system
```

1. **Enable debug logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
controller = MainApplicationController()
controller.initialize_system()
```

### Problem: Validation fails

**Symptoms**:

```python
System Validation: FAIL
Mathematical Engine: FAIL
```

**Causes**:

- Component integration issues
- Invalid parameters
- Missing files

**Solutions**:

1. **Check detailed validation**:

```bash
python -m apgi_framework.cli validate-system --detailed
```

1. **Verify file structure**:

```bash
ls -R apgi_framework/  # Check all modules present
```

1. **Test individual components**:

```python
from apgi_framework.core import APGIEquation
equation = APGIEquation()
result = equation.calculate_surprise(1.0, 0.8, 2.0, 1.5, 1.3)
print(f"Surprise: {result}")  # Should print a number
```

## Test Execution Problems

### Problem: Test hangs or takes too long

**Symptoms**:

- Test runs for hours without completing
- No progress updates
- High CPU usage

**Causes**:

- Too many trials
- Infinite loop (bug)
- Resource constraints

**Solutions**:

1. **Reduce trial count for testing**:

```bash
python -m apgi_framework.cli run-test primary --trials 100
```

1. **Monitor progress**:

```python
import logging
logging.basicConfig(level=logging.INFO)
# Progress will be logged
result = test.run_test(n_trials=1000)
```

1. **Check system resources**:

```bash
# Linux/Mac
top
htop
# Windows
Task Manager (Ctrl+Shift+Esc)
```

1. **Kill and restart**:

```bash
# Press Ctrl+C to interrupt
# Then restart with fewer trials
```

### Problem: Test fails with numerical errors

**Symptoms**:

```python
RuntimeWarning: overflow encountered in exp
RuntimeWarning: invalid value encountered in divide
```

**Causes**:

- Extreme parameter values
- Numerical instability
- Division by zero

**Solutions**:

1. **Check parameter ranges**:

```python
# Ensure parameters are in valid ranges
config_manager.update_apgi_parameters(
    extero_precision=2.0,  # 0.1-10.0
    intero_precision=1.5,  # 0.1-10.0
    threshold=3.5,         # 0.5-10.0
    steepness=2.0,         # 0.1-5.0
    somatic_gain=1.3       # 0.1-5.0
)
```

1. **Enable numerical stability**:

```python
from apgi_framework.core import APGIEquation
equation = APGIEquation(numerical_stability=True)
```

1. **Avoid extreme values**:

```python
# Don't use extreme values
# Bad: threshold=0.01, steepness=10.0
# Good: threshold=3.5, steepness=2.0
```

### Problem: "No module named 'scipy'" during test

**Symptoms**:

```python
ModuleNotFoundError: No module named 'scipy'
```

**Cause**:

- Missing scipy dependency

**Solution**:

```bash
pip install scipy
```

### Problem: Test results are all the same

**Symptoms**:

- Every test returns identical results
- No variation across trials

**Causes**:

- Random seed set and not changing
- Bug in simulation

**Solutions**:

1. **Remove random seed**:

```python
config_manager.update_experimental_config(random_seed=None)
```

1. **Verify simulation is running**:

```python
# Enable debug logging to see trial-by-trial output
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Results and Data Issues

### Problem: Results not saving

**Symptoms**:

- No files in output directory
- "Permission denied" errors

**Causes**:

- Invalid output path
- Permission issues
- Disk full

**Solutions**:

1. **Check output directory**:

```bash
ls -la results/
# Should show files after test completion
```

1. **Verify permissions**:

```bash
# Linux/Mac
chmod 755 results/
# Windows
# Right-click folder → Properties → Security
```

1. **Use absolute path**:

```python
config_manager.update_experimental_config(
    output_directory="/absolute/path/to/results"
)
```

1. **Check disk space**:

```bash
df -h  # Linux/Mac
# Windows: Check in File Explorer
```

### Problem: Cannot load saved results

**Symptoms**:

```python
JSONDecodeError: Expecting value: line 1 column 1
```

**Causes**:

- Corrupted JSON file
- Incomplete save
- Wrong file format

**Solutions**:

1. **Verify file is valid JSON**:

```bash
python -m json.tool results/primary_result_*.json
```

1. **Check file size**:

```bash
ls -lh results/
# Files should be > 0 bytes
```

1. **Try loading with error handling**:

```python
import json
try:
    with open('results/primary_result_001.json', 'r') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Error at line {e.lineno}: {e.msg}")
```

### Problem: Missing data in results

**Symptoms**:

- Result file missing expected fields
- `KeyError` when accessing results

**Causes**:

- Incomplete test execution
- No results loaded
- Partial save

**Solutions**:

1. **Check for errors during test**:

```bash
cat results/apgi_framework.log | grep ERROR
```

1. **Verify test completed**:

```python
# Check for completion marker
if 'detailed_results' in result_data:
    print("Test completed successfully")
else:
    print("Test may have been interrupted")
```

1. **Re-run test**:

```bash
python -m apgi_framework.cli run-test primary --trials 1000
```

## Performance Problems

### Problem: Tests run very slowly

**Symptoms**:

- Tests take much longer than expected
- System becomes unresponsive

**Causes**:

- Too many trials
- Insufficient resources
- Debug logging enabled
- Other processes consuming resources

**Solutions**:

1. **Reduce trial count**:

```bash
# Start with fewer trials
python -m apgi_framework.cli run-test primary --trials 500
```

1. **Disable debug logging**:

```bash
python -m apgi_framework.cli --log-level WARNING run-test primary
```

1. **Close other applications**:

- Close unnecessary programs
- Check background processes

1. **Use batch processing efficiently**:

```bash
# Process sequentially, not in parallel
python -m apgi_framework.cli run-batch --all-tests
# Don't use --parallel unless necessary
```

### Problem: High memory usage

**Symptoms**:

- System runs out of memory
- "MemoryError" exceptions

**Causes**:

- Too many trials stored in memory
- Large datasets
- Memory leak

**Solutions**:

1. **Process in batches**:

```python
# Instead of all at once
for batch in range(10):
    result = test.run_test(n_trials=100)
    save_result(result)
```

1. **Enable intermediate saves**:

```python
config_manager.update_experimental_config(
    save_intermediate=True
)
```

1. **Monitor memory usage**:

```bash
# Linux/Mac
free -h
watch -n 1 free -h
# Windows
Task Manager → Performance → Memory
```

## GUI Issues

### Problem: GUI won't launch

**Symptoms**:

```text
ImportError: No module named 'PyQt5'
```

**Cause**:

- Missing GUI dependencies

**Solution**:

```bash
pip install PyQt5
```

### Problem: GUI freezes during test

**Symptoms**:

- GUI becomes unresponsive
- "Not Responding" message

**Cause**:

- Long-running test blocking GUI thread

**Solution**:

- This is expected behavior for long tests
- Wait for test to complete
- Progress should update when test finishes
- Consider using CLI for long tests

### Problem: Plots not displaying

**Symptoms**:

- Empty visualization panel
- "No data to display" message

**Causes**:

- Test not completed
- No results loaded
- Visualization error

**Solutions**:

1. **Ensure test completed**:

- Check progress panel shows 100%
- Look for completion message

1. **Try reloading results**:

- File → Load Results
- Select result file

1. **Check for errors**:

```bash
python GUI-Launcher.py --verbose
```

## CLI Issues

### Problem: Command not found

**Symptoms**:

```bash
python: No module named apgi_framework.cli
```

**Causes**:

- Wrong directory
- Package not installed
- Python path issue

**Solutions**:

1. **Check working directory**:

```bash
pwd  # Should be in project root
ls apgi_framework/  # Should see cli.py
```

1. **Use full path**:

```bash
python -m apgi_framework.cli --help
```

1. **Install package**:

```bash
pip install -e .
```

### Problem: Invalid command or arguments

**Symptoms**:

```python
error: invalid choice: 'test'
```

**Cause**:

- Typo in command name
- Wrong argument format

**Solution**:

```bash
# Check available commands
python -m apgi_framework.cli --help
# Use correct command name
python -m apgi_framework.cli run-test primary  # Not just 'test'
```

### Problem: Configuration file not found

**Symptoms**:

```python
FileNotFoundError: [Errno 2] No such file or directory: 'config.json'
```

**Causes**:

- File doesn't exist
- Wrong path
- Wrong directory

**Solutions**:

1. **Generate default configuration**:

```bash
python -m apgi_framework.cli generate-config --output config.json
```

1. **Use absolute path**:

```bash
python -m apgi_framework.cli --config /full/path/to/config.json run-test primary
```

1. **Check file exists**:

```bash
ls -l config.json
```

## Configuration Problems

### Problem: Invalid parameter values

**Symptoms**:

```python
ValidationError: Parameter 'threshold' must be between 0.5 and 10.0
```

**Cause**:

- Parameter outside valid range
**Solution**:

```python
# Check valid ranges
# extero_precision: 0.1-10.0
# intero_precision: 0.1-10.0
# threshold: 0.5-10.0
# steepness: 0.1-5.0
# somatic_gain: 0.1-5.0
config_manager.update_apgi_parameters(
    threshold=3.5  # Within valid range
)
```

### Problem: Configuration not loading

**Symptoms**:

- Default values used instead of config file
- Changes not taking effect
**Causes**:
- Config file not specified
- JSON syntax error
- Wrong file format
**Solutions**:

1. **Validate JSON syntax**:

```bash
python -m json.tool config.json
```

1. **Check file is being loaded**:

```python
import json
with open('config.json', 'r') as f:
    config = json.load(f)
    print(config)  # Verify contents
```

1. **Specify config explicitly**:

```bash
python -m apgi_framework.cli --config config.json run-test primary
```

## Statistical Issues

### Problem: Low statistical power warning

**Symptoms**:

```python
Warning: Statistical power (0.62) is below recommended threshold (0.80)
```

**Cause**:

- Insufficient sample size
**Solution**:

```bash
# Increase number of trials
python -m apgi_framework.cli run-test primary --trials 2000
```

### Problem: All p-values are 1.0

**Symptoms**:

- Every test returns p-value = 1.0
- No significant results
**Causes**:
- No variation in data
- Bug in statistical calculation
- Insufficient trials
**Solutions**:

1. **Increase trials**:

```bash
python -m apgi_framework.cli run-test primary --trials 2000
```

1. **Check data variation**:

```python
# Verify data has variation
print(f"Mean: {np.mean(data)}")
print(f"Std: {np.std(data)}")  # Should be > 0
```

1. **Enable debug logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Problem: Inconsistent results across runs

**Symptoms**:

- Different results each time
- Cannot reproduce findings

**Cause**:

- Random seed not set

**Solution**:

```python
# Set random seed for reproducibility
config_manager.update_experimental_config(random_seed=42)
```

## Getting Additional Help

### Diagnostic Commands

```bash
# System status
python -m apgi_framework.cli status
# Detailed validation
python -m apgi_framework.cli validate-system --detailed
# Check logs
cat results/apgi_framework.log
# Recent errors
tail -n 50 results/apgi_framework.log | grep ERROR
```

### Enable Verbose Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### Collect System Information

```python
import sys
import platform
import numpy as np
import scipy
print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"NumPy: {np.__version__}")
print(f"SciPy: {scipy.__version__}")
```

### Create Minimal Reproducible Example

When reporting issues, create a minimal example:

```python
from apgi_framework.main_controller import MainApplicationController
# Minimal example that reproduces the issue
controller = MainApplicationController()
controller.initialize_system()
tests = controller.get_falsification_tests()
result = tests['primary'].run_test(n_trials=100)
print(f"Result: {result}")
```

### Where to Get Help

1. **Check Documentation**:
   - USER_GUIDE.md
   - CLI_REFERENCE.md
   - RESULTS_INTERPRETATION_GUIDE.md
2. **Review Examples**:
   - examples/ directory
   - Working code samples
3. **Check Logs**:
   - results/apgi_framework.log
   - Enable DEBUG logging
4. **Run Diagnostics**:
   - System validation
   - Component tests
5. **Search Issues**:
   - Check if problem already reported
   - Look for similar issues

### Reporting Bugs

When reporting bugs, include:

1. **System Information**:
   - Python version
   - Operating system
   - Package versions
2. **Steps to Reproduce**:
   - Exact commands run
   - Configuration used
   - Expected vs actual behavior
3. **Error Messages**:
   - Full error traceback
   - Relevant log entries
4. **Minimal Example**:
   - Simplest code that reproduces issue
   - Sample data if needed

---
**Version**: 1.0  
**Last Updated**: 2025-01-07  
**See Also**: USER_GUIDE.md, CLI_REFERENCE.md
