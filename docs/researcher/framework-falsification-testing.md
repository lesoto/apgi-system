# APGI Framework Documentation

Welcome to the APGI Framework Testing System documentation.

## 📚 Documentation Overview

This directory contains comprehensive documentation for using, understanding, and troubleshooting the APGI Framework.

## 🚀 Getting Started

**New users should start here:**

1. **[Quick Start Guide](QUICK_START_GUIDE.md)** - Get up and running in 5 minutes
   - Installation instructions
   - Your first test (GUI, CLI, or Python API)
   - Understanding basic results
   - Common workflows

2. **[GUI Visual Guide](GUI_VISUAL_GUIDE.md)** - Visual walkthrough of the GUI
   - Main window layout with ASCII diagrams
   - Step-by-step visual instructions
   - Button states and interactions
   - Workflow examples with visuals

3. **[Examples](../examples/README.md)** - Working code examples
   - Running primary falsification test
   - Batch processing configurations
   - Custom analysis of results
   - Extending the framework

## 📖 Complete Documentation

### User Guides

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [Quick Start Guide](QUICK_START_GUIDE.md) | 5-minute introduction | First time using the system |
| [User Guide](USER_GUIDE.md) | Complete user manual | Comprehensive reference |
| [GUI Visual Guide](GUI_VISUAL_GUIDE.md) | Visual GUI walkthrough | Learning the GUI interface |
| [CLI Reference](CLI_REFERENCE.md) | Command-line documentation | Using CLI or automation |

### Understanding Results

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [Results Interpretation Guide](RESULTS_INTERPRETATION_GUIDE.md) | How to interpret test results | After running tests |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and solutions | When encountering problems |

### Technical Documentation

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [Error Handling Quick Reference](ERROR_HANDLING_QUICK_REFERENCE.md) | Error handling patterns | Development and debugging |
| [Validation Quick Reference](../VALIDATION_QUICK_REFERENCE.md) | Parameter validation | Development and debugging |
| [Parameter Validation Guide](parameter_validation_guide.md) | Detailed validation docs | Development |

### Theoretical Background

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [APGI Falsification](../APGI-Falsification.md) | Falsification theory | Understanding the science |
| [APGI Ignition Equation](../APGI-Ignition-Equation.md) | Mathematical framework | Understanding the math |
| [APGI Testable Predictions](../APGI-Testable-Predictions.md) | Framework predictions | Understanding predictions |

### Implementation Documentation

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [Task 3.1 Implementation Summary](TASK_3.1_IMPLEMENTATION_SUMMARY.md) | Parameter validation implementation | Development reference |
| [Task 3.2 Error Handling Summary](TASK_3.2_ERROR_HANDLING_SUMMARY.md) | Error handling implementation | Development reference |
| [Validation and Error Handling Summary](../VALIDATION_AND_ERROR_HANDLING_SUMMARY.md) | Complete implementation summary | Development reference |

### Index and Navigation

| Document | Description | When to Use |
| ---------- | ------------- | ------------- |
| [Documentation Index](DOCUMENTATION_INDEX.md) | Complete documentation index | Finding specific information |

## 🎯 Documentation by Task

### I want to

#### Run my first test

1. [Quick Start Guide](QUICK_START_GUIDE.md)
2. [GUI Visual Guide](GUI_VISUAL_GUIDE.md) (if using GUI)
3. [Example 01](../examples/01_run_primary_falsification_test.py)

#### Understand my results

