"""
Iowa Gambling Task (IGT)

The Iowa Gambling Task is a neuropsychological paradigm that assesses decision-making
under uncertainty and ambiguity. Participants choose from four decks of cards, receiving
rewards and occasional penalties. Two decks are advantageous in the long term (low
immediate rewards but smaller penalties), while two are disadvantageous (high immediate
rewards but larger penalties).

Key findings:
- Healthy participants learn to prefer advantageous decks over time
- Patients with ventromedial prefrontal cortex damage show impaired learning
- Somatic markers (physiological responses) guide decision-making
- Performance reflects the balance between immediate rewards and long-term outcomes

This task tests how the APGI system handles:
- Decision-making under uncertainty
- Learning from reward and punishment
- Interoceptive signals (somatic markers) guiding choices
- Integration of short-term rewards with long-term consequences

References:
- Bechara, A., Damasio, A. R., Damasio, H., & Anderson, S. W. (1994). Insensitivity to
  future consequences following damage to human prefrontal cortex. Cognition, 50(1-3), 7-15.
- Bechara, A., Damasio, H., Tranel, D., & Damasio, A. R. (1997). Deciding advantageously
  before knowing the advantageous strategy. Science, 275(5304), 1293-1295.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class DeckType(Enum):
    """Types of decks in the Iowa Gambling Task."""

    A = "A"  # Bad deck: High reward, very high penalty (net -250 per 10 cards)
    B = "B"  # Bad deck: High reward, very high penalty (net -250 per 10 cards)
    C = "C"  # Good deck: Low reward, low penalty (net +250 per 10 cards)
    D = "D"  # Good deck: Low reward, low penalty (net +250 per 10 cards)


# Standard IGT reward/penalty schedules
DECK_SCHEDULES = {
    DeckType.A: {
        "reward": 100,  # Every card gives $100
        "penalty_frequency": 0.5,  # 50% of cards have penalty
        "penalties": [150, 200, 250, 300, 350],  # Variable penalties
        "net_per_10": -250,  # Net loss over 10 cards
    },
    DeckType.B: {
        "reward": 100,  # Every card gives $100
        "penalty_frequency": 0.1,  # 10% of cards have penalty
        "penalties": [1250],  # One large penalty
        "net_per_10": -250,  # Net loss over 10 cards
    },
    DeckType.C: {
        "reward": 50,  # Every card gives $50
        "penalty_frequency": 0.5,  # 50% of cards have penalty
        "penalties": [25, 50, 75],  # Small penalties
        "net_per_10": 250,  # Net gain over 10 cards
    },
    DeckType.D: {
        "reward": 50,  # Every card gives $50
        "penalty_frequency": 0.1,  # 10% of cards have penalty
        "penalties": [250],  # Occasional penalty
        "net_per_10": 250,  # Net gain over 10 cards
    },
}


@dataclass
class Trial:
    """Configuration for a single Iowa Gambling Task trial."""

    trial_number: int
    deck_choice: DeckType
    deck_stimulus: np.ndarray  # Visual representation of chosen deck
    reward: int
    penalty: int
    net_outcome: int


@dataclass
class TrialResult:
    """Results from a single IGT trial."""

    trial_number: int
    deck_choice: DeckType
    reward: int
    penalty: int
    net_outcome: int
    running_total: int
    ignition_occurred: bool
    ignition_strength: float
    somatic_marker_strength: float  # Interoceptive signal strength
    decision_time: float
    anticipatory_response: float  # Pre-choice bodily response


class IowaGamblingTask:
    """
    Iowa Gambling Task experimental paradigm.

    Tests decision-making under uncertainty by presenting participants with
    four decks of cards. Each choice results in immediate reward and sometimes
    a penalty. The task measures learning to prefer advantageous decks.

    Parameters
    ----------
    num_trials : int, default=100
        Total number of card selections
    initial_balance : int, default=2000
        Starting money amount (in dollars)
    deck_stimulus_strength : float, default=1.5
        Strength of deck visual stimuli
    outcome_stimulus_strength : float, default=2.0
        Strength of outcome (reward/penalty) stimuli
    interoceptive_gain : float, default=1.0
        Multiplier for interoceptive signals (somatic markers)
    deck_selection_strategy : str, default='balanced'
        How trials are generated: 'balanced' (equal deck exposure),
        'participant_choice' (simulated learning), or 'random'
    """

    def __init__(
        self,
        num_trials: int = 100,
        initial_balance: int = 2000,
        deck_stimulus_strength: float = 1.5,
        outcome_stimulus_strength: float = 2.0,
        interoceptive_gain: float = 1.0,
        deck_selection_strategy: str = "balanced",
    ):
        """Initialize Iowa Gambling Task."""
        self.num_trials = num_trials
        self.initial_balance = initial_balance
        self.deck_stimulus_strength = deck_stimulus_strength
        self.outcome_stimulus_strength = outcome_stimulus_strength
        self.interoceptive_gain = interoceptive_gain
        self.deck_selection_strategy = deck_selection_strategy

        # Stimulus dimensions
        self.stim_dim = 256

        # Task state
        self.current_balance = initial_balance
        self.deck_frequencies = {deck: 0 for deck in DeckType}

        # Generate deck penalty schedules
        self._initialize_penalty_schedules()

        # Generate all trials
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results: List[TrialResult] = []

        print(f"Iowa Gambling Task initialized:")
        print(f"  - Total trials: {self.num_trials}")
        print(f"  - Initial balance: ${self.initial_balance}")
        print(f"  - Selection strategy: {self.deck_selection_strategy}")
        print(f"  - Deck A & B (Bad): High reward, larger penalties (net -$250/10 cards)")
        print(f"  - Deck C & D (Good): Low reward, smaller penalties (net +$250/10 cards)")

    def _initialize_penalty_schedules(self):
        """Initialize randomized penalty schedules for each deck."""
        np.random.seed(42)  # For reproducibility
        self.penalty_schedules = {}

        for deck_type in DeckType:
            schedule = DECK_SCHEDULES[deck_type]
            # Create a schedule for many cards
            max_cards = 200
            penalties = []

            for i in range(max_cards):
                if np.random.random() < schedule["penalty_frequency"]:
                    # Select a random penalty from the list
                    penalty = np.random.choice(schedule["penalties"])
                    penalties.append(penalty)
                else:
                    penalties.append(0)

            self.penalty_schedules[deck_type] = penalties

    def _generate_trials(self) -> List[Trial]:
        """Generate all trial configurations."""
        trials = []

        if self.deck_selection_strategy == "balanced":
            # Equal exposure to all decks
            decks_per_type = self.num_trials // 4
            deck_sequence = (
                [DeckType.A] * decks_per_type
                + [DeckType.B] * decks_per_type
                + [DeckType.C] * decks_per_type
                + [DeckType.D] * decks_per_type
            )
            # Add remaining trials if num_trials not divisible by 4
            remaining = self.num_trials - len(deck_sequence)
            for i in range(remaining):
                deck_sequence.append(list(DeckType)[i % 4])

            # Randomize order
            np.random.shuffle(deck_sequence)

        elif self.deck_selection_strategy == "random":
            # Completely random deck selection
            deck_sequence = [np.random.choice(list(DeckType)) for _ in range(self.num_trials)]

        else:  # 'participant_choice' or other
            # Simulate gradual shift from bad to good decks (learning)
            deck_sequence = []
            for i in range(self.num_trials):
                # Probability of choosing good decks increases over time
                p_good = min(0.8, 0.2 + (i / self.num_trials) * 0.6)

                if np.random.random() < p_good:
                    deck_sequence.append(np.random.choice([DeckType.C, DeckType.D]))
                else:
                    deck_sequence.append(np.random.choice([DeckType.A, DeckType.B]))

        # Create trials with outcomes
        for trial_num, deck_choice in enumerate(deck_sequence):
            schedule = DECK_SCHEDULES[deck_choice]

            # Get reward (always given)
            reward = schedule["reward"]

            # Get penalty from pre-generated schedule
            deck_card_num = self.deck_frequencies[deck_choice]
            penalty = self.penalty_schedules[deck_choice][
                deck_card_num % len(self.penalty_schedules[deck_choice])
            ]

            # Net outcome
            net_outcome = reward - penalty

            # Generate deck stimulus (unique pattern for each deck)
            deck_stimulus = self._generate_deck_stimulus(deck_choice)

            trial = Trial(
                trial_number=trial_num,
                deck_choice=deck_choice,
                deck_stimulus=deck_stimulus,
                reward=reward,
                penalty=penalty,
                net_outcome=net_outcome,
            )
            trials.append(trial)

            # Update deck frequency
            self.deck_frequencies[deck_choice] += 1

        return trials

    def _generate_deck_stimulus(self, deck_type: DeckType) -> np.ndarray:
        """
        Generate visual stimulus for a deck.

        Each deck has a unique visual pattern to make it distinguishable.
        """
        stimulus = np.zeros(self.stim_dim)

        # Deck-specific frequency signatures
        if deck_type == DeckType.A:
            # Deck A: Low frequency pattern
            freq = 2 * np.pi * 2
            stimulus[: self.stim_dim // 2] = self.deck_stimulus_strength * np.sin(
                np.linspace(0, freq, self.stim_dim // 2)
            )
        elif deck_type == DeckType.B:
            # Deck B: Mid-low frequency pattern
            freq = 2 * np.pi * 4
            stimulus[: self.stim_dim // 2] = self.deck_stimulus_strength * np.sin(
                np.linspace(0, freq, self.stim_dim // 2)
            )
        elif deck_type == DeckType.C:
            # Deck C: Mid-high frequency pattern
            freq = 2 * np.pi * 6
            stimulus[self.stim_dim // 4 : 3 * self.stim_dim // 4] = (
                self.deck_stimulus_strength * np.sin(np.linspace(0, freq, self.stim_dim // 2))
            )
        else:  # DeckType.D
            # Deck D: High frequency pattern
            freq = 2 * np.pi * 8
            stimulus[self.stim_dim // 4 : 3 * self.stim_dim // 4] = (
                self.deck_stimulus_strength * np.sin(np.linspace(0, freq, self.stim_dim // 2))
            )

        # Add small noise for variability
        stimulus += 0.1 * np.random.randn(self.stim_dim)

        return stimulus

    def _generate_outcome_stimulus(self, net_outcome: int) -> np.ndarray:
        """
        Generate interoceptive stimulus representing reward/penalty outcome.

        Positive outcomes create pleasant bodily sensations, negative outcomes
        create unpleasant ones. This simulates somatic markers.
        """
        stimulus = np.zeros(self.stim_dim)

        # Normalize outcome to stimulus strength
        # Typical outcomes range from -1150 (worst) to +100 (best)
        normalized_outcome = np.clip(net_outcome / 500.0, -3.0, 1.0)

        if net_outcome > 0:
            # Positive outcome: Pleasant, regular pattern
            freq = 2 * np.pi * 5
            amplitude = self.outcome_stimulus_strength * (normalized_outcome)
            stimulus += amplitude * np.sin(np.linspace(0, freq, self.stim_dim))
        else:
            # Negative outcome: Unpleasant, irregular pattern
            freq = 2 * np.pi * 10
            amplitude = self.outcome_stimulus_strength * abs(normalized_outcome)
            stimulus += amplitude * np.sin(np.linspace(0, freq, self.stim_dim))
            # Add dissonance for negative outcomes
            stimulus += 0.5 * amplitude * np.random.randn(self.stim_dim)

        # Apply interoceptive gain
        stimulus *= self.interoceptive_gain

        return stimulus

    def run_trial(self, apgi_system, trial: Trial) -> TrialResult:
        """
        Run a single Iowa Gambling Task trial.

        Timeline:
        1. Reset system to neutral state
        2. Present deck stimulus (deck selection phase)
        3. Monitor anticipatory responses (somatic markers)
        4. Present outcome stimulus (reward/penalty feedback)
        5. Monitor for ignition and interoceptive responses

        Parameters
        ----------
        apgi_system : APGISystem
            The APGI system instance to run the trial on
        trial : Trial
            Trial configuration

        Returns
        -------
        TrialResult
            Results from the trial including outcomes and physiological responses
        """
        apgi_system.reset()

        # Tracking variables
        ignition_occurred = False
        max_ignition_strength = 0.0
        anticipatory_response = 0.0
        decision_start_time = apgi_system.time

        # Phase 1: Deck presentation (decision phase)
        # Present deck stimulus for 500ms (simulating looking at the deck)
        deck_presentation_steps = 500

        for step in range(deck_presentation_steps):
            state = apgi_system.step(trial.deck_stimulus)

            # Monitor anticipatory somatic markers (bodily responses before outcome)
            # These emerge from interoceptive precision signals
            if "body" in state and "prediction_error" in state["body"]:
                # Use prediction error magnitude as somatic marker
                intero_signal = np.linalg.norm(state["body"]["prediction_error"])
                if intero_signal > anticipatory_response:
                    anticipatory_response = intero_signal
            elif "interoception" in state:
                intero_signal = state["interoception"].get("interoceptive_precision", 0.0)
                if intero_signal > anticipatory_response:
                    anticipatory_response = intero_signal

            # Check for ignition during deck viewing
            if state["ignition"]["ignition_occurred"]:
                ignition_occurred = True
                ignition_strength = state["ignition"]["total_signal"]
                if ignition_strength > max_ignition_strength:
                    max_ignition_strength = ignition_strength

        # Record decision time
        decision_time = apgi_system.time - decision_start_time

        # Phase 2: Brief pause (card selection)
        blank_steps = 200
        blank = 0.05 * np.random.randn(self.stim_dim)
        for step in range(blank_steps):
            apgi_system.step(blank)

        # Phase 3: Outcome presentation (reward/penalty feedback)
        # Present outcome stimulus representing the somatic response to gain/loss
        outcome_stimulus = self._generate_outcome_stimulus(trial.net_outcome)
        outcome_steps = 1000  # 1 second to experience outcome

        somatic_marker_strength = 0.0

        for step in range(outcome_steps):
            state = apgi_system.step(outcome_stimulus)

            # Monitor somatic marker (interoceptive response to outcome)
            if "body" in state and "prediction_error" in state["body"]:
                # Use prediction error magnitude as somatic marker
                intero_signal = np.linalg.norm(state["body"]["prediction_error"])
                if intero_signal > somatic_marker_strength:
                    somatic_marker_strength = intero_signal
            elif "interoception" in state:
                intero_signal = state["interoception"].get("interoceptive_precision", 0.0)
                if intero_signal > somatic_marker_strength:
                    somatic_marker_strength = intero_signal

            # Check for ignition during outcome processing
            if state["ignition"]["ignition_occurred"]:
                ignition_occurred = True
                ignition_strength = state["ignition"]["total_signal"]
                if ignition_strength > max_ignition_strength:
                    max_ignition_strength = ignition_strength

        # Update running balance
        self.current_balance += trial.net_outcome

        # Create result
        result = TrialResult(
            trial_number=trial.trial_number,
            deck_choice=trial.deck_choice,
            reward=trial.reward,
            penalty=trial.penalty,
            net_outcome=trial.net_outcome,
            running_total=self.current_balance,
            ignition_occurred=ignition_occurred,
            ignition_strength=max_ignition_strength,
            somatic_marker_strength=somatic_marker_strength,
            decision_time=decision_time,
            anticipatory_response=anticipatory_response,
        )

        self.results.append(result)
        self.current_trial_idx += 1
        return result

    def run_all_trials(self, apgi_system) -> Dict[str, Any]:
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
        self.current_balance = self.initial_balance

        print(f"\n{'='*70}")
        print(f"Running Iowa Gambling Task: {len(self.trials)} trials")
        print(f"{'='*70}\n")

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
            - Overall performance metrics
            - Results by deck type
            - Learning curve analysis (by blocks)
            - Somatic marker analysis
        """
        if not self.results:
            return {"error": "No results to analyze", "total_trials": 0}

        # Overall statistics
        total_earnings = self.current_balance - self.initial_balance
        good_deck_choices = sum(
            1 for r in self.results if r.deck_choice in [DeckType.C, DeckType.D]
        )
        bad_deck_choices = sum(1 for r in self.results if r.deck_choice in [DeckType.A, DeckType.B])
        advantageous_ratio = good_deck_choices / len(self.results) if self.results else 0.0

        # Analyze by deck
        deck_analysis = {}
        for deck_type in DeckType:
            deck_results = [r for r in self.results if r.deck_choice == deck_type]

            if deck_results:
                avg_outcome = np.mean([r.net_outcome for r in deck_results])
                total_selections = len(deck_results)
                avg_somatic = np.mean([r.somatic_marker_strength for r in deck_results])
                avg_anticipatory = np.mean([r.anticipatory_response for r in deck_results])
            else:
                avg_outcome = 0.0
                total_selections = 0
                avg_somatic = 0.0
                avg_anticipatory = 0.0

            deck_analysis[deck_type.value] = {
                "selections": total_selections,
                "selection_percentage": (total_selections / len(self.results)) * 100,
                "avg_net_outcome": float(avg_outcome),
                "avg_somatic_marker": float(avg_somatic),
                "avg_anticipatory_response": float(avg_anticipatory),
            }

        # Block analysis (learning over time)
        # Divide trials into 5 blocks of 20 trials each
        block_size = 20
        num_blocks = min(5, len(self.results) // block_size)
        block_analysis = []

        for block_idx in range(num_blocks):
            start_idx = block_idx * block_size
            end_idx = min(start_idx + block_size, len(self.results))
            block_results = self.results[start_idx:end_idx]

            good_choices = sum(
                1 for r in block_results if r.deck_choice in [DeckType.C, DeckType.D]
            )
            bad_choices = sum(1 for r in block_results if r.deck_choice in [DeckType.A, DeckType.B])
            net_score = good_choices - bad_choices  # Net advantageous choices

            block_earnings = sum(r.net_outcome for r in block_results)
            avg_somatic = np.mean([r.somatic_marker_strength for r in block_results])

            block_analysis.append(
                {
                    "block": block_idx + 1,
                    "trials": f"{start_idx+1}-{end_idx}",
                    "good_deck_choices": good_choices,
                    "bad_deck_choices": bad_choices,
                    "net_score": net_score,
                    "block_earnings": block_earnings,
                    "avg_somatic_marker": float(avg_somatic),
                    "good_deck_percentage": (good_choices / len(block_results)) * 100,
                }
            )

        # Somatic marker analysis
        # Check if somatic markers correlate with deck quality
        good_deck_somatic = (
            np.mean(
                [
                    r.somatic_marker_strength
                    for r in self.results
                    if r.deck_choice in [DeckType.C, DeckType.D]
                ]
            )
            if good_deck_choices > 0
            else 0.0
        )

        bad_deck_somatic = (
            np.mean(
                [
                    r.somatic_marker_strength
                    for r in self.results
                    if r.deck_choice in [DeckType.A, DeckType.B]
                ]
            )
            if bad_deck_choices > 0
            else 0.0
        )

        # Learning metrics
        # Compare first 20 vs last 20 trials
        if len(self.results) >= 40:
            first_20 = self.results[:20]
            last_20 = self.results[-20:]

            first_20_good = sum(1 for r in first_20 if r.deck_choice in [DeckType.C, DeckType.D])
            last_20_good = sum(1 for r in last_20 if r.deck_choice in [DeckType.C, DeckType.D])

            learning_improvement = last_20_good - first_20_good
        else:
            learning_improvement = 0

        return {
            "total_trials": len(self.results),
            "initial_balance": self.initial_balance,
            "final_balance": self.current_balance,
            "total_earnings": total_earnings,
            "good_deck_choices": good_deck_choices,
            "bad_deck_choices": bad_deck_choices,
            "advantageous_ratio": advantageous_ratio,
            "net_score": good_deck_choices - bad_deck_choices,
            "by_deck": deck_analysis,
            "by_block": block_analysis,
            "somatic_markers": {
                "good_decks_avg": float(good_deck_somatic),
                "bad_decks_avg": float(bad_deck_somatic),
                "differential": float(abs(good_deck_somatic - bad_deck_somatic)),
            },
            "learning_improvement": learning_improvement,
            "task_parameters": {
                "num_trials": self.num_trials,
                "initial_balance": self.initial_balance,
                "strategy": self.deck_selection_strategy,
            },
        }

    def print_results(self, analysis: Optional[Dict[str, Any]] = None):
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
        print("IOWA GAMBLING TASK RESULTS")
        print("=" * 80)
        print(f"\nTotal Trials: {analysis['total_trials']}")
        print(f"Initial Balance: ${analysis['initial_balance']}")
        print(f"Final Balance: ${analysis['final_balance']}")
        print(f"Total Earnings: ${analysis['total_earnings']}")
        print(f"\nDeck Choices:")
        print(
            f"  Good Decks (C & D): {analysis['good_deck_choices']} ({analysis['advantageous_ratio']:.1%})"
        )
        print(f"  Bad Decks (A & B): {analysis['bad_deck_choices']}")
        print(f"  Net Score: {analysis['net_score']} (good - bad)")

        print("\n" + "-" * 80)
        print("Performance by Deck:")
        print("-" * 80)
        print(
            f"{'Deck':<6} {'Type':<8} {'Selections':<12} {'%':<8} {'Avg Outcome':<14} {'Somatic Marker'}"
        )
        print("-" * 80)

        deck_types = {"A": "Bad", "B": "Bad", "C": "Good", "D": "Good"}
        for deck in ["A", "B", "C", "D"]:
            data = analysis["by_deck"][deck]
            print(
                f"{deck:<6} {deck_types[deck]:<8} "
                f"{data['selections']:<12} "
                f"{data['selection_percentage']:<8.1f} "
                f"${data['avg_net_outcome']:<13.1f} "
                f"{data['avg_somatic_marker']:.3f}"
            )

        print("\n" + "-" * 80)
        print("Learning Curve (by Block):")
        print("-" * 80)
        print(
            f"{'Block':<8} {'Trials':<12} {'Good':<8} {'Bad':<8} {'Net':<8} {'Earnings':<12} {'Good %'}"
        )
        print("-" * 80)

        for block in analysis["by_block"]:
            print(
                f"{block['block']:<8} "
                f"{block['trials']:<12} "
                f"{block['good_deck_choices']:<8} "
                f"{block['bad_deck_choices']:<8} "
                f"{block['net_score']:<8} "
                f"${block['block_earnings']:<11} "
                f"{block['good_deck_percentage']:.1f}%"
            )

        print("\n" + "-" * 80)
        print("Somatic Marker Analysis:")
        print("-" * 80)
        sm = analysis["somatic_markers"]
        print(f"  Good Decks Average: {sm['good_decks_avg']:.4f}")
        print(f"  Bad Decks Average: {sm['bad_decks_avg']:.4f}")
        print(f"  Differential: {sm['differential']:.4f}")

        print("\n" + "-" * 80)
        print(
            f"Learning Improvement: {analysis['learning_improvement']} more good deck choices in last 20 vs first 20"
        )
        print("-" * 80)

        print("\n" + "=" * 80)
        print("Interpretation:")
        print("  • Good performance: Net score > 10, advantageous ratio > 60%")
        print("  • Learning should show increasing good deck % across blocks")
        print("  • Somatic markers should differentiate between good/bad decks")
        print("  • Healthy participants typically achieve 60-70% good deck choices")
        print("=" * 80 + "\n")

    def save_results(self, filename: str):
        """
        Save results to JSON file.

        Parameters
        ----------
        filename : str
            Output filename (e.g., 'iowa_gambling_results.json')
        """
        import json
        from datetime import datetime

        analysis = self.analyze_results()

        # Helper function to convert numpy types to Python native types
        def convert_to_native(obj):
            """Convert numpy types to Python native types for JSON serialization."""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_native(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_native(item) for item in obj]
            return obj

        # Prepare detailed trial data
        trial_data = []
        for result in self.results:
            trial_data.append(
                {
                    "trial_number": int(result.trial_number),
                    "deck_choice": result.deck_choice.value,
                    "reward": int(result.reward),
                    "penalty": int(result.penalty),
                    "net_outcome": int(result.net_outcome),
                    "running_total": int(result.running_total),
                    "ignition_occurred": bool(result.ignition_occurred),
                    "ignition_strength": float(result.ignition_strength),
                    "somatic_marker_strength": float(result.somatic_marker_strength),
                    "decision_time": float(result.decision_time),
                    "anticipatory_response": float(result.anticipatory_response),
                }
            )

        # Compile full output
        output = {
            "experiment": "Iowa Gambling Task",
            "timestamp": datetime.now().isoformat(),
            "summary": convert_to_native(analysis),
            "trials": trial_data,
        }

        # Save to file
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to: {filename}")

    def reset(self):
        """Reset task for a new run."""
        self.current_balance = self.initial_balance
        self.deck_frequencies = {deck: 0 for deck in DeckType}
        self._initialize_penalty_schedules()
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results = []
        print("Task reset. Ready for new run.")
