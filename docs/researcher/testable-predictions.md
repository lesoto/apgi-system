# APGI Framework — Testable Predictions

Testable Predictions: Empirical Validation Roadmap

To guard against post-hoc rationalization, the APGI framework establishes a priori evidential standards that define what constitutes strong support, weak support, or falsification of its core predictions. These criteria apply uniformly across empirical domains and are grounded in effect size, statistical significance, and replicability. These standards anchor the APGI framework’s commitment to empirical rigor and ensure that its specific, falsifiable predictions—spanning neural dynamics, neuromodulation, and behavioral correlates—can be objectively evaluated. The following section presents a comprehensive and prioritized list of such empirical tests.

Strong support requires that the observed effect exceeds the predicted magnitude, achieves statistical significance at p < 0.01, and is replicated in at least two independent laboratories. Moderate support is assigned when the effect aligns with the predicted direction and falls within the expected range, reaches p < 0.05, but is reported by a single lab. Weak support applies when the effect is in the predicted direction yet smaller than anticipated, with p < 0.05, but requires independent replication to be considered reliable. Findings showing no significant deviation from zero (p > 0.05) or effects in the opposite direction (p < 0.05) are classified as providing no support. Falsification occurs if an effect is significantly opposite to the prediction (p < 0.01) or if a critical mechanistic component is absent despite adequate statistical power to detect it.

Priority 1: Direct Threshold Estimation (Highest Priority)

Prediction 1.1: Psychophysical Threshold Estimation Predicts Neural and Clinical Outcomes

Hypothesis:
The ignition threshold (θₜ) is the central parameter of the APGI framework, yet no current method directly estimates it. All existing evidence is indirect—inferring θₜ from P3b amplitude, detection rates, or similar proxies. A direct psychophysical measurement would provide the strongest possible validation of θₜ as a biologically real and behaviorally meaningful construct.

Method:

Task Design:
Adaptive staircase procedure presenting stimuli at varying intensities across multiple modalities (visual, auditory, interoceptive).
Each trial: Stimulus → 50–500 ms delay → Subjective awareness probe (“Did you consciously perceive the stimulus?”).
Stimulus intensity and contextual factors (threat, uncertainty, cognitive load) are systematically varied.

Threshold Estimation:

For each condition, estimate the stimulus intensity that yields 50% conscious detection—the “ignition threshold” in stimulus space.
Across modalities, compute a normalized threshold relative to the sensory detection threshold (reflecting unconscious processing).
This normalized threshold serves as a behavioral proxy for θₜ in the model.

Neural Validation:

Simultaneous EEG recordings during threshold estimation.
On threshold trials: Stochastic P3b should appear on ~50% of trials.
On subthreshold trials (intensity < threshold): No P3b, reduced gamma-band activity, but preserved early ERPs.
On suprathreshold trials (intensity > threshold): Reliable P3b and sustained gamma activity.

Predictions:

Within-Subject Stability:

Estimated θₜ should demonstrate high test–retest reliability across sessions (ICC > 0.70 over a 1-week interval).
Stability is a necessary condition for θₜ to function as a meaningful trait-like parameter.

Cross-Modal Consistency: θₜ estimates derived from visual, auditory, and interoceptive modalities should correlate significantly (r > 0.5), supporting its status as a domain-general parameter rather than a modality-specific one.

Neural Correspondence: Lower estimated θₜ should predict:
Higher baseline P3b amplitude to suprathreshold stimuli (r > 0.5)
Higher resting gamma power in frontoparietal regions (r > 0.4)
Lower pre-stimulus alpha power (indicating reduced inhibitory tone) (r > –0.4)

Falsification:

Failure of 1 or 2: θₜ may not be a stable, domain-general parameter → requires reformulation as modality-specific thresholds
Failure of 3: The link between behavioral threshold and neural signatures is weaker than claimed → model needs revision
Failure of 4: Neuromodulatory implementation is incorrect → κ coefficients and θ₀ equation require reformulation
Failure of 5: Clinical profiles are not θₜ-mediated → disorders involve other parameters or non-APGI mechanisms
Failure of 6: Context modulation is weaker than predicted → β and urgency mechanisms need revision

Priority 2: Core Mechanism Predictions (Highest Impact)

Prediction 2.1: Neuromodulatory Blockade Effects

Hypothesis:
Pharmacological blockade of norepinephrine will reduce P3b amplitude and diminish emotional stimulus ignition probability while leaving early sensory ERPs unaffected.

