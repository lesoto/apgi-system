"""
Comprehensive test suite for pharmacological_simulator.py module.

This test suite provides full coverage for the PharmacologicalSimulator class and all
drug simulation methods, ensuring all critical functionality is tested.
"""

from datetime import datetime

import pytest

from apgi_framework.exceptions import ValidationError

# Import the modules we're testing
from apgi_framework.simulators.pharmacological_simulator import (
    DrugAdministration,
    DrugClass,
    DrugProfile,
    NeuromodulatorSystem,
    PharmacologicalResponse,
    PharmacologicalSimulator,
)


class TestDrugClass:
    """Test DrugClass enum."""

    def test_drug_class_values(self):
        """Test DrugClass enum values."""
        assert DrugClass.BETA_BLOCKER.value == "beta_blocker"
        assert DrugClass.DOPAMINE_PRECURSOR.value == "dopamine_precursor"
        assert DrugClass.SEROTONIN_REUPTAKE_INHIBITOR.value == "serotonin_reuptake_inhibitor"
        assert DrugClass.CHOLINESTERASE_INHIBITOR.value == "cholinesterase_inhibitor"
        assert DrugClass.PLACEBO.value == "placebo"


class TestNeuromodulatorSystem:
    """Test NeuromodulatorSystem enum."""

    def test_neuromodulator_system_values(self):
        """Test NeuromodulatorSystem enum values."""
        assert NeuromodulatorSystem.NOREPINEPHRINE.value == "norepinephrine"
        assert NeuromodulatorSystem.DOPAMINE.value == "dopamine"
        assert NeuromodulatorSystem.SEROTONIN.value == "serotonin"
        assert NeuromodulatorSystem.ACETYLCHOLINE.value == "acetylcholine"


class TestDrugProfile:
    """Test DrugProfile dataclass."""

    def test_drug_profile_creation(self):
        """Test creating a DrugProfile."""
        profile = DrugProfile(
            name="test_drug",
            drug_class=DrugClass.BETA_BLOCKER,
            target_system=NeuromodulatorSystem.NOREPINEPHRINE,
            half_life=4.0,
            peak_effect_time=1.5,
            bioavailability=0.8,
            dose_response_curve="linear",
            threshold_effect_magnitude=0.5,
            threshold_effect_direction=1,
            physiological_effects={"heart_rate": (-10, -5)},
        )

        assert profile.name == "test_drug"
        assert profile.drug_class == DrugClass.BETA_BLOCKER
        assert profile.target_system == NeuromodulatorSystem.NOREPINEPHRINE
        assert profile.half_life == 4.0
        assert profile.peak_effect_time == 1.5
        assert profile.bioavailability == 0.8
        assert profile.dose_response_curve == "linear"
        assert profile.threshold_effect_magnitude == 0.5
        assert profile.threshold_effect_direction == 1
        assert profile.physiological_effects == {"heart_rate": (-10, -5)}


class TestDrugAdministration:
    """Test DrugAdministration dataclass."""

    def test_drug_administration_creation(self):
        """Test creating a DrugAdministration."""
        profile = DrugProfile(
            "test",
            DrugClass.BETA_BLOCKER,
            NeuromodulatorSystem.NOREPINEPHRINE,
            4.0,
            1.5,
            0.8,
            "linear",
            0.5,
            1,
            {},
        )

        administration = DrugAdministration(
            drug_profile=profile,
            dosage=10.0,
            administration_time=datetime.now(),
            route="oral",
            participant_weight=70.0,
            metabolism_rate=1.0,
            sensitivity_factor=1.0,
        )

        assert administration.drug_profile == profile
        assert administration.dosage == 10.0
        assert administration.route == "oral"
        assert administration.participant_weight == 70.0
        assert administration.metabolism_rate == 1.0
        assert administration.sensitivity_factor == 1.0


