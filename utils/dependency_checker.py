#!/usr/bin/env python3
"""
APGI System Dependency Checker

This module provides utilities to check for required dependencies
at startup and provide helpful installation instructions.

Usage:
    python dependency_checker.py
    python dependency_checker.py --install-missing
    python dependency_checker.py --core-only
"""

import importlib
import importlib.metadata
import subprocess
import sys
from typing import Any, Dict, Optional, Tuple

from packaging import version

# Core dependencies with version requirements
CORE_DEPENDENCIES = {
    "numpy": {"min_version": "1.20.0", "description": "Numerical computing"},
    "scipy": {"min_version": "1.7.0", "description": "Scientific computing"},
    "matplotlib": {"min_version": "3.5.0", "description": "Plotting and visualization"},
    "pandas": {"min_version": "1.3.0", "description": "Data manipulation"},
    "torch": {"min_version": "1.10.0", "description": "Deep learning"},
    "customtkinter": {"min_version": "5.0.0", "description": "GUI framework"},
    "numba": {"min_version": "0.55.0", "description": "Just-In-Time compiler"},
    "h5py": {"min_version": "3.6.0", "description": "HDF5 file handling"},
    "statsmodels": {"min_version": "0.13.0", "description": "Statistical modeling"},
    "flask": {"min_version": "2.0.0", "description": "Web framework"},
    "flask_socketio": {
        "min_version": "5.1.0",
        "description": "Real-time web framework",
    },
    "pytest": {"min_version": "7.0.0", "description": "Testing framework"},
    "jupyter": {"min_version": "1.0.0", "description": "Interactive computing"},
    "streamlit": {"min_version": "1.0.0", "description": "Data science web framework"},
    "psutil": {"min_version": "5.8.0", "description": "System monitoring"},
    "requests": {"min_version": "2.28.0", "description": "HTTP requests"},
}

# Optional dependencies with version requirements
OPTIONAL_DEPENDENCIES = {
    "pyautogui": {
        "min_version": "0.9.50",
        "description": "Cross-platform GUI automation",
    },
    "pygetwindow": {
        "min_version": "0.0.9",
        "description": "Cross-platform window management",
    },
    "PIL": {"min_version": "9.0.0", "description": "Image processing"},
    "cv2": {"min_version": "4.5.5", "description": "Computer vision"},
    "scikit-learn": {"min_version": "1.0.0", "description": "Machine learning"},
    "seaborn": {"min_version": "0.11.2", "description": "Data visualization"},
    "plotly": {
        "min_version": "5.10.0",
        "description": "Interactive data visualization",
    },
    "mne": {"min_version": "1.0.0", "description": "MEG/EEG analysis"},
    "nibabel": {"min_version": "3.2.2", "description": "Neuroimaging data handling"},
    "torchvision": {
        "min_version": "0.11.0",
        "description": "Deep learning computer vision",
    },
    "torchaudio": {
        "min_version": "0.11.0",
        "description": "Deep learning audio processing",
    },
    "memory-profiler": {"min_version": "0.60.0", "description": "Memory profiling"},
    "line-profiler": {"min_version": "3.0.0", "description": "Line profiling"},
    "sphinx": {"min_version": "4.0.0", "description": "Documentation generation"},
    "PySide6": {"min_version": "6.0.0", "description": "GUI framework"},
    "black": {"min_version": "22.0.0", "description": "Code formatting"},
    "flake8": {"min_version": "5.0.0", "description": "Linting"},
    "mypy": {"min_version": "1.0.0", "description": "Type checking"},
    "tensorflow": {"min_version": "2.8.0", "description": "Deep learning"},
    "toml": {"min_version": "0.10.0", "description": "TOML file parsing"},
    "weasyprint": {"min_version": "54.0", "description": "PDF generation"},
    "jinja2": {"min_version": "3.0.0", "description": "Template engine"},
    "psutil": {"min_version": "5.8.0", "description": "System monitoring"},
}


