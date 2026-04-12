"""
Main APGI System Integrator

Integrates all subsystems into a cohesive consciousness model.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

import numpy as np
import yaml
from numpy.typing import NDArray

from apgi_system.config_validator import ConfigValidationError, ConfigValidator
from apgi_system.core import ActiveInferenceEngine, HierarchicalPredictor, PrecisionWeighting
from apgi_system.ignition import GlobalWorkspace, IgnitionThreshold
from apgi_system.interoception import AllostaticRegulator, BodyModel, SomaticMarkerSystem
from apgi_system.monitoring import PerformanceMonitor
from apgi_system.neural.macroscale.large_scale_networks import LargeScaleNetworkManager
from apgi_system.neural.oscillations import OscillationEngine
from apgi_system.platform_utils import get_resource_path
from apgi_system.self_model import CoherenceMaintenance, MinimalSelf, NarrativeSelf
from apgi_system.thermodynamic import EntropyTracker, MetabolicBudget


class APGISystem:
    """
    Complete Allostatic Precision-Gated Ignition System.

    Integrates:
    - Active inference engine
    - Hierarchical predictive processing
    - Precision weighting
    - Interoceptive prediction
    - Somatic markers
    - Ignition dynamics
    - Global workspace
    - Self-model
    - Metabolic constraints
    - Neural oscillations
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize APGI system.

        Args:
            config_path: Path to YAML configuration file (relative to project root or absolute)
        """
        # Load configuration
        config_file_path: str
        if config_path is None:
            config_file_path = str(get_resource_path("config/default.yaml"))
        else:
            # If provided path is relative, resolve it using get_resource_path
            config_path_obj = Path(config_path)
            if not config_path_obj.is_absolute():
                config_file_path = str(get_resource_path(config_path))
            else:
                config_file_path = str(config_path_obj)

        with open(config_file_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Validate configuration
        validator = ConfigValidator()
        try:
            validator.validate(self.config)
        except ConfigValidationError as e:
            raise ValueError(f"Configuration validation failed:\n{e}") from e

        # Initialize all subsystems
        self._initialize_subsystems()

        # System state
        self.time = 0.0
        self.timestep_ms = self.config["system"]["timestep_ms"]
        self.is_running = False

        # History for analysis - use bounded deques to prevent memory leaks
        max_history_size = self.config.get("system", {}).get("max_history_size", 10000)
        from collections import deque

        self.history: Dict[str, Any] = {
            "time": deque(maxlen=max_history_size),
            "ignitions": deque(maxlen=max_history_size),
            "free_energy": deque(maxlen=max_history_size),
            "precision": deque(maxlen=max_history_size),
            "metabolic_reserves": deque(maxlen=max_history_size),
        }

    def _initialize_subsystems(self) -> None:
        """Initialize all subsystems."""
        # Core active inference
        self.active_inference = ActiveInferenceEngine(self.config)
        self.predictor = HierarchicalPredictor(self.config)
        self.precision = PrecisionWeighting(self.config)

        # Interoception
        self.body_model = BodyModel(self.config)
        self.allostasis = AllostaticRegulator(self.config)
        self.somatic_markers = SomaticMarkerSystem(self.config)

        # Ignition and global workspace
        self.ignition_threshold = IgnitionThreshold(self.config)
        self.global_workspace = GlobalWorkspace(self.config)

        # Large-scale networks
        self.networks = LargeScaleNetworkManager(self.config)

        # Self-model
        self.minimal_self = MinimalSelf(self.config)
        self.narrative_self = NarrativeSelf(self.config)
        self.coherence = CoherenceMaintenance(self.config)

        # Thermodynamics
        self.metabolism = MetabolicBudget(self.config)
        self.entropy = EntropyTracker(self.config)

        # Neural oscillations
        self.oscillations = OscillationEngine(self.config)

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor(self.config)

    def step(
        self, extero_input: NDArray[np.floating], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Single timestep of the integrated system.

        Args:
            extero_input: Exteroceptive (sensory) input
            context: Optional contextual information

        Returns:
            Complete system state
        """
        # Start performance monitoring
        self.performance_monitor.start_step()

        dt = self.timestep_ms
        self.time += dt

        # 1. Body model update
        body_info = self.body_model.update(dt)
        intero_vector = self.body_model.get_interoceptive_vector()

        # 2. Allostatic regulation
        allostasis_info = self.allostasis.update(body_info["current"], dt)

        # 3. Predictive processing
        prediction_results = self.predictor.predict(
            extero_input=extero_input.astype(np.float64), intero_input=intero_vector, dt_ms=dt
        )
        errors = self.predictor.get_prediction_errors()

        # 4. Precision weighting
        extero_stats: Any = errors.get("exteroceptive_stats", {})
        intero_stats: Any = errors.get("interoceptive_stats", {})

        extero_variance = (
            extero_stats.get("mean_error", 1.0) ** 2 if isinstance(extero_stats, dict) else 1.0
        )
        intero_variance = (
            intero_stats.get("mean_error", 1.0) ** 2 if isinstance(intero_stats, dict) else 1.0
        )

        precision_info = self.precision.update(
            extero_error_variance=extero_variance,
            intero_error_variance=intero_variance,
            context=context,
        )

        # 5. Generate action policies and execute Active Inference
        # In a full system, available actions would be generated by a motor planner.
        available_actions = [np.random.randn(10) for _ in range(self.active_inference.num_policies)]

        ai_action, ai_info = self.active_inference.step(
            observation=extero_input.astype(np.float64), available_actions=available_actions
        )

        # 6. Somatic marker retrieval limits evaluation to the winning action
        somatic_gain, marker_found = self.somatic_markers.retrieve(
            context=extero_input, action=ai_action
        )

        # 7. Ignition threshold computation
        # Get actual exteroceptive prediction errors from predictor
        predictor_errors = self.predictor.get_prediction_errors()
        extero_error: float | NDArray[np.floating] = predictor_errors.get(
            "exteroceptive", np.zeros(len(extero_input))
        )

        # Ensure extero_error has correct shape and type
        if isinstance(extero_error, (int, float)):
            extero_error = np.array([extero_error], dtype=np.float64)
        elif isinstance(extero_error, np.ndarray) and extero_error.shape != extero_input.shape:
            # Fallback to computed prediction error if predictor output is malformed
            prediction = prediction_results.get("prediction", np.zeros_like(extero_input))
            extero_error = extero_input - prediction

        # Ensure proper shape and dtype for ignition computation
        if isinstance(extero_error, np.ndarray):
            if extero_error.ndim == 1:
                extero_error = extero_error.reshape(1, -1)
            extero_error = extero_error.astype(np.float64)
        else:
            extero_error = np.array([extero_error], dtype=np.float64)

        intero_error = body_info["prediction_error"]

        ignition_occurred, ignition_info = self.ignition_threshold.compute_ignition_signal(
            extero_error=extero_error,  # type: ignore
            extero_precision=precision_info["exteroceptive"],
            intero_error=intero_error,
            intero_precision=precision_info["interoceptive"],
            somatic_marker_gain=somatic_gain,
            current_time=self.time,
        )

        # Update threshold with metabolic state
        metabolic_info = self.metabolism.update(
            ignition_occurred=ignition_occurred,
            task_active=True,
            dt=dt,
            broadcast_content=extero_input,
        )

        self.ignition_threshold.update_metabolic_state(
            reserves=metabolic_info["reserve_fraction"],
            allostatic_load=allostasis_info["allostatic_load"],
        )

        # 8. Global workspace update
        workspace_info = self.global_workspace.update(
            ignition_occurred=ignition_occurred,
            candidate_content=extero_input.astype(np.float64),
            source="sensory",
            dt=dt,
        )

        # 9. Timeline orchestration (disabled - temporal_dynamics module removed)
        timeline_info = {"current_phase": "idle", "time_in_phase": 0.0}

        # Calculate cognitive conflict based on prediction error divergence and EFE
        conflict_signal = float(min(1.0, (extero_variance + intero_variance) / 20.0))

        # 10. Large-scale networks
        network_info = self.networks.update(
            extero_input=extero_input,
            intero_input=intero_vector,
            ignition_signal=ignition_occurred,
            conflict_signal=conflict_signal,
            dt=dt,
        )

        # 11. Self-model
        prediction_accuracy = 1.0 - min(1.0, extero_variance / 10.0)
        minimal_info = self.minimal_self.update(intero_vector, prediction_accuracy, dt)
        narrative_info = self.narrative_self.update({"time": self.time}, dt)
        coherence_info = self.coherence.update(minimal_info, narrative_info)

        # 12. Oscillations
        osc_modulation = {"gamma": 2.0 if ignition_occurred else 1.0}
        osc_info = self.oscillations.generate(modulation=osc_modulation)

        # 13. Entropy tracking
        entropy_info = self.entropy.update(num_spikes=0, ignition=ignition_occurred, dt=dt)

        # 14. Learn from experience (somatic markers)
        if ignition_occurred and np.random.rand() < 0.1:
            outcome = -allostasis_info["allostatic_load"]  # Negative load is good
            self.somatic_markers.learn(extero_input, ai_action, outcome, self.time)

        # Record history
        self._record_history(
            ignition_occurred, ai_info["free_energy"], precision_info, metabolic_info
        )

        # End performance monitoring and record metrics
        perf_metrics = self.performance_monitor.end_step(
            system_time_ms=self.time,
            ignition_occurred=ignition_occurred,
            free_energy=ai_info["free_energy"],
            precision=precision_info["exteroceptive"],
        )

        # Compile complete state
        state = {
            "time": self.time,
            "free_energy": ai_info["free_energy"],
            "ignition": ignition_info,
            "workspace": workspace_info,
            "timeline": timeline_info,
            "body": body_info,
            "allostasis": allostasis_info,
            "precision": precision_info,
            "prediction": prediction_results,
            "networks": network_info,
            "self_model": {
                "minimal": minimal_info,
                "narrative": narrative_info,
                "coherence": coherence_info,
            },
            "metabolism": metabolic_info,
            "entropy": entropy_info,
            "oscillations": osc_info,
            "reportable": workspace_info["is_reportable"],
        }

        # Add performance metrics if available
        if perf_metrics is not None:
            state["performance"] = {
                "step_time_ms": perf_metrics.step_time_ms,
                "memory_usage_mb": perf_metrics.memory_usage_mb,
                "ignition_rate_hz": perf_metrics.ignition_rate_hz,
            }

        return state

    def run(
        self,
        duration_ms: float = 1000.0,
        extero_input_fn: Optional[Callable[[float], NDArray[np.floating]]] = None,
    ) -> Dict[str, Any]:
        """
        Run simulation for specified duration.

        Args:
            duration_ms: Duration in milliseconds (must be positive)
            extero_input_fn: Function that generates exteroceptive input

        Returns:
            Summary of run

        Raises:
            ValueError: If duration_ms is negative or zero
        """
        if duration_ms <= 0:
            raise ValueError(f"duration_ms must be positive, got {duration_ms}")

        self.is_running = True
        num_steps = int(duration_ms / self.timestep_ms)

        # Default input function
        if extero_input_fn is None:

            def default_extero_input(t: float) -> NDArray[np.floating]:
                return np.random.randn(256).astype(np.float64) * 0.5

            extero_input_fn = default_extero_input

        results = []

        for step in range(num_steps):
            extero_input = extero_input_fn(self.time)
            state = self.step(extero_input)
            results.append(state)

        self.is_running = False

        return {
            "total_steps": num_steps,
            "duration_ms": duration_ms,
            "ignition_count": sum([1 for r in results if r["ignition"]["ignition_occurred"]]),
            "final_state": results[-1] if results else {},
            "history": self.history,
        }

    def _record_history(
        self,
        ignition: bool,
        free_energy: float,
        precision: Dict[str, Any],
        metabolism: Dict[str, Any],
    ) -> None:
        """Record metrics for analysis."""
        self.history["time"].append(self.time)
        self.history["ignitions"].append(1 if ignition else 0)
        self.history["free_energy"].append(free_energy)
        self.history["precision"].append(precision["exteroceptive"])
        self.history["metabolic_reserves"].append(metabolism["reserves"])

    def reset(self) -> None:
        """Reset all subsystems."""
        self.active_inference.reset()
        self.predictor.reset()
        self.precision.reset()
        self.body_model.reset()
        self.allostasis.reset()
        self.somatic_markers.reset()
        self.ignition_threshold.reset()
        self.global_workspace.reset()
        self.networks.reset()
        self.minimal_self.reset()
        self.narrative_self.reset()
        self.coherence.reset()
        self.metabolism.reset()
        self.entropy.reset()
        self.oscillations.reset()
        self.performance_monitor.reset()

        self.time = 0.0
        self.history = {k: [] for k in self.history.keys()}

    def get_state(self) -> Dict[str, Any]:
        """
        Get complete system state.

        Returns the full state of all subsystems, providing comprehensive
        information about the current system configuration and dynamics.

        Returns
        -------
        state : Dict[str, Any]
            Complete system state including all subsystem states
        """
        return {
            "time": self.time,
            "timestep_ms": self.timestep_ms,
            "is_running": self.is_running,
            "core": {
                "active_inference": {
                    "time": self.active_inference.time,
                    "beliefs": [
                        {
                            "mean": belief.mean.copy(),
                            "covariance": belief.covariance.copy(),
                            "precision": belief.precision,
                            "prediction": belief.prediction.copy(),
                            "prediction_error": belief.prediction_error.copy(),
                        }
                        for belief in self.active_inference.filter.beliefs
                    ],
                },
                "precision": {
                    "extero_precision": self.precision.extero_precision,
                    "intero_precision": self.precision.intero_precision,
                    "attention_focus": self.precision.attention_focus,
                    "attention_gain": self.precision.attention_gain,
                    "fatigue_level": self.precision.fatigue_level,
                    "cognitive_load": self.precision.cognitive_load,
                },
            },
            "ignition": {
                "threshold_stats": self.ignition_threshold.get_statistics(),
                "workspace_state": (
                    "broadcasting" if self.global_workspace.is_reportable() else "idle"
                ),
                "timeline_state": "idle",  # temporal_dynamics module removed
            },
            "interoception": {
                "body_state": self.body_model.get_current_state(),
                "allostatic_load": self.allostasis.get_allostatic_load(),
                "somatic_markers": self.somatic_markers.get_statistics(),
            },
            "self_model": {
                "minimal_self": self.minimal_self.get_current_state(),
                "narrative_self": self.narrative_self.get_current_state(),
                "coherence": self.coherence.get_coherence_metrics(),
            },
            "thermodynamic": {
                "metabolic_reserves": self.metabolism.current_reserves,
                "entropy_stats": self.entropy.get_statistics(),
            },
            "neural": {
                "networks": self.networks.get_network_states(),
                "oscillations": self.oscillations.get_current_state(),
            },
            "history": self.history,
            "performance": self.performance_monitor.get_statistics(),
        }

    def get_state_summary(self) -> Dict[str, Any]:
        """Get high-level summary of current state."""
        return {
            "time_ms": self.time,
            "ignition_stats": self.ignition_threshold.get_statistics(),
            "workspace_state": "broadcasting" if self.global_workspace.is_reportable() else "idle",
            "allostatic_load": self.allostasis.get_allostatic_load(),
            "metabolic_reserves": self.metabolism.current_reserves,
            "somatic_markers": self.somatic_markers.get_statistics(),
        }

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance monitoring statistics.

        Returns
        -------
        stats : Dict[str, Any]
            Performance statistics including step time, memory usage, and ignition rate
        """
        return self.performance_monitor.get_statistics()

    def log_performance(self, verbose: bool = False) -> None:
        """Log current performance statistics.

        Parameters
        ----------
        verbose : bool, optional
            Whether to print detailed statistics, by default False
        """
        self.performance_monitor.log_performance(verbose=verbose)
