"""
Large-Scale Neural Networks

Implements macroscale brain networks:
- Frontoparietal workspace network (global broadcasting)
- Salience network (interoception and attention switching)
- Default mode network (self-modeling and simulation)
"""

import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum


class NetworkType(Enum):
    """Types of large-scale networks."""
    FRONTOPARIETAL = "frontoparietal"
    SALIENCE = "salience"
    DEFAULT_MODE = "default_mode"
    SENSORY = "sensory"


class FrontoparietalNetwork:
    """
    Frontoparietal workspace network.

    Implements global workspace theory:
    - Sparse long-range connections
    - Recurrent amplification
    - Winner-take-all dynamics
    - Broadcasting mechanism
    """

    def __init__(self, num_nodes: int = 1000, config: Optional[Dict[str, Any]] = None):
        """
        Initialize frontoparietal network.

        Args:
            num_nodes: Number of workspace nodes
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.config = config or {}

        # Network state
        self.activity = np.zeros(num_nodes)
        self.broadcast_state = np.zeros(num_nodes)

        # Connectivity (sparse long-range)
        self.connection_density = 0.05  # 5% connectivity
        self.weights = self._initialize_weights()

        # Dynamics parameters
        self.tau = 20.0  # ms, time constant
        self.amplification_gain = 2.0  # Recurrent amplification
        self.competition_strength = 0.5  # Winner-take-all

        # Broadcasting
        self.is_broadcasting = False
        self.broadcast_content = None
        self.broadcast_start_time = None

    def _initialize_weights(self) -> np.ndarray:
        """Initialize sparse connectivity."""
        weights = np.random.randn(self.num_nodes, self.num_nodes) * 0.1
        # Make sparse
        mask = np.random.rand(self.num_nodes, self.num_nodes) < self.connection_density
        weights *= mask
        np.fill_diagonal(weights, 0)
        return weights

    def update(
        self,
        external_input: np.ndarray,
        ignition_signal: bool = False,
        dt: float = 1.0
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Update network activity.

        Args:
            external_input: Input from other networks
            ignition_signal: Whether ignition occurred
            dt: Timestep in ms

        Returns:
            activity: Current workspace activity
            info: Diagnostic information
        """
        # Recurrent input
        recurrent_input = self.weights @ self.activity

        # Competition (soft winner-take-all)
        competition = -self.competition_strength * np.mean(self.activity)

        # Total input
        total_input = external_input + self.amplification_gain * recurrent_input + competition

        # Update activity
        dactivity = (dt / self.tau) * (-self.activity + total_input)
        self.activity += dactivity

        # Apply nonlinearity
        self.activity = np.maximum(0, self.activity)  # ReLU

        # Normalization to prevent explosion
        max_activity = np.max(self.activity)
        if max_activity > 10.0:
            self.activity *= 10.0 / max_activity

        # Handle broadcasting
        if ignition_signal and not self.is_broadcasting:
            self._initiate_broadcast()
        elif self.is_broadcasting:
            self._maintain_broadcast(dt)

        info = {
            'mean_activity': float(np.mean(self.activity)),
            'max_activity': float(np.max(self.activity)),
            'active_nodes': int(np.sum(self.activity > 0.1)),
            'is_broadcasting': self.is_broadcasting
        }

        return self.activity.copy(), info

    def _initiate_broadcast(self):
        """Initiate global broadcast."""
        self.is_broadcasting = True
        # Winner pattern becomes broadcast content
        self.broadcast_content = self.activity.copy()
        self.broadcast_state = self.broadcast_content
        self.broadcast_start_time = 0.0

    def _maintain_broadcast(self, dt: float):
        """Maintain broadcast for sustained period."""
        broadcast_duration = 300.0  # ms

        if self.broadcast_start_time is not None:
            self.broadcast_start_time += dt

            if self.broadcast_start_time > broadcast_duration:
                # End broadcast
                self.is_broadcasting = False
                self.broadcast_content = None
                self.broadcast_start_time = None
            else:
                # Maintain broadcast state
                self.broadcast_state = self.broadcast_content

    def get_broadcast(self) -> Optional[np.ndarray]:
        """Get current broadcast content."""
        if self.is_broadcasting:
            return self.broadcast_state.copy()
        return None

    def reset(self):
        """Reset network."""
        self.activity = np.zeros(self.num_nodes)
        self.broadcast_state = np.zeros(self.num_nodes)
        self.is_broadcasting = False
        self.broadcast_content = None