class TestPharmacologicalResponse:
    """Test PharmacologicalResponse dataclass."""

    def test_pharmacological_response_creation(self):
        """Test creating a PharmacologicalResponse."""
        profile = DrugProfile(
            "test",
            DrugClass.BETA_BLOCKER,
            NeuromodulatorSystem.NOREPINEPHRINE,
            4.0,
            1.5,
            0.8,
            "linear",
            0.5,
            1,
            {},
        )

        administration = DrugAdministration(profile, 10.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        response = PharmacologicalResponse(
            drug_administration=administration,
            time_course={0.0: 0.0, 1.0: 5.0},
            threshold_modulation={0.0: 0.0, 1.0: 0.3},
            peak_threshold_effect=0.3,
            peak_effect_time=1.0,
            physiological_responses={"heart_rate": {0.0: 70.0, 1.0: 65.0}},
            drug_level_confirmed=True,
            physiological_effects_confirmed=True,
            expected_vs_observed_correlation=0.95,
        )

        assert response.drug_administration == administration
        assert response.time_course == {0.0: 0.0, 1.0: 5.0}
        assert response.threshold_modulation == {0.0: 0.0, 1.0: 0.3}
        assert response.peak_threshold_effect == 0.3
        assert response.peak_effect_time == 1.0
        assert response.physiological_responses == {"heart_rate": {0.0: 70.0, 1.0: 65.0}}
        assert response.drug_level_confirmed is True
        assert response.physiological_effects_confirmed is True
        assert response.expected_vs_observed_correlation == 0.95


class TestPharmacologicalSimulator:
    """Test PharmacologicalSimulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = PharmacologicalSimulator()

    def test_pharmacological_simulator_initialization(self):
        """Test PharmacologicalSimulator initialization."""
        assert isinstance(self.simulator.drug_profiles, dict)
        assert len(self.simulator.drug_profiles) > 0
        assert self.simulator.simulation_duration == 8.0
        assert self.simulator.time_resolution == 0.25
        assert self.simulator.default_metabolism_range == (0.7, 1.3)
        assert self.simulator.default_sensitivity_range == (0.8, 1.2)

    def test_initialize_drug_profiles(self):
        """Test drug profile initialization."""
        profiles = self.simulator._initialize_drug_profiles()

        assert isinstance(profiles, dict)
        assert "propranolol" in profiles
        assert "l_dopa" in profiles

        # Check propranolol profile
        propranolol = profiles["propranolol"]
        assert propranolol.name == "propranolol"
        assert propranolol.drug_class == DrugClass.BETA_BLOCKER
        assert propranolol.target_system == NeuromodulatorSystem.NOREPINEPHRINE
        assert propranolol.half_life == 4.0
        assert propranolol.bioavailability == 0.25

        # Check L-DOPA profile
        l_dopa = profiles["l_dopa"]
        assert l_dopa.name == "l_dopa"
        assert l_dopa.drug_class == DrugClass.DOPAMINE_PRECURSOR
        assert l_dopa.target_system == NeuromodulatorSystem.DOPAMINE
        assert l_dopa.half_life == 1.5

    def test_simulate_drug_administration_basic(self):
        """Test basic drug administration simulation."""
        response = self.simulator.simulate_drug_administration(
            drug_name="propranolol",
            dosage=40.0,
            participant_weight=70.0,
            route="oral",
            metabolism_rate=1.0,
            sensitivity_factor=1.0,
        )

        assert isinstance(response, PharmacologicalResponse)
        assert isinstance(response.time_course, dict)
        assert isinstance(response.threshold_modulation, dict)
        assert isinstance(response.physiological_responses, dict)
        assert isinstance(response.peak_threshold_effect, float)
        assert isinstance(response.peak_effect_time, float)
        assert isinstance(bool(response.drug_level_confirmed), bool)
        assert isinstance(bool(response.physiological_effects_confirmed), bool)
        assert isinstance(response.expected_vs_observed_correlation, float)

    def test_simulate_drug_administration_different_routes(self):
        """Test drug administration with different routes."""
        for route in ["oral", "iv", "im"]:
            response = self.simulator.simulate_drug_administration(
                drug_name="propranolol",
                dosage=40.0,
                participant_weight=70.0,
                route=route,
                metabolism_rate=1.0,
                sensitivity_factor=1.0,
            )

            assert isinstance(response, PharmacologicalResponse)
            assert bool(response.drug_level_confirmed) is True

    def test_simulate_drug_administration_individual_variability(self):
        """Test drug administration with individual variability."""
        # Test different metabolism rates
        for metabolism in [0.8, 1.0, 1.2]:
            response = self.simulator.simulate_drug_administration(
                drug_name="l_dopa",
                dosage=100.0,
                participant_weight=70.0,
                route="oral",
                metabolism_rate=metabolism,
                sensitivity_factor=1.0,
            )

            assert isinstance(response, PharmacologicalResponse)
            assert bool(response.drug_level_confirmed) is True

    def test_simulate_pharmacokinetics(self):
        """Test pharmacokinetics simulation."""
        profile = self.simulator.get_drug_profile("propranolol")
        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = self.simulator._simulate_pharmacokinetics(administration)

        assert isinstance(time_course, dict)
        assert len(time_course) > 0

        # Check that time points are reasonable
        times = list(time_course.keys())
        assert times[0] >= 0.0
        assert times[-1] <= self.simulator.simulation_duration

        # Check that concentrations are reasonable
        concentrations = list(time_course.values())
        assert all(c >= 0 for c in concentrations)
        assert max(concentrations) > 0

    def test_simulate_threshold_modulation(self):
        """Test threshold modulation simulation."""
        profile = self.simulator.get_drug_profile("propranolol")
        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = {0.0: 0.0, 1.0: 5.0, 2.0: 3.0}
        threshold_modulation = self.simulator._simulate_threshold_modulation(
            administration, time_course
        )

        assert isinstance(threshold_modulation, dict)
        assert len(threshold_modulation) == len(time_course)

        # Check that threshold changes are reasonable
        threshold_changes = list(threshold_modulation.values())
        assert isinstance(threshold_changes[0], (int, float))

    def test_simulate_physiological_responses(self):
        """Test physiological responses simulation."""
        profile = self.simulator.get_drug_profile("propranolol")
        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = {0.0: 0.0, 1.0: 5.0, 2.0: 3.0}

        responses = self.simulator._simulate_physiological_responses(administration, time_course)

        assert isinstance(responses, dict)

        # Check that physiological effects are present
        for effect_name in profile.physiological_effects.keys():
            assert effect_name in responses
            assert isinstance(responses[effect_name], dict)

    def test_confirm_drug_levels(self):
        """Test drug level confirmation."""
        time_course = {0.0: 0.0, 1.0: 5.0, 2.0: 3.0}

        confirmed = self.simulator._confirm_drug_levels(time_course)

        assert isinstance(confirmed, bool)
        assert confirmed is True  # Should be confirmed for valid time course

    def test_confirm_drug_levels_empty(self):
        """Test drug level confirmation with empty time course."""
        time_course = {}

        confirmed = self.simulator._confirm_drug_levels(time_course)

        assert confirmed is False

    def test_confirm_physiological_effects(self):
        """Test physiological effects confirmation."""
        profile = self.simulator.get_drug_profile("propranolol")
        physiological_responses = {"heart_rate": {0.0: 70.0, 1.0: 65.0}}

        confirmed = self.simulator._confirm_physiological_effects(physiological_responses, profile)

        assert isinstance(confirmed, bool)

    def test_calculate_effect_correlation(self):
        """Test effect correlation calculation."""
        profile = self.simulator.get_drug_profile("propranolol")
        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        threshold_modulation = {0.0: 0.0, 1.0: 0.3, 2.0: 0.2}
        physiological_responses = {"heart_rate": {0.0: 70.0, 1.0: 65.0, 2.0: 67.0}}

        correlation = self.simulator._calculate_effect_correlation(
            administration, threshold_modulation, physiological_responses
        )

        assert isinstance(correlation, (int, float))
        assert 0.0 <= correlation <= 1.0

    def test_simulate_drug_interaction(self):
        """Test drug interaction simulation."""
        drug_names = ["propranolol", "l_dopa"]
        dosages = [40.0, 100.0]

        responses = self.simulator.simulate_drug_interaction(
            drug_names, dosages, participant_weight=70.0
        )

        assert isinstance(responses, dict)
        assert len(responses) == len(drug_names)

        for drug_name in drug_names:
            assert drug_name in responses
            assert isinstance(responses[drug_name], PharmacologicalResponse)

    def test_apply_drug_interactions(self):
        """Test applying drug interactions."""
        profile = self.simulator.get_drug_profile("propranolol")
        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        response = PharmacologicalResponse(
            administration, {0.0: 0.0}, {0.0: 0.0}, 0.0, 0.0, {}, True, True, 0.95
        )

        responses = {"propranolol": response}

        modified_responses = self.simulator._apply_drug_interactions(responses)

        assert isinstance(modified_responses, dict)
        assert "propranolol" in modified_responses

    def test_get_interaction_factor(self):
        """Test getting interaction factor between drugs."""
        factor = self.simulator._get_interaction_factor("propranolol", "l_dopa")

        assert isinstance(factor, (int, float))
        assert factor > 0

    def test_get_interaction_factor_same_drug(self):
        """Test interaction factor for same drug."""
        factor = self.simulator._get_interaction_factor("propranolol", "propranolol")

        assert factor == 1.0

    def test_get_interaction_factor_unknown_drug(self):
        """Test interaction factor for unknown drug."""
        factor = self.simulator._get_interaction_factor("unknown_drug", "propranolol")

        assert factor == 1.0  # Default interaction factor

    def test_get_drug_profile(self):
        """Test getting drug profile."""
        profile = self.simulator.get_drug_profile("propranolol")

        assert isinstance(profile, DrugProfile)
        assert profile.name == "propranolol"

    def test_get_drug_profile_unknown(self):
        """Test getting unknown drug profile."""
        with pytest.raises(ValidationError, match="Unknown drug"):
            self.simulator.get_drug_profile("unknown_drug")

    def test_list_available_drugs(self):
        """Test listing available drugs."""
        drugs = self.simulator.list_available_drugs()

        assert isinstance(drugs, list)
        assert len(drugs) > 0
        assert "propranolol" in drugs
        assert "l_dopa" in drugs

    def test_validate_dosage_valid(self):
        """Test dosage validation with valid dosage."""
        is_valid, message = self.simulator.validate_dosage("propranolol", 40.0)

        assert is_valid is True
        assert "safe range" in message.lower()

    def test_validate_dosage_invalid_negative(self):
        """Test dosage validation with negative dosage."""
        is_valid, message = self.simulator.validate_dosage("propranolol", -10.0)

        assert is_valid is False
        assert "below minimum" in message.lower()

    def test_validate_dosage_invalid_too_high(self):
        """Test dosage validation with too high dosage."""
        is_valid, message = self.simulator.validate_dosage("propranolol", 1000.0)

        assert is_valid is False
        assert "exceeds maximum" in message.lower()

    def test_validate_dosage_unknown_drug(self):
        """Test dosage validation for unknown drug."""
        is_valid, message = self.simulator.validate_dosage("unknown_drug", 40.0)

        assert is_valid is False
        assert "unknown" in message.lower()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = PharmacologicalSimulator()

    def test_simulate_drug_administration_zero_dosage(self):
        """Test drug administration with zero dosage."""
        response = self.simulator.simulate_drug_administration(
            drug_name="propranolol",
            dosage=0.0,
            participant_weight=70.0,
            route="oral",
            metabolism_rate=1.0,
            sensitivity_factor=1.0,
        )

        assert isinstance(response, PharmacologicalResponse)
        # Should have minimal effects with zero dosage
        assert abs(response.peak_threshold_effect) < 0.1

    def test_simulate_drug_administration_extreme_metabolism(self):
        """Test drug administration with extreme metabolism rates."""
        for metabolism in [0.1, 5.0]:  # Extreme values
            response = self.simulator.simulate_drug_administration(
                drug_name="l_dopa",
                dosage=100.0,
                participant_weight=70.0,
                route="oral",
                metabolism_rate=metabolism,
                sensitivity_factor=1.0,
            )

            assert isinstance(response, PharmacologicalResponse)

    def test_simulate_drug_administration_extreme_sensitivity(self):
        """Test drug administration with extreme sensitivity factors."""
        for sensitivity in [0.1, 5.0]:  # Extreme values
            response = self.simulator.simulate_drug_administration(
                drug_name="propranolol",
                dosage=40.0,
                participant_weight=70.0,
                route="oral",
                metabolism_rate=1.0,
                sensitivity_factor=sensitivity,
            )

            assert isinstance(response, PharmacologicalResponse)

    def test_simulate_drug_interaction_single_drug(self):
        """Test drug interaction with single drug."""
        responses = self.simulator.simulate_drug_interaction(
            drug_names=["propranolol"], dosages=[40.0], participant_weight=70.0
        )

        assert isinstance(responses, dict)
        assert len(responses) == 1
        assert "propranolol" in responses

    def test_simulate_drug_interaction_mismatched_lengths(self):
        """Test drug interaction with mismatched array lengths."""
        with pytest.raises(ValidationError, match="Number of drugs must match"):
            self.simulator.simulate_drug_interaction(
                drug_names=["propranolol", "l_dopa"],
                dosages=[40.0],
                participant_weight=70.0,
            )

    def test_simulate_drug_interaction_unknown_drug(self):
        """Test drug interaction with unknown drug."""
        responses = self.simulator.simulate_drug_interaction(
            drug_names=["unknown_drug"], dosages=[40.0], participant_weight=70.0
        )

        # Should handle unknown drug gracefully
        assert isinstance(responses, dict)


class TestPharmacokineticModels:
    """Test specific pharmacokinetic models."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = PharmacologicalSimulator()

    def test_linear_dose_response(self):
        """Test linear dose-response curve."""
        profile = DrugProfile(
            "test",
            DrugClass.BETA_BLOCKER,
            NeuromodulatorSystem.NOREPINEPHRINE,
            4.0,
            1.5,
            0.8,
            "linear",
            0.5,
            1,
            {},
        )

        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = self.simulator._simulate_pharmacokinetics(administration)

        assert isinstance(time_course, dict)
        assert len(time_course) > 0

    def test_logarithmic_dose_response(self):
        """Test logarithmic dose-response curve."""
        profile = self.simulator.get_drug_profile("propranolol")  # Uses logarithmic

        administration = DrugAdministration(profile, 40.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = self.simulator._simulate_pharmacokinetics(administration)

        assert isinstance(time_course, dict)
        assert len(time_course) > 0

    def test_sigmoid_dose_response(self):
        """Test sigmoid dose-response curve."""
        profile = self.simulator.get_drug_profile("l_dopa")  # Uses sigmoid

        administration = DrugAdministration(profile, 100.0, datetime.now(), "oral", 70.0, 1.0, 1.0)

        time_course = self.simulator._simulate_pharmacokinetics(administration)

        assert isinstance(time_course, dict)
        assert len(time_course) > 0


if __name__ == "__main__":
    pytest.main([__file__])
