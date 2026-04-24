import matplotlib.pyplot as plt
import numpy as np

# Setup: Simulate 50 steps of errors and precisions
np.random.seed(42)
steps = 50
epsilon_e = np.random.normal(0, 1, steps)  # exteroceptive errors
epsilon_i = np.random.normal(0, 1, steps)  # interoceptive errors
pi_e = 1.0  # fixed extero precision
pi_i = np.abs(np.random.normal(1, 0.5, steps))  # intero precision with somatic bias variation
theta_t = 1.5 + np.cumsum(np.random.normal(0, 0.1, steps)) * 0.2
# dynamic threshold
S_t = pi_e * np.abs(epsilon_e) + pi_i * np.abs(epsilon_i)  # total surprise
ignitions = S_t > theta_t  # ignition events

# Plot
plt.figure(figsize=(10, 6))
plt.plot(S_t, label="S_t (Total Surprise)")
plt.plot(theta_t, label="θ_t (Dynamic Threshold)")
plt.scatter(np.where(ignitions)[0], S_t[ignitions], color="red", label="Ignition Events")
plt.xlabel("Time Steps")
plt.ylabel("Value")
plt.title("APGI Framework: Surprise Dynamics and Ignition Threshold")
plt.legend()
plt.savefig("apgi_demo_visualization.png")  # Save for viewing
print("Ignition steps:", np.where(ignitions)[0])
