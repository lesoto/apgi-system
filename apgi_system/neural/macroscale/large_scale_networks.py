"""
Large-Scale Neural Networks

Implements macroscale brain networks:
- Frontoparietal workspace network (global broadcasting)
- Salience network (interoception and attention switching)
- Default mode network (self-modeling and simulation)
"""

import numpy as np
import threading
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
    Frontoparietal workspace network implementing Global Workspace Theory.

    This network models the frontoparietal control network that serves as
    the neural substrate for conscious access and global information
    broadcasting. It implements key principles of Global Workspace Theory:

    **Architecture**:
    - Sparse long-range connections (5% connectivity by default)
    - Recurrent amplification loops for signal enhancement
    - Winner-take-all competition dynamics
    - Global broadcasting mechanism for conscious access

    **Dynamics**:
    - Nodes compete through lateral inhibition
    - Winning patterns are amplified through recurrent connections
    - Ignition events trigger sustained broadcasting (300-500ms)
    - Activity normalization prevents runaway excitation

    The network maintains two key states:
    1. **Competitive state**: Multiple patterns compete for dominance
    2. **Broadcasting state**: Winner pattern is globally broadcast

    Parameters
    ----------
    num_nodes : int, optional
        Number of workspace nodes, by default 1000
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_nodes : int
        Number of nodes in the workspace
    activity : np.ndarray
        Current activity pattern across nodes
    broadcast_state : np.ndarray
        Current broadcast pattern (active during ignition)
    weights : np.ndarray
        Sparse connectivity matrix between nodes
    is_broadcasting : bool
        Whether network is currently in broadcasting mode
    broadcast_content : Optional[np.ndarray]
        Pattern being broadcast (None if not broadcasting)
    broadcast_start_time : Optional[float]
        Time when current broadcast began

    Examples
    --------
    >>> network = FrontoparietalNetwork(num_nodes=500)
    >>> external_input = np.random.randn(500) * 0.1
    >>> activity, info = network.update(external_input, ignition_signal=True)
    >>> print(f"Broadcasting: {info['is_broadcasting']}")
    Broadcasting: True
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
        self, external_input: np.ndarray, ignition_signal: bool = False, dt: float = 1.0
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
        with threading.Lock():
            # Recurrent input with enhanced overflow protection
            # Check weights and activity for numerical stability before computation
            self.weights = np.nan_to_num(self.weights, nan=0.0, posinf=1.0, neginf=-1.0)
            self.activity = np.nan_to_num(self.activity, nan=0.0, posinf=1.0, neginf=-1.0)

            # Apply gradient clipping to prevent extreme values
            self.weights = np.clip(self.weights, -10, 10)
            self.activity = np.clip(self.activity, 0, 5)

            # Thread-safe matrix multiplication
            recurrent_input = self.weights @ self.activity

            # Enhanced numerical stability checks
            if not np.all(np.isfinite(recurrent_input)):
                # Reset to safe values if overflow occurs
                self.weights = np.clip(self.weights, -5, 5)
                self.activity = np.clip(self.activity, 0.1, 2)
                # Thread-safe matrix multiplication in recovery path
                recurrent_input = self.weights @ self.activity

                # Log warning for debugging
                import warnings

                warnings.warn(
                    "Numerical instability detected in recurrent computation, values reset",
                    RuntimeWarning,
                )

            # Competition (soft winner-take-all)
            competition = -self.competition_strength * np.mean(self.activity)

            # Total input with bounds checking
            total_input = external_input + self.amplification_gain * recurrent_input + competition

            # Check total input for numerical issues
            if not np.all(np.isfinite(total_input)):
                total_input = np.clip(total_input, -100, 100)

            # Update activity
            dactivity = (dt / self.tau) * (-self.activity + total_input)

            # Check derivative for numerical issues
            if not np.all(np.isfinite(dactivity)):
                dactivity = np.clip(dactivity, -10, 10)

            self.activity += dactivity

            # Apply nonlinearity
            self.activity = np.maximum(0, self.activity)  # ReLU

            # Normalization to prevent explosion
            max_activity = np.max(self.activity)
            if max_activity > 10.0:
                self.activity *= 10.0 / max_activity

        # Handle broadcasting
        if ignition_signal and not self.is_broadcasting:
            with threading.Lock():
                self._initiate_broadcast()
        elif self.is_broadcasting:
            with threading.Lock():
                self._maintain_broadcast(dt)

        with threading.Lock():
            info = {
                "mean_activity": float(np.mean(self.activity)),
                "max_activity": float(np.max(self.activity)),
                "active_nodes": int(np.sum(self.activity > 0.1)),
                "is_broadcasting": self.is_broadcasting,
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
    Salience network for interoceptive processing and attention switching.

    Models the salience network, a key brain system that integrates
    interoceptive (body-based) and exteroceptive (external) information
    to detect salient events and control attention switching. The network
    consists of two main subregions:

    **Insula Analog**:
    - Processes interoceptive signals from the body
    - Integrates physiological state information
    - Generates interoceptive awareness

    **Anterior Cingulate Cortex (ACC) Analog**:
    - Detects conflicts and prediction errors
    - Monitors salience of events
    - Triggers attention switching

    **Key Functions**:
    - Integrates body state signals for interoceptive awareness
    - Detects salient events requiring attention
    - Switches attention between internal (interoceptive) and external focus
    - Modulates precision weights for different information channels
    - Controls network interactions (e.g., suppressing default mode)

    Parameters
    ----------
    num_nodes : int, optional
        Total number of nodes in the network, by default 200
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_nodes : int
        Total number of nodes
    insula_nodes : int
        Number of nodes in insula subregion (half of total)
    acc_nodes : int
        Number of nodes in ACC subregion (half of total)
    insula_activity : np.ndarray
        Current activity in insula subregion
    acc_activity : np.ndarray
        Current activity in ACC subregion
    current_attention : Optional[str]
        Current attention target ('interoceptive' or 'exteroceptive')
    salience_threshold : float
        Threshold for triggering attention switching

    Examples
    --------
    >>> network = SalienceNetwork(num_nodes=100)
    >>> intero_input = np.array([0.8, 0.6, 0.9])  # Body signals
    >>> extero_input = np.array([0.2, 0.3, 0.1])  # External signals
    >>> activity, info = network.update(intero_input, extero_input, conflict_signal=0.5)
    >>> print(f"Attention target: {info['attention_target']}")
    Attention target: interoceptive
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
        self.acc_nodes = num_nodes // 2  # Conflict/salience detection

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
        dt: float = 1.0,
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
        intero_padded[: min(len(interoceptive_input), self.insula_nodes)] = interoceptive_input[
            : min(len(interoceptive_input), self.insula_nodes)
        ]

        target_insula = intero_padded
        dinsula = (dt / self.tau) * (target_insula - self.insula_activity)
        self.insula_activity += dinsula
        self.insula_activity = np.maximum(0, self.insula_activity)

        # ACC processes conflict and prediction errors
        # Pad interoceptive input for ACC processing
        intero_acc_padded = np.zeros(self.acc_nodes // 2)
        intero_acc_padded[: min(len(interoceptive_input), self.acc_nodes // 2)] = (
            interoceptive_input[: min(len(interoceptive_input), self.acc_nodes // 2)]
        )

        combined_signal = np.concatenate(
            [exteroceptive_input[: self.acc_nodes // 2], intero_acc_padded]
        )[: self.acc_nodes]

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
            if np.mean(self.insula_activity) > np.mean(exteroceptive_input[: self.num_nodes]):
                self.current_attention = "interoceptive"
            else:
                self.current_attention = "exteroceptive"

        activity = {"insula": self.insula_activity.copy(), "acc": self.acc_activity.copy()}

        info = {
            "salience": float(salience),
            "attention_target": self.current_attention,
            "insula_activity": float(np.mean(self.insula_activity)),
            "acc_activity": float(np.mean(self.acc_activity)),
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
            "interoceptive": float(intero_modulation),
            "exteroceptive": float(extero_modulation),
        }

    def reset(self):
        """Reset network."""
        self.insula_activity = np.zeros(self.insula_nodes)
        self.acc_activity = np.zeros(self.acc_nodes)
        self.current_attention = None


class DefaultModeNetwork:
    """
    Default mode network for self-referential processing and simulation.

    Models the default mode network (DMN), a brain system active during
    rest and introspective tasks. The DMN is crucial for self-referential
    thinking, autobiographical memory, and mental simulation. It shows
    anti-correlation with task-positive networks.

    **Subregions**:
    - **Medial Prefrontal Cortex (mPFC)**: Self-referential processing,
      theory of mind, moral reasoning
    - **Posterior Cingulate Cortex (PCC)**: Autobiographical memory
      integration, self-awareness
    - **Temporoparietal Junction (TPJ)**: Perspective-taking, social
      cognition, integration hub

    **Key Functions**:
    - Self-referential and introspective processing
    - Autobiographical memory retrieval and integration
    - Mental simulation and prospective thinking
    - Narrative self-model construction and maintenance
    - Mind-wandering and spontaneous thought

    **Dynamics**:
    - High baseline activity during rest
    - Suppressed by external task demands
    - Slow temporal dynamics (100ms time constant)
    - Strong recurrent connectivity within network

    Parameters
    ----------
    num_nodes : int, optional
        Total number of nodes in the network, by default 300
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary, by default None

    Attributes
    ----------
    num_nodes : int
        Total number of nodes
    activity : np.ndarray
        Current overall network activity
    mpfc_activity : np.ndarray
        Activity in medial prefrontal cortex subregion
    pcc_activity : np.ndarray
        Activity in posterior cingulate cortex subregion
    tpj_activity : np.ndarray
        Activity in temporoparietal junction subregion
    self_representation : np.ndarray
        Slowly-evolving self-model representation
    narrative_buffer : List
        Buffer for narrative elements (currently unused)

    Examples
    --------
    >>> network = DefaultModeNetwork(num_nodes=150)
    >>> self_input = np.random.randn(50) * 0.1  # Self-related signals
    >>> memory_input = np.random.randn(50) * 0.1  # Memory signals
    >>> activity, info = network.update(self_input, memory_input, task_activity=0.2)
    >>> print(f"DMN suppression: {info['suppression_factor']:.2f}")
    DMN suppression: 0.86
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
        self.pcc_activity = np.zeros(num_nodes // 3)  # Memory integration
        self.tpj_activity = np.zeros(num_nodes // 3)  # Perspective-taking

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
        dt: float = 1.0,
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
        self_padded[: min(len(self_related_input), len(self.mpfc_activity))] = self_related_input[
            : min(len(self_related_input), len(self.mpfc_activity))
        ]

        target_mpfc = self_padded * suppression
        dmpfc = (dt / self.tau) * (target_mpfc - self.mpfc_activity)
        self.mpfc_activity += dmpfc

        # Pad memory input to match pcc size
        memory_padded = np.zeros(len(self.pcc_activity))
        memory_padded[: min(len(memory_input), len(self.pcc_activity))] = memory_input[
            : min(len(memory_input), len(self.pcc_activity))
        ]

        target_pcc = memory_padded * suppression
        dpcc = (dt / self.tau) * (target_pcc - self.pcc_activity)
        self.pcc_activity += dpcc

        # TPJ integrates
        target_tpj = 0.5 * (
            self.mpfc_activity[: len(self.tpj_activity)]
            + self.pcc_activity[: len(self.tpj_activity)]
        )
        dtpj = (dt / self.tau) * (target_tpj - self.tpj_activity)
        self.tpj_activity += dtpj

        # Combine into overall activity
        self.activity[: len(self.mpfc_activity)] = self.mpfc_activity
        self.activity[len(self.mpfc_activity) : 2 * len(self.mpfc_activity)] = self.pcc_activity
        self.activity[2 * len(self.mpfc_activity) :] = self.tpj_activity

        # Apply nonlinearity
        self.activity = np.maximum(0, self.activity)

        # Update self-representation (slow integration)
        self.self_representation = 0.99 * self.self_representation + 0.01 * self.activity

        info = {
            "mean_activity": float(np.mean(self.activity)),
            "mpfc_activity": float(np.mean(self.mpfc_activity)),
            "pcc_activity": float(np.mean(self.pcc_activity)),
            "suppression_factor": float(suppression),
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
    Coordinates interactions between large-scale brain networks.

    Manages the dynamic interactions between three major brain networks
    that are crucial for consciousness and cognitive function:

    **Network Interactions**:
    - **Frontoparietal ↔ Salience**: Salience network activates workspace
      for conscious access when salient events are detected
    - **Frontoparietal ↔ Default Mode**: Task-positive frontoparietal
      activity suppresses default mode network (anti-correlation)
    - **Salience ↔ Default Mode**: Salience network can activate default
      mode during introspective attention

    **Coordination Functions**:
    - Routes information between networks based on attention state
    - Implements network switching for different cognitive modes
    - Manages competition and cooperation between networks
    - Coordinates global brain states (focused vs. introspective)

    The manager implements known principles of large-scale brain organization:
    - Anti-correlation between task-positive and default networks
    - Salience network as attention switch between networks
    - Dynamic reconfiguration based on cognitive demands

    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary containing network parameters

    Attributes
    ----------
    frontoparietal : FrontoparietalNetwork
        Workspace network for conscious access
    salience : SalienceNetwork
        Salience detection and attention switching
    default_mode : DefaultModeNetwork
        Self-referential and simulation network
    fp_to_dmn : float
        Interaction strength from frontoparietal to default mode (negative)
    sal_to_fp : float
        Interaction strength from salience to frontoparietal (positive)
    dmn_to_sal : float
        Interaction strength from default mode to salience (weak positive)

    Examples
    --------
    >>> config = {'ignition': {'workspace_nodes': 500}}
    >>> manager = LargeScaleNetworkManager(config)
    >>> extero = np.random.randn(100) * 0.1
    >>> intero = np.random.randn(6) * 0.1
    >>> result = manager.update(extero, intero, ignition_signal=True, conflict_signal=0.3)
    >>> print(f"Broadcasting: {result['frontoparietal']['info']['is_broadcasting']}")
    Broadcasting: True
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize network manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize networks
        ignition_config = config.get("ignition", {})
        workspace_nodes = ignition_config.get("workspace_nodes", 1000)

        self.frontoparietal = FrontoparietalNetwork(num_nodes=workspace_nodes, config=config)
        self.salience = SalienceNetwork(num_nodes=200, config=config)
        self.default_mode = DefaultModeNetwork(num_nodes=300, config=config)

        # Interaction strengths
        self.fp_to_dmn = -0.5  # Frontoparietal suppresses DMN
        self.sal_to_fp = 0.8  # Salience activates frontoparietal
        self.dmn_to_sal = 0.3  # DMN weakly activates salience

    def update(
        self,
        extero_input: np.ndarray,
        intero_input: np.ndarray,
        ignition_signal: bool,
        conflict_signal: float,
        dt: float = 1.0,
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
            dt=dt,
        )

        # Frontoparietal input (from salience)
        sal_mean = np.mean(sal_activity["acc"])
        fp_input = sal_mean * self.sal_to_fp * np.random.rand(self.frontoparietal.num_nodes)

        # Update frontoparietal network
        fp_activity, fp_info = self.frontoparietal.update(
            external_input=fp_input, ignition_signal=ignition_signal, dt=dt
        )

        # Default mode (suppressed by task/frontoparietal activity)
        task_activity = np.mean(fp_activity)
        dmn_activity, dmn_info = self.default_mode.update(
            self_related_input=intero_input,
            memory_input=extero_input,
            task_activity=task_activity,
            dt=dt,
        )

        return {
            "frontoparietal": {"activity": fp_activity, "info": fp_info},
            "salience": {"activity": sal_activity, "info": sal_info},
            "default_mode": {"activity": dmn_activity, "info": dmn_info},
            "broadcast": self.frontoparietal.get_broadcast(),
        }

    def get_network_states(self) -> Dict[str, Any]:
        """Get current states of all networks."""
        return {
            "frontoparietal": {
                "activity": self.frontoparietal.activity.copy(),
                "is_broadcasting": self.frontoparietal.is_broadcasting,
                "mean_activity": float(np.mean(self.frontoparietal.activity)),
            },
            "salience": {
                "insula_activity": self.salience.insula_activity.copy(),
                "acc_activity": self.salience.acc_activity.copy(),
                "current_attention": self.salience.current_attention,
            },
            "default_mode": {
                "activity": self.default_mode.activity.copy(),
                "self_representation": self.default_mode.self_representation.copy(),
                "mean_activity": float(np.mean(self.default_mode.activity)),
            },
        }

    def reset(self):
        """Reset all networks."""
        self.frontoparietal.reset()
        self.salience.reset()
        self.default_mode.reset()
