"""
Custom Hypothesis strategies for APGI system data types.

This module provides strategies for generating valid test data for
property-based testing of the APGI system components.
"""

from hypothesis import strategies as st
import numpy as np


@st.composite
def body_state_strategy(draw):
    """
    Generate valid physiological body states.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    dict
        Dictionary containing physiological variables within valid ranges.
        
    Notes
    -----
    All values are constrained to physiologically plausible ranges:
    - heart_rate: 50-120 bpm
    - cortisol: 5-30 μg/dL
    - temperature: 36.0-39.0°C
    - glucose: 3.0-8.0 mmol/L
    - respiration: 10-30 breaths/min
    - systolic_bp: 90-160 mmHg
    """
    return {
        'heart_rate': draw(st.floats(min_value=50.0, max_value=120.0)),
        'cortisol': draw(st.floats(min_value=5.0, max_value=30.0)),
        'temperature': draw(st.floats(min_value=36.0, max_value=39.0)),
        'glucose': draw(st.floats(min_value=3.0, max_value=8.0)),
        'respiration': draw(st.floats(min_value=10.0, max_value=30.0)),
        'systolic_bp': draw(st.floats(min_value=90.0, max_value=160.0))
    }


@st.composite
def observation_strategy(draw, dim=256):
    """
    Generate valid observation vectors.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
    dim : int, optional
        Dimensionality of observation vector, by default 256.
        
    Returns
    -------
    np.ndarray
        Observation vector of shape (dim,) with values in reasonable range.
        
    Notes
    -----
    Values are constrained to [-10, 10] to represent typical sensory
    input magnitudes and avoid numerical instability.
    """
    values = draw(st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=dim,
        max_size=dim
    ))
    return np.array(values, dtype=np.float64)


@st.composite
def belief_state_strategy(draw, num_levels=4, level_dims=None):
    """
    Generate valid belief states for hierarchical inference.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
    num_levels : int, optional
        Number of hierarchical levels, by default 4.
    level_dims : list of int, optional
        Dimensions for each level. If None, uses [256, 128, 64, 32].
        
    Returns
    -------
    list of dict
        List of belief dictionaries, one per level, each containing:
        - 'mean': np.ndarray of shape (level_dim,)
        - 'precision': float > 0
        - 'prediction_error': np.ndarray of shape (level_dim,)
        
    Notes
    -----
    Belief means and errors are constrained to [-5, 5] for numerical stability.
    Precision values are constrained to [0.1, 10.0] for realistic uncertainty.
    """
    if level_dims is None:
        level_dims = [256, 128, 64, 32][:num_levels]
    
    beliefs = []
    for dim in level_dims:
        mean_values = draw(st.lists(
            st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=dim,
            max_size=dim
        ))
        error_values = draw(st.lists(
            st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=dim,
            max_size=dim
        ))
        precision = draw(st.floats(min_value=0.1, max_value=10.0))
        
        beliefs.append({
            'mean': np.array(mean_values, dtype=np.float64),
            'precision': precision,
            'prediction_error': np.array(error_values, dtype=np.float64)
        })
    
    return beliefs


