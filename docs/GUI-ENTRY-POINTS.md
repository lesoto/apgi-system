# APGI Framework GUI Entry Points

## Overview

The APGI Framework provides multiple GUI entry points for different use cases, from comprehensive research interfaces to specialized utility runners.

---

## Primary Entry Points

### 1. `APGI_GUI.py` (5,649 lines)

**Purpose:** Main comprehensive GUI application for APGI System

**Features:**

- Full-featured experiment management
- Real-time monitoring dashboard with system metrics
- Advanced parameter configuration
- Data visualization and export (CSV, JSON)
- Multi-threaded experiment execution
- Theme management with dark/light modes
- Matplotlib integration for plotting
- Comprehensive logging and error handling
- BIDS-compatible data organization

**Use Case:** Primary interface for researchers and power users

**Usage:**

```bash
python APGI_GUI.py
```

---

### 2. `APGI_Application_GUI.py` (6,974 lines)

**Purpose:** Application-level GUI with modern CustomTkinter interface

**Features:**

- Modern CustomTkinter-based UI with theming
- Multi-experiment support with tabbed interface
- Real-time console output with log levels
- Advanced plotting with matplotlib
- Data export to CSV, Excel, JSON formats
- Session persistence and auto-save
- Sidebar navigation with tooltips
- Progress tracking and status indicators
- Keyboard shortcuts and accessibility features

**Use Case:** Application-level interface with modern UI

**Usage:**

```bash
python APGI_Application_GUI.py
```

---

### 3. `GUI-Launcher.py` (1,396 lines)

**Purpose:** Centralized launcher for all GUI applications

**Features:**

- Menu-driven selection of 50+ applications
- Real-time availability checking (✓/✗ indicators)
- Category-based organization (10 categories)
- DPI-aware window scaling for different screen sizes
- Support for 4K, QHD, FHD, and smaller displays
- Scrollable interface for large app collections
- Command-line options (--list, --version)
- Visual status indicators and file paths

**Categories:**
- Core Applications (7 apps)
- Analysis & Visualization (9 apps)
- Configuration & Management (7 apps)
- Development & Testing (5 apps)
- CLI Tools & Framework (8 apps)
- API & Backend (2 apps)
- Testing & Benchmarks (4 apps)
- Utilities & Tools (23 apps)
- Examples & Tutorials (6 apps)

**Use Case:** Entry point for users who need access to multiple GUI types

**Usage:**

```bash
python GUI-Launcher.py              # Launch GUI
python GUI-Launcher.py --list       # List available applications
python GUI-Launcher.py --version    # Show version
```

---

## Specialized GUI Applications

### 4. `Assistant_GUI.py` (8,848 lines)

**Purpose:** AI Assistant interface with advanced capabilities

**Features:**

- AI-powered assistant with context-aware responses
- Module loading and dynamic plugin system
- Real-time chat interface with history
- Tool calling and function execution
- File attachment and processing
- Session management and persistence
- Theme integration with the framework
- System monitoring integration
- Keyboard shortcuts (Ctrl+Enter, etc.)

**Use Case:** AI-assisted research and analysis

**Usage:**

```bash
python Assistant_GUI.py
```

---

### 5. `Psychological_States_GUI.py` (9,286 lines)

**Purpose:** Psychological State Parameter Library with Advanced Visualizations

**Features:**

- Complete parameter mappings for 51+ psychological states
- Interactive visualizations (radar charts, heatmaps)
- Embedded matplotlib rendering (no browser dependencies)
- State classification and clinical awareness
- Specparam/FOOOF integration for EEG analysis
- Dataset catalog integration
- Export capabilities (JSON, CSV)
- Real-time state monitoring

**Use Case:** Psychological state analysis and visualization

**Usage:**

```bash
python Psychological_States_GUI.py
```

---

### 6. `APGI_Simulation_GUI.py` (931 lines)

**Purpose:** Simulation visualization and control GUI

**Features:**

- Real-time cognitive state monitoring
- Oscillatory spectrum analysis
- Biofeedback integration
- Energy management visualization
- Performance metrics display
- Data export capabilities
- Queue-based data processing
- Rotating log files

**Use Case:** Simulation control and real-time monitoring

**Usage:**

```bash
python APGI_Simulation_GUI.py
```

---

## Utility Runners

### 7. `Utils_GUI.py` (309 lines)

**Purpose:** GUI to run all utils folder scripts

**Features:**

- Run utility scripts from the utils folder
- Real-time output display in scrolled text widget
- Error handling and process management
- Script organization by category
- Process termination capabilities
- Output logging and save options

**Use Case:** Quick access to utility scripts without command line

**Usage:**

```bash
python Utils_GUI.py
```

---

### 8. `Tests_GUI.py` (169 lines)

**Purpose:** GUI to run all tests folder scripts and complete test suite

**Features:**

- Run individual test scripts
- Run all tests sequentially
- Run complete test suite using pytest
- Real-time output display with color coding
- Error handling and process management
- Test results summary panel
- Success/failure counters
- Process termination capabilities

