"""
APGI System Dependency Checker

This module provides utilities to check for required dependencies
at startup and provide helpful installation instructions.
"""

import sys
import importlib
import subprocess
import platform
from typing import List, Dict, Tuple, Optional


class DependencyChecker:
    """Checks for required dependencies and provides installation guidance."""

    def __init__(self):
        self.python_version = sys.version_info
        self.platform = platform.system()
        self.errors = []
        self.warnings = []

    def check_python_version(self, min_version: Tuple[int, int] = (3, 8)) -> bool:
        """Check if Python version meets minimum requirements."""
        if self.python_version < min_version:
            self.errors.append(
                f"Python {'.'.join(map(str, min_version))}+ required, "
                f"found {'.'.join(map(str, self.python_version[:2]))}"
            )
            return False
        return True

    def check_package(self, package_name: str, import_name: Optional[str] = None) -> bool:
        """Check if a Python package is available."""
        if import_name is None:
            import_name = package_name

        try:
            importlib.import_module(import_name)
            return True
        except ImportError:
            self.errors.append(f"Missing required package: {package_name}")
            return False

    def check_system_service(self, service_name: str, test_command: List[str]) -> bool:
        """Check if a system service is running."""
        try:
            result = subprocess.run(test_command, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
            else:
                self.warnings.append(f"Service {service_name} may not be running properly")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.warnings.append(f"Service {service_name} is not available")
            return False

    def check_all_dependencies(self) -> Dict[str, bool]:
        """Check all required dependencies."""
        results = {}

        # Python version
        results["python_version"] = self.check_python_version()

        # Core scientific packages
        core_packages = [
            ("numpy", "numpy"),
            ("scipy", "scipy"),
            ("matplotlib", "matplotlib"),
            ("pandas", "pandas"),
            ("sklearn", "sklearn"),
            ("networkx", "networkx"),
            ("torch", "torch"),
            ("jax", "jax"),
        ]

        for package, import_name in core_packages:
            results[f"package_{package}"] = self.check_package(package, import_name)

        # Web framework packages
        web_packages = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("pydantic", "pydantic"),
            ("sqlalchemy", "sqlalchemy"),
            ("redis", "redis"),
            ("psycopg2", "psycopg2"),
        ]

        for package, import_name in web_packages:
            results[f"package_{package}"] = self.check_package(package, import_name)

        # GUI packages
        results["package_tkinter"] = self.check_package("tkinter", "tkinter")

        # System services
        if self.platform == "Darwin":  # macOS
            results["service_redis"] = self.check_system_service("redis", ["redis-cli", "ping"])
            results["service_postgresql"] = self.check_system_service(
                "postgresql", ["psql", "-d", "apgi_api", "-c", "SELECT 1;"]
            )
        elif self.platform == "Linux":
            results["service_redis"] = self.check_system_service("redis", ["redis-cli", "ping"])
            results["service_postgresql"] = self.check_system_service(
                "postgresql", ["psql", "-d", "apgi_api", "-c", "SELECT 1;"]
            )

        return results

    def _format_python_instructions(self, python_errors: List[str]) -> List[str]:
        """Format Python version installation instructions."""
        if not python_errors:
            return []

        instructions = [
            "\n📦 Python Version:",
        ]
        for error in python_errors:
            instructions.append(f"   ❌ {error}")
        instructions.append("   💡 Install Python 3.8+ from https://python.org")
        return instructions

    def _format_package_instructions(self, package_errors: List[str]) -> List[str]:
        """Format package installation instructions."""
        if not package_errors:
            return []

        instructions = [
            "\n📦 Python Packages:",
        ]
        for error in package_errors:
            instructions.append(f"   ❌ {error}")
        instructions.append("\n   💡 Install all packages:")
        instructions.append("      source venv/bin/activate  # Activate virtual environment")
        instructions.append("      pip install -r requirements.txt")
        instructions.append("\n   💡 Or run the automated setup:")
        instructions.append("      ./install.sh")
        return instructions

    def _format_service_instructions(self, service_warnings: List[str]) -> List[str]:
        """Format service installation instructions."""
        if not service_warnings:
            return []

        instructions = [
            "\n[TOOLS] System Services:",
        ]
        for warning in service_warnings:
            instructions.append(f"   [!] {warning}")

        instructions.append("\n   [INFO] Start services:")
        if self.platform == "Darwin":  # macOS
            instructions.append("      brew services start redis")
            instructions.append("      brew services start postgresql@14")
        elif self.platform == "Linux":
            instructions.append("      sudo systemctl start redis")
            instructions.append("      sudo systemctl start postgresql")
        return instructions

    def get_installation_instructions(self) -> str:
        """Generate helpful installation instructions."""
        instructions = []

        if self.errors:
            instructions.append("\n🔧 INSTALLATION INSTRUCTIONS:")
            instructions.append("=" * 50)

            # Python version issues
            python_errors = [e for e in self.errors if "Python" in e]
            instructions.extend(self._format_python_instructions(python_errors))

            # Missing packages
            package_errors = [e for e in self.errors if "Missing required package" in e]
            instructions.extend(self._format_package_instructions(package_errors))

        if self.warnings:
            instructions.append("\n[!] SERVICE WARNINGS:")
            instructions.append("=" * 50)

            service_warnings = [w for w in self.warnings if "Service" in w]
            instructions.extend(self._format_service_instructions(service_warnings))

        if not self.errors and not self.warnings:
            instructions.append("\n[OK] All dependencies satisfied!")

        return "\n".join(instructions)

    def _print_python_version(self, results: Dict[str, bool]):
        """Print Python version information."""
        print(f"\n[PYTHON] Python Version: {'.'.join(map(str, self.python_version[:2]))}")
        if results["python_version"]:
            print("   [OK] Meets minimum requirements (3.8+)")
        else:
            print("   [FAIL] Does not meet minimum requirements")

    def _print_package_group(self, title: str, packages: List[str], results: Dict[str, bool]):
        """Print a group of packages with their status."""
        print(f"\n{title}")
        for package in packages:
            key = f"package_{package}"
            if results.get(key, False):
                print(f"   [OK] {package}")
            else:
                print(f"   [FAIL] {package}")

    def _print_services(self, results: Dict[str, bool]):
        """Print system services status."""
        print("\n[TOOLS] System Services:")

        if "service_redis" in results:
            status = "[OK]" if results["service_redis"] else "[!]"
            note = "" if results["service_redis"] else " (may not be running)"
            print(f"   {status} Redis{note}")

        if "service_postgresql" in results:
            status = "[OK]" if results["service_postgresql"] else "[!]"
            note = "" if results["service_postgresql"] else " (may not be running)"
            print(f"   {status} PostgreSQL{note}")

    def print_dependency_report(self):
        """Print a comprehensive dependency report."""
        print("\n[SEARCH] APGI System Dependency Check")
        print("=" * 50)

        results = self.check_all_dependencies()

        # Python version
        self._print_python_version(results)

        # Core packages
        core_packages = [
            "numpy",
            "scipy",
            "matplotlib",
            "pandas",
            "sklearn",
            "networkx",
            "torch",
            "jax",
        ]
        self._print_package_group("\n[PACKAGES] Core Scientific Packages:", core_packages, results)

        # Web framework packages
        web_packages = ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "redis", "psycopg2"]
        self._print_package_group("\n[WEB] Web Framework Packages:", web_packages, results)

        # GUI packages
        gui_status = "[OK]" if results.get("package_tkinter", False) else "[FAIL]"
        print(f"\n[GUI] GUI Packages:\n   {gui_status} tkinter")

        # System services
        self._print_services(results)

        # Print instructions
        print(self.get_installation_instructions())


def check_dependencies_on_startup(silent: bool = True):
    """Check dependencies at application startup and provide guidance.

    Args:
        silent: If True, suppress verbose output (default for GUI)
    """
    checker = DependencyChecker()

    # Check if we should skip the detailed check (for quick startup)
    if "--skip-deps-check" in sys.argv:
        return True

    if not silent:
        checker.print_dependency_report()

    # If there are critical errors, show warnings (unless completely silent)
    if checker.errors and not silent:
        print("\n❌ CRITICAL ISSUES FOUND")
        print("Some dependencies are missing. The application may not work correctly.")
        print("Please follow the installation instructions above.")

        # Ask user if they want to continue
        try:
            response = input("\nContinue anyway? (y/N): ").strip().lower()
            return response in ["y", "yes"]
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return False
    elif checker.errors and silent:
        # In silent mode, log errors but don't show interactive prompt
        import logging

        logger = logging.getLogger(__name__)
        for error in checker.errors:
            logger.error(f"Dependency issue: {error}")
        return False  # Don't continue if there are critical errors

    return True


if __name__ == "__main__":
    # Run dependency check when script is executed directly
    checker = DependencyChecker()
    checker.print_dependency_report()