@st.composite
def config_strategy(draw):
    """
    Generate valid configuration dictionaries.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    dict
        Configuration dictionary with randomized but valid parameters.
        
    Notes
    -----
    This generates a minimal valid configuration with key parameters
    randomized within acceptable ranges. Not all config fields are included.
    """
    return {
        'system': {
            'timestep_ms': draw(st.floats(min_value=0.1, max_value=10.0)),
            'random_seed': draw(st.integers(min_value=0, max_value=9999))
        },
        'active_inference': {
            'learning_rate': draw(st.floats(min_value=0.001, max_value=0.1)),
            'precision_init': draw(st.floats(min_value=0.5, max_value=2.0)),
            'precision_range': [0.1, 10.0]
        },
        'ignition': {
            'baseline_threshold': draw(st.floats(min_value=1.0, max_value=5.0)),
            'threshold_range': [1.0, 5.0],
            'sigmoid_alpha': draw(st.floats(min_value=1.0, max_value=10.0)),
            'amplification_duration_ms': draw(st.floats(min_value=200.0, max_value=500.0)),
            'refractory_period_ms': draw(st.floats(min_value=100.0, max_value=300.0)),
            'workspace_nodes': 1000
        },
        'precision': {
            'exteroceptive_baseline': draw(st.floats(min_value=0.5, max_value=2.0)),
            'interoceptive_baseline': draw(st.floats(min_value=0.5, max_value=2.0)),
            'attention_gain_range': [0.5, 3.0],
            'volatility_sensitivity': draw(st.floats(min_value=0.01, max_value=0.5))
        },
        'thermodynamic': {
            'total_energy_budget': draw(st.floats(min_value=50.0, max_value=200.0)),
            'baseline_consumption': draw(st.floats(min_value=10.0, max_value=30.0)),
            'ignition_cost': draw(st.floats(min_value=5.0, max_value=15.0)),
            'recovery_rate': draw(st.floats(min_value=1.0, max_value=10.0)),
            'depletion_threshold': draw(st.floats(min_value=5.0, max_value=20.0))
        }
    }


@st.composite
def precision_weighted_error_strategy(draw):
    """
    Generate valid precision-weighted prediction errors.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    dict
        Dictionary containing:
        - 'extero_error': np.ndarray of shape (256,)
        - 'extero_precision': float > 0
        - 'intero_error': np.ndarray of shape (6,)
        - 'intero_precision': float > 0
        
    Notes
    -----
    Errors are constrained to [-5, 5] and precisions to [0.1, 10.0]
    for numerical stability and realistic values.
    """
    extero_error_values = draw(st.lists(
        st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        min_size=256,
        max_size=256
    ))
    intero_error_values = draw(st.lists(
        st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        min_size=6,
        max_size=6
    ))
    
    return {
        'extero_error': np.array(extero_error_values, dtype=np.float64),
        'extero_precision': draw(st.floats(min_value=0.1, max_value=10.0)),
        'intero_error': np.array(intero_error_values, dtype=np.float64),
        'intero_precision': draw(st.floats(min_value=0.1, max_value=10.0))
    }


@st.composite
def error_variance_strategy(draw):
    """
    Generate valid error variance values.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    float
        Error variance value in range [0.01, 100.0].
        
    Notes
    -----
    Lower bound is 0.01 to avoid division by zero in precision calculations.
    Upper bound is 100.0 to represent high but not extreme uncertainty.
    """
    return draw(st.floats(min_value=0.01, max_value=100.0))


@st.composite
def metabolic_reserve_strategy(draw, max_capacity=100.0):
    """
    Generate valid metabolic reserve values.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
    max_capacity : float, optional
        Maximum metabolic capacity, by default 100.0.
        
    Returns
    -------
    float
        Metabolic reserve value in range [0, max_capacity].
    """
    return draw(st.floats(min_value=0.0, max_value=max_capacity))


@st.composite
def allostatic_load_strategy(draw):
    """
    Generate valid allostatic load values.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    float
        Allostatic load value in range [0.0, 10.0].
        
    Notes
    -----
    Range represents cumulative homeostatic deviation from 0 (no load)
    to 10 (severe chronic stress).
    """
    return draw(st.floats(min_value=0.0, max_value=10.0))


@st.composite
def somatic_marker_gain_strategy(draw):
    """
    Generate valid somatic marker gain values.
    
    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
        
    Returns
    -------
    float
        Somatic marker gain in range [0.5, 2.0].
        
    Notes
    -----
    Range represents modulation from 0.5 (reduced influence) to 2.0
    (amplified influence) of learned somatic markers.
    """
    return draw(st.floats(min_value=0.5, max_value=2.0))
