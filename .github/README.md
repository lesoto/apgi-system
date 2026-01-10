# GitHub Actions CI/CD

This directory contains the continuous integration and deployment workflows for the APGI System.

## Workflows

### `test.yml` - Test Suite

Runs on every push and pull request to `main` and `develop` branches.

**Steps:**

1. **Code Formatting Check** - Validates code formatting with `black`
2. **Linting** - Checks code quality with `flake8`
3. **Type Checking** - Validates type hints with `mypy` (non-blocking)
4. **Test Execution** - Runs full test suite with `pytest`
5. **Coverage Reporting** - Generates coverage reports and enforces 80% minimum coverage

**Coverage Threshold:** 80% - The build will fail if coverage drops below this threshold.

## Local Testing

Before pushing, you can run the same checks locally:

```bash
# Format check
black --check apgi_system tests

# Auto-format
black apgi_system tests

# Linting
flake8 apgi_system tests

# Type checking
mypy apgi_system --ignore-missing-imports

# Run tests with coverage
pytest tests/ -v --cov=apgi_system --cov-report=html --cov-report=term-missing
```

## Configuration Files

- `.flake8` - Flake8 linter configuration
- `pyproject.toml` - Black formatter and pytest configuration
- `.github/workflows/test.yml` - CI workflow definition

## Coverage Reports

Coverage reports are:

- Displayed in the terminal during CI runs
- Uploaded as artifacts (HTML format) for each CI run
- Optionally uploaded to Codecov for tracking over time

## Requirements

The CI pipeline validates:

- ✅ Code formatting (black)
- ✅ Code quality (flake8)
- ✅ Type safety (mypy)
- ✅ Test passing (pytest)
- ✅ Coverage threshold (80%)

All checks must pass for the CI pipeline to succeed.
