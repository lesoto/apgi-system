"""
Large-Scale Neural Networks

Implements macroscale brain networks:
- Frontoparietal workspace network (global broadcasting)
- Salience network (interoception and attention switching)
- Default mode network (self-modeling and simulation)
"""

import threading
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


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

    def __init__(
        self, num_nodes: int = 1000, batch_size: int = 1, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize frontoparietal network.

        Args:
            num_nodes: Number of workspace nodes
            batch_size: Number of parallel agent simulations
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.batch_size = batch_size
        self.config = config or {}
        self._lock = threading.Lock()

        # Network state: (B, D)
        self.activity = np.zeros((batch_size, num_nodes))
        self.broadcast_state = np.zeros((batch_size, num_nodes))

        # Connectivity (sparse long-range) - Shared across agents?
        # Yes, usually the architecture is the same.
        self.connection_density = 0.05  # 5% connectivity
        self.weights = self._initialize_weights()

        # Dynamics parameters
        self.tau = 20.0  # ms, time constant
        self.amplification_gain = 2.0  # Recurrent amplification
        self.competition_strength = 0.5  # Winner-take-all

        # Broadcasting state for each agent
        self.is_broadcasting = np.zeros(batch_size, dtype=bool)
        self.broadcast_content = np.zeros((batch_size, num_nodes))
        self.broadcast_start_time = np.zeros(batch_size)

    def _initialize_weights(self) -> np.ndarray:
        """Initialize sparse connectivity."""
        weights = np.random.randn(self.num_nodes, self.num_nodes) * 0.1
        # Make sparse
        mask = np.random.rand(self.num_nodes, self.num_nodes) < self.connection_density
        weights *= mask
        np.fill_diagonal(weights, 0)
        return weights

    def update(
        self, external_input: np.ndarray, ignition_signal: np.ndarray, dt: float = 1.0
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Update workspace activity for all agents in batch (B, D)."""
        with self._lock:
            # recurrent_input: (B, D)
            recurrent_input = self.activity @ self.weights.T

            # Mean-field competition (B, 1)
            competition = -self.competition_strength * np.mean(self.activity, axis=1, keepdims=True)

            # Total input: (B, D)
            total_input = external_input + self.amplification_gain * recurrent_input + competition

            # Update activity (Euler integration)
            dactivity = (dt / self.tau) * (-self.activity + total_input)
            self.activity += dactivity

            # Apply nonlinearity and clipping for stability
            self.activity = np.clip(self.activity, 0.0, 10.0)

            # Initiate broadcasts (B,)
            ignition_bool = np.asarray(ignition_signal, dtype=bool)
            initiate_mask = ignition_bool & ~self.is_broadcasting
            if np.any(initiate_mask):
                self.is_broadcasting[initiate_mask] = True
                self.broadcast_content[initiate_mask] = self.activity[initiate_mask].copy()
                self.broadcast_start_time[initiate_mask] = 0.0

            # Maintain existing broadcasts
            if np.any(self.is_broadcasting):
                self.broadcast_start_time[self.is_broadcasting] += dt

                # Expiry check
                broadcast_duration = 300.0
                expired_mask = self.is_broadcasting & (
                    self.broadcast_start_time > broadcast_duration
                )
                if np.any(expired_mask):
                    self.is_broadcasting[expired_mask] = False
                    self.broadcast_content[expired_mask] = 0.0

                # Update broadcast state
                self.broadcast_state.fill(0.0)
                active_mask = self.is_broadcasting
                if np.any(active_mask):
                    self.broadcast_state[active_mask] = self.broadcast_content[active_mask]

            info = {
                "mean_activity": float(np.mean(self.activity)),
                "is_broadcasting": self.is_broadcasting.copy(),
            }

            return self.activity.copy(), info

    def get_broadcast(self) -> np.ndarray:
        """Get current broadcast content for all agents (B, D)."""
        return self.broadcast_state.copy()

    def reset(self) -> None:
        """Reset network for all agents in batch."""
        self.activity.fill(0.0)
        self.broadcast_state.fill(0.0)
        self.is_broadcasting.fill(False)
        self.broadcast_content.fill(0.0)
        self.broadcast_start_time.fill(0.0)


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

    def __init__(
        self, num_nodes: int = 200, batch_size: int = 1, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize salience network.

        Args:
            num_nodes: Number of nodes
            batch_size: Number of parallel agent simulations
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.batch_size = batch_size
        self.config = config or {}
        self._lock = threading.Lock()

        # Subregions
        self.insula_nodes = num_nodes // 2  # Interoceptive processing
        self.acc_nodes = num_nodes // 2  # Conflict/salience detection

        self.insula_activity = np.zeros((batch_size, self.insula_nodes))
        self.acc_activity = np.zeros((batch_size, self.acc_nodes))

        # Parameters
        self.tau = 30.0  # ms
        self.salience_threshold = 1.0

        # Switching state
        self.current_attention = np.array([None] * batch_size)  # Which network is prioritized

    def update(
        self,
        interoceptive_input: Union[np.ndarray, float],
        exteroceptive_input: Union[np.ndarray, float],
        conflict_signal: Union[np.ndarray, float],
        dt: float = 1.0,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        Update salience network for all agents.

        Args:
            interoceptive_input: Body state signals (B, D_intero)
            exteroceptive_input: External signals (B, D_extero)
            conflict_signal: Conflict/uncertainty signal (B,)
            dt: Timestep in ms

        Returns:
            activity: Dictionary with subregion activities (B, D)
            info: Diagnostic information
        """
        with self._lock:
            # 1. Insula processes interoceptive signals
            # Ensure input shape compatibility (B, D)
            if not isinstance(interoceptive_input, np.ndarray):
                interoceptive_input = np.array([interoceptive_input])

            if interoceptive_input.ndim == 1:
                # If batch_size is 1, it might be (D,). If batch_size > 1 and it's (D,), something is wrong.
                # Assume (D,) represents a single agent if batch_size=1, or needs broadcast if batch_size > 1.
                if self.batch_size == 1:
                    interoceptive_input = interoceptive_input[np.newaxis, :]
                else:
                    # Broadcast to match batch_size
                    interoceptive_input = np.tile(interoceptive_input, (self.batch_size, 1))

            b_size = interoceptive_input.shape[0]
            # Map interoceptive input to insular nodes (B, D_insula)
            target_insula = np.zeros((b_size, self.insula_nodes))
            d_min = min(interoceptive_input.shape[1], self.insula_nodes)
            target_insula[:, :d_min] = interoceptive_input[:, :d_min]

            dinsula = (dt / self.tau) * (target_insula - self.insula_activity)
            self.insula_activity += dinsula
            self.insula_activity = np.maximum(0, self.insula_activity)

            # 2. ACC processes conflict and prediction errors
            if not isinstance(exteroceptive_input, np.ndarray):
                exteroceptive_input = np.array([exteroceptive_input])

            if exteroceptive_input.ndim == 1:
                if self.batch_size == 1:
                    exteroceptive_input = exteroceptive_input[np.newaxis, :]
                else:
                    exteroceptive_input = np.tile(exteroceptive_input, (self.batch_size, 1))

            # Ensure conflict_signal is a batch array (B,)
            if not isinstance(conflict_signal, np.ndarray):
                conflict_signal = np.full(b_size, float(conflict_signal))
            elif conflict_signal.shape != (b_size,):
                conflict_signal = np.full(b_size, float(np.mean(conflict_signal)))

            # Hybrid signal: exteroceptive + interoceptive
            acc_half = self.acc_nodes // 2
            combined_signal = np.zeros((b_size, self.acc_nodes))

            d_extero = min(exteroceptive_input.shape[1], acc_half)
            combined_signal[:, :d_extero] = exteroceptive_input[:, :d_extero]

            d_intero = min(interoceptive_input.shape[1], acc_half)
            combined_signal[:, acc_half : acc_half + d_intero] = interoceptive_input[:, :d_intero]

            # Multiply by conflict signal (B,) broadcasted to (B, D_acc)
            target_acc = combined_signal + conflict_signal[:, np.newaxis]

            dacc = (dt / self.tau) * (target_acc - self.acc_activity)
            self.acc_activity += dacc
            self.acc_activity = np.maximum(0, self.acc_activity)

            # 3. Compute overall salience (B,)
            salience = np.mean(self.acc_activity, axis=1) + 0.5 * np.mean(
                self.insula_activity, axis=1
            )

            # 4. Attention switching (B,)
            high_salience_mask = salience > self.salience_threshold
            if np.any(high_salience_mask):
                insula_mean = np.mean(self.insula_activity, axis=1)
                extero_mean = np.mean(exteroceptive_input, axis=1)

                inward_mask = high_salience_mask & (insula_mean > extero_mean)
                outward_mask = high_salience_mask & ~inward_mask

                self.current_attention[inward_mask] = "interoceptive"
                self.current_attention[outward_mask] = "exteroceptive"

            activity = {"insula": self.insula_activity.copy(), "acc": self.acc_activity.copy()}

            info = {
                "salience": float(np.mean(salience)),
                "insula_activity": float(np.mean(self.insula_activity)),
                "acc_activity": float(np.mean(self.acc_activity)),
            }

            return activity, info

    def get_precision_modulation(self) -> Dict[str, np.ndarray]:
        """
        Get precision modulation signals for all agents.

        Returns:
            Dictionary with modulation factors (B,)
        """
        # (B,)
        intero_modulation = 1.0 + 0.5 * np.mean(self.insula_activity, axis=1)
        extero_modulation = 1.0 + 0.3 * np.mean(self.acc_activity, axis=1)

        return {
            "interoceptive": intero_modulation,
            "exteroceptive": extero_modulation,
        }

    def reset(self) -> None:
        """Reset network."""
        self.insula_activity.fill(0.0)
        self.acc_activity.fill(0.0)
        self.current_attention.fill(None)


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

    def __init__(
        self, num_nodes: int = 300, batch_size: int = 1, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize default mode network.

        Args:
            num_nodes: Number of nodes
            batch_size: Number of agents
            config: Configuration dictionary
        """
        self.num_nodes = num_nodes
        self.batch_size = batch_size
        self.config = config or {}
        self._lock = threading.Lock()

        # Activity subregions (B, D)
        self.mpfc_activity = np.zeros((batch_size, num_nodes // 3))
        self.pcc_activity = np.zeros((batch_size, num_nodes // 3))
        self.tpj_activity = np.zeros((batch_size, num_nodes // 3))
        self.activity = np.zeros((batch_size, num_nodes))

        # Parameters
        self.tau = 100.0  # Slow dynamics
        self.self_coupling = 0.8  # Strong recurrent connections

        # Self-model state
        self.self_representation = np.zeros((batch_size, num_nodes))
        self.narrative_buffer: List[List[str]] = [[] for _ in range(batch_size)]

    def update(
        self,
        self_related_input: Union[np.ndarray, float],
        memory_input: Union[np.ndarray, float],
        task_activity: Union[np.ndarray, float],
        dt: float = 1.0,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Update default mode network for all agents.

        Args:
            self_related_input: Self-referential signals (B, D)
            memory_input: Episodic memory signals (B, D)
            task_activity: External task demands (B,) - suppresses DMN
            dt: Timestep in ms
        """
        with self._lock:
            # DMN is anti-correlated with task activity
            if not isinstance(task_activity, np.ndarray):
                task_activity = np.full(self.batch_size, float(task_activity))

            suppression = (1.0 - 0.7 * task_activity)[:, np.newaxis]  # (B, 1)

            # Ensure inputs are arrays
            if not isinstance(self_related_input, np.ndarray):
                self_related_input = np.array([self_related_input])
            if self_related_input.ndim == 1:
                self_related_input = (
                    self_related_input[np.newaxis, :]
                    if self.batch_size == 1
                    else np.tile(self_related_input, (self.batch_size, 1))
                )

            if not isinstance(memory_input, np.ndarray):
                memory_input = np.array([memory_input])
            if memory_input.ndim == 1:
                memory_input = (
                    memory_input[np.newaxis, :]
                    if self.batch_size == 1
                    else np.tile(memory_input, (self.batch_size, 1))
                )

            # mPFC (Self)
            n_mpfc = self.mpfc_activity.shape[1]
            target_mpfc = np.zeros_like(self.mpfc_activity)
            d_self = min(self_related_input.shape[1], n_mpfc)
            target_mpfc[:, :d_self] = self_related_input[:, :d_self] * suppression

            dmpfc = (dt / self.tau) * (target_mpfc - self.mpfc_activity)
            self.mpfc_activity += dmpfc

            # PCC (Memory)
            n_pcc = self.pcc_activity.shape[1]
            target_pcc = np.zeros_like(self.pcc_activity)
            d_mem = min(memory_input.shape[1], n_pcc)
            target_pcc[:, :d_mem] = memory_input[:, :d_mem] * suppression

            dpcc = (dt / self.tau) * (target_pcc - self.pcc_activity)
            self.pcc_activity += dpcc

            # TPJ (Integration)
            target_tpj = 0.5 * (self.mpfc_activity + self.pcc_activity)
            dtpj = (dt / self.tau) * (target_tpj - self.tpj_activity)
            self.tpj_activity += dtpj

            # Combine into overall activity: (B, D)
            off0 = 0
            off1 = n_mpfc
            off2 = off1 + self.pcc_activity.shape[1]

            self.activity[:, off0:off1] = self.mpfc_activity
            self.activity[:, off1:off2] = self.pcc_activity
            self.activity[:, off2:] = self.tpj_activity

            self.activity = np.maximum(0, self.activity)

            # Update slowly-evolving self-representation
            self.self_representation = 0.99 * self.self_representation + 0.01 * self.activity

            info = {
                "mean_activity": float(np.mean(self.activity)),
                "suppression_factor": float(np.mean(suppression)),
            }

            return self.activity.copy(), info

    def get_self_representation(self) -> np.ndarray:
        """Get current self-model representation."""
        return self.self_representation.copy()

    def reset(self) -> None:
        """Reset network."""
        self.activity = np.zeros((self.batch_size, self.num_nodes))
        self.mpfc_activity = np.zeros((self.batch_size, self.num_nodes // 3))
        self.pcc_activity = np.zeros((self.batch_size, self.num_nodes // 3))
        self.tpj_activity = np.zeros((self.batch_size, self.num_nodes // 3))
        self.self_representation = np.zeros((self.batch_size, self.num_nodes))


class LargeScaleNetworkManager:
    """Coordinates interactions between large-scale brain networks."""

    def __init__(self, config: Dict[str, Any], batch_size: int = 1):
        """
        Initialize network manager.

        Args:
            config: Configuration dictionary
            batch_size: Number of agents
        """
        self.config = config
        self.batch_size = batch_size
        self._lock = threading.Lock()

        # Initialize networks with batch support
        ignition_config = config.get("ignition", {})
        workspace_nodes = ignition_config.get("workspace_nodes", 1000)

        self.frontoparietal = FrontoparietalNetwork(
            num_nodes=workspace_nodes, batch_size=batch_size, config=config
        )
        self.salience = SalienceNetwork(num_nodes=200, batch_size=batch_size, config=config)
        self.default_mode = DefaultModeNetwork(num_nodes=300, batch_size=batch_size, config=config)

        # Interaction strengths
        self.sal_to_fp = 0.8  # Salience activates frontoparietal
        self.fp_to_dmn = -0.5  # Frontoparietal suppresses DMN

    def update(
        self,
        extero_input: np.ndarray,
        intero_input: np.ndarray,
        ignition_signal: np.ndarray,
        conflict_signal: np.ndarray,
        dt: float = 1.0,
    ) -> Dict[str, Any]:
        """Update all networks for batch."""
        with self._lock:
            # 1. Salience (Attention switching)
            sal_activity, sal_info = self.salience.update(
                interoceptive_input=intero_input,
                exteroceptive_input=extero_input,
                conflict_signal=conflict_signal,
                dt=dt,
            )

            # 2. FP input (B, D_fp)
            # From ACC mean activity (B, 1) to FP nodes (B, D_fp)
            sal_acc_mean = np.mean(sal_activity["acc"], axis=1, keepdims=True)
            fp_drive = sal_acc_mean * self.sal_to_fp
            # Sparse project drive? For now use scalar drive
            fp_activity, fp_info = self.frontoparietal.update(
                external_input=fp_drive, ignition_signal=ignition_signal, dt=dt
            )

            # 3. DMN suppression
            task_engagement = np.mean(fp_activity, axis=1)
            dmn_activity, dmn_info = self.default_mode.update(
                self_related_input=intero_input,
                memory_input=extero_input,
                task_activity=task_engagement,
                dt=dt,
            )

            return {
                "frontoparietal": fp_info,
                "broadcast": self.frontoparietal.get_broadcast(),
                "salience": sal_info,
                "default_mode": dmn_info,
            }

    def get_network_states(self) -> Dict[str, Any]:
        """Get current states of all networks."""
        return {
            "frontoparietal": {
                "activity": self.frontoparietal.activity.copy(),
                "is_broadcasting": self.frontoparietal.is_broadcasting.copy(),
            },
            "salience": {
                "insula_activity": self.salience.insula_activity.copy(),
                "acc_activity": self.salience.acc_activity.copy(),
                "current_attention": self.salience.current_attention.copy(),
            },
            "default_mode": {
                "activity": self.default_mode.activity.copy(),
                "self_representation": self.default_mode.self_representation.copy(),
            },
        }

    def reset(self) -> None:
        """Reset all networks."""
        self.frontoparietal.reset()
        self.salience.reset()
        self.default_mode.reset()