**Use Case:** GUI-based test execution for developers

**Usage:**

```bash
python Tests_GUI.py
```

---

## Application-Specific GUIs

### 9. `apps/apgi-design.py` (1,635 lines)

**Purpose:** Neuroscape / Architect visual design application

**Features:**

- Canvas-based visualization with matplotlib
- Parameter control panel (threshold, precision, prediction error, neuromodulator)
- Real-time 10Hz data animation
- Session management with JSON/CSV export
- Theme manager with purple/green color scheme
- Multi-panel visualization (radar, SDE trajectory, correlation heatmap)
- State classification and clinical awareness
- Responsive layout with proportional sizing
- Keyboard shortcuts (Ctrl+E export, Ctrl+S statistics)
- Live equation display (Π × |ε| vs Bt ignition check)

**Use Case:** Visual experiment design and parameter tuning

**Usage:**

```bash
python apps/apgi-design.py
```

---

### 10. `apps/gui_template.py`

**Purpose:** GUI template for development

**Features:**

- Starter template for new GUI applications
- Standard layout and styling
- Placeholder components
- Documentation and examples

**Use Case:** Starting point for developing new GUIs

**Usage:**

```bash
python apps/gui_template.py
```

---

## User Guide

| User Need | Recommended Entry Point | Reason |
|-----------|------------------------|--------|
| **New Users** | `GUI-Launcher.py` | Easy interface selection with organized categories |
| **Researchers** | `APGI_GUI.py` | Full-featured experiment management |
| **Modern UI Preference** | `APGI_Application_GUI.py` | CustomTkinter with advanced theming |
| **Simulation Control** | `APGI_Simulation_GUI.py` | Real-time monitoring and biofeedback |
| **AI Assistance** | `Assistant_GUI.py` | AI-powered research assistant |
| **Psychological Analysis** | `Psychological_States_GUI.py` | 51+ state mappings and visualizations |
| **Developers** | `Tests_GUI.py` | Test execution with summary reports |
| **Utilities** | `Utils_GUI.py` | Quick access to all utility scripts |
| **Visual Designers** | `apps/apgi-design.py` | Canvas-based parameter tuning |
| **Multi-App Access** | `GUI-Launcher.py` | Single entry to all 50+ applications |

---

## File Organization

```
APGI Framework GUI Structure
│
├── Root-Level GUIs (8 applications)
│   ├── APGI_GUI.py                 # Main comprehensive GUI (5,649 lines)
│   ├── APGI_Application_GUI.py     # Modern CustomTkinter app (6,974 lines)
│   ├── APGI_Simulation_GUI.py      # Simulation control (931 lines)
│   ├── Assistant_GUI.py            # AI Assistant interface (8,848 lines)
│   ├── Psychological_States_GUI.py # Psychological analysis (9,286 lines)
│   ├── GUI-Launcher.py             # Centralized launcher (1,396 lines)
│   ├── Tests_GUI.py                # Test runner (169 lines)
│   └── Utils_GUI.py                # Utility runner (309 lines)
│
├── apps/ (2 applications)
│   ├── apgi-design.py              # Visual design system (1,635 lines)
│   └── gui_template.py             # Development template
│
└── Framework GUI Modules (35+ modules)
    ├── apgi_framework/gui/         # 15+ GUI modules
    ├── apgi_gui/                   # GUI components
    └── utils/gui_*.py              # GUI utilities
```

---

## GUI Dependencies

### Required

- `tkinter` (Python standard library)
- `matplotlib` with `tkagg` backend
- `numpy`, `pandas`

### Optional (for specific features)

- `customtkinter` (for `APGI_Application_GUI.py`)
- `psutil` (for system monitoring in `APGI_GUI.py`)
- `PyYAML` (for configuration management)
- `keyboard` (for global shortcuts)
- `pytest` (for test running in `Tests_GUI.py`)
- `specparam` or `fooof` (for EEG analysis in `Psychological_States_GUI.py`)
- `httpx` (for HTTP requests)

### Install All Dependencies

```bash
pip install customtkinter matplotlib numpy pandas psutil pyyaml keyboard pytest specparam httpx
```

---

## Quick Reference

| Script | Lines | Category | Key Feature |
|--------|-------|----------|-------------|
| `APGI_GUI.py` | 5,649 | Primary | Full experiment management |
| `APGI_Application_GUI.py` | 6,974 | Primary | Modern CustomTkinter UI |
| `Assistant_GUI.py` | 8,848 | Specialized | AI-powered assistant |
| `Psychological_States_GUI.py` | 9,286 | Specialized | 51+ psychological states |
| `GUI-Launcher.py` | 1,396 | Utility | Launches 50+ applications |
| `APGI_Simulation_GUI.py` | 931 | Specialized | Real-time simulation |
| `Tests_GUI.py` | 169 | Utility | Test runner with summaries |
| `Utils_GUI.py` | 309 | Utility | Utility script runner |
| `apps/apgi-design.py` | 1,635 | Specialized | Visual parameter tuning |
| `apps/gui_template.py` | - | Template | New GUI starter template |
