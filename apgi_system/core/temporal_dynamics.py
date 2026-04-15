"""
Temporal Dynamics Module

Implements oscillatory synchronization, phase-amplitude coupling (PAC),
and neural orchestration for the Global Neuronal Workspace.
"""

from typing import Any, Dict, Optional

import numpy as np
from apgi_system.types import ConfigDict


class TemporalDynamics:
    """
    Handles temporal orchestration of neural activity through oscillations.

    Implements:
    - Multi-band oscillatory oscillations (Delta to Gamma)
    - Phase-Amplitude Coupling (PAC)
    - Synchrony metrics for ignition validation
    - Phase-dependent gain modulation

    Parameters
    ----------
    config : dict
        Configuration dictionary (``oscillations`` sub-key is used).
    rng : np.random.Generator, optional
        Seeded NumPy random generator.  When provided, all stochastic
        operations use this generator so that runs are fully reproducible.
        If *None*, a new default generator is created (non-reproducible).
    """

    def __init__(self, config: ConfigDict, rng: Optional[np.random.Generator] = None) -> None:
        """
        Initialize the Temporal Dynamics module.

        Parameters
        ----------
        config : dict
            Configuration dictionary.
        rng : np.random.Generator, optional
            Seeded generator for reproducible phase initialisation.
        """
        self.config = config.get("oscillations", {})
        self.bands = self.config.get(
            "bands",
            {
                "delta": {"range": [1, 4], "amplitude": 0.5},
                "theta": {"range": [4, 8], "amplitude": 0.7},
                "alpha": {"range": [8, 12], "amplitude": 1.0},
                "beta": {"range": [12, 30], "amplitude": 0.8},
                "gamma": {"range": [30, 80], "amplitude": 0.6},
            },
        )
        self.coupling_strength = self.config.get("coupling_strength", 0.3)

        # Use caller-supplied RNG; fall back to a new default generator (non-seeded).
        self._rng: np.random.Generator = rng if rng is not None else np.random.default_rng()

        self.time = 0.0
        # Initialize phases reproducibly via the injected RNG
        self.phases = {band: self._rng.uniform(0, 2 * np.pi) for band in self.bands}

    def update(self, dt: float) -> Dict[str, Any]:
        """
        Update oscillator phases and compute coupling.

        Args:
            dt: Timestep in seconds

        Returns:
            Dictionary with current oscillatory state
        """
        self.time += dt

        current_amplitudes = {}
        for band, params in self.bands.items():
            freq_range = params["range"]
            # Centers frequency within band
            freq = (freq_range[0] + freq_range[1]) / 2.0

            # Update phase: dφ/dt = 2πf
            self.phases[band] = (self.phases[band] + 2 * np.pi * freq * dt) % (2 * np.pi)

            # Oscillatory signal
            current_amplitudes[band] = params["amplitude"] * np.sin(self.phases[band])

        # Compute Phase-Amplitude Coupling (PAC)
        # Typically: Theta phase modulates Gamma amplitude
        theta_phase = self.phases.get("theta", 0.0)
        pac_modulation = 1.0 + self.coupling_strength * np.sin(theta_phase)
        current_amplitudes["gamma"] *= pac_modulation

        return {
            "phases": self.phases,
            "amplitudes": current_amplitudes,
            "pac_factor": pac_modulation,
            "synchrony": self._compute_synchrony(current_amplitudes),
        }

    def _compute_synchrony(self, amplitudes: Dict[str, float]) -> float:
        """Compute simplified global synchrony metric."""
        if not amplitudes:
            return 0.0
        # Phase locking or global amplitude coherence approximation
        vals = list(amplitudes.values())
        return float(np.abs(np.mean(vals)) / (np.mean(np.abs(vals)) + 1e-10))

    def get_gain_modulation(self, band: str = "alpha") -> float:
        """Get phase-dependent gain modulation for perceptual gating."""
        phase = self.phases.get(band, 0.0)
        # Gain is highest at specific phase (e.g. crest)
        return float(1.0 + 0.5 * np.sin(phase))

    def reset(self) -> None:
        """Reset temporal state."""
        self.time = 0.0
        self.phases = {band: self._rng.uniform(0, 2 * np.pi) for band in self.bands}