Method:

Double-blind, placebo-controlled, within-subjects design
Drug: Propranolol (β-adrenergic antagonist, 40-80mg oral) vs. placebo
Task: Emotional oddball paradigm (threatening faces/words as deviants among neutral standards)
Measures: EEG (P3b amplitude, latency), early sensory ERPs (N1, P1), behavioral detection rates

Predictions:

P3b amplitude reduced by 20-40% for emotional deviants under propranolol
N1/P1 amplitudes unchanged (early sensory processing unaffected)
Detection accuracy reduced for emotional stimuli specifically
Neutral stimuli effects minimal

Falsification:
If propranolol reduces early ERPs but not P3b, suggests NE affects sensory encoding rather than ignition threshold.

Prediction 2.2: Thalamic Disruption Dissociation

Hypothesis:
Optogenetic inhibition of pulvinar thalamus will disrupt global broadcast (gamma synchrony, PCI) without impairing local visual processing.

Method:

Animal model: Non-human primates (macaques) or mice with comparable thalamocortical architecture
Optogenetics: Halorhodopsin expression in pulvinar neurons for temporally precise inhibition
Task: Visual detection with concurrent electrophysiology

Measures:

Local visual processing: Early visual cortex (V1/V2) responses to stimuli
Global broadcast: Gamma-band synchrony between frontal and posterior cortex
PCI via intracranial EEG with electrical stimulation
Behavioral: Detection rates, reaction times

Predictions:

Pulvinar inhibition during stimulus presentation (0-300ms post-onset):

V1/V2 responses preserved (local processing intact)
Long-range gamma synchrony abolished or reduced >50%
PCI drops from >0.4 to <0.3 (loss of complex dynamics)
Behavioral report impaired (reduced detection for near-threshold stimuli)

Control:

Inhibition of ventral posterior thalamus (core/relay nucleus) should impair V1 responses but preserve ignition capacity for other modalities

Falsification:
If pulvinar inhibition impairs V1 responses equivalently to impairing report, suggests pulvinar is involved in early sensory processing rather than selective ignition amplification.

Translation to Humans:

Pulvinar lesion patients: Test for dissociation between local visual processing (contrast sensitivity, motion detection) and conscious report
TMS over pulvinar region: Disrupt processing during critical window (100-300ms), measure effects on P3b and report

Prediction 2.3: Surprise Accumulation Dynamics

Hypothesis:
Trial-by-trial Sₜ accumulation, estimated from neural data, predicts ignition probability with high accuracy.

Method:

Human EEG/MEG with computational modeling
Perceptual detection at threshold (adjusting stimulus intensity to ~50% detection)

Analysis:

Fit computational model (Sₜ accumulation equations) to single-trial data
Estimate Sₜ(t) from ramping parietal activity + pupil dilation (NE proxy)
Estimate θₜ from pre-stimulus alpha/beta power
Predict trial-by-trial seen/unseen based on Sₜ > θₜ

Predictions:

Model prediction accuracy >75% for seen vs. unseen trials
Sₜ trajectory diverges between seen/unseen around 150-200ms pre-report
Trials where Sₜ narrowly exceeds θₜ show longest reaction times (near-threshold dynamics)
Individual differences in fitted parameters (α, γ, δ, β) predict anxiety scores, interoceptive accuracy

Falsification:
If Sₜ estimation from neural data doesn't predict report better than stimulus intensity alone, suggests threshold model is incorrect or neural proxies are inadequate.

Priority 3: Clinical Translation Predictions

Prediction 3.1: Anxiety Disorder Differentiation

Hypothesis:
GAD, panic disorder and social anxiety show distinct neural signatures differentiating exteroceptive vs. interoceptive precision dysregulation.

Method:

Participants:
Age-matched groups (GAD, panic disorder, social anxiety, healthy controls; n≥30 per group)

Tasks:

Cognitive threat task: Semantic threat words in oddball paradigm (GAD prediction: elevated P3b)
Interoceptive challenge: CO₂ inhalation or heartbeat detection (panic prediction: elevated P3b)
Social evaluation task: Being watched while performing task (social anxiety prediction: context-specific elevation)

Measures:
EEG (P3b to cognitive, interoceptive and social-evaluative stimuli), fMRI (insula-LC connectivity), pupillometry

Predictions:

