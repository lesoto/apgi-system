"""
Custom Hypothesis strategies for APGI system data types.

This module provides strategies for generating valid test data for
property-based testing of the APGI system components.
"""

import numpy as np
from hypothesis import strategies as st

# ============================================================================
# Core Strategies (as specified in design document)
# ============================================================================


@st.composite
def belief_states(draw):
    """Generate valid belief state distributions.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    np.ndarray
        Probability distribution that sums to 1.0.

    Notes
    -----
    Generates belief states as probability distributions over discrete states.
    Size varies between 2 and 10 states. All values are non-negative and sum to 1.
    """
    size = draw(st.integers(min_value=2, max_value=10))
    values = draw(st.lists(st.floats(min_value=0, max_value=1), min_size=size, max_size=size))
    # Normalize to sum to 1
    total = sum(values)
    if total > 0:
        return np.array([v / total for v in values])
    return np.ones(size) / size


@st.composite
def precision_values(draw):
    """Generate valid precision weights.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    float
        Precision weight in range [0.0, 1.0].

    Notes
    -----
    Precision weights represent confidence or certainty in predictions.
    Values are bounded between 0 (no confidence) and 1 (full confidence).
    """
    return draw(
        st.floats(
            min_value=0.0,
            max_value=1.0,
            exclude_min=False,
            exclude_max=False,
            allow_nan=False,
            allow_infinity=False,
        )
    )


@st.composite
def observations(draw):
    """Generate valid observations.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    list of float
        Observation values in range [-10, 10].

    Notes
    -----
    Generates sensor observations as lists of floating-point values.
    Size varies between 1 and 10 observations. Values are constrained
    to [-10, 10] to represent typical sensory input magnitudes.
    """
    size = draw(st.integers(min_value=1, max_value=10))
    return draw(
        st.lists(
            st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size,
        )
    )


@st.composite
def configurations(draw):
    """Generate valid system configurations.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    dict
        Configuration dictionary with key parameters.

    Notes
    -----
    Generates minimal valid configurations with randomized parameters:
    - learning_rate: [0.001, 0.1]
    - precision_threshold: [0.0, 1.0]
    - max_iterations: [1, 1000]
    - convergence_tolerance: [1e-6, 1e-2]
    """
    return {
        "learning_rate": draw(st.floats(min_value=0.001, max_value=0.1)),
        "precision_threshold": draw(st.floats(min_value=0.0, max_value=1.0)),
        "max_iterations": draw(st.integers(min_value=1, max_value=1000)),
        "convergence_tolerance": draw(st.floats(min_value=1e-6, max_value=1e-2)),
    }


# ============================================================================
# Extended Strategies (for specific APGI subsystems)
# ============================================================================


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
        "heart_rate": draw(st.floats(min_value=50.0, max_value=120.0)),
        "cortisol": draw(st.floats(min_value=5.0, max_value=30.0)),
        "temperature": draw(st.floats(min_value=36.0, max_value=39.0)),
        "glucose": draw(st.floats(min_value=3.0, max_value=8.0)),
        "respiration": draw(st.floats(min_value=10.0, max_value=30.0)),
        "systolic_bp": draw(st.floats(min_value=90.0, max_value=160.0)),
    }


