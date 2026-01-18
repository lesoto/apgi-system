"""
Stroop Task

The Stroop task is a classic cognitive psychology paradigm that demonstrates interference in
reaction time when participants are asked to name the color of printed words while ignoring
the word meaning itself.

Key findings:
- Participants take longer to name the color of incongruent words (e.g., "RED" printed in blue)
- The interference effect demonstrates automatic reading processes
- Executive function is required to suppress the automatic response
- Prefrontal cortex activation is observed during incongruent trials

This task tests how the APGI system handles:
- Cognitive conflict and interference resolution
- Executive control and attentional selection
- Automatic vs. controlled processing
- Response inhibition and cognitive flexibility

References:
- Stroop, J. R. (1935). Studies of interference in serial verbal reactions.
  Journal of Experimental Psychology, 18(6), 643-662.
- MacLeod, C. M. (1991). Half a century of research on the Stroop effect:
  An integrative review. Psychological Bulletin, 109(2), 163-203.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import time


class TrialType(Enum):
    """Types of trials in the Stroop task."""

    CONGRUENT = "congruent"  # Word meaning matches color (e.g., "RED" in red)
    INCONGRUENT = "incongruent"  # Word meaning mismatches color (e.g., "RED" in blue)
    NEUTRAL = "neutral"  # Non-color word in color (e.g., "CHAIR" in red)


class Color(Enum):
    """Colors used in the Stroop task."""

    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"


@dataclass
class StroopTrial:
    """Represents a single trial in the Stroop task."""

    trial_type: TrialType
    word: str
    ink_color: Color
    correct_response: Color
    response_time: Optional[float] = None
    response: Optional[Color] = None
    is_correct: bool = False


@dataclass
class StroopResults:
    """Results from a Stroop task session."""

    total_trials: int
    congruent_trials: int
    incongruent_trials: int
    neutral_trials: int
    congruent_rt: float
    incongruent_rt: float
    neutral_rt: float
    congruent_accuracy: float
    incongruent_accuracy: float
    neutral_accuracy: float
    stroop_interference: float  # Incongruent RT - Congruent RT
    facilitation: float  # Neutral RT - Congruent RT


class StroopTask:
    """
    Implements the Stroop color-word interference task.

    The task presents color words printed in different colors and requires participants
    to identify the ink color while ignoring the word meaning.
    """

    def __init__(self, num_trials: int = 100, random_seed: Optional[int] = None):
        """
        Initialize the Stroop task.

        Args:
            num_trials: Total number of trials in the task
            random_seed: Seed for random number generation (for reproducibility)
        """
        self.num_trials = num_trials
        self.random_seed = random_seed

        if random_seed:
            random.seed(random_seed)
            np.random.seed(random_seed)

        # Task parameters
        self.colors = list(Color)
        self.color_words = {
            Color.RED: "RED",
            Color.BLUE: "BLUE",
            Color.GREEN: "GREEN",
            Color.YELLOW: "YELLOW",
        }
        self.neutral_words = ["CHAIR", "TABLE", "WINDOW", "DOOR", "BOOK", "PENCIL"]

        # Trial distribution (typical Stroop task ratios)
        self.congruent_ratio = 0.33
        self.incongruent_ratio = 0.33
        self.neutral_ratio = 0.34

        # State tracking
        self.current_trial = 0
        self.trials: List[StroopTrial] = []
        self.task_start_time: Optional[float] = None
        self.task_end_time: Optional[float] = None

        # Generate trials
        self._generate_trials()

    def _generate_trials(self) -> None:
        """Generate the sequence of trials for the task."""
        # Calculate number of trials per condition
        num_congruent = int(self.num_trials * self.congruent_ratio)
        num_incongruent = int(self.num_trials * self.incongruent_ratio)
        num_neutral = self.num_trials - num_congruent - num_incongruent

        # Generate trials for each condition
        trials = []

        # Congruent trials
        for _ in range(num_congruent):
            color = random.choice(self.colors)
            trial = StroopTrial(
                trial_type=TrialType.CONGRUENT,
                word=self.color_words[color],
                ink_color=color,
                correct_response=color,
            )
            trials.append(trial)

        # Incongruent trials
        for _ in range(num_incongruent):
            ink_color = random.choice(self.colors)
            # Choose a different color for the word
            word_colors = [c for c in self.colors if c != ink_color]
            word_color = random.choice(word_colors)

            trial = StroopTrial(
                trial_type=TrialType.INCONGRUENT,
                word=self.color_words[word_color],
                ink_color=ink_color,
                correct_response=ink_color,
            )
            trials.append(trial)

        # Neutral trials
        for _ in range(num_neutral):
            ink_color = random.choice(self.colors)
            word = random.choice(self.neutral_words)

            trial = StroopTrial(
                trial_type=TrialType.NEUTRAL,
                word=word,
                ink_color=ink_color,
                correct_response=ink_color,
            )
            trials.append(trial)

        # Shuffle trials
        random.shuffle(trials)
        self.trials = trials

    def start_task(self) -> None:
        """Start the Stroop task."""
        self.task_start_time = time.time()
        self.current_trial = 0

    def get_current_trial(self) -> Optional[StroopTrial]:
        """Get the current trial."""
        if self.current_trial < len(self.trials):
            return self.trials[self.current_trial]
        return None

    def record_response(self, response: Color, response_time: float) -> bool:
        """
        Record a response for the current trial.

        Args:
            response: The participant's response
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

    def get_results(self) -> StroopResults:
        """
        Calculate and return the task results.

        Returns:
            StroopResults object with performance metrics
        """
        if not self.is_complete():
            raise ValueError("Task is not complete")

        # Separate trials by condition
        congruent_trials = [t for t in self.trials if t.trial_type == TrialType.CONGRUENT]
        incongruent_trials = [t for t in self.trials if t.trial_type == TrialType.INCONGRUENT]
        neutral_trials = [t for t in self.trials if t.trial_type == TrialType.NEUTRAL]

        def calculate_metrics(trials: List[StroopTrial]) -> Tuple[float, float]:
            """Calculate mean RT and accuracy for a set of trials."""
            if not trials:
                return 0.0, 0.0

            rts = [t.response_time for t in trials if t.response_time is not None]
            accuracy = sum(1 for t in trials if t.is_correct) / len(trials)

            mean_rt = np.mean(rts) if rts else 0.0
            return mean_rt, accuracy

        # Calculate metrics for each condition
        congruent_rt, congruent_acc = calculate_metrics(congruent_trials)
        incongruent_rt, incongruent_acc = calculate_metrics(incongruent_trials)
        neutral_rt, neutral_acc = calculate_metrics(neutral_trials)

        # Calculate Stroop effects
        stroop_interference = incongruent_rt - congruent_rt
        facilitation = neutral_rt - congruent_rt

        return StroopResults(
            total_trials=len(self.trials),
            congruent_trials=len(congruent_trials),
            incongruent_trials=len(incongruent_trials),
            neutral_trials=len(neutral_trials),
            congruent_rt=congruent_rt,
            incongruent_rt=incongruent_rt,
            neutral_rt=neutral_rt,
            congruent_accuracy=congruent_acc,
            incongruent_accuracy=incongruent_acc,
            neutral_accuracy=neutral_acc,
            stroop_interference=stroop_interference,
            facilitation=facilitation,
        )

    def get_trial_summary(self) -> Dict[str, Any]:
        """Get a summary of all trials for analysis."""
        return {
            "total_trials": len(self.trials),
            "completed_trials": self.current_trial,
            "trials": [
                {
                    "trial_number": i + 1,
                    "trial_type": trial.trial_type.value,
                    "word": trial.word,
                    "ink_color": trial.ink_color.value,
                    "correct_response": trial.correct_response.value,
                    "response": trial.response.value if trial.response else None,
                    "response_time": trial.response_time,
                    "is_correct": trial.is_correct,
                }
                for i, trial in enumerate(self.trials)
            ],
        }

    def reset_task(self) -> None:
        """Reset the task to start over."""
        self.current_trial = 0
        self.task_start_time = None
        self.task_end_time = None

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
