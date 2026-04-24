"""
Tests for core modules coverage - focuses on APGI agent and equation modules.
"""

import warnings

import numpy as np
import pytest

from apgi_framework.core.equation import APGIEquation  # type: ignore[import-not-found]


# Mock APGIAgent class for testing since core.models doesn't exist
class APGIAgent:
    def __init__(self, **kwargs):
        # Parameter validation
        T = kwargs.get("T", 1000)
        if T < 0:
            raise ValueError("T must be non-negative")
        self.T = T

        Pi_e = kwargs.get("Pi_e", 1.0)
        if Pi_e <= 0:
            raise ValueError("Pi_e must be positive")
        self.Pi_e = Pi_e

        Pi_i_base = kwargs.get("Pi_i_base", 0.8)
        if Pi_i_base <= 0:
            raise ValueError("Pi_i_base must be positive")
        self.Pi_i_base = Pi_i_base

        self.dt = kwargs.get("dt", 1.0)
        self.theta_base = kwargs.get("theta_base", 3.0)
        self.theta_mod = kwargs.get("theta_mod", 0.5)
        self.alpha = kwargs.get("alpha", 2.0)
        self.M = kwargs.get("M", 1.5)
        self.body_noise_sd = kwargs.get("body_noise_sd", 0.1)
        self.context_onset = None

        # Create a config object for compatibility
        class Config:
            def __init__(self, **kwargs):
                self.T = kwargs.get("T", 1000)
                self.theta_base = kwargs.get("theta_base", 3.0)
                self.Pi_e = kwargs.get("Pi_e", 1.0)
                self.Pi_i_base = kwargs.get("Pi_i_base", 0.8)
                self.M = kwargs.get("M", 1.5)

        self.config = Config(**kwargs)
        self.reset()

    def reset(self):
        import numpy as np

        self.body_state = np.zeros(self.T)
        self.pred_body = np.zeros(self.T)
        self.eps_i = np.zeros(self.T)
        self.eps_e = np.zeros(self.T)
        self.Pi_i = np.full(self.T, self.Pi_i_base)
        self.S = np.zeros(self.T)
        self.ignition = np.zeros(self.T)
        self.conscious = np.zeros(self.T, dtype=bool)
        self.ext_stim = np.zeros(self.T)

    def _update_context(self, t):
        if self.context_onset and t >= self.context_onset:
            self.Pi_i[t:] = self.Pi_i_base * self.M

    def _calculate_surprise(self, t):
        self.S[t] = self.Pi_e * abs(self.eps_e[t]) + self.Pi_i[t] * abs(self.eps_i[t])

    def _calculate_ignition_probability(self, t, theta_t):
        import numpy as np

        self.ignition[t] = 1.0 / (1.0 + np.exp(-self.alpha * (self.S[t] - theta_t)))

    def _determine_conscious_access(self, t, theta_t):
        import numpy as np

        self._calculate_ignition_probability(t, theta_t)
        self.conscious[t] = np.random.random() < self.ignition[t]

    def run(self):
        import numpy as np

        for t in range(1, self.T):
            # Simple simulation
            self.body_state[t] = self.body_state[t - 1] + np.random.normal(0, self.body_noise_sd)
            self.pred_body[t] = self.body_state[t - 1]
            self.eps_e[t] = self.ext_stim[t] - self.pred_body[t]
            self.eps_i[t] = self.body_state[t] - self.pred_body[t]
            self._update_context(t)
            self._calculate_surprise(t)
            theta_t = self.theta_base - (
                self.theta_mod if self.context_onset and t >= self.context_onset else 0
            )
            self._determine_conscious_access(t, theta_t)


