# Hierarchical Bayesian Parameter Estimation

This module implements a complete hierarchical Bayesian modeling framework for estimating the three core APGI parameters:

- **θ₀** (theta0): Baseline ignition threshold
- **Πᵢ** (pi_i): Interoceptive precision  
- **β** (beta): Somatic bias

## Overview

The parameter estimation pipeline combines behavioral task data with multi-modal neural measurements (EEG, pupillometry, cardiac) to extract individualized parameter estimates with full uncertainty quantification.

## Core Components

### 1. Bayesian Models (`bayesian_models.py`)

#### HierarchicalBayesianModel

Main class for hierarchical Bayesian parameter estimation using Stan/PyMC3.

```python
from apgi_framework.analysis import HierarchicalBayesianModel

model = HierarchicalBayesianModel()
model.compile_model()

# Prepare data from three tasks

data = model.prepare_data(
    detection_data, heartbeat_data, oddball_data, n_subjects=10
)

# Fit model

fit_result = model.fit(data, chains=4, iter=2000)

# Extract parameters for subject 0

estimates = model.extract_parameters(
    subject_id=0,
    participant_id='P001',
    session_id='S001'
)

print(f"θ₀ = {estimates.theta0.mean:.3f} "
      f"[{estimates.theta0.credible_interval_95}]")
```json

#### SurpriseAccumulator

Implements surprise accumulation dynamics: dSₜ/dt = –Sₜ/τ + f(Πₑ·|εₑ|, β·Πᵢ·|εᵢ|)

```python
from apgi_framework.analysis import SurpriseAccumulator

accumulator = SurpriseAccumulator(tau=1.0, dt=0.001)

# Integrate surprise over time

surprise_trace = accumulator.integrate(
    pi_e, epsilon_e, pi_i, epsilon_i, beta, duration=2.0
)
```python

#### IgnitionProbabilityCalculator

Calculates ignition probability: Bₜ = σ(α(Sₜ – θₜ))

```python
from apgi_framework.analysis import IgnitionProbabilityCalculator

calculator = IgnitionProbabilityCalculator(alpha=10.0)

# Compute ignition probability

prob = calculator.compute_probability(surprise=0.8, threshold=0.5)

# Find ignition time

ignition_time = calculator.find_ignition_time(
    surprise_trace, threshold=0.5, probability_threshold=0.9
)
```python

#### StanModelCompiler

Manages Stan model compilation with caching for efficient reuse.

```python
from apgi_framework.analysis import StanModelCompiler

compiler = StanModelCompiler(cache_dir='~/.apgi_framework/stan_cache')
model = compiler.compile_stan_model(model_code)
```python

### 2. Parameter Estimation Pipeline (`parameter_estimation.py`)

#### JointParameterFitter

Fits all parameters simultaneously from behavioral and neural data.

```python
from apgi_framework.analysis import JointParameterFitter

fitter = JointParameterFitter()

results = fitter.fit_all_subjects(
    detection_data, heartbeat_data, oddball_data,
    participant_ids=['P001', 'P002', 'P003'],
    session_ids=['S001', 'S002', 'S003'],
    chains=4,
    iter=2000
)

# Check convergence

if results.convergence_diagnostics.converged:
    print("✓ Model converged successfully")
    
# Access parameter estimates

for est in results.parameter_estimates:
    print(f"{est.participant_id}: θ₀={est.theta0.mean:.3f}")
```json

#### ConvergenceDiagnosticsCalculator

Computes R-hat, effective sample size, and chain mixing diagnostics.

```python
from apgi_framework.analysis import ConvergenceDiagnosticsCalculator

calculator = ConvergenceDiagnosticsCalculator()
diagnostics = calculator.assess_convergence(fit_result)

print(f"R-hat: {diagnostics.r_hat}")
print(f"ESS: {diagnostics.effective_sample_size}")
print(f"Converged: {diagnostics.converged}")
```json

#### IndividualParameterEstimator

Estimates personalized parameters with uncertainty quantification.

```python
from apgi_framework.analysis import IndividualParameterEstimator

estimator = IndividualParameterEstimator()

estimates = estimator.estimate_parameters(
    participant_id='P001',
    session_id='S001',
    detection_data=detection_data,
    heartbeat_data=heartbeat_data,
    oddball_data=oddball_data
)

# Compute multiple credible intervals

intervals = estimator.compute_credible_intervals(
    estimates.theta0.posterior_samples,
    credibility_levels=[0.50, 0.95, 0.99]
)
```python

