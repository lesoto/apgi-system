# Virtual Metabolic Layer (VML)

## Overview

The Virtual Metabolic Layer provides biophysically-grounded ATP flux estimation for the APGI system using Neural Mass Models (NMMs). It replaces order-of-magnitude κ (kappa) estimates with detailed calculations based on glutamate recycling costs, ion pumping requirements, and neural population dynamics.

## Key Components

### 1. Neural Mass Model (Jansen-Rit Inspired)

The `NeuralMassModel` class implements a Jansen-Rit type model to estimate population-level firing rates:

- **Pyramidal cells**: Main excitatory output population
- **Excitatory interneurons**: Local excitatory connections
- **Inhibitory interneurons**: Feedback inhibition

State variables track postsynaptic potentials (PSPs) and their derivatives:

- `y[0-1]`: Excitatory PSP at pyramidal cells
- `y[2-3]`: Inhibitory PSP at pyramidal cells
- `y[4-5]`: Excitatory PSP at interneurons
- `y[6-7]`: Inhibitory PSP at interneurons

### 2. ATP Flux Calculator

The `ATPFluxCalculator` computes metabolic costs:

**ATP Components:**

- **Glutamate recycling**: ~20,000 ATP per vesicle cycle
- **Na+/K+ pumping**: Restoration of ion gradients after action potentials
- **Ca2+ pumping**: Restoration of calcium gradients
- **Baseline metabolism**: ~10^9 ATP/s per neuron at rest
- **Propagation costs**: Action potential propagation along axons

**Key Equation:**

```text
ATP_total = ATP_glutamate + ATP_NaK + ATP_Ca + ATP_baseline + ATP_propagation
```

### 3. Kappa (κ) Computation

The κ value represents metabolic cost per bit of information, normalized by the Landauer limit:

```text
κ = ATP_total / (bits × kT × ln(2))
```

Where:

- `ATP_total`: Total ATP molecules consumed
- `bits`: Information content of the broadcast
- `kT ln(2)`: Landauer limit (~0.018 eV at 37°C)

For biological systems, κ is typically ~10^6 to 10^7 (millions of times the theoretical minimum).

### 4. Integrated Metabolic System

The `IntegratedMetabolicSystem` connects the VML with existing APGI components:

- Combines with `MetabolicBudget` for energy tracking
- Provides dynamic κ values during ignition events
- Tracks ignition cost history for statistical analysis

## Usage

### Quick κ Estimation

```python
from apgi_framework.thermodynamic import estimate_kappa_for_ignition
import numpy as np

kappa = estimate_kappa_for_ignition(
    ignition_signal=3.5,  # S_t
    threshold=2.0,        # θ_t
    workspace_content=np.random.randn(256),
    ignition_duration_ms=300.0,
)
print(f"κ = {kappa:.2e}")  # Output: ~10^13
```

### Full Virtual Metabolic Layer

```python
from apgi_framework.thermodynamic import VirtualMetabolicLayer

# Create layer
vml = VirtualMetabolicLayer()

# Simulate pre-ignition activity
vml.simulate_neural_activity(input_drive=0.3, duration_ms=100.0)

# Compute ignition cost
ignition_cost = vml.compute_ignition_cost(
    ignition_signal=3.5,
    threshold=2.0,
    workspace_content=workspace_vector,
    ignition_duration_ms=300.0,
)

print(f"κ = {ignition_cost['kappa_landauer']:.2e}")
print(f"ATP total = {ignition_cost['atp_total']:.2e}")
```

### Integrated System

```python
from apgi_framework.thermodynamic import IntegratedMetabolicSystem

# Configuration
config = {
    "thermodynamic": {
        "total_energy_budget": 100.0,
        "use_dynamic_kappa": True,  # Enable NMM-based κ
        "workspace_neurons": 100_000,
    }
}

# Create system
system = IntegratedMetabolicSystem(config)

# Update during simulation loop
result = system.update(
    ignition_occurred=True,
    ignition_signal=3.0,
    threshold=2.0,
    workspace_content=content_vector,
    task_active=True,
    dt_ms=1.0,
)

kappa = result["current_kappa"]
reserves = result["reserve_fraction"]
```

### Factory Function

```python
from apgi_framework.thermodynamic import create_metabolic_system_with_vml

# Quick setup
system = create_metabolic_system_with_vml(
    workspace_neurons=150_000,
    use_dynamic_kappa=True,
    config_overrides={
        "thermodynamic": {"total_energy_budget": 150.0},
    },
)
```

## Biological Basis

### Energy Budget References

1. **Attwell & Laughlin (2001)**: Energy budget for signaling in grey matter
   - Action potentials: ~10^7 ATP per spike
   - Synaptic transmission: ~2×10^4 ATP per vesicle
   - Resting metabolism: ~10^9 ATP/s per neuron

2. **Lennie (2003)**: Cost of cortical computation
   - Brain consumes ~20% of body's energy budget
   - Most energy goes to synaptic transmission and Na+/K+ pumping

3. **Howarth et al. (2012)**: Updated energy budgets
   - Astrocytes contribute ~20% via lactate shuttle
   - Glutamate recycling is metabolically expensive

### Neural Mass Model Parameters

Default values represent a canonical cortical column:

- **Neurons**: ~10^5 per column
- **Synapses**: ~10^7 per column
- **Excitatory fraction**: 80% (pyramidal cells)
- **Time constants**: τ_e = 10 ms, τ_i = 20 ms

## Integration with APGI

### Threshold Modulation

The metabolic state (reserves, allostatic load) modulates the ignition threshold:

