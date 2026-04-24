"""
Test suite for core equation module.
"""

import pytest
import numpy as np
from apgi_framework.engines import APGIEquation


class TestAPGIEquation:
    """Test cases for APGI Equation core functionality."""

    def test_equation_initialization(self):
        """Test APGIEquation initialization."""
        equation = APGIEquation()
        assert equation is not None
        assert hasattr(equation, "numerical_stability")
        assert hasattr(equation, "precision_calculator")
        assert hasattr(equation, "prediction_error_processor")
        assert hasattr(equation, "somatic_marker_engine")
        assert hasattr(equation, "threshold_manager")

    def test_equation_parameters(self):
        """Test equation parameter handling."""
        equation = APGIEquation(numerical_stability=True, max_sigmoid_input=10.0)
        assert equation.numerical_stability is True
        assert equation._max_sigmoid_input == 10.0

    def test_calculate_surprise(self):
        """Test surprise calculation."""
        equation = APGIEquation()
        # Test with valid inputs
        surprise = equation.calculate_surprise(
            extero_error=1.0,
            intero_error=1.0,
            extero_precision=2.0,
            intero_precision=1.5,
        )
        assert surprise is not None
        assert isinstance(surprise, (float, np.ndarray))

    def test_calculate_ignition_probability(self):
        """Test ignition probability calculation."""
        equation = APGIEquation()
        # Test with valid inputs
        prob = equation.calculate_ignition_probability(surprise=2.0, threshold=3.5, steepness=2.0)
        assert prob is not None
        assert isinstance(prob, (float, np.ndarray))
        assert 0 <= prob <= 1

    def test_calculate_full_equation(self):
        """Test full equation calculation."""
        equation = APGIEquation()
        # Test with valid inputs
        result = equation.calculate_full_equation(
            extero_error=1.0,
            intero_error=1.0,
            extero_precision=2.0,
            intero_precision=1.5,
            threshold=3.5,
            steepness=2.0,
        )
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        surprise, probability = result
        assert isinstance(surprise, (float, np.ndarray))
        assert isinstance(probability, (float, np.ndarray))

    def test_parameter_validation(self):
        """Test parameter validation."""
        equation = APGIEquation()
        # Test that invalid steepness raises error
        from apgi_framework.exceptions import MathematicalError

        with pytest.raises(MathematicalError):
            equation.calculate_ignition_probability(
                surprise=2.0, threshold=3.5, steepness=0.0  # Invalid: zero steepness
            )

    def test_array_inputs(self):
        """Test equation with array inputs."""
        equation = APGIEquation()
        # Test with numpy arrays - use individual elements since full_equation expects scalars
        extero_errors = np.array([0.5, 1.0, 1.5])
        intero_errors = np.array([0.8, 1.2, 1.0])

        # Test individual array elements
        for i in range(len(extero_errors)):
            result = equation.calculate_full_equation(
                extero_error=float(extero_errors[i]),
                intero_error=float(intero_errors[i]),
                extero_precision=2.0,
                intero_precision=1.5,
                threshold=3.5,
                steepness=2.0,
            )
            assert isinstance(result, tuple)
            assert len(result) == 2
            surprise, probability = result
            assert isinstance(surprise, (float, np.ndarray))
            assert isinstance(probability, (float, np.ndarray))

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        equation = APGIEquation()

        # Test with zero surprise
        prob = equation.calculate_ignition_probability(surprise=0.0, threshold=3.5, steepness=2.0)
        assert prob is not None

        # Test with very high surprise
        prob = equation.calculate_ignition_probability(surprise=10.0, threshold=3.5, steepness=2.0)
        assert prob is not None
        assert prob > 0.5  # High surprise should give high probability


if __name__ == "__main__":
    pytest.main([__file__])
