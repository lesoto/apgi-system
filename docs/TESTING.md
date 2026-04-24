# APGI Framework Testing Suite

This document provides information about the testing infrastructure for the APGI Framework.

## 📊 Overview

The APGI Framework testing suite has been completely reorganized and fixed to provide:

- __713 tests__ across __36 test suites__
- __0 collection errors__ (previously had 6+ errors)
- __Properly organized__ test structure
- __Comprehensive test runner__ with reporting
- __Working GUI test integration__

## 🏗️ Test Organization

### Test Categories

- __Unit Tests__ (583 tests): Fast, isolated component tests
- __Integration Tests__ (8 tests): Cross-component integration tests  
- __GUI Tests__ (78 tests): Graphical user interface component tests
- __Performance Tests__ (17 tests): Benchmarks and performance validation
- __Property Tests__ (27 tests): Property-based testing with Hypothesis

### Test Directory Structure

```text
apgi-experiments/
├── tests/                          # Main test directory
│   ├── test_*.py                  # Unit and integration tests
│   ├── test_*_properties.py      # Property-based tests
│   └── test_*_simple.py          # Simplified test variants
├── benchmarks/                     # Performance benchmarks
│   ├── test_performance.py
│   └── conftest.py
├── research/                       # Domain-specific tests
│   └── interoceptive_gating/
│       └── tests/
└── apgi_framework/                # Framework internal tests
    ├── tests/
    ├── testing/                   # Test infrastructure
    └── utils/test_utils.py        # Test utilities
```

## 🚀 Quick Start

### Run All Tests

```bash
python run_tests.py --all
```

### Run Specific Categories

```bash
# Unit tests only
python run_tests.py --unit

# GUI tests with coverage
python run_tests.py --gui --coverage

# Performance tests
python run_tests.py --performance
```

### Discover Tests

```bash
python run_tests.py --discover
```

### Generate Reports

```bash
python run_tests.py --all --report test_results.json
```

## 🛠️ Test Infrastructure

### Core Components

1. __TestUtilities__ (`apgi_framework.utils.test_utils`)
   - Test discovery and organization
   - Test execution coordination
   - Result processing and reporting

2. __TestExecutionController__ (`apgi_framework.gui.test_execution_controller`)
   - GUI-based test execution
   - Real-time progress monitoring
   - Cancellation and pause/resume support

3. __ComprehensiveTestRunner__ (`run_tests.py`)
   - Command-line test runner
   - Multiple execution modes
   - Comprehensive reporting

### Test Data Models

- __TestDefinition__: Individual test case representation
- __TestCollection__: Group of related tests
- __TestRunExecution__: Test execution session
- __TestResults__: Execution results summary
- __TestConfiguration__: Execution parameters

## 🔧 Configuration

### pytest.ini

- Test discovery patterns
- Marker definitions
- Execution settings
- Logging configuration

### pyproject.toml

- Comprehensive testing configuration
- Coverage settings
- CI/CD integration
- Parallel execution settings

## 📈 Test Results

### Current Status

- ✅ __713 tests__ successfully discovered
- ✅ __0 collection errors__
- ✅ __GUI integration working__
- ✅ __Test runner functional__

### Test Categories Distribution

```text
Unit Tests:        583 (81.8%)
GUI Tests:          78 (10.9%)
Property Tests:     27 (3.8%)
Performance Tests:  17 (2.4%)
Integration Tests:   8 (1.1%)
```

## 🎯 Best Practices

### Writing Tests

1. Use descriptive test names following `test_<functionality>` pattern
2. Organize tests by category using appropriate markers
3. Include proper docstrings for test documentation
4. Use the TestUtilities class for complex test scenarios

### Test Category Markers

- Mark unit tests with `@pytest.mark.unit`
- Mark integration tests with `@pytest.mark.integration`
- Mark GUI tests with `@pytest.mark.gui`
- Mark performance tests with `@pytest.mark.performance`

### Running Tests

- Use `run_tests.py` for comprehensive test execution
- Use pytest directly for quick test runs
- Generate coverage reports regularly
- Use discovery mode to understand test organization

## 🔍 GUI Testing

### Test Runner GUI

The framework includes a comprehensive GUI test runner accessible through:

- Main GUI application
- Standalone test runner window
- Real-time progress monitoring
- Test selection and filtering

### GUI Test Features

- Test discovery and organization
- Category-based filtering
- Real-time execution monitoring
- Detailed result reporting
- Export functionality

## 📊 Reporting

### Report Formats

- __JSON__: Machine-readable detailed results
- __HTML__: Human-readable coverage reports
- __Console__: Real-time execution feedback

### Report Contents

- Test execution summary
- Category-wise breakdown
- Coverage metrics
- Performance benchmarks
- Failure analysis

## 🔄 Continuous Integration

### CI Configuration

- Automated test execution on commits
- Coverage reporting
- Performance regression detection
- Test result artifacts

### Quality Gates

- Minimum coverage threshold: 80%
- Zero tolerance for critical failures
- Performance regression detection
- Test execution time limits

## 🛠️ Development Workflow

### Adding New Tests

1. Create test file in appropriate directory
2. Use proper naming conventions
3. Add appropriate markers
4. Update test documentation
5. Run discovery to verify integration

### Debugging Tests

1. Use verbose mode for detailed output
2. Run specific test categories
3. Use pytest debugging features
4. Check GUI logs for GUI tests
5. Review coverage reports

## 📚 Additional Resources

### Documentation

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Property Testing](https://hypothesis.works/)
- [Coverage.py](https://coverage.readthedocs.io/)

### Tools

- __pytest__: Test framework
- __hypothesis__: Property-based testing
- __coverage.py__: Coverage measurement
- __customtkinter__: GUI framework
- __PySide6__: Advanced GUI components

## 🤝 Contributing

When contributing to the testing suite:

1. Follow existing naming conventions
2. Add appropriate test markers
3. Include comprehensive documentation
4. Update this README if needed
5. Ensure all tests pass before submission

---

__Last Updated__: 2025-01-22
__Test Suite Version__: 2.0
__Framework Version__: APGI Framework v1.0+
