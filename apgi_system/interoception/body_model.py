"""
Body State Model

Simulates physiological states and generates interoceptive predictions.
"""

import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from apgi_system.validation import InputValidator
from apgi_system.types import FloatArray, ConfigDict, BodyState


@dataclass
class PhysiologicalState:
    """Complete physiological state."""
    heart_rate: float  # bpm
    respiration: float  # breaths per minute
    temperature: float  # Celsius
    glucose: float  # mmol/L
    cortisol: float  # μg/dL
    blood_pressure: float  # mmHg (systolic)


class BodyModel:
    """
    Multi-organ physiological model for interoceptive processing.

    The BodyModel simulates physiological states across multiple organ systems
    and generates interoceptive predictions for active inference. It maintains
    current body states and generates forward predictions to enable prediction
    error computation for interoceptive processing.

    The model tracks six key physiological variables:
    - Cardiovascular: heart rate (bpm) and blood pressure (mmHg)
    - Respiratory: respiration rate (breaths per minute)
    - Thermoregulation: body temperature (Celsius)
    - Metabolic: blood glucose (mmol/L)
    - Stress: cortisol levels (μg/dL)

    Each variable follows simplified linear dynamics with configurable time
    constants and is influenced by arousal, activity, and stress levels.
    Predictions are generated 50-200ms ahead for comparison with afferent signals.

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing interoception settings including:
        - body_states: List of state configurations with baselines and ranges
        - prediction_lead_ms: Prediction horizon in milliseconds (default: 100)

    Attributes
    ----------
    current_state : PhysiologicalState
        Current physiological state across all tracked variables
    predicted_state : PhysiologicalState
        Predicted future state at prediction_lead_ms ahead
    arousal_level : float
        Current arousal level (0-1), affects heart rate and cortisol
    activity_level : float
        Current activity level (0-1), affects heart rate, respiration, glucose
    stress_level : float
        Current stress level (0-1), affects cortisol and blood pressure
    prediction_lead_ms : float
        Time horizon for predictions in milliseconds

    Examples
    --------
    >>> config = {'interoception': {'prediction_lead_ms': 100}}
    >>> body_model = BodyModel(config)
    >>> body_model.set_arousal(0.5)
    >>> result = body_model.update(dt=1.0)
    >>> print(result['current']['heart_rate'])
    75.2
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize body model with configuration.

        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary containing interoception settings
        """
        self.config = config
        intero_config = config.get('interoception', {})
        body_states_config = intero_config.get('body_states', [])

        # Parse body state configurations
        self.state_configs = {}
        for state_dict in body_states_config:
            for name, cfg in state_dict.items():
                self.state_configs[name] = cfg

        # Current state
        self.current_state = PhysiologicalState(
            heart_rate=self.state_configs.get('heart_rate', {}).get('baseline', 70),
            respiration=self.state_configs.get('respiration', {}).get('baseline', 15),
            temperature=self.state_configs.get('temperature', {}).get('baseline', 37.0),
            glucose=self.state_configs.get('glucose', {}).get('baseline', 5.0),
            cortisol=self.state_configs.get('cortisol', {}).get('baseline', 10),
            blood_pressure=120  # Default
        )

        # Predicted state (prediction_lead_ms ahead)
        self.prediction_lead_ms = intero_config.get('prediction_lead_ms', 100)
        self.predicted_state = PhysiologicalState(
            heart_rate=self.current_state.heart_rate,
            respiration=self.current_state.respiration,
            temperature=self.current_state.temperature,
            glucose=self.current_state.glucose,
            cortisol=self.current_state.cortisol,
            blood_pressure=self.current_state.blood_pressure
        )

        # Dynamics parameters (simplified linear dynamics)
        self.tau_heart = 1000.0  # ms, heart rate time constant
        self.tau_respiration = 2000.0  # ms
        self.tau_temperature = 10000.0  # ms (very slow)
        self.tau_glucose = 5000.0  # ms
        self.tau_cortisol = 30000.0  # ms (slow)

        # External influences
        self.arousal_level = 0.0  # 0-1, affects HR and cortisol
        self.activity_level = 0.0  # 0-1, affects HR, respiration, glucose
        self.stress_level = 0.0  # 0-1, affects cortisol

    def update(self, dt: float = 1.0) -> Dict[str, Any]:
        """
        Update body state and generate predictions.

        Performs a complete update cycle:
        1. Updates all physiological variables using their dynamics
        2. Generates forward predictions at prediction_lead_ms horizon
        3. Computes prediction errors (simulated)

        Each physiological variable evolves according to:
        - Target value based on arousal, activity, and stress
        - Time constant governing rate of change
        - Gaussian noise representing natural variability

        Parameters
        ----------
        dt : float, optional
            Timestep in milliseconds, by default 1.0

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - 'current': Current physiological state (all variables)
            - 'predicted': Predicted future state
            - 'prediction_error': Prediction error vector (5D)
            - 'arousal': Current arousal level
            - 'activity': Current activity level
            - 'stress': Current stress level

        Examples
        --------
        >>> body_model = BodyModel(config)
        >>> result = body_model.update(dt=1.0)
        >>> print(result['current']['heart_rate'])
        70.5
        >>> print(result['prediction_error'].shape)
        (5,)
        """
        # Validate inputs
        InputValidator.validate_scalar(
            dt, 
            "dt", 
            value_range=(0.0, 10000.0),
            positive=True
        )
        
        # Update current state
        self._update_heart_rate(dt)
        self._update_respiration(dt)
        self._update_temperature(dt)
        self._update_glucose(dt)
        self._update_cortisol(dt)
        self._update_blood_pressure(dt)

        # Generate prediction (lead time ahead)
        self._generate_prediction()

        # Compute prediction error
        prediction_error = self._compute_prediction_error()

        return {
            'current': self._state_to_dict(self.current_state),
            'predicted': self._state_to_dict(self.predicted_state),
            'prediction_error': prediction_error,
            'arousal': self.arousal_level,
            'activity': self.activity_level,
            'stress': self.stress_level
        }

    def _update_heart_rate(self, dt: float):
        """
        Update heart rate dynamics.

        Heart rate evolves toward a target determined by arousal and activity:
        target_hr = baseline + 30 * arousal + 50 * activity

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = self.state_configs.get('heart_rate', {}).get('baseline', 70)

        # Target heart rate depends on arousal and activity
        target_hr = baseline + 30 * self.arousal_level + 50 * self.activity_level

        # Clamp to range
        hr_range = self.state_configs.get('heart_rate', {}).get('range', [50, 120])
        target_hr = np.clip(target_hr, hr_range[0], hr_range[1])

        # Update with time constant
        dhr = (dt / self.tau_heart) * (target_hr - self.current_state.heart_rate)
        self.current_state.heart_rate += dhr

        # Add noise
        noise_std = self.state_configs.get('heart_rate', {}).get('variance', 5)
        self.current_state.heart_rate += np.random.randn() * noise_std * np.sqrt(dt/1000.0)

    def _update_respiration(self, dt: float):
        """
        Update respiration rate dynamics.

        Respiration rate evolves toward a target determined by arousal and activity:
        target_rr = baseline + 5 * arousal + 10 * activity

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = self.state_configs.get('respiration', {}).get('baseline', 15)
        target_rr = baseline + 5 * self.arousal_level + 10 * self.activity_level

        rr_range = self.state_configs.get('respiration', {}).get('range', [10, 30])
        target_rr = np.clip(target_rr, rr_range[0], rr_range[1])

        drr = (dt / self.tau_respiration) * (target_rr - self.current_state.respiration)
        self.current_state.respiration += drr

        noise_std = self.state_configs.get('respiration', {}).get('variance', 2)
        self.current_state.respiration += np.random.randn() * noise_std * np.sqrt(dt/1000.0)

    def _update_temperature(self, dt: float):
        """
        Update body temperature dynamics.

        Temperature evolves slowly toward a target influenced by activity:
        target_temp = baseline + 0.5 * activity

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = self.state_configs.get('temperature', {}).get('baseline', 37.0)
        target_temp = baseline + 0.5 * self.activity_level

        temp_range = self.state_configs.get('temperature', {}).get('range', [36.0, 39.0])
        target_temp = np.clip(target_temp, temp_range[0], temp_range[1])

        dtemp = (dt / self.tau_temperature) * (target_temp - self.current_state.temperature)
        self.current_state.temperature += dtemp

        noise_std = self.state_configs.get('temperature', {}).get('variance', 0.2)
        self.current_state.temperature += np.random.randn() * noise_std * np.sqrt(dt/1000.0)

    def _update_glucose(self, dt: float):
        """
        Update blood glucose dynamics.

        Glucose evolves toward a target that decreases with activity:
        target_glucose = baseline - 1.0 * activity

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = self.state_configs.get('glucose', {}).get('baseline', 5.0)
        # Activity decreases glucose, baseline otherwise
        target_glucose = baseline - 1.0 * self.activity_level

        glucose_range = self.state_configs.get('glucose', {}).get('range', [3.0, 8.0])
        target_glucose = np.clip(target_glucose, glucose_range[0], glucose_range[1])

        dglucose = (dt / self.tau_glucose) * (target_glucose - self.current_state.glucose)
        self.current_state.glucose += dglucose

        noise_std = self.state_configs.get('glucose', {}).get('variance', 0.5)
        self.current_state.glucose += np.random.randn() * noise_std * np.sqrt(dt/1000.0)

    def _update_cortisol(self, dt: float):
        """
        Update cortisol level dynamics.

        Cortisol evolves slowly toward a target influenced by stress and arousal:
        target_cortisol = baseline + 15 * stress + 5 * arousal

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = self.state_configs.get('cortisol', {}).get('baseline', 10)
        target_cortisol = baseline + 15 * self.stress_level + 5 * self.arousal_level

        cortisol_range = self.state_configs.get('cortisol', {}).get('range', [5, 30])
        target_cortisol = np.clip(target_cortisol, cortisol_range[0], cortisol_range[1])

        dcortisol = (dt / self.tau_cortisol) * (target_cortisol - self.current_state.cortisol)
        self.current_state.cortisol += dcortisol

        noise_std = self.state_configs.get('cortisol', {}).get('variance', 3)
        self.current_state.cortisol += np.random.randn() * noise_std * np.sqrt(dt/1000.0)

    def _update_blood_pressure(self, dt: float):
        """
        Update blood pressure dynamics.

        Blood pressure evolves toward a target influenced by arousal and stress:
        target_bp = baseline + 20 * arousal + 10 * stress

        Parameters
        ----------
        dt : float
            Timestep in milliseconds
        """
        baseline = 120
        target_bp = baseline + 20 * self.arousal_level + 10 * self.stress_level

        target_bp = np.clip(target_bp, 90, 160)

        dbp = (dt / self.tau_heart) * (target_bp - self.current_state.blood_pressure)
        self.current_state.blood_pressure += dbp

        self.current_state.blood_pressure += np.random.randn() * 5 * np.sqrt(dt/1000.0)

    def _generate_prediction(self):
        """
        Generate prediction for future state.

        Simple forward model that predicts the state will continue its current
        trajectory. In a more sophisticated implementation, this would use
        learned dynamics models to predict future states based on current
        trends and external influences.

        Currently implements a naive prediction where predicted_state equals
        current_state (assumes stability over the prediction horizon).
        """
        # For simplicity, predict based on current trend
        # In a more sophisticated model, this would use learned dynamics

        self.predicted_state.heart_rate = self.current_state.heart_rate
        self.predicted_state.respiration = self.current_state.respiration
        self.predicted_state.temperature = self.current_state.temperature
        self.predicted_state.glucose = self.current_state.glucose
        self.predicted_state.cortisol = self.current_state.cortisol
        self.predicted_state.blood_pressure = self.current_state.blood_pressure

    def _compute_prediction_error(self) -> np.ndarray:
        """
        Compute prediction error between predicted and actual states.

        In a complete implementation, this would compare predictions against
        actual afferent signals from the body. Here we simulate small random
        errors to represent the natural variability in interoceptive signals.

        Returns
        -------
        np.ndarray
            5D prediction error vector for [heart_rate, respiration,
            temperature, glucose, cortisol]
        """
        error = np.array([
            np.random.randn() * 2,  # Heart rate error
            np.random.randn() * 1,  # Respiration error
            np.random.randn() * 0.1,  # Temperature error
            np.random.randn() * 0.2,  # Glucose error
            np.random.randn() * 1,  # Cortisol error
        ])

        return error

    def set_arousal(self, level: float):
        """
        Set arousal level.

        Arousal affects heart rate and cortisol levels. Higher arousal
        increases both variables.

        Parameters
        ----------
        level : float
            Arousal level, clamped to range [0.0, 1.0]
        """
        self.arousal_level = np.clip(level, 0.0, 1.0)

    def set_activity(self, level: float):
        """
        Set activity level.

        Activity affects heart rate, respiration, temperature, and glucose.
        Higher activity increases heart rate, respiration, and temperature
        while decreasing glucose.

        Parameters
        ----------
        level : float
            Activity level, clamped to range [0.0, 1.0]
        """
        self.activity_level = np.clip(level, 0.0, 1.0)

    def set_stress(self, level: float):
        """
        Set stress level.

        Stress affects cortisol and blood pressure. Higher stress increases
        both variables.

        Parameters
        ----------
        level : float
            Stress level, clamped to range [0.0, 1.0]
        """
        self.stress_level = np.clip(level, 0.0, 1.0)

    def get_interoceptive_vector(self) -> np.ndarray:
        """
        Get current interoceptive state as vector.

        Returns the current physiological state as a 6D vector suitable for
        use in active inference computations.

        Returns
        -------
        np.ndarray
            6D vector containing [heart_rate, respiration, temperature,
            glucose, cortisol, blood_pressure]

        Examples
        --------
        >>> body_model = BodyModel(config)
        >>> vector = body_model.get_interoceptive_vector()
        >>> print(vector.shape)
        (6,)
        """
        return np.array([
            self.current_state.heart_rate,
            self.current_state.respiration,
            self.current_state.temperature,
            self.current_state.glucose,
            self.current_state.cortisol,
            self.current_state.blood_pressure
        ])

    def _state_to_dict(self, state: PhysiologicalState) -> Dict[str, float]:
        """
        Convert physiological state to dictionary.

        Parameters
        ----------
        state : PhysiologicalState
            State object to convert

        Returns
        -------
        Dict[str, float]
            Dictionary mapping variable names to values
        """
        return {
            'heart_rate': float(state.heart_rate),
            'respiration': float(state.respiration),
            'temperature': float(state.temperature),
            'glucose': float(state.glucose),
            'cortisol': float(state.cortisol),
            'blood_pressure': float(state.blood_pressure)
        }

    def reset(self):
        """
        Reset to baseline physiological state.

        Restores all physiological variables to their configured baseline
        values and resets arousal, activity, and stress levels to zero.
        """
        self.current_state = PhysiologicalState(
            heart_rate=self.state_configs.get('heart_rate', {}).get('baseline', 70),
            respiration=self.state_configs.get('respiration', {}).get('baseline', 15),
            temperature=self.state_configs.get('temperature', {}).get('baseline', 37.0),
            glucose=self.state_configs.get('glucose', {}).get('baseline', 5.0),
            cortisol=self.state_configs.get('cortisol', {}).get('baseline', 10),
            blood_pressure=120
        )

        self.predicted_state = PhysiologicalState(
            heart_rate=self.current_state.heart_rate,
            respiration=self.current_state.respiration,
            temperature=self.current_state.temperature,
            glucose=self.current_state.glucose,
            cortisol=self.current_state.cortisol,
            blood_pressure=self.current_state.blood_pressure
        )

        self.arousal_level = 0.0
        self.activity_level = 0.0
        self.stress_level = 0.0
