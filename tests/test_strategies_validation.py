"""
Quick validation test for Hypothesis strategies.

This test verifies that all custom strategies generate valid data.
"""

import pytest
import numpy as np
from hypothesis import given, settings
from tests.strategies import (
    body_state_strategy,
    observation_strategy,
    belief_state_strategy,
    config_strategy,
    precision_weighted_error_strategy,
    error_variance_strategy,
    metabolic_reserve_strategy,
    allostatic_load_strategy,
    somatic_marker_gain_strategy
)


@given(body_state_strategy())
@settings(max_examples=10)
def test_body_state_strategy_generates_valid_states(body_state):
    """Test that body_state_strategy generates valid physiological states."""
    # Check all required keys are present
    required_keys = ['heart_rate', 'cortisol', 'temperature', 'glucose', 'respiration', 'systolic_bp']
    for key in required_keys:
        assert key in body_state, f"Missing key: {key}"
    
    # Check values are within valid ranges
    assert 50.0 <= body_state['heart_rate'] <= 120.0
    assert 5.0 <= body_state['cortisol'] <= 30.0
    assert 36.0 <= body_state['temperature'] <= 39.0
    assert 3.0 <= body_state['glucose'] <= 8.0
    assert 10.0 <= body_state['respiration'] <= 30.0
    assert 90.0 <= body_state['systolic_bp'] <= 160.0


@given(observation_strategy())
@settings(max_examples=10)
def test_observation_strategy_generates_valid_observations(observation):
    """Test that observation_strategy generates valid observation vectors."""
    # Check shape
    assert observation.shape == (256,)
    
    # Check dtype
    assert observation.dtype == np.float64
    
    # Check values are in valid range
    assert np.all(observation >= -10.0)
    assert np.all(observation <= 10.0)
    
    # Check no NaN or Inf
    assert not np.any(np.isnan(observation))
    assert not np.any(np.isinf(observation))


@given(belief_state_strategy())
@settings(max_examples=10)
def test_belief_state_strategy_generates_valid_beliefs(beliefs):
    """Test that belief_state_strategy generates valid belief states."""
    # Check we have 4 levels by default
    assert len(beliefs) == 4
    
    # Check each level has required keys
    for i, belief in enumerate(beliefs):
        assert 'mean' in belief
        assert 'precision' in belief
        assert 'prediction_error' in belief
        
        # Check types
        assert isinstance(belief['mean'], np.ndarray)
        assert isinstance(belief['precision'], float)
        assert isinstance(belief['prediction_error'], np.ndarray)
        
        # Check precision is positive
        assert belief['precision'] > 0
        assert 0.1 <= belief['precision'] <= 10.0
        
        # Check no NaN or Inf
        assert not np.any(np.isnan(belief['mean']))
        assert not np.any(np.isinf(belief['mean']))
        assert not np.any(np.isnan(belief['prediction_error']))
        assert not np.any(np.isinf(belief['prediction_error']))


@given(config_strategy())
@settings(max_examples=10)
def test_config_strategy_generates_valid_configs(config):
    """Test that config_strategy generates valid configuration dictionaries."""
    # Check required top-level keys
    assert 'system' in config
    assert 'active_inference' in config
    assert 'ignition' in config
    assert 'precision' in config
    assert 'thermodynamic' in config
    
    # Check system config
    assert 'timestep_ms' in config['system']
    assert 0.1 <= config['system']['timestep_ms'] <= 10.0
    
    # Check active inference config
    assert 'learning_rate' in config['active_inference']
    assert 0.001 <= config['active_inference']['learning_rate'] <= 0.1
    
    # Check ignition config
    assert 'baseline_threshold' in config['ignition']
    assert 1.0 <= config['ignition']['baseline_threshold'] <= 5.0


@given(precision_weighted_error_strategy())
@settings(max_examples=10)
def test_precision_weighted_error_strategy_generates_valid_errors(error_data):
    """Test that precision_weighted_error_strategy generates valid data."""
    # Check required keys
    assert 'extero_error' in error_data
    assert 'extero_precision' in error_data
    assert 'intero_error' in error_data
    assert 'intero_precision' in error_data
    
    # Check shapes
    assert error_data['extero_error'].shape == (256,)
    assert error_data['intero_error'].shape == (6,)
    
    # Check precisions are positive
    assert error_data['extero_precision'] > 0
    assert error_data['intero_precision'] > 0
    
    # Check no NaN or Inf
    assert not np.any(np.isnan(error_data['extero_error']))
    assert not np.any(np.isinf(error_data['extero_error']))
    assert not np.any(np.isnan(error_data['intero_error']))
    assert not np.any(np.isinf(error_data['intero_error']))


@given(error_variance_strategy())
@settings(max_examples=10)
def test_error_variance_strategy_generates_valid_variances(variance):
    """Test that error_variance_strategy generates valid variance values."""
    assert isinstance(variance, float)
    assert 0.01 <= variance <= 100.0


@given(metabolic_reserve_strategy())
@settings(max_examples=10)
def test_metabolic_reserve_strategy_generates_valid_reserves(reserve):
    """Test that metabolic_reserve_strategy generates valid reserve values."""
    assert isinstance(reserve, float)
    assert 0.0 <= reserve <= 100.0


@given(allostatic_load_strategy())
@settings(max_examples=10)
def test_allostatic_load_strategy_generates_valid_loads(load):
    """Test that allostatic_load_strategy generates valid load values."""
    assert isinstance(load, float)
    assert 0.0 <= load <= 10.0


@given(somatic_marker_gain_strategy())
@settings(max_examples=10)
def test_somatic_marker_gain_strategy_generates_valid_gains(gain):
    """Test that somatic_marker_gain_strategy generates valid gain values."""
    assert isinstance(gain, float)
    assert 0.5 <= gain <= 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
