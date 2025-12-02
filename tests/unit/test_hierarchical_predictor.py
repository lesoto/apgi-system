"""Unit tests for HierarchicalPredictor."""

import pytest
import numpy as np
import yaml
from pathlib import Path

from apgi_system.core.predictive_processing import HierarchicalPredictor, PredictionErrorChannel


@pytest.fixture
def config():
    """Load default configuration."""
    config_path = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def simple_config():
    """Simple test configuration."""
    return {
        'hierarchy': {
            'num_levels': 3,
            'level_configs': [
                {'name': 'sensory', 'nodes': 32, 'timescale_ms': 1},
                {'name': 'perceptual', 'nodes': 16, 'timescale_ms': 10},
                {'name': 'conceptual', 'nodes': 8, 'timescale_ms': 100}
            ]
        },
        'predictive_processing': {
            'prediction_horizon_ms': 200,
            'temporal_discount': 0.95,
            'error_accumulation_window_ms': 100
        },
        'system': {'timestep_ms': 1.0}
    }


class TestPredictionErrorChannel:
    """Test PredictionErrorChannel functionality."""

    def test_initialization(self):
        """Test channel initializes correctly."""
        channel = PredictionErrorChannel(
            name='test',
            dimension=16,
            window_size_ms=100.0,
            timestep_ms=1.0
        )
        
        assert channel.name == 'test'
        assert channel.dimension == 16
        assert channel.window_size == 100
        assert len(channel.error_buffer) == 0
        assert channel.accumulated_error == 0.0

    def test_update_basic(self):
        """Test basic update functionality."""
        channel = PredictionErrorChannel('test', 8)
        
        observation = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        prediction = np.array([1.1, 1.9, 3.2, 3.8, 5.1, 5.9, 7.1, 7.9])
        
        error = channel.update(observation, prediction, precision=1.5)
        
        expected_error = observation - prediction
        assert np.allclose(error, expected_error)
        assert channel.precision == 1.5
        assert len(channel.error_buffer) == 1

    def test_sliding_window(self):
        """Test sliding window behavior."""
        channel = PredictionErrorChannel('test', 4, window_size_ms=3.0, timestep_ms=1.0)
        
        # Add more errors than window size
        for i in range(5):
            obs = np.ones(4) * i
            pred = np.zeros(4)
            channel.update(obs, pred)
        
        # Should only keep last 3
        assert len(channel.error_buffer) == 3

    def test_accumulated_signal(self):
        """Test accumulated signal computation."""
        channel = PredictionErrorChannel('test', 2)
        
        # Add some errors
        channel.update(np.array([1.0, 0.0]), np.array([0.0, 0.0]), precision=2.0)
        channel.update(np.array([0.0, 1.0]), np.array([0.0, 0.0]), precision=2.0)
        
        signal = channel.get_accumulated_signal()
        
        # Signal should be precision * sqrt(sum of squared errors)
        expected_signal = 2.0 * np.sqrt(2.0)  # 2 errors of magnitude 1 each
        assert abs(signal - expected_signal) < 1e-6

    def test_statistics(self):
        """Test error statistics computation."""
        channel = PredictionErrorChannel('test', 2)
        
        # Add known errors
        channel.update(np.array([2.0, 0.0]), np.array([0.0, 0.0]))  # Error: [2, 0]
        channel.update(np.array([0.0, 3.0]), np.array([0.0, 0.0]))  # Error: [0, 3]
        
        stats = channel.get_statistics()
        
        assert 'mean_error' in stats
        assert 'std_error' in stats
        assert 'max_error' in stats
        assert 'accumulated' in stats
        assert 'current_magnitude' in stats
        
        # Check some values
        assert stats['max_error'] == 3.0
        assert stats['current_magnitude'] == 3.0  # Last error magnitude

    def test_reset(self):
        """Test channel reset."""
        channel = PredictionErrorChannel('test', 2)
        
        # Add some data
        channel.update(np.array([1.0, 1.0]), np.array([0.0, 0.0]))
        assert len(channel.error_buffer) > 0
        assert channel.accumulated_error > 0
        
        # Reset
        channel.reset()
        
        assert len(channel.error_buffer) == 0
        assert channel.accumulated_error == 0.0
        assert np.allclose(channel.current_error, 0.0)


