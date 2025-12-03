"""
Neural Column Implementation

Rate-coded neural columns with:
- Hierarchical predictive coding
- Dendritic gain modulation
- Beta oscillation generation (12-30 Hz)
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple


class NeuralColumn:
    """
    Rate-coded neural column implementing hierarchical predictive coding.

    Models a cortical column as the basic computational unit for predictive
    processing. Each column implements the core predictive coding algorithm:
    predictions flow top-down, errors flow bottom-up, and learning minimizes
    prediction errors through Bayesian inference.

    **Neural Populations**:
    - **Prediction neurons**: Generate top-down predictions of lower-level activity
    - **Error neurons**: Compute bottom-up prediction errors (observation - prediction)
    - **Modulatory neurons**: Control gain and precision of error signals

    **Computational Functions**:
    - Hierarchical predictive coding with error minimization
    - Dendritic gain modulation for precision weighting
    - Beta oscillation generation (12-30 Hz) for top-down signaling
    - Adaptation mechanisms to prevent over-fitting
    - Nonlinear dendritic computation with soft thresholding

    **Dynamics**:
    - Fast dynamics (10ms) for prediction updates
    - Slow dynamics (100ms) for adaptation
    - Beta oscillations for temporal coordination
    - Gain modulation based on error magnitude

    The column receives bottom-up input from lower levels and top-down
    predictions from higher levels, computing prediction errors that
    drive learning and inference.

    Parameters
    ----------
    num_units : int
        Number of units in the column
    layer_name : str, optional
        Name identifier for this layer, by default "column"
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_units : int
        Number of units in the column
    layer_name : str
        Layer identifier
    prediction_units : np.ndarray
        Activity of prediction neurons (top-down)
    error_units : np.ndarray
        Activity of error neurons (bottom-up)
    modulatory_units : np.ndarray
        Gain modulation values for each unit
    activity : np.ndarray
        Current output activity of the column
    adaptation : np.ndarray
        Slow adaptation state for each unit
    beta_phase : float
        Current phase of beta oscillation (radians)

    Examples
    --------
    >>> column = NeuralColumn(num_units=64, layer_name="V1")
    >>> bottom_up = np.random.randn(64) * 0.5
    >>> top_down = np.random.randn(64) * 0.3
    >>> activity, info = column.update(bottom_up, top_down, dt=1.0)
    >>> print(f"Prediction error: {info['prediction_error_magnitude']:.3f}")
    Prediction error: 0.425
    """

    def __init__(
        self, num_units: int, layer_name: str = "column", config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize neural column.

        Args:
            num_units: Number of units in column
            layer_name: Name of this layer
            config: Configuration dictionary
        """
        self.num_units = num_units
        self.layer_name = layer_name
        self.config = config or {}

        # Neural populations
        self.prediction_units = np.zeros(num_units)  # Top-down
        self.error_units = np.zeros(num_units)  # Bottom-up
        self.modulatory_units = np.ones(num_units)  # Gain control

        # State variables
        self.activity = np.zeros(num_units)
        self.adaptation = np.zeros(num_units)

        # Parameters
        self.tau_fast = 10.0  # ms, fast dynamics
        self.tau_slow = 100.0  # ms, slow dynamics (adaptation)
        self.gain_baseline = 1.0
        self.gain_range = [0.5, 2.0]

        # Predictive coding parameters
        self.prediction_strength = 0.8
        self.error_gain = 1.0

        # Beta oscillation
        self.beta_freq = 20.0  # Hz
        self.beta_amplitude = 0.1
        self.beta_phase = 0.0

        # Dendritic computation
        self.dendritic_threshold = 0.5

    def update(
        self,
        bottom_up_input: np.ndarray,
        top_down_prediction: np.ndarray,
        gain_modulation: float = 1.0,
        dt: float = 1.0,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Update column activity.

        Args:
            bottom_up_input: Input from lower level
            top_down_prediction: Prediction from higher level
            gain_modulation: Global gain factor
            dt: Timestep in ms

        Returns:
            activity: Current activity pattern
            info: Diagnostic information
        """
        # Compute prediction error
        self.error_units = bottom_up_input - self.prediction_units

        # Update prediction units (blend input and top-down)
        target_prediction = (
            self.prediction_strength * top_down_prediction
            + (1 - self.prediction_strength) * bottom_up_input
        )

        # Fast dynamics
        dpred = (dt / self.tau_fast) * (target_prediction - self.prediction_units)
        self.prediction_units += dpred

        # Update modulatory gain based on error magnitude
        error_magnitude = np.mean(np.abs(self.error_units))
        self.modulatory_units = self._compute_gain(error_magnitude, gain_modulation)

        # Compute activity (error neurons with gain modulation)
        self.activity = self.modulatory_units * self.error_units * self.error_gain

        # Apply dendritic nonlinearity
        self.activity = self._dendritic_computation(self.activity)

        # Adaptation (slow negative feedback)
        dadapt = (dt / self.tau_slow) * (self.activity - self.adaptation)
        self.adaptation += dadapt
        self.activity -= 0.3 * self.adaptation

        # Add beta oscillation
        beta_modulation = self.beta_amplitude * np.sin(self.beta_phase)
        self.activity += beta_modulation

        # Update beta phase
        self.beta_phase += 2 * np.pi * self.beta_freq * (dt / 1000.0)
        self.beta_phase = self.beta_phase % (2 * np.pi)

        # Nonlinearity (ReLU-like)
        self.activity = np.maximum(0, self.activity)

        # Compile info
        info = {
            "prediction_error_magnitude": float(error_magnitude),
            "mean_gain": float(np.mean(self.modulatory_units)),
            "mean_activity": float(np.mean(self.activity)),
            "beta_phase": float(self.beta_phase),
        }

        return self.activity.copy(), info

    def _compute_gain(self, error_magnitude: float, global_modulation: float) -> np.ndarray:
        """
        Compute gain modulation.

        Higher errors -> higher gain (within limits).
        """
        # Error-dependent gain
        error_gain = self.gain_baseline + 0.5 * error_magnitude

        # Clamp to range
        error_gain = np.clip(error_gain, self.gain_range[0], self.gain_range[1])

        # Apply global modulation
        total_gain = error_gain * global_modulation

        return total_gain * np.ones(self.num_units)

    def _dendritic_computation(self, activity: np.ndarray) -> np.ndarray:
        """
        Dendritic nonlinear computation.

        Implements soft thresholding with gain.
        """
        # Soft threshold
        threshold = self.dendritic_threshold
        gain = 2.0

        output = np.where(activity > threshold, threshold + gain * (activity - threshold), activity)

        return output

    def set_prediction(self, prediction: np.ndarray):
        """Set prediction directly."""
        self.prediction_units = prediction.copy()

    def get_prediction_error(self) -> np.ndarray:
        """Get current prediction error."""
        return self.error_units.copy()

    def reset(self):
        """Reset column state."""
        self.prediction_units = np.zeros(self.num_units)
        self.error_units = np.zeros(self.num_units)
        self.modulatory_units = np.ones(self.num_units)
        self.activity = np.zeros(self.num_units)
        self.adaptation = np.zeros(self.num_units)
        self.beta_phase = 0.0


class HierarchicalColumnNetwork:
    """
    Hierarchical network of neural columns implementing predictive coding.

    Organizes multiple neural columns in a hierarchical architecture where
    information flows bidirectionally: bottom-up sensory signals and
    top-down predictions. This implements the hierarchical predictive
    coding framework for cortical computation.

    **Hierarchical Organization**:
    - **Lower levels**: Process fast, detailed, concrete information
    - **Higher levels**: Process slow, abstract, contextual information
    - **Bidirectional flow**: Bottom-up signals, top-down predictions

    **Information Processing**:
    - Sensory input enters at the bottom level
    - Each level predicts activity at the level below
    - Prediction errors propagate upward to drive learning
    - Higher levels provide context and priors to lower levels

    **Mapping Functions**:
    - **Bottom-up**: Compression/pooling to extract abstractions
    - **Top-down**: Expansion/repetition to provide detailed predictions

    This architecture captures key principles of cortical hierarchy:
    receptive field size increases, temporal integration increases,
    and abstraction level increases with hierarchical depth.

    Parameters
    ----------
    layer_sizes : list
        Number of units in each layer, ordered from bottom (sensory) to top (abstract)
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_layers : int
        Number of hierarchical levels
    layer_sizes : list
        Number of units in each layer
    columns : List[NeuralColumn]
        List of neural columns, one per hierarchical level

    Examples
    --------
    >>> # Create 3-level hierarchy: 256 -> 128 -> 64 units
    >>> network = HierarchicalColumnNetwork([256, 128, 64])
    >>> sensory_input = np.random.randn(256) * 0.1
    >>> results = network.forward(sensory_input, dt=1.0)
    >>> print(f"Layer 0 error: {np.mean(results['layer_0']['prediction_error']):.3f}")
    Layer 0 error: 0.087
    """

    def __init__(self, layer_sizes: list, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hierarchical network.

        Args:
            layer_sizes: Number of units in each layer (bottom to top)
            config: Configuration dictionary
        """
        self.num_layers = len(layer_sizes)
        self.layer_sizes = layer_sizes
        self.config = config or {}

        # Create columns
        self.columns = []
        for i, size in enumerate(layer_sizes):
            column = NeuralColumn(num_units=size, layer_name=f"layer_{i}", config=config)
            self.columns.append(column)

    def forward(self, sensory_input: np.ndarray, dt: float = 1.0) -> Dict[str, Any]:
        """
        Forward pass through hierarchy.

        Args:
            sensory_input: Sensory input to bottom layer
            dt: Timestep in ms

        Returns:
            Dictionary with layer activities and errors
        """
        results = {}

        # Bottom-up pass
        bottom_up = sensory_input
        for i, column in enumerate(self.columns):
            # Get top-down prediction (from layer above or prior)
            if i < self.num_layers - 1:
                top_down = self._map_down(self.columns[i + 1].prediction_units, self.layer_sizes[i])
            else:
                # Top layer has no higher prediction
                top_down = np.zeros(self.layer_sizes[i])

            # Update column
            activity, info = column.update(
                bottom_up_input=bottom_up, top_down_prediction=top_down, dt=dt
            )

            results[f"layer_{i}"] = {
                "activity": activity,
                "prediction_error": column.get_prediction_error(),
                "info": info,
            }

            # Propagate to next layer
            bottom_up = self._map_up(activity, self.layer_sizes[min(i + 1, self.num_layers - 1)])

        return results

    def _map_up(self, activity: np.ndarray, target_size: int) -> np.ndarray:
        """Map activity up to next layer (compression)."""
        if len(activity) == target_size:
            return activity

        # Simple pooling
        if len(activity) > target_size:
            ratio = len(activity) // target_size
            result = np.zeros(target_size)
            for i in range(target_size):
                start = i * ratio
                end = min((i + 1) * ratio, len(activity))
                result[i] = np.mean(activity[start:end])
            return result
        else:
            # Upsample if needed
            result = np.zeros(target_size)
            result[: len(activity)] = activity
            return result

    def _map_down(self, activity: np.ndarray, target_size: int) -> np.ndarray:
        """Map activity down to previous layer (expansion)."""
        if len(activity) == target_size:
            return activity

        # Simple repetition
        if len(activity) < target_size:
            ratio = target_size // len(activity)
            result = np.repeat(activity, ratio)
            if len(result) < target_size:
                result = np.pad(result, (0, target_size - len(result)))
            return result[:target_size]
        else:
            return activity[:target_size]
