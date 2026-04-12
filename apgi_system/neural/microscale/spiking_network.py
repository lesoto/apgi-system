"""
Spiking Neural Network Implementation

Implements leaky integrate-and-fire neurons with:
- Spike-timing-dependent plasticity (STDP)
- Synaptic ATP consumption tracking
- Landauer cost calculation
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class NeuronState:
    """State of a single neuron."""

    membrane_potential: float = -65.0  # mV
    spike_time: float = -np.inf
    refractory_until: float = 0.0
    adaptation_current: float = 0.0


class SpikingNeuralNetwork:
    """
    Leaky Integrate-and-Fire (LIF) spiking neural network with STDP and energy tracking.

    Implements a biologically realistic spiking neural network using the
    Leaky Integrate-and-Fire neuron model. The network includes:

    **Neuron Dynamics**:
    τ dV/dt = -(V - V_rest) + R*I_syn + R*I_ext

    When V ≥ V_threshold:
    - Emit spike
    - V := V_reset
    - Enter refractory period (2ms)

    **Key Features**:
    - **STDP Learning**: Spike-timing-dependent plasticity for synaptic learning
    - **Energy Tracking**: ATP consumption for spikes and synaptic transmission
    - **Landauer Cost**: Thermodynamic cost of information erasure
    - **Dale's Principle**: 80% excitatory, 20% inhibitory neurons
    - **Sparse Connectivity**: Configurable connection probability

    **Learning Rule (STDP)**:
    - Pre-before-post: Δw = A+ * exp(-Δt/τ+) (LTP)
    - Post-before-pre: Δw = -A- * exp(Δt/τ-) (LTD)

    **Energy Model**:
    - Spike cost: 1.0 ATP unit per action potential
    - Synapse cost: 0.1 ATP unit per synaptic transmission
    - Landauer cost: kT ln(2) per bit erased (2.87e-21 J at room temperature)

    Parameters
    ----------
    num_neurons : int
        Number of neurons in the network
    connection_probability : float, optional
        Probability of connection between any two neurons, by default 0.1
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_neurons : int
        Number of neurons
    neurons : List[NeuronState]
        State of each neuron (membrane potential, spike times, etc.)
    connectivity : np.ndarray
        Binary connectivity matrix (sparse)
    weights : np.ndarray
        Synaptic weight matrix
    synaptic_currents : np.ndarray
        Current synaptic input to each neuron
    total_energy_consumed : float
        Total ATP consumed (spikes + synapses)
    bits_erased : float
        Total information bits erased (for Landauer cost)
    spike_times : List[float]
        Times of all spikes
    spike_neurons : List[int]
        Neuron indices for all spikes

    Examples
    --------
    >>> network = SpikingNeuralNetwork(num_neurons=1000, connection_probability=0.05)
    >>> external_input = np.random.randn(1000) * 2.0  # External current
    >>> spike_mask, info = network.step(external_input, dt=0.1)
    >>> print(f"Spikes: {info['num_spikes']}, Energy: {info['energy_consumed']:.2f}")
    Spikes: 23, Energy: 25.30
    """

    def __init__(
        self,
        num_neurons: int,
        connection_probability: float = 0.1,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize spiking network.

        Args:
            num_neurons: Number of neurons
            connection_probability: Probability of connection between neurons
            config: Configuration dictionary
        """
        self.num_neurons = num_neurons
        self.config = config or {}

        # Neuron parameters
        self.tau_membrane = 20.0  # ms, membrane time constant
        self.v_rest = -65.0  # mV
        self.v_threshold = -50.0  # mV
        self.v_reset = -70.0  # mV
        self.refractory_period = 2.0  # ms

        # Synaptic parameters
        self.tau_syn = 5.0  # ms, synaptic time constant
        self.w_excite_init = 0.5  # Initial excitatory weight
        self.w_inhibit_init = -0.8  # Initial inhibitory weight

        # Initialize neurons
        self.neurons = [NeuronState() for _ in range(num_neurons)]

        # Initialize connectivity
        self.connectivity = self._initialize_connectivity(connection_probability)
        self.weights = self._initialize_weights()

        # Synaptic current buffer
        self.synaptic_currents = np.zeros(num_neurons)

        # STDP parameters
        self.tau_stdp_plus = 20.0  # ms
        self.tau_stdp_minus = 20.0  # ms
        self.a_plus = 0.01  # LTP amplitude
        self.a_minus = 0.01  # LTD amplitude

        # Energy tracking
        self.spike_energy_cost = 1.0  # ATP units per spike
        self.synapse_energy_cost = 0.1  # ATP units per synaptic transmission
        self.total_energy_consumed = 0.0

        # Landauer cost tracking
        self.landauer_cost_per_bit = 2.87e-21  # Joules at room temperature (kT ln2)
        self.bits_erased = 0.0

        # Recording
        self.spike_times: List[float] = []
        self.spike_neurons: List[int] = []

    def _initialize_connectivity(self, prob: float) -> np.ndarray:
        """
        Initialize random sparse connectivity.

        Args:
            prob: Connection probability

        Returns:
            Binary connectivity matrix
        """
        connectivity = np.random.rand(self.num_neurons, self.num_neurons) < prob
        # No self-connections
        np.fill_diagonal(connectivity, False)
        return connectivity

    def _initialize_weights(self) -> np.ndarray:
        """Initialize synaptic weights."""
        weights = np.zeros((self.num_neurons, self.num_neurons))

        # 80% excitatory, 20% inhibitory (Dale's principle)
        num_excitatory = int(0.8 * self.num_neurons)

        for i in range(self.num_neurons):
            for j in range(self.num_neurons):
                if self.connectivity[i, j]:
                    if i < num_excitatory:
                        weights[i, j] = self.w_excite_init
                    else:
                        weights[i, j] = self.w_inhibit_init

        return weights

    def step(
        self, external_input: np.ndarray, dt: float = 0.1
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Simulate one timestep.

        Args:
            external_input: External input current to each neuron
            dt: Timestep in ms

        Returns:
            spike_mask: Boolean array indicating which neurons spiked
            info: Dictionary with metrics
        """
        spike_mask = np.zeros(self.num_neurons, dtype=bool)
        current_time = len(self.spike_times) * dt if self.spike_times else 0

        # Update each neuron
        for i, neuron in enumerate(self.neurons):
            # Skip if in refractory period
            if current_time < neuron.refractory_until:
                continue

            # Total input current
            i_total = external_input[i] + self.synaptic_currents[i]

            # Update membrane potential
            dv = dt / self.tau_membrane * (-(neuron.membrane_potential - self.v_rest) + i_total)
            neuron.membrane_potential += dv

            # Check for spike
            if neuron.membrane_potential >= self.v_threshold:
                # Emit spike
                spike_mask[i] = True
                neuron.spike_time = current_time
                neuron.membrane_potential = self.v_reset
                neuron.refractory_until = current_time + self.refractory_period

                # Record spike
                self.spike_times.append(current_time)
                self.spike_neurons.append(i)

                # Energy cost
                self.total_energy_consumed += self.spike_energy_cost

                # Information erasure (spike generated, bit erased)
                self.bits_erased += 1.0

        # Update synaptic currents
        self._update_synaptic_currents(spike_mask, dt)

        # STDP learning
        if np.any(spike_mask):
            self._apply_stdp(spike_mask, current_time)

        # Decay synaptic currents
        self.synaptic_currents *= np.exp(-dt / self.tau_syn)

        # Compute metrics
        info = {
            "num_spikes": int(np.sum(spike_mask)),
            "mean_potential": float(np.mean([n.membrane_potential for n in self.neurons])),
            "energy_consumed": self.total_energy_consumed,
            "landauer_cost": self.bits_erased * self.landauer_cost_per_bit,
            "firing_rate": len(self.spike_times) / (self.num_neurons * max(current_time, 1)),
        }

        return spike_mask, info

    def _update_synaptic_currents(self, spike_mask: np.ndarray, dt: float) -> None:
        """Update synaptic currents from spikes."""
        for i in range(self.num_neurons):
            if spike_mask[i]:
                # Add synaptic input to all postsynaptic neurons
                postsynaptic = self.connectivity[i, :]
                self.synaptic_currents[postsynaptic] += self.weights[i, postsynaptic]

                # Energy cost for synaptic transmission
                num_synapses = np.sum(postsynaptic)
                self.total_energy_consumed += num_synapses * self.synapse_energy_cost

    def _apply_stdp(self, spike_mask: np.ndarray, current_time: float) -> None:
        """
        Apply spike-timing-dependent plasticity.

        Δw = A_+ exp(-Δt/τ_+)  if pre before post (LTP)
        Δw = -A_- exp(Δt/τ_-)  if post before pre (LTD)
        """
        for post_idx in range(self.num_neurons):
            if not spike_mask[post_idx]:
                continue

            post_spike_time = current_time

            # Find presynaptic neurons
            for pre_idx in range(self.num_neurons):
                if not self.connectivity[pre_idx, post_idx]:
                    continue

                pre_spike_time = self.neurons[pre_idx].spike_time

                if pre_spike_time > -np.inf:
                    dt_spike = post_spike_time - pre_spike_time

                    if dt_spike > 0:
                        # Pre before post: LTP
                        dw = self.a_plus * np.exp(-dt_spike / self.tau_stdp_plus)
                    else:
                        # Post before pre: LTD
                        dw = -self.a_minus * np.exp(dt_spike / self.tau_stdp_minus)

                    # Update weight
                    self.weights[pre_idx, post_idx] += dw

                    # Clamp weights
                    if self.weights[pre_idx, post_idx] > 0:
                        self.weights[pre_idx, post_idx] = min(self.weights[pre_idx, post_idx], 2.0)
                    else:
                        self.weights[pre_idx, post_idx] = max(self.weights[pre_idx, post_idx], -2.0)

    def get_firing_rates(self, window_ms: float = 100.0) -> np.ndarray:
        """
        Compute recent firing rates.

        Args:
            window_ms: Time window in ms

        Returns:
            Firing rates for each neuron (Hz)
        """
        if not self.spike_times:
            return np.zeros(self.num_neurons)

        current_time = self.spike_times[-1]
        window_start = max(0, current_time - window_ms)

        rates = np.zeros(self.num_neurons)
        for spike_time, neuron_idx in zip(self.spike_times, self.spike_neurons):
            if spike_time >= window_start:
                rates[neuron_idx] += 1

        # Convert to Hz
        rates = rates / (window_ms / 1000.0)

        return rates

    def reset(self) -> None:
        """Reset network state."""
        self.neurons = [NeuronState() for _ in range(self.num_neurons)]
        self.synaptic_currents = np.zeros(self.num_neurons)
        self.spike_times = []
        self.spike_neurons = []
        self.total_energy_consumed = 0.0
        self.bits_erased = 0.0
