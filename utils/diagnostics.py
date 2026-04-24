#!/usr/bin/env python3
"""
APGI Framework Diagnostics Tool

This script performs comprehensive diagnostics on the APGI Framework
installation, checking system requirements, dependencies, and configuration.

Usage:
    python tools/diagnostics.py [options]

Examples:
    python tools/diagnostics.py                # Full diagnostics
    python tools/diagnostics.py --quick        # Quick health check
    python tools/diagnostics.py --deps         # Check dependencies only
    python tools/diagnostics.py --config       # Check configuration
"""

import importlib
import json
import platform
import sys
from pathlib import Path
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class APGIDiagnostics:
    """Comprehensive diagnostics for APGI Framework."""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []

    def log_issue(self, message: str):
        """Log a critical issue."""
        self.issues.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str):
        """Log a warning."""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_pass(self, message: str):
        """Log a passed check."""
        self.passed.append(message)
        print(f"✅ {message}")

    def check_python_version(self):
        """Check Python version compatibility."""
        version = sys.version_info
        if version >= (3, 8):
            self.log_pass(f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
        else:
            self.log_issue(
                f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+"
            )

    def check_dependencies(self):
        """Check required and optional dependencies."""
        required_deps = [
            "numpy",
            "scipy",
            "matplotlib",
            "pandas",
        ]

        optional_deps = [
            "scikit-learn",
            "customtkinter",
            "flask",
            "flask-socketio",
            "pytest",
            "tkinter",
        ]

        print("\n🔍 Checking dependencies...")

        for dep in required_deps:
            try:
                importlib.import_module(dep)
                self.log_pass(f"{dep} - Installed")
            except ImportError:
                self.log_issue(f"{dep} - Missing (required)")

        for dep in optional_deps:
            try:
                importlib.import_module(dep)
                self.log_pass(f"{dep} - Installed")
            except ImportError:
                self.log_warning(f"{dep} - Missing (optional)")

    def check_apgi_framework(self):
        """Check APGI Framework components."""
        print("\n🏗️  Checking APGI Framework...")

        components = [
            "apgi_framework",
            "apgi_framework.config",
            "apgi_framework.analysis.analysis_engine",
            "apgi_framework.logging.standardized_logging",
        ]

        for component in components:
            try:
                importlib.import_module(component)
                self.log_pass(f"{component} - Importable")
            except ImportError as e:
                self.log_issue(f"{component} - Import failed: {e}")

    def check_system_requirements(self):
        """Check system requirements."""
        print("\n💻 Checking system requirements...")

        # Check OS
        os_name = platform.system()
        if os_name in ["Windows", "Linux", "Darwin"]:
            self.log_pass(f"OS: {os_name} - Supported")
        else:
            self.log_warning(f"OS: {os_name} - May have limited support")

        # Check architecture
        arch = platform.machine()
        if arch in ["x86_64", "AMD64", "arm64", "aarch64"]:
            self.log_pass(f"Architecture: {arch} - Supported")
        else:
            self.log_warning(f"Architecture: {arch} - May have compatibility issues")

        # Check memory (rough estimate)
        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            if memory_gb >= 4:
                self.log_pass(f"Memory: {memory_gb:.1f} GB - Sufficient")
            else:
                self.log_warning(f"Memory: {memory_gb:.1f} GB - Insufficient (4GB recommended)")
        except ImportError:
            self.log_warning("Memory check unavailable (install psutil for detailed info)")

    def check_configuration(self):
        """Check configuration files and settings."""
        print("\n⚙️  Checking configuration...")

        config_files = [
            "apgi_framework/config/constants.py",
            "apgi_framework/config/config_manager.py",
            "pyproject.toml",
            "requirements.txt",
        ]

        for config_file in config_files:
            path = Path(__file__).parent.parent / config_file
            if path.exists():
                self.log_pass(f"{config_file} - Exists")
            else:
                self.log_warning(f"{config_file} - Missing")

    def check_tests(self):
        """Check test suite availability."""
        print("\n🧪 Checking test suite...")

        test_dirs = ["tests"]
        test_files = []

        for test_dir in test_dirs:
            path = Path(__file__).parent.parent / test_dir
            if path.exists() and path.is_dir():
                py_files = list(path.rglob("test_*.py"))
                test_files.extend(py_files)
                self.log_pass(f"{test_dir}/ - {len(py_files)} test files")
            else:
                self.log_warning(f"{test_dir}/ - Directory missing")

        if test_files:
            self.log_pass(f"Total test files: {len(test_files)}")
        else:
            self.log_warning("No test files found")

    def generate_report(self) -> Dict:
        """Generate diagnostic report."""
        return {
            "timestamp": str(Path(__file__).parent.parent.stat().st_mtime),
            "python_version": (
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            ),
            "platform": platform.platform(),
            "issues": len(self.issues),
            "warnings": len(self.warnings),
            "passed": len(self.passed),
            "details": {
                "issues": self.issues,
                "warnings": self.warnings,
                "passed": self.passed,
            },
        }

    def run_full_diagnostics(self):
        """Run complete diagnostic suite."""
        print("🔬 APGI Framework Diagnostics")
        print("=" * 50)

        self.check_python_version()
        self.check_system_requirements()
        self.check_dependencies()
        self.check_apgi_framework()
        self.check_configuration()
        self.check_tests()

        print("\n📊 Summary")
        print("=" * 50)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Issues: {len(self.issues)}")

        if self.issues:
            print("\n🔧 Critical Issues (must fix):")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print("\n💡 Recommendations:")
            for warning in self.warnings:
                print(f"  • {warning}")

        return len(self.issues) == 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="APGI Framework Diagnostics Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--quick", action="store_true", help="Run quick health check only")

    parser.add_argument("--deps", action="store_true", help="Check dependencies only")

    parser.add_argument("--config", action="store_true", help="Check configuration only")

    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    diagnostics = APGIDiagnostics()

    if args.deps:
        diagnostics.check_dependencies()
    elif args.config:
        diagnostics.check_configuration()
    elif args.quick:
        diagnostics.check_python_version()
        diagnostics.check_apgi_framework()
    else:
        success = diagnostics.run_full_diagnostics()

    if args.json:
        report = diagnostics.generate_report()
        print(json.dumps(report, indent=2))
    else:
        if not (args.deps or args.config or args.quick):
            success = len(diagnostics.issues) == 0
            if success:
                print("\n🎉 All diagnostics passed!")
            else:
                print(f"\n⚠️  Found {len(diagnostics.issues)} critical issues")
                sys.exit(1)


if __name__ == "__main__":
    main()
