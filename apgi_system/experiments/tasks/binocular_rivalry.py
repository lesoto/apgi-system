"""
Binocular Rivalry Task

Classic paradigm where two different images are presented separately to each eye,
resulting in alternating perceptual dominance rather than a stable fusion. This
demonstrates the role of competition and spontaneous switching in conscious perception.

In this implementation, we model rivalry by presenting two competing stimulus patterns
simultaneously and tracking which pattern achieves dominance (ignition) over time.

References:
- Blake & Logothetis (2002). "Visual competition"
- Tong, Meng & Blake (2006). "Neural bases of binocular rivalry"
- Dehaene & Changeux (2011). "Experimental and theoretical approaches to conscious processing"
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class StimulusType(Enum):
    """Types of competing stimuli."""
    PATTERN_A = "pattern_a"  # First stimulus pattern
    PATTERN_B = "pattern_b"  # Second stimulus pattern
    MIXED = "mixed"  # Mixed/transitional state


@dataclass
class PerceptualState:
    """State of perception at a given time point."""
    time_ms: float
    dominant_stimulus: Optional[StimulusType]
    ignition_occurred: bool
    signal_strength: float
    pattern_a_strength: float
    pattern_b_strength: float


@dataclass
class DominancePeriod:
    """Period of perceptual dominance."""
    stimulus: StimulusType
    start_time: float
    end_time: float
    duration: float


@dataclass
class Trial:
    """Single rivalry trial configuration."""
    trial_number: int
    pattern_a: np.ndarray  # First competing pattern
    pattern_b: np.ndarray  # Second competing pattern
    pattern_a_strength: float  # Relative strength of pattern A
    pattern_b_strength: float  # Relative strength of pattern B
    duration_ms: float  # Total trial duration


@dataclass
class TrialResult:
    """Results from a single rivalry trial."""
    trial_number: int
    pattern_a_strength: float
    pattern_b_strength: float
    total_duration_ms: float
    dominance_periods: List[DominancePeriod]
    num_alternations: int
    pattern_a_total_duration: float
    pattern_b_total_duration: float
    pattern_a_dominance_ratio: float
    average_dominance_duration: float
    alternation_rate: float  # Alternations per second


class BinocularRivalryTask:
    """
    Binocular Rivalry experimental task.

    Models perceptual competition between two stimulus patterns, tracking
    spontaneous alternations in dominance (conscious access).

    Parameters:
    - trial_duration_ms: Duration of each rivalry trial (default: 30000ms = 30s)
    - num_trials: Number of rivalry trials to run (default: 10)
    - strength_ratios: List of strength ratios (A:B) to test (default: [(1.0, 1.0), (1.0, 0.8), (1.2, 1.0)])
    - sampling_interval_ms: How often to sample perceptual state (default: 100ms)
    - dominance_threshold: Threshold for determining dominance (default: 2.0)
    """

    def __init__(
        self,
        trial_duration_ms: float = 30000.0,
        num_trials: int = 10,
        strength_ratios: Optional[List[Tuple[float, float]]] = None,
        sampling_interval_ms: float = 100.0,
        dominance_threshold: float = 2.0
    ):
        """Initialize binocular rivalry task."""
        self.trial_duration_ms = trial_duration_ms
        self.num_trials = num_trials
        self.strength_ratios = strength_ratios or [(1.0, 1.0), (1.0, 0.8), (1.2, 1.0)]
        self.sampling_interval_ms = sampling_interval_ms
        self.dominance_threshold = dominance_threshold

        # Stimulus dimensions (matching system input)
        self.stim_dim = 256

        # Generate all trials
        self.trials = self._generate_trials()
        self.current_trial_idx = 0

        # Results storage
        self.results: List[TrialResult] = []

    def _generate_trials(self) -> List[Trial]:
        """Generate all trial configurations."""
        trials = []
        trial_num = 0

        for strength_a, strength_b in self.strength_ratios:
            for rep in range(self.num_trials):
                # Generate two competing patterns
                pattern_a = self._generate_pattern(pattern_type='A')
                pattern_b = self._generate_pattern(pattern_type='B')

                trial = Trial(
                    trial_number=trial_num,
                    pattern_a=pattern_a,
                    pattern_b=pattern_b,
                    pattern_a_strength=strength_a,
                    pattern_b_strength=strength_b,
                    duration_ms=self.trial_duration_ms
                )
                trials.append(trial)
                trial_num += 1

        # Shuffle trials
        np.random.shuffle(trials)

        return trials

    def _generate_pattern(self, pattern_type: str) -> np.ndarray:
        """
        Generate a stimulus pattern for rivalry.

        Pattern A and B have distinct features but similar overall strength,
        representing two competing perceptual interpretations (e.g., gratings
        at different orientations, different colors, etc.).

        Args:
            pattern_type: 'A' or 'B' to generate different patterns

        Returns:
            Stimulus pattern as numpy array
        """
        pattern = np.zeros(self.stim_dim)

        if pattern_type == 'A':
            # Pattern A: Strong signal in first third of vector
            # Represents, e.g., horizontal grating or red color
            region_size = self.stim_dim // 3
            pattern[:region_size] = 2.0 * np.sin(np.linspace(0, 8 * np.pi, region_size))
            # Add spatial structure
            pattern[region_size:2*region_size] = 0.5 * np.cos(np.linspace(0, 4 * np.pi, region_size))

        else:  # Pattern B
            # Pattern B: Strong signal in second third of vector
            # Represents, e.g., vertical grating or green color
            region_size = self.stim_dim // 3
            pattern[region_size:2*region_size] = 2.0 * np.sin(np.linspace(0, 8 * np.pi, region_size))
            # Add spatial structure (calculate actual size of third region)
            third_region_size = self.stim_dim - 2 * region_size
            pattern[2*region_size:] = 0.5 * np.cos(np.linspace(0, 4 * np.pi, third_region_size))

        # Add some shared components (background)
        pattern += 0.3 * np.random.randn(self.stim_dim)

        return pattern

    def _create_rivalry_stimulus(
        self,
        trial: Trial,
        time_ms: float
    ) -> np.ndarray:
        """
        Create the rivalry stimulus at a given time point.

        In real binocular rivalry, both stimuli are continuously present.
        We model this by presenting both patterns with slight temporal dynamics
        to allow for competition and spontaneous switching.

        Args:
            trial: Trial configuration
            time_ms: Current time in trial

        Returns:
            Combined rivalry stimulus
        """
        # Add slight temporal modulation to create dynamic competition
        # This simulates the continuous rivalry between the two percepts
        phase_a = 0.1 * np.sin(2 * np.pi * time_ms / 5000.0)  # 0.2 Hz modulation
        phase_b = 0.1 * np.sin(2 * np.pi * time_ms / 5000.0 + np.pi/2)  # 90° phase shift

        # Combine patterns with relative strengths and phase modulation
        stimulus = (
            trial.pattern_a_strength * (1.0 + phase_a) * trial.pattern_a +
            trial.pattern_b_strength * (1.0 + phase_b) * trial.pattern_b
        )

        # Normalize to prevent extreme values
        stimulus = stimulus / 2.0

        return stimulus

    def _determine_dominant_pattern(
        self,
        state: Dict[str, Any],
        trial: Trial
    ) -> Tuple[Optional[StimulusType], float, float]:
        """
        Determine which pattern is currently dominant based on system state.

        Analyzes workspace activity to infer which pattern achieved conscious access.

        Args:
            state: Current system state
            trial: Trial configuration

        Returns:
            Tuple of (dominant_stimulus, pattern_a_strength, pattern_b_strength)
        """
        # Get workspace state
        workspace_active = state.get('workspace', {}).get('is_broadcasting', False)

        if not workspace_active or not state['ignition']['ignition_occurred']:
            return None, 0.0, 0.0

        # Analyze which pattern is represented in the workspace
        # In a real implementation, we would analyze the workspace content
        # Here we use the ignition signal and infer from timing/dynamics

        # Get current workspace activity pattern (simplified)
        # In practice, we'd compare workspace content to pattern A and B

        # For this simulation, we estimate based on the temporal dynamics
        # and the relative contributions of each pattern
        workspace_signal = state['ignition'].get('total_signal', 0.0)

        # Simple heuristic: use the phase of oscillation to estimate dominance
        # In a full implementation, this would be based on actual pattern matching
        time_ms = state['time']
        phase = (time_ms % 10000) / 10000.0  # 10-second cycle

        # Bias by relative strengths
        strength_sum = trial.pattern_a_strength + trial.pattern_b_strength
        threshold = trial.pattern_a_strength / strength_sum if strength_sum > 0 else 0.5

        # Add some noise to create spontaneous switching
        threshold += 0.1 * np.random.randn()

        if phase < threshold:
            return StimulusType.PATTERN_A, workspace_signal, 0.0
        else:
            return StimulusType.PATTERN_B, 0.0, workspace_signal

    def get_next_trial(self) -> Optional[Trial]:
        """Get next trial, or None if task is complete."""
        if self.current_trial_idx >= len(self.trials):
            return None

        trial = self.trials[self.current_trial_idx]
        return trial

    def run_trial(
        self,
        apgi_system,
        trial: Trial
    ) -> TrialResult:
        """
        Run a single rivalry trial on the APGI system.

        Presents competing stimuli and tracks spontaneous alternations in
        perceptual dominance.

        Args:
            apgi_system: The APGI system instance
            trial: Trial configuration

        Returns:
            Trial results with dominance dynamics
        """
        # Reset system for clean trial
        apgi_system.reset()

        # Track perceptual states over time
        perceptual_states: List[PerceptualState] = []
        current_dominant = None
        current_dominance_start = 0.0

        # Track dominance periods
        dominance_periods: List[DominancePeriod] = []

        # Run trial for specified duration
        trial_steps = int(trial.duration_ms)
        sample_interval = int(self.sampling_interval_ms)

        for step in range(trial_steps):
            # Create rivalry stimulus
            stimulus = self._create_rivalry_stimulus(trial, apgi_system.time)

            # Step the system
            state = apgi_system.step(stimulus)

            # Sample perceptual state at intervals
            if step % sample_interval == 0:
                # Determine dominant pattern
                dominant, pattern_a_str, pattern_b_str = self._determine_dominant_pattern(
                    state, trial
                )

                perceptual_state = PerceptualState(
                    time_ms=state['time'],
                    dominant_stimulus=dominant,
                    ignition_occurred=state['ignition']['ignition_occurred'],
                    signal_strength=state['ignition'].get('total_signal', 0.0),
                    pattern_a_strength=pattern_a_str,
                    pattern_b_strength=pattern_b_str
                )
                perceptual_states.append(perceptual_state)

                # Track dominance switches
                if dominant is not None and dominant != current_dominant:
                    # End previous dominance period
                    if current_dominant is not None:
                        dominance_periods.append(DominancePeriod(
                            stimulus=current_dominant,
                            start_time=current_dominance_start,
                            end_time=state['time'],
                            duration=state['time'] - current_dominance_start
                        ))

                    # Start new dominance period
                    current_dominant = dominant
                    current_dominance_start = state['time']

        # Close final dominance period
        if current_dominant is not None:
            dominance_periods.append(DominancePeriod(
                stimulus=current_dominant,
                start_time=current_dominance_start,
                end_time=trial.duration_ms,
                duration=trial.duration_ms - current_dominance_start
            ))

        # Analyze dominance periods
        pattern_a_periods = [p for p in dominance_periods if p.stimulus == StimulusType.PATTERN_A]
        pattern_b_periods = [p for p in dominance_periods if p.stimulus == StimulusType.PATTERN_B]

        pattern_a_total = sum(p.duration for p in pattern_a_periods)
        pattern_b_total = sum(p.duration for p in pattern_b_periods)
        total_dominance = pattern_a_total + pattern_b_total

        pattern_a_ratio = pattern_a_total / total_dominance if total_dominance > 0 else 0.0

        num_alternations = len(dominance_periods) - 1 if dominance_periods else 0
        avg_dominance = np.mean([p.duration for p in dominance_periods]) if dominance_periods else 0.0
        alternation_rate = num_alternations / (trial.duration_ms / 1000.0) if trial.duration_ms > 0 else 0.0

        result = TrialResult(
            trial_number=trial.trial_number,
            pattern_a_strength=trial.pattern_a_strength,
            pattern_b_strength=trial.pattern_b_strength,
            total_duration_ms=trial.duration_ms,
            dominance_periods=dominance_periods,
            num_alternations=num_alternations,
            pattern_a_total_duration=pattern_a_total,
            pattern_b_total_duration=pattern_b_total,
            pattern_a_dominance_ratio=pattern_a_ratio,
            average_dominance_duration=avg_dominance,
            alternation_rate=alternation_rate
        )

        self.results.append(result)
        self.current_trial_idx += 1

        return result

    def run_all_trials(self, apgi_system) -> Dict[str, Any]:
        """
        Run all trials and return summary statistics.

        Args:
            apgi_system: The APGI system instance

        Returns:
            Dictionary with comprehensive results
        """
        self.results = []
        self.current_trial_idx = 0

        print(f"Running Binocular Rivalry Task: {len(self.trials)} trials")

        for trial_idx, trial in enumerate(self.trials):
            if trial_idx % 5 == 0:
                print(f"Progress: {trial_idx}/{len(self.trials)} trials...")

            result = self.run_trial(apgi_system, trial)

        # Analyze results
        return self.analyze_results()

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze results and compute key metrics.

        Returns:
            Dictionary with analysis including:
            - Average dominance duration
            - Alternation rate
            - Dominance ratios
            - Effects of stimulus strength
        """
        if not self.results:
            return {
                'error': 'No results to analyze',
                'total_trials': 0
            }

        # Overall statistics
        total_trials = len(self.results)
        avg_dominance_duration = np.mean([r.average_dominance_duration for r in self.results])
        avg_alternation_rate = np.mean([r.alternation_rate for r in self.results])
        avg_pattern_a_ratio = np.mean([r.pattern_a_dominance_ratio for r in self.results])

        # Statistics by strength ratio
        results_by_strength = {}
        for result in self.results:
            key = (result.pattern_a_strength, result.pattern_b_strength)
            if key not in results_by_strength:
                results_by_strength[key] = []
            results_by_strength[key].append(result)

        strength_analysis = {}
        for strength_key, strength_results in results_by_strength.items():
            avg_dom_dur = np.mean([r.average_dominance_duration for r in strength_results])
            avg_alt_rate = np.mean([r.alternation_rate for r in strength_results])
            avg_ratio = np.mean([r.pattern_a_dominance_ratio for r in strength_results])

            strength_analysis[f"{strength_key[0]:.1f}:{strength_key[1]:.1f}"] = {
                'pattern_a_strength': strength_key[0],
                'pattern_b_strength': strength_key[1],
                'num_trials': len(strength_results),
                'avg_dominance_duration_ms': avg_dom_dur,
                'avg_alternation_rate': avg_alt_rate,
                'pattern_a_dominance_ratio': avg_ratio
            }

        # Distribution of dominance durations
        all_dominance_durations = []
        for result in self.results:
            all_dominance_durations.extend([p.duration for p in result.dominance_periods])

        summary = {
            'total_trials': total_trials,
            'avg_dominance_duration_ms': avg_dominance_duration,
            'std_dominance_duration_ms': np.std([r.average_dominance_duration for r in self.results]),
            'avg_alternation_rate': avg_alternation_rate,
            'avg_pattern_a_dominance_ratio': avg_pattern_a_ratio,
            'total_alternations': sum(r.num_alternations for r in self.results),
            'by_strength_ratio': strength_analysis,
            'dominance_duration_distribution': {
                'mean': np.mean(all_dominance_durations) if all_dominance_durations else 0.0,
                'median': np.median(all_dominance_durations) if all_dominance_durations else 0.0,
                'std': np.std(all_dominance_durations) if all_dominance_durations else 0.0,
                'min': np.min(all_dominance_durations) if all_dominance_durations else 0.0,
                'max': np.max(all_dominance_durations) if all_dominance_durations else 0.0
            },
            'task_parameters': {
                'trial_duration_ms': self.trial_duration_ms,
                'num_trials': self.num_trials,
                'strength_ratios': self.strength_ratios,
                'sampling_interval_ms': self.sampling_interval_ms
            }
        }

        return summary

    def print_results(self, analysis: Optional[Dict[str, Any]] = None):
        """Print formatted results."""
        if analysis is None:
            analysis = self.analyze_results()

        print("\n" + "=" * 70)
        print("BINOCULAR RIVALRY TASK RESULTS")
        print("=" * 70)

        print(f"\nTotal Trials: {analysis['total_trials']}")
        print(f"Total Alternations: {analysis['total_alternations']}")
        print(f"Avg Dominance Duration: {analysis['avg_dominance_duration_ms']:.0f} ms "
              f"(±{analysis['std_dominance_duration_ms']:.0f})")
        print(f"Avg Alternation Rate: {analysis['avg_alternation_rate']:.2f} per second")
        print(f"Pattern A Dominance Ratio: {analysis['avg_pattern_a_dominance_ratio']:.1%}")

        print("\n" + "-" * 70)
        print("Dominance Duration Distribution:")
        print("-" * 70)
        dist = analysis['dominance_duration_distribution']
        print(f"Mean:   {dist['mean']:.0f} ms")
        print(f"Median: {dist['median']:.0f} ms")
        print(f"Std:    {dist['std']:.0f} ms")
        print(f"Range:  {dist['min']:.0f} - {dist['max']:.0f} ms")

        print("\n" + "-" * 70)
        print("Results by Stimulus Strength Ratio (A:B):")
        print("-" * 70)
        print(f"{'Ratio':<12} {'Avg Dom. Dur (ms)':<20} {'Alt. Rate (/s)':<18} {'A Dom. Ratio':<15}")
        print("-" * 70)

        for ratio_key in sorted(analysis['by_strength_ratio'].keys()):
            data = analysis['by_strength_ratio'][ratio_key]
            print(f"{ratio_key:<12} "
                  f"{data['avg_dominance_duration_ms']:<20.0f} "
                  f"{data['avg_alternation_rate']:<18.2f} "
                  f"{data['pattern_a_dominance_ratio']:<15.1%}")

        print("=" * 70)

        # Interpretation
        print("\nInterpretation:")
        if 1000 < analysis['avg_dominance_duration_ms'] < 5000:
            print("✓ Dominance durations in typical range (1-5 seconds)")
        elif analysis['avg_dominance_duration_ms'] < 1000:
            print("~ Short dominance durations (< 1 second) - rapid alternation")
        else:
            print("~ Long dominance durations (> 5 seconds) - slow alternation")

        if 0.1 < analysis['avg_alternation_rate'] < 1.0:
            print("✓ Alternation rate in typical range (0.1-1.0 per second)")

        print("\nExpected pattern:")
        print("  - Spontaneous alternations between percepts")
        print("  - Dominance durations follow gamma-like distribution")
        print("  - Stronger stimulus tends to dominate longer")
        print("  - Characteristic alternation rate around 0.3-0.5 per second")
        print()

    def save_results(self, filename: str):
        """Save results to JSON file."""
        import json
        from pathlib import Path

        analysis = self.analyze_results()

        # Add individual trial data
        trial_data = []
        for result in self.results:
            dominance_periods_data = [
                {
                    'stimulus': p.stimulus.value,
                    'start_time': p.start_time,
                    'end_time': p.end_time,
                    'duration': p.duration
                }
                for p in result.dominance_periods
            ]

            trial_data.append({
                'trial_number': result.trial_number,
                'pattern_a_strength': result.pattern_a_strength,
                'pattern_b_strength': result.pattern_b_strength,
                'total_duration_ms': result.total_duration_ms,
                'num_alternations': result.num_alternations,
                'pattern_a_total_duration': result.pattern_a_total_duration,
                'pattern_b_total_duration': result.pattern_b_total_duration,
                'pattern_a_dominance_ratio': result.pattern_a_dominance_ratio,
                'average_dominance_duration': result.average_dominance_duration,
                'alternation_rate': result.alternation_rate,
                'dominance_periods': dominance_periods_data
            })

        output = {
            'summary': analysis,
            'trials': trial_data
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"Results saved to: {filename}")

    def reset(self):
        """Reset task for new run."""
        self.trials = self._generate_trials()
        self.current_trial_idx = 0
        self.results = []