GAD: P3b_cognitive > P3b_interoceptive; dlPFC-amygdala hyperconnectivity
Panic disorder: P3b_interoceptive >> P3b_cognitive; AI-LC hyperconnectivity; exaggerated pupil response to interoceptive challenge
Social anxiety: P3b_social > controls only during social evaluation context; context-dependent AI-LC hyperconnectivity
Discriminant function analysis: Neural profiles classify disorder subtype with >75% accuracy

Clinical Utility:
If validated, could guide precision medicine—tailor treatments to specific precision profile (β-blockers for panic, CBT focus for GAD, exposure type for social anxiety).

Prediction 3.2: Depression Treatment Response

Hypothesis:
Individual-level fitted APGI parameters predict antidepressant treatment response.

Method:

Participants:
Unmedicated depressed patients (n≥60) before treatment initiation

Baseline assessment:

Emotional oddball task with EEG (estimate baseline θₜ from P3b threshold)
Pupillometry during reward anticipation (estimate DA/NE tone)
Interoceptive accuracy tasks (estimate baseline Πᵢ)
Computational modeling to extract individual θₜ, Πₑ, Πᵢ, γ parameters

Treatment:
Standard SSRI or SNRI (8 weeks)

Outcome:
Response defined as >50% reduction in depression scores

Predictions:

Elevated θₜ at baseline predicts better response to noradrenergic agents (SNRI, bupropion)
Reduced Πᵢ predicts better response to interventions addressing anhedonia
Slow γ (impaired homeostatic recovery) predicts need for augmentation strategies
Parameter-based prediction model outperforms clinical variables alone

Clinical Translation:
Develop brief (~30 min) assessment battery extracting APGI parameters to guide treatment selection.

Prediction 3.3: PTSD Treatment Mechanism

Hypothesis:
Successful PTSD treatment (prolonged exposure) updates M_{trauma}, measurable as reduced Πᵢ for trauma cues.

Method:

Participants: PTSD patients (n≥40) undergoing prolonged exposure therapy
Assessment at baseline, mid-treatment (session 6), post-treatment (session 12):
Neural: fMRI during trauma-related vs. neutral image viewing (insula, amygdala, vmPFC activation)
Physiological: Heart rate, skin conductance to trauma cues
EEG: P3b to trauma-related auditory cues during oddball task
Computational: Model M_{trauma} parameters from psychophysical tasks (how predictable is interoceptive response to trauma cues?)

Predictions:

Successful treatment shows:

Reduced interoceptive P3b to trauma cues (by 40-60%)
Decreased AI-LC connectivity during trauma cue exposure
Normalized vmPFC activity (increased contextualization)
Computational model: Increased Σ_{trauma} (reduced confidence), reduced μ_{trauma} (less extreme predicted response)

Treatment non-responders show minimal parameter changes

Early prediction: Changes at mid-treatment predict final outcome

Mechanism Validation: If treatment-related changes in neural parameters mediate symptom improvement (formal mediation analysis), supports the causal role of M_{trauma} updating.

Priority 4: High-Resolution Neural Signatures

Prediction 4.1: EEG Microstate Transitions

Hypothesis:
Ignition events correspond to transitions from posterior (DMN/sensory) to anterior (frontoparietal/salience) EEG microstates, with transition probability predicted by Sₜ/θₜ ratio.

Method:

High-density EEG (128+ channels) during threshold detection task
Microstate analysis: Cluster scalp topographies into ~4-6 canonical states
Trial-by-trial analysis:
Classify microstates moment-by-moment (ms resolution)
Estimate Sₜ/θₜ from neural/pupil data
Relate microstate transition timing to ignition

Predictions:

Pre-ignition (−200 to 0 ms): Dominance of posterior microstates (visual processing, DMN)
Ignition onset (0-100 ms): Rapid transition to anterior microstates (frontoparietal, salience)
Post-ignition (100-500 ms): Stable anterior microstate occupancy
Transition probability P(posterior→anterior) = σ(Sₜ/θₜ)
Higher Sₜ/θₜ → faster transitions

Validation:
Provides millisecond-resolution marker of ignition transition, enabling precise temporal dissection.

Prediction 4.2: Pupillometry as LC-NE Proxy

Hypothesis:
Pupil dilation correlates with interoceptive precision (Πᵢ) on trial-by-trial basis, independent of luminance and motor preparation, with ~200-500ms lag.

Method:

High-speed eye-tracking (1000 Hz) during emotional/interoceptive tasks
Constant luminance throughout task
Control for motor preparation (delayed response paradigm)
Trial-by-trial correlation between:
Pupil dilation (baseline-corrected, 200-500ms post-stimulus)
Estimated Πᵢ (from task-evoked interoceptive prediction errors)
P3b amplitude (ignition marker)
Subjective arousal ratings

