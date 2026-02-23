"""
Change Blindness Task

Classic change detection paradigm where observers fail to notice changes in visual
scenes when the change is accompanied by a brief visual disruption (flicker).
The original and modified images alternate with blank intervals until the change
is detected or a timeout occurs.

References:
- Rensink, O'Regan & Clark (1997). "To see or not to see: The need for attention
  to perceive changes in scenes."
- Simons & Levin (1997). "Change blindness"
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional, cast
from numpy.typing import NDArray
from dataclasses import dataclass
from enum import Enum
from random import shuffle


class ChangeType(Enum):
    """Types of changes in the scene."""

    APPEARANCE = "appearance"  # Object appears
    DISAPPEARANCE = "disappearance"  # Object disappears
    COLOR = "color"  # Color change
    LOCATION = "location"  # Position change


@dataclass
class Trial:
    """Single trial configuration."""

    trial_number: int
    change_type: ChangeType
    change_magnitude: float  # Strength of the change (0.0-1.0)
    original_image: NDArray[np.float64]  # Original scene
    modified_image: NDArray[np.float64]  # Scene with change
    max_alternations: int  # Maximum number of flicker cycles


@dataclass
class TrialResult:
    """Results from a single trial."""

    trial_number: int
    change_type: ChangeType
    change_magnitude: float
    change_detected: bool  # Whether change was detected
    alternations_to_detection: Optional[int]  # Number of cycles to detect
    time_to_detection: Optional[float]  # Time to detection (ms)
    ignition_signal_strength: float  # Signal strength at detection


class ChangeBlindnessTask:
    """
    Change Blindness experimental task.

    The flicker paradigm: alternates between original and modified images with
    brief blank intervals. Tests the role of attention and ignition in conscious
    change detection.

    Parameters:
    - presentation_duration_ms: Duration of each image presentation (default: 240ms)
    - blank_duration_ms: Duration of blank interval (default: 80ms)
    - max_alternations: Maximum alternation cycles before timeout (default: 20)
    - num_trials_per_condition: Trials per change type/magnitude (default: 10)
    - change_magnitudes: List of change magnitudes to test (default: [0.3, 0.5, 0.8])
    """

    def __init__(
        self,
        presentation_duration_ms: float = 240.0,
        blank_duration_ms: float = 80.0,
        max_alternations: int = 20,
        num_trials_per_condition: int = 10,
        change_magnitudes: Optional[List[float]] = None,
    ):
        """Initialize change blindness task."""
        self.presentation_duration_ms = presentation_duration_ms
        self.blank_duration_ms = blank_duration_ms
        self.max_alternations = max_alternations
        self.num_trials_per_condition = num_trials_per_condition
        self.change_magnitudes = change_magnitudes or [0.3, 0.5, 0.8]

        # Stimulus dimensions (matching system input)
        self.stim_dim = 256

        # Generate all trials
        self.trials = self._generate_trials()
        self.current_trial_idx = 0

        # Results storage
        self.results: List[TrialResult] = []

        # Step execution state
        self._step_state: Optional[Dict[str, Any]] = None
        self._current_trial_result: Optional[TrialResult] = None

    def _generate_trials(self) -> List[Trial]:
        """Generate all trial configurations."""
        trials = []
        trial_num = 0

        # Test each change type and magnitude combination
        change_types = list(ChangeType)

        for change_type in change_types:
            for magnitude in self.change_magnitudes:
                for rep in range(self.num_trials_per_condition):
                    # Generate original and modified images
                    original, modified = self._generate_image_pair(change_type, magnitude)

                    trial = Trial(
                        trial_number=trial_num,
                        change_type=change_type,
                        change_magnitude=magnitude,
                        original_image=original,
                        modified_image=modified,
                        max_alternations=self.max_alternations,
                    )
                    trials.append(trial)
                    trial_num += 1

        # Shuffle trials
        shuffle(trials)

        return trials

    def _generate_image_pair(
        self, change_type: ChangeType, magnitude: float
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Generate original and modified image pair.

        For the APGI system, we represent images as high-dimensional vectors.
        The change is implemented as a localized modification in the vector space.

        Args:
            change_type: Type of change to implement
            magnitude: Strength of the change (0.0-1.0)

        Returns:
            Tuple of (original_image, modified_image)
        """
        # Generate base scene with structured pattern
        # This represents a complex visual scene
        original = self._generate_base_scene()

        # Create modified version based on change type
        modified = original.copy()

        # Change region: middle section of the vector (represents salient object)
        change_region_start = self.stim_dim // 3
        change_region_end = 2 * self.stim_dim // 3
        change_region_size = change_region_end - change_region_start

        if change_type == ChangeType.APPEARANCE:
            # Add new object (increase signal in region)
            modified[change_region_start:change_region_end] += (
                magnitude * 2.0 * np.random.randn(change_region_size)
            )

        elif change_type == ChangeType.DISAPPEARANCE:
            # Remove object (decrease signal in region)
            modified[change_region_start:change_region_end] *= 1.0 - magnitude

        elif change_type == ChangeType.COLOR:
            # Change color (shift pattern in region)
            shift = int(magnitude * 20)  # Shift by up to 20 positions
            region = modified[change_region_start:change_region_end]
            modified[change_region_start:change_region_end] = np.roll(region, shift)

        elif change_type == ChangeType.LOCATION:
            # Move object (swap two regions)
            region1 = modified[change_region_start:change_region_end].copy()
            offset = int(magnitude * 50)  # Movement distance
            region2_start = min(change_region_end + offset, self.stim_dim - change_region_size)
            region2_end = region2_start + change_region_size
            region2 = modified[region2_start:region2_end].copy()

            # Swap regions
            modified[change_region_start:change_region_end] = region2
            modified[region2_start:region2_end] = region1

        return original, modified

    def _generate_base_scene(self) -> NDArray[np.float64]:
        """
        Generate a base visual scene.

        Creates a structured pattern that represents a complex visual scene
        with multiple objects and features.
        """
        scene = np.zeros(self.stim_dim)

        # Add background texture (low-frequency components)
        scene += 0.3 * np.random.randn(self.stim_dim)

        # Add several "objects" at different locations (structured patterns)
        num_objects = 5
        for i in range(num_objects):
            obj_center = (i + 1) * self.stim_dim // (num_objects + 1)
            obj_size = self.stim_dim // (num_objects * 2)
            obj_start = max(0, obj_center - obj_size // 2)
            obj_end = min(self.stim_dim, obj_center + obj_size // 2)

            # Structured pattern for object
            obj_pattern = np.sin(np.linspace(0, 4 * np.pi, obj_end - obj_start))
            scene[obj_start:obj_end] += 0.8 * obj_pattern

        return scene

    def _generate_blank(self) -> NDArray[np.float64]:
        """Generate blank screen (low noise)."""
        return 0.1 * np.random.randn(self.stim_dim)

    def get_next_trial(self) -> Optional[Trial]:
        """Get next trial, or None if task is complete."""
        if self.current_trial_idx >= len(self.trials):
            return None

        trial = self.trials[self.current_trial_idx]
        return trial

    def run_trial(self, apgi_system: Any, trial: Trial) -> TrialResult:
        """
        Run a single trial on the APGI system.

        Alternates between original and modified images with blank intervals.
        Detects if the system achieves ignition during modified image presentation,
        indicating conscious detection of the change.

        Args:
            apgi_system: The APGI system instance
            trial: Trial configuration

        Returns:
            Trial results with detection outcome
        """
        # Reset system for clean trial
        apgi_system.reset()

        # Track detection
        change_detected = False
        alternations_to_detection = None
        time_to_detection = None
        ignition_signal_strength = 0.0

        blank_screen = self._generate_blank()

        # Run alternation cycles
        for alternation in range(trial.max_alternations):
            # === Present ORIGINAL image ===
            presentation_steps = int(self.presentation_duration_ms)

            for _ in range(presentation_steps):
                state = apgi_system.step(trial.original_image)

                # Check for ignition during original (shouldn't happen for change detection)
                if state["ignition"]["ignition_occurred"]:
                    # False positive - ignition during original
                    pass

            # === Blank interval ===
            blank_steps = int(self.blank_duration_ms)
            for _ in range(blank_steps):
                state = apgi_system.step(blank_screen)

            # === Present MODIFIED image ===
            presentation_steps = int(self.presentation_duration_ms)

            for step in range(presentation_steps):
                state = apgi_system.step(trial.modified_image)

                # Check for ignition during modified image
                if state["ignition"]["ignition_occurred"] and not change_detected:
                    # Change detected!
                    change_detected = True
                    alternations_to_detection = alternation + 1
                    time_to_detection = state["time"] - (
                        alternation
                        * (self.presentation_duration_ms * 2 + self.blank_duration_ms * 2)
                    )
                    ignition_signal_strength = state["ignition"]["total_signal"]
                    break

            # If detected, stop alternating
            if change_detected:
                break

            # === Blank interval before next cycle ===
            blank_steps = int(self.blank_duration_ms)
            for _ in range(blank_steps):
                state = apgi_system.step(blank_screen)

        result = TrialResult(
            trial_number=trial.trial_number,
            change_type=trial.change_type,
            change_magnitude=trial.change_magnitude,
            change_detected=change_detected,
            alternations_to_detection=alternations_to_detection,
            time_to_detection=time_to_detection,
            ignition_signal_strength=ignition_signal_strength,
        )

        self.results.append(result)
        self.current_trial_idx += 1

        return result

    def run_all_trials(self, apgi_system: Any) -> Dict[str, Any]:
        """
        Run all trials and return summary statistics.

        Args:
            apgi_system: The APGI system instance

        Returns:
            Dictionary with comprehensive results
        """
        self.results = []
        self.current_trial_idx = 0

        print(f"Running Change Blindness Task: {len(self.trials)} trials")

        for trial_idx, trial in enumerate(self.trials):
            if trial_idx % 10 == 0:
                print(f"Progress: {trial_idx}/{len(self.trials)} trials...")

            self.run_trial(apgi_system, trial)

        # Analyze results
        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze results and compute key metrics.

        Returns:
            Dictionary with analysis including:
            - Detection rates by change type and magnitude
            - Average time to detection
            - Average alternations to detection
            - Change blindness effects
        """
        if not self.results:
            return {"error": "No results to analyze", "total_trials": 0}

        # Organize by change type and magnitude
        results_by_type: Dict[ChangeType, List[TrialResult]] = {ct: [] for ct in ChangeType}
        results_by_magnitude: Dict[float, List[TrialResult]] = {
            mag: [] for mag in self.change_magnitudes
        }
        results_by_type_mag: Dict[ChangeType, Dict[float, List[TrialResult]]] = {
            ct: {mag: [] for mag in self.change_magnitudes} for ct in ChangeType
        }

        for result in self.results:
            results_by_type[result.change_type].append(result)
            results_by_magnitude[result.change_magnitude].append(result)
            results_by_type_mag[result.change_type][result.change_magnitude].append(result)

        # Compute metrics by change type
        type_analysis = {}
        for change_type, type_results in results_by_type.items():
            if not type_results:
                continue

            detected = [r for r in type_results if r.change_detected]

            avg_alternations = (
                np.mean(
                    [
                        r.alternations_to_detection
                        for r in detected
                        if r.alternations_to_detection is not None
                    ]
                )
                if detected
                else 0.0
            )

            avg_time = (
                np.mean([r.time_to_detection for r in detected if r.time_to_detection is not None])
                if detected
                else 0.0
            )

            type_analysis[change_type.value] = {
                "total_trials": len(type_results),
                "detection_rate": len(detected) / len(type_results),
                "avg_alternations_to_detection": avg_alternations,
                "avg_time_to_detection_ms": avg_time,
                "detections": len(detected),
            }

        # Compute metrics by magnitude
        magnitude_analysis = {}
        for magnitude, mag_results in results_by_magnitude.items():
            if not mag_results:
                continue

            detected = [r for r in mag_results if r.change_detected]

            avg_alternations = (
                np.mean(
                    [
                        r.alternations_to_detection
                        for r in detected
                        if r.alternations_to_detection is not None
                    ]
                )
                if detected
                else 0.0
            )

            magnitude_analysis[magnitude] = {
                "total_trials": len(mag_results),
                "detection_rate": len(detected) / len(mag_results),
                "avg_alternations_to_detection": avg_alternations,
                "detections": len(detected),
            }

        # Compute metrics by type AND magnitude
        type_mag_analysis: Dict[str, Dict[float, Dict[str, Any]]] = {}
        for change_type in ChangeType:
            type_mag_analysis[change_type.value] = {}
            for magnitude in self.change_magnitudes:
                results = results_by_type_mag[change_type][magnitude]
                if not results:
                    continue

                detected = [r for r in results if r.change_detected]

                type_mag_analysis[change_type.value][magnitude] = {
                    "total_trials": len(results),
                    "detection_rate": len(detected) / len(results) if results else 0.0,
                    "detections": len(detected),
                }

        # Overall statistics
        total_trials = len(self.results)
        total_detected = sum(1 for r in self.results if r.change_detected)
        detected_results = [r for r in self.results if r.change_detected]

        overall_avg_alternations = (
            np.mean(
                [
                    r.alternations_to_detection
                    for r in detected_results
                    if r.alternations_to_detection is not None
                ]
            )
            if detected_results
            else 0.0
        )

        overall_avg_time = (
            np.mean(
                [r.time_to_detection for r in detected_results if r.time_to_detection is not None]
            )
            if detected_results
            else 0.0
        )

        summary = {
            "total_trials": total_trials,
            "overall_detection_rate": total_detected / total_trials if total_trials > 0 else 0.0,
            "overall_blindness_rate": 1.0
            - (total_detected / total_trials if total_trials > 0 else 0.0),
            "overall_avg_alternations": overall_avg_alternations,
            "overall_avg_time_ms": overall_avg_time,
            "by_change_type": type_analysis,
            "by_magnitude": magnitude_analysis,
            "by_type_and_magnitude": type_mag_analysis,
            "task_parameters": {
                "presentation_duration_ms": self.presentation_duration_ms,
                "blank_duration_ms": self.blank_duration_ms,
                "max_alternations": self.max_alternations,
                "change_magnitudes": self.change_magnitudes,
                "trials_per_condition": self.num_trials_per_condition,
            },
        }

        return summary

    def print_results(self, analysis: Optional[Dict[str, Any]] = None) -> None:
        """Print formatted results."""
        if analysis is None:
            analysis = self.analyze_results()

        print("\n" + "=" * 70)
        print("CHANGE BLINDNESS TASK RESULTS")
        print("=" * 70)

        print(f"\nTotal Trials: {analysis['total_trials']}")
        print(f"Overall Detection Rate: {analysis['overall_detection_rate']:.1%}")
        print(f"Overall Blindness Rate: {analysis['overall_blindness_rate']:.1%}")
        print(f"Avg Alternations to Detection: {analysis['overall_avg_alternations']:.1f}")
        print(f"Avg Time to Detection: {analysis['overall_avg_time_ms']:.0f} ms")

        print("\n" + "-" * 70)
        print("Results by Change Type:")
        print("-" * 70)
        print(f"{'Type':<20} {'Detection Rate':<18} {'Avg Alternations':<18}")
        print("-" * 70)

        for change_type, data in analysis["by_change_type"].items():
            print(
                f"{change_type:<20} "
                f"{data['detection_rate']:<18.1%} "
                f"{data['avg_alternations_to_detection']:<18.1f}"
            )

        print("\n" + "-" * 70)
        print("Results by Change Magnitude:")
        print("-" * 70)
        print(f"{'Magnitude':<15} {'Detection Rate':<18} {'Avg Alternations':<18}")
        print("-" * 70)

        for magnitude in sorted(analysis["by_magnitude"].keys()):
            data = analysis["by_magnitude"][magnitude]
            print(
                f"{magnitude:<15.1f} "
                f"{data['detection_rate']:<18.1%} "
                f"{data['avg_alternations_to_detection']:<18.1f}"
            )

        print("\n" + "-" * 70)
        print("Detection Matrix (Change Type × Magnitude):")
        print("-" * 70)

        # Print header
        header = f"{'Type':<20}"
        for mag in sorted(self.change_magnitudes):
            header += f"{mag:<12.1f}"
        print(header)
        print("-" * 70)

        # Print rows
        for change_type in ChangeType:
            row = f"{change_type.value:<20}"
            for mag in sorted(self.change_magnitudes):
                if mag in analysis["by_type_and_magnitude"].get(change_type.value, {}):
                    rate = analysis["by_type_and_magnitude"][change_type.value][mag][
                        "detection_rate"
                    ]
                    row += f"{rate:<12.1%}"
                else:
                    row += f"{'N/A':<12}"
            print(row)

        print("=" * 70)

        # Interpretation
        print("\nInterpretation:")
        if analysis["overall_blindness_rate"] > 0.3:
            print("✓ Strong change blindness effect observed")
            print(f"  {analysis['overall_blindness_rate']:.1%} of changes were missed")
        elif analysis["overall_blindness_rate"] > 0.15:
            print("~ Moderate change blindness effect")
        else:
            print("✗ Weak or no change blindness (high detection)")

        print("\nExpected pattern:")
        print("  - Lower detection rates for subtle changes (low magnitude)")
        print("  - Higher detection for salient changes (high magnitude)")
        print("  - Some change types may be harder to detect than others")
        print("  - Longer detection times indicate change blindness")
        print()

    def save_results(self, filename: str) -> None:
        """Save results to JSON file."""
        import json

        analysis = self.analyze_results()

        # Add individual trial data
        trial_data = []
        for result in self.results:
            trial_data.append(
                {
                    "trial_number": result.trial_number,
                    "change_type": result.change_type.value,
                    "change_magnitude": result.change_magnitude,
                    "change_detected": result.change_detected,
                    "alternations_to_detection": result.alternations_to_detection,
                    "time_to_detection": result.time_to_detection,
                    "ignition_signal_strength": result.ignition_signal_strength,
                }
            )

        output = {"summary": analysis, "trials": trial_data}

        with open(filename, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to: {filename}")

    def reset(self) -> None:
        """Reset task for new run."""
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results = []
        self._step_state = None
        self._current_trial_result = None

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
            - 'phase': Current phase ('original', 'blank', 'modified')
            - 'alternation': Current alternation number
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
                    "alternation": None,
                    "stimulus": None,
                    "result": None,
                    "state": None,
                }

            # Initialize trial state
            apgi_system.reset()
            blank_screen = self._generate_blank()
            self._step_state = {
                "trial": trial,
                "alternation": 0,
                "phase": "original",  # original, blank, modified
                "step_in_phase": 0,
                "blank_screen": blank_screen,
                "change_detected": False,
                "alternations_to_detection": None,
                "time_to_detection": None,
                "ignition_signal_strength": 0.0,
            }
            self._current_trial_result = None

        state = self._step_state
        trial = cast(Trial, state["trial"])

        # Determine stimulus based on phase
        if state["phase"] == "original":
            stimulus = trial.original_image  # type: ignore[union-attr]
            phase_duration = self.presentation_duration_ms
        elif state["phase"] == "blank":
            stimulus = state["blank_screen"]
            phase_duration = self.blank_duration_ms
        else:  # modified
            stimulus = trial.modified_image  # type: ignore[union-attr]
            phase_duration = self.presentation_duration_ms

        # Step the system
        system_state = apgi_system.step(stimulus)

        # Check for ignition during modified image
        if state["phase"] == "modified" and not state["change_detected"]:
            if system_state["ignition"]["ignition_occurred"]:
                state["change_detected"] = True
                state["alternations_to_detection"] = state["alternation"] + 1
                state["time_to_detection"] = system_state["time"] - (
                    state["alternation"]
                    * (self.presentation_duration_ms * 2 + self.blank_duration_ms * 2)
                )
                state["ignition_signal_strength"] = system_state["ignition"]["total_signal"]

        # Advance step counter
        state["step_in_phase"] += 1

        # Check if phase is complete
        if state["step_in_phase"] >= int(phase_duration):
            state["step_in_phase"] = 0

            # Transition to next phase
            if state["phase"] == "original":
                state["phase"] = "blank"
            elif state["phase"] == "blank":
                state["phase"] = "modified"
            else:  # modified
                state["phase"] = "blank"
                state["alternation"] += 1

                # Check if should stop (detected or max alternations)
                if state["change_detected"] or state["alternation"] >= trial.max_alternations:  # type: ignore[union-attr]
                    # Trial complete
                    result = TrialResult(
                        trial_number=trial.trial_number,  # type: ignore[union-attr]
                        change_type=trial.change_type,  # type: ignore[union-attr]
                        change_magnitude=trial.change_magnitude,  # type: ignore[union-attr]
                        change_detected=state["change_detected"],
                        alternations_to_detection=state["alternations_to_detection"],
                        time_to_detection=state["time_to_detection"],
                        ignition_signal_strength=state["ignition_signal_strength"],
                    )
                    self.results.append(result)
                    self.current_trial_idx += 1
                    self._step_state = None
                    self._current_trial_result = result

                    return {
                        "done": self.get_next_trial() is None,
                        "trial_complete": True,
                        "trial_number": trial.trial_number,  # type: ignore[union-attr]
                        "phase": None,
                        "alternation": state["alternation"],
                        "stimulus": None,
                        "result": result,
                        "state": None,
                    }

        return {
            "done": False,
            "trial_complete": False,
            "trial_number": trial.trial_number,  # type: ignore[union-attr]
            "phase": state["phase"],
            "alternation": state["alternation"],
            "stimulus": stimulus,
            "result": None,
            "state": system_state,
        }
