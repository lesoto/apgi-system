"""
Comprehensive tests for core modules.

Tests for core/equation.py, core/models.py, core/threshold.py to improve coverage.
"""

import numpy as np


class TestCoreEquation:
    """Tests for core/equation.py module."""

    def test_module_imports(self):
        """Test that equation module can be imported."""
        from apgi_framework.core import equation  # type: ignore[import-not-found]

        assert hasattr(equation, "APGIEquation")

    def test_apgi_equation_initialization(self):
        """Test APGIEquation initialization."""
        from apgi_framework.core.equation import APGIEquation  # type: ignore[import-not-found]

        eq = APGIEquation()
        assert eq is not None
        assert eq.numerical_stability is True

    def test_calculate_surprise(self):
        """Test surprise calculation."""
        from apgi_framework.core.equation import APGIEquation  # type: ignore[import-not-found]

        eq = APGIEquation()
        result = eq.calculate_surprise(
            extero_error=0.5,
            intero_error=0.3,
            extero_precision=2.0,
            intero_precision=1.5,
        )

        assert isinstance(result, (int, float, np.number))
        assert result >= 0

    def test_calculate_with_different_parameters(self):
        """Test calculation with different parameter sets."""
        from apgi_framework.core.equation import APGIEquation

        eq = APGIEquation()

        # Test with various parameter values
        params = [
            (0.3, 0.2, 2.0, 1.5),
            (0.7, 0.4, 2.5, 1.8),
            (0.5, 0.3, 2.0, 1.5),
        ]

        for extero_e, intero_e, extero_p, intero_p in params:
            result = eq.calculate_surprise(extero_e, intero_e, extero_p, intero_p)
            assert isinstance(result, (int, float, np.number))
            assert result >= 0

    def test_calculate_ignition_probability(self):
        """Test ignition probability calculation."""
        from apgi_framework.core.equation import APGIEquation

        eq = APGIEquation()

        # Test with valid inputs
        prob = eq.calculate_ignition_probability(surprise=2.0, threshold=3.5, steepness=2.0)
        assert prob is not None
        assert isinstance(prob, (float, np.ndarray))
        assert 0 <= prob <= 1

    def test_equation_edge_cases(self):
        """Test equation with edge case values."""
        from apgi_framework.core.equation import APGIEquation

        eq = APGIEquation()

        # Test with zero prediction errors
        result = eq.calculate_surprise(0.0, 0.0, 2.0, 1.5)
        assert result == 0.0


class TestCoreModels:
    """Tests for core/models.py module."""

    def test_module_imports(self):
        """Test that models module can be imported."""
        from apgi_framework.core import models  # type: ignore[import-not-found]

        assert hasattr(models, "SomaticAgent")
        assert hasattr(models, "PredictiveIgnitionNetwork")

    def test_somatic_agent_initialization(self):
        """Test SomaticAgent initialization."""
        from apgi_framework.core.models import SomaticAgent  # type: ignore[import-not-found]

        agent = SomaticAgent()
        assert agent is not None

    def test_predictive_ignition_network_initialization(self):
        """Test PredictiveIgnitionNetwork initialization."""
        from apgi_framework.core.models import PredictiveIgnitionNetwork

        network = PredictiveIgnitionNetwork()
        assert network is not None

    def test_somatic_agent_decision_making(self):
        """Test SomaticAgent decision making."""
        from apgi_framework.core.models import SomaticAgent  # type: ignore[import-not-found]

        agent = SomaticAgent(n_states=4, n_actions=3, n_contexts=2)

        # Test decision making with sample inputs
        beliefs = np.array([0.5, 0.3, 0.2, 0.0])  # Beliefs over 4 states
        action, conscious, energy = agent.decide(beliefs, context=0, surprise=1.0)

        assert isinstance(action, (int, np.integer))
        assert isinstance(conscious, bool)
        assert isinstance(energy, np.ndarray)

    def test_predictive_ignition_network_forward_pass(self):
        """Test PredictiveIgnitionNetwork forward pass."""
        from apgi_framework.core.models import PredictiveIgnitionNetwork

        network = PredictiveIgnitionNetwork(n_features=5, n_global_units=3)

        # Create sample sensory input
        sensory_input = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        predictions, errors, weighted_errors, ignited, ignition_prob = network.forward_pass(
            sensory_input, somatic_gain=1.0
        )

        assert isinstance(predictions, np.ndarray)
        assert isinstance(errors, np.ndarray)
        assert isinstance(ignition_prob, (float, np.floating))
        assert 0 <= ignition_prob <= 1
        assert isinstance(ignited, bool)


