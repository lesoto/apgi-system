"""
Extended tests for Threshold Detection Paradigm component.
"""

from datetime import datetime

import numpy as np
import pytest

# Import threshold detection components
try:
    from apgi_framework.research.threshold_detection_paradigm import (
        AdaptiveStaircase,
        ConsciousnessLevel,
        ModalityType,
        PsychometricFunction,
        StimulusParameters,
        ThresholdDetectionSystem,
        ThresholdMethod,
        TrialResponse,
    )

    THRESHOLD_DETECTION_AVAILABLE = True
except ImportError as e:
    THRESHOLD_DETECTION_AVAILABLE = False
    IMPORT_ERROR_THRESHOLD = e


class TestThresholdDetectionParadigmExtended:
    """Extended tests for Threshold Detection Paradigm."""

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_all_modality_types(self):
        """Test all modality types."""
        system = ThresholdDetectionSystem()

        for modality in ModalityType:
            # Should be able to run threshold estimation for all modalities
            estimate = system.run_threshold_estimation(
                modality=modality,
                method=ThresholdMethod.ADAPTIVE_STAIRCASE,
                n_trials=20,
            )

            assert estimate.modality == modality
            assert estimate.threshold_value >= 0
            assert estimate.n_trials == 20

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_all_threshold_methods(self):
        """Test all threshold estimation methods."""
        system = ThresholdDetectionSystem()

        for method in ThresholdMethod:
            # Should be able to run all methods
            estimate = system.run_threshold_estimation(
                modality=ModalityType.VISUAL, method=method, n_trials=20
            )

            assert estimate.method == method
            assert estimate.threshold_value >= 0

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_all_psychometric_functions(self):
        """Test all psychometric function types."""
        # Test cumulative Gaussian
        gaussian_func = PsychometricFunction("cumulative_gaussian")
        x = np.linspace(0, 10, 100)
        y = gaussian_func.cumulative_gaussian(x, 5.0, 1.0, 0.5, 0.05)

        assert len(y) == len(x)
        assert y[0] >= 0.5  # Guess rate at low intensity
        assert y[-1] > y[0]  # Should increase with intensity
        assert all(0.5 <= yi <= 1.0 for yi in y)  # All values should be between guess rate and 1

        # Test Weibull
        weibull_func = PsychometricFunction("weibull")
        y_weibull = weibull_func.weibull(x, 5.0, 2.0, 0.5, 0.05)
        assert len(y_weibull) == len(x)
        assert y_weibull[0] >= 0.5  # Guess rate at low intensity
        assert y_weibull[-1] > y_weibull[0]  # Should increase with intensity
        assert all(0.5 <= yi <= 1.0 for yi in y_weibull)

        # Test logistic
        logistic_func = PsychometricFunction("logistic")
        y_logistic = logistic_func.logistic(x, 5.0, 1.0, 0.5, 0.05)
        assert len(y_logistic) == len(x)
        assert y_logistic[0] >= 0.5  # Guess rate at low intensity
        assert y_logistic[-1] > y_logistic[0]  # Should increase with intensity
        assert all(0.5 <= yi <= 1.0 for yi in y_logistic)

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_psychometric_function_fitting_edge_cases(self):
        """Test psychometric function fitting with edge cases."""
        func = PsychometricFunction("cumulative_gaussian")

        # Perfect separation (all 0s then all 1s)
        intensities = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        responses = np.array([0, 0, 0, 0, 1, 1, 1, 1])

        fit_result = func.fit_function(intensities, responses)
        assert "parameters" in fit_result
        assert fit_result["r_squared"] >= 0

        # All same response
        responses_all_zero = np.array([0, 0, 0, 0, 0, 0, 0, 0])
        with pytest.raises(Exception):  # Should fail to fit
            func.fit_function(intensities, responses_all_zero)

        # Very noisy data
        responses_noisy = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        fit_result = func.fit_function(intensities, responses_noisy)
        assert "parameters" in fit_result
        assert fit_result["r_squared"] <= 0.5  # Poor fit expected

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_adaptive_staircase_rules(self):
        """Test different staircase rules."""
        # Test 3up_1down rule
        staircase_3up1down = AdaptiveStaircase(
            start_intensity=5.0, step_size=0.5, rule="3up_1down", max_trials=20
        )

        # Test invalid rule
        with pytest.raises(Exception):
            AdaptiveStaircase(
                start_intensity=5.0, step_size=0.5, rule="invalid_rule", max_trials=20
            )

        # Test staircase behavior
        for i in range(10):
            # 3up_1down: need 3 correct to go down
            staircase_3up1down.get_next_intensity()
            staircase_3up1down.update_staircase(True)  # Correct

            if i < 2:  # First 2 correct, shouldn't change
                assert staircase_3up1down.current_intensity == 5.0
            elif i == 2:  # 3rd correct, should decrease
                assert staircase_3up1down.current_intensity == 4.5
                staircase_3up1down.consecutive_correct = 0  # Reset for next test

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_staircase_completion_conditions(self):
        """Test staircase completion conditions."""
        staircase = AdaptiveStaircase(
            start_intensity=5.0, step_size=0.5, rule="3up_1down", max_trials=10
        )

        # Should not be complete initially
        assert not staircase.is_complete()

        # Run to max trials
        for i in range(10):
            staircase.update_staircase(i % 2 == 0)  # Alternate correct/incorrect

        # Should be complete due to max trials
        assert staircase.is_complete()

        # Test with reversals
        staircase_reversal = AdaptiveStaircase(
            start_intensity=5.0, step_size=0.5, rule="3up_1down", max_trials=50
        )

        # Create many reversals (3 correct, 1 incorrect pattern)
        for i in range(20):
            response = (i % 4) != 3  # True for i%4 in [0,1,2], False for i%4==3
            staircase_reversal.update_staircase(response)

        # Should be complete due to reversals
        assert staircase_reversal.is_complete()
        assert len(staircase_reversal.reversals) >= 2

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_threshold_extraction_methods(self):
        """Test different threshold extraction methods."""
        func = PsychometricFunction("cumulative_gaussian")

        # Test extraction at different performance levels
        intensities = np.linspace(0, 10, 50)
        responses = func.cumulative_gaussian(intensities, 5.0, 1.0, 0.5, 0.05)
        binary_responses = np.random.random(len(responses)) < responses

        fit_result = func.fit_function(intensities, binary_responses)
        params = fit_result["parameters"]

        # Test extraction at different performance levels
        for target_perf in [0.5, 0.7, 0.8, 0.9]:
            threshold = func._extract_threshold_at_performance(
                "cumulative_gaussian", params, target_perf
            )

            assert isinstance(threshold, float)
            assert 0 <= threshold <= 10

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_confidence_interval_methods(self):
        """Test confidence interval calculation methods."""
        system = ThresholdDetectionSystem()

        # Test with good data
        intensities = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        responses = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 1])
        threshold = 5.0

        ci_lower, ci_upper = system._calculate_confidence_interval(
            intensities, responses, threshold
        )

        assert ci_lower <= threshold <= ci_upper
        assert ci_lower >= 0
        assert ci_upper >= threshold

        # Test with noisy data
        noisy_responses = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        ci_lower_noisy, ci_upper_noisy = system._calculate_confidence_interval(
            intensities, noisy_responses, threshold
        )

        # Should still produce valid interval
        assert ci_lower_noisy <= threshold <= ci_upper_noisy

        # Test with minimal data
        min_intensities = np.array([1, 2])
        min_responses = np.array([0, 1])
        ci_lower_min, ci_upper_min = system._calculate_confidence_interval(
            min_intensities, min_responses, 1.5
        )

        assert ci_lower_min <= 1.5 <= ci_upper_min

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_neural_validation_comprehensive(self):
        """Test comprehensive neural validation."""
        system = ThresholdDetectionSystem()

        # Create trial data with varying neural responses
        trial_data = []
        for i in range(30):
            # Create intensity-dependent neural responses
            intensity = i * 0.3
            detection_probability = 1 / (1 + np.exp(-(intensity - 5) / 2))
            detected = np.random.random() < detection_probability

            # Neural responses scale with detection probability
            p3b_amp = detected * (5.0 + detection_probability * 3) + np.random.normal(0, 0.5)
            gamma_power = detected * (2.0 + detection_probability * 1) + np.random.normal(0, 0.2)
            pupil_dilation = detected * (0.4 + detection_probability * 0.2) + np.random.normal(
                0, 0.05
            )

            stim_params = StimulusParameters(
                modality=ModalityType.VISUAL, intensity=intensity, duration=100.0
            )

            trial = TrialResponse(
                trial_id=f"neural_comprehensive_{i}",
                timestamp=datetime.now(),
                stimulus_params=stim_params,
                detection=detected,
                confidence=detection_probability,
                reaction_time=300 + np.random.normal(0, 50),
                consciousness_level="clear_awareness" if detected else "no_awareness",
                p3b_amplitude=p3b_amp,
                gamma_power=gamma_power,
                pupil_dilation=pupil_dilation,
            )
            trial_data.append(trial)

        # Test neural validation
        correlation, neural_threshold = system._validate_with_neural_data(trial_data)

        assert -1 <= correlation <= 1
        assert neural_threshold is None or neural_threshold >= 0

        # Should find positive correlation with good data
        assert correlation > 0

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_cross_modal_comparisons_comprehensive(self):
        """Test comprehensive cross-modal comparisons."""
        system = ThresholdDetectionSystem()

        # Run estimations for multiple modalities
        modalities = [
            ModalityType.VISUAL,
            ModalityType.AUDITORY,
            ModalityType.INTEROCEPTIVE,
        ]
        estimates = {}

        for modality in modalities:
            estimate = system.run_threshold_estimation(
                modality=modality,
                method=ThresholdMethod.ADAPTIVE_STAIRCASE,
                n_trials=30,
            )
            estimates[modality] = estimate

        # Test all pairwise comparisons
        for i, modality1 in enumerate(modalities):
            for modality2 in modalities[i + 1 :]:
                comparison = system.compare_cross_modal_thresholds(modality1, modality2)

                assert comparison.primary_modality == modality1
                assert comparison.comparison_modality == modality2
                assert comparison.primary_threshold == estimates[modality1].threshold_value
                assert comparison.comparison_threshold == estimates[modality2].threshold_value
                assert comparison.sensitivity_ratio > 0
                assert -1 <= comparison.cross_modal_correlation <= 1
                assert isinstance(comparison.shared_neural_signatures, list)
                assert isinstance(comparison.modality_specific_signatures, list)

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_all_consciousness_levels(self):
        """Test all consciousness levels in trial responses."""
        stim_params = StimulusParameters(
            modality=ModalityType.VISUAL, intensity=5.0, duration=100.0
        )

        for level in ConsciousnessLevel:
            trial = TrialResponse(
                trial_id=f"consciousness_{level.value}",
                timestamp=datetime.now(),
                stimulus_params=stim_params,
                detection=True,
                confidence=0.8,
                reaction_time=350.0,
                consciousness_level=level,
            )

            assert trial.consciousness_level == level

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_stimulus_parameters_all_modalities(self):
        """Test stimulus parameters for all modalities."""
        # Visual stimulus
        visual_params = StimulusParameters(
            modality=ModalityType.VISUAL,
            intensity=5.0,
            duration=100.0,
            frequency=10.0,
            contrast=0.8,
            gabor_orientation=45.0,
            gabor_frequency=2.0,
        )

        visual_dict = visual_params.to_dict()
        assert visual_dict["modality"] == "visual"
        assert visual_dict["contrast"] == 0.8
        assert visual_dict["gabor_orientation"] == 45.0

        # Auditory stimulus
        auditory_params = StimulusParameters(
            modality=ModalityType.AUDITORY,
            intensity=70.0,
            duration=200.0,
            frequency=1000.0,
            amplitude=0.5,
            tone_frequency=440.0,
        )

        auditory_dict = auditory_params.to_dict()
        assert auditory_dict["modality"] == "auditory"
        assert auditory_dict["frequency"] == 1000.0
        assert auditory_dict["tone_frequency"] == 440.0

        # Interoceptive stimulus
        interoceptive_params = StimulusParameters(
            modality=ModalityType.INTEROCEPTIVE,
            intensity=3.0,
            duration=500.0,
            co2_concentration=5.0,
        )

        interoceptive_dict = interoceptive_params.to_dict()
        assert interoceptive_dict["modality"] == "interoceptive"
        assert interoceptive_dict["co2_concentration"] == 5.0

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_report_generation_comprehensive(self):
        """Test comprehensive report generation."""
        system = ThresholdDetectionSystem()

        # Generate data for multiple modalities and methods
        for modality in [ModalityType.VISUAL, ModalityType.AUDITORY]:
            for method in [
                ThresholdMethod.ADAPTIVE_STAIRCASE,
                ThresholdMethod.CONSTANT_STIMULI,
            ]:
                system.run_threshold_estimation(modality, method, n_trials=20)

        # Generate cross-modal comparisons
        system.compare_cross_modal_thresholds(ModalityType.VISUAL, ModalityType.AUDITORY)

        # Generate comprehensive report
        report = system.generate_threshold_report()

        # Check report structure
        assert "Threshold Detection Paradigm Report" in report
        assert "THRESHOLD ESTIMATES" in report
        assert "CROSS-MODAL COMPARISONS" in report

        # Check that all modalities and methods are included
        assert "visual" in report.lower()
        assert "auditory" in report.lower()
        assert "adaptive_staircase" in report
        assert "constant_stimuli" in report

        # Check cross-modal comparison section
        assert "visual vs auditory" in report.lower()
        assert "sensitivity ratio" in report.lower()
        assert "cross-modal correlation" in report.lower()

        # Check neural validation information
        assert "neural correlation" in report.lower()

        # Check performance metrics
        assert "goodness of fit" in report.lower()
        assert "bic" in report.lower()
        assert "trials" in report.lower()

    @pytest.mark.skipif(
        not THRESHOLD_DETECTION_AVAILABLE,
        reason=f"Threshold detection not available: {IMPORT_ERROR_THRESHOLD if not THRESHOLD_DETECTION_AVAILABLE else ''}",
    )
    def test_error_handling_robustness(self):
        """Test robust error handling."""
        system = ThresholdDetectionSystem()

        # Test with invalid parameters
        with pytest.raises(Exception):
            system.run_threshold_estimation(
                modality="invalid_modality",  # Invalid
                method=ThresholdMethod.ADAPTIVE_STAIRCASE,
                n_trials=10,
            )

        # Test with invalid method
        with pytest.raises(Exception):
            system.run_threshold_estimation(
                modality=ModalityType.VISUAL,
                method="invalid_method",  # Invalid
                n_trials=10,
            )

        # Test with insufficient trials
        estimate = system.run_threshold_estimation(
            modality=ModalityType.VISUAL,
            method=ThresholdMethod.ADAPTIVE_STAIRCASE,
            n_trials=5,  # Very few trials
        )

        # Should still produce result but with warnings
        assert estimate.threshold_value >= 0
        assert estimate.n_trials == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
