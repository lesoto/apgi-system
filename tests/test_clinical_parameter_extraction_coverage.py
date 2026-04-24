"""
Tests for Clinical Parameter Extraction in apgi_framework/clinical/parameter_extraction.py.
"""

from datetime import datetime
from apgi_framework.clinical.parameter_extraction import (
    ClinicalParameterExtractor,
    ModalityType,
    TaskType,
    AssessmentTask,
    AssessmentBattery,
    ClinicalParameters,
)


class TestClinicalParameterExtraction:
    def test_clinical_parameters_to_dict(self):
        params = ClinicalParameters(
            participant_id="P001",
            assessment_date=datetime(2024, 1, 1),
            theta_t=3.7,
            pi_e=2.2,
            pi_i=1.6,
            beta=1.3,
        )
        data = params.to_dict()
        assert data["participant_id"] == "P001"
        assert data["theta_t"] == 3.7
        assert data["assessment_date"] == "2024-01-01T00:00:00"

    def test_clinical_parameters_from_dict(self):
        data = {
            "participant_id": "P002",
            "theta_t": 3.8,
            "assessment_date": "2024-02-01T12:00:00",
        }
        params = ClinicalParameters.from_dict(data)
        assert params.participant_id == "P002"
        assert params.theta_t == 3.8
        assert params.assessment_date == datetime(2024, 2, 1, 12, 0)

    def test_assessment_task_to_dict(self):
        task = AssessmentTask(
            task_type=TaskType.THRESHOLD_DETECTION,
            modality=ModalityType.VISUAL,
            duration=5.0,
            n_trials=40,
        )
        data = task.to_dict()
        assert data["task_type"] == "threshold_detection"
        assert data["modality"] == "visual"
        assert data["duration"] == 5.0

    def test_assessment_battery_logic(self):
        battery = AssessmentBattery(battery_id="B001", participant_id="P001")
        task1 = AssessmentTask(TaskType.THRESHOLD_DETECTION, ModalityType.VISUAL, 5.0, 40)
        task2 = AssessmentTask(TaskType.THRESHOLD_DETECTION, ModalityType.AUDITORY, 5.0, 40)

        battery.add_task(task1)
        battery.add_task(task2)

        assert len(battery.tasks) == 2
        assert battery.get_total_planned_duration() == 10.0
        assert battery.get_completion_rate() == 0.0

        task1.completed = True
        task1.data_quality = 0.8
        assert battery.get_completion_rate() == 0.5
        assert battery.get_overall_quality() == 0.8

    def test_extractor_create_battery(self):
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()

        assert battery.participant_id == "P001"
        assert len(battery.tasks) == 6
        assert any(
            t.task_type == TaskType.THRESHOLD_DETECTION and t.modality == ModalityType.VISUAL
            for t in battery.tasks
        )

    def test_extract_parameters_from_battery(self):
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()

        # Mock data
        behavioral_data = {
            "visual_threshold": 0.4,
            "auditory_threshold": 0.4,
            "interoceptive_threshold": 0.6,
            "visual_accuracy": 0.8,
            "auditory_accuracy": 0.8,
            "rt_variability": 80.0,
            "heartbeat_accuracy": 0.7,
            "breath_awareness": 0.6,
            "emotional_stroop_interference": 70.0,
            "psychometric_slope": 1.2,
            "recovery_trials": 3,
        }

        params = extractor.extract_parameters_from_battery(battery, behavioral_data)

        assert params.participant_id == "P001"
        assert 1.0 <= params.theta_t <= 6.0
        assert 0.5 <= params.pi_e <= 4.0
        assert 0.3 <= params.pi_i <= 3.5
        assert 0.5 <= params.beta <= 3.0

    def test_reliability_metrics(self):
        extractor = ClinicalParameterExtractor("P001")
        p1 = ClinicalParameters(theta_t=3.5, pi_e=2.0)
        p2 = ClinicalParameters(theta_t=3.6, pi_e=2.1)

        metrics = extractor.calculate_reliability_metrics(p1, p2)
        assert "theta_t" in metrics.test_retest_icc
        assert "pi_e" in metrics.test_retest_icc

    def test_internal_consistency(self):
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()
        trial_data = {
            "task1": [1.0, 1.0, 0.0, 1.0, 1.0] * 10,
            "task2": [1.0, 0.0, 1.0, 1.0, 1.0] * 10,
        }
        alpha = extractor.calculate_internal_consistency(battery, trial_data)
        assert isinstance(alpha, float)

    def test_split_half_reliability(self):
        extractor = ClinicalParameterExtractor("P001")
        battery = extractor.create_standard_battery()
        trial_data = {"task1": [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0] * 10}
        res = extractor.calculate_split_half_reliability(battery, trial_data)
        assert isinstance(res, float)
