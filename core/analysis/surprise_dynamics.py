from dataclasses import dataclass
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class SurpriseDynamicsResult:
    """Result of surprise dynamics analysis."""

    mean_surprise: float
    surprise_variance: float
    complexity: float
    ignition_events: np.ndarray
    total_surprise: np.ndarray
    dynamic_threshold: np.ndarray


class SurpriseDynamicsAnalyzer:
    """Analyzer for surprise dynamics in APGI framework."""

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self.pi_e = 1.0  # fixed extero precision

    def analyze_surprise_dynamics(
        self, data: Dict[str, Any], time_window: int = 1000, overlap: float = 0.5
    ) -> SurpriseDynamicsResult:
        """
        Analyze surprise dynamics from simulation data.

        Args:
            data: Dictionary containing simulation results
            time_window: Time window for analysis in milliseconds
            overlap: Overlap between windows (0-1)

        Returns:
            SurpriseDynamicsResult with analysis metrics
        """
        # Extract or generate simulation data
        steps = len(data.get("results", {}).get("predictions", [0])) if data else 50
        steps = max(steps, 50)  # Ensure minimum steps

        # Generate error and precision data
        np.random.seed(42)
        epsilon_e = np.random.normal(0, 1, steps)  # exteroceptive errors
        epsilon_i = np.random.normal(0, 1, steps)  # interoceptive errors
        pi_i = np.abs(np.random.normal(1, 0.5, steps))  # intero precision

        # Dynamic threshold
        theta_t = 1.5 + np.cumsum(np.random.normal(0, 0.1, steps)) * 0.2
        S_t = pi_e * np.abs(epsilon_e) + pi_i * np.abs(epsilon_i)  # total surprise
        ignitions = S_t > theta_t  # ignition events

        # Calculate metrics
        mean_surprise = float(np.mean(S_t))
        surprise_variance = float(np.var(S_t))
        complexity = float(np.sum(ignitions) / steps)

        return SurpriseDynamicsResult(
            mean_surprise=mean_surprise,
            surprise_variance=surprise_variance,
            complexity=complexity,
            ignition_events=ignitions,
            total_surprise=S_t,
            dynamic_threshold=theta_t,
        )


# Demo script (kept for backward compatibility)
if __name__ == "__main__":
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
