# APGI Framework Parameter Estimation Pipeline

The APGI Framework enables rapid, individualized quantification of key computational parameters—baseline ignition threshold (θ₀), interoceptive precision (Πᵢ), and somatic bias (β)—using a standardized 45–60 minute protocol combining behavioral tasks, high-density EEG (128+ channels), and pupillometry. All tasks are adaptive, computerized, and optimized for clinical feasibility.

## Extraction of Core APGI Parameters from EEG and Behavior (<1 Hour)

### Baseline Ignition Threshold (θ₀)

Task:
Adaptive visual/auditory detection staircase (200 trials, ~10 min).

Stimuli:
Gabor patches or tones are presented at varying intensities; participants press a button only if they consciously perceived the stimulus.

EEG Marker:
P3b amplitude (250–500 ms at Pz).

Estimation:
The stimulus intensity yielding 50% “seen” responses is the behavioral ignition threshold. A lower stimulus intensity at the 50% detection point indicates a lower θ₀, and vice versa.

Validation:
Lower θ₀ correlates with higher resting P3b to suprathreshold standards (r > 0.5).

### Interoceptive Precision (Πᵢ)

Task:
Heartbeat detection task with trial-by-trial confidence ratings (60 trials, ~8 min).

Participants report whether an auditory tone is synchronized with their heartbeat; tones are either synchronous or asynchronous.

Physiological Proxy:
High-speed pupillometry (1000 Hz) during trials.

EEG Marker:
Heartbeat-evoked potential (HEP; 250–400 ms post-R-peak) and interoceptive P3b to synchronous tones.

Estimation:
Πᵢ is derived from d′ in heartbeat detection. Trial-level Πᵢ is modeled as a gain factor on interoceptive prediction errors, fitted via hierarchical Bayesian model inversion using HEP amplitude and pupil dilation (200–500 ms post-stimulus) as neural priors.

### Somatic Bias (β)

Task:
Dual-modality oddball with matched-precision stimuli (120 trials, ~12 min).
Interoceptive deviants: Brief CO₂ puffs (non-painful, 10% CO₂) or heartbeat-synchronized flashes.

Exteroceptive deviants:
Rare visual Gabor orientations.
Stimulus intensities are pre-calibrated so that Πₑ ≈ Πᵢ (via separate staircase procedures).

EEG Marker:
P3b amplitude to interoceptive vs. exteroceptive deviants.

Estimation:
β = (P3b_interoceptive / P3b_exteroceptive) under neutral context. This ratio approximates β because Πₑ ≈ Πᵢ by design, isolating the weighting term.

## Model Fitting, Validation & Practical Implementation

### Model Fitting & Output

All behavioral and neural data are jointly fit within a hierarchical Bayesian framework (Stan/PyMC3). The model incorporates:

Surprise accumulation:
dSₜ/dt = –Sₜ/τ + f(Πₑ·|εₑ|, β·Πᵢ·|εᵢ|)

Ignition probability:
Bₜ = σ(α(Sₜ – θₜ))

Output: Individualized θ₀, Πᵢ, and β estimates with 95% credible intervals.
Reliability: Test–retest ICC > 0.75 over 1 week (validated in pilot N = 40).

### Parameter Recovery Study (In Silico Validation)

Before collecting empirical data, we will conduct a comprehensive parameter recovery analysis to validate the entire computational pipeline. We will simulate 100 synthetic datasets with known ground-truth parameters, incorporating realistic trial-by-trial noise and physiological artifacts that match the characteristics of our EEG and pupillometry setup. The pipeline will be deemed validated only if it demonstrates high-fidelity recovery of all core parameters, with Pearson correlations between true and recovered values exceeding r > 0.85 for the ignition threshold (θ₀) and metacognitive sensitivity (β), and r > 0.75 for interoceptive precision (Πᵢ) across the simulated cohort. This step is non-negotiable: it establishes that the assay can, in principle, distinguish distinct computational phenotypes before exposure to real-world noise and confounds.

### Predictive Validity on Independent Tasks

The clinical utility of the APGI parameters depends on their capacity to predict behavior on tasks independent of those used for parameter estimation. We pre-register the following specific predictions. First, elevated Πᵢ will predict greater performance disruption—manifested as slower reaction times and more errors—on a standardized emotional interference task (e.g., emotional Stroop or flanker), outperforming traditional trait anxiety measures in predictive accuracy. Second, elevated θ₀ will predict more attentional lapses (missed targets) and higher intra-individual variability in reaction time on a graded Continuous Performance Task (CPT), surpassing the predictive power of baseline EEG theta/beta ratio. Third, the fitted β parameter will show a stronger correlation with validated questionnaires assessing somatic symptom focus (e.g., the Body Vigilance Scale) than raw heartbeat detection accuracy (d′) alone.

### Addressing Practical Hurdles

Several methodological challenges are anticipated, and targeted strategies are in place to address them. For participants with consistently poor heartbeat perception (d′ < 0.5), we will implement an adaptive staircase procedure that dynamically adjusts the asynchrony window between cardiac and external stimuli to maintain a ~75% correct response rate. This ensures a measurable behavioral signal, and Πᵢ will be estimated from both the required asynchrony threshold and the associated neural responses (HEP amplitude and pupil dilation), yielding a “neural accuracy” measure even when behavioral performance is at floor. To preserve EEG signal quality during respiratory interventions (e.g., CO₂ puffs), we will minimize motion artifacts by using a bite bar or chin rest, employ brief and standardized puff durations (<500 ms), and apply a robust artifact rejection pipeline (e.g., the FASTER algorithm), analyzing only trials free of movement-related amplitude excursions. Finally, to control for metacognitive biases in subjective reports of conscious perception, we will standardize response criteria across participants using an instructional video with clear examples of “seen” versus “guessed” responses, include a post-task confidence calibration check, and explicitly model individual differences in response criterion within the hierarchical Bayesian fitting procedure.