1. [Results Interpretation Guide](RESULTS_INTERPRETATION_GUIDE.md)
2. [Quick Start Guide - Understanding Results](QUICK_START_GUIDE.md#understanding-your-results)

#### Use the GUI

1. [Quick Start Guide - GUI Section](QUICK_START_GUIDE.md#option-a-using-the-gui-recommended-for-beginners)
2. [GUI Visual Guide](GUI_VISUAL_GUIDE.md)
3. [User Guide - GUI Section](USER_GUIDE.md#gui-user-guide)

#### Use the CLI

1. [Quick Start Guide - CLI Section](QUICK_START_GUIDE.md#option-b-using-the-cli-recommended-for-automation)
2. [CLI Reference](CLI_REFERENCE.md)

#### Use the Python API

1. [Quick Start Guide - Python API Section](QUICK_START_GUIDE.md#option-c-using-python-api-recommended-for-integration)
2. [Examples](../examples/README.md)

#### Run batch tests

1. [User Guide - Batch Processing](USER_GUIDE.md#batch-processing)
2. [Example 02](../examples/02_batch_processing_configurations.py)

#### Analyze saved results

1. [User Guide - Loading Results](USER_GUIDE.md#loading-previous-results)
2. [Example 03](../examples/03_custom_analysis_saved_results.py)

#### Troubleshoot problems

1. [Troubleshooting Guide](TROUBLESHOOTING.md)
2. [User Guide - Troubleshooting Section](USER_GUIDE.md#troubleshooting)

#### Understand the theory

1. [APGI Falsification](../APGI-Falsification.md)
2. [APGI Ignition Equation](../APGI-Ignition-Equation.md)
3. [APGI Testable Predictions](../APGI-Testable-Predictions.md)

#### Extend the framework

1. [Example 04](../examples/04_extending_falsification_criteria.py)
2. [Error Handling Quick Reference](ERROR_HANDLING_QUICK_REFERENCE.md)

## 📊 Documentation by User Type

### Researchers

**Start here:**

1. [Quick Start Guide](QUICK_START_GUIDE.md)
2. [Results Interpretation Guide](RESULTS_INTERPRETATION_GUIDE.md)
3. [APGI Falsification](../APGI-Falsification.md)

**Then explore:**

- [User Guide](USER_GUIDE.md) - Complete reference
- [Examples](../examples/README.md) - Working code
- [CLI Reference](CLI_REFERENCE.md) - Automation

### Students/Learners

**Start here:**

1. [Quick Start Guide](QUICK_START_GUIDE.md)
2. [GUI Visual Guide](GUI_VISUAL_GUIDE.md)
3. [Examples](../examples/README.md)

**Then explore:**

- [User Guide](USER_GUIDE.md) - Detailed instructions
- [APGI Falsification](../APGI-Falsification.md) - Theory
- [Results Interpretation Guide](RESULTS_INTERPRETATION_GUIDE.md) - Understanding results

### Developers

**Start here:**

1. [Error Handling Quick Reference](ERROR_HANDLING_QUICK_REFERENCE.md)
2. [Validation Quick Reference](../VALIDATION_QUICK_REFERENCE.md)
3. [Example 04](../examples/04_extending_falsification_criteria.py)

**Then explore:**

- Implementation summaries
- Code in `apgi_framework/`
- [Parameter Validation Guide](parameter_validation_guide.md)

### System Administrators

**Start here:**

1. [Quick Start Guide - Installation](QUICK_START_GUIDE.md#installation-2-minutes)
2. [Troubleshooting Guide](TROUBLESHOOTING.md)
3. [CLI Reference](CLI_REFERENCE.md)

**Then explore:**

- [User Guide](USER_GUIDE.md) - Complete reference
- System validation procedures

## 🔍 Quick Reference

### Common Commands

```bash
# Validate system
python -m apgi_framework.cli validate-system

# Run primary test
python -m apgi_framework.cli run-test primary --trials 1000

# Run all tests
python -m apgi_framework.cli run-batch --all-tests

# Generate configuration
python -m apgi_framework.cli generate-config --output config.json

# Launch GUI
python GUI-Launcher.py
```

### Parameter Ranges

| Parameter | Range | Default |
| ----------- | ------- | --------- |
| extero_precision | 0.1-10.0 | 2.0 |
| intero_precision | 0.1-10.0 | 1.5 |
| threshold | 0.5-10.0 | 3.5 |
| steepness | 0.1-5.0 | 2.0 |
| somatic_gain | 0.1-5.0 | 1.3 |

### Statistical Thresholds

| Metric | Threshold | Interpretation |
| -------- | ----------- | ---------------- |
| Confidence | ≥ 0.8 | High confidence |
| P-value | < 0.05 | Significant |
| Effect Size | ≥ 0.5 | Medium effect |
| Power | ≥ 0.8 | Well-powered |

## 📝 Documentation Standards

All documentation follows these standards:

- **Markdown format** for easy reading and version control
- **Table of contents** for long documents
- **Working code examples** that can be run directly
- **Consistent terminology** across all documents
- **Version information** and last updated dates
- **Cross-references** to related documents

## 🆘 Getting Help

### Step-by-Step Help Process

1. **Check Quick Start Guide** - [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
   - Covers most common use cases
   - 5-minute introduction

2. **Search Documentation Index** - [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)
   - Find relevant documentation
   - Organized by task and user type

3. **Try Examples** - [../examples/README.md](../examples/README.md)
   - Working code samples
   - Common use cases

4. **Check Troubleshooting** - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
   - Common issues and solutions
   - Diagnostic commands

5. **Enable Debug Logging**

   ```bash
   python -m apgi_framework.cli --log-level DEBUG run-test primary
   ```

6. **Run System Validation**

   ```bash
   python -m apgi_framework.cli validate-system --detailed
   ```

### Support Resources

- **Documentation**: This directory
- **Examples**: `../examples/` directory
- **Logs**: `results/apgi_framework.log`
- **System Validation**: `python -m apgi_framework.cli validate-system`

## 📦 Documentation Structure

```text
docs/
├── README.md                                    ← You are here
├── DOCUMENTATION_INDEX.md                       ← Complete index
│
├── Getting Started/
│   ├── QUICK_START_GUIDE.md                    ← Start here (5 min)
│   ├── GUI_VISUAL_GUIDE.md                     ← Visual GUI guide
│   └── USER_GUIDE.md                           ← Complete manual
│
├── Reference/
│   ├── CLI_REFERENCE.md                        ← CLI documentation
│   ├── RESULTS_INTERPRETATION_GUIDE.md         ← Understanding results
│   └── parameter_validation_guide.md           ← Validation reference
│
├── Troubleshooting/
│   ├── TROUBLESHOOTING.md                      ← Problem solving
│   └── ERROR_HANDLING_QUICK_REFERENCE.md       ← Error patterns
│
├── Theory/
│   ├── ../APGI-Falsification.md                 ← Falsification theory
│   ├── ../APGI-Ignition-Equation.md             ← Mathematical framework
│   └── ../APGI-Testable-Predictions.md          ← Framework predictions
│
└── Implementation/
    ├── TASK_3.1_IMPLEMENTATION_SUMMARY.md      ← Validation implementation
    ├── TASK_3.2_ERROR_HANDLING_SUMMARY.md      ← Error handling implementation
    └── clinical_parameter_extraction_guide.md   ← Clinical parameters
```

## 🔄 Documentation Updates

**Current Version:** 1.0  
**Last Updated:** 2025-01-07

### Recent Additions

- ✨ Quick Start Guide - 5-minute introduction
- ✨ GUI Visual Guide - Visual walkthrough with ASCII diagrams
- ✨ Enhanced Documentation Index
- ✨ This README for easy navigation

### Contributing to Documentation

To improve documentation:

1. Identify gaps or unclear sections
2. Follow existing documentation style
3. Include working examples
4. Test all code samples
5. Update this README and index

## 🎓 Learning Path

### Beginner Path (1-2 hours)

1. [Quick Start Guide](QUICK_START_GUIDE.md) - 5 min
2. [GUI Visual Guide](GUI_VISUAL_GUIDE.md) - 15 min
3. Run first test - 5 min
4. [Results Interpretation Guide](RESULTS_INTERPRETATION_GUIDE.md) - 30 min
5. [Examples](../examples/README.md) - 30 min

### Intermediate Path (3-4 hours)

1. Complete Beginner Path
2. [User Guide](USER_GUIDE.md) - 1 hour
3. [CLI Reference](CLI_REFERENCE.md) - 30 min
4. [Batch Processing Example](../examples/02_batch_processing_configurations.py) - 30 min
5. [Custom Analysis Example](../examples/03_custom_analysis_saved_results.py) - 30 min

### Advanced Path (5-8 hours)

1. Complete Intermediate Path
2. [APGI Falsification Theory](../APGI-Falsification.md) - 1 hour
3. [APGI Ignition Equation](../APGI-Ignition-Equation.md) - 1 hour
4. [Extending Framework Example](../examples/04_extending_falsification_criteria.py) - 1 hour
5. [Error Handling Reference](ERROR_HANDLING_QUICK_REFERENCE.md) - 30 min
6. Explore source code - 2+ hours

## 📞 Contact and Support

For questions, issues, or contributions:

1. Check documentation first
2. Review examples for similar use cases
3. Run system validation
4. Enable debug logging
5. Check logs for detailed information

---

**Ready to get started?** → [Quick Start Guide](QUICK_START_GUIDE.md)

**Need help?** → [Troubleshooting Guide](TROUBLESHOOTING.md)

**Want to learn more?** → [Documentation Index](DOCUMENTATION_INDEX.md)

---

**Version:** 1.0  
**Last Updated:** 2025-01-07  
**Maintainer:** APGI Framework Development Team
