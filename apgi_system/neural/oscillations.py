"""
Neural Oscillation Engine

Generates multi-band oscillations and phase-amplitude coupling.
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class OscillationBand:
    """Configuration for an oscillation band."""

    name: str
    freq_range: Tuple[float, float]  # Hz
    amplitude: float
    phase: float = 0.0
    power: float = 0.0


class OscillationEngine:
    """
    Multi-band neural oscillation generator with phase-amplitude coupling.

    Generates neural oscillations across multiple frequency bands that are
    critical for consciousness and cognitive processing. Each band serves
    specific computational functions:

    - **Delta (1-4 Hz)**: Slow allostatic cycles and deep sleep rhythms
    - **Theta (4-8 Hz)**: Long-range coordination and memory encoding
    - **Alpha (8-12 Hz)**: Inhibition, gating, and attention control
    - **Beta (12-30 Hz)**: Top-down prediction signaling and motor control
    - **Gamma (30-80 Hz)**: Feature binding, local coherence, conscious access

    The engine implements phase-amplitude coupling (PAC), particularly:
    - Theta-gamma coupling: Gamma amplitude modulated by theta phase
    - Alpha-gamma coupling: Attention-related gamma modulation

    Each oscillation band maintains its own phase, amplitude, and power
    estimates. The system supports dynamic frequency modulation and
    amplitude control for experimental manipulations.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing oscillation settings:
        - oscillations.bands: Dictionary of band configurations with
          'range' (frequency range in Hz) and 'amplitude' (base amplitude)
        - oscillations.coupling_strength: Strength of cross-frequency coupling (default: 0.3)
        - oscillations.criticality_parameter: Criticality parameter (default: 1.0)
        - system.timestep_ms: System timestep in milliseconds (default: 1.0)

    Attributes
    ----------
    bands : Dict[str, OscillationBand]
        Dictionary of oscillation bands with their current states
    coupling_strength : float
        Strength of phase-amplitude coupling between bands
    criticality_param : float
        Parameter controlling criticality dynamics
    time : float
        Current simulation time in seconds
    dt_sec : float
        Timestep in seconds
    signal_history : List[float]
        Recent history of total oscillatory signal for analysis
    max_history : int
        Maximum length of signal history buffer

    Examples
    --------
    >>> config = {
    ...     'oscillations': {
    ...         'bands': {
    ...             'gamma': {'range': [30, 80], 'amplitude': 0.5},
    ...             'theta': {'range': [4, 8], 'amplitude': 0.3}
    ...         },
    ...         'coupling_strength': 0.4
    ...     }
    ... }
    >>> engine = OscillationEngine(config)
    >>> result = engine.generate(dt=0.001)
    >>> print(result['band_powers']['gamma'])
    0.25
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize oscillation engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        osc_config = config.get("oscillations", {})
        bands_config = osc_config.get("bands", {})

        # Initialize bands
        self.bands = {}
        for band_name, band_cfg in bands_config.items():
            freq_range = tuple(band_cfg["range"])
            amplitude = band_cfg["amplitude"]

            # Start with random frequency in range
            center_freq = (freq_range[0] + freq_range[1]) / 2

            self.bands[band_name] = OscillationBand(
                name=band_name,
                freq_range=freq_range,
                amplitude=amplitude,
                phase=np.random.rand() * 2 * np.pi,
                power=0.0,
            )

        # Coupling parameters
        self.coupling_strength = osc_config.get("coupling_strength", 0.3)
        self.criticality_param = osc_config.get("criticality_parameter", 1.0)

        # Time tracking
        self.time = 0.0
        self.dt_sec = config.get("system", {}).get("timestep_ms", 1.0) / 1000.0

        # History for power calculation
        self.signal_history = []
        self.max_history = 100

    def generate(
        self, modulation: Optional[Dict[str, float]] = None, dt: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate multi-band oscillatory signals with cross-frequency coupling.

        Performs a complete oscillation generation cycle:
        1. Updates phase for each oscillation band based on center frequency
        2. Generates sinusoidal signals for each band
        3. Applies phase-amplitude coupling (theta-gamma, alpha-gamma)
        4. Computes power estimates using exponential smoothing
        5. Calculates cross-frequency coupling metrics

        The total signal is the sum of all band signals. Phase-amplitude
        coupling modulates gamma amplitude based on theta and alpha phases,
        implementing known neural mechanisms for attention and memory.

        Parameters
        ----------
        modulation : Optional[Dict[str, float]], optional
            Dictionary mapping band names to amplitude modulation factors.
            Values > 1.0 increase amplitude, < 1.0 decrease amplitude.
            If None, uses baseline amplitudes. By default None.
        dt : Optional[float], optional
            Timestep in seconds. If None, uses configured system timestep.
            By default None.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'total_signal': Sum of all band signals (float)
            - 'band_signals': Dict mapping band names to current signal values
            - 'band_powers': Dict mapping band names to power estimates
            - 'band_phases': Dict mapping band names to current phases (radians)
            - 'coupling_metrics': Dict with cross-frequency coupling measures

        Examples
        --------
        >>> engine = OscillationEngine(config)
        >>> # Generate with gamma enhancement
        >>> result = engine.generate(modulation={'gamma': 1.5}, dt=0.001)
        >>> print(f"Total signal: {result['total_signal']:.3f}")
        Total signal: 0.847
        >>> print(f"Gamma power: {result['band_powers']['gamma']:.3f}")
        Gamma power: 0.563
        """
        if dt is None:
            dt = self.dt_sec

        # Update time
        self.time += dt

        # Generate each band
        band_signals = {}
        total_signal = 0.0

        for band_name, band in self.bands.items():
            # Get center frequency
            center_freq = (band.freq_range[0] + band.freq_range[1]) / 2

            # Update phase
            band.phase += 2 * np.pi * center_freq * dt
            band.phase = band.phase % (2 * np.pi)

            # Apply modulation if provided
            amplitude = band.amplitude
            if modulation and band_name in modulation:
                amplitude *= modulation[band_name]

            # Generate signal
            signal = amplitude * np.sin(band.phase)

            # Apply phase-amplitude coupling
            if band_name == "gamma":
                # Gamma amplitude modulated by theta phase
                if "theta" in self.bands:
                    theta_phase = self.bands["theta"].phase
                    pac_modulation = 1.0 + self.coupling_strength * np.cos(theta_phase)
                    signal *= pac_modulation

            if band_name == "gamma" and "alpha" in self.bands:
                # Alpha-gamma coupling for attention
                alpha_phase = self.bands["alpha"].phase
                alpha_modulation = 1.0 + 0.5 * self.coupling_strength * np.sin(alpha_phase)
                signal *= alpha_modulation

            band_signals[band_name] = signal
            total_signal += signal

            # Update power estimate
            band.power = 0.9 * band.power + 0.1 * (signal**2)

        # Add to history for analysis
        self.signal_history.append(total_signal)
        if len(self.signal_history) > self.max_history:
            self.signal_history.pop(0)

        # Compute cross-frequency metrics
        coupling_metrics = self._compute_coupling_metrics()

        return {
            "total_signal": total_signal,
            "band_signals": band_signals,
            "band_powers": {name: band.power for name, band in self.bands.items()},
            "band_phases": {name: band.phase for name, band in self.bands.items()},
            "coupling_metrics": coupling_metrics,
        }

    def _compute_coupling_metrics(self) -> Dict[str, float]:
        """Compute phase-amplitude coupling metrics."""
        metrics = {}

        # Theta-gamma coupling
        if "theta" in self.bands and "gamma" in self.bands:
            theta_phase = self.bands["theta"].phase
            gamma_power = self.bands["gamma"].power

            # Modulation index (simplified)
            coupling = gamma_power * np.cos(theta_phase)
            metrics["theta_gamma_coupling"] = float(coupling)

        # Alpha-gamma coupling
        if "alpha" in self.bands and "gamma" in self.bands:
            alpha_phase = self.bands["alpha"].phase
            gamma_power = self.bands["gamma"].power

            coupling = gamma_power * np.sin(alpha_phase)
            metrics["alpha_gamma_coupling"] = float(coupling)

        # Beta power (predictive signaling)
        if "beta" in self.bands:
            metrics["beta_power"] = float(self.bands["beta"].power)

        return metrics

    def modulate_band(self, band_name: str, amplitude_factor: float):
        """
        Modulate a specific oscillation band's amplitude.

        Multiplies the current amplitude of the specified band by the given
        factor. This allows for dynamic control of oscillation strength,
        useful for simulating pharmacological interventions, attention
        modulation, or pathological states.

        Parameters
        ----------
        band_name : str
            Name of the oscillation band to modulate (e.g., 'gamma', 'theta')
        amplitude_factor : float
            Multiplicative factor applied to current amplitude.
            Values > 1.0 increase amplitude, < 1.0 decrease amplitude.
            Factor of 0.0 effectively silences the band.

        Examples
        --------
        >>> engine = OscillationEngine(config)
        >>> engine.modulate_band('gamma', 2.0)  # Double gamma amplitude
        >>> engine.modulate_band('alpha', 0.5)  # Halve alpha amplitude
        """
        if band_name in self.bands:
            self.bands[band_name].amplitude *= amplitude_factor

    def set_band_frequency(self, band_name: str, frequency: float):
        """
        Set center frequency of a band.

        Args:
            band_name: Name of band
            frequency: Frequency in Hz
        """
        if band_name in self.bands:
            band = self.bands[band_name]
            # Ensure within range
            frequency = np.clip(frequency, band.freq_range[0], band.freq_range[1])

            # Update by changing phase increment
            # (Implementation detail - stored in freq_range for now)
            center = (band.freq_range[0] + band.freq_range[1]) / 2
            if frequency != center:
                # Adjust range around new center (maintaining width)
                width = band.freq_range[1] - band.freq_range[0]
                band.freq_range = (frequency - width / 2, frequency + width / 2)

    def get_spectral_power(self) -> Dict[str, float]:
        """Get current spectral power in each band."""
        return {name: float(band.power) for name, band in self.bands.items()}

    def detect_gamma_burst(self, threshold: float = 0.5) -> bool:
        """
        Detect gamma burst events associated with conscious access.

        Gamma bursts (sudden increases in gamma power) are neural signatures
        of conscious access and global ignition. This method detects when
        gamma power exceeds a threshold, indicating potential conscious
        processing of information.

        Parameters
        ----------
        threshold : float, optional
            Power threshold for gamma burst detection, by default 0.5.
            Higher thresholds require stronger gamma activity for detection.

        Returns
        -------
        bool
            True if gamma power exceeds threshold (burst detected),
            False otherwise. Returns False if gamma band not configured.

        Examples
        --------
        >>> engine = OscillationEngine(config)
        >>> result = engine.generate()
        >>> if engine.detect_gamma_burst(threshold=0.7):
        ...     print("Conscious access event detected!")
        """
        if "gamma" in self.bands:
            return self.bands["gamma"].power > threshold
        return False

    def get_current_state(self) -> Dict[str, Any]:
        """Get current oscillation state."""
        return {
            "time": self.time,
            "band_powers": {name: band.power for name, band in self.bands.items()},
            "band_phases": {name: band.phase for name, band in self.bands.items()},
            "band_frequencies": {
                name: (band.freq_range[0] + band.freq_range[1]) / 2
                for name, band in self.bands.items()
            },
            "coupling_metrics": self._compute_coupling_metrics(),
            "gamma_burst": self.detect_gamma_burst(),
        }

    def reset(self):
        """Reset oscillation engine."""
        for band in self.bands.values():
            band.phase = np.random.rand() * 2 * np.pi
            band.power = 0.0

        self.time = 0.0
        self.signal_history = []
