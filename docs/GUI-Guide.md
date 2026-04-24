# APGI System - GUI Application Guide

## Overview

The APGI GUI provides a real-time interface for interacting with the Allostatic Precision-Gated Ignition consciousness modeling framework. Built with Tkinter, it offers core system features through an intuitive graphical interface.

## Features

### 🎛️ **Complete System Control**

- **Real-time simulation** with start/pause/stop/reset controls
- **Adjustable simulation speed** (0.1x to 10x)
- **Live parameter adjustment** for all subsystems
- **Preset experimental tasks**

### 📊 **Multi-Panel Visualization**

The GUI currently provides three primary visualization tabs:

#### **Tab 1: Neural Activity**

- Ignition events timeline (scatter plot)
- Global workspace activity
- Exteroceptive/interoceptive precision dynamics
- Free energy trajectory

#### **Tab 2: Interoception**

- Heart rate monitoring
- Cortisol levels
- Allostatic load accumulation
- Metabolic energy reserves

#### **Tab 3: System Metrics**

- Somatic marker count
- Gamma band power (30-80 Hz)
- Beta band power (12-30 Hz)

*Note: Additional tabs (Self-Model, Oscillations, 3D State Space) are planned for future releases.*

### 🎚️ **Quick Parameter Controls**

Adjust in real-time:

- **Ignition Threshold** (1.0 - 5.0)
- **Exteroceptive Precision** (0.1 - 10.0)
- **Interoceptive Precision** (0.1 - 10.0)
- **Arousal Level** (0.0 - 1.0)
- **Stress Level** (0.0 - 1.0)
- **Activity Level** (0.0 - 1.0)
- **Learning Rate** (0.001 - 0.1)
- **Attention Gain** (0.5 - 3.0)

### 📋 **Menu System**

#### **File Menu**

- **New Session** (Ctrl+N) - Start fresh simulation
- **Load Configuration** (Ctrl+O) - Load YAML config
- **Save Configuration** (Ctrl+S) - Save current parameters
- **Export Data** (Ctrl+E) - Export to CSV/JSON
- **Export Plot** - Save current visualization
- **Auto-save Data** - Toggle automatic data saving
- **Exit** (Ctrl+Q) - Close application

#### **Edit Menu**

- **System Parameters** - Advanced parameter editing
- **Precision Settings** - Precision modulation controls
- **Ignition Threshold** - Threshold configuration
- **Reset to Defaults** - Restore default parameters

#### **Simulation Menu**

- **Start** (F5) - Begin simulation
- **Pause/Resume** (F6) - Toggle pause state
- **Stop** (F7) - Stop simulation
- **Reset** (F8) - Reset system to initial state
- **Run Preset Task** - Execute experimental paradigms

#### **View Menu**

- Toggle panel visibility
- Zoom controls
- Display customization

#### **Tools Menu**

- **Trigger Ignition Event** - Force ignition
- **Induce Stressor** - Apply allostatic stressor
- **Modulate Precision** - Precision modulation dialog
- **Inject Sensory Input** - Custom input injection
- **Set Body State** - Manual body state configuration
- **System Diagnostics** - View system health

#### **Analysis Menu**

- **Ignition Statistics** - Detailed ignition metrics
- **Energy Budget Report** - Metabolic analysis
- **Somatic Marker Analysis** - Marker statistics
- **Self-Model Coherence** - Coherence analysis
- **Generate Report** - Comprehensive text report

#### **Help Menu**

- **Documentation** - System overview
- **Keyboard Shortcuts** - Hotkey reference
- **About APGI System** - Version information

### 📈 **Status Indicators**

Real-time display of:

- **Simulation Time** (seconds)
- **Ignition Event Count**
- **Global Workspace State** (Idle/Broadcasting)
- **Metabolic Reserves** (percentage)
- **Allostatic Load** (percentage)
- **FPS** (frames per second)

### 📝 **Event Log**

Scrollable log showing:

