# APGI-Simulation Standalone Package Plan

## Overview

Create a production-ready Python package `apgi-simulation` that can be installed via:

```bash
pip install apgi-simulation
```

## Current State Analysis

### Project Structure

- **Core Package**: `apgi_system/` - Allostatic Precision-Gated Ignition Framework
- **GUI Package**: `apgi_gui/` - GUI components (imports from root-level APGI-GUI.py)
- **API Package**: `api/` - API components
- **Standalone Scripts**: Root-level .py files (APGI_GUI.py, APGI_Simulation_GUI.py, etc.)
- **Tests**: `tests/` directory with unit, integration, property tests
- **Documentation**: `docs/` directory

### Current Issues for Distribution

1. **Partial Package Declaration**: `pyproject.toml` only declares `apgi_system`, missing `apgi_gui`, `api`
2. **Non-Standard Imports**: `apgi_gui/__init__.py` uses dynamic import from root-level file
3. **Missing Entry Points**: No CLI commands defined for easy script execution
4. **Resource Files**: No MANIFEST.in for including non-Python assets (icons, configs)
5. **Version Consistency**: Version declared in multiple places
6. **Missing Package Data**: Resources (icons, configs) not included in distribution
7. **No CI Testing**: No automated build verification before publishing
8. **Missing Security Scanning**: No dependency vulnerability checks in CI
9. **Incomplete PyPI Metadata**: Missing classifiers, keywords, project URLs
10. **No Platform Validation**: Pure Python but not tested across platforms

## Implementation Status

### Phase 1: Package Structure Refactoring ✅

- **Consolidate GUI Module**: Done. Moved `APGI_GUI.py` to `apgi_gui/main.py`.
- **Refactor apgi\_gui/\_\_init\_\_.py**: Done. Updated to use standard imports.
- **Internal Imports**: Finalized relative imports and resource management.
- **Resource Consolidation**: Moved icons and configs to `apgi_gui/resources` and `apgi_simulation/resources`.

### Phase 2: Entry Points & CLI ✅

- **Define Console Scripts**: Added `apgi-simulate`, `apgi-analysis`, and `apgi-gui` to `pyproject.toml`.
- **Create CLI Modules**: Created `apgi_simulation/cli.py` and `apgi_gui/cli.py`.

### Phase 3: Version Management ✅

- **Single Source of Truth**: Created `apgi_simulation/_version.py` and linked to `apgi_simulation/__init__.py` and `pyproject.toml`.

### Phase 4: Dependencies Management ✅

- **Extras Definition**: Defined `gui` and `api` extras in `pyproject.toml`.

### Phase 5: Testing & Quality ✅

- **CI/CD Workflow**: Implemented `.github/workflows/ci.yml` and `.github/workflows/release.yml`.
- **Security Scanning**: Implemented `.github/workflows/audit.yml` for dependency vulnerability checks.

## Implementation Plan

### Phase 1: Package Structure Refactoring

#### 1.1 Consolidate GUI Module

**Priority**: High

**Actions**:

- Move GUI implementation from `APGI_GUI.py` into `apgi_gui/main.py`
- Refactor `apgi_gui/__init__.py` to use standard imports
- Update all internal imports to use relative imports

**Files to Create/Modify**:

- `apgi_gui/main.py` (new - extract from APGI_GUI.py)
- `apgi_gui/__init__.py` (refactor)
- `apgi_gui/components/` (ensure all components included)

#### 1.2 Update pyproject.toml

**Priority**: High

**Actions**:

- Add `apgi_gui` and `api` to packages list
- Define console script entry points (cli vs gui_scripts)
- Add complete PyPI metadata (classifiers, keywords, URLs)
- Configure package data inclusion
- Add long_description_content_type

**Complete Target Configuration**:

