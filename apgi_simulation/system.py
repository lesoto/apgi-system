"""
Main APGI System Integrator

Integrates all subsystems into a cohesive consciousness model.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import numpy as np
import yaml
from numpy.typing import NDArray

from apgi_simulation.config_validator import ConfigValidationError, ConfigValidator
from apgi_simulation.core import ActiveInferenceEngine, HierarchicalPredictor, PrecisionWeighting
from apgi_simulation.core.interfaces import SubsystemProtocol
from apgi_simulation.core.vp15 import VP15ValidationProtocol
from apgi_simulation.ignition import GlobalWorkspace, IgnitionThreshold
from apgi_simulation.interoception import AllostaticRegulator, BodyModel, SomaticMarkerSystem
from apgi_simulation.monitoring import PerformanceMonitor
from apgi_simulation.neural.macroscale.large_scale_networks import LargeScaleNetworkManager
from apgi_simulation.neural.oscillations import OscillationEngine
from apgi_simulation.platform_utils import get_resource_path
from apgi_simulation.self_model import CoherenceMaintenance, MinimalSelf, NarrativeSelf
from apgi_simulation.thermodynamic import EntropyTracker, MetabolicBudget


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

        seed = self.config.get("system", {}).get("random_seed", None)
        self._rng = np.random.default_rng(seed)

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
        self.ignition_threshold = IgnitionThreshold(self.config, rng=self._rng)
        self.global_workspace = GlobalWorkspace(self.config, rng=self._rng)

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

        self._subsystem_protocol_adapters = self._build_subsystem_protocol_adapters()
        for name, subsystem in self._subsystem_protocol_adapters.items():
            assert isinstance(
                subsystem, SubsystemProtocol
            ), f"Subsystem '{name}' does not satisfy SubsystemProtocol at runtime."

        # Initialize VP-15 validation protocol
        self.vp15 = VP15ValidationProtocol(self.config)

    def _build_subsystem_protocol_adapters(self) -> Dict[str, SubsystemProtocol]:
        """Wrap heterogeneous subsystem APIs behind the SubsystemProtocol contract."""

        class _SubsystemAdapter:
            def __init__(self, subsystem: Any):
                self._subsystem = subsystem

            def step(self, dt: float, inputs: Dict[str, Any]) -> Dict[str, Any]:
                if hasattr(self._subsystem, "step"):
                    output = self._subsystem.step(**inputs)
                elif hasattr(self._subsystem, "update"):
                    output = self._subsystem.update(**inputs)
                elif hasattr(self._subsystem, "predict"):
                    output = self._subsystem.predict(**inputs)
                elif hasattr(self._subsystem, "generate"):
                    output = self._subsystem.generate(**inputs)
                else:
                    raise AttributeError(
                        f"{type(self._subsystem).__name__} has no step/update/predict/generate method"
                    )
                return output if isinstance(output, dict) else {"result": output, "dt_ms": dt}

            def reset(self) -> None:
                self._subsystem.reset()

            def get_state(self) -> Dict[str, Any]:
                if hasattr(self._subsystem, "get_state"):
                    state = self._subsystem.get_state()
                    return state if isinstance(state, dict) else {"state": state}
                return {"type": type(self._subsystem).__name__}

        return {
            "active_inference": _SubsystemAdapter(self.active_inference),
            "predictor": _SubsystemAdapter(self.predictor),
            "precision": _SubsystemAdapter(self.precision),
            "body_model": _SubsystemAdapter(self.body_model),
            "allostasis": _SubsystemAdapter(self.allostasis),
            "somatic_markers": _SubsystemAdapter(self.somatic_markers),
            "ignition_threshold": _SubsystemAdapter(self.ignition_threshold),
            "global_workspace": _SubsystemAdapter(self.global_workspace),
            "networks": _SubsystemAdapter(self.networks),
            "minimal_self": _SubsystemAdapter(self.minimal_self),
            "narrative_self": _SubsystemAdapter(self.narrative_self),
            "coherence": _SubsystemAdapter(self.coherence),
            "metabolism": _SubsystemAdapter(self.metabolism),
            "entropy": _SubsystemAdapter(self.entropy),
            "oscillations": _SubsystemAdapter(self.oscillations),
            "performance_monitor": _SubsystemAdapter(self.performance_monitor),
        }

    def step(
        self,
        extero_input: Union[NDArray[np.float64], Dict[str, NDArray[np.float64]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Single timestep of the integrated system.

        Args:
            extero_input: Exteroceptive (sensory) input - can be a vector or a multi-modal dict
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
        # Convert body state dict back to array format for allostasis compatibility
        # Handle both scalar (batch_size=1) and array (batch_size>1) cases
        body_state_values = [
            body_info["current"]["heart_rate"],
            body_info["current"]["respiration"],
            body_info["current"]["temperature"],
            body_info["current"]["glucose"],
            body_info["current"]["cortisol"],
            body_info["current"]["blood_pressure"],
        ]
        # Convert to 2D array (1, 6) for batch_size=1 compatibility
        body_state_array = np.array(body_state_values).reshape(1, -1)
        allostasis_info = self.allostasis.update(body_state_array, dt)

        # 3. Multi-modal fusion and Predictive processing
        # Use simple fusion if vector provided, otherwise let active_inference handle dict
        if isinstance(extero_input, dict):
            # For the hierarchical predictor, we concatenate for now
            # In a better version, hierarchical predictor would also be multi-modal
            predictor_input = self.active_inference.input_layer.fuse(extero_input)
            predictor_input = extero_input.get(
                "vision", predictor_input
            )  # Use vision as primary for some metrics
        else:
            predictor_input = extero_input.astype(np.float64)

        prediction_results = self.predictor.predict(
            extero_input=predictor_input, intero_input=intero_vector, dt_ms=dt
        )
        errors = self.predictor.get_prediction_errors()

        # 4. Precision weighting
        extero_stats: Any = errors.get("exteroceptive_stats", {})
        intero_stats: Any = errors.get("interoceptive_stats", {})

        # Extract scalar variance from stats (handle both scalar and array returns)
        extero_mean_error = (
            extero_stats.get("mean_error", 1.0) if isinstance(extero_stats, dict) else 1.0
        )
        intero_mean_error = (
            intero_stats.get("mean_error", 1.0) if isinstance(intero_stats, dict) else 1.0
        )

        # Convert to scalar if array
        if isinstance(extero_mean_error, np.ndarray):
            extero_mean_error = float(np.mean(extero_mean_error))
        if isinstance(intero_mean_error, np.ndarray):
            intero_mean_error = float(np.mean(intero_mean_error))

        extero_variance = extero_mean_error**2
        intero_variance = intero_mean_error**2

        precision_info = self.precision.update(
            extero_error_variance=extero_variance,
            intero_error_variance=intero_variance,
            context=context,
        )

        # 5. Generate action policies and execute Active Inference
        # available_actions can be passed here or generated internally by motor_planner
        ai_action, ai_info = self.active_inference.step(
            observation=extero_input, available_actions=None
        )

        # 6. Somatic marker retrieval limits evaluation to the winning action
        somatic_gain, marker_found = self.somatic_markers.retrieve(
            context=predictor_input, action=ai_action
        )

        # Sigmoid-modulated effective interoceptive precision (APGI Eq. 2.2)
        M_0 = 0.0  # neutral baseline
        beta = self.config.get("precision", {}).get("intero_somatic_beta", 1.0)
        Pi_i_baseline = precision_info["interoceptive"]
        sigmoid_M = 1.0 / (1.0 + np.exp(-(somatic_gain - M_0)))
        effective_intero_precision = Pi_i_baseline * (1.0 + beta * sigmoid_M)

        # 7. Ignition threshold computation
        # Get actual exteroceptive prediction errors from predictor
        predictor_errors = self.predictor.get_prediction_errors()
        extero_error: float | NDArray[np.floating] = predictor_errors.get(
            "exteroceptive", np.zeros(len(extero_input))
        )

        # Ensure extero_error has correct shape and type
        if isinstance(extero_error, (int, float)):
            extero_error = np.array([extero_error], dtype=np.float64)
        elif isinstance(extero_error, np.ndarray) and extero_error.shape != predictor_input.shape:
            # Fallback to computed prediction error if predictor output is malformed
            prediction = prediction_results.get("prediction", np.zeros_like(predictor_input))
            extero_error = predictor_input - prediction

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
            intero_precision=effective_intero_precision,
            somatic_marker_gain=somatic_gain,
            current_time=self.time,
        )

        # Convert array to scalar for boolean checks
        ignition_scalar = bool(np.any(ignition_occurred))

        # Add ignition_occurred to ignition_info (keep as numpy array for internal use)
        ignition_info["ignition_occurred"] = ignition_occurred

        # Update threshold with metabolic state
        metabolic_info = self.metabolism.update(
            ignition_occurred=ignition_scalar,
            task_active=True,
            dt=dt,
            broadcast_content=predictor_input,
        )

        self.ignition_threshold.update_metabolic_state(
            reserves=metabolic_info["reserve_fraction"],
            allostatic_load=allostasis_info["allostatic_load"],
        )

        # 8. Global workspace update
        ignition_mask = ignition_occurred
        if ignition_scalar:
            # Reshape predictor_input to match workspace content dimensions
            workspace_dim = self.global_workspace.content_dim
            if predictor_input.shape[0] > workspace_dim:
                # Truncate or project to workspace dimension
                candidate = predictor_input[:workspace_dim]
            elif predictor_input.shape[0] < workspace_dim:
                # Pad with zeros
                candidate = np.zeros(workspace_dim)
                candidate[: predictor_input.shape[0]] = predictor_input
            else:
                candidate = predictor_input
            candidates = np.array([candidate])
        else:
            candidates = None
        workspace_info = self.global_workspace.update(
            ignition_mask=ignition_mask,
            candidates=candidates,
            dt=dt,
        )

        # 9. Temporal orchestration — surfaced from ActiveInferenceEngine.temporal_dynamics
        # (driven by the seeded TemporalDynamics instance inside the engine)
        timeline_info = ai_info.get(
            "temporal",
            {"phases": {}, "amplitudes": {}, "pac_factor": 1.0, "synchrony": 0.0},
        )

        # Calculate cognitive conflict based on prediction error divergence and EFE
        conflict_divisor = self.config.get("system", {}).get("conflict_divisor", 20.0)
        conflict_signal = float(min(1.0, (extero_variance + intero_variance) / conflict_divisor))

        # 10. Large-scale networks
        batch_size = self.config.get("active_inference", {}).get("batch_size", 1)
        network_info = self.networks.update(
            extero_input=predictor_input,
            intero_input=intero_vector,
            ignition_signal=np.full(batch_size, 1.0 if ignition_scalar else 0.0),
            conflict_signal=np.full(batch_size, conflict_signal),
            dt=dt,
        )

        # 11. Self-model
        accuracy_divisor = self.config.get("system", {}).get("accuracy_divisor", 10.0)
        prediction_accuracy = 1.0 - min(1.0, extero_variance / accuracy_divisor)
        minimal_info = self.minimal_self.update(intero_vector, prediction_accuracy, dt)
        narrative_info = self.narrative_self.update({"time": self.time}, dt)
        coherence_info = self.coherence.update(minimal_info, narrative_info)

        # 12. Oscillations
        osc_modulation = {"gamma": 2.0 if ignition_scalar else 1.0}
        osc_info = self.oscillations.generate(modulation=osc_modulation)

        # 13. Entropy tracking
        entropy_info = self.entropy.update(num_spikes=0, ignition=ignition_scalar, dt=dt)

        # 14. Learn from experience (somatic markers)
        learning_prob = self.config.get("somatic_markers", {}).get("learning_prob", 0.1)
        if ignition_scalar and float(self._rng.random()) < learning_prob:
            outcome = -allostasis_info["allostatic_load"]  # Negative load is good
            self.somatic_markers.learn(predictor_input, ai_action, outcome, self.time)

        # Record history
        self._record_history(
            ignition_scalar, ai_info["free_energy"], precision_info, metabolic_info
        )

        # End performance monitoring and record metrics
        # Extract scalar precision for performance monitor
        precision_scalar = precision_info.get("exteroceptive", 1.0)
        if isinstance(precision_scalar, np.ndarray):
            precision_scalar = float(np.mean(precision_scalar))
        perf_metrics = self.performance_monitor.end_step(
            system_time_ms=self.time,
            ignition_occurred=ignition_scalar,
            free_energy=ai_info["free_energy"],
            precision=precision_scalar,
        )

        # Convert precision to scalars if batch_size is 1 for test compatibility
        precision_info_scalar = {
            k: float(v[0]) if isinstance(v, np.ndarray) and v.ndim > 0 else float(v)
            for k, v in precision_info.items()
        }

        # Compile complete state
        state = {
            "time": self.time,
            "free_energy": ai_info["free_energy"],
            "ignition": ignition_info,
            "workspace": workspace_info,
            "timeline": timeline_info,
            "body": body_info,
            "allostasis": allostasis_info,
            "precision": precision_info_scalar,
            "prediction": prediction_results,
            "networks": network_info,
            "active_inference": ai_info,
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

        # 15. VP-15 Validation
        is_valid, vp15_metrics = self.vp15.validate_step(state)
        state["vp15"] = {
            "is_valid": is_valid,
            "metrics": vp15_metrics.__dict__,
            "report": self.vp15.get_violation_report() if not is_valid else "",
        }

        # Add performance metrics if available
        if perf_metrics is not None:
            state["performance"] = {
                "step_time_ms": perf_metrics.step_time_ms,
                "memory_usage_mb": perf_metrics.memory_usage_mb,
                "ignition_rate_hz": perf_metrics.ignition_rate_hz,
            }

        return state

    async def step_async(
        self,
        extero_input: Union[NDArray[np.float64], Dict[str, NDArray[np.float64]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronous version of system step utilizing concurrent subsystem updates.
        """
        import asyncio

        # Start performance monitoring
        self.performance_monitor.start_step()

        dt = self.timestep_ms
        self.time += dt

        # 1 & 12 Parallel: Body model and Neural Oscillations
        results = await asyncio.gather(
            asyncio.to_thread(self.body_model.update, dt),
            asyncio.to_thread(self.oscillations.generate),
        )
        body_info, osc_info = results

        # 2. Allostatic regulation
        # Convert body state dict back to array format for allostasis compatibility
        # Handle both scalar (batch_size=1) and array (batch_size>1) cases
        body_state_values = [
            body_info["current"]["heart_rate"],
            body_info["current"]["respiration"],
            body_info["current"]["temperature"],
            body_info["current"]["glucose"],
            body_info["current"]["cortisol"],
            body_info["current"]["blood_pressure"],
        ]
        # Convert to 2D array (1, 6) for batch_size=1 compatibility
        body_state_array = np.array(body_state_values).reshape(1, -1)
        allostasis_info = self.allostasis.update(body_state_array, dt)

        # 3, 4, 5. Core Sequential (Inference & Action)
        # We run these in a single thread to avoid overhead, but could thread specific matrix ops
        state_sync = await asyncio.to_thread(
            self._step_core_sequential, extero_input, body_info, allostasis_info, dt, context
        )

        # 8, 10, 11, 13 Parallel: Post-ignition updates
        ignition_mask = np.full(
            self.global_workspace.batch_size, state_sync["ignition_occurred"], dtype=bool
        )
        if state_sync["ignition_occurred"]:
            # Reshape predictor_input to match workspace content dimensions
            workspace_dim = self.global_workspace.content_dim
            predictor_input_sync = state_sync["predictor_input"]
            if predictor_input_sync.shape[0] > workspace_dim:
                candidate = predictor_input_sync[:workspace_dim]
            elif predictor_input_sync.shape[0] < workspace_dim:
                candidate = np.zeros(workspace_dim)
                candidate[: predictor_input_sync.shape[0]] = predictor_input_sync
            else:
                candidate = predictor_input_sync
            candidates = np.array([candidate])
        else:
            candidates = None
        batch_size = self.config.get("active_inference", {}).get("batch_size", 1)
        post_results = await asyncio.gather(
            asyncio.to_thread(self.global_workspace.update, ignition_mask, candidates, None, dt),
            asyncio.to_thread(
                self.networks.update,
                state_sync["predictor_input"],
                self.body_model.get_interoceptive_vector(),
                np.full(batch_size, float(state_sync["ignition_occurred"])),
                np.full(batch_size, state_sync["conflict_signal"]),
                dt,
            ),
            asyncio.to_thread(
                self.metabolism.update,
                state_sync["ignition_occurred"],
                True,
                dt,
                state_sync["predictor_input"],
            ),
            asyncio.to_thread(self.entropy.update, 0, state_sync["ignition_occurred"], dt),
        )
        workspace_info, network_info, metabolic_info, entropy_info = post_results

        # Self-model needs sequential minimal -> coherence
        minimal_info = self.minimal_self.update(
            self.body_model.get_interoceptive_vector(), state_sync["prediction_accuracy"], dt
        )
        narrative_info = self.narrative_self.update({"time": self.time}, dt)
        self.coherence.update(minimal_info, narrative_info)

        # Record history
        self._record_history(
            state_sync["ignition_occurred"],
            state_sync["ai_info"]["free_energy"],
            state_sync["precision_info"],
            metabolic_info,
        )

        perf_metrics = self.performance_monitor.end_step(
            system_time_ms=self.time,
            ignition_occurred=state_sync["ignition_occurred"],
            free_energy=state_sync["ai_info"]["free_energy"],
            precision=state_sync["precision_info"]["exteroceptive"],
        )

        state = {
            "time": self.time,
            "free_energy": state_sync["ai_info"]["free_energy"],
            "ignition": state_sync["ignition_info"],
            "workspace": workspace_info,
            "timeline": state_sync["ai_info"].get("temporal", {}),
            "body": body_info,
            "allostasis": allostasis_info,
            "precision": state_sync["precision_info"],
            "prediction": state_sync["prediction_results"],
            "networks": network_info,
            "active_inference": state_sync["ai_info"],
            "self_model": {
                "minimal": minimal_info,
                "narrative": narrative_info,
                "coherence": self.coherence.get_coherence_metrics(),
            },
            "metabolism": metabolic_info,
            "entropy": entropy_info,
            "oscillations": osc_info,
            "reportable": workspace_info["is_reportable"],
        }

        # VP-15 Validation
        is_valid, vp15_metrics = self.vp15.validate_step(state)
        state["vp15"] = {"is_valid": is_valid, "metrics": vp15_metrics.__dict__}

        if perf_metrics is not None:
            state["performance"] = {"step_time_ms": perf_metrics.step_time_ms}

        return state

    def _step_core_sequential(
        self,
        extero_input: Any,
        body_info: Dict[str, Any],
        allostasis_info: Dict[str, Any],
        dt: float,
        context: Any,
    ) -> Dict[str, Any]:
        """Hidden helper for sequential core of the step."""
        intero_vector = self.body_model.get_interoceptive_vector()
        if isinstance(extero_input, dict):
            predictor_input = self.active_inference.input_layer.fuse(extero_input)
            predictor_input = extero_input.get("vision", predictor_input)
        else:
            predictor_input = extero_input.astype(np.float64)

        prediction_results = self.predictor.predict(
            extero_input=predictor_input, intero_input=intero_vector, dt_ms=dt
        )
        errors = self.predictor.get_prediction_errors()
        extero_stats = errors.get("exteroceptive_stats", {})
        intero_stats = errors.get("interoceptive_stats", {})

        # Extract scalar variance from stats (handle both scalar and array returns)
        extero_mean_error = (
            extero_stats.get("mean_error", 1.0) if isinstance(extero_stats, dict) else 1.0
        )
        intero_mean_error = (
            intero_stats.get("mean_error", 1.0) if isinstance(intero_stats, dict) else 1.0
        )

        # Convert to scalar if array
        if isinstance(extero_mean_error, np.ndarray):
            extero_mean_error = float(np.mean(extero_mean_error))
        if isinstance(intero_mean_error, np.ndarray):
            intero_mean_error = float(np.mean(intero_mean_error))

        extero_variance = extero_mean_error**2
        intero_variance = intero_mean_error**2

        # Convert scalar variances to arrays for precision.update type compatibility
        extero_variance_array = np.full(self.precision.batch_size, extero_variance)
        intero_variance_array = np.full(self.precision.batch_size, intero_variance)

        precision_info = self.precision.update(
            extero_error_variance=extero_variance_array,
            intero_error_variance=intero_variance_array,
            context=context,
        )

        ai_action, ai_info = self.active_inference.step(
            observation=extero_input, available_actions=None
        )

        somatic_gain, _ = self.somatic_markers.retrieve(context=predictor_input, action=ai_action)
        beta = self.config.get("precision", {}).get("intero_somatic_beta", 1.0)
        sigmoid_M = 1.0 / (1.0 + np.exp(-(somatic_gain)))
        effective_intero_precision = precision_info["interoceptive"] * (1.0 + beta * sigmoid_M)

        extero_error = errors.get("exteroceptive", np.zeros(len(extero_input)))
        ignition_occurred, ignition_info = self.ignition_threshold.compute_ignition_signal(
            extero_error=extero_error,
            extero_precision=precision_info["exteroceptive"],
            intero_error=body_info["prediction_error"],
            intero_precision=effective_intero_precision,
            somatic_marker_gain=somatic_gain,
            current_time=self.time,
        )

        conflict_divisor = self.config.get("system", {}).get("conflict_divisor", 20.0)
        conflict_signal = float(min(1.0, (extero_variance + intero_variance) / conflict_divisor))

        accuracy_divisor = self.config.get("system", {}).get("accuracy_divisor", 10.0)
        prediction_accuracy = 1.0 - min(1.0, extero_variance / accuracy_divisor)

        return {
            "predictor_input": predictor_input,
            "prediction_results": prediction_results,
            "precision_info": precision_info,
            "ai_info": ai_info,
            "ignition_occurred": ignition_occurred,
            "ignition_info": ignition_info,
            "conflict_signal": conflict_signal,
            "prediction_accuracy": prediction_accuracy,
        }

    def run(
        self,
        duration_ms: float = 1000.0,
        extero_input_fn: Optional[Callable[[float], NDArray[np.float64]]] = None,
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

            def default_extero_input(t: float) -> NDArray[np.float64]:
                return self._rng.normal(size=256).astype(np.float64) * 0.5

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
            "ignition_occurred": results[-1]["ignition"]["ignition_occurred"] if results else False,
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
        # Rebuild history deques preserving each deque's original maxlen so that
        # the memory-safety guarantee established in __init__ is not lost.
        self.history = {k: type(v)(maxlen=v.maxlen) for k, v in self.history.items()}

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
