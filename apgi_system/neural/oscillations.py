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
    Multi-band neural oscillation generator.

    Implements:
    - Delta (1-4 Hz): Slow allostatic cycles
    - Theta (4-8 Hz): Long-range coordination
    - Alpha (8-12 Hz): Inhibition and gating
    - Beta (12-30 Hz): Top-down prediction signaling
    - Gamma (30-80 Hz): Feature binding, local coherence

    Includes phase-amplitude coupling (e.g., theta-gamma).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize oscillation engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        osc_config = config.get('oscillations', {})
        bands_config = osc_config.get('bands', {})

        # Initialize bands
        self.bands = {}
        for band_name, band_cfg in bands_config.items():
            freq_range = tuple(band_cfg['range'])
            amplitude = band_cfg['amplitude']

            # Start with random frequency in range
            center_freq = (freq_range[0] + freq_range[1]) / 2

            self.bands[band_name] = OscillationBand(
                name=band_name,
                freq_range=freq_range,
                amplitude=amplitude,
                phase=np.random.rand() * 2 * np.pi,
                power=0.0
            )

        # Coupling parameters
        self.coupling_strength = osc_config.get('coupling_strength', 0.3)
        self.criticality_param = osc_config.get('criticality_parameter', 1.0)

        # Time tracking
        self.time = 0.0
        self.dt_sec = config.get('system', {}).get('timestep_ms', 1.0) / 1000.0

        # History for power calculation
        self.signal_history = []
        self.max_history = 100

    def generate(
        self,
        modulation: Optional[Dict[str, float]] = None,
        dt: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate oscillatory signal.

        Args:
            modulation: Optional modulation of band amplitudes
            dt: Time step in seconds (uses default if None)

        Returns:
            Dictionary with signals and band information
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
            if band_name == 'gamma':
                # Gamma amplitude modulated by theta phase
                if 'theta' in self.bands:
                    theta_phase = self.bands['theta'].phase
                    pac_modulation = 1.0 + self.coupling_strength * np.cos(theta_phase)
                    signal *= pac_modulation

            if band_name == 'gamma' and 'alpha' in self.bands:
                # Alpha-gamma coupling for attention
                alpha_phase = self.bands['alpha'].phase
                alpha_modulation = 1.0 + 0.5 * self.coupling_strength * np.sin(alpha_phase)
                signal *= alpha_modulation

            band_signals[band_name] = signal
            total_signal += signal

            # Update power estimate
            band.power = 0.9 * band.power + 0.1 * (signal ** 2)

        # Add to history for analysis
        self.signal_history.append(total_signal)
        if len(self.signal_history) > self.max_history:
            self.signal_history.pop(0)

        # Compute cross-frequency metrics
        coupling_metrics = self._compute_coupling_metrics()

        return {
            'total_signal': total_signal,
            'band_signals': band_signals,
            'band_powers': {name: band.power for name, band in self.bands.items()},
            'band_phases': {name: band.phase for name, band in self.bands.items()},
            'coupling_metrics': coupling_metrics
        }

    def _compute_coupling_metrics(self) -> Dict[str, float]:
        """Compute phase-amplitude coupling metrics."""
        metrics = {}

        # Theta-gamma coupling
        if 'theta' in self.bands and 'gamma' in self.bands:
            theta_phase = self.bands['theta'].phase
            gamma_power = self.bands['gamma'].power

            # Modulation index (simplified)
            coupling = gamma_power * np.cos(theta_phase)
            metrics['theta_gamma_coupling'] = float(coupling)

        # Alpha-gamma coupling
        if 'alpha' in self.bands and 'gamma' in self.bands:
            alpha_phase = self.bands['alpha'].phase
            gamma_power = self.bands['gamma'].power

            coupling = gamma_power * np.sin(alpha_phase)
            metrics['alpha_gamma_coupling'] = float(coupling)

        # Beta power (predictive signaling)
        if 'beta' in self.bands:
            metrics['beta_power'] = float(self.bands['beta'].power)

        return metrics

    def modulate_band(self, band_name: str, amplitude_factor: float):
        """
        Modulate a specific band's amplitude.

        Args:
            band_name: Name of band to modulate
            amplitude_factor: Multiplicative factor
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
                band.freq_range = (frequency - width/2, frequency + width/2)

    def get_spectral_power(self) -> Dict[str, float]:
        """Get current spectral power in each band."""
        return {name: float(band.power) for name, band in self.bands.items()}

    def detect_gamma_burst(self, threshold: float = 0.5) -> bool:
        """
        Detect gamma burst (associated with conscious access).

        Args:
            threshold: Power threshold for detection

        Returns:
            True if gamma burst detected
        """
        if 'gamma' in self.bands:
            return self.bands['gamma'].power > threshold
        return False

    def reset(self):
        """Reset oscillation engine."""
        for band in self.bands.values():
            band.phase = np.random.rand() * 2 * np.pi
            band.power = 0.0

        self.time = 0.0
        self.signal_history = []
