# Coverage Analysis Scripts

This directory contains scripts for comprehensive test coverage analysis and reporting.

## Scripts

### run_coverage.py

Main coverage analysis script that runs tests with coverage measurement and generates reports.

**Usage:**
```bash
python scripts/run_coverage.py
```

**Features:**
- Runs pytest with full coverage measurement
- Generates HTML, JSON, XML, and terminal reports
- Identifies files with coverage gaps
- Provides summary statistics
- Exit code 0 if 100% coverage achieved

**Output:**
- `htmlcov/` - HTML coverage report (open `htmlcov/index.html` in browser)
- `coverage.json` - JSON coverage data for programmatic analysis
- `coverage.xml` - XML coverage report for CI/CD integration
- `.coverage` - Coverage database file

### analyze_gaps.py

Detailed gap analysis script that categorizes uncovered code by module and type.

**Usage:**
```bash
python scripts/analyze_gaps.py
```

**Features:**
- Analyzes coverage.json to identify all gaps
- Categorizes gaps by module (core, experiments, neural, api, etc.)
- Classifies gaps by type (error_path, edge_case, untested_logic)
- Generates detailed report with prioritization
- Saves analysis to JSON for tracking

**Output:**
- `coverage_gap_analysis.json` - Detailed gap analysis data
- Terminal report with gaps organized by module and type

## Makefile Commands

The Makefile provides convenient shortcuts for coverage analysis:

```bash
# Run tests with coverage and generate reports
make test-coverage

# Generate coverage report (HTML + terminal)
make coverage-report

# Analyze coverage gaps in detail
make coverage-gaps

# Run specific test types
make test-unit          # Unit tests only
make test-property      # Property-based tests only
make test-integration   # Integration tests only
```

## Coverage Configuration

Coverage settings are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov=apgi_system",
    "--cov=api",
    "--cov-fail-under=100",
    # ... other options
]

[tool.coverage.run]
source = ["apgi_system", "api"]
omit = [
    "**/apgi_gui.py",
    "**/*_GUI.py",
    "**/tests/*",
]
branch = true
```

## Hypothesis Configuration

Property-based testing is configured with multiple profiles:

- **dev** (default): 20 examples, fast feedback during development
- **ci**: 100 examples, balanced thoroughness for CI/CD
- **thorough**: 1000 examples, maximum coverage for critical testing

Set profile via environment variable:
```bash
export HYPOTHESIS_PROFILE=ci
pytest tests/property/
```

## CI/CD Integration

Coverage is automatically measured in GitHub Actions workflows:

- `.github/workflows/test.yml` - Basic test workflow with coverage
- `.github/workflows/ci-cd.yml` - Full CI/CD pipeline with coverage gates

Both workflows:
- Require 100% coverage to pass
- Upload coverage reports to Codecov
- Archive HTML reports as artifacts
- Use `HYPOTHESIS_PROFILE=ci` for property tests

## Workflow

1. **Run tests with coverage:**
   ```bash
   make test-coverage
   ```

2. **Review HTML report:**
   Open `htmlcov/index.html` in browser to see line-by-line coverage

3. **Analyze gaps:**
   ```bash
   make coverage-gaps
   ```

4. **Write tests for uncovered code:**
   - Focus on high-priority modules first (core, api)
   - Classify gaps: error paths, edge cases, or untested logic
   - Write appropriate unit, property, or integration tests

5. **Verify coverage:**
   ```bash
   make test-coverage
   ```

6. **Repeat until 100% coverage achieved**

## Tips

- Use `pytest --cov-report=term-missing` to see uncovered lines in terminal
- Use `pytest -k test_name --cov` to check coverage for specific tests
- Use `pytest -m unit --cov` to check coverage by test category
- Review `coverage_gap_analysis.json` to track progress over time
- Focus on meaningful tests, not just exercising code for coverage
