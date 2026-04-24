# APGI Framework Ignition Threshold Equation

Conscious access is formalized through a precision-gated threshold mechanism:

```math
Sₜ = Πₑ·|εₑ| + Πᵢ(M_{c,a})·|εᵢ|
Bₜ = σ(α(Sₜ - θₜ))
```python

Ignition occurs if $Sₜ > θₜ$

Where

- **$Sₜ$**: Total precision-weighted surprise (dimensionless, typical range: 0–10)
- **$Πₑ, Πᵢ$**: Precision (inverse variance) of exteroceptive and interoceptive prediction errors
- **$εₑ, εᵢ$**: Prediction errors (standardized as z-scores)
- **$M_{c,a}$**: Somatic marker gain—learned value function linking context $c$ and action $a$ to expected interoceptive consequences
- **$θₜ$**: Dynamic ignition threshold, reflecting metabolic and computational cost
- **$α$**: Sigmoid steepness controlling transition sharpness
- **$σ(·)$**: Logistic sigmoid function ($σ(x) = 1/(1 + e⁻ˣ)$)
- **$Bₜ$**: Probability of global ignition (range: [0,1])

## Key Interpretations

- Absolute values ensure ignition depends on magnitude of surprise, not valence.
- Precision implements attention: high-precision signals dominate inference.
- Somatic markers modulate $Πⁱ$, not $εⁱ$—they are gain mechanisms, not signal generators.
- Threshold $θₜ$ is dynamic: lowered in high-stakes contexts, raised during routine tasks or under anesthesia.