@st.composite
def observation_strategy(draw, dim=448):
    """
    Generate valid observation vectors.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
    dim : int, optional
        Dimensionality of observation vector, by default 448.

    Returns
    -------
    np.ndarray
        Observation vector of shape (dim,) with values in reasonable range.

    Notes
    -----
    Values are constrained to [-10, 10] to represent typical sensory
    input magnitudes and avoid numerical instability.
    """
    values = draw(
        st.lists(
            st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=dim,
            max_size=dim,
        )
    )
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
        level_dims = [64, 32, 16, 8][:num_levels]  # Reduced from [256, 128, 64, 32]

    beliefs = []
    for dim in level_dims:
        mean_values = draw(
            st.lists(
                st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
                min_size=dim,
                max_size=dim,
            )
        )
        error_values = draw(
            st.lists(
                st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
                min_size=dim,
                max_size=dim,
            )
        )
        precision = draw(st.floats(min_value=0.1, max_value=10.0))

        beliefs.append(
            {
                "mean": np.array(mean_values, dtype=np.float64),
                "precision": precision,
                "prediction_error": np.array(error_values, dtype=np.float64),
            }
        )

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
        "system": {
            "timestep_ms": draw(st.floats(min_value=0.1, max_value=10.0)),
            "random_seed": draw(st.integers(min_value=0, max_value=9999)),
        },
        "active_inference": {
            "learning_rate": draw(st.floats(min_value=0.001, max_value=0.1)),
            "precision_init": draw(st.floats(min_value=0.5, max_value=2.0)),
            "precision_range": [0.1, 10.0],
        },
        "ignition": {
            "baseline_threshold": draw(st.floats(min_value=1.0, max_value=5.0)),
            "threshold_range": [1.0, 5.0],
            "sigmoid_alpha": draw(st.floats(min_value=1.0, max_value=10.0)),
            "amplification_duration_ms": draw(st.floats(min_value=200.0, max_value=500.0)),
            "refractory_period_ms": draw(st.floats(min_value=100.0, max_value=300.0)),
            "workspace_nodes": 1000,
        },
        "precision": {
            "exteroceptive_baseline": draw(st.floats(min_value=0.5, max_value=2.0)),
            "interoceptive_baseline": draw(st.floats(min_value=0.5, max_value=2.0)),
            "attention_gain_range": [0.5, 3.0],
            "volatility_sensitivity": draw(st.floats(min_value=0.01, max_value=0.5)),
        },
        "thermodynamic": {
            "total_energy_budget": draw(st.floats(min_value=50.0, max_value=200.0)),
            "baseline_consumption": draw(st.floats(min_value=10.0, max_value=30.0)),
            "ignition_cost": draw(st.floats(min_value=5.0, max_value=15.0)),
            "recovery_rate": draw(st.floats(min_value=1.0, max_value=10.0)),
            "depletion_threshold": draw(st.floats(min_value=5.0, max_value=20.0)),
        },
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
        - 'extero_error': np.ndarray of shape (448,)
        - 'extero_precision': float > 0
        - 'intero_error': np.ndarray of shape (6,)
        - 'intero_precision': float > 0

    Notes
    -----
    Errors are constrained to [-5, 5] and precisions to [0.1, 10.0]
    for numerical stability and realistic values.
    """
    extero_error_values = draw(
        st.lists(
            st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=448,
            max_size=448,
        )
    )
    intero_error_values = draw(
        st.lists(
            st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=6,
            max_size=6,
        )
    )

    return {
        "extero_error": np.array(extero_error_values, dtype=np.float64),
        "extero_precision": draw(st.floats(min_value=0.1, max_value=10.0)),
        "intero_error": np.array(intero_error_values, dtype=np.float64),
        "intero_precision": draw(st.floats(min_value=0.1, max_value=10.0)),
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


@st.composite
def probability_distribution_strategy(draw, size=None):
    """
    Generate valid probability distributions that sum to 1.0.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.
    size : int, optional
        Size of distribution. If None, randomly chosen between 2 and 20.

    Returns
    -------
    np.ndarray
        Probability distribution that sums to 1.0.

    Notes
    -----
    Uses Dirichlet distribution to generate valid probability vectors.
    """
    if size is None:
        size = draw(st.integers(min_value=2, max_value=20))

    # Generate positive values and normalize
    values = draw(
        st.lists(
            st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size,
        )
    )
    arr = np.array(values, dtype=np.float64)
    return arr / arr.sum()


@st.composite
def precision_weight_strategy(draw):
    """
    Generate valid precision weights in [0, 1] range.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    float
        Precision weight in range [0.0, 1.0].
    """
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def confidence_value_strategy(draw):
    """
    Generate valid confidence values for precision calculations.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    float
        Confidence value in range [0.0, 1.0].
    """
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))


@st.composite
def free_energy_components_strategy(draw):
    """
    Generate valid components for free energy calculation.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    dict
        Dictionary containing belief, observation, and precision for free energy.
    """
    size = draw(st.integers(min_value=2, max_value=20))

    # Generate normalized belief
    belief_values = draw(
        st.lists(
            st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size,
        )
    )
    belief = np.array(belief_values, dtype=np.float64)
    belief = belief / belief.sum()

    # Generate observation
    observation = draw(observation_strategy(dim=size))

    # Generate precision
    precision = draw(st.floats(min_value=0.1, max_value=10.0))

    return {
        "belief": belief,
        "observation": observation,
        "precision": precision,
    }


@st.composite
def serializable_config_strategy(draw):
    """
    Generate configurations that are serializable (for round-trip testing).

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    dict
        Configuration dictionary with only JSON-serializable types.
    """
    return {
        "system": {
            "timestep_ms": draw(st.floats(min_value=0.1, max_value=10.0)),
            "random_seed": draw(st.integers(min_value=0, max_value=9999)),
            "name": draw(
                st.text(
                    min_size=1,
                    max_size=50,
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
                    ),
                )
            ),
        },
        "active_inference": {
            "learning_rate": draw(st.floats(min_value=0.001, max_value=0.1)),
            "precision_init": draw(st.floats(min_value=0.5, max_value=2.0)),
            "enabled": draw(st.booleans()),
        },
        "precision": {
            "exteroceptive_baseline": draw(st.floats(min_value=0.5, max_value=2.0)),
            "interoceptive_baseline": draw(st.floats(min_value=0.5, max_value=2.0)),
        },
    }


@st.composite
def invalid_input_strategy(draw):
    """
    Generate various types of invalid inputs for error handling tests.

    Parameters
    ----------
    draw : callable
        Hypothesis draw function for sampling from strategies.

    Returns
    -------
    any
        Invalid input of various types.
    """
    invalid_type = draw(
        st.sampled_from(["nan", "inf", "neg_inf", "negative", "wrong_type", "empty", "none"])
    )

    if invalid_type == "nan":
        return float("nan")
    elif invalid_type == "inf":
        return float("inf")
    elif invalid_type == "neg_inf":
        return float("-inf")
    elif invalid_type == "negative":
        return draw(st.floats(max_value=-0.001, allow_nan=False, allow_infinity=False))
    elif invalid_type == "wrong_type":
        return draw(st.text(min_size=1, max_size=20))
    elif invalid_type == "empty":
        return draw(st.sampled_from([[], {}, "", np.array([])]))
    elif invalid_type == "none":
        return None
