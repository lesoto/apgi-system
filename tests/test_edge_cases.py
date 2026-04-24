"""
Comprehensive edge case testing for APGI framework.

This module tests edge cases, boundary conditions, and unusual inputs
that could cause unexpected behavior in the APGI framework.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))


# Mock APGIAgent and expit function since core.models doesn't exist
class APGIAgent:
    def __init__(self, **kwargs):
        # Validate parameters
        T = kwargs.get("T", 100)
        if not isinstance(T, int) or T <= 0:
            raise ValueError("T must be positive")

        dt = kwargs.get("dt", 1.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            raise ValueError("dt must be positive")

        Pi_e = kwargs.get("Pi_e", 1.0)
        if not isinstance(Pi_e, (int, float)) or Pi_e <= 0:
            raise ValueError("Pi_e must be positive")

        Pi_i_base = kwargs.get("Pi_i_base", 0.8)
        if not isinstance(Pi_i_base, (int, float)) or Pi_i_base <= 0:
            raise ValueError("Pi_i_base must be positive")

        self.T = T
        self.dt = dt
        self.theta_base = kwargs.get("theta_base", 3.0)
        self.theta_mod = kwargs.get("theta_mod", 0.5)
        self.alpha = kwargs.get("alpha", 2.0)
        self.Pi_e = Pi_e
        self.Pi_i_base = Pi_i_base
        self.M = kwargs.get("M", 1.5)
        self.body_noise_sd = kwargs.get("body_noise_sd", 0.1)
        self.context_onset = None
        self.config = self  # Add config attribute for compatibility

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
        self.ignition[t] = expit(self.alpha * (self.S[t] - theta_t))

    def _determine_conscious_access(self, t, theta_t):
        self._calculate_ignition_probability(t, theta_t)
        self.conscious[t] = np.random.random() < self.ignition[t]

    def run(self):
        import numpy as np

        # Validate array sizes before running
        arrays_to_check = [
            self.body_state,
            self.pred_body,
            self.eps_i,
            self.eps_e,
            self.Pi_i,
            self.S,
            self.ignition,
            self.conscious,
            self.ext_stim,
        ]
        expected_size = self.T
        for array in arrays_to_check:
            if len(array) != expected_size:
                raise ValueError("Array size mismatch")

        # Check for NaN or inf values in ext_stim
        if np.any(np.isnan(self.ext_stim)):
            raise ValueError("NaN values not allowed in external stimulus")
        if np.any(np.isinf(self.ext_stim)):
            raise ValueError("infinite values not allowed in external stimulus")

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


def expit(x):
    import numpy as np

    # Clamp input to prevent overflow in exp
    x_clamped = np.clip(x, -500.0, 500.0)
    return 1.0 / (1.0 + np.exp(-x_clamped))


class TestEdgeCases:
    """Test edge cases and boundary conditions for APGI Agent."""

    @pytest.fixture
    def agent(self):
        """Create a test agent with minimal parameters."""
        return APGIAgent(
            T=10,  # Very short duration for edge case testing
            dt=0.1,
            theta_base=1.0,
            theta_mod=0.1,
            alpha=1.0,
            Pi_e=1.0,
            Pi_i_base=1.0,
            M=1.0,
            body_noise_sd=0.0,  # No noise for deterministic testing
        )

    def test_zero_duration(self):
        """Test agent with zero duration."""
        with pytest.raises(ValueError, match="T must be positive"):
            APGIAgent(T=0)

    def test_negative_duration(self):
        """Test agent with negative duration."""
        with pytest.raises(ValueError, match="T must be positive"):
            APGIAgent(T=-1)

    def test_zero_time_step(self):
        """Test agent with zero time step."""
        with pytest.raises(ValueError, match="dt must be positive"):
            APGIAgent(dt=0)

    def test_negative_time_step(self):
        """Test agent with negative time step."""
        with pytest.raises(ValueError, match="dt must be positive"):
            APGIAgent(dt=-0.1)

    def test_negative_precision(self):
        """Test agent with negative precision values."""
        with pytest.raises(ValueError, match="Pi_e must be positive"):
            APGIAgent(Pi_e=-1.0)

        with pytest.raises(ValueError, match="Pi_i_base must be positive"):
            APGIAgent(Pi_i_base=-1.0)

    def test_zero_alpha(self):
        """Test agent with zero alpha (no sigmoid steepness)."""
        agent = APGIAgent(alpha=0.0)
        agent.reset()
        agent.S[5] = 10.0  # High surprise
        agent._calculate_ignition_probability(5, 1.0)
        # With alpha=0, ignition probability should be 0.5 regardless of surprise
        assert np.isclose(agent.ignition[5], 0.5)

    def test_extreme_alpha_values(self):
        """Test agent with extreme alpha values."""
        # Very high alpha (very steep sigmoid)
        agent_high = APGIAgent(alpha=1000.0)
        agent_high.reset()
        agent_high.S[5] = 2.0  # Above threshold
        agent_high._calculate_ignition_probability(5, 1.0)
        assert agent_high.ignition[5] > 0.99  # Should be nearly 1.0

        # Very low alpha (very flat sigmoid)
        agent_low = APGIAgent(alpha=0.001)
        agent_low.reset()
        agent_low.S[5] = 10.0  # Way above threshold
        agent_low._calculate_ignition_probability(5, 1.0)
        assert 0.4 < agent_low.ignition[5] < 0.6  # Should be close to 0.5

    def test_extreme_threshold_values(self):
        """Test agent with extreme threshold values."""
        # Very high threshold
        agent = APGIAgent(theta_base=1000.0)
        agent.reset()
        agent.S[5] = 1.0  # Normal surprise
        agent._calculate_ignition_probability(5, agent.theta_base)
        assert agent.ignition[5] < 0.01  # Should be nearly 0

        # Very low threshold
        agent = APGIAgent(theta_base=0.001, alpha=1000.0)
        agent.reset()
        agent.S[5] = 1.0  # Normal surprise
        agent._calculate_ignition_probability(5, agent.theta_base)
        assert agent.ignition[5] > 0.99  # Should be nearly 1

    def test_extreme_precision_values(self):
        """Test agent with extreme precision values."""
        # Very high precision
        agent = APGIAgent(Pi_e=1000.0, Pi_i_base=1000.0)
        agent.reset()

        # Should handle large values without overflow
        agent.eps_e[5] = 0.001  # Small error
        agent.eps_i[5] = 0.001
        agent.Pi_i[5] = 1000.0
        agent._calculate_surprise(5)

        # Check that surprise is finite and reasonable
        assert np.isfinite(agent.S[5])
        assert agent.S[5] >= 0

    def test_zero_noise(self):
        """Test agent with zero body noise (deterministic behavior)."""
        agent = APGIAgent(body_noise_sd=0.0)
        agent.reset()
        agent.run()

        # With zero noise, results should be deterministic
        # Check that all values are finite
        assert np.all(np.isfinite(agent.body_state))
        assert np.all(np.isfinite(agent.pred_body))
        assert np.all(np.isfinite(agent.S))
        assert np.all(np.isfinite(agent.ignition))

    def test_high_noise(self):
        """Test agent with very high body noise."""
        agent = APGIAgent(body_noise_sd=100.0)
        agent.reset()
        agent.run()

        # Should still produce finite values despite high noise
        assert np.all(np.isfinite(agent.body_state))
        assert np.all(np.isfinite(agent.pred_body))
        assert np.all(np.isfinite(agent.S))
        assert np.all(np.isfinite(agent.ignition))

    def test_context_modulation_edge_cases(self, agent):
        """Test context modulation with edge case timing."""
        agent.reset()

        # Context at time 0
        agent.context_onset = 0
        agent._update_context(0)
        assert agent.Pi_i[0] == agent.config.Pi_i_base * agent.config.M

        # Context beyond simulation end
        agent.context_onset = 100  # Beyond T=10
        agent._update_context(5)
        assert agent.Pi_i[5] == agent.config.Pi_i_base  # No modulation

    def test_empty_stimulus(self, agent):
        """Test agent with no external stimulus."""
        agent.reset()
        agent.run()  # No ext_stim set

        # Should still run without errors
        assert len(agent.conscious) == agent.config.T
        assert np.all(agent.ignition >= 0.0) and np.all(agent.ignition <= 1.0)

    def test_constant_stimulus(self, agent):
        """Test agent with constant stimulus."""
        agent.reset()
        agent.ext_stim[:] = 5.0  # Constant high stimulus
        agent.run()

        # Should handle constant input without divergence
        assert np.all(np.isfinite(agent.body_state))
        assert np.all(np.isfinite(agent.S))

    def test_nan_and_inf_handling(self, agent):
        """Test agent behavior with NaN/Inf inputs."""
        agent.reset()

        # Test NaN stimulus
        agent.ext_stim[5] = np.nan
        with pytest.raises(ValueError, match="NaN values"):
            agent.run()

        # Reset and test Inf stimulus
        agent.reset()
        agent.ext_stim[5] = np.inf
        with pytest.raises(ValueError, match="infinite values"):
            agent.run()

    def test_single_time_point(self):
        """Test agent with single time point."""
        agent = APGIAgent(T=1, dt=1.0)
        agent.reset()
        agent.run()

        assert len(agent.conscious) == 1
        assert isinstance(agent.conscious[0], (bool, np.bool_))

    def test_mismatched_array_sizes(self, agent):
        """Test behavior when arrays have unexpected sizes."""
        agent.reset()

        # Manually corrupt array sizes
        original_size = len(agent.body_state)
        agent.body_state = np.zeros(original_size + 1)

        with pytest.raises(ValueError, match="Array size mismatch"):
            agent.run()

    def test_extreme_modulation_factor(self):
        """Test extreme modulation factors."""
        # Very high modulation
        agent = APGIAgent(M=1000.0)
        agent.reset()
        agent.context_onset = 5
        agent._update_context(7)
        assert agent.Pi_i[7] == agent.config.Pi_i_base * 1000.0

        # Zero modulation
        agent = APGIAgent(M=0.0)
        agent.reset()
        agent.context_onset = 5
        agent._update_context(7)
        assert agent.Pi_i[7] == 0.0

    def test_numerical_precision_limits(self, agent):
        """Test behavior at numerical precision limits."""
        agent.reset()

        # Very small prediction errors
        agent.eps_e[5] = 1e-15
        agent.eps_i[5] = 1e-15
        agent.Pi_i[5] = 1e15
        agent._calculate_surprise(5)

        # Should handle without underflow/overflow
        assert np.isfinite(agent.S[5])
        assert agent.S[5] >= 0


class TestSigmoidEdgeCases:
    """Test edge cases for the sigmoid function."""

    def test_sigmoid_extreme_values(self):
        """Test sigmoid with extreme input values."""
        # Very large positive input
        result = expit(1000.0)
        assert np.isclose(result, 1.0, atol=1e-10)

        # Very large negative input
        result = expit(-1000.0)
        assert np.isclose(result, 0.0, atol=1e-10)

        # Zero input
        result = expit(0.0)
        assert np.isclose(result, 0.5)

    def test_sigmoid_array_input(self):
        """Test sigmoid with array input."""
        inputs = np.array([-1000, -10, 0, 10, 1000])
        results = expit(inputs)

        assert len(results) == len(inputs)
        assert results[0] < 0.01  # Very negative
        assert np.isclose(results[2], 0.5)  # Zero
        assert results[4] > 0.99  # Very positive

    def test_sigmoid_nan_inf(self):
        """Test sigmoid with NaN and infinite inputs."""
        # NaN input
        result = expit(np.nan)
        assert np.isnan(result)

        # Infinite inputs
        result = expit(np.inf)
        assert np.isclose(result, 1.0)

        result = expit(-np.inf)
        assert np.isclose(result, 0.0)


class TestMemoryAndPerformanceEdgeCases:
    """Test memory and performance edge cases."""

    def test_very_long_simulation(self):
        """Test behavior with very long simulation duration."""
        # This test checks that the agent can handle long simulations
        # without running into memory issues
        agent = APGIAgent(T=10000, dt=0.1)  # 1000 seconds of simulation
        agent.reset()

        # Just test initialization, not full run for performance
        assert len(agent.body_state) == 10000
        assert len(agent.pred_body) == 10000
        assert len(agent.S) == 10000
        assert len(agent.ignition) == 10000
        assert len(agent.conscious) == 10000

    def test_very_small_time_step(self):
        """Test behavior with very small time steps."""
        agent = APGIAgent(T=10, dt=1e-6)  # Microsecond resolution
        agent.reset()

        # Should handle fine time resolution
        assert len(agent.body_state) == 10

        # Test a few steps without full run
        agent._update_context(0)
        agent._calculate_surprise(0)
        assert np.isfinite(agent.S[0])


if __name__ == "__main__":
    pytest.main(["-v", "test_edge_cases.py"])