```toml
[project]
name = "apgi-simulation"
dynamic = ["version"]
description = "Allostatic Precision-Gated Ignition Framework"
readme = {file = "README.md", content-type = "text/markdown"}
requires-python = ">=3.11"
license = {text = "MIT"}
keywords = [
    "active-inference",
    "free-energy-principle",
    "predictive-processing",
    "computational-neuroscience",
    "cognitive-modeling",
    "neural-simulation",
    "allostasis",
    "interoception"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Operating System :: OS Independent",
    "Natural Language :: English",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/lesoto/apgi-simulation"
Documentation = "https://github.com/lesoto/apgi-simulation/blob/main/docs/README.md"
Repository = "https://github.com/lesoto/apgi-simulation"
"Bug Tracker" = "https://github.com/lesoto/apgi-simulation/issues"
Changelog = "https://github.com/lesoto/apgi-simulation/blob/main/CHANGELOG.md"

[tool.setuptools]
packages = ["apgi_system", "apgi_gui", "api"]
package-data = {
    "apgi_system" = ["py.typed"],
    "apgi_gui" = ["py.typed", "resources/**/*"],
    "api" = ["py.typed"]
}
zip-safe = false
```

#### 1.3 Create MANIFEST.in

**Priority**: High

**Purpose**: Include non-Python files in distribution and ensure clean builds

**Content**:

```text
# Include documentation
include README.md
include LICENSE
include CHANGELOG.md
include requirements.txt
include requirements-build.txt

# Include type hints marker (PEP 561)
recursive-include apgi_system py.typed
recursive-include apgi_gui py.typed
recursive-include api py.typed

# Include GUI resources
recursive-include resources *.icns *.ico *.png *.jpg *.svg
recursive-include resources/icons *.icns *.ico
recursive-include resources/icons/apgi.iconset *

# Include default configs
recursive-include config *.yaml *.yml *.json

# Include Python source
recursive-include apgi_system *.py
recursive-include apgi_gui *.py
recursive-include api *.py

# Exclude test files from distribution
recursive-exclude tests *
recursive-exclude **/test_*.py
global-exclude __pycache__/*
global-exclude *.pyc

# Exclude build artifacts and development files
global-exclude *.so
exclude .git*
exclude .dockerignore
exclude Dockerfile
exclude docker-compose.yml
exclude k8s/**/*
exclude .github/**/*
exclude standalone-package.md
```

### Phase 2: Entry Points & CLI

#### 2.1 Define Console Scripts

**Priority**: High

**Add to pyproject.toml** - Use `gui-scripts` for GUI entry point (no console window on Windows):

```toml
[project.scripts]
apgi-simulate = "apgi_system.cli:main"
apgi-analysis = "apgi_system.analysis:cli_main"

[project.gui-scripts]
apgi-gui = "apgi_gui.cli:main"
```

**Rationale**: `gui_scripts` prevents console window popup on Windows GUI apps.

#### 2.2 Create CLI Modules

**Priority**: High

**Files to Create**:

- `apgi_system/cli.py` - Command-line interface for core simulations
- `apgi_gui/cli.py` - CLI to launch GUI

**Example CLI Structure**:

```python
# apgi_system/cli.py
import argparse
import sys
from apgi_system.system import APGISystem

def main():
    parser = argparse.ArgumentParser(
        description="APGI Simulation CLI"
    )
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--mode", choices=["single", "batch"], default="single")
    args = parser.parse_args()
    
    system = APGISystem(config_path=args.config)
    if args.mode == "single":
        system.run_single_trial()
    else:
        system.run_batch()

if __name__ == "__main__":
    main()
```

### Phase 3: Version Management

#### 3.1 Single Source of Truth

**Priority**: Medium

**Approach**: Use `_version.py` pattern

**Create** `apgi_system/_version.py`:

```python
__version__ = "0.1.0"
```

**Update** `apgi_system/__init__.py`:

```python
from apgi_system._version import __version__
```

**Update** `pyproject.toml`:

```toml
[project]
dynamic = ["version"]
...
[tool.setuptools.dynamic]
version = {attr = "apgi_system.__version__"}
```

### Phase 4: Dependencies Management

#### 4.1 Core vs Optional Dependencies

**Priority**: Medium

**Current** `pyproject.toml` already has good structure:

- Core deps: numpy, scipy, matplotlib, etc.
- Optional `ml`: jax, torch
- Optional `dev`: testing, linting tools
- Optional `testing`: hypothesis, pytest extensions

#### 4.2 GUI Dependencies Extra

**Priority**: Medium

**Refinements**:

- Move heavy ML dependencies (jax, torch) to `ml` extra
- Create `gui` extra for GUI dependencies (tkinter alternatives, etc.)
- Create `api` extra for FastAPI/uvicorn if API server included

**Add to pyproject.toml**:

```toml
[project.optional-dependencies]
gui = [
    "Pillow>=9.0.0",
    # Add any GUI-specific deps
]
api = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
    "starlette>=0.36.3",
    "pydantic>=2.8.0",
]
```

### Phase 5: Testing & Quality

#### 5.1 CI/CD Testing Workflow

**Priority**: High

**Create** `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}
      - name: Install dependencies
        run: pip install -e ".[dev,testing]"
      - name: Run tests
        run: pytest tests/ -v --cov
      - name: Type check
        run: mypy apgi_system apgi_gui api
      - name: Security scan
        run: |
          pip install bandit safety
          bandit -r apgi_system apgi_gui api -f json -o bandit-report.json || true
          safety check

  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Build package
        run: |
          pip install build check-wheel-contents
          python -m build
      - name: Check wheel
        run: |
          pip install twine
          twine check dist/*
          check-wheel-contents dist/*.whl
      - name: Test install
        run: |
          pip install dist/*.whl
          python -c "import apgi_system; import apgi_gui; print('OK')"
          apgi-simulate --help
```

#### 5.2 Package Import Tests

**Create** `tests/test_package_imports.py`:

```python
"""Test that all package modules can be imported after installation."""

def test_import_apgi_system():
    import apgi_system
    assert hasattr(apgi_system, '__version__')

def test_import_core_modules():
    from apgi_system.core import ActiveInferenceEngine
    from apgi_system.core import FreeEnergyCalculator
    from apgi_system.ignition import GlobalWorkspace

def test_import_apgi_gui():
    import apgi_gui
    assert hasattr(apgi_gui, 'APGIGui')

def test_import_api():
    import api
    assert hasattr(api, 'create_app')

def test_entry_points_exist():
    """Verify all entry points are registered."""
    from importlib.metadata import entry_points
    scripts = entry_points(group='console_scripts')
    gui_scripts = entry_points(group='gui_scripts')
    assert any(e.name == 'apgi-simulate' for e in scripts)
    assert any(e.name == 'apgi-gui' for e in gui_scripts)

def test_package_data_included():
    """Verify resources are accessible."""
    from importlib.resources import files
    gui_files = files('apgi_gui')
    assert gui_files is not None
```

### Phase 6: Build & Distribution

#### 6.1 Build Configuration with setuptools-scm

**Priority**: High

**Update** `pyproject.toml` build section with automatic versioning:

```toml
[build-system]
requires = ["setuptools>=65.0", "setuptools-scm>=8.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
write_to = "apgi_system/_version.py"
version_scheme = "release-branch-semver"
local_scheme = "node-and-timestamp"
```

**Key improvements**:

- `setuptools-scm` generates version from git tags automatically
- `write_to` creates version file for runtime access
- Semantic versioning scheme for releases

#### 6.2 Required Distribution Files

**Priority**: High

**Ensure these files exist**:

- `LICENSE` - MIT license file (required for PyPI)
- `README.md` - Main package documentation
- `CHANGELOG.md` - Version history (PyPI best practice)
- `apgi_system/py.typed` - PEP 561 marker for typed package
- `apgi_gui/py.typed` - PEP 561 marker
- `api/py.typed` - PEP 561 marker

