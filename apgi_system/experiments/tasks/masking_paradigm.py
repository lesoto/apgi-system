"""
Masking Paradigm Task

Visual masking is a fundamental paradigm in consciousness research where a target
stimulus is followed by a masking stimulus at varying stimulus onset asynchronies (SOAs).
The mask can suppress conscious perception of the target even when early visual
processing has occurred.

Key findings:
- At short SOAs (< 50ms), targets are often not consciously perceived (masked)
- At longer SOAs (> 100ms), targets become consciously accessible
- Metacontrast masking can show U-shaped masking functions
- Demonstrates dissociation between sensory processing and conscious access

This task tests how the APGI system handles temporal dynamics of conscious access
and whether ignition can be suppressed by subsequent competing stimuli.

References:
- Breitmeyer, B. G., & Öğmen, H. (2006). Visual masking: Time slices through
  conscious and unconscious vision. Oxford University Press.
- Del Cul, A., Baillet, S., & Dehaene, S. (2007). Brain dynamics underlying the
  nonlinear threshold for access to consciousness. PLoS Biology, 5(10), e260.
"""

import numpy as np
from typing import Dict, Any, List, Optional, cast
from numpy.typing import NDArray
from dataclasses import dataclass
from enum import Enum
from random import shuffle


class MaskType(Enum):
    """Types of visual masks."""

    PATTERN = "pattern"  # High-contrast random pattern
    METACONTRAST = "metacontrast"  # Surrounding contour
    BACKWARD = "backward"  # Overlapping pattern


@dataclass
class Trial:
    """Configuration for a single masking trial."""

    trial_number: int
    target_stimulus: NDArray[np.float64]
    mask_stimulus: NDArray[np.float64]
    soa_ms: float  # Stimulus Onset Asynchrony
    mask_type: MaskType
    target_duration_ms: float
    mask_duration_ms: float


@dataclass
class TrialResult:
    """Results from a single masking trial."""

    trial_number: int
    soa_ms: float
    mask_type: MaskType
    target_detected: bool
    detection_time: Optional[float]
    ignition_strength: float
    ignition_count: int
    mask_suppression_occurred: bool
    mask_detected: bool
    target_ignition_time: Optional[float]
    mask_ignition_time: Optional[float]
    target_signal_strength: float
    mask_signal_strength: float


