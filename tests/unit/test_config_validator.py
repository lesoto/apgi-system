"""
Unit tests for configuration validator.
"""

import pytest

from apgi_framework.config_validator import (
    ConfigValidationError,
    ConfigValidator,
    validate_config_file,
)


class TestConfigValidator:
    """Unit tests for ConfigValidator class."""

    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = ConfigValidator()
        assert validator.schema is not None
        assert "system" in validator.schema
        assert "ignition" in validator.schema

    def test_validate_valid_minimal_config(self):
        """Test validation of minimal valid configuration."""
        validator = ConfigValidator()
        config = {
            "system": {"timestep_ms": 1.0},
            "hierarchy": {"num_levels": 4, "level_configs": []},
            "active_inference": {
                "learning_rate": 0.01,
                "precision_init": 1.0,
                "precision_range": [0.1, 10.0],
                "free_energy_threshold": 100.0,
            },
            "predictive_processing": {
                "prediction_horizon_ms": 200.0,
                "error_accumulation_window_ms": 100.0,
                "temporal_discount": 0.95,
            },
            "precision": {
                "exteroceptive_baseline": 1.0,
                "interoceptive_baseline": 0.8,
                "attention_gain_range": [0.5, 3.0],
                "volatility_sensitivity": 0.1,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "amplification_duration_ms": 300.0,
                "refractory_period_ms": 200.0,
                "workspace_nodes": 1000,
            },
            "interoception": {
                "body_states": [],
                "prediction_lead_ms": 100.0,
                "allostatic_ranges": {},
            },
            "somatic_markers": {
                "capacity": 10000,
                "learning_rate": 0.05,
                "decay_rate": 0.001,
                "retrieval_threshold": 0.3,
                "gain_modulation_range": [0.5, 2.0],
            },
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 20.0,
                "ignition_cost": 7.5,
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            },
        }

        # Should not raise
        validator.validate(config)

    def test_validate_missing_required_section(self):
        """Test that missing required section raises error."""
        validator = ConfigValidator()
        config = {
            "system": {"timestep_ms": 1.0}
            # Missing other required sections
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "Missing required section" in str(exc_info.value)

    def test_validate_missing_required_field(self):
        """Test that missing required field raises error."""
        validator = ConfigValidator()
        config = {
            "system": {},  # Missing timestep_ms
            "hierarchy": {"num_levels": 4, "level_configs": []},
            "active_inference": {
                "learning_rate": 0.01,
                "precision_init": 1.0,
                "precision_range": [0.1, 10.0],
                "free_energy_threshold": 100.0,
            },
            "predictive_processing": {
                "prediction_horizon_ms": 200.0,
                "error_accumulation_window_ms": 100.0,
                "temporal_discount": 0.95,
            },
            "precision": {
                "exteroceptive_baseline": 1.0,
                "interoceptive_baseline": 0.8,
                "attention_gain_range": [0.5, 3.0],
                "volatility_sensitivity": 0.1,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "amplification_duration_ms": 300.0,
                "refractory_period_ms": 200.0,
                "workspace_nodes": 1000,
            },
            "interoception": {
                "body_states": [],
                "prediction_lead_ms": 100.0,
                "allostatic_ranges": {},
            },
            "somatic_markers": {
                "capacity": 10000,
                "learning_rate": 0.05,
                "decay_rate": 0.001,
                "retrieval_threshold": 0.3,
                "gain_modulation_range": [0.5, 2.0],
            },
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 20.0,
                "ignition_cost": 7.5,
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            },
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "timestep_ms" in str(exc_info.value)

    def test_validate_out_of_range_value(self):
        """Test that out of range value raises error."""
        validator = ConfigValidator()
        config = {
            "system": {"timestep_ms": 1000.0},  # Out of range (max 100.0)
            "hierarchy": {"num_levels": 4, "level_configs": []},
            "active_inference": {
                "learning_rate": 0.01,
                "precision_init": 1.0,
                "precision_range": [0.1, 10.0],
                "free_energy_threshold": 100.0,
            },
            "predictive_processing": {
                "prediction_horizon_ms": 200.0,
                "error_accumulation_window_ms": 100.0,
                "temporal_discount": 0.95,
            },
            "precision": {
                "exteroceptive_baseline": 1.0,
                "interoceptive_baseline": 0.8,
                "attention_gain_range": [0.5, 3.0],
                "volatility_sensitivity": 0.1,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "amplification_duration_ms": 300.0,
                "refractory_period_ms": 200.0,
                "workspace_nodes": 1000,
            },
            "interoception": {
                "body_states": [],
                "prediction_lead_ms": 100.0,
                "allostatic_ranges": {},
            },
            "somatic_markers": {
                "capacity": 10000,
                "learning_rate": 0.05,
                "decay_rate": 0.001,
                "retrieval_threshold": 0.3,
                "gain_modulation_range": [0.5, 2.0],
            },
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 20.0,
                "ignition_cost": 7.5,
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            },
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "out of range" in str(exc_info.value)

    def test_validate_wrong_type(self):
        """Test that wrong type raises error."""
        validator = ConfigValidator()
        config = {
            "system": {"timestep_ms": "1.0"},  # Should be numeric, not string
            "hierarchy": {"num_levels": 4, "level_configs": []},
            "active_inference": {
                "learning_rate": 0.01,
                "precision_init": 1.0,
                "precision_range": [0.1, 10.0],
                "free_energy_threshold": 100.0,
            },
            "predictive_processing": {
                "prediction_horizon_ms": 200.0,
                "error_accumulation_window_ms": 100.0,
                "temporal_discount": 0.95,
            },
            "precision": {
                "exteroceptive_baseline": 1.0,
                "interoceptive_baseline": 0.8,
                "attention_gain_range": [0.5, 3.0],
                "volatility_sensitivity": 0.1,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "amplification_duration_ms": 300.0,
                "refractory_period_ms": 200.0,
                "workspace_nodes": 1000,
            },
            "interoception": {
                "body_states": [],
                "prediction_lead_ms": 100.0,
                "allostatic_ranges": {},
            },
            "somatic_markers": {
                "capacity": 10000,
                "learning_rate": 0.05,
                "decay_rate": 0.001,
                "retrieval_threshold": 0.3,
                "gain_modulation_range": [0.5, 2.0],
            },
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 20.0,
                "ignition_cost": 7.5,
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            },
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "wrong type" in str(exc_info.value)

    def test_validate_invalid_range_list(self):
        """Test that invalid range (min >= max) raises error."""
        validator = ConfigValidator()
        config = {
            "system": {"timestep_ms": 1.0},
            "hierarchy": {"num_levels": 4, "level_configs": []},
            "active_inference": {
                "learning_rate": 0.01,
                "precision_init": 1.0,
                "precision_range": [10.0, 0.1],  # Invalid: min > max
                "free_energy_threshold": 100.0,
            },
            "predictive_processing": {
                "prediction_horizon_ms": 200.0,
                "error_accumulation_window_ms": 100.0,
                "temporal_discount": 0.95,
            },
            "precision": {
                "exteroceptive_baseline": 1.0,
                "interoceptive_baseline": 0.8,
                "attention_gain_range": [0.5, 3.0],
                "volatility_sensitivity": 0.1,
            },
            "ignition": {
                "baseline_threshold": 2.0,
                "threshold_range": [1.0, 5.0],
                "sigmoid_alpha": 5.0,
                "amplification_duration_ms": 300.0,
                "refractory_period_ms": 200.0,
                "workspace_nodes": 1000,
            },
            "interoception": {
                "body_states": [],
                "prediction_lead_ms": 100.0,
                "allostatic_ranges": {},
            },
            "somatic_markers": {
                "capacity": 10000,
                "learning_rate": 0.05,
                "decay_rate": 0.001,
                "retrieval_threshold": 0.3,
                "gain_modulation_range": [0.5, 2.0],
            },
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 20.0,
                "ignition_cost": 7.5,
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            },
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            validator.validate(config)

        assert "range invalid" in str(exc_info.value)

    def test_validate_parameter_ranges_thermodynamic_warning(self):
        """Test thermodynamic consistency warnings."""
        validator = ConfigValidator()
        config = {
            "thermodynamic": {
                "total_energy_budget": 100.0,
                "baseline_consumption": 60.0,
                "ignition_cost": 50.0,  # Total exceeds budget
                "recovery_rate": 5.0,
                "depletion_threshold": 10.0,
            }
        }

        warnings = validator.validate_parameter_ranges(config)
        assert len(warnings) > 0
        assert any("baseline_consumption" in w and "ignition_cost" in w for w in warnings)

    def test_suggest_fixes(self):
        """Test that suggest_fixes provides helpful suggestions."""
        validator = ConfigValidator()
        config = {
            "active_inference": {
                "precision_init": 15.0,  # Outside range
                "precision_range": [0.1, 10.0],
            },
            "thermodynamic": {
                "total_energy_budget": 50.0,
                "baseline_consumption": 40.0,
                "ignition_cost": 20.0,  # Exceeds budget
            },
        }

        suggestions = validator.suggest_fixes(config)
        assert len(suggestions) > 0
        assert (
            "active_inference.precision_init" in suggestions
            or "thermodynamic.total_energy_budget" in suggestions
        )

    def test_get_common_mistakes_help(self):
        """Test that help text is available."""
        validator = ConfigValidator()
        help_text = validator.get_common_mistakes_help()
        assert len(help_text) > 0
        assert "Common Configuration Mistakes" in help_text

    def test_validate_config_file_with_default(self):
        """Test validating the default configuration file."""
        # Should not raise
        validate_config_file("config/default.yaml")