class TestCoreThreshold:
    """Tests for core/threshold.py module."""

    def test_module_imports(self):
        """Test that threshold module can be imported."""
        from apgi_framework.core import threshold  # type: ignore[import-not-found]

        assert hasattr(threshold, "ThresholdManager")
        assert hasattr(threshold, "ThresholdDetector")  # Backward compat alias

    def test_threshold_manager_initialization(self):
        """Test ThresholdManager initialization."""
        from apgi_framework.core.threshold import ThresholdManager  # type: ignore[import-not-found]

        manager = ThresholdManager()
        assert manager is not None
        assert manager.baseline_threshold == 3.5

    def test_threshold_manager_with_threshold(self):
        """Test manager with specific threshold."""
        from apgi_framework.core.threshold import ThresholdDetector  # type: ignore[import-not-found]

        detector = ThresholdDetector(baseline_threshold=2.5)
        assert detector.baseline_threshold == 2.5

    def test_get_current_threshold(self):
        """Test getting current threshold."""
        from apgi_framework.core.threshold import ThresholdDetector  # type: ignore[import-not-found]

        detector = ThresholdDetector(baseline_threshold=3.0)
        threshold = detector.get_current_threshold()

        assert isinstance(threshold, (float, np.floating))
        assert threshold > 0

    def test_update_threshold(self):
        """Test updating threshold based on ignition."""
        from apgi_framework.core.threshold import ThresholdDetector  # type: ignore[import-not-found]

        detector = ThresholdDetector(baseline_threshold=3.0)

        # Update with ignition occurred
        new_threshold = detector.update_threshold(ignition_occurred=True)

        assert isinstance(new_threshold, (float, np.floating))

    def test_threshold_adaptive(self):
        """Test adaptive threshold functionality."""
        from apgi_framework.core.threshold import (
            ThresholdDetector,  # type: ignore[import-not-found]
        )

        detector = ThresholdDetector(baseline_threshold=3.0, adaptation_type="adaptive")

        # Simulate several ignition updates
        for _ in range(20):
            detector.update_threshold(ignition_occurred=np.random.random() > 0.5)

        threshold = detector.get_current_threshold()
        assert isinstance(threshold, (float, np.floating))

    def test_get_ignition_statistics(self):
        """Test getting ignition statistics."""
        from apgi_framework.core.threshold import ThresholdDetector  # type: ignore[import-not-found]

        detector = ThresholdDetector(baseline_threshold=3.0)

        # Simulate some ignitions
        for _ in range(10):
            detector.update_threshold(ignition_occurred=np.random.random() > 0.5)

        stats = detector.get_ignition_statistics()
        assert isinstance(stats, dict)
        assert "ignition_rate" in stats
        assert "n_trials" in stats

    def test_reset_threshold(self):
        """Test resetting threshold."""
        from apgi_framework.core.threshold import ThresholdDetector  # type: ignore[import-not-found]

        detector = ThresholdDetector(baseline_threshold=3.0)

        # Update threshold
        detector.update_threshold(ignition_occurred=True)
        detector.update_threshold(ignition_occurred=True)

        # Reset
        detector.reset_threshold()

        assert detector.get_current_threshold() == 3.0


class TestCoreDataModels:
    """Tests for core/data_models.py module."""

    def test_module_imports(self):
        """Test that data_models module can be imported."""
        from apgi_framework.core import data_models

        assert hasattr(data_models, "APGIParameters")
        assert hasattr(data_models, "ExperimentalTrial")

    def test_apgi_parameters_creation(self):
        """Test creating APGIParameters object."""
        from apgi_framework.core.data_models import APGIParameters

        params = APGIParameters(
            extero_precision=2.5,
            intero_precision=1.8,
            extero_error=0.5,
            intero_error=0.3,
            somatic_gain=1.5,
            threshold=3.0,
            steepness=2.5,
        )

        assert params.extero_precision == 2.5
        assert params.intero_precision == 1.8
        assert params.extero_error == 0.5
        assert params.intero_error == 0.3
        assert params.somatic_gain == 1.5
        assert params.threshold == 3.0
        assert params.steepness == 2.5

    def test_experimental_trial_creation(self):
        """Test creating ExperimentalTrial object."""
        from apgi_framework.core.data_models import ExperimentalTrial

        trial = ExperimentalTrial(
            trial_id="trial_001",
            condition="test",
        )

        assert trial.trial_id == "trial_001"
        assert trial.condition == "test"

    def test_apgi_parameters_defaults(self):
        """Test APGIParameters default values."""
        from apgi_framework.core.data_models import APGIParameters

        params = APGIParameters()

        assert params.extero_precision == 2.0
        assert params.intero_precision == 1.5
        assert params.extero_error == 1.0
        assert params.intero_error == 0.8
        assert params.somatic_gain == 1.2
        assert params.threshold == 3.5
        assert params.steepness == 2.0


