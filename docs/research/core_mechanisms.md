# Core Mechanisms Research Domain

This domain investigates the fundamental computational mechanisms underlying the APGI framework, focusing on threshold estimation, precision modulation, and neural validation of conscious access predictions.

## Research Questions

1. **Threshold Estimation**: How can we accurately estimate the dynamic threshold for conscious access?
2. **Precision Modulation**: How do neuromodulatory systems influence precision-weighted prediction errors?
3. **Neural Validation**: What are the neural signatures of precision-weighted surprise accumulation?
4. **Temporal Dynamics**: How do timing mechanisms support conscious access processes?

## Theoretical Background

The APGI framework proposes that conscious access emerges when precision-weighted prediction errors exceed a dynamic threshold. This domain tests the core computational mechanisms:

### Dynamic Threshold Mechanism

- Adaptive threshold based on prediction error precision
- Influence of neuromodulatory systems (noradrenaline, acetylcholine)
- Context-dependent threshold modulation

### Precision-Weighted Prediction Errors

- Hierarchical precision estimation
- Interactions between interoceptive and exteroceptive precision
- Neuromodulatory blockade effects

### Neural Signatures

- P3b amplitude as ignition marker
- Gamma synchrony for global workspace access
- ERP components for prediction error processing

## Experimental Components

### 1. Threshold Estimation System

**Location**: `experiments/threshold_estimation_system.py`

Implements adaptive procedures for estimating conscious access thresholds:

- QUEST+ algorithm for optimal stimulus selection
- Cross-modal threshold normalization
- Real-time convergence detection
- Test-retest reliability assessment

### 2. Neuromodulatory Blockade Simulation

**Location**: `experiments/neuromodulatory_blockade.py`

Tests predictions about neuromodulatory influence on conscious access:

- Beta-adrenergic blockade (propranolol) effects
- Selective P3b amplitude reduction
- Preservation of early sensory processing
- Emotional stimulus selectivity

### 3. Surprise Accumulation Dynamics

**Location**: `experiments/surprise_accumulation_dynamics.py`

Analyzes trial-by-trial neural dynamics:

- Precision-weighted surprise accumulation
- P3b amplitude tracking
- Gamma synchrony analysis
- Reaction time correlation analysis
- Prediction accuracy validation

### 4. Experimental Control System

**Location**: `experiments/` (multiple modules)

Provides comprehensive experimental infrastructure:

- Multi-modal stimulus presentation
- Real-time data acquisition
- Adaptive staircase procedures
- Synchronization with neural recording

## Key Predictions

### Threshold Estimation

- Individual thresholds can be reliably estimated
- Thresholds vary with attention and task demands
- Cross-modal normalization enables comparison

### Neuromodulatory Effects

- Propranolol selectively reduces P3b amplitude
- Early sensory ERPs remain unchanged
- Emotional stimuli show selective preservation

### Surprise Accumulation

- P3b amplitude tracks precision-weighted surprise
- Gamma synchrony correlates with ignition events
- Neural features predict conscious access accuracy

## Usage Examples

### Threshold Estimation Protocol

```python
from research.core_mechanisms.experiments.experimental.threshold_estimation_system import (
    ThresholdEstimationProtocol,
    create_default_visual_config
)

protocol = ThresholdEstimationProtocol("P001", "session_001")
protocol.initialize()
result = protocol.run_threshold_estimation(create_default_visual_config())
```

### Neuromodulatory Blockade

```python
from research.core_mechanisms.experiments.experimental.neuromodulatory_blockade import (
    NeuromodulatoryBlockadeSimulator
)

simulator = NeuromodulatoryBlockadeSimulator(random_seed=42)
result = simulator.simulate_blockade_experiment(
    n_trials_per_condition=40,
    baseline_p3b_mean=8.0
)
```

### Surprise Accumulation Analysis

```python
from research.core_mechanisms.experiments.experimental.surprise_accumulation_dynamics import (
    SurpriseAccumulationAnalyzer
)

analyzer = SurpriseAccumulationAnalyzer(apgi_equation=APGIEquation())
result = analyzer.analyze_trial_by_trial(
    erp_components=your_erp_data,
    gamma_powers=your_gamma_data,
    reaction_times=your_rt_data
)
```

## Validation Criteria

### Threshold Estimation Validation

- Convergence within 50 trials
- Test-retest reliability r > 0.8
- Cross-modal consistency

### Neuromodulatory Effects Validation

- P3b reduction 20-40%
- Early ERP preservation < 10% change
- Emotional selectivity effect d > 0.5

### Surprise Accumulation Validation

- Prediction accuracy > 0.7
- AUC-ROC > 0.7
- RT-surprise correlation |r| > 0.3

## Integration with Other Domains

### Interoceptive Gating

- Provides threshold estimation for interoceptive experiments
- Validates precision modulation predictions
- Supplies neural analysis tools

### Clinical Applications

- Enables biomarker identification
- Supports patient stratification
- Provides outcome measures

### AI Benchmarking

- Offers computational validation
- Enables cross-species comparison
- Provides performance metrics

## Technical Infrastructure

### Timing Control

- Sub-millisecond precision timing
- Hardware synchronization support
- Event marker management

### Stimulus Presentation

- Multi-modal stimulus coordination
- Adaptive parameter control
- Real-time performance monitoring

### Data Analysis

- ERP component extraction
- Gamma synchrony analysis
- Statistical validation pipelines

## Future Directions

1. **Real-time Implementation**: Online threshold adaptation during experiments
2. **Multi-modal Integration**: Combined interoceptive-exteroceptive paradigms
3. **Clinical Translation**: Biomarker development for psychiatric disorders
4. **Computational Extensions**: Enhanced precision estimation algorithms

## References

- Dehaene, S., & Changeux, J. P. (2011). Experimental and theoretical approaches to conscious processing. Neuron.
- Auksztulewicz, R., & Friston, K. (2016). Attentional enhancement of auditory cortical representations. Journal of Neuroscience.
- Parr, T., & Friston, K. (2017). The active inference constructor: A tutorial. Journal of Mathematical Psychology.