```python
# In IgnitionThreshold._update_threshold()
c_metabolic = 2.0 * (1.0 - metabolic_reserves)
delta_theta = eta * (c_metabolic - v_information + allostatic_penalty)
```

With the VML, this becomes:

```python
# Using actual ATP-based reserves
reserves = ignition_cost['atp_total'] / max_budget
c_metabolic = 2.0 * (1.0 - reserves)
```

### Metabolic Budget Integration

The `IntegratedMetabolicSystem` updates both:

1. Traditional `MetabolicBudget` (simplified energy units)
2. VML-based ATP tracking (biophysical units)

This allows backward compatibility while providing more accurate κ values.

## Example: Ignition Cost Breakdown

For a typical Global Ignition event:

```text
Ignition Signal: 3.5
Threshold: 2.0
Signal Excess: 1.5
Workspace Content: 256 dimensions
Duration: 300 ms

ATP Cost Breakdown:
- Glutamate recycling: 1.20e+16 ATP (33%)
- Na+/K+ pumping: 1.80e+16 ATP (50%)
- Ca2+ pumping: 1.80e+14 ATP (0.5%)
- Baseline: 3.00e+15 ATP (8%)
- Propagation: 3.00e+15 ATP (8%)
- Total: 3.60e+16 ATP

Information Metrics:
- Bits broadcast: ~128-256
- Vesicles released: ~3×10^5

κ = 2.56×10^13 (~25 million × Landauer limit)
```

## API Reference

### Classes

#### `NeuralMassParameters`

Configuration for the neural mass model.

**Key Parameters:**

- `excitatory_time_constant_ms`: τ_e (default: 10.0)
- `inhibitory_time_constant_ms`: τ_i (default: 20.0)
- `synaptic_gain_excitatory`: A (default: 3.25)
- `synaptic_gain_inhibitory`: B (default: 22.0)
- `num_neurons`: Population size (default: 100,000)
- `num_synapses`: Synapse count (default: 10,000,000)

#### `MetabolicCostFactors`

ATP cost factors for neural computation.

**Key Factors:**

- `atp_per_glutamate_cycle`: ~20,000 ATP per vesicle
- `resting_atp_per_neuron_s`: ~10^9 ATP/s per neuron
- `astrocyte_lactate_factor`: 1.2 (20% astrocyte contribution)

#### `NeuralMassModel`

Neural mass dynamics simulation.

**Methods:**

- `step(input_current, dt_ms)`: Advance simulation
- `sigmoid(v)`: Firing rate function
- `get_average_firing_rates(window_ms)`: Recent firing rates
- `reset()`: Reset state

#### `ATPFluxCalculator`

ATP consumption calculation.

**Methods:**

- `compute_atp_flux(...)`: ATP flux components
- `compute_ignition_cost(...)`: Total ignition cost
- `compute_kappa(atp_total, bits, consider_landauer)`: κ value
- `get_summary_stats()`: Statistics

#### `VirtualMetabolicLayer`

Main interface combining NMM and ATP calculation.

**Methods:**

- `simulate_neural_activity(input_drive, duration_ms)`: Run simulation
- `compute_ignition_cost(signal, threshold, content, duration)`: Ignition cost
- `get_dynamic_kappa(use_recent_average)`: Current κ value
- `get_metabolic_state()`: State summary
- `reset()`: Reset all state

#### `IntegratedMetabolicSystem`

Integration with APGI metabolic budget.

**Methods:**

- `update(ignition_occurred, ignition_signal, threshold, ...)`: Main update
- `get_current_kappa(use_recent_average)`: Current κ
- `compute_ignition_cost_estimate(...)`: Cost prediction
- `get_metabolic_summary()`: Full summary

#### `MetabolicIgnitionAdapter`

Adapter for IgnitionThreshold integration.

**Methods:**

- `update(ignition_signal, threshold, ignition_occurred, ...)`: Coordinated update
- `get_kappa_for_cost_update()`: κ for cost calculations
- `estimate_future_cost(...)`: Predictive cost estimation

### Convenience Functions

#### `estimate_kappa_for_ignition(...)`

Quick one-off κ estimation without maintaining state.

#### `create_metabolic_system_with_vml(...)`

Factory function for quick system setup.

## Testing

Run the test suite:

```bash
pytest tests/unit/test_virtual_metabolic_layer.py -v
```

Run the demo:

```bash
python examples/virtual_metabolic_layer_demo.py
```

## Performance Considerations

- **Neural Mass Simulation**: ~1ms per 100 timesteps (Python/NumPy)
- **ATP Calculation**: ~0.1ms per computation
- **Memory**: ~1MB for full history (1000 samples)

For production use with many agents:

- Consider vectorized batch processing
- Use pre-computed κ tables for common conditions
- Cache ignition cost estimates

## Future Enhancements

1. **Multi-population models**: Multiple interacting cortical columns
2. **Frequency-dependent costs**: Different ATP costs for gamma vs. beta oscillations
3. **Pathological conditions**: Adjusted costs for epilepsy, anesthesia
4. **Temperature effects**: Q10 corrections for hypothermia/hyperthermia
5. **Developmental scaling**: Age-dependent metabolic parameters

## References

- Jansen, B. H., & Rit, V. G. (1995). Electroencephalogram and visual evoked potential generation in a mathematical model of coupled cortical columns.
- Attwell, D., & Laughlin, S. B. (2001). An energy budget for signaling in the grey matter of the brain.
- Lennie, P. (2003). The cost of cortical computation.
- Howarth, C., Gleeson, P., & Attwell, D. (2012). Updated energy budgets for neural computation in the neocortex.
