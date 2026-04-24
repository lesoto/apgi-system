from apgi_framework.experimental_control import (
    ConsciousnessMeasurementValidator,
    ExperimentalIntegrityChecker,
    ExperimentalCondition,
)


def test_consciousness_measurement_validator():
    validator = ConsciousnessMeasurementValidator()

    # Assess metacognitive sensitivity
    primary_responses = [True, False, True, True, False]
    confidence_ratings = [0.9, 0.4, 0.8, 0.7, 0.3]
    correct_answers = [True, True, True, False, False]

    meta_assess = validator.assess_metacognitive_sensitivity(
        "P1", primary_responses, confidence_ratings, correct_answers
    )
    assert meta_assess.participant_id == "P1"

    # Validate single measure
    measure = validator.validate_consciousness_measure("confidence", [0.8, 0.7, 0.9])
    assert measure.measure_type == "confidence"

    # Generate full report
    report = validator.generate_consciousness_validation_report(
        "P1", "S1", [True] * 5, [True] * 5, [0.8] * 5, [0.5] * 5, [True] * 5
    )
    assert report.participant_id == "P1"


def test_experimental_integrity_checker():
    checker = ExperimentalIntegrityChecker()

    # Response system integrity
    resp_data = {"motor": {"response_times": [0.2, 0.3], "accuracies": [True, True]}}
    res = checker.check_response_system_integrity("P1", resp_data)
    assert res.check_name == "response_system_integrity"

    # Consciousness validity
    cons_data = {
        "subjective_reports": [True] * 3,
        "forced_choice_responses": [True] * 3,
        "confidence_ratings": [0.8] * 3,
        "wagering_responses": [0.5] * 3,
        "correct_answers": [True] * 3,
    }
    cons_res = checker.check_consciousness_measurement_validity("P1", "S1", cons_data)
    assert cons_res.check_name == "consciousness_measurement_validity"

    # Condition compliance
    cond = ExperimentalCondition("C1", "Cond1", {"param1": 1.0, "param2": "val"}, {}, ["ctrl1"], {})
    act_params = {"param1": 1.0, "param2": "val", "controls_verified": ["ctrl1"]}
    comp_res = checker.check_experimental_condition_compliance(cond, act_params)
    assert comp_res.passed

    # Data quality
    session_data = {
        "response_times": [0.2] * 10,
        "accuracies": [True] * 10,
        "confidence_ratings": [0.8] * 10,
        "trial_timestamps": [1.0, 3.0, 5.0, 7.0, 9.0],
    }
    qual_res = checker.check_data_quality("P1", session_data)
    assert qual_res.passed

    # Generate integrity report
    exp_data = {
        "response_data": resp_data,
        "consciousness_data": cons_data,
        "experimental_condition": cond,
        "actual_parameters": act_params,
        "session_data": session_data,
    }
    report = checker.generate_integrity_report("Exp1", "P1", "S1", exp_data)
    assert report.experiment_id == "Exp1"

    batch_reports = checker.validate_experiment_batch(
        [
            {
                "experiment_id": "Exp1",
                "participant_id": "P1",
                "session_id": "S1",
                **exp_data,
            }
        ]
    )
    assert len(batch_reports) == 1
