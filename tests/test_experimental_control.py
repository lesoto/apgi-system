import pytest

from apgi_framework.experimental_control import (
    ConsciousnessMeasurementValidator,
    ExperimentalControlManager,
    ParticipantPopulationGenerator,
    ParticipantProfile,
    ParticipantSimulator,
    ResponseSystemType,
    StimulusProperties,
    StimulusValidator,
    TaskType,
    TaskValidator,
    WellTrainedTaskChecker,
)


@pytest.fixture
def base_config():
    return None  # Will use defaults


def test_experimental_control_manager():
    manager = ExperimentalControlManager()

    # Test valid motor response
    response_times = [0.2, 0.25, 0.3, 0.22, 0.28]
    accuracies = [True, True, True, False, True]

    val = manager.validate_response_system(
        "P001", ResponseSystemType.MOTOR, response_times, accuracies
    )
    assert val.system_type == ResponseSystemType.MOTOR
    assert val.is_intact

    # Test invalid motor response (too short)
    val2 = manager.validate_response_system(
        "P002", ResponseSystemType.MOTOR, [0.01, 0.05], [True, True]
    )
    assert not val2.is_intact
    assert "Response time out of range" in val2.notes

    # Test task comprehension
    comp = manager.verify_task_comprehension("P001", TaskType.DETECTION, [True] * 25, 0.9)
    assert comp.performance_criterion_met

    # Generate report
    report = manager.generate_control_report("P001", "S1", [val], [comp])
    assert report.participant_id == "P001"
    assert report.overall_validity
    assert manager.is_participant_valid("P001")


def test_participant_simulator():
    profile = ParticipantProfile(
        participant_id="P001",
        age=30,
        cognitive_ability=0.8,
        attention_span=0.9,
        response_speed=1.0,
        consistency=0.9,
        fatigue_rate=1.0,
        learning_rate=1.0,
        individual_differences={"impulsivity": 0.2, "motivation": 0.8},
    )
    sim = ParticipantSimulator(profile, random_seed=42)

    response = sim.simulate_response(0.5, 0.5, "A", ["A", "B"])
    assert response.trial_number == 1

    train_resp = sim.simulate_training_session(0.5, 5, ["A"] * 5, [["A", "B"]] * 5)
    assert len(train_resp) == 5

    exp_resp = sim.simulate_experimental_session([0.5] * 5, [0.5] * 5, ["A"] * 5, [["A", "B"]] * 5)
    assert len(exp_resp) == 5

    metrics = sim.get_performance_metrics(exp_resp)
    assert "accuracy_mean" in metrics

    sim.reset_session()
    assert sim.trial_count == 0


def test_participant_population_generator():
    pop = ParticipantPopulationGenerator.generate_population(5, random_seed=42)
    assert len(pop) == 5
    assert all(isinstance(p, ParticipantProfile) for p in pop)

    clin_pop_adhd = ParticipantPopulationGenerator.generate_clinical_population(2, "adhd", 42)
    assert len(clin_pop_adhd) == 2
    assert clin_pop_adhd[0].participant_id.startswith("ADHD")

    clin_pop_dep = ParticipantPopulationGenerator.generate_clinical_population(2, "depression", 42)
    clin_pop_ctrl = ParticipantPopulationGenerator.generate_clinical_population(2, "control", 42)
    assert len(clin_pop_dep) == 2
    assert len(clin_pop_ctrl) == 2


def test_stimulus_validator():
    validator = StimulusValidator()

    valid_stim = StimulusProperties(
        stimulus_id="stim1",
        presentation_duration=0.5,
        contrast=0.5,
        size=1.0,
        luminance=50.0,
        is_supraliminal=True,
        detection_threshold=0.01,
        stimulus_type="visual",
    )
    is_valid, issues = validator.validate_stimulus(valid_stim)
    assert is_valid is True

    invalid_stim = StimulusProperties(
        stimulus_id="stim2",
        presentation_duration=0.01,
        contrast=0.01,
        size=-1.0,
        luminance=-10.0,
        is_supraliminal=False,
        detection_threshold=0.5,
        stimulus_type="visual",
    )
    is_valid_inv, issues_inv = validator.validate_stimulus(invalid_stim)
    assert is_valid_inv is False
    assert len(issues_inv) > 0

    aud_stim = StimulusProperties("A1", 0.5, 1.0, 1.0, 100.0, True, 10.0, "auditory")
    assert validator.validate_stimulus(aud_stim)[0] is True

    tact_stim = StimulusProperties("T1", 0.5, 1.0, 1.0, 20.0, True, 1.0, "tactile")
    assert validator.validate_stimulus(tact_stim)[0] is True


def test_task_validator():
    pass

    stim_val = StimulusValidator()
    config = stim_val._get_default_config()
    validator = TaskValidator(config=config)
    # The TaskValidator's default config wouldn't have detection_thresholds,
    # but we need to merge it.
    config.update(validator._get_default_config())
    validator = TaskValidator(config=config)
    # Mock some responses
    profile = ParticipantProfile("P1", 20, 0.9, 0.9, 1.0, 0.9, 1.0, 1.0, {})
    sim = ParticipantSimulator(profile, 42)
    responses = sim.simulate_training_session(0.5, 60, ["A"] * 60, [["A", "B"]] * 60)

    assessment = validator.assess_training_adequacy("T1", "P1", responses)
    assert assessment.training_trials_completed == 60

    stimuli = [StimulusProperties("S1", 0.5, 0.5, 1.0, 50.0, True, 0.01, "visual")]
    task_val = validator.validate_task_design("T1", stimuli, 5.0, 2.0)
    assert task_val.is_valid is True


def test_well_trained_task_checker():
    checker = WellTrainedTaskChecker()
    profile = ParticipantProfile("P1", 20, 0.9, 0.9, 1.0, 0.9, 1.0, 1.0, {})
    sim = ParticipantSimulator(profile, 42)
    session1 = sim.simulate_training_session(0.5, 30, ["A"] * 30, [["A", "B"]] * 30)
    session2 = sim.simulate_training_session(0.5, 30, ["A"] * 30, [["A", "B"]] * 30)
    session3 = sim.simulate_training_session(0.5, 30, ["A"] * 30, [["A", "B"]] * 30)

    res = checker.assess_task_proficiency("P1", "T1", [session1, session2, session3])
    assert "proficiency_level" in res


def test_consciousness_validator():
    # just instantiate to test module loads and config works
    validator = ConsciousnessMeasurementValidator()
    assert validator.config is not None