class TestCorePrecision:
    """Tests for core/precision.py module."""

    def test_module_imports(self):
        """Test that precision module can be imported."""
        from apgi_framework.core import precision  # type: ignore[import-not-found]

        assert hasattr(precision, "PrecisionCalculator")

    def test_precision_calculator_initialization(self):
        """Test PrecisionCalculator initialization."""
        from apgi_framework.core.precision import PrecisionCalculator  # type: ignore[import-not-found]

        calc = PrecisionCalculator()
        assert calc is not None

    def test_calculate_precision(self):
        """Test precision calculation from samples."""
        from apgi_framework.core.precision import PrecisionCalculator  # type: ignore[import-not-found]

        calc = PrecisionCalculator()

        # Test with sample data
        samples = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        precision = calc.calculate_precision(samples)
        assert isinstance(precision, (int, float, np.number))
        assert precision > 0

    def test_calculate_exteroceptive_precision(self):
        """Test exteroceptive precision calculation."""
        from apgi_framework.core.precision import PrecisionCalculator

        calc = PrecisionCalculator()
        precision = calc.calculate_exteroceptive_precision(variance=0.5, confidence=1.0)

        assert isinstance(precision, (float, np.floating))
        assert precision > 0

    def test_calculate_interoceptive_precision(self):
        """Test interoceptive precision calculation."""
        from apgi_framework.core.precision import PrecisionCalculator

        calc = PrecisionCalculator()
        precision = calc.calculate_interoceptive_precision(variance=0.3, attention=1.0, arousal=1.0)

        assert isinstance(precision, (float, np.floating))
        assert precision > 0

    def test_precision_metrics(self):
        """Test comprehensive precision metrics."""
        from apgi_framework.core.precision import PrecisionCalculator

        calc = PrecisionCalculator()
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

        metrics = calc.precision_metrics(data)

        assert isinstance(metrics, dict)
        assert "precision" in metrics
        assert "confidence_interval_95" in metrics
        assert "coefficient_of_variation" in metrics


class TestCorePredictionError:
    """Tests for core/prediction_error.py module."""

    def test_module_imports(self):
        """Test that prediction_error module can be imported."""
        from apgi_framework.core import prediction_error  # type: ignore[import-not-found]

        assert hasattr(prediction_error, "PredictionErrorProcessor")

    def test_prediction_error_processor_initialization(self):
        """Test PredictionErrorProcessor initialization."""
        from apgi_framework.core.prediction_error import PredictionErrorProcessor

        processor = PredictionErrorProcessor()
        assert processor is not None

    def test_process_exteroceptive_error(self):
        """Test exteroceptive prediction error processing."""
        from apgi_framework.core.prediction_error import PredictionErrorProcessor

        processor = PredictionErrorProcessor(standardize=False)

        error = np.array([0.5, 0.6, 0.7])
        processed = processor.process_exteroceptive_error(error)

        assert isinstance(processed, np.ndarray)

    def test_process_interoceptive_error(self):
        """Test interoceptive prediction error processing."""
        from apgi_framework.core.prediction_error import PredictionErrorProcessor

        processor = PredictionErrorProcessor(standardize=False)

        error = np.array([0.3, 0.4, 0.5])
        processed = processor.process_interoceptive_error(error)

        assert isinstance(processed, np.ndarray)

    def test_validate_error_pair(self):
        """Test error pair validation."""
        from apgi_framework.core.prediction_error import PredictionErrorProcessor

        processor = PredictionErrorProcessor()

        valid, message = processor.validate_error_pair(0.5, 0.3)
        assert isinstance(valid, bool)
        assert isinstance(message, str)


class TestCoreSomaticMarker:
    """Tests for core/somatic_marker.py module."""

    def test_module_imports(self):
        """Test that somatic_marker module can be imported."""
        from apgi_framework.core import somatic_marker  # type: ignore[import-not-found]

        assert hasattr(somatic_marker, "SomaticMarkerEngine")
        assert hasattr(somatic_marker, "ContextType")

    def test_somatic_marker_engine_initialization(self):
        """Test SomaticMarkerEngine initialization."""
        from apgi_framework.core.somatic_marker import SomaticMarkerEngine  # type: ignore[import-not-found]

        engine = SomaticMarkerEngine()
        assert engine is not None

    def test_somatic_marker_gain_calculation(self):
        """Test somatic marker gain calculation."""
        from apgi_framework.core.somatic_marker import SomaticMarkerEngine, ContextType  # type: ignore[import-not-found]

        engine = SomaticMarkerEngine()

        # Test gain calculation for different contexts
        gain = engine.calculate_somatic_gain(ContextType.NEUTRAL)
        assert isinstance(gain, (float, np.floating))
        assert gain > 0

    def test_context_type_values(self):
        """Test ContextType enum values."""
        from apgi_framework.core.somatic_marker import ContextType

        assert ContextType.ROUTINE.value == "routine"
        assert ContextType.HIGH_STAKES.value == "high_stakes"
        assert ContextType.EMOTIONAL.value == "emotional"
        assert ContextType.NEUTRAL.value == "neutral"