def install_package(package_name: str, min_version: Optional[str] = None) -> bool:
    """Install a package using pip, optionally with version requirement."""
    try:
        if min_version:
            package_spec = f"{package_name}>={min_version}"
            print(f"Installing {package_spec}...")
        else:
            package_spec = package_name
            print(f"Installing {package_name}...")

        # Try different installation methods for externally managed environments
        install_commands = [
            [sys.executable, "-m", "pip", "install", "--user", package_spec],
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--break-system-packages",
                package_spec,
            ],
            [sys.executable, "-m", "pip", "install", package_spec],
        ]

        for cmd in install_commands:
            try:
                subprocess.check_call(cmd)
                print(f"✅ Successfully installed {package_spec}")
                return True
            except subprocess.CalledProcessError as e:
                if "externally-managed-environment" in str(e):
                    continue  # Try next method
                else:
                    raise e

        # If all methods failed, provide guidance
        print(f"❌ Failed to install {package_name}")
        print("\n💡 Installation Options:")
        print("   1. Create virtual environment:")
        print("      python3 -m venv venv")
        print("      source venv/bin/activate")
        print(f"      pip install {package_spec}")
        print("   2. Use Homebrew (if available):")
        print(f"      brew install {package_name}")
        print("   3. Use pipx (for Python applications):")
        print(f"      pipx install {package_name}")

        return False

    except Exception as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False


def check_version_compatibility(
    package_name: str, min_version: str
) -> Tuple[bool, str, Optional[str]]:
    """Check if a package meets minimum version requirements.

    Returns:
        Tuple of (is_compatible, current_version, error_message)
    """
    try:
        installed_version = importlib.metadata.version(package_name)
        if version.parse(installed_version) >= version.parse(min_version):
            return True, installed_version, None
        else:
            return (
                False,
                installed_version,
                f"Version {installed_version} is below minimum {min_version}",
            )
    except importlib.metadata.PackageNotFoundError:
        return False, "", "Package not installed"
    except Exception as e:
        return False, "", f"Error checking version: {e}"


