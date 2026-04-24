"""
Hypothesis strategies for property-based testing.

This module provides custom Hypothesis strategies for generating
test data for APGI system components.
"""

from typing import Any

import numpy as np
from hypothesis import strategies as st
from numpy.typing import NDArray


def observation_strategy(dim: int = 256) -> st.SearchStrategy[NDArray[np.float64]]:
    """Generate observation vectors for testing.

    Parameters
    ----------
    dim : int
        Dimension of the observation vector

    Returns
    -------
    SearchStrategy
        Strategy for generating observation vectors
    """
    return st.builds(
        np.array,
        st.lists(
            st.lists(
                st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
                min_size=dim,
                max_size=dim,
            ),
            min_size=1,
            max_size=1,
        ),
        st.just(np.float64),
    )


def error_variance_strategy() -> st.SearchStrategy[float]:
    """Generate error variance values for testing.

    Returns
    -------
    SearchStrategy
        Strategy for generating error variance values
    """
    return st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False)


def body_state_strategy() -> st.SearchStrategy[dict[str, float]]:
    """Generate body state dictionaries for testing.

    Returns
    -------
    SearchStrategy
        Strategy for generating body state dictionaries
    """
    return st.fixed_dictionaries(
        {
            "heart_rate": st.floats(
                min_value=50.0, max_value=120.0, allow_nan=False, allow_infinity=False
            ),
            "cortisol": st.floats(
                min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False
            ),
            "temperature": st.floats(
                min_value=36.0, max_value=39.0, allow_nan=False, allow_infinity=False
            ),
            "glucose": st.floats(
                min_value=3.0, max_value=8.0, allow_nan=False, allow_infinity=False
            ),
            "respiration": st.floats(
                min_value=10.0, max_value=30.0, allow_nan=False, allow_infinity=False
            ),
            "systolic_bp": st.floats(
                min_value=90.0, max_value=160.0, allow_nan=False, allow_infinity=False
            ),
        }
    )


# Additional strategies for other tests
def belief_states() -> st.SearchStrategy[NDArray[np.float64]]:
    """Generate belief state probability distributions.

    Returns
    -------
    SearchStrategy
        Strategy for generating probability distributions
    """
    return st.builds(
        np.array,
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=2,  # type: ignore[arg-type]
            max_size=10,  # type: ignore[arg-type]
        ),
        st.just(np.float64),
    ).map(
        lambda x: x / np.sum(x)
    )  # Normalize to sum to 1


def precision_values() -> st.SearchStrategy[float]:
    """Generate precision weight values.

    Returns
    -------
    SearchStrategy
        Strategy for generating precision values
    """
    return st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)


def observations() -> st.SearchStrategy[list[float]]:
    """Generate observation lists for testing.

    Returns
    -------
    SearchStrategy
        Strategy for generating observation lists
    """
    return st.lists(
        st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    )


def configurations() -> st.SearchStrategy[dict[str, Any]]:
    """Generate system configuration dictionaries.

    Returns
    -------
    SearchStrategy
        Strategy for generating configuration dictionaries
    """
    return st.fixed_dictionaries(
        {
            "learning_rate": st.floats(
                min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False
            ),
            "precision_threshold": st.floats(
                min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
            ),
            "max_iterations": st.integers(min_value=1, max_value=1000),
            "convergence_tolerance": st.floats(
                min_value=1e-6, max_value=1e-2, allow_nan=False, allow_infinity=False
            ),
        }
    )


@st.composite
def _belief_state_strategy_impl(
    draw: st.DrawFn,
    num_levels: int = 4,
    level_dims: list[int] | None = None,
) -> list[dict[str, Any]]:
    """Internal implementation using @composite pattern."""
    if level_dims is None:
        level_dims = [64] * num_levels

    beliefs = []
    for i in range(num_levels):
        dim = level_dims[i] if i < len(level_dims) else 64
        beliefs.append(
            {
                "mean": np.zeros(dim),
                "precision": draw(
                    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
                ),
                "prediction_error": np.zeros(dim),
            }
        )
    return beliefs


def belief_state_strategy(
    num_levels: int = 4,
    level_dims: list[int] | None = None,
) -> st.SearchStrategy[list[dict[str, Any]]]:
    """Generate hierarchical belief states.

    Parameters
    ----------
    num_levels : int
        Number of hierarchical levels to generate (default: 4)
    level_dims : list[int] | None
        Dimensions for each level (default: [64] * num_levels)

    Returns
    -------
    SearchStrategy
        Strategy for generating belief state lists
    """
    return _belief_state_strategy_impl(num_levels=num_levels, level_dims=level_dims)


def config_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """Generate full system configuration.

    Returns
    -------
    SearchStrategy
        Strategy for generating full configuration dictionaries
    """
    return st.fixed_dictionaries(
        {
            "system": st.fixed_dictionaries(
                {
                    "timestep_ms": st.floats(
                        min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
                    ),
                }
            ),
            "active_inference": st.fixed_dictionaries(
                {
                    "learning_rate": st.floats(
                        min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False
                    ),
                }
            ),
            "ignition": st.fixed_dictionaries(
                {
                    "baseline_threshold": st.floats(
                        min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False
                    ),
                }
            ),
            "precision": st.just({}),
            "thermodynamic": st.just({}),
        }
    )


def precision_weighted_error_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """Generate precision-weighted error data.

    Returns
    -------
    SearchStrategy
        Strategy for generating precision-weighted error dictionaries
    """
    return st.fixed_dictionaries(
        {
            "extero_error": st.builds(
                np.array,
                st.lists(
                    st.floats(
                        min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
                    ),
                    min_size=256,
                    max_size=256,
                ),
                st.just(np.float64),
            ),
            "extero_precision": st.floats(
                min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
            ),
            "intero_error": st.builds(
                np.array,
                st.lists(
                    st.floats(
                        min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
                    ),
                    min_size=6,
                    max_size=6,
                ),
                st.just(np.float64),
            ),
            "intero_precision": st.floats(
                min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False
            ),
        }
    )


def metabolic_reserve_strategy() -> st.SearchStrategy[float]:
    """Generate metabolic reserve values.

    Returns
    -------
    SearchStrategy
        Strategy for generating metabolic reserve values
    """
    return st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)


def allostatic_load_strategy() -> st.SearchStrategy[float]:
    """Generate allostatic load values.

    Returns
    -------
    SearchStrategy
        Strategy for generating allostatic load values
    """
    return st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)


def somatic_marker_gain_strategy() -> st.SearchStrategy[float]:
    """Generate somatic marker gain values.

    Returns
    -------
    SearchStrategy
        Strategy for generating somatic marker gain values
    """
    return st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False)