Predictions:

Pupil dilation at 200-500ms predicts P3b amplitude (r > 0.4)
Larger dilation for interoceptive vs. exteroceptive stimuli (soma-bias)
Individual differences: Higher baseline pupil diameter correlates with trait anxiety and elevated Πᵢ
Pharmacological validation: Propranolol reduces task-evoked dilation and Πᵢ in parallel

Utility:
Provides non-invasive, continuous readout of neuromodulatory state for closed-loop applications.

Prediction 4.3: Intracranial Recording of Ignition Cascade

Hypothesis:
Intracranial recordings in surgical patients show layer-specific activation sequence matching APGI circuit model.

Method:

Participants: Epilepsy patients with intracranial electrodes (depth, grid) undergoing presurgical monitoring
Task: Visual/auditory detection during recordings
Analysis: Current source density analysis to isolate layer-specific activity

Predictions:

Thalamus: Pulvinar/MD show ramping activity preceding cortical ignition
Insula: Earlier activation for emotional/interoceptive stimuli (soma-bias)
Frontal-parietal synchrony: Gamma-band coherence emerges 100-300ms, coincident with conscious report

Timing:

0-50 ms: Layer 4 activation (thalamic input)
50-100 ms: Layer 5 deep activation (dendritic spikes)
100-200 ms: Layer 2/3 activation (horizontal spread)
200-500 ms: Sustained multilayer activity

Validation:
Direct test of microcircuit model with unparalleled spatial and temporal resolution.

Priority 5: Computational Modeling

Prediction 5.1: Simulated Agent Performance

Hypothesis:
Simulated agents with somatic-marker-gated ignition rule outperform standard PP agents in embodied, uncertain environments.

Method:

Simulated environment: Foraging task with:
Volatile reward contingencies (locations change unpredictably)
Occasional high-cost states (poisoned food sources cause interoceptive aversive states)
Resource constraints (limited energy budget)

Agent types:

APGI agent: Implements Sₜ = Πₑ·εₑ + β·Πᵢ·εᵢ, threshold θₜ, somatic markers M_{c,a}
Standard PP agent: Pure free energy minimization without ignition threshold or somatic gating
Threshold-only agent: Has θₜ but no somatic bias (β = 1)

Metrics:
Cumulative reward, sample efficiency (trials to learn), robustness to volatility

Predictions:

APGI agent outperforms in:

Volatile environments (better uncertainty handling)
Presence of high-cost states (soma-bias prevents catastrophic errors)
Resource-limited conditions (threshold conserves computation)

Standard PP agent outperforms in stable, fully observable environments (no need for selective deployment)

Threshold-only agent: Intermediate performance (benefits of selective deployment but misses embodied prioritization)

Validation:
Demonstrates computational advantages of APGI architecture, supporting evolutionary argument.

Prediction 5.2: Parameter Recovery from Behavior

Hypothesis:
APGI model parameters fitted to human behavioral data are stable, reliable and predict independent neural measures.

Method:

Participants:
Healthy adults (n≥100)

Session 1—Behavioral fitting:

Temporal bisection task with emotional vs. neutral stimuli (estimates β)
Detection threshold task with varying pre-stimulus cues (estimates θₜ dynamics)
Interoceptive accuracy tasks (estimates Πᵢ)
Fit full model to extract individual θₜ, β, Πₑ, Πᵢ, α, γ parameters

Session 2—Neural validation (subset, n≥40):

EEG during oddball task (measure P3b, gamma)
fMRI during emotional processing (measure insula-LC connectivity)
Pupillometry during arousal task

Predictions:

Test-retest reliability: Parameters show ICC > 0.7 over 2-week interval
Neural correspondence:

Fitted θₜ correlates with inverse P3b amplitude (r > 0.5)
Fitted Πᵢ correlates with insula-LC connectivity (r > 0.4)
Fitted β correlates with interoceptive accuracy scores (r > 0.3)

Clinical prediction: Fitted parameters predict anxiety/depression scores (multiple regression R² > 0.3)

Utility:
If validated, enables efficient parameter estimation from a brief behavioral battery for clinical applications.

Priority 6: Perturbational Studies

Prediction 6.1: Insula TMS Effects

Hypothesis:
TMS over anterior insula reduces PCI and interoceptive P3b while sparing exteroceptive ignition.

