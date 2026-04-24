import matplotlib.pyplot as plt
import numpy as np
from scipy.special import expit
from typing import Union


def ignition_probability(
    S_t: Union[float, np.ndarray], theta_t: float, alpha: float
) -> Union[float, np.ndarray]:
    """Calculate probability of ignition B_t using sigmoid."""
    result: Union[float, np.ndarray] = expit(alpha * (S_t - theta_t))
    return result


# Generate data
S_t_range = np.linspace(0, 10, 100)  # Range of precision-weighted surprise
theta_values = [3, 5, 7]  # Different threshold contexts
alpha_values = [0.5, 1.0, 2.0]  # Different sigmoid steepness

# Plot effect of threshold
plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
for theta in theta_values:
    B_t = ignition_probability(S_t_range, theta, alpha=1.0)
    plt.plot(S_t_range, B_t, label=f"θ_t = {theta}")
plt.xlabel("Precision-Weighted Surprise (S_t)")
plt.ylabel("Ignition Probability (B_t)")
plt.title("Effect of Dynamic Threshold (θ_t)")
plt.legend()
plt.grid(True)

# Plot effect of alpha (sigmoid steepness)
plt.subplot(1, 3, 2)
for alpha in alpha_values:
    B_t = ignition_probability(S_t_range, theta_t=5, alpha=alpha)
    plt.plot(S_t_range, B_t, label=f"α = {alpha}")
plt.xlabel("Precision-Weighted Surprise (S_t)")
plt.ylabel("Ignition Probability (B_t)")
plt.title("Effect of Transition Sharpness (α)")
plt.legend()
plt.grid(True)

# Show somatic marker effect
plt.subplot(1, 3, 3)
S_t_extero = 2.5  # Constant exteroceptive signal
M_values = [0.5, 1.0, 2.0]  # Somatic marker gains
epsilon_i = 3.0  # Interoceptive prediction error

for M in M_values:
    S_t_total = S_t_extero + M * epsilon_i
    B_t = ignition_probability(S_t_total, theta_t=5, alpha=1.0)
    plt.bar(f"M={M}", B_t, label=f"S_t={S_t_total:.1f}")
plt.ylabel("Ignition Probability (B_t)")
plt.title("Somatic Marker (M) Effect on Ignition")
plt.grid(True)

plt.tight_layout()
plt.show()