class TestHierarchicalPredictor:
    """Test HierarchicalPredictor functionality."""

    def test_initialization(self, simple_config):
        """Test predictor initializes correctly."""
        predictor = HierarchicalPredictor(simple_config)
        
        assert predictor.num_levels == 3
        assert len(predictor.levels) == 3
        assert predictor.levels[0]['name'] == 'sensory'
        assert predictor.levels[0]['nodes'] == 32
        assert predictor.exteroceptive_channel is not None
        assert predictor.interoceptive_channel is not None

    def test_predict_exteroceptive_only(self, simple_config):
        """Test prediction with exteroceptive input only."""
        predictor = HierarchicalPredictor(simple_config)
        
        extero_input = np.random.randn(32)
        results = predictor.predict(extero_input=extero_input, dt_ms=1.0)
        
        assert 'exteroceptive' in results
        assert 'interoceptive' in results
        assert 'hierarchical_errors' in results
        
        # Should have exteroceptive results
        assert 'error' in results['exteroceptive']
        assert 'stats' in results['exteroceptive']
        
        # Should have hierarchical errors for all levels
        assert len(results['hierarchical_errors']) == 3

    def test_predict_interoceptive_only(self, simple_config):
        """Test prediction with interoceptive input only."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Body state: [heart_rate, respiration, temperature, glucose, cortisol, blood_pressure]
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])
        results = predictor.predict(intero_input=intero_input, dt_ms=1.0)
        
        assert 'interoceptive' in results
        assert 'error' in results['interoceptive']
        assert 'stats' in results['interoceptive']

    def test_predict_both_streams(self, simple_config):
        """Test prediction with both input streams."""
        predictor = HierarchicalPredictor(simple_config)
        
        extero_input = np.random.randn(32)
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])
        
        results = predictor.predict(
            extero_input=extero_input,
            intero_input=intero_input,
            dt_ms=1.0
        )
        
        # Should have both streams
        assert 'exteroceptive' in results
        assert 'interoceptive' in results
        assert results['exteroceptive']['error'].shape == (32,)
        assert results['interoceptive']['error'].shape == (6,)

    def test_multi_level_prediction_scenarios(self, simple_config):
        """Test multi-level prediction scenarios."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Test different timescales
        extero_input = np.random.randn(32)
        
        # Run multiple steps to trigger different level updates
        for i in range(15):  # Should trigger level 1 update at step 10
            results = predictor.predict(extero_input=extero_input, dt_ms=1.0)
            
            # Check that hierarchical errors are computed
            assert len(results['hierarchical_errors']) == 3
            for level_error in results['hierarchical_errors']:
                assert 'level' in level_error
                assert 'error' in level_error
                assert 'magnitude' in level_error
                assert 'precision' in level_error

    def test_temporal_integration(self, simple_config):
        """Test temporal integration over multiple steps."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Consistent input should reduce prediction errors over time
        extero_input = np.ones(32) * 0.5
        
        errors = []
        for _ in range(20):
            results = predictor.predict(extero_input=extero_input, dt_ms=1.0)
            error_mag = results['exteroceptive']['stats']['mean_error']
            errors.append(error_mag)
        
        # Error should generally decrease (allowing some fluctuation)
        # Use a moving average to smooth out noise
        window = 5
        if len(errors) >= window:
            early_avg = np.mean(errors[:window])
            late_avg = np.mean(errors[-window:])
            assert late_avg <= early_avg * 1.2  # Allow 20% tolerance

    def test_get_prediction_errors(self, simple_config):
        """Test prediction error retrieval."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Generate some errors
        extero_input = np.random.randn(32)
        intero_input = np.array([70.0, 15.0, 37.0, 5.0, 10.0, 120.0])
        predictor.predict(extero_input=extero_input, intero_input=intero_input)
        
        errors = predictor.get_prediction_errors()
        
        assert 'exteroceptive_signal' in errors
        assert 'interoceptive_signal' in errors
        assert 'exteroceptive_stats' in errors
        assert 'interoceptive_stats' in errors
        
        # Signals should be non-negative
        assert errors['exteroceptive_signal'] >= 0
        assert errors['interoceptive_signal'] >= 0

    def test_reset(self, simple_config):
        """Test predictor reset."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Generate some state
        extero_input = np.random.randn(32)
        predictor.predict(extero_input=extero_input)
        
        # Check that state exists
        assert not np.allclose(predictor.levels[0]['state'], 0.0)
        
        # Reset
        predictor.reset()
        
        # State should be reset
        for level in predictor.levels:
            assert np.allclose(level['state'], 0.0)
            assert np.allclose(level['prediction'], 0.0)
            assert np.allclose(level['error'], 0.0)
        
        assert np.allclose(predictor.intero_prediction, 0.0)

    def test_invalid_extero_input_shape(self, simple_config):
        """Test error handling for invalid exteroceptive input shape."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Wrong shape
        with pytest.raises(ValueError):
            predictor.predict(extero_input=np.random.randn(16))  # Should be 32

    def test_invalid_intero_input_shape(self, simple_config):
        """Test error handling for invalid interoceptive input shape."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Wrong shape
        with pytest.raises(ValueError):
            predictor.predict(intero_input=np.random.randn(4))  # Should be 6

    def test_invalid_dt(self, simple_config):
        """Test error handling for invalid dt."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Negative dt
        with pytest.raises(ValueError):
            predictor.predict(extero_input=np.random.randn(32), dt_ms=-1.0)
        
        # Zero dt
        with pytest.raises(ValueError):
            predictor.predict(extero_input=np.random.randn(32), dt_ms=0.0)

    def test_nan_inputs(self, simple_config):
        """Test error handling for NaN inputs."""
        predictor = HierarchicalPredictor(simple_config)
        
        # NaN exteroceptive input
        with pytest.raises(ValueError):
            predictor.predict(extero_input=np.full(32, np.nan))
        
        # NaN interoceptive input
        with pytest.raises(ValueError):
            predictor.predict(intero_input=np.full(6, np.nan))

    def test_boundary_conditions(self, simple_config):
        """Test boundary conditions."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Very small inputs
        extero_input = np.ones(32) * 1e-10
        results = predictor.predict(extero_input=extero_input)
        assert np.isfinite(results['exteroceptive']['stats']['mean_error'])
        
        # Very large inputs
        extero_input = np.ones(32) * 1e6
        results = predictor.predict(extero_input=extero_input)
        assert np.isfinite(results['exteroceptive']['stats']['mean_error'])

    def test_interoceptive_prediction_learning(self, simple_config):
        """Test that interoceptive predictions adapt over time."""
        predictor = HierarchicalPredictor(simple_config)
        
        # Consistent interoceptive input
        intero_input = np.array([75.0, 18.0, 37.2, 5.5, 12.0, 125.0])
        
        initial_prediction = predictor.intero_prediction.copy()
        
        # Run multiple updates
        for _ in range(50):
            predictor.predict(intero_input=intero_input)
        
        final_prediction = predictor.intero_prediction.copy()
        
        # Prediction should have moved toward the input
        distance_initial = np.linalg.norm(intero_input - initial_prediction)
        distance_final = np.linalg.norm(intero_input - final_prediction)
        
        assert distance_final < distance_initial