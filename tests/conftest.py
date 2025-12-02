"""
Shared test fixtures and configuration for APGI system tests.

This module provides common fixtures used across unit, property-based,
and integration tests.
"""

import pytest
import numpy as np
import yaml
from pathlib import Path
from hypothesis import settings, HealthCheck


# Configure Hypothesis profiles
settings.register_profile(
    "ci",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)

settings.register_profile(
    "dev",
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)

settings.register_profile(
    "thorough",
    max_examples=1000,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)

# Load the appropriate profile (default to 'dev' for faster local testing)
settings.load_profile("dev")


@pytest.fixture
def config():
    """
    Load default configuration from config/default.yaml.
    
    Returns
    -------
    dict
        Configuration dictionary with all system parameters.
    """
    config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def apgi_system():
    """
    Provide a fresh APGI system instance.
    
    Yields
    ------
    APGISystem
        A newly initialized APGI system instance.
        
    Notes
    -----
    The system is reset after the test completes to ensure clean state.
    """
    from apgi_system.system import APGISystem
    
    system = APGISystem()
    yield system
    system.reset()


@pytest.fixture
def body_model(config):
    """
    Provide a body model instance.
    
    Parameters
    ----------
    config : dict
        Configuration dictionary (from config fixture).
        
    Returns
    -------
    BodyModel
        A newly initialized body model instance.
    """
    from apgi_system.interoception.body_model import BodyModel
    
    return BodyModel(config)


@pytest.fixture
def random_observation():
    """
    Generate a random observation vector.
    
    Returns
    -------
    np.ndarray
        Random observation vector of shape (256,) with values ~ N(0, 0.5^2).
        
    Notes
    -----
    The observation is scaled to have moderate variance (0.5) to represent
    typical sensory input magnitudes.
    """
    return np.random.randn(256) * 0.5


@pytest.fixture
def random_body_state():
    """
    Generate a random but physiologically valid body state.
    
    Returns
    -------
    dict
        Dictionary containing physiological variables within valid ranges:
        - heart_rate: 60-100 bpm (normal resting range)
        - cortisol: 8-15 μg/dL (normal range)
        - temperature: 36.5-37.5°C (normal range)
        - glucose: 4.0-6.0 mmol/L (normal fasting range)
        - respiration: 12-18 breaths/min (normal range)
        - systolic_bp: 110-130 mmHg (normal range)
        
    Notes
    -----
    All values are uniformly sampled within physiologically plausible ranges
    to ensure valid test inputs.
    """
    return {
        'heart_rate': np.random.uniform(60, 100),
        'cortisol': np.random.uniform(8, 15),
        'temperature': np.random.uniform(36.5, 37.5),
        'glucose': np.random.uniform(4.0, 6.0),
        'respiration': np.random.uniform(12, 18),
        'systolic_bp': np.random.uniform(110, 130)
    }
