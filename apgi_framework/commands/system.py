import argparse
import sys
from typing import Any, Dict

from apgi_framework.commands.base import BaseCommand


class ValidateSystemCommand(BaseCommand):
    """Handles system validation."""

    def execute(self, args: argparse.Namespace) -> None:
        if not self.controller:
            self.logger.error("Controller not initialized")
            return

        self.logger.info("Validating system components...")
        try:
            validation_results = self.controller.run_system_validation()
            if args.detailed:
                self._display_detailed_validation(validation_results)
            else:
                self._display_simple_validation(validation_results)

            if not validation_results.get("overall", False):
                sys.exit(1)
        except (RuntimeError, ValueError, KeyError) as e:
            self.logger.error(f"System validation failed: {e}")
            sys.exit(1)

    def _display_detailed_validation(self, results: Dict[str, Any]) -> None:
        for component, status in results.items():
            if component != "overall":
                self.logger.info(
                    f"{component.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}"
                )
        self.logger.info(f"Overall Status: {'PASS' if results.get('overall', False) else 'FAIL'}")

    def _display_simple_validation(self, results: Dict[str, Any]) -> None:
        self.logger.info(
            f"System Validation: {'PASS' if results.get('overall', False) else 'FAIL'}"
        )


class StatusCommand(BaseCommand):
    """Handles showing system status."""

    def execute(self, args: argparse.Namespace) -> None:
        if not self.controller:
            self.logger.error("Controller not initialized")
            return

        try:
            status = self.controller.get_system_status()
            self._display_system_status(status)
        except (RuntimeError, AttributeError) as e:
            self.logger.error(f"Failed to get system status: {e}")
            sys.exit(1)

    def _display_system_status(self, status: Dict[str, Any]) -> None:
        self.logger.info(f"\n{'=' * 50}")
        self.logger.info("APGI Framework System Status")
        self.logger.info(f"{'=' * 50}")
        for key, value in status.items():
            if key != "timestamp":
                display_value = "YES" if value else "NO" if isinstance(value, bool) else str(value)
                self.logger.info(f"{key.replace('_', ' ').title()}: {display_value}")
        self.logger.info(f"Last Updated: {status.get('timestamp', 'Unknown')}")
        self.logger.info(f"{'=' * 50}\n")