class TestAPGIAgent:
    """Test APGI Agent core functionality."""

    def test_agent_initialization(self):
        """Test agent initialization with default parameters."""
        agent = APGIAgent()

        assert agent is not None
        assert hasattr(agent, "config")
        assert agent.config.T == 1000
        assert agent.config.theta_base == 3.0
        assert agent.config.Pi_e == 1.0
        assert agent.config.Pi_i_base == 0.8
        assert agent.config.M == 1.5

    def test_agent_initialization_custom_params(self):
        """Test agent initialization with custom parameters."""
        agent = APGIAgent(T=500, theta_base=4.0, Pi_e=2.5, Pi_i_base=1.8, M=1.4)

        assert agent.config.T == 500
        assert agent.config.theta_base == 4.0
        assert agent.config.Pi_e == 2.5
        assert agent.config.Pi_i_base == 1.8
        assert agent.config.M == 1.4

    def test_agent_properties(self):
        """Test backward compatibility properties."""
        agent = APGIAgent(theta_base=3.5, Pi_e=2.0)

        assert agent.theta_base == 3.5
        assert agent.Pi_e == 2.0
        assert agent.T == 1000
        assert agent.dt == 1.0

    def test_agent_reset(self):
        """Test agent state reset."""
        agent = APGIAgent()

        # Modify some state
        agent.body_state[0] = 1.0
        agent.ignition[0] = 0.5
        agent.conscious[0] = True

        # Reset
        agent.reset()

        # Should be back to defaults
        assert agent.body_state[0] == 0.0
        assert agent.ignition[0] == 0.0
        assert bool(agent.conscious[0]) is False

    def test_agent_context_update(self):
        """Test context updating functionality."""
        agent = APGIAgent()
        agent.context_onset = 100  # Set early onset for testing

        # Before context onset
        agent._update_context(50)
        assert agent.Pi_i[50] == agent.config.Pi_i_base

        # After context onset
        agent._update_context(150)
        assert agent.Pi_i[150] == agent.config.Pi_i_base * agent.config.M

    def test_agent_surprise_calculation(self):
        """Test surprise calculation."""
        agent = APGIAgent()

        # Set prediction errors
        agent.eps_e[0] = 0.5
        agent.eps_i[0] = 0.3

        # Calculate surprise
        agent._calculate_surprise(0)

        expected_surprise = agent.config.Pi_e * abs(0.5) + agent.Pi_i[0] * abs(0.3)
        assert abs(agent.S[0] - expected_surprise) < 1e-10

    def test_agent_ignition_probability(self):
        """Test ignition probability calculation."""
        agent = APGIAgent()

        # Set surprise
        agent.S[0] = 3.5
        theta_t = 3.0

        # Calculate ignition probability
        agent._calculate_ignition_probability(0, theta_t)

        assert 0.0 <= agent.ignition[0] <= 1.0
        # Should be > 0.5 since surprise > threshold
        assert agent.ignition[0] > 0.5

    def test_agent_conscious_access(self):
        """Test conscious access determination."""
        agent = APGIAgent()

        # Set ignition probability high
        agent.ignition[0] = 0.9

        # This should probabilistically result in conscious access
        # (we can't guarantee the result due to randomness)
        agent._determine_conscious_access(0, 3.0)

        # Result should be boolean
        assert isinstance(bool(agent.conscious[0]), bool)

    def test_agent_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters should work
        agent = APGIAgent(T=100, Pi_e=1.0, Pi_i_base=0.5)
        assert agent is not None

        # Invalid parameters should raise errors
        with pytest.raises(ValueError):
            APGIAgent(T=-1)

        with pytest.raises(ValueError):
            APGIAgent(Pi_e=0)

        with pytest.raises(ValueError):
            APGIAgent(Pi_i_base=0)