- System initialization
- Simulation state changes
- Parameter modifications
- Ignition events
- Errors and warnings

## Installation & Setup

### Requirements

```bash
# Install dependencies
pip install -e .

# Or install GUI-specific requirements
pip install numpy scipy matplotlib pyyaml
```

### Launch GUI

```bash
# Method 1: Module execution (recommended)
python -m apgi_gui

# Method 2: CLI launcher with optional config
python -m apgi_gui.cli --config path/to/config.yaml

# Method 3: Python one-liner
python -c "from apgi_gui.main import main; main()"
```

## Quick Start Guide

### Basic Usage

1. **Launch Application**

   ```bash
   python -m apgi_gui
   ```

2. **Start Simulation**
   - Click "▶ Start" button or press F5
   - Observe real-time metrics updating

3. **Adjust Parameters**
   - Use sliders in "Quick Parameters" panel
   - Changes apply immediately to running simulation

4. **Pause/Analyze**
   - Click "⏸ Pause" or press F6
   - Navigate through tabs to inspect different aspects

5. **Export Results**
   - File → Export Data (Ctrl+E)
   - Choose CSV or JSON format
   - Save plots: File → Export Plot

### Advanced Usage

#### Running Preset Tasks

1. Simulation → Run Preset Task
2. Select from:
   - Attentional Blink
   - Change Blindness
   - Binocular Rivalry
   - Masking Paradigm
   - Iowa Gambling Task
3. Click "Run Task"

#### Manual Interventions

**Trigger Ignition:**

```bash
Tools → Trigger Ignition Event
```

Temporarily elevates arousal and stress levels to induce ignition, then
auto-restores after 2 seconds.

**Induce Stressor:**

```bash
Tools → Induce Stressor
```

Adds allostatic load spike

**Modulate Precision:**

```bash
Tools → Modulate Precision
```

Apply multiplicative factor to precision weights

#### Configuration Management

**Save Current Setup:**

```bash
File → Save Configuration (Ctrl+S)
```

Saves all parameter values to YAML

**Load Previous Setup:**

```bash
File → Load Configuration (Ctrl+O)
```

Restores parameters from YAML file

## Data Export Formats

### CSV Export

```csv
time, ignition, free_energy, extero_precision, intero_precision,...
0.00, 0, 1.234, 1.0, 0.8,...
0.01, 0, 1.245, 1.0, 0.8,...
0.02, 1, 2.456, 1.5, 0.9,...
```

### JSON Export

```json
[
  {
    "time": 0.00,
    "ignition": 0,
    "free_energy": 1.234,
    "extero_precision": 1.0,
    ...
  },
  ...
]
```

## Keyboard Shortcuts Reference

| Shortcut | Action |
| - | - |
| **Ctrl+N** / **⌘N** | New Session |
| **Ctrl+O** / **⌘O** | Load Configuration |
| **Ctrl+S** / **⌘S** | Save Configuration |
| **Ctrl+E** / **⌘E** | Export Data |
| **Ctrl+Q** / **⌘Q** | Exit Application |
| **F5** | Start Simulation |
| **F6** | Pause/Resume |
| **F7** | Stop Simulation |
| **F8** | Reset System |

*On macOS, use ⌘ (Command) in place of Ctrl.*

## Visualization Guide

### Understanding the Plots

#### **Ignition Events (Red Dots)**

- Each dot = consciousness event
- Clustering indicates high ignition rate
- Gaps indicate suppression/refractory periods

#### **Workspace Activity (Blue Line)**

- 0 = Idle (unconscious processing)
- 1 = Broadcasting (conscious access)
- Duration ~300-500ms per event

#### **Precision (Green/Red Lines)**

- Green = Exteroceptive (sensory)
- Red = Interoceptive (body)
- Higher = more influence on ignition

#### **Free Energy (Purple Line)**

- Prediction error magnitude
- Spikes precede ignition events
- Minimized through learning

#### **Heart Rate**