class SalienceNetwork:
    """
    Salience network.

    Functions:
    - Integrates interoceptive signals (insula analog)
    - Detects salient events (ACC analog)
    - Switches attention between networks
    - Modulates precision
    """

    def __init__(self, num_nodes: int = 200, config: Optional[Dict[str, Any]] = None):
        """
        Initialize salience network.

        Args:
            num_nodes: Number of nodes
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.config = config or {}

        # Subregions
        self.insula_nodes = num_nodes // 2  # Interoceptive processing
        self.acc_nodes = num_nodes // 2     # Conflict/salience detection

        self.insula_activity = np.zeros(self.insula_nodes)
        self.acc_activity = np.zeros(self.acc_nodes)

        # Parameters
        self.tau = 30.0  # ms
        self.salience_threshold = 1.0

        # Switching state
        self.current_attention = None  # Which network is prioritized

    def update(
        self,
        interoceptive_input: np.ndarray,
        exteroceptive_input: np.ndarray,
        conflict_signal: float = 0.0,
        dt: float = 1.0
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Update salience network.

        Args:
            interoceptive_input: Body state signals
            exteroceptive_input: External signals
            conflict_signal: Conflict/uncertainty signal
            dt: Timestep in ms

        Returns:
            activity: Dictionary with subregion activities
            info: Diagnostic information
        """
        # Insula processes interoceptive signals
        # Pad interoceptive input to match insula nodes
        intero_padded = np.zeros(self.insula_nodes)
        intero_padded[:min(len(interoceptive_input), self.insula_nodes)] = \
            interoceptive_input[:min(len(interoceptive_input), self.insula_nodes)]

        target_insula = intero_padded
        dinsula = (dt / self.tau) * (target_insula - self.insula_activity)
        self.insula_activity += dinsula
        self.insula_activity = np.maximum(0, self.insula_activity)

        # ACC processes conflict and prediction errors
        # Pad interoceptive input for ACC processing
        intero_acc_padded = np.zeros(self.acc_nodes//2)
        intero_acc_padded[:min(len(interoceptive_input), self.acc_nodes//2)] = \
            interoceptive_input[:min(len(interoceptive_input), self.acc_nodes//2)]

        combined_signal = np.concatenate([
            exteroceptive_input[:self.acc_nodes//2],
            intero_acc_padded
        ])[:self.acc_nodes]

        # Add conflict signal
        conflict_component = conflict_signal * np.ones(self.acc_nodes)
        target_acc = combined_signal + conflict_component

        dacc = (dt / self.tau) * (target_acc - self.acc_activity)
        self.acc_activity += dacc
        self.acc_activity = np.maximum(0, self.acc_activity)

        # Compute overall salience
        salience = np.mean(self.acc_activity) + 0.5 * np.mean(self.insula_activity)

        # Attention switching
        if salience > self.salience_threshold:
            # High interoceptive activity -> attend inward
            if np.mean(self.insula_activity) > np.mean(exteroceptive_input[:self.num_nodes]):
                self.current_attention = "interoceptive"
            else:
                self.current_attention = "exteroceptive"

        activity = {
            'insula': self.insula_activity.copy(),
            'acc': self.acc_activity.copy()
        }

        info = {
            'salience': float(salience),
            'attention_target': self.current_attention,
            'insula_activity': float(np.mean(self.insula_activity)),
            'acc_activity': float(np.mean(self.acc_activity))
        }

        return activity, info

    def get_precision_modulation(self) -> Dict[str, float]:
        """
        Get precision modulation signals.

        Returns modulation factors for different channels.
        """
        intero_modulation = 1.0 + 0.5 * np.mean(self.insula_activity)
        extero_modulation = 1.0 + 0.3 * np.mean(self.acc_activity)

        return {
            'interoceptive': float(intero_modulation),
            'exteroceptive': float(extero_modulation)
        }

    def reset(self):
        """Reset network."""
        self.insula_activity = np.zeros(self.insula_nodes)
        self.acc_activity = np.zeros(self.acc_nodes)
        self.current_attention = None


class DefaultModeNetwork:
    """
    Default mode network.

    Functions:
    - Self-referential processing
    - Autobiographical memory
    - Mental simulation
    - Narrative self-model
    """

    def __init__(self, num_nodes: int = 300, config: Optional[Dict[str, Any]] = None):
        """
        Initialize default mode network.

        Args:
            num_nodes: Number of nodes
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.config = config or {}

        # Activity
        self.activity = np.zeros(num_nodes)

        # Subregions
        self.mpfc_activity = np.zeros(num_nodes // 3)  # Self-referential
        self.pcc_activity = np.zeros(num_nodes // 3)   # Memory integration
        self.tpj_activity = np.zeros(num_nodes // 3)   # Perspective-taking

        # Parameters
        self.tau = 100.0  # Slow dynamics
        self.self_coupling = 0.8  # Strong recurrent connections

        # Self-model state
        self.self_representation = np.zeros(num_nodes)
        self.narrative_buffer = []

    def update(
        self,
        self_related_input: np.ndarray,
        memory_input: np.ndarray,
        task_activity: float = 0.0,
        dt: float = 1.0
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Update default mode network.

        Args:
            self_related_input: Self-referential signals
            memory_input: Episodic memory signals
            task_activity: External task demands (suppresses DMN)
            dt: Timestep in ms

        Returns:
            activity: DMN activity
            info: Diagnostic information
        """
        # DMN is anti-correlated with task activity
        suppression = 1.0 - 0.7 * task_activity

        # Update subregions
        # Pad self-related input to match mpfc size
        self_padded = np.zeros(len(self.mpfc_activity))
        self_padded[:min(len(self_related_input), len(self.mpfc_activity))] = \
            self_related_input[:min(len(self_related_input), len(self.mpfc_activity))]

        target_mpfc = self_padded * suppression
        dmpfc = (dt / self.tau) * (target_mpfc - self.mpfc_activity)
        self.mpfc_activity += dmpfc

        # Pad memory input to match pcc size
        memory_padded = np.zeros(len(self.pcc_activity))
        memory_padded[:min(len(memory_input), len(self.pcc_activity))] = \
            memory_input[:min(len(memory_input), len(self.pcc_activity))]

        target_pcc = memory_padded * suppression
        dpcc = (dt / self.tau) * (target_pcc - self.pcc_activity)
        self.pcc_activity += dpcc

        # TPJ integrates
        target_tpj = 0.5 * (self.mpfc_activity[:len(self.tpj_activity)] +
                           self.pcc_activity[:len(self.tpj_activity)])
        dtpj = (dt / self.tau) * (target_tpj - self.tpj_activity)
        self.tpj_activity += dtpj

        # Combine into overall activity
        self.activity[:len(self.mpfc_activity)] = self.mpfc_activity
        self.activity[len(self.mpfc_activity):2*len(self.mpfc_activity)] = self.pcc_activity
        self.activity[2*len(self.mpfc_activity):] = self.tpj_activity

        # Apply nonlinearity
        self.activity = np.maximum(0, self.activity)

        # Update self-representation (slow integration)
        self.self_representation = 0.99 * self.self_representation + 0.01 * self.activity

        info = {
            'mean_activity': float(np.mean(self.activity)),
            'mpfc_activity': float(np.mean(self.mpfc_activity)),
            'pcc_activity': float(np.mean(self.pcc_activity)),
            'suppression_factor': float(suppression)
        }

        return self.activity.copy(), info

    def get_self_representation(self) -> np.ndarray:
        """Get current self-model representation."""
        return self.self_representation.copy()

    def reset(self):
        """Reset network."""
        self.activity = np.zeros(self.num_nodes)
        self.mpfc_activity = np.zeros(self.num_nodes // 3)
        self.pcc_activity = np.zeros(self.num_nodes // 3)
        self.tpj_activity = np.zeros(self.num_nodes // 3)
        self.self_representation = np.zeros(self.num_nodes)


class LargeScaleNetworkManager:
    """
    Manages interactions between large-scale networks.

    Coordinates:
    - Frontoparietal (workspace/consciousness)
    - Salience (attention/interoception)
    - Default mode (self/simulation)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize network manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize networks
        ignition_config = config.get('ignition', {})
        workspace_nodes = ignition_config.get('workspace_nodes', 1000)

        self.frontoparietal = FrontoparietalNetwork(
            num_nodes=workspace_nodes,
            config=config
        )
        self.salience = SalienceNetwork(num_nodes=200, config=config)
        self.default_mode = DefaultModeNetwork(num_nodes=300, config=config)

        # Interaction strengths
        self.fp_to_dmn = -0.5  # Frontoparietal suppresses DMN
        self.sal_to_fp = 0.8   # Salience activates frontoparietal
        self.dmn_to_sal = 0.3  # DMN weakly activates salience

    def update(
        self,
        extero_input: np.ndarray,
        intero_input: np.ndarray,
        ignition_signal: bool,
        conflict_signal: float,
        dt: float = 1.0
    ) -> Dict[str, Any]:
        """
        Update all networks and their interactions.

        Args:
            extero_input: Exteroceptive input
            intero_input: Interoceptive input
            ignition_signal: Whether ignition occurred
            conflict_signal: Conflict/uncertainty
            dt: Timestep

        Returns:
            Dictionary with all network states
        """
        # Update salience network
        sal_activity, sal_info = self.salience.update(
            interoceptive_input=intero_input,
            exteroceptive_input=extero_input,
            conflict_signal=conflict_signal,
            dt=dt
        )

        # Frontoparietal input (from salience)
        sal_mean = np.mean(sal_activity['acc'])
        fp_input = sal_mean * self.sal_to_fp * np.random.rand(self.frontoparietal.num_nodes)

        # Update frontoparietal network
        fp_activity, fp_info = self.frontoparietal.update(
            external_input=fp_input,
            ignition_signal=ignition_signal,
            dt=dt
        )

        # Default mode (suppressed by task/frontoparietal activity)
        task_activity = np.mean(fp_activity)
        dmn_activity, dmn_info = self.default_mode.update(
            self_related_input=intero_input,
            memory_input=extero_input,
            task_activity=task_activity,
            dt=dt
        )

        return {
            'frontoparietal': {'activity': fp_activity, 'info': fp_info},
            'salience': {'activity': sal_activity, 'info': sal_info},
            'default_mode': {'activity': dmn_activity, 'info': dmn_info},
            'broadcast': self.frontoparietal.get_broadcast()
        }

    def reset(self):
        """Reset all networks."""
        self.frontoparietal.reset()
        self.salience.reset()
        self.default_mode.reset()
