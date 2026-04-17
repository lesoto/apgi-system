"""
Attentional Blink Task

Classic RSVP (Rapid Serial Visual Presentation) paradigm where two targets
are embedded in a stream of distractors. The second target (T2) is often
missed when presented 200-500ms after the first target (T1), demonstrating
the temporal limits of conscious access.

References:
- Raymond, Shapiro & Arnell (1992). "Temporary suppression of visual processing
  in an RSVP task: An attentional blink?"
- Sergent & Dehaene (2004). "Is consciousness a gradual phenomenon?"
"""

from dataclasses import dataclass
from enum import Enum
from random import shuffle
from typing import Any, Dict, List, Optional, cast

import numpy as np
from numpy.typing import NDArray


class StimulusType(Enum):
    """Types of stimuli in RSVP stream."""

    DISTRACTOR = "distractor"
    TARGET_1 = "target_1"
    TARGET_2 = "target_2"


@dataclass
class Trial:
    """Single trial configuration."""

    trial_number: int
    t1_position: int  # Position in stream (0-indexed)
    t2_position: int  # Position in stream
    lag: int  # Number of items between T1 and T2
    stream: List[NDArray[np.float64]]  # Full stimulus stream
    stream_types: List[StimulusType]  # Type of each stimulus


@dataclass
class TrialResult:
    """Results from a single trial."""

    trial_number: int
    lag: int
    t1_detected: bool  # Whether T1 triggered ignition
    t2_detected: bool  # Whether T2 triggered ignition
    t1_ignition_time: Optional[float]  # Time of T1 ignition (ms)
    t2_ignition_time: Optional[float]  # Time of T2 ignition (ms)
    t1_signal_strength: float  # Ignition signal for T1
    t2_signal_strength: float  # Ignition signal for T2
    blink_occurred: bool  # T1 detected but T2 missed


