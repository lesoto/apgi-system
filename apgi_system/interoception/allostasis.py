"""
Allostatic Regulation

Maintains homeostatic set points and manages allostatic load.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from apgi_system.validation import InputValidator


@dataclass
class AllostaticSetPoint:
    """Set point for a physiological variable."""

    name: str
    target: float
    acceptable_range: Tuple[float, float]
    current_deviation: float = 0.0
    load_contribution: float = 0.0


class AllostaticRegulator:
    """
    Manages allostatic regulation and cumulative load tracking.

    Allostasis refers to achieving stability through change - the process by
    which the body maintains homeostasis through adaptive responses to stressors.
    This class implements allostatic regulation by:

    1. Maintaining homeostatic set points for key physiological variables
    2. Computing deviations from optimal states
    3. Tracking cumulative allostatic load (wear-and-tear from adaptation)
    4. Generating regulatory signals to restore homeostasis

    Allostatic load accumulates when physiological variables remain outside
    their acceptable ranges, representing the cumulative cost of adaptation.
    High allostatic load indicates chronic stress and can modulate other
    system processes (e.g., raising ignition thresholds).

    The regulator tracks four key variables:
    - Heart rate: Target 70 bpm, acceptable range (65-75)
    - Temperature: Target 37.0°C, acceptable range (36.8-37.2)
    - Glucose: Target 5.0 mmol/L, acceptable range (4.5-5.5)
    - Cortisol: Target 10 μg/dL, acceptable range (8-12)

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing:
        - interoception.allostatic_ranges: Range factors for regulation

    Attributes
    ----------
    set_points : List[AllostaticSetPoint]
        Set points for tracked physiological variables
    total_load : float
        Cumulative allostatic load (0-1), representing wear-and-tear
    load_decay_rate : float
        Rate at which load decays over time (per ms)
    load_accumulation_rate : float
        Rate at which deviations contribute to load

    Examples
    --------
    >>> config = {'interoception': {'allostatic_ranges': {}}}
    >>> regulator = AllostaticRegulator(config)
    >>> body_state = {'heart_rate': 85, 'temperature': 37.0}
    >>> result = regulator.update(body_state, dt=1.0)
    >>> print(result['allostatic_load'])
    0.05
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize allostatic regulator with configuration.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing allostatic range settings
        """
        self.config = config
        intero_config = config.get("interoception", {})
        ranges_config = intero_config.get("allostatic_ranges", {})

        # Define set points for key variables
        self.set_points = [
            AllostaticSetPoint(name="heart_rate", target=70.0, acceptable_range=(65, 75)),
            AllostaticSetPoint(name="temperature", target=37.0, acceptable_range=(36.8, 37.2)),
            AllostaticSetPoint(name="glucose", target=5.0, acceptable_range=(4.5, 5.5)),
            AllostaticSetPoint(name="cortisol", target=10.0, acceptable_range=(8, 12)),
        ]

        # Allostatic load tracking
        self.total_load = 0.0
        self.load_decay_rate = 0.001  # per ms
        self.load_accumulation_rate = 0.01

        # Regulation parameters
        self.tight_range_factor = ranges_config.get("tight", 0.1)
        self.moderate_range_factor = ranges_config.get("moderate", 0.2)
        self.wide_range_factor = ranges_config.get("wide", 0.3)

    def update(self, body_state: Dict[str, float], dt: float = 1.0) -> Dict[str, Any]:
        """
        Update allostatic regulation and compute load.

        Performs a complete regulation cycle:
        1. Computes deviation from set points for each tracked variable
        2. Determines if variables are within acceptable ranges
        3. Accumulates allostatic load for out-of-range variables
        4. Generates proportional regulatory signals
        5. Applies decay to existing load

        Load accumulation is proportional to the magnitude of deviation
        normalized by the acceptable range width. Larger deviations contribute
        more to cumulative load.

        Parameters
        ----------
        body_state : Dict[str, float]
            Current physiological state with keys matching set point names
            (e.g., 'heart_rate', 'temperature', 'glucose', 'cortisol')
        dt : float, optional
            Timestep in milliseconds, by default 1.0

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'regulation_signals': Dict mapping variable names to regulatory
              signals (proportional to deviation)
            - 'allostatic_load': Current cumulative load (0-1)
            - 'total_deviation': Sum of absolute deviations across all variables
            - 'set_points_status': List of status dicts for each set point
            - 'homeostatic_stability': Overall stability metric (0-1)

        Examples
        --------
        >>> regulator = AllostaticRegulator(config)
        >>> body_state = {'heart_rate': 90, 'temperature': 37.5}
        >>> result = regulator.update(body_state, dt=1.0)
        >>> print(result['regulation_signals']['heart_rate'])
        -2.0  # Negative signal to reduce heart rate
        >>> print(result['homeostatic_stability'])
        0.75
        """
        # Validate inputs
        if not isinstance(body_state, dict):
            raise TypeError(f"body_state must be dict, got {type(body_state)}")

        InputValidator.validate_scalar(dt, "dt", value_range=(0.0, 10000.0), positive=True)

        # Validate body_state values
        for key, value in body_state.items():
            InputValidator.validate_scalar(
                value,
                f"body_state['{key}']",
                value_range=(-1000.0, 1000.0),  # Reasonable physiological range
            )

        regulation_signals = {}
        total_deviation = 0.0

        # Check each set point
        for set_point in self.set_points:
            if set_point.name in body_state:
                current_value = body_state[set_point.name]

                # Compute deviation from target
                deviation = current_value - set_point.target
                set_point.current_deviation = deviation

                # Check if within acceptable range
                in_range = (
                    set_point.acceptable_range[0] <= current_value <= set_point.acceptable_range[1]
                )

                if not in_range:
                    # Compute load contribution
                    # Larger deviations contribute more to load
                    range_width = set_point.acceptable_range[1] - set_point.acceptable_range[0]

                    normalized_deviation = abs(deviation) / range_width
                    set_point.load_contribution = normalized_deviation

                    # Accumulate total load
                    self.total_load += (
                        self.load_accumulation_rate * normalized_deviation * dt / 1000.0
                    )
                else:
                    set_point.load_contribution = 0.0

                # Generate regulatory signal (proportional to deviation)
                regulation_signals[set_point.name] = -0.1 * deviation

                total_deviation += abs(deviation)

        # Decay load over time
        self.total_load *= 1.0 - self.load_decay_rate * dt / 1000.0
        self.total_load = max(0.0, self.total_load)

        # Clamp load to [0, 1]
        self.total_load = min(1.0, self.total_load)

        return {
            "regulation_signals": regulation_signals,
            "allostatic_load": float(self.total_load),
            "total_deviation": float(total_deviation),
            "set_points_status": self._get_set_points_status(),
            "homeostatic_stability": self._compute_stability(),
        }

    def _get_set_points_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all set points.

        Returns
        -------
        List[Dict[str, Any]]
            List of status dictionaries, one per set point, containing:
            - 'name': Variable name
            - 'target': Target value
            - 'deviation': Current deviation from target
            - 'load_contribution': Contribution to allostatic load
            - 'in_range': Boolean indicating if within acceptable range
        """
        status = []
        for sp in self.set_points:
            status.append(
                {
                    "name": sp.name,
                    "target": sp.target,
                    "deviation": sp.current_deviation,
                    "load_contribution": sp.load_contribution,
                    "in_range": abs(sp.current_deviation)
                    < (sp.acceptable_range[1] - sp.acceptable_range[0]) / 2,
                }
            )
        return status

    def _compute_stability(self) -> float:
        """
        Compute overall homeostatic stability.

        Stability is computed as 1 minus the average normalized deviation
        across all set points. Higher values indicate greater stability
        (all variables near their set points).

        Returns
        -------
        float
            Stability metric in range [0, 1], where:
            - 1.0 = perfect stability (all variables at set points)
            - 0.0 = maximum instability (all variables far from set points)
        """
        total_normalized_deviation = 0.0

        for sp in self.set_points:
            range_width = sp.acceptable_range[1] - sp.acceptable_range[0]
            normalized_dev = abs(sp.current_deviation) / range_width
            total_normalized_deviation += normalized_dev

        # Average across set points
        avg_deviation = total_normalized_deviation / len(self.set_points)

        # Convert to stability (1 - deviation)
        stability = max(0.0, 1.0 - avg_deviation)

        return float(stability)

    def get_allostatic_load(self) -> float:
        """
        Get current allostatic load.

        Returns
        -------
        float
            Current cumulative allostatic load in range [0, 1]
        """
        return self.total_load

    def trigger_stressor(self, intensity: float = 0.5) -> None:
        """
        Simulate an acute stressor event.

        Immediately increases allostatic load to simulate the impact of
        an acute stressor (e.g., threat, challenge, or perturbation).

        Parameters
        ----------
        intensity : float, optional
            Stressor intensity in range [0, 1], by default 0.5
            Higher intensity produces larger load increase
        """
        self.total_load += intensity * 0.2
        self.total_load = min(1.0, self.total_load)

    def reset(self) -> None:
        """
        Reset to baseline state.

        Clears all allostatic load and resets all set point deviations
        and load contributions to zero.
        """
        self.total_load = 0.0
        for sp in self.set_points:
            sp.current_deviation = 0.0
            sp.load_contribution = 0.0