### 3. Parameter Recovery Validation (`parameter_recovery.py`)

#### SyntheticDataGenerator

Generates synthetic data with known ground-truth parameters.

```python
from apgi_framework.analysis import (
    SyntheticDataGenerator, 
    GroundTruthParameters
)

generator = SyntheticDataGenerator(random_seed=42)

ground_truth = GroundTruthParameters(
    theta0=0.5, pi_i=1.2, beta=1.1
)

detection, heartbeat, oddball = generator.generate_complete_dataset(
    ground_truth, noise_level=0.1
)
```python

#### ParameterRecoveryValidator

Validates pipeline through simulation of 100 synthetic datasets.

```python
from apgi_framework.analysis import ParameterRecoveryValidator

validator = ParameterRecoveryValidator(
    validation_criteria={
        'theta0': 0.85,  # r > 0.85
        'pi_i': 0.75,    # r > 0.75
        'beta': 0.85     # r > 0.85
    }
)

results = validator.run_validation(
    n_datasets=100,
    noise_level=0.1,
    chains=4,
    iter=1000
)

if results.passed:
    print("✓ Parameter recovery validation PASSED")
else:
    print("✗ Parameter recovery validation FAILED")
```json

#### RecoveryAnalyzer

Analyzes recovery with correlation metrics and bias assessment.

```python
from apgi_framework.analysis import RecoveryAnalyzer

analyzer = RecoveryAnalyzer()

metrics = analyzer.analyze_recovery(
    ground_truth_list, recovered_list
)

for param, metric in metrics.items():
    print(f"{param}: r={metric.correlation:.3f}, "
          f"bias={metric.bias:.3f}")

# Generate recovery plots

analyzer.plot_recovery(
    ground_truth_list, recovered_list,
    save_path='recovery_plots.png'
)
```python

#### ValidationReportGenerator

Generates comprehensive validation reports.

```python
from apgi_framework.analysis import ValidationReportGenerator

report = ValidationReportGenerator.generate_report(
    recovery_results,
    output_path='validation_report.txt'
)

print(report)
```python

### 4. Predictive Validity Testing (`predictive_validity.py`)

#### EmotionalInterferenceTask

Emotional Stroop/flanker task for Πᵢ validation.

```python
from apgi_framework.analysis import EmotionalInterferenceTask

task = EmotionalInterferenceTask(task_type='stroop')

performance = task.run_task('P001', n_trials=120)

# Predict from Πᵢ

predicted_interference = task.predict_from_pi_i(
    pi_i=1.2, baseline_interference=100.0
)
```python

#### ContinuousPerformanceTask

CPT for θ₀ validation and attentional lapse prediction.

```python
from apgi_framework.analysis import ContinuousPerformanceTask

task = ContinuousPerformanceTask(duration_minutes=10)

performance = task.run_task('P001')

# Predict from θ₀

predicted_lapses = task.predict_from_theta0(
    theta0=0.5, baseline_lapse_rate=0.05
)
```python

#### BodyVigilanceScaleAnalyzer

BVS analyzer for β validation through somatic symptom correlation.

```python
from apgi_framework.analysis import BodyVigilanceScaleAnalyzer

analyzer = BodyVigilanceScaleAnalyzer()

responses = analyzer.collect_questionnaire('P001')
bvs_score = analyzer.compute_bvs_score(responses)

# Predict from β

predicted_bvs = analyzer.predict_from_beta(beta=1.1)
```sql

#### PredictivePowerComparator

Compares APGI parameters against traditional measures.

```python
from apgi_framework.analysis import PredictivePowerComparator

comparator = PredictivePowerComparator()

# Test predictive validity

validity_result = comparator.test_predictive_validity(
    parameter_estimates, task_performance,
    parameter_name='pi_i',
    performance_metric='interference_effect'
)

print(f"r = {validity_result.correlation:.3f}, "
      f"p = {validity_result.p_value:.4f}")

# Compare to traditional measures

comparison = comparator.compare_to_traditional_measures(
    apgi_parameter, traditional_measure, outcome,
    apgi_name='Πᵢ', traditional_name='Trait Anxiety'
)

if comparison.apgi_better:
    print(f"APGI parameter outperforms by "
          f"{comparison.improvement_percentage:.1f}%")
```json

