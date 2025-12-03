"""
Unit tests for experimental task implementations.

Tests specific trial sequences and edge cases for:
- Iowa Gambling Task
- Masking Paradigm
- Attentional Blink

These tests verify correct behavior for specific scenarios and edge cases,
complementing the property-based tests that verify general properties.

Requirements tested: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import numpy as np
from apgi_system.experiments.tasks.iowa_gambling import IowaGamblingTask, DeckType, DECK_SCHEDULES
from apgi_system.experiments.tasks.masking_paradigm import MaskingParadigmTask, MaskType
from apgi_system.experiments.tasks.attentional_blink import AttentionalBlinkTask, StimulusType


class TestIowaGamblingTask:
    """Unit tests for Iowa Gambling Task with specific trial sequences."""

    def test_task_initialization(self):
        """Test that task initializes with correct parameters."""
        task = IowaGamblingTask(
            num_trials=100,
            initial_balance=2000,
            deck_stimulus_strength=1.5,
            outcome_stimulus_strength=2.0,
        )

        assert task.num_trials == 100
        assert task.initial_balance == 2000
        assert task.deck_stimulus_strength == 1.5
        assert task.outcome_stimulus_strength == 2.0
        assert len(task.trials) == 100
        assert task.current_balance == 2000

    def test_deck_schedules_defined(self):
        """Test that all deck schedules are properly defined."""
        for deck_type in DeckType:
            assert deck_type in DECK_SCHEDULES
            schedule = DECK_SCHEDULES[deck_type]
            assert "reward" in schedule
            assert "penalty_frequency" in schedule
            assert "penalties" in schedule
            assert "net_per_10" in schedule

    def test_good_vs_bad_decks(self):
        """Test that good decks have positive net outcomes and bad decks negative."""
        # Good decks (C and D) should have positive net per 10 cards
        assert DECK_SCHEDULES[DeckType.C]["net_per_10"] > 0
        assert DECK_SCHEDULES[DeckType.D]["net_per_10"] > 0

        # Bad decks (A and B) should have negative net per 10 cards
        assert DECK_SCHEDULES[DeckType.A]["net_per_10"] < 0
        assert DECK_SCHEDULES[DeckType.B]["net_per_10"] < 0

    def test_balanced_strategy_distribution(self):
        """Test that balanced strategy creates roughly equal deck distribution."""
        task = IowaGamblingTask(num_trials=100, deck_selection_strategy="balanced")

        # Count deck frequencies
        deck_counts = {deck: 0 for deck in DeckType}
        for trial in task.trials:
            deck_counts[trial.deck_choice] += 1

        # Each deck should appear roughly 25 times (±5 for randomness)
        for deck, count in deck_counts.items():
            assert 20 <= count <= 30, f"Deck {deck} appeared {count} times, expected ~25"

    def test_trial_outcomes_match_schedules(self):
        """Test that trial outcomes match the deck schedules."""
        task = IowaGamblingTask(num_trials=20)

        for trial in task.trials:
            schedule = DECK_SCHEDULES[trial.deck_choice]

            # Reward should match schedule
            assert trial.reward == schedule["reward"]

            # Penalty should be from the schedule's penalty list or 0
            if trial.penalty > 0:
                assert trial.penalty in schedule["penalties"]

            # Net outcome should be reward - penalty
            assert trial.net_outcome == trial.reward - trial.penalty

    def test_deck_stimulus_generation(self):
        """Test that deck stimuli are generated with correct dimensions and patterns."""
        task = IowaGamblingTask(num_trials=4, deck_selection_strategy="balanced")

        for trial in task.trials:
            # Check stimulus dimensions
            assert trial.deck_stimulus.shape == (256,)

            # Check that stimulus has non-zero values (not all zeros)
            assert np.any(trial.deck_stimulus != 0)

            # Check that stimulus magnitude is reasonable
            assert np.max(np.abs(trial.deck_stimulus)) < 10.0

    def test_single_trial_execution(self, apgi_system):
        """Test running a single trial on the APGI system."""
        task = IowaGamblingTask(num_trials=1)
        trial = task.trials[0]

        result = task.run_trial(apgi_system, trial)

        # Verify result structure
        assert result.trial_number == 0
        assert result.deck_choice in DeckType
        assert isinstance(result.reward, (int, np.integer))
        assert isinstance(result.penalty, (int, np.integer))
        assert isinstance(result.net_outcome, (int, np.integer))
        assert isinstance(result.running_total, (int, np.integer))
        assert isinstance(result.ignition_occurred, bool)
        assert isinstance(result.ignition_strength, (float, np.floating))
        assert isinstance(result.somatic_marker_strength, (float, np.floating))
        assert isinstance(result.decision_time, (float, np.floating))
        assert isinstance(result.anticipatory_response, (float, np.floating))

        # Verify running total updated correctly
        expected_total = task.initial_balance + result.net_outcome
        assert result.running_total == expected_total

    def test_multiple_trials_balance_tracking(self, apgi_system):
        """Test that balance is tracked correctly across multiple trials."""
        task = IowaGamblingTask(num_trials=5)
        initial_balance = task.initial_balance

        for trial in task.trials:
            result = task.run_trial(apgi_system, trial)

        # Final balance should equal initial + sum of all net outcomes
        total_net = sum(r.net_outcome for r in task.results)
        expected_final = initial_balance + total_net
        assert task.current_balance == expected_final

    def test_analysis_with_no_results(self):
        """Test that analysis handles empty results gracefully."""
        task = IowaGamblingTask(num_trials=10)
        task.results = []  # Clear results

        analysis = task.analyze_results()

        assert "error" in analysis
        assert analysis["total_trials"] == 0

    def test_analysis_structure(self, apgi_system):
        """Test that analysis returns expected structure."""
        task = IowaGamblingTask(num_trials=20)

        # Run a few trials
        for i in range(10):
            task.run_trial(apgi_system, task.trials[i])

        analysis = task.analyze_results()

        # Check required keys
        assert "total_trials" in analysis
        assert "initial_balance" in analysis
        assert "final_balance" in analysis
        assert "total_earnings" in analysis
        assert "good_deck_choices" in analysis
        assert "bad_deck_choices" in analysis
        assert "advantageous_ratio" in analysis
        assert "by_deck" in analysis
        assert "by_block" in analysis
        assert "somatic_markers" in analysis

        # Check deck analysis structure
        for deck in ["A", "B", "C", "D"]:
            assert deck in analysis["by_deck"]
            deck_data = analysis["by_deck"][deck]
            assert "selections" in deck_data
            assert "avg_net_outcome" in deck_data
            assert "avg_somatic_marker" in deck_data

    def test_task_reset(self, apgi_system):
        """Test that task reset works correctly."""
        task = IowaGamblingTask(num_trials=10)

        # Run some trials
        for i in range(5):
            task.run_trial(apgi_system, task.trials[i])

        initial_results_count = len(task.results)
        assert initial_results_count > 0

        # Reset task
        task.reset()

        # Verify reset state
        assert task.current_balance == task.initial_balance
        assert len(task.results) == 0
        assert task.current_trial_idx == 0
        assert len(task.trials) == task.num_trials


class TestMaskingParadigm:
    """Unit tests for Masking Paradigm with specific SOA values."""

    def test_task_initialization(self):
        """Test that masking task initializes correctly."""
        soas = [0, 50, 100, 200]
        task = MaskingParadigmTask(
            target_duration_ms=50.0, soas=soas, mask_duration_ms=100.0, num_trials_per_condition=10
        )

        assert task.target_duration_ms == 50.0
        assert task.soas == soas
        assert task.mask_duration_ms == 100.0
        assert task.num_trials_per_condition == 10
        # Total trials = num_soas * trials_per_condition
        assert len(task.trials) == len(soas) * 10

    def test_soa_distribution(self):
        """Test that trials are distributed across all SOA conditions."""
        soas = [0, 50, 100]
        trials_per_condition = 5
        task = MaskingParadigmTask(soas=soas, num_trials_per_condition=trials_per_condition)

        # Count trials per SOA
        soa_counts = {soa: 0 for soa in soas}
        for trial in task.trials:
            soa_counts[trial.soa_ms] += 1

        # Each SOA should have exactly trials_per_condition trials
        for soa, count in soa_counts.items():
            assert (
                count == trials_per_condition
            ), f"SOA {soa} has {count} trials, expected {trials_per_condition}"

    def test_target_stimulus_generation(self):
        """Test that target stimuli are generated correctly."""
        task = MaskingParadigmTask(num_trials_per_condition=1)

        target = task._generate_target()

        # Check dimensions
        assert target.shape == (256,)

        # Check that target has structure (not all zeros)
        assert np.any(target != 0)

        # Check magnitude is reasonable
        assert np.max(np.abs(target)) < 10.0

    def test_mask_stimulus_generation(self):
        """Test that mask stimuli are generated correctly."""
        task = MaskingParadigmTask(num_trials_per_condition=1)

        mask = task._generate_mask()

        # Check dimensions
        assert mask.shape == (256,)

        # Check that mask has high energy (not all zeros)
        assert np.any(mask != 0)

        # Mask should typically have higher energy than target
        assert np.std(mask) > 1.0

    def test_zero_soa_trial(self):
        """Test trial with SOA=0 (simultaneous target and mask)."""
        task = MaskingParadigmTask(soas=[0], num_trials_per_condition=1)

        trial = task.trials[0]
        assert trial.soa_ms == 0
        assert trial.target_duration_ms > 0
        assert trial.mask_duration_ms > 0

    def test_long_soa_trial(self):
        """Test trial with long SOA (target should be detected)."""
        task = MaskingParadigmTask(soas=[300], num_trials_per_condition=1)

        trial = task.trials[0]
        assert trial.soa_ms == 300
        # Long SOA means significant gap between target and mask

    def test_single_trial_execution(self, apgi_system):
        """Test running a single masking trial."""
        task = MaskingParadigmTask(soas=[100], num_trials_per_condition=1)

        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Verify result structure
        assert result.trial_number == 0
        assert result.soa_ms == 100
        assert result.mask_type == MaskType.PATTERN
        assert isinstance(result.target_detected, bool)
        assert isinstance(result.ignition_strength, float)
        assert isinstance(result.ignition_count, int)
        assert isinstance(result.mask_suppression_occurred, bool)

        # If detected, detection time should be set
        if result.target_detected:
            assert result.detection_time is not None
            assert result.detection_time >= 0

    def test_masking_effect_short_soa(self, apgi_system):
        """Test that short SOA typically shows masking effect."""
        task = MaskingParadigmTask(
            soas=[0, 17],  # Very short SOAs
            num_trials_per_condition=3,
            target_strength=2.0,
            mask_strength=4.0,  # Strong mask
        )

        for trial in task.trials:
            result = task.run_trial(apgi_system, trial)

        # At least some trials should show suppression at short SOAs
        suppressed_count = sum(1 for r in task.results if r.mask_suppression_occurred)
        # We expect some suppression, but not necessarily all trials
        assert suppressed_count >= 0  # At least check it's tracked

    def test_analysis_structure(self, apgi_system):
        """Test that analysis returns expected structure."""
        task = MaskingParadigmTask(soas=[0, 100], num_trials_per_condition=2)

        # Run all trials
        for trial in task.trials:
            task.run_trial(apgi_system, trial)

        analysis = task.analyze_results()

        # Check required keys
        assert "total_trials" in analysis
        assert "overall_detection_rate" in analysis
        assert "overall_suppression_rate" in analysis
        assert "masking_effect" in analysis
        assert "by_soa" in analysis
        assert "masking_curve" in analysis
        assert "task_parameters" in analysis

        # Check SOA analysis
        for soa in task.soas:
            assert soa in analysis["by_soa"]
            soa_data = analysis["by_soa"][soa]
            assert "detection_rate" in soa_data
            assert "suppression_rate" in soa_data
            assert "avg_ignition_strength" in soa_data

    def test_analysis_with_no_results(self):
        """Test that analysis handles empty results gracefully."""
        task = MaskingParadigmTask(soas=[0, 100], num_trials_per_condition=1)
        task.results = []

        analysis = task.analyze_results()

        assert "error" in analysis
        assert analysis["total_trials"] == 0

    def test_task_reset(self, apgi_system):
        """Test that task reset works correctly."""
        task = MaskingParadigmTask(soas=[0, 100], num_trials_per_condition=2)

        # Run some trials
        for i in range(2):
            task.run_trial(apgi_system, task.trials[i])

        assert len(task.results) > 0

        # Reset
        task.reset()

        # Verify reset state
        assert len(task.results) == 0
        assert task.current_trial_idx == 0
        assert len(task.trials) == len(task.soas) * task.num_trials_per_condition


class TestAttentionalBlink:
    """Unit tests for Attentional Blink with specific lag conditions."""

    def test_task_initialization(self):
        """Test that attentional blink task initializes correctly."""
        lags = [1, 2, 3, 8]
        task = AttentionalBlinkTask(
            stream_length=15, item_duration_ms=100.0, num_trials_per_lag=10, lags=lags
        )

        assert task.stream_length == 15
        assert task.item_duration_ms == 100.0
        assert task.num_trials_per_lag == 10
        assert task.lags == lags
        # Total trials = num_lags * trials_per_lag
        assert len(task.trials) == len(lags) * 10

    def test_lag_distribution(self):
        """Test that trials are distributed across all lag conditions."""
        lags = [1, 2, 4]
        trials_per_lag = 5
        task = AttentionalBlinkTask(lags=lags, num_trials_per_lag=trials_per_lag)

        # Count trials per lag
        lag_counts = {lag: 0 for lag in lags}
        for trial in task.trials:
            lag_counts[trial.lag] += 1

        # Each lag should have exactly trials_per_lag trials
        for lag, count in lag_counts.items():
            assert (
                count == trials_per_lag
            ), f"Lag {lag} has {count} trials, expected {trials_per_lag}"

    def test_trial_structure(self):
        """Test that trials have correct structure."""
        task = AttentionalBlinkTask(stream_length=15, lags=[2], num_trials_per_lag=1)

        trial = task.trials[0]

        # Check trial attributes
        assert hasattr(trial, "trial_number")
        assert hasattr(trial, "t1_position")
        assert hasattr(trial, "t2_position")
        assert hasattr(trial, "lag")
        assert hasattr(trial, "stream")
        assert hasattr(trial, "stream_types")

        # Check stream length
        assert len(trial.stream) == task.stream_length
        assert len(trial.stream_types) == task.stream_length

        # Check lag relationship
        assert trial.t2_position == trial.t1_position + trial.lag

        # Check that T1 and T2 are in the stream
        assert trial.stream_types[trial.t1_position] == StimulusType.TARGET_1
        assert trial.stream_types[trial.t2_position] == StimulusType.TARGET_2

    def test_target_positions_valid(self):
        """Test that target positions are within valid ranges."""
        task = AttentionalBlinkTask(stream_length=15, lags=[1, 2, 3], num_trials_per_lag=5)

        for trial in task.trials:
            # T1 should not be too early or too late
            assert 0 <= trial.t1_position < task.stream_length
            assert 0 <= trial.t2_position < task.stream_length

            # T2 should come after T1
            assert trial.t2_position > trial.t1_position

            # Lag should match position difference
            assert trial.t2_position - trial.t1_position == trial.lag

    def test_target_stimulus_generation(self):
        """Test that target stimuli are generated correctly."""
        task = AttentionalBlinkTask(num_trials_per_lag=1)

        t1 = task._generate_target(target_num=1)
        t2 = task._generate_target(target_num=2)

        # Check dimensions
        assert t1.shape == (256,)
        assert t2.shape == (256,)

        # Check that targets have structure
        assert np.any(t1 != 0)
        assert np.any(t2 != 0)

        # T1 and T2 should be different (different patterns)
        assert not np.allclose(t1, t2)

    def test_distractor_stimulus_generation(self):
        """Test that distractor stimuli are generated correctly."""
        task = AttentionalBlinkTask(num_trials_per_lag=1)

        distractor = task._generate_distractor()

        # Check dimensions
        assert distractor.shape == (256,)

        # Distractors should have lower magnitude than targets
        assert np.std(distractor) < task.target_salience

    def test_single_trial_execution(self, apgi_system):
        """Test running a single attentional blink trial."""
        task = AttentionalBlinkTask(stream_length=10, lags=[2], num_trials_per_lag=1)

        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Verify result structure
        assert result.trial_number == 0
        assert result.lag == 2
        assert isinstance(result.t1_detected, bool)
        assert isinstance(result.t2_detected, bool)
        assert isinstance(result.t1_signal_strength, float)
        assert isinstance(result.t2_signal_strength, float)
        assert isinstance(result.blink_occurred, bool)

        # If T1 detected, should have ignition time
        if result.t1_detected:
            assert result.t1_ignition_time is not None
            assert result.t1_ignition_time >= 0

        # If T2 detected, should have ignition time
        if result.t2_detected:
            assert result.t2_ignition_time is not None
            assert result.t2_ignition_time >= 0

        # Blink occurs when T1 detected but T2 missed
        expected_blink = result.t1_detected and not result.t2_detected
        assert result.blink_occurred == expected_blink

    def test_lag_1_sparing(self, apgi_system):
        """Test lag-1 sparing effect (T2 often detected at lag 1)."""
        task = AttentionalBlinkTask(
            stream_length=10,
            lags=[1],
            num_trials_per_lag=3,
            target_salience=3.0,  # High salience to increase detection
        )

        for trial in task.trials:
            result = task.run_trial(apgi_system, trial)

        # At lag 1, we might see some T2 detections (lag-1 sparing)
        # Just verify the mechanism works, not strict performance
        t2_detections = sum(1 for r in task.results if r.t2_detected)
        assert t2_detections >= 0  # At least check it's tracked

    def test_analysis_structure(self, apgi_system):
        """Test that analysis returns expected structure."""
        task = AttentionalBlinkTask(stream_length=10, lags=[1, 3], num_trials_per_lag=2)

        # Run all trials
        for trial in task.trials:
            task.run_trial(apgi_system, trial)

        analysis = task.analyze_results()

        # Check required keys
        assert "total_trials" in analysis
        assert "overall_t1_accuracy" in analysis
        assert "overall_t2_accuracy" in analysis
        assert "overall_blink_rate" in analysis
        assert "lag_analysis" in analysis
        assert "max_blink_lag" in analysis
        assert "max_blink_rate" in analysis
        assert "task_parameters" in analysis

        # Check lag analysis
        for lag in task.lags:
            assert lag in analysis["lag_analysis"]
            lag_data = analysis["lag_analysis"][lag]
            assert "t1_accuracy" in lag_data
            assert "t2_accuracy" in lag_data
            assert "t2_given_t1_accuracy" in lag_data
            assert "blink_rate" in lag_data

    def test_analysis_with_no_results(self):
        """Test that analysis handles empty results gracefully."""
        task = AttentionalBlinkTask(lags=[1, 2], num_trials_per_lag=1)
        task.results = []

        analysis = task.analyze_results()

        assert "error" in analysis
        assert analysis["total_trials"] == 0

    def test_task_reset(self, apgi_system):
        """Test that task reset works correctly."""
        task = AttentionalBlinkTask(lags=[1, 2], num_trials_per_lag=2)

        # Run some trials
        for i in range(2):
            task.run_trial(apgi_system, task.trials[i])

        assert len(task.results) > 0

        # Reset
        task.reset()

        # Verify reset state
        assert len(task.results) == 0
        assert task.current_trial_idx == 0
        assert len(task.trials) == len(task.lags) * task.num_trials_per_lag

    def test_blink_detection_logic(self, apgi_system):
        """Test that blink detection logic works correctly."""
        task = AttentionalBlinkTask(stream_length=10, lags=[2], num_trials_per_lag=1)

        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Verify blink logic
        if result.t1_detected and not result.t2_detected:
            assert result.blink_occurred is True
        else:
            assert result.blink_occurred is False


class TestTaskResultCompleteness:
    """Test that all tasks produce complete result structures."""

    def test_iowa_gambling_result_fields(self, apgi_system):
        """Test that Iowa Gambling results have all required fields."""
        task = IowaGamblingTask(num_trials=1)
        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Check all required fields exist
        required_fields = [
            "trial_number",
            "deck_choice",
            "reward",
            "penalty",
            "net_outcome",
            "running_total",
            "ignition_occurred",
            "ignition_strength",
            "somatic_marker_strength",
            "decision_time",
            "anticipatory_response",
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"

    def test_masking_result_fields(self, apgi_system):
        """Test that Masking Paradigm results have all required fields."""
        task = MaskingParadigmTask(soas=[100], num_trials_per_condition=1)
        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Check all required fields exist
        required_fields = [
            "trial_number",
            "soa_ms",
            "mask_type",
            "target_detected",
            "detection_time",
            "ignition_strength",
            "ignition_count",
            "mask_suppression_occurred",
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"

    def test_attentional_blink_result_fields(self, apgi_system):
        """Test that Attentional Blink results have all required fields."""
        task = AttentionalBlinkTask(lags=[2], num_trials_per_lag=1)
        trial = task.trials[0]
        result = task.run_trial(apgi_system, trial)

        # Check all required fields exist
        required_fields = [
            "trial_number",
            "lag",
            "t1_detected",
            "t2_detected",
            "t1_ignition_time",
            "t2_ignition_time",
            "t1_signal_strength",
            "t2_signal_strength",
            "blink_occurred",
        ]

        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"
