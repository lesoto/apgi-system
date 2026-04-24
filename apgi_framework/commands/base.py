import argparse
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from apgi_framework.main_controller import MainApplicationController


class BaseCommand(ABC):
    """Base class for all CLI commands."""

    def __init__(self, controller: Optional[MainApplicationController] = None):
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_controller(self, controller: MainApplicationController):
        self.controller = controller

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Execute the command logic."""
        pass

    def _display_test_result(self, result: Any, test_type: str) -> None:
        """Display individual test result."""
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"APGI Framework Test Results: {test_type.upper()}")
        self.logger.info(f"{'=' * 60}")

        if hasattr(result, "is_falsified"):
            self.logger.info(
                f"Falsification Status: {'FALSIFIED' if result.is_falsified else 'NOT FALSIFIED'}"
            )
            self.logger.info(f"Confidence Level: {result.confidence_level:.3f}")
            self.logger.info(f"Effect Size: {result.effect_size:.3f}")
            self.logger.info(f"P-value: {result.p_value:.6f}")
            self.logger.info(f"Statistical Power: {result.statistical_power:.3f}")
        else:
            self.logger.info(f"Result: {result}")

        self.logger.info(f"{'=' * 60}\n")

    def _save_test_result(self, result: Any, test_type: str) -> None:
        """Save individual test result to file."""
        try:
            if self.controller is None:
                self.logger.warning("Controller not initialized, skipping save")
                return
            output_dir = Path(
                self.controller.config_manager.get_experimental_config().output_directory
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"{test_type}_result_{timestamp}.json"

            # Convert result to dictionary for JSON serialization
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__
            else:
                result_dict = {"result": str(result)}

            with open(filename, "w") as f:
                json.dump(result_dict, f, indent=2, default=str)

            self.logger.info(f"Results saved to {filename}")

        except (IOError, OSError, ValueError, TypeError) as e:
            self.logger.warning(f"Failed to save results: {e}")