#### PredictiveValidityFramework

Complete framework for testing predictive validity.

```python
from apgi_framework.analysis import PredictiveValidityFramework

framework = PredictiveValidityFramework()

validity_results = framework.run_complete_validation(
    parameter_estimates, collect_behavioral_data=True
)

report = framework.generate_validity_report(
    validity_results, comparative_results
)

print(report)
```python

## Data Requirements

### Detection Task Data

```python
detection_data = {
    'subject_id': np.array([...]),        # Subject indices (1-based)
    'stimulus_intensity': np.array([...]), # Stimulus intensities
    'detected': np.array([...]),          # Binary detection responses
    'p3b_amplitude': np.array([...])      # P3b amplitudes (250-500ms at Pz)
}
```

### Heartbeat Detection Task Data

```python
heartbeat_data = {
    'subject_id': np.array([...]),        # Subject indices
    'synchronous': np.array([...]),       # Binary: tone sync with heartbeat
    'response_sync': np.array([...]),     # Binary: participant response
    'confidence': np.array([...]),        # Confidence ratings (0-1)
    'hep_amplitude': np.array([...]),     # HEP amplitudes (250-400ms)
    'pupil_response': np.array([...])     # Pupil dilation (200-500ms)
}
```

### Oddball Task Data

```python
oddball_data = {
    'subject_id': np.array([...]),        # Subject indices
    'trial_type': np.array([...]),        # 0=standard, 1=intero, 2=extero
    'p3b_intero': np.array([...]),        # P3b to interoceptive deviants
    'p3b_extero': np.array([...])         # P3b to exteroceptive deviants
}
```

## Installation Requirements

```bash

# Core dependencies

pip install numpy scipy pandas matplotlib

# Bayesian modeling (required for parameter estimation)

pip install pystan

# For GPU acceleration (optional)

pip install pystan-cuda

# Alternative: PyMC3

pip install pymc3
```bash

## Workflow

### 1. Parameter Recovery Validation (Required First)

```python
from apgi_framework.analysis import ParameterRecoveryValidator

validator = ParameterRecoveryValidator()
results = validator.run_validation(n_datasets=100)

if not results.passed:
    print("Warning: Parameter recovery failed. Refine pipeline before "
          "collecting empirical data.")
```json

### 2. Empirical Parameter Estimation

```python
from apgi_framework.analysis import JointParameterFitter

fitter = JointParameterFitter()
results = fitter.fit_all_subjects(
    detection_data, heartbeat_data, oddball_data,
    participant_ids=participant_ids,
    session_ids=session_ids
)

# Save results

for est in results.parameter_estimates:
    save_to_database(est)
```python

### 3. Predictive Validity Testing

```python
from apgi_framework.analysis import PredictiveValidityFramework

framework = PredictiveValidityFramework()
validity_results = framework.run_complete_validation(
    results.parameter_estimates
)

report = framework.generate_validity_report(validity_results)
```python

## Performance Considerations

- **Model compilation**: First compilation takes ~1-2 minutes, then cached
- **Parameter estimation**: ~5-10 minutes per subject (4 chains, 2000 iterations)
- **Parameter recovery**: ~8-16 hours for 100 datasets
- **Memory usage**: ~2-4 GB for typical datasets

## Validation Criteria

### Parameter Recovery

- θ₀: Pearson r > 0.85
- Πᵢ: Pearson r > 0.75
- β: Pearson r > 0.85
- 95% CI coverage > 90%

### Convergence

- R-hat < 1.01 for all parameters
- Effective sample size > 400
- No divergent transitions

### Predictive Validity

- Significant correlations (p < 0.05) with independent measures
- Outperform traditional measures (trait anxiety, EEG ratios)

## Troubleshooting

### Model doesn't converge

- Increase iterations: `iter=4000`
- Increase warmup: `warmup=2000`
- Check data quality and outliers
- Verify model identifiability

### Poor parameter recovery

- Increase number of trials per task
- Reduce noise in neural measurements
- Check for systematic biases in data generation
- Verify model specification

### Low predictive validity

- Ensure sufficient sample size (n > 30)
- Check for range restriction in parameters
- Verify independent task reliability
- Consider moderating variables

## References

See `example_bayesian_parameter_estimation.py` for complete working examples.

## Support

For issues or questions, refer to the main APGI Framework documentation.