def check_import(package_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a package can be imported."""
    try:
        importlib.import_module(package_name)
        return True, "✓ Successfully imported"
    except ImportError as e:
        return False, f"✗ Import failed: {e}"
    except Exception as e:
        return False, f"✗ Error: {e}"


def check_dependency(
    package_name: str, version_info: Dict[str, str]
) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """Check a dependency with version compatibility."""
    is_available, message = check_import(package_name)
    if is_available:
        is_compatible, current_version, error = check_version_compatibility(
            package_name, version_info["min_version"]
        )
        if is_compatible:
            return True, "✓", current_version, None
        else:
            return False, "⚠️", current_version, error
    else:
        return False, "✗", None, message


def check_core_dependencies() -> Dict[str, Tuple[bool, str, Optional[str], Optional[str]]]:
    """Check all core dependencies with version compatibility."""
    results = {}
    print("Checking core dependencies:")
    print("-" * 50)

    for package_name, version_info in CORE_DEPENDENCIES.items():
        is_available, status, current_version, error = check_dependency(package_name, version_info)
        results[package_name] = (is_available, status, current_version, error)
        print(f"  {status} {package_name:<20} {version_info['description']}")
        if error:
            print(f"    ⚠️  {error}")

    return results


def check_optional_dependencies() -> Dict[str, Tuple[bool, str, Optional[str], Optional[str]]]:
    """Check all optional dependencies with version compatibility."""
    results = {}
    print("Checking optional dependencies:")
    print("-" * 50)

    for package_name, version_info in OPTIONAL_DEPENDENCIES.items():
        is_available, status, current_version, error = check_dependency(package_name, version_info)
        results[package_name] = (is_available, status, current_version, error)
        print(f"  {status} {package_name:<20} {version_info['description']}")
        if error:
            print(f"    ⚠️  {error}")

    return results


def generate_summary(
    core_results: Dict[str, Tuple[bool, str, Optional[str], Optional[str]]],
    optional_results: Dict[str, Tuple[bool, str, Optional[str], Optional[str]]],
) -> Dict[str, Any]:
    """Generate a summary of dependency check results."""
    core_available = sum(1 for is_available, _, _, _ in core_results.values() if is_available)
    core_total = len(core_results)

    optional_available = sum(
        1 for is_available, _, _, _ in optional_results.values() if is_available
    )
    optional_total = len(optional_results)

    # Collect version information
    version_issues = []
    all_results = {**core_results, **optional_results}

    for package_name, (is_available, _, current_version, error) in all_results.items():
        if error and "Version" in error:
            version_issues.append(
                {
                    "package": package_name,
                    "current_version": current_version,
                    "error": error,
                }
            )

    return {
        "core_dependencies": {
            "available": core_available,
            "total": core_total,
            "percentage": (core_available / core_total) * 100 if core_total > 0 else 0,
        },
        "optional_dependencies": {
            "available": optional_available,
            "total": optional_total,
            "percentage": (
                (optional_available / optional_total) * 100 if optional_total > 0 else 0
            ),
        },
        "version_issues": version_issues,
        "overall_status": ("ready" if core_available == core_total else "needs_attention"),
    }


def check_dependencies(install_missing=False, core_only=False) -> Dict[str, Any]:
    """Check all dependencies and return results."""
    core_results = check_core_dependencies()

    if install_missing:
        # Install missing core dependencies
        for package_name, (is_available, _, _, error) in core_results.items():
            if not is_available:
                min_version = CORE_DEPENDENCIES[package_name].get("min_version")
                if not install_package(package_name, min_version):
                    print(f"❌ Failed to install required dependency: {package_name}")

        # Re-check after installation
        print("\nRe-checking dependencies after installation...")
        core_results = check_core_dependencies()

    if not core_only:
        optional_results = check_optional_dependencies()

        if install_missing:
            # Install missing optional dependencies
            for package_name, (is_available, _, _, error) in optional_results.items():
                if not is_available:
                    min_version = OPTIONAL_DEPENDENCIES[package_name].get("min_version")
                    install_package(package_name, min_version)

        # Generate and display summary
        summary = generate_summary(core_results, optional_results)

        print("\n" + "=" * 60)
        print("DEPENDENCY CHECK SUMMARY")
        print("=" * 60)

        # Type ignore for dynamic dictionary access
        print(
            f"Core dependencies: {summary['core_dependencies']['available']}/{summary['core_dependencies']['total']} ({summary['core_dependencies']['percentage']:.1f}%)"
        )
        print(
            f"Optional dependencies: {summary['optional_dependencies']['available']}/{summary['optional_dependencies']['total']} ({summary['optional_dependencies']['percentage']:.1f}%)"
        )
        print(f"Overall status: {summary['overall_status']}")

        if summary["version_issues"]:
            print("\n⚠️  Version Issues Found:")
            for issue in summary["version_issues"]:
                print(f"  • {issue['package']}: {issue['error']}")
                print(f"    Current: {issue['current_version']}, Update required")

        if summary["overall_status"] == "ready":
            print("\n🎉 All dependencies are satisfied!")
        else:
            print("\n⚠️  Some dependencies need attention.")

            # Only show installation suggestions for missing core dependencies
            missing_core = [
                name for name, (available, _, _, _) in core_results.items() if not available
            ]
            if missing_core:
                print("\n💡 Missing CORE dependencies (required):")
                print("   1. Auto-install missing packages:")
                print(f"      python {__file__} --install-missing")
                print("   2. Install manually with pip:")
                print("      pip install --user <package_name>")
                print("   3. Use virtual environment (recommended):")
                print("      python3 -m venv venv && source venv/bin/activate")
                print("      pip install -r requirements.txt")
            else:
                print(
                    "\n💡 All CORE dependencies satisfied. Optional packages can be installed later:"
                )
                print("   pip install --user <optional_package_name>")

                # List missing optional dependencies
                missing_optional = [
                    name for name, (available, _, _, _) in optional_results.items() if not available
                ]
                if missing_optional:
                    print("\n📦 Missing OPTIONAL dependencies:")
                    for package in missing_optional:
                        desc = OPTIONAL_DEPENDENCIES[package]["description"]
                        min_ver = OPTIONAL_DEPENDENCIES[package]["min_version"]
                        print(f"  • {package} (>= {min_ver}) - {desc}")
                        print(f"    pip install --user '{package}>={min_ver}'")
    else:
        print("\nOPTIONAL DEPENDENCIES - SKIPPED (core-only mode)")
        summary = generate_summary(core_results, {})

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check APGI Framework dependencies")
    parser.add_argument(
        "--install-missing", action="store_true", help="Install missing dependencies"
    )
    parser.add_argument("--core-only", action="store_true", help="Check only core dependencies")

    args = parser.parse_args()

    check_dependencies(install_missing=args.install_missing, core_only=args.core_only)
