# Experimental Tasks Documentation

This directory contains experimental paradigms for testing the APGI consciousness model.

## Available Tasks

### 1. Attentional Blink Task (`attentional_blink.py`)

**Purpose**: Tests temporal limits of conscious perception and attentional gating.

**Description**:

The attentional blink paradigm demonstrates that when two targets are presented in rapid succession (within 200-500ms), the second target is often not consciously perceived. This tests the temporal resolution of conscious access and the refractory period of the global workspace.

**Parameters**:

- `stimulus_duration_ms`: Duration of each stimulus (default: 50ms)
- `inter_stimulus_interval_ms`: Interval between stimuli (default: 200ms)
- `target_probability`: Probability of target vs distractor (default: 0.3)
- `num_trials`: Number of experimental trials (default: 100)

**Expected Behavior**:

- High ignition rates for first target
- Reduced ignition probability for second target during blink period
- Increased free energy during attentional demands
- Elevated precision weighting during target detection

**Neural Correlates**:

- P3 ERP component modulation
- Parietal activation patterns
- Frontal attention network engagement

---

### 2. Binocular Rivalry Task (`binocular_rivalry.py`)

**Purpose**: Investigates spontaneous perceptual alternations and competition between conscious representations.

**Description**:

When different images are presented to each eye, perception alternates between them rather than fusing. This tests the stability of conscious representations and the dynamics of perceptual competition in the global workspace.

**Parameters**:

- `left_image_pattern`: Pattern for left eye stimulus (default: "grating")
- `right_image_pattern`: Pattern for right eye stimulus (default: "grating")
- `contrast_level`: Stimulus contrast (default: 0.8)
- `switch_threshold`: Threshold for perceptual switching (default: 0.6)
- `observation_duration_s`: Duration of each observation period (default: 30s)

**Expected Behavior**:

- Spontaneous alternations between perceptual states
- Competition dynamics in workspace broadcasting
- Variable ignition rates during perceptual switches
- Precision fluctuations during perceptual uncertainty

**Neural Correlates**:

- Frontoparietal network oscillations
- Gamma band activity during perceptual switches
- Inter-hemispheric competition patterns

---

### 3. Change Blindness Task (`change_blindness.py`)

**Purpose**: Examines change detection limitations and the role of attention in conscious perception.

**Description**:

Demonstrates that large changes in a visual scene can go unnoticed when attention is directed elsewhere. This tests the capacity of the global workspace to detect salient changes without focused attention.

**Parameters**:

- `scene_complexity`: Number of elements in scene (default: 10)
- `change_magnitude`: Size of visual change (default: 0.7)
- `distractor_load`: Number of distractor elements (default: 5)
- `change_duration_ms`: Duration of change event (default: 200ms)
- `attentional_load`: Cognitive load during task (default: 0.5)

**Expected Behavior**:

- Failed ignition events during unattended changes
- Successful detection with focused attention
- Increased free energy during change detection
- Precision modulation with attentional load

**Neural Correlates**:

- Parietal lobe activation patterns
- Ventral visual stream processing
- Attentional network modulation

---

### 4. Iowa Gambling Task (`iowa_gambling.py`)

**Purpose**: Assesses decision-making under uncertainty and somatic marker learning.

**Description**:

Participants choose from decks of cards with different reward/punishment schedules. This tests the integration of interoceptive signals (somatic markers) with decision-making and the learning of value associations.

**Parameters**:

- `deck_reward_schedules`: Reward probabilities for each deck (default: [0.7, 0.7, 0.3, 0.3])
- `punishment_magnitude`: Loss amount for bad decks (default: -50)
- `reward_magnitude`: Gain amount for good decks (default: 100)
- `selection_timeout_ms`: Time for decision (default: 3000ms)
- `num_trials`: Total trials in experiment (default: 100)

**Expected Behavior**:

- Learning of advantageous deck preferences
- Somatic marker development for good/bad choices
- Increased ignition events during decision points
- Coherence fluctuations during uncertainty

**Neural Correlates**:

- Ventromedial prefrontal cortex activity
- Insula activation (interoception)
- Striatal reward processing
- Somatic marker system engagement

---

### 5. Masking Paradigm Task (`masking_paradigm.py`)

**Purpose**: Investigates temporal limits of conscious processing and backward masking effects.

**Description**:

A mask stimulus presented shortly after a target can prevent conscious perception of the target. This tests the temporal integration window of the global workspace and the susceptibility of conscious access to interference.

**Parameters**:

- `target_duration_ms`: Duration of target stimulus (default: 30ms)
- `mask_duration_ms`: Duration of mask stimulus (default: 50ms)
- `stimulus_onset_asynchrony_ms`: Delay between target and mask (default: 50ms)
- `mask_intensity`: Strength of masking stimulus (default: 0.8)
- `target_contrast`: Visibility of target (default: 0.6)

**Expected Behavior**:

- Reduced target detection with short SOA
- Increased ignition failures during backward masking
- Elevated precision during successful detection
- Free energy accumulation during failed perception

**Neural Correlates**:

- Early visual cortex (V1/V2) modulation
- Temporal cortex processing
- Attentional gating mechanisms

---

## Task Implementation Framework

### Base Class Structure

All experimental tasks inherit from `ExperimentalTask` base class:

```python
class ExperimentalTask:
    def __init__(self, apgi_simulation, config):
        self.system = apgi_simulation
        self.config = config
        
    def setup(self):
        """Initialize task parameters and system state."""
        pass
        
    def run_trial(self, trial_params):
        """Execute a single trial of the experiment."""
        pass
        
    def cleanup(self):
        """Reset system state after task completion."""
        pass
```

### Required Methods

Each task must implement:

1. **`setup()`**: Initialize the experimental paradigm
2. **`run_trial()`**: Execute individual trials with parameter validation
3. **`cleanup()`**: Reset system to baseline state
4. **`get_results()`**: Return trial-by-trial performance data

### Data Collection

All tasks automatically collect:

- **Ignition Events**: Timestamp and strength of each ignition
- **System State**: Free energy, precision, metabolic reserves
- **Performance Metrics**: Accuracy, reaction times, choices
- **Physiological Markers**: Heart rate, cortisol, allostatic load
- **Temporal Dynamics**: Time series of all system variables

## Integration with APGI System

### System Interactions

Tasks interact with APGI components:

1. **Global Workspace**: Broadcast task-relevant information
2. **Precision Weighting**: Modulate sensory reliability
3. **Somatic Markers**: Store action-outcome associations
4. **Metabolic System**: Track energy consumption
5. **Self-Model**: Maintain coherence during task performance

### Configuration Format

Tasks use standardized YAML configuration:

```yaml
task_name: "attentional_blink"
parameters:
  stimulus_duration_ms: 50
  inter_stimulus_interval_ms: 200
  target_probability: 0.3
  num_trials: 100
system_settings:
  initial_precision: 1.0
  metabolic_reserve_level: 1.0
  coherence_threshold: 0.7
data_collection:
  record_ignition_events: true
  record_system_state: true
  save_time_series: true
```

## Running Experiments

### Command Line Interface

```bash
# Run single task
python -m apgi_simulation.experiments.tasks.attentional_blink --config config.yaml

# Run with custom parameters
python -m apgi_simulation.experiments.tasks.iowa_gambling --trials 200 --decks 4

# Batch experiments
python -m apgi_simulation.experiments.run_batch --tasks all --output results/
```

### GUI Integration

Tasks can be launched from the APGI GUI:

1. **Simulation Menu → Run Preset Task**
2. Select desired task from dropdown
3. Configure parameters in dialog
4. Click "Start Task"
5. Monitor real-time results in analysis tabs

## Data Analysis

### Output Formats

Each task generates standardized output:

1. **CSV Files**: Trial-by-trial data with timestamps
2. **JSON Files**: Complete system state snapshots
3. **HDF5 Files**: Large datasets with hierarchical organization
4. **Plots**: Automatic generation of performance graphs

### Analysis Scripts

Standard analysis scripts are provided:

- `analyze_performance.py`: Statistical analysis of task results
- `compare_tasks.py`: Cross-task performance comparisons
- `generate_report.py`: Comprehensive experimental reports

## Best Practices

### Task Design

1. **Clear Hypotheses**: Each task should test specific predictions
2. **Parametric Flexibility**: Allow parameter adjustment for exploration
3. **Baseline Conditions**: Include control conditions for comparison
4. **Multiple Trials**: Ensure statistical reliability
5. **Randomization**: Counterbalance order effects

### System Integration

1. **Minimal Interference**: Tasks should not disrupt core system dynamics
2. **State Monitoring**: Track all relevant system variables
3. **Error Handling**: Graceful recovery from unexpected states
4. **Resource Management**: Monitor memory and computational load
5. **Data Validation**: Ensure data integrity and completeness

### Documentation Standards

1. **Parameter Descriptions**: Clear explanation of all parameters
2. **Expected Behavior**: Predictions for system responses
3. **Neural Correlates**: Relevant brain activity patterns
4. **Usage Examples**: Practical implementation guidance
5. **Troubleshooting**: Common issues and solutions

## Contributing New Tasks

When adding new experimental tasks:

1. **Inherit from Base Class**: Use `ExperimentalTask` framework
2. **Follow Naming Conventions**: Snake_case for files, CamelCase for classes
3. **Add Documentation**: Include comprehensive task description
4. **Implement Tests**: Unit tests for task functionality
5. **Update Registry**: Add task to task registry system
6. **Version Control**: Track changes and improvements

## References

Key papers for each paradigm:

- **Attentional Blink**: Raymond, Shapiro, & Arnell (1992)
- **Binocular Rivalry**: Blake & Logothetis (2002)  
- **Change Blindness**: Rensink, O'Regan, & Clark (1997)
- **Iowa Gambling**: Bechara et al. (1994)
- **Masking**: Macknik & Livingstone (1998)

These experimental paradigms provide rigorous tests of the APGI model's predictions about conscious access, attentional gating, and the integration of interoceptive signals with cognitive processing.