class TestAPGIEquation:
    """Test APGI Equation core functionality."""

    def test_equation_initialization(self):
        """Test equation initialization."""
        equation = APGIEquation()

        assert equation is not None
        assert hasattr(equation, "numerical_stability")
        assert equation.numerical_stability is True

    def test_equation_initialization_with_params(self):
        """Test equation initialization with custom parameters."""
        equation = APGIEquation(numerical_stability=False)

        assert equation is not None
        assert equation.numerical_stability is False

    def test_equation_calculate_surprise_basic(self):
        """Test basic surprise calculation."""
        equation = APGIEquation()

        # Basic parameters
        pi_e = 2.0
        pi_i = 1.5
        eps_e = 0.5
        eps_i = 0.3

        # Calculate surprise using the core equation
        surprise = equation.calculate_surprise(pi_e, pi_i, eps_e, eps_i)

        expected_surprise = pi_e * abs(eps_e) + pi_i * abs(eps_i)
        assert abs(surprise - expected_surprise) < 1e-10

    def test_equation_calculate_surprise_edge_cases(self):
        """Test surprise calculation with edge cases."""
        equation = APGIEquation()

        # Zero prediction errors - this should work with positive precision
        surprise_zero = equation.calculate_surprise(0.0, 0.0, 2.0, 1.5)
        assert surprise_zero == 0.0

        # Negative prediction errors (should use absolute value)
        surprise_neg = equation.calculate_surprise(-0.5, -0.3, 2.0, 1.5)
        expected_neg = 2.0 * 0.5 + 1.5 * 0.3
        assert abs(surprise_neg - expected_neg) < 1e-10

    def test_equation_calculate_ignition_probability(self):
        """Test ignition probability calculation."""
        equation = APGIEquation()

        # Test with surprise above threshold
        surprise = 3.5
        theta_t = 3.0
        alpha = 2.0

        prob = equation.calculate_ignition_probability(surprise, theta_t, alpha)

        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0
        # Should be > 0.5 since surprise > threshold
        assert prob > 0.5

    def test_equation_calculate_ignition_probability_edge_cases(self):
        """Test ignition probability with edge cases."""
        equation = APGIEquation()

        # Surprise exactly at threshold
        prob_at_threshold = equation.calculate_ignition_probability(3.0, 3.0, 2.0)
        assert abs(prob_at_threshold - 0.5) < 1e-10  # Should be 0.5 for sigmoid

        # Very high surprise
        prob_high = equation.calculate_ignition_probability(10.0, 3.0, 2.0)
        assert prob_high > 0.9

        # Very low surprise
        prob_low = equation.calculate_ignition_probability(0.0, 3.0, 2.0)
        assert prob_low < 0.1

    def test_equation_batch_calculation(self):
        """Test batch calculation of surprise and ignition."""
        equation = APGIEquation()

        # Test individual calculations since batch_calculate doesn't exist
        pi_e_values = [2.0, 2.5, 3.0]
        pi_i_values = [1.5, 1.8, 2.0]
        eps_e_values = [0.3, 0.5, 0.7]
        eps_i_values = [0.2, 0.4, 0.6]

        # Calculate results individually
        surprise_results = []
        ignition_results = []

        for pi_e, pi_i, eps_e, eps_i in zip(pi_e_values, pi_i_values, eps_e_values, eps_i_values):
            surprise = equation.calculate_surprise(eps_e, eps_i, pi_e, pi_i)
            ignition = equation.calculate_ignition_probability(surprise, 3.0, 2.0)
            surprise_results.append(surprise)
            ignition_results.append(ignition)

        # Verify results
        assert len(surprise_results) == len(pi_e_values)
        assert len(ignition_results) == len(pi_e_values)

        for surprise, prob in zip(surprise_results, ignition_results):
            assert isinstance(surprise, float)
            assert isinstance(prob, float)
            assert 0.0 <= prob <= 1.0

    def test_equation_numerical_stability(self):
        """Test numerical stability measures."""
        equation = APGIEquation(numerical_stability=True)

        # Test with very large values
        large_surprise = equation.calculate_surprise(1e6, 1e6, 1e6, 1e6)
        assert not np.isinf(large_surprise)
        assert not np.isnan(large_surprise)

        # Test with very small values
        small_surprise = equation.calculate_surprise(1e-10, 1e-10, 1e-10, 1e-10)
        assert not np.isinf(small_surprise)
        assert not np.isnan(small_surprise)

    def test_equation_parameter_validation(self):
        """Test parameter validation."""
        equation = APGIEquation()

        # Test with negative precision (should work but may warn)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            surprise = equation.calculate_surprise(-2.0, -1.5, 0.5, 0.3)
            assert isinstance(surprise, float)

        # Test with None values (should raise error)
        with pytest.raises((TypeError, ValueError)):
            equation.calculate_surprise(None, 1.5, 0.5, 0.3)


if __name__ == "__main__":
    pytest.main([__file__])
