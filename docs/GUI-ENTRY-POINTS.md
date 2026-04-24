# APGI Framework GUI Entry Points

## Primary Entry Points

### 1. `GUI.py` (7,309 lines)

**Purpose:** Main comprehensive GUI application

**Features:**

- Full-featured experiment management
- Real-time monitoring dashboard
- Advanced parameter configuration
- Data visualization and export
- Multi-threaded experiment execution
- CustomTkinter-based modern UI
- Matplotlib integration for plotting
- Comprehensive experiment simulation (Dynamic Threshold, Precision Effects, etc.)
- Fallback implementations when main controller unavailable

**Use Case:** Primary interface for researchers and power users

**Usage:**

```bash
python GUI.py
```

## Secondary Entry Points

### 2. `GUI-Launcher.py` (1,060 lines)

**Purpose:** Centralized launcher for all GUI applications

**Features:**

- Menu-driven selection of different GUIs
- System information and requirements checking
- Easy switching between interfaces
- DPI-aware window scaling for different screen sizes
- Support for 4K, QHD, FHD, and smaller displays
- Command-line options for listing applications and version info

**Use Case:** Entry point for users who need access to multiple GUI types

**Usage:**

```bash
python GUI-Launcher.py              # Launch GUI
python GUI-Launcher.py --list       # List available applications
python GUI-Launcher.py --version    # Show version
```

### 3. `Utils-GUI.py` (641 lines)

**Purpose:** GUI to run all utils folder scripts

**Features:**

- Run utility scripts from the utils folder
- Real-time output display
- Error handling and process management
- Configuration-based script organization
- Timeout and retry support
- Process termination capabilities

**Use Case:** Quick access to utility scripts without command line

**Usage:**

```bash
python Utils-GUI.py
```

### 4. `Tests-GUI.py` (764 lines)

**Purpose:** GUI to run all tests folder scripts and complete test suite

**Features:**

- Run individual test scripts
- Run all tests sequentially
- Run complete test suite using pytest
- Real-time output display
- Error handling and process management
- Test categorization and filtering
- Process termination capabilities

**Use Case:** GUI-based test execution for developers

**Usage:**

```bash
python Tests-GUI.py
```

### 5. `apps/apgi-design.py` (1,674 lines)

**Purpose:** Neuroscape / Architect visual design application

**Features:**

- Canvas-based visualization with matplotlib
- Parameter control panel (threshold, precision, prediction error, neuromodulator)
- Real-time 10Hz data animation
- Session management with JSON export
- Theme manager with purple/green color scheme
- Keyboard shortcuts (Ctrl+E export, Ctrl+S statistics, etc.)
- Live equation display (Π × |ε| vs Bt ignition check)

**Use Case:** Visual experiment design and parameter tuning

**Usage:**

```bash
python apps/apgi-design.py
```

## User Guide

- **New Users:** Start with `GUI-Launcher.py` for easy interface selection
- **Researchers:** Use `GUI.py` for full-featured experiment management
- **Developers:** Use `Tests-GUI.py` for test execution and `Utils-GUI.py` for utilities
- **System Administrators:** Use `GUI-Launcher.py` to provide access to all interfaces
- **Visual Designers:** Use `apps/apgi-design.py` for canvas-based parameter tuning

## File Organization

The current structure provides multiple entry points for different use cases:

1. **GUI.py** - Main comprehensive application for researchers
2. **GUI-Launcher.py** - Centralized launcher for navigation
3. **Utils-GUI.py** - Utility script runner
4. **Tests-GUI.py** - Test execution interface
5. **apps/apgi-design.py** - Visual design application

This separation allows for:

- Clear separation of concerns
- Specialized interfaces for different user types
- Easier maintenance and testing
- Flexible deployment options

## Recommended Usage

| User Type | Recommended Entry Point | Reason |
| --------- | ----------------------- | ------ |
| **New Users** | `GUI-Launcher.py` | Easy interface selection with organized categories |
| **Researchers** | `GUI.py` | Full-featured experiment management |
| **Developers** | `Tests-GUI.py` | Test execution and debugging |
| **System Administrators** | `GUI-Launcher.py` | Access to all interfaces and deployment tools |
| **Visual Designers** | `apps/apgi-design.py` | Canvas-based parameter tuning |

## GUI Dependencies

All GUI applications require:

- `tkinter` (standard library)
- `customtkinter` (for `GUI.py`)
- `matplotlib` with `tkagg` backend
- `numpy`, `pandas`

Optional features require:

- `keyboard` module (for keyboard shortcuts in `GUI.py`)
- `pytest` (for test running in `Tests-GUI.py`)