**Create marker files**:

```bash
touch apgi_system/py.typed apgi_gui/py.typed api/py.typed
```

#### 6.3 GitHub Actions for PyPI (Production-Grade)

**Priority**: Critical

**Create** `.github/workflows/publish.yml` with staging and trusted publishing:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for setuptools-scm
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python }}
      - name: Install build tools
        run: pip install build check-wheel-contents
      - name: Build package
        run: python -m build
      - name: Verify wheel
        run: check-wheel-contents dist/*.whl
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ matrix.os }}-py${{ matrix.python }}
          path: dist/

  test-install:
    needs: build
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: dist-*
          merge-multiple: true
          path: dist/
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Test wheel install
        run: |
          pip install dist/*.whl
          python -c "import apgi_system; import apgi_gui; print('Import OK')"
          apgi-simulate --help

  publish-testpypi:
    needs: test-install
    runs-on: ubuntu-latest
    environment: testpypi
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: dist-*
          merge-multiple: true
          path: dist/
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          skip-existing: true

  publish-pypi:
    needs: publish-testpypi
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # Trusted publishing (OIDC)
    steps:
      - uses: actions/download-artifact@v4
        with:
          pattern: dist-*
          merge-multiple: true
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

**Key improvements**:

- Multi-platform builds (Linux, macOS, Windows)
- Multi-Python versions (3.11, 3.12, 3.13)
- TestPyPI staging before production
- Trusted publishing (OIDC) - no long-lived API tokens
- Wheel verification before upload

### Phase 7: Documentation

#### 7.1 Installation Documentation

**Create** `docs/INSTALLATION.md`:

```markdown
# Installation Guide

## pip install
```bash
pip install apgi-simulation
```

## With Optional Dependencies

```bash
# With ML support (Jax, PyTorch)
pip install apgi-simulation[ml]

# With GUI support
pip install apgi-simulation[gui]

# With API server
pip install apgi-simulation[api]

# Development install
pip install apgi-simulation[dev,testing]
```

### 7.2 Usage After Installation

**Update** main README with:

```markdown
## Quick Start

```python
from apgi_system import APGISystem

# Create and run simulation
system = APGISystem()
results = system.run_single_trial()
```

## CLI Usage

```bash
# Run simulation
apgi-simulate --config config.yaml

# Launch GUI
apgi-gui
```

## Implementation Checklist

### Phase 1: Structure

- [ ] Extract GUI from APGI_GUI.py to apgi_gui/main.py
- [ ] Refactor `apgi_gui/__init__.py` with standard imports + dual-mode compatibility
- [ ] Update pyproject.toml packages list (apgi_system, apgi_gui, api)
- [ ] Add complete PyPI metadata (classifiers, keywords, URLs)
- [ ] Create MANIFEST.in with resources and configs
- [ ] Create py.typed markers (PEP 561) in all packages
- [ ] Verify all subpackages included (core, ignition, interoception, neural, etc.)

### Phase 2: CLI

- [ ] Create apgi_system/cli.py
- [ ] Create apgi_gui/cli.py
- [ ] Add console_scripts entry points to pyproject.toml
- [ ] Add gui_scripts entry for GUI (no console window)
- [ ] Test CLI commands work after pip install
- [ ] Test backward compatibility with root-level scripts

### Phase 3: Version

- [ ] Configure setuptools-scm for automatic versioning
- [ ] Update `__init__.py` to import version from _version.py
- [ ] Verify version available at runtime: `apgi_system.__version__`

### Phase 4: Dependencies

- [ ] Refine optional dependency groups (gui, api, ml, dev, testing)
- [ ] Test minimal install vs full install
- [ ] Document dependency sizes for users

### Phase 5: Testing

- [ ] Create tests/test_package_imports.py
- [ ] Create .github/workflows/ci.yml with multi-platform testing
- [ ] Add security scanning (bandit, safety) to CI
- [ ] Add build verification to CI
- [ ] Verify tests pass from installed package

### Phase 6: Distribution

- [ ] Ensure LICENSE file exists
- [ ] Ensure CHANGELOG.md exists
- [ ] Create py.typed markers in all packages
- [ ] Update README for pip installation instructions
- [ ] Create GitHub Actions workflow for multi-platform builds
- [ ] Configure TestPyPI staging environment
- [ ] Configure PyPI production environment with trusted publishing

### Phase 7: Validation

- [ ] Build wheel: `python -m build`
- [ ] Verify wheel contents with `check-wheel-contents`
- [ ] Test install from wheel: `pip install dist/*.whl`
- [ ] Verify all entry points work: `apgi-simulate --help`
- [ ] Verify all imports work across platforms
- [ ] Upload to TestPyPI and verify
- [ ] Final upload to PyPI
- [ ] Test `pip install apgi-simulation` from PyPI

## Commands for Building and Testing

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Install build tools
pip install build twine

# Build package
python -m build

# Check package
python -m twine check dist/*

# Test install locally
pip install dist/apgi_simulation-0.1.0-py3-none-any.whl

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ apgi-simulation

# Upload to PyPI (final)
python -m twine upload dist/*
```

## Post-Installation Usage Examples

### Python API

```python
from apgi_system import APGISystem
from apgi_system.core import ActiveInferenceEngine

# Initialize system
system = APGISystem()

# Run experiment
results = system.run_experiment(
    duration=1000,
    save_results=True
)
```

### CLI

```bash
# Run with default configuration
apgi-simulate

# Run with custom config
apgi-simulate --config my_experiment.yaml --output results/

# Launch GUI
apgi-gui
```

### Jupyter Notebook

```python
from apgi_system.analysis import analyze_free_energy
from apgi_system.visualization import plot_results

# Analyze and visualize
analysis = analyze_free_energy(results)
fig = plot_results(analysis)
```

## Backward Compatibility Strategy

### For Existing Source-Installation Users

The package refactoring must not break existing workflows:

### 1. Keep Root-Level Scripts Functional

- `APGI_GUI.py` remains importable for existing users
- Add deprecation warnings but maintain functionality
- Gradual migration path over 2-3 minor versions

### 2. Dual-Mode Package Structure

```python
# apgi_gui/__init__.py - supports both modes
try:
    # New: Proper package import
    from .main import APGIGui
except ImportError:
    # Legacy: Dynamic import from root
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from APGI_GUI import APGIGui  # type: ignore
```

### 3. Migration Guide for Users

**Before (source installation)**:

```bash
git clone https://github.com/lesoto/apgi-simulation.git
cd apgi-simulation
python APGI_GUI.py
```

**After (pip installation)**:

```bash
pip install apgi-simulation
apgi-gui  # New CLI command
```

### 4. Dependency Strategy

- **Core install**: `pip install apgi-simulation` - simulation only
- **GUI install**: `pip install apgi-simulation[gui]` - with GUI support
- **ML install**: `pip install apgi-simulation[ml]` - with ML dependencies
- **Full install**: `pip install apgi-simulation[all]` - everything

### 5. Version Compatibility Matrix

| Package Version | Python Versions | Breaking Changes |
|:----------------|:----------------|:-----------------|
| 0.1.x           | 3.11, 3.12      | Initial release  |
| 0.2.x           | 3.11-3.13       | CLI additions    |
| 1.0.x           | 3.11-3.13       | Stable API       |

### Development Recommendations

1. **GUI Dependencies**: Keep tkinter-based GUI as optional; headless servers don't need it
2. **ML Dependencies**: Jax and PyTorch remain optional extras due to size
3. **Python Version**: Require >=3.11 for modern type hints and performance
4. **Type Safety**: PEP 561 `py.typed` markers enable mypy for downstream users