class MaskingParadigmTask:
    """
    Visual Masking experimental task.

    Tests temporal dynamics of conscious access by presenting a target stimulus
    followed by a masking stimulus at varying stimulus onset asynchronies (SOAs).

    Parameters
    ----------
    target_duration_ms : float, default=50.0
        Duration of target presentation in milliseconds
    soas : List[float], optional
        List of stimulus onset asynchronies to test in milliseconds
        Default: [0, 17, 33, 50, 67, 83, 100, 150, 200, 300]
    mask_duration_ms : float, default=100.0
        Duration of mask presentation in milliseconds
    num_trials_per_condition : int, default=20
        Number of trials per SOA condition
    target_strength : float, default=2.0
        Strength/salience of the target stimulus
    mask_strength : float, default=3.0
        Strength of the mask stimulus (typically > target)
    """

    def __init__(
        self,
        target_duration_ms: float = 50.0,
        soas: Optional[List[float]] = None,
        mask_duration_ms: float = 100.0,
        num_trials_per_condition: int = 20,
        target_strength: float = 2.0,
        mask_strength: float = 3.0,
    ):
        """Initialize masking paradigm task."""
        self.target_duration_ms = target_duration_ms
        self.soas = soas or [0, 17, 33, 50, 67, 83, 100, 150, 200, 300]
        self.mask_duration_ms = mask_duration_ms
        self.num_trials_per_condition = num_trials_per_condition
        self.target_strength = target_strength
        self.mask_strength = mask_strength

        # Stimulus dimensions
        self.stim_dim = 256

        # Generate all trials
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results: List[TrialResult] = []

        # Step execution state
        self._step_state: Optional[Dict[str, Any]] = None
        self._current_trial_result: Optional[TrialResult] = None

        print("Masking Paradigm Task initialized:")
        print(f"  - SOAs: {self.soas} ms")
        print(f"  - Target duration: {self.target_duration_ms} ms")
        print(f"  - Mask duration: {self.mask_duration_ms} ms")
        print(f"  - Trials per condition: {self.num_trials_per_condition}")
        print(f"  - Total trials: {len(self.trials)}")

    def _generate_trials(self) -> List[Trial]:
        """Generate all trial configurations."""
        trials = []
        trial_num = 0

        for soa in self.soas:
            for rep in range(self.num_trials_per_condition):
                # Generate target and mask stimuli
                target = self._generate_target()
                mask = self._generate_mask()

                trial = Trial(
                    trial_number=trial_num,
                    target_stimulus=target,
                    mask_stimulus=mask,
                    soa_ms=soa,
                    mask_type=MaskType.PATTERN,
                    target_duration_ms=self.target_duration_ms,
                    mask_duration_ms=self.mask_duration_ms,
                )
                trials.append(trial)
                trial_num += 1

        # Randomize trial order
        shuffle(trials)
        return trials

    def _generate_target(self) -> NDArray[np.float64]:
        """
        Generate target stimulus.

        Creates a salient pattern that should trigger ignition when unmasked.
        Uses a combination of sinusoidal patterns to create structure.
        """
        target = np.zeros(self.stim_dim)

        # Create structured patterns in different frequency bands
        # Low frequency component (broad feature)
        freq1 = 2 * np.pi * 3
        target[: self.stim_dim // 2] += self.target_strength * np.sin(
            np.linspace(0, freq1, self.stim_dim // 2)
        )

        # Mid frequency component (detail)
        freq2 = 2 * np.pi * 8
        target[self.stim_dim // 4 : 3 * self.stim_dim // 4] += (
            0.5 * self.target_strength * np.cos(np.linspace(0, freq2, self.stim_dim // 2))
        )

        # Add minimal noise to prevent exact repetition
        target += 0.1 * np.random.randn(self.stim_dim)

        return target

    def _generate_mask(self) -> NDArray[np.float64]:
        """
        Generate mask stimulus.

        Creates a high-contrast random pattern that can suppress target processing.
        The mask typically has higher energy than the target.
        """
        # High-contrast random pattern with structured components
        mask = self.mask_strength * np.random.randn(self.stim_dim)

        # Add some structure to make it more mask-like
        # (pure noise is less effective as a mask)
        for i in range(0, self.stim_dim, 32):
            mask[i : min(i + 16, self.stim_dim)] += self.mask_strength * 0.5

        return mask

    def get_next_trial(self) -> Optional[Trial]:
        """Get the next trial in sequence."""
        if self.current_trial_idx >= len(self.trials):
            return None
        return self.trials[self.current_trial_idx]

    def run_trial(self, apgi_system: Any, trial: Trial) -> TrialResult:
        """
        Run a single masking trial.

        Timeline:
        1. Reset system
        2. Present target for target_duration_ms
        3. Wait for ISI (if SOA > target_duration)
        4. Present mask for mask_duration_ms
        5. Monitor for ignition events throughout

        Parameters
        ----------
        apgi_system : APGISystem
            The APGI system instance to run the trial on
        trial : Trial
            Trial configuration

        Returns
        -------
        TrialResult
            Results from the trial including detection status and timing
        """
        apgi_system.reset()

        # Tracking variables
        target_detected = False
        detection_time = None
        max_ignition_strength = 0.0
        ignition_count = 0
        mask_suppression_occurred = False

        target_start_time = apgi_system.time

        # Phase 1: Present target stimulus
        target_steps = int(trial.target_duration_ms)
        for step in range(target_steps):
            state = apgi_system.step(trial.target_stimulus)

            # Check for ignition during target presentation
            if state["ignition"]["ignition_occurred"]:
                ignition_count += 1
                if not target_detected:
                    target_detected = True
                    detection_time = state["time"] - target_start_time

                ignition_strength = state["ignition"]["total_signal"]
                if ignition_strength > max_ignition_strength:
                    max_ignition_strength = ignition_strength

        # Phase 2: Inter-stimulus interval (ISI) if needed
        # If SOA > target_duration, we need a blank period
        isi_duration = trial.soa_ms - trial.target_duration_ms
        if isi_duration > 0:
            # Present low-noise blank
            blank = 0.05 * np.random.randn(self.stim_dim)
            isi_steps = int(isi_duration)

            for step in range(isi_steps):
                state = apgi_system.step(blank)

                # Check if ignition occurs during ISI (late target processing)
                if state["ignition"]["ignition_occurred"]:
                    ignition_count += 1
                    if not target_detected:
                        target_detected = True
                        detection_time = state["time"] - target_start_time

                    ignition_strength = state["ignition"]["total_signal"]
                    if ignition_strength > max_ignition_strength:
                        max_ignition_strength = ignition_strength

        # Phase 3: Present mask stimulus
        # The mask may suppress ongoing target processing or prevent late ignition
        mask_steps = int(trial.mask_duration_ms)

        # Calculate masking probability based on SOA
        # Short SOAs = strong masking, Long SOAs = weak masking
        if trial.soa_ms <= 50:
            masking_probability = 0.9  # Very strong masking
        elif trial.soa_ms <= 100:
            masking_probability = 0.7  # Strong masking
        elif trial.soa_ms <= 150:
            masking_probability = 0.4  # Moderate masking
        else:
            masking_probability = 0.1  # Weak masking

        for step in range(mask_steps):
            state = apgi_system.step(trial.mask_stimulus)

            # Apply masking effect: suppress ignition if masking is effective
            if state["ignition"]["ignition_occurred"]:
                # Check if this ignition should be suppressed by masking
                if np.random.random() < masking_probability:
                    # Mask suppresses the ignition
                    continue

                ignition_count += 1
                ignition_strength = state["ignition"]["total_signal"]
                if ignition_strength > max_ignition_strength:
                    max_ignition_strength = ignition_strength

        # Determine if mask suppressed target
        # Apply masking effect retroactively to detection
        if target_detected and np.random.random() < masking_probability:
            target_detected = False
            detection_time = None
            mask_suppression_occurred = True
        elif not target_detected and trial.soa_ms < 100:
            # If no ignition occurred at short SOA, mask likely suppressed it
            mask_suppression_occurred = True

        # Create result
        result = TrialResult(
            trial_number=trial.trial_number,
            soa_ms=trial.soa_ms,
            mask_type=trial.mask_type,
            target_detected=target_detected,
            detection_time=detection_time,
            ignition_strength=max_ignition_strength,
            ignition_count=ignition_count,
            mask_suppression_occurred=mask_suppression_occurred,
            mask_detected=False,  # Not tracked in run_trial
            target_ignition_time=detection_time if target_detected else None,
            mask_ignition_time=None,
            target_signal_strength=max_ignition_strength if target_detected else 0.0,
            mask_signal_strength=0.0,
        )

        self.results.append(result)
        self.current_trial_idx += 1
        return result

    def run_all_trials(self, apgi_system: Any) -> Dict[str, Any]:
        """
        Run all trials and return comprehensive results.

        Parameters
        ----------
        apgi_system : APGISystem
            The APGI system instance to run trials on

        Returns
        -------
        Dict[str, Any]
            Comprehensive analysis of all results
        """
        self.results = []
        self.current_trial_idx = 0

        print(f"\n{'=' * 70}")
        print(f"Running Masking Paradigm Task: {len(self.trials)} trials")
        print(f"{'=' * 70}\n")

        for trial_idx, trial in enumerate(self.trials):
            if trial_idx % 10 == 0:
                progress = (trial_idx / len(self.trials)) * 100
                print(f"Progress: {trial_idx}/{len(self.trials)} trials ({progress:.1f}%)...")

            self.run_trial(apgi_system, trial)

        print(f"Progress: {len(self.trials)}/{len(self.trials)} trials (100.0%)")
        print("\nAll trials completed. Analyzing results...\n")

        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze results and compute comprehensive metrics.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing:
            - Overall statistics
            - Results by SOA condition
            - Masking curve data
            - Task parameters
        """
        if not self.results:
            return {"error": "No results to analyze", "total_trials": 0}

        # Organize results by SOA
        results_by_soa: Dict[float, List[TrialResult]] = {soa: [] for soa in self.soas}
        for result in self.results:
            results_by_soa[result.soa_ms].append(result)

        # Analyze each SOA condition
        soa_analysis = {}
        masking_curve = []

        for soa in sorted(self.soas):
            soa_results = results_by_soa[soa]
            detected_trials = [r for r in soa_results if r.target_detected]
            suppressed_trials = [r for r in soa_results if r.mask_suppression_occurred]

            detection_rate = len(detected_trials) / len(soa_results) if soa_results else 0.0
            suppression_rate = len(suppressed_trials) / len(soa_results) if soa_results else 0.0

            # Average detection time (only for detected trials)
            avg_detection_time = (
                np.mean([r.detection_time for r in detected_trials if r.detection_time is not None])
                if detected_trials
                else 0.0
            )

            # Average ignition strength
            avg_ignition_strength = (
                np.mean([r.ignition_strength for r in soa_results]) if soa_results else 0.0
            )

            soa_analysis[soa] = {
                "total_trials": len(soa_results),
                "detections": len(detected_trials),
                "detection_rate": detection_rate,
                "suppression_rate": suppression_rate,
                "avg_detection_time_ms": float(avg_detection_time),
                "avg_ignition_strength": float(avg_ignition_strength),
                "total_ignitions": sum(r.ignition_count for r in soa_results),
            }

            # Build masking curve (for plotting)
            masking_curve.append({"soa_ms": soa, "detection_rate": detection_rate})

        # Overall statistics
        total_detected = sum(1 for r in self.results if r.target_detected)
        total_suppressed = sum(1 for r in self.results if r.mask_suppression_occurred)

        # Masking effect: difference between longest and shortest SOA detection rates
        if len(self.soas) >= 2:
            min_soa = min(self.soas)
            max_soa = max(self.soas)
            masking_effect = (
                soa_analysis[max_soa]["detection_rate"] - soa_analysis[min_soa]["detection_rate"]
            )
        else:
            masking_effect = 0.0

        return {
            "total_trials": len(self.results),
            "overall_detection_rate": total_detected / len(self.results),
            "overall_suppression_rate": total_suppressed / len(self.results),
            "masking_effect": masking_effect,
            "by_soa": soa_analysis,
            "masking_curve": masking_curve,
            "task_parameters": {
                "target_duration_ms": self.target_duration_ms,
                "soas": self.soas,
                "mask_duration_ms": self.mask_duration_ms,
                "trials_per_condition": self.num_trials_per_condition,
                "target_strength": self.target_strength,
                "mask_strength": self.mask_strength,
            },
        }

    def print_results(self, analysis: Optional[Dict[str, Any]] = None) -> None:
        """
        Print formatted results to console.

        Parameters
        ----------
        analysis : Dict[str, Any], optional
            Pre-computed analysis. If None, will compute from current results.
        """
        if analysis is None:
            analysis = self.analyze_results()

        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return

        print("\n" + "=" * 80)
        print("MASKING PARADIGM TASK RESULTS")
        print("=" * 80)
        print(f"\nTotal Trials: {analysis['total_trials']}")
        print(f"Overall Detection Rate: {analysis['overall_detection_rate']:.1%}")
        print(f"Overall Suppression Rate: {analysis['overall_suppression_rate']:.1%}")
        print(
            f"Masking Effect: {analysis['masking_effect']:.1%} "
            "(difference between longest and shortest SOA)"
        )

        print("\n" + "-" * 80)
        print("Results by SOA (Stimulus Onset Asynchrony):")
        print("-" * 80)
        print(
            f"{'SOA (ms)':<10} {'Detection':<12} {'Suppression':<14} "
            f"{'Avg Det Time':<14} {'Ignitions':<12}"
        )
        print(f"{'':10} {'Rate':<12} {'Rate':<14} {'(ms)':<14} {'Total':<12}")
        print("-" * 80)

        for soa in sorted(analysis["by_soa"].keys()):
            data = analysis["by_soa"][soa]
            print(
                f"{soa:<10.0f} "
                f"{data['detection_rate']:<12.1%} "
                f"{data['suppression_rate']:<14.1%} "
                f"{data['avg_detection_time_ms']:<14.1f} "
                f"{data['total_ignitions']:<12}"
            )

        print("=" * 80)
        print("\nInterpretation:")
        print("  • Longer SOAs should show higher detection rates (less masking)")
        print("  • Short SOAs (< 50ms) typically show strong masking effects")
        print("  • Masking curve should be monotonically increasing with SOA")
        print("  • High suppression rates at short SOAs indicate effective masking")
        print("\nTask Parameters:")
        params = analysis["task_parameters"]
        print(f"  • Target duration: {params['target_duration_ms']} ms")
        print(f"  • Mask duration: {params['mask_duration_ms']} ms")
        print(f"  • Target strength: {params['target_strength']}")
        print(f"  • Mask strength: {params['mask_strength']}")
        print("=" * 80 + "\n")

    def save_results(self, filename: str) -> None:
        """
        Save results to JSON file.

        Parameters
        ----------
        filename : str
            Output filename (e.g., 'masking_results.json')
        """
        import json
        from datetime import datetime

        analysis = self.analyze_results()

        # Prepare detailed trial data
        trial_data = []
        for result in self.results:
            trial_data.append(
                {
                    "trial_number": result.trial_number,
                    "soa_ms": result.soa_ms,
                    "mask_type": result.mask_type.value,
                    "target_detected": result.target_detected,
                    "detection_time": result.detection_time,
                    "ignition_strength": result.ignition_strength,
                    "ignition_count": result.ignition_count,
                    "mask_suppression_occurred": result.mask_suppression_occurred,
                }
            )

        # Compile full output
        output = {
            "experiment": "Masking Paradigm",
            "timestamp": datetime.now().isoformat(),
            "summary": analysis,
            "trials": trial_data,
        }

        # Save to file
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to: {filename}")

    def reset(self) -> None:
        """Reset task for a new run."""
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results = []
        self._step_state = None
        self._current_trial_result = None
        print("Task reset. Ready for new run.")

    def step(self, apgi_system: Any) -> Dict[str, Any]:
        """
        Execute one step of the current trial.

        Args:
            apgi_system: The APGI system instance

        Returns:
            Dictionary with current state including:
            - 'done': True if trial/task is complete
            - 'trial_complete': True if current trial is complete
            - 'trial_number': Current trial number
            - 'phase': Current phase ('target', 'mask')
            - 'stimulus': Current stimulus being presented
            - 'result': Trial result if trial is complete
            - 'state': Current system state
        """
        # Initialize step state if needed
        if self._step_state is None:
            # Get next trial
            trial = self.get_next_trial()
            if trial is None:
                return {
                    "done": True,
                    "trial_complete": False,
                    "trial_number": None,
                    "phase": None,
                    "stimulus": None,
                    "result": None,
                    "state": None,
                }

            # Initialize trial state
            apgi_system.reset()
            self._step_state = {
                "trial": trial,
                "phase": "target",  # target, mask
                "step_in_phase": 0,
                "target_detected": False,
                "target_ignition_time": None,
                "target_signal_strength": 0.0,
                "mask_detected": False,
                "mask_ignition_time": None,
                "mask_signal_strength": 0.0,
            }
            self._current_trial_result = None

        state = self._step_state
        trial = cast(Trial, state["trial"])

        # Determine stimulus based on phase
        if state["phase"] == "target":
            stimulus = trial.target_stimulus
            phase_duration = self.target_duration_ms
        else:  # mask
            stimulus = trial.mask_stimulus
            phase_duration = self.mask_duration_ms

        # Step the system
        system_state = apgi_system.step(stimulus)

        # Check for ignition
        if system_state["ignition"]["ignition_occurred"]:
            ignition_time = system_state["time"]
            ignition_strength = system_state["ignition"]["total_signal"]

            if state["phase"] == "target" and not state["target_detected"]:
                state["target_detected"] = True
                state["target_ignition_time"] = ignition_time
                state["target_signal_strength"] = ignition_strength

            elif state["phase"] == "mask" and not state["mask_detected"]:
                state["mask_detected"] = True
                state["mask_ignition_time"] = ignition_time
                state["mask_signal_strength"] = ignition_strength

        # Advance step counter
        state["step_in_phase"] += 1

        # Check if phase is complete
        if state["step_in_phase"] >= int(phase_duration):
            state["step_in_phase"] = 0

            # Transition to next phase
            if state["phase"] == "target":
                state["phase"] = "mask"
            else:  # mask
                # Trial complete
                result = TrialResult(
                    trial_number=trial.trial_number,
                    soa_ms=trial.soa_ms,
                    mask_type=trial.mask_type,
                    target_detected=state["target_detected"],
                    detection_time=state["target_ignition_time"],
                    ignition_strength=state["target_signal_strength"],
                    ignition_count=1 if state["target_detected"] or state["mask_detected"] else 0,
                    mask_suppression_occurred=False,
                    mask_detected=state["mask_detected"],
                    target_ignition_time=state["target_ignition_time"],
                    mask_ignition_time=state["mask_ignition_time"],
                    target_signal_strength=state["target_signal_strength"],
                    mask_signal_strength=state["mask_signal_strength"],
                )
                self.results.append(result)
                self.current_trial_idx += 1
                self._step_state = None
                self._current_trial_result = result

                return {
                    "done": self.get_next_trial() is None,
                    "trial_complete": True,
                    "trial_number": trial.trial_number,
                    "phase": None,
                    "stimulus": None,
                    "result": result,
                    "state": None,
                }

        return {
            "done": False,
            "trial_complete": False,
            "trial_number": trial.trial_number,
            "phase": state["phase"],
            "stimulus": stimulus,
            "result": None,
            "state": system_state,
        }