class AttentionalBlinkTask:
    """
    Attentional Blink experimental task.

    Parameters:
    - stream_length: Number of items in RSVP stream (default: 15)
    - item_duration_ms: Duration of each item (default: 100ms)
    - num_trials_per_lag: Number of trials for each lag condition (default: 20)
    - lags: List of lags to test (default: [1, 2, 3, 4, 8])
    - target_salience: Salience boost for targets vs distractors (default: 2.0)
    """

    def __init__(
        self,
        stream_length: int = 15,
        item_duration_ms: float = 100.0,
        num_trials_per_lag: int = 20,
        lags: Optional[List[int]] = None,
        target_salience: float = 2.0,
    ):
        """Initialize attentional blink task."""
        self.stream_length = stream_length
        self.item_duration_ms = item_duration_ms
        self.num_trials_per_lag = num_trials_per_lag
        self.lags = lags or [1, 2, 3, 4, 8]  # Lag-1 to Lag-8
        self.target_salience = target_salience

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

        for lag in self.lags:
            for rep in range(self.num_trials_per_lag):
                # T1 position: not too early or late
                t1_pos = np.random.randint(3, self.stream_length - lag - 3)
                t2_pos = t1_pos + lag

                # Generate stimulus stream
                stream = []
                stream_types = []

                for i in range(self.stream_length):
                    if i == t1_pos:
                        stim = self._generate_target(target_num=1)
                        stim_type = StimulusType.TARGET_1
                    elif i == t2_pos:
                        stim = self._generate_target(target_num=2)
                        stim_type = StimulusType.TARGET_2
                    else:
                        stim = self._generate_distractor()
                        stim_type = StimulusType.DISTRACTOR

                    stream.append(stim)
                    stream_types.append(stim_type)

                trial = Trial(
                    trial_number=trial_num,
                    t1_position=t1_pos,
                    t2_position=t2_pos,
                    lag=lag,
                    stream=stream,
                    stream_types=stream_types,
                )
                trials.append(trial)
                trial_num += 1

        # Shuffle trials
        shuffle(trials)

        return trials

    def _generate_target(self, target_num: int) -> NDArray[np.float64]:
        """
        Generate a target stimulus (high salience).

        Target stimuli have higher amplitude to simulate salience.
        T1 and T2 have slightly different patterns for distinctiveness.
        """
        if target_num == 1:
            # T1: Strong signal at beginning of vector
            target = np.zeros(self.stim_dim)
            target[:50] = self.target_salience * np.random.randn(50)
        else:
            # T2: Strong signal at middle of vector
            target = np.zeros(self.stim_dim)
            target[50:100] = self.target_salience * np.random.randn(50)

        # Add some noise
        target += 0.2 * np.random.randn(self.stim_dim)

        return target

    def _generate_distractor(self) -> NDArray[np.float64]:
        """Generate a distractor stimulus (low salience)."""
        # Weak random noise
        distractor = 0.5 * np.random.randn(self.stim_dim)
        return distractor

    def get_next_trial(self) -> Optional[Trial]:
        """Get next trial, or None if task is complete."""
        if self.current_trial_idx >= len(self.trials):
            return None

        trial = self.trials[self.current_trial_idx]
        return trial

    def run_trial(self, apgi_simulation: Any, trial: Trial) -> TrialResult:
        """
        Run a single trial on the APGI system.

        Args:
            apgi_simulation: The APGI system instance
            trial: Trial configuration

        Returns:
            Trial results with detection outcomes
        """
        # Reset system for clean trial
        apgi_simulation.reset()

        # Track ignitions
        t1_detected = False
        t2_detected = False
        t1_ignition_time = None
        t2_ignition_time = None
        t1_signal_strength = 0.0
        t2_signal_strength = 0.0

        # Track what position we're at and what we've seen
        seen_t1 = False
        seen_t2 = False
        t1_presentation_time = None
        t2_presentation_time = None

        # Present entire stream
        for position, (stimulus, stim_type) in enumerate(zip(trial.stream, trial.stream_types)):
            # Present stimulus for item_duration_ms
            start_time = apgi_simulation.time

            # Track presentation times
            if stim_type == StimulusType.TARGET_1:
                t1_presentation_time = start_time
                seen_t1 = True
            elif stim_type == StimulusType.TARGET_2:
                t2_presentation_time = start_time
                seen_t2 = True

            # Step through presentation duration
            presentation_steps = int(self.item_duration_ms)
            for _ in range(presentation_steps):
                state = apgi_simulation.step(stimulus)

                # Check for ignition
                if state["ignition"]["ignition_occurred"]:
                    ignition_time = state["time"]

                    # Determine which target this ignition is for
                    # Within 400ms window after target presentation
                    if seen_t1 and not t1_detected:
                        if t1_presentation_time is not None:
                            time_since_t1 = ignition_time - t1_presentation_time
                            if 0 <= time_since_t1 <= 400:  # 400ms window
                                t1_detected = True
                                t1_ignition_time = ignition_time
                                t1_signal_strength = state["ignition"]["total_signal"]

                    if seen_t2 and not t2_detected:
                        if t2_presentation_time is not None:
                            time_since_t2 = ignition_time - t2_presentation_time
                            if 0 <= time_since_t2 <= 400:  # 400ms window
                                t2_detected = True
                                t2_ignition_time = ignition_time
                                t2_signal_strength = state["ignition"]["total_signal"]

        # Determine if blink occurred: T1 detected but T2 missed
        blink_occurred = t1_detected and not t2_detected

        result = TrialResult(
            trial_number=trial.trial_number,
            lag=trial.lag,
            t1_detected=t1_detected,
            t2_detected=t2_detected,
            t1_ignition_time=t1_ignition_time,
            t2_ignition_time=t2_ignition_time,
            t1_signal_strength=t1_signal_strength,
            t2_signal_strength=t2_signal_strength,
            blink_occurred=blink_occurred,
        )

        self.results.append(result)
        self.current_trial_idx += 1

        return result

    def run_all_trials(self, apgi_simulation: Any) -> Dict[str, Any]:
        """
        Run all trials and return summary statistics.

        Args:
            apgi_simulation: The APGI system instance

        Returns:
            Dictionary with comprehensive results
        """
        self.results = []
        self.current_trial_idx = 0

        print(f"Running Attentional Blink Task: {len(self.trials)} trials")

        for trial_idx, trial in enumerate(self.trials):
            if trial_idx % 10 == 0:
                print(f"Progress: {trial_idx}/{len(self.trials)} trials...")

        # Analyze results
        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze results and compute key metrics.

        Returns:
            Dictionary with analysis including:
            - T1 accuracy by lag
            - T2 accuracy by lag (T2|T1 accuracy)
            - Blink magnitude
            - Timing statistics
        """
        if not self.results:
            return {"error": "No results to analyze", "total_trials": 0}

        # Organize by lag
        results_by_lag: Dict[int, List[TrialResult]] = {lag: [] for lag in self.lags}
        for result in self.results:
            results_by_lag[result.lag].append(result)

        # Compute metrics for each lag
        lag_analysis = {}
        for lag, lag_results in results_by_lag.items():
            total = len(lag_results)
            t1_correct = sum(1 for r in lag_results if r.t1_detected)
            t2_correct = sum(1 for r in lag_results if r.t2_detected)

            # T2|T1: T2 accuracy given T1 was detected
            t1_trials = [r for r in lag_results if r.t1_detected]
            t2_given_t1 = sum(1 for r in t1_trials if r.t2_detected) if t1_trials else 0
            t2_given_t1_rate = t2_given_t1 / len(t1_trials) if t1_trials else 0.0

            blink_count = sum(1 for r in lag_results if r.blink_occurred)

            lag_analysis[lag] = {
                "total_trials": total,
                "t1_accuracy": t1_correct / total if total > 0 else 0.0,
                "t2_accuracy": t2_correct / total if total > 0 else 0.0,
                "t2_given_t1_accuracy": t2_given_t1_rate,
                "blink_rate": blink_count / total if total > 0 else 0.0,
                "t1_detections": t1_correct,
                "t2_detections": t2_correct,
                "blink_occurrences": blink_count,
            }

        # Overall statistics
        total_trials = len(self.results)
        total_t1 = sum(1 for r in self.results if r.t1_detected)
        total_t2 = sum(1 for r in self.results if r.t2_detected)
        total_blinks = sum(1 for r in self.results if r.blink_occurred)

        # Find the lag with maximum blink (typically lag 2-3)
        max_blink_lag = max(lag_analysis.items(), key=lambda x: x[1]["blink_rate"])

        summary = {
            "total_trials": total_trials,
            "overall_t1_accuracy": total_t1 / total_trials if total_trials > 0 else 0.0,
            "overall_t2_accuracy": total_t2 / total_trials if total_trials > 0 else 0.0,
            "overall_blink_rate": total_blinks / total_trials if total_trials > 0 else 0.0,
            "lag_analysis": lag_analysis,
            "max_blink_lag": max_blink_lag[0],
            "max_blink_rate": max_blink_lag[1]["blink_rate"],
            "task_parameters": {
                "stream_length": self.stream_length,
                "item_duration_ms": self.item_duration_ms,
                "lags_tested": self.lags,
                "trials_per_lag": self.num_trials_per_lag,
            },
        }

        return summary

    def print_results(self, analysis: Optional[Dict[str, Any]] = None) -> None:
        """Print formatted results."""
        if analysis is None:
            analysis = self.analyze_results()

        print("\n" + "=" * 70)
        print("ATTENTIONAL BLINK TASK RESULTS")
        print("=" * 70)

        print(f"\nTotal Trials: {analysis['total_trials']}")
        print(f"Overall T1 Accuracy: {analysis['overall_t1_accuracy']:.1%}")
        print(f"Overall T2 Accuracy: {analysis['overall_t2_accuracy']:.1%}")
        print(f"Overall Blink Rate: {analysis['overall_blink_rate']:.1%}")

        print(
            f"\nMaximum Blink at Lag {analysis['max_blink_lag']}: {analysis['max_blink_rate']:.1%}"
        )

        print("\n" + "-" * 70)
        print("Results by Lag:")
        print("-" * 70)
        print(f"{'Lag':<6} {'T1 Acc':<10} {'T2 Acc':<10} {'T2|T1 Acc':<12} {'Blink Rate':<12}")
        print("-" * 70)

        for lag in sorted(analysis["lag_analysis"].keys()):
            lag_data = analysis["lag_analysis"][lag]
            print(
                f"{lag:<6} "
                f"{lag_data['t1_accuracy']:<10.1%} "
                f"{lag_data['t2_accuracy']:<10.1%} "
                f"{lag_data['t2_given_t1_accuracy']:<12.1%} "
                f"{lag_data['blink_rate']:<12.1%}"
            )

        print("=" * 70)

        # Interpretation
        print("\nInterpretation:")
        if analysis["max_blink_rate"] > 0.3:
            print("✓ Strong attentional blink observed")
            print(
                f"  Peak blink at lag {analysis['max_blink_lag']} ({analysis['max_blink_rate']:.1%})"
            )
        elif analysis["max_blink_rate"] > 0.15:
            print("~ Moderate attentional blink observed")
        else:
            print("✗ Weak or no attentional blink")

        print("\nExpected pattern:")
        print("  - High T1 accuracy (>80%)")
        print("  - T2 accuracy dip at lag 2-4 (attentional blink)")
        print("  - T2 accuracy recovery at lag 8+ (sparing)")
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
                    "lag": result.lag,
                    "t1_detected": result.t1_detected,
                    "t2_detected": result.t2_detected,
                    "t1_ignition_time": result.t1_ignition_time,
                    "t2_ignition_time": result.t2_ignition_time,
                    "t1_signal_strength": result.t1_signal_strength,
                    "t2_signal_strength": result.t2_signal_strength,
                    "blink_occurred": result.blink_occurred,
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

    def step(self, apgi_simulation: Any) -> Dict[str, Any]:
        """
        Execute one step of the current trial.

        This method allows incremental execution of the task, useful for:
        - Real-time interaction
        - GUI integration
        - Testing and debugging

        Args:
            apgi_simulation: The APGI system instance

        Returns:
            Dictionary with current state including:
            - 'done': True if trial/task is complete
            - 'trial_complete': True if current trial is complete
            - 'trial_number': Current trial number
            - 'stimulus': Current stimulus being presented
            - 'stimulus_type': Type of current stimulus
            - 'position': Current position in stream
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
                    "stimulus": None,
                    "stimulus_type": None,
                    "position": None,
                    "result": None,
                    "state": None,
                }

            # Initialize trial state
            apgi_simulation.reset()
            self._step_state = {
                "trial": trial,
                "position": 0,
                "step_in_position": 0,
                "t1_detected": False,
                "t2_detected": False,
                "t1_ignition_time": None,
                "t2_ignition_time": None,
                "t1_signal_strength": 0.0,
                "t2_signal_strength": 0.0,
                "t1_presentation_time": None,
                "t2_presentation_time": None,
                "seen_t1": False,
                "seen_t2": False,
            }
            self._current_trial_result = None

        state = self._step_state
        trial = cast(Trial, state["trial"])

        # Get current stimulus
        if state["position"] >= len(trial.stream):
            # Trial complete
            blink_occurred = state["t1_detected"] and not state["t2_detected"]
            result = TrialResult(
                trial_number=trial.trial_number,
                lag=trial.lag,
                t1_detected=state["t1_detected"],
                t2_detected=state["t2_detected"],
                t1_ignition_time=state["t1_ignition_time"],
                t2_ignition_time=state["t2_ignition_time"],
                t1_signal_strength=state["t1_signal_strength"],
                t2_signal_strength=state["t2_signal_strength"],
                blink_occurred=blink_occurred,
            )
            self.results.append(result)
            self.current_trial_idx += 1
            self._step_state = None
            self._current_trial_result = result

            return {
                "done": self.get_next_trial() is None,
                "trial_complete": True,
                "trial_number": trial.trial_number,
                "stimulus": None,
                "stimulus_type": None,
                "position": state["position"],
                "result": result,
                "state": None,
            }

        stimulus = trial.stream[state["position"]]
        stim_type = trial.stream_types[state["position"]]

        # Track presentation times
        if stim_type == StimulusType.TARGET_1:
            state["t1_presentation_time"] = apgi_simulation.time
            state["seen_t1"] = True
        elif stim_type == StimulusType.TARGET_2:
            state["t2_presentation_time"] = apgi_simulation.time
            state["seen_t2"] = True

        # Step the system
        system_state = apgi_simulation.step(stimulus)

        # Check for ignition
        if system_state["ignition"]["ignition_occurred"]:
            ignition_time = system_state["time"]

            # Determine which target this ignition is for
            if state["seen_t1"] and not state["t1_detected"]:
                if state["t1_presentation_time"] is not None:
                    time_since_t1 = ignition_time - state["t1_presentation_time"]
                    if 0 <= time_since_t1 <= 400:  # 400ms window
                        state["t1_detected"] = True
                        state["t1_ignition_time"] = ignition_time
                        state["t1_signal_strength"] = system_state["ignition"]["total_signal"]

            if state["seen_t2"] and not state["t2_detected"]:
                if state["t2_presentation_time"] is not None:
                    time_since_t2 = ignition_time - state["t2_presentation_time"]
                    if 0 <= time_since_t2 <= 400:  # 400ms window
                        state["t2_detected"] = True
                        state["t2_ignition_time"] = ignition_time
                        state["t2_signal_strength"] = system_state["ignition"]["total_signal"]

        # Advance step counter
        state["step_in_position"] += 1
        if state["step_in_position"] >= int(self.item_duration_ms):
            state["position"] += 1
            state["step_in_position"] = 0

        return {
            "done": False,
            "trial_complete": False,
            "trial_number": trial.trial_number,
            "stimulus": stimulus,
            "stimulus_type": stim_type,
            "position": state["position"],
            "result": None,
            "state": system_state,
        }