Method:

Participants: Healthy adults (n≥30)
TMS: Figure-8 coil over right anterior insula (neuronavigated)
Timing: Stimulation at 0-100ms post-stimulus (during early ignition phase)
Tasks: Interoceptive (heartbeat detection) and exteroceptive (visual oddball) in separate blocks

Measures:
P3b amplitude, PCI (via additional single TMS pulse at various delays), detection accuracy

Predictions:

Interoceptive task: Insula TMS reduces P3b by 30-50%, impairs detection
Exteroceptive task: Minimal effects (retained ignition capacity via other routes)
PCI: Reduced during interoceptive task with TMS
Control site (dorsal PFC): Opposite pattern—affects exteroceptive more than interoceptive

Validation:
Demonstrates causal role of insula in interoceptive ignition specifically.

Prediction 6.2: Pulvinar Stimulation Enhancement

Hypothesis:
Electrical stimulation of pulvinar enhances gamma synchrony and stimulus reportability without altering local sensory processing.

Method:

Participants: Surgical patients with therapeutic deep brain stimulation (DBS) electrodes (or research participants with investigational devices)
Stimulation: Low-intensity pulvinar stimulation (30-80 Hz, 100-200ms duration) time-locked to stimulus onset
Task: Threshold visual detection

Measures:
Cortical ECoG (if available), scalp EEG, behavioral detection rates, early visual ERPs

Predictions:

Pulvinar stimulation during ignition window (0-200ms post-stimulus):

Increased gamma-band synchrony between frontal and posterior cortex
Improved detection rates for near-threshold stimuli (by 15-30%)
Unchanged early visual ERPs (V1 processing unaffected)

Stimulation before or after ignition window: Minimal effects
Dose-response: Effects scale with stimulation intensity/duration up to saturation

Utility:
If validated, could inform neuromodulation therapies for disorders of consciousness or attention.

Priority 7: Cross-Species Comparative Predictions

Prediction 7.1: Phylogenetic Distribution of Ignition Signatures

Hypothesis:
Species with complex, unpredictable ecological niches show more elaborate ignition signatures (P3b-like components, long-range synchrony) than specialists.

Method:

Comparative EEG/local field potentials across species during oddball paradigms
Species selection:

High complexity: Primates, corvids, parrots, elephants, cetaceans
Moderate: Rodents, carnivores
Low: Reptiles, amphibians

Measures:
Late positive components, gamma synchrony, PCI-equivalent measures

Predictions:

P3b-like component amplitude and duration correlates with:

Brain size (absolute and relative to body)
Ecological complexity (dietary breadth, habitat variability)
Lifespan

Long-range gamma synchrony present in high-complexity species, absent or minimal in specialists
Behavioral flexibility (novel problem-solving) correlates with ignition signatures

Evolutionary Validation:
Supports adaptive optimization hypothesis—ignition evolves under ecological pressure for flexibility.

## Appendix: The Ignition Threshold Equation

Conscious access is formalized through a precision-gated threshold mechanism:

```math
Sₜ = Πₑ·|εₑ| + Πᵢ(M_{c,a})·|εᵢ|
Bₜ = σ(α(Sₜ - θₜ))
```python

Ignition occurs if $Sₜ > θₜ$

### Where

- **$Sₜ$**: Total precision-weighted surprise (dimensionless, typical range: 0–10)
- **$Πₑ, Πᵢ$**: Precision (inverse variance) of exteroceptive and interoceptive prediction errors
- **$εₑ, εᵢ$**: Prediction errors (standardized as z-scores)
- **$M_{c,a}$**: Somatic marker gain—learned value function linking context $c$ and action $a$ to expected interoceptive consequences
- **$θₜ$**: Dynamic ignition threshold, reflecting metabolic and computational cost
- **$α$**: Sigmoid steepness controlling transition sharpness
- **$σ(·)$**: Logistic sigmoid function ($σ(x) = 1/(1 + e⁻ˣ)$)
- **$Bₜ$**: Probability of global ignition (range: [0,1])

### Key Interpretations

- Absolute values ensure ignition depends on magnitude of surprise, not valence.
- Precision implements attention: high-precision signals dominate inference.
- Somatic markers modulate $Πⁱ$, not $εⁱ$—they are gain mechanisms, not signal generators.
- Threshold $θₜ$ is dynamic: lowered in high-stakes contexts, raised during routine tasks or under anesthesia.
