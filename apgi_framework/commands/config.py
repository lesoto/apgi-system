import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from apgi_framework.commands.base import BaseCommand


class GenerateConfigCommand(BaseCommand):
    """Handles generating configuration files."""

    def execute(self, args: argparse.Namespace) -> None:
        self.logger.info(f"Generating {args.template} configuration file: {args.output}")

        try:
            if args.template == "minimal":
                config_data = self._create_minimal_config()
            elif args.template == "comprehensive":
                config_data = self._create_comprehensive_config()
            else:  # default
                config_data = self._create_default_config()

            # Create output directory if needed
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)

            # Save configuration
            with open(args.output, "w") as f:
                json.dump(config_data, f, indent=2)

            self.logger.info(f"Configuration saved to {args.output}")

        except (IOError, OSError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to generate configuration: {e}")
            sys.exit(1)

    def _create_default_config(self) -> Dict[str, Any]:
        return {
            "apgi_parameters": {
                "extero_precision": 2.0,
                "intero_precision": 1.5,
                "extero_error": 1.2,
                "intero_error": 0.8,
                "somatic_gain": 1.3,
                "threshold": 3.5,
                "steepness": 2.0,
            },
            "experimental_config": {
                "n_trials": 1000,
                "n_participants": 100,
                "random_seed": None,
                "output_directory": "results",
                "log_level": "INFO",
                "save_intermediate": True,
                "p3b_threshold": 5.0,
                "gamma_plv_threshold": 0.3,
                "bold_z_threshold": 3.1,
                "pci_threshold": 0.4,
                "alpha_level": 0.05,
                "effect_size_threshold": 0.5,
                "power_threshold": 0.8,
            },
        }

    def _create_minimal_config(self) -> Dict[str, Any]:
        return {
            "apgi_parameters": {"threshold": 3.5, "steepness": 2.0},
            "experimental_config": {"n_trials": 100, "output_directory": "results"},
        }

    def _create_comprehensive_config(self) -> Dict[str, Any]:
        config = self._create_default_config()
        config["experimental_config"].update(
            {
                "detailed_logging": True,
                "save_raw_data": True,
                "generate_plots": True,
                "statistical_corrections": ["fdr", "bonferroni"],
                "bootstrap_iterations": 10000,
                "confidence_interval": 0.95,
            }
        )
        return config


class SetParamsCommand(BaseCommand):
    """Handles setting APGI parameters."""

    def execute(self, args: argparse.Namespace) -> None:
        if not self.controller:
            self.logger.error("Controller not initialized")
            return

        try:
            updates = {}
            if args.extero_precision is not None:
                updates["extero_precision"] = args.extero_precision
            if args.intero_precision is not None:
                updates["intero_precision"] = args.intero_precision
            if args.threshold is not None:
                updates["threshold"] = args.threshold
            if args.steepness is not None:
                updates["steepness"] = args.steepness
            if args.somatic_gain is not None:
                updates["somatic_gain"] = args.somatic_gain

            if updates:
                self.controller.config_manager.update_apgi_parameters(**updates)
                self.logger.info(f"Updated parameters: {updates}")
            else:
                self.logger.warning("No parameters specified to update")

        except (RuntimeError, ValueError, TypeError) as e:
            self.logger.error(f"Failed to set parameters: {e}")
            sys.exit(1)
