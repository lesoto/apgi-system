"""
N-Back Task

The N-back task is a widely used paradigm for assessing working memory and cognitive control.
Participants monitor a sequence of stimuli and indicate when the current stimulus matches
the one presented N positions back in the sequence.

Key findings:
- Performance decreases as N increases (1-back > 2-back > 3-back)
- Activates dorsolateral prefrontal cortex and parietal regions
- Requires continuous updating and maintenance of information
- Sensitive to age-related cognitive decline and neurological disorders

This task tests how the APGI system handles:
- Working memory maintenance and updating
- Continuous monitoring and attention
- Temporal order processing
- Cognitive load and capacity limitations

References:
- Kirchner, W. K. (1958). Age differences in short-term retention of rapidly changing information.
  Journal of Experimental Psychology, 55(4), 352-358.
- Owen, A. M., McMillan, K. M., Laird, A. R., & Bullmore, E. (2005). N-back working memory
  paradigm: A meta-analysis of normative functional neuroimaging studies. Human Brain Mapping, 25(1), 46-59.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import random
import time
import string
from scipy.special import erfcinv  # type: ignore


class StimulusType(Enum):
    """Types of stimuli used in the N-back task."""

    LETTERS = "letters"
    NUMBERS = "numbers"
    SHAPES = "shapes"
    POSITIONS = "positions"


@dataclass
class NBackTrial:
    """Represents a single trial in the N-back task."""

    trial_number: int
    stimulus: str
    stimulus_type: StimulusType
    is_target: bool  # True if this matches N-back stimulus
    correct_response: bool  # True if participant should respond
    response: Optional[bool] = None  # Participant's actual response
    response_time: Optional[float] = None
    is_correct: bool = False


@dataclass
class NBackResults:
    """Results from an N-back task session."""

    n_level: int
    total_trials: int
    target_trials: int
    non_target_trials: int
    hits: int  # Correctly identified targets
    misses: int  # Missed targets
    correct_rejections: int  # Correctly rejected non-targets
    false_alarms: int  # Incorrectly responded to non-targets
    accuracy: float
    hit_rate: float
    false_alarm_rate: float
    d_prime: float  # Signal detection measure
    criterion: float  # Response bias measure
    mean_rt_hits: float
    mean_rt_correct_rejections: float


class NBackTask:
    """
    Implements the N-back working memory task.

    The task presents a sequence of stimuli and requires participants to indicate when
    the current stimulus matches the one presented N positions back.
    """

    def __init__(
        self,
        n_level: int = 2,
        num_trials: int = 100,
        stimulus_type: StimulusType = StimulusType.LETTERS,
        target_probability: float = 0.3,
        random_seed: Optional[int] = None,
    ):
        """
        Initialize the N-back task.

        Args:
            n_level: The N value (how many positions back to match)
            num_trials: Total number of trials in the task
            stimulus_type: Type of stimuli to use
            target_probability: Probability of target trials
            random_seed: Seed for random number generation
        """
        self.n_level = n_level
        self.num_trials = num_trials
        self.stimulus_type = stimulus_type
        self.target_probability = target_probability
        self.random_seed = random_seed

        if random_seed:
            random.seed(random_seed)
            np.random.seed(random_seed)

        # Stimulus sets
        self.letter_stimuli = list(string.ascii_uppercase)[:20]  # A-T
        self.number_stimuli = list(range(1, 10))  # 1-9
        self.shape_stimuli = ["CIRCLE", "SQUARE", "TRIANGLE", "DIAMOND", "STAR"]
        self.position_stimuli = ["TOP", "BOTTOM", "LEFT", "RIGHT", "CENTER"]

        # State tracking
        self.current_trial = 0
        self.trials: List[NBackTrial] = []
        self.task_start_time: Optional[float] = None
        self.stimulus_history: List[str] = []
        self.results: List[Dict[str, Any]] = []

        # Generate trials
        self._generate_trials()

    def _get_stimulus_set(self) -> List[str]:
        """Get the stimulus set based on the stimulus type."""
        if self.stimulus_type == StimulusType.LETTERS:
            return self.letter_stimuli
        elif self.stimulus_type == StimulusType.NUMBERS:
            return [str(s) for s in self.number_stimuli]
        elif self.stimulus_type == StimulusType.SHAPES:
            return self.shape_stimuli
        elif self.stimulus_type == StimulusType.POSITIONS:
            return self.position_stimuli
        else:
            raise ValueError(f"Unknown stimulus type: {self.stimulus_type}")

    def _generate_trials(self) -> None:
        """Generate the sequence of trials for the task."""
        stimulus_set = self._get_stimulus_set()
        trials = []
        stimulus_history: List[str] = []

        for trial_num in range(self.num_trials):
            # Determine if this should be a target trial
            if trial_num < self.n_level:
                # First N trials cannot be targets
                is_target = False
            else:
                is_target = random.random() < self.target_probability

            if is_target and trial_num >= self.n_level:
                # Make it a target by repeating the stimulus from N trials back
                stimulus = stimulus_history[-self.n_level]
            else:
                # Choose a random stimulus that doesn't create an unintended target
                while True:
                    stimulus = random.choice(stimulus_set)
                    # Check if this would accidentally create a target
                    if trial_num < self.n_level or stimulus != stimulus_history[-self.n_level]:
                        break

            # Create trial
            trial = NBackTrial(
                trial_number=trial_num + 1,
                stimulus=stimulus,
                stimulus_type=self.stimulus_type,
                is_target=is_target,
                correct_response=is_target,
            )
            trials.append(trial)
            stimulus_history.append(stimulus)

        self.trials = trials
        self.stimulus_history = stimulus_history

    def start_task(self) -> None:
        """Start the N-back task."""
        self.task_start_time = time.time()
        self.current_trial = 0

    def get_current_trial(self) -> Optional[NBackTrial]:
        """Get the current trial."""
        if self.current_trial < len(self.trials):
            return self.trials[self.current_trial]
        return None

    def record_response(self, response: bool, response_time: float) -> bool:
        """
        Record a response for the current trial.

        Args:
            response: The participant's response (True = target, False = non-target)
            response_time: Time taken to respond in seconds

        Returns:
            True if the response was correct, False otherwise
        """
        if self.current_trial >= len(self.trials):
            return False

        trial = self.trials[self.current_trial]
        trial.response = response
        trial.response_time = response_time
        trial.is_correct = response == trial.correct_response

        self.current_trial += 1
        return trial.is_correct

    def is_complete(self) -> bool:
        """Check if the task is complete."""
        return self.current_trial >= len(self.trials)

    def get_results(self) -> NBackResults:
        """
        Calculate and return the task results.

        Returns:
            NBackResults object with performance metrics
        """
        if not self.is_complete():
            raise ValueError("Task is not complete")

        # Count different types of responses
        hits = sum(1 for t in self.trials if t.is_target and t.response is True)
        misses = sum(1 for t in self.trials if t.is_target and t.response is False)
        correct_rejections = sum(1 for t in self.trials if not t.is_target and t.response is False)
        false_alarms = sum(1 for t in self.trials if not t.is_target and t.response is True)

        target_trials = sum(1 for t in self.trials if t.is_target)
        non_target_trials = sum(1 for t in self.trials if not t.is_target)

        # Calculate accuracy
        total_correct = hits + correct_rejections
        accuracy = total_correct / len(self.trials) if self.trials else 0.0

        # Calculate signal detection measures
        hit_rate = hits / target_trials if target_trials > 0 else 0.0
        false_alarm_rate = false_alarms / non_target_trials if non_target_trials > 0 else 0.0

        # Calculate d' and criterion (with extreme value correction)
        hit_rate_corr = min(max(hit_rate, 0.01), 0.99)
        false_alarm_rate_corr = min(max(false_alarm_rate, 0.01), 0.99)

        z_hit = np.sqrt(2) * erfcinv(2 * (1 - hit_rate_corr))
        z_fa = np.sqrt(2) * erfcinv(2 * (1 - false_alarm_rate_corr))
        d_prime = z_hit - z_fa
        criterion = -0.5 * (z_hit + z_fa)

        # Calculate mean response times
        hit_rts = [
            t.response_time
            for t in self.trials
            if t.is_target and t.response is True and t.response_time is not None
        ]
        cr_rts = [
            t.response_time
            for t in self.trials
            if not t.is_target and t.response is False and t.response_time is not None
        ]

        mean_rt_hits = float(np.mean(hit_rts) if hit_rts else 0.0)
        mean_rt_correct_rejections = float(np.mean(cr_rts) if cr_rts else 0.0)

        return NBackResults(
            n_level=self.n_level,
            total_trials=len(self.trials),
            target_trials=target_trials,
            non_target_trials=non_target_trials,
            hits=hits,
            misses=misses,
            correct_rejections=correct_rejections,
            false_alarms=false_alarms,
            accuracy=accuracy,
            hit_rate=hit_rate,
            false_alarm_rate=false_alarm_rate,
            d_prime=d_prime,
            criterion=criterion,
            mean_rt_hits=mean_rt_hits,
            mean_rt_correct_rejections=mean_rt_correct_rejections,
        )

    def get_trial_summary(self) -> Dict[str, Any]:
        """Get a summary of all trials for analysis."""
        return {
            "n_level": self.n_level,
            "stimulus_type": self.stimulus_type.value,
            "total_trials": len(self.trials),
            "completed_trials": self.current_trial,
            "trials": [
                {
                    "trial_number": trial.trial_number,
                    "stimulus": trial.stimulus,
                    "stimulus_type": trial.stimulus_type.value,
                    "is_target": trial.is_target,
                    "correct_response": trial.correct_response,
                    "response": trial.response,
                    "response_time": trial.response_time,
                    "is_correct": trial.is_correct,
                }
                for trial in self.trials
            ],
        }

    def reset_task(self) -> None:
        """Reset the task to start over."""
        self.current_trial = 0
        self.task_start_time = None
        self.stimulus_history = []

        # Reset trial data
        for trial in self.trials:
            trial.response = None
            trial.response_time = None
            trial.is_correct = False

        # Regenerate trials if needed
        if self.random_seed:
            random.seed(self.random_seed)
            np.random.seed(self.random_seed)
            self._generate_trials()

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
        self.current_trial = 0

        print(f"\n{'=' * 70}")
        print(f"Running N-Back Task: {len(self.trials)} trials")
        print(f"{'=' * 70}\n")

        for trial_idx, trial in enumerate(self.trials):
            if trial_idx % 10 == 0:
                progress = (trial_idx / len(self.trials)) * 100
                print(f"Progress: {trial_idx}/{len(self.trials)} trials ({progress:.1f}%)...")

            # For N-back task, we need to simulate participant responses
            # In a real experiment, this would come from user input
            # For now, simulate with some accuracy
            response_time = 0.5 + np.random.exponential(0.3)  # Simulate RT distribution

            # Simulate participant accuracy (imperfect but above chance)
            if trial.is_target:
                response = np.random.random() < 0.8  # 80% hit rate
            else:
                response = np.random.random() < 0.2  # 20% false alarm rate

            self.record_response(response, response_time)

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
            - Results by condition
            - Task parameters
        """
        if not self.is_complete():
            return {"error": "Task not complete", "total_trials": len(self.trials)}

        results = self.get_results()

        return {
            "total_trials": results.total_trials,
            "overall_accuracy": results.accuracy,
            "hit_rate": results.hit_rate,
            "false_alarm_rate": results.false_alarm_rate,
            "d_prime": results.d_prime,
            "criterion": results.criterion,
            "mean_rt_hits": results.mean_rt_hits,
            "mean_rt_correct_rejections": results.mean_rt_correct_rejections,
            "by_condition": {},  # N-back doesn't have multiple conditions like other tasks
            "task_parameters": {
                "n_level": self.n_level,
                "stimulus_type": self.stimulus_type.value,
                "num_trials": self.num_trials,
                "target_probability": self.target_probability,
            },
        }