- Responds to arousal/activity
- Predicted by interoceptive model
- Prediction errors drive ignition

#### **Allostatic Load**

- Cumulative stress/deviation
- Rises during challenges
- Decay during recovery
- High load → higher ignition threshold

#### **Metabolic Reserves**

- Energy budget (0-100)
- Depletes during ignition (~7.5% per event)
- Recovers slowly over time
- Depletion → performance degradation

## Troubleshooting

### GUI Won't Start

```bash
# Check dependencies
pip install matplotlib

# Verify system installation
python -c "from apgi_framework.system import APGISystem; print('OK')"
```

### Slow Performance

- Reduce simulation speed (slider)
- Decrease buffer size in code
- Close other applications

### Plots Not Updating

- Check if simulation is running (not paused)
- Verify FPS counter shows activity
- Reset simulation (F8)

### Memory Issues

- Export data periodically
- Reset simulation to clear buffers
- Reduce buffer_size in apgi_gui.py

## Tips & Best Practices

### For Research

1. **Start with baseline** - Run 10-20 seconds without intervention
2. **Single variable** - Change one parameter at a time
3. **Export regularly** - Save data before major changes
4. **Document settings** - Save configurations with meaningful names

### For Demonstrations

1. **Trigger events** - Use Tools → Trigger Ignition for dramatic effect
2. **Stress response** - Induce stressor to show allostatic regulation
3. **Parameter sweep** - Smoothly vary arousal to show threshold dynamics
4. **Export data** - Export to CSV/JSON for post-analysis

### For Learning

1. **Read event log** - Follow system events chronologically
2. **Correlate plots** - Notice how ignition affects all metrics
3. **Test limits** - Max out parameters to see system boundaries
4. **Compare tabs** - Switch between views during same run

## Architecture Notes

### Threading Model

- **Main thread**: GUI updates, user interaction
- **Simulation thread**: APGI system stepping (separate)
- **Update rate**: 100ms GUI refresh, ~1ms simulation steps

### Data Flow

```text
User Input → Parameters → APGI System → State → Buffers → Plots
                                          ↓
                                    Export/Log
```

### Performance Optimization

- Plots update at 10 Hz (not every simulation step)
- Deque buffers limit memory (1000 samples)
- Canvas draw_idle() for efficient rendering
- Thread separation prevents GUI blocking

## Future Enhancements

Planned features:

- [ ] Additional visualization tabs (Self-Model, Oscillations, 3D State Space)
- [x] Full Edit menu dialogs (System Parameters, Precision Settings, Ignition Threshold)
- [x] Tools menu interventions (Trigger Ignition, Induce Stressor, Modulate Precision, Inject Input, Set Body State)
- [x] Analysis menu reports (Statistics, Energy Report, Coherence Analysis, Generate Report)
- [x] Help menu dialogs (Documentation, Shortcuts, About)
- [x] Config file I/O (Load/Save/Export CSV/JSON)
- [x] Preset task runner (Attentional Blink, Change Blindness, etc.)
- [x] Auto-save data toggle
- [x] Plot export (PNG/PDF)
- [x] Keyboard shortcuts with platform-aware bindings (Command on macOS)
- [x] System Diagnostics window (live thread/buffer/memory info)
- [x] View menu panel/tab toggles (hide/show control panel and viz tabs)
- [x] Sensory input injection with configurable amplitude and duration
- [ ] Custom task designer
- [ ] Real-time neural network visualization
- [ ] Multi-session comparison
- [ ] Automated parameter optimization
- [ ] Video export (simulation playback)
- [ ] Plugin system for extensions

## Support & Resources

- **Documentation**: See main APGI-Simulation-README.md
- **Examples**: /examples directory
- **Tests**: /tests directory
- **Configuration**: /config directory

## License

Same as main APGI System project (MIT License)

## Conclusion

Happy Modeling! 🧠✨

For questions or issues, please open a GitHub issue in the project repository.
