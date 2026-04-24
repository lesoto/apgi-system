#!/usr/bin/env python3
"""
APGI Framework Dependency Installer
==================================

Simple script to install all required dependencies for the APGI framework.
This handles the installation of both core and optional dependencies.

Usage:
    python install_dependencies.py [--optional]
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


# Error handling classes (fallback since error_handler module may not be available)
class APGIError(Exception):
    pass


class ConfigurationError(APGIError):
    def __init__(
        self,
        message: Optional[str] = None,
        context: Optional[dict] = None,
        suggestion: Optional[str] = None,
    ):
        self.message = message or "Configuration error"
        self.context = context or {}
        self.suggestion = suggestion
        super().__init__(self.message)


class DataError(APGIError):
    pass


class ErrorSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


def format_error_message(
    error: Any, context: Optional[Any] = None, reason: Optional[str] = None
) -> str:
    if reason:
        return f"{error}: {reason}"
    if context:
        return f"{error} (context: {context})"
    return str(error)


def handle_error(error: Any, context: Optional[Any] = None) -> None:
    print(f"Error: {format_error_message(error, context)}")


def safe_execute(func: Any, *args: Any, **kwargs: Any) -> Any:
    return func(*args, **kwargs)


def run_command(command: list, description: str) -> bool:
    """Run a command and handle errors gracefully."""
    print(f"\n📦 {description}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        error = ConfigurationError(
            message=format_error_message(
                "protocol_failed",
                reason=f"Command failed with return code {e.returncode}",
            ),
            context={
                "command": command,
                "description": description,
                "return_code": e.returncode,
                "stderr": e.stderr,
            },
            suggestion="Check command syntax and system permissions",
        )
        print(f"❌ {error}")
        return False


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        error = ConfigurationError(
            message="Python 3.8+ is required for this framework",
            context={
                "current_version": f"{version.major}.{version.minor}.{version.micro}",
                "required_version": "3.8+",
            },
            suggestion="Please upgrade Python to version 3.8 or higher",
        )
        print(f"❌ {error}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_core_dependencies() -> bool:
    """Install core dependencies from requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"

    if not requirements_path.exists():
        error = DataError(format_error_message("file_not_found"))
        print(f"❌ {error}")
        return False

    print("📦 Note: This script uses --break-system-packages flag to install dependencies.")
    print("💡 For production use, consider creating a virtual environment:")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("   pip install -r requirements.txt")
    print()

    # Upgrade pip first (try multiple approaches)
    pip_upgraded = False
    try:
        # First try without --break-system-packages
        run_command(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            "Upgrading pip",
        )
        pip_upgraded = True
    except Exception:
        try:
            # If that fails, try with --break-system-packages
            run_command(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "pip",
                    "--break-system-packages",
                ],
                "Upgrading pip (with system packages override)",
            )
            pip_upgraded = True
        except Exception:
            print("⚠️  Could not upgrade pip, continuing with current version...")

    if pip_upgraded:
        print("✅ Pip upgraded successfully")
    else:
        print("ℹ️  Using existing pip version")

    # Install core requirements
    success = False
    try:
        success = run_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_path),
                "--break-system-packages",
            ],
            "Installing core dependencies",
        )
    except Exception:
        try:
            # Fallback: try without --break-system-packages
            success = run_command(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                "Installing core dependencies (fallback)",
            )
        except Exception:
            print("❌ Failed to install core dependencies")
            return False

    return success


def install_optional_dependencies() -> None:
    """Install optional dependencies for enhanced functionality."""
    optional_packages = [
        "jupyter>=1.0.0",
        "ipykernel>=6.0.0",
        "notebook>=6.0.0",
        "ipywidgets>=7.6.0",
    ]

    for package in optional_packages:
        run_command(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                package,
                "--break-system-packages",
            ],
            f"Installing {package}",
        )


def verify_installation() -> bool:
    """Verify that critical dependencies are installed."""
    critical_packages = [
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "seaborn",
        "sklearn",
        "torch",
        "click",
        "rich",
    ]

    print("\n🔍 Verifying installation...")
    failed = []

    for package in critical_packages:
        try:
            __import__(package)
            print(f" {package}")
        except ImportError:
            print(f" {package}")
            failed.append(package)

    if failed:
        error = ConfigurationError(
            message=f"Failed to install critical dependencies: {', '.join(failed)}",
            context={"failed_packages": failed},
            suggestion="Run the installer again or install packages manually",
        )
        print(f"\n⚠️  {error}")
        return False
    else:
        print("\n✅ All critical dependencies installed successfully!")
        return True


def main() -> None:
    """Main installation function."""
    print("🧠 APGI Framework Dependency Installer")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install core dependencies
    if not install_core_dependencies():
        error = ConfigurationError(
            message="Core dependency installation failed",
            suggestion="Check system permissions and internet connection",
        )
        print(f"\n❌ {error}")
        sys.exit(1)

    # Check for optional flag
    install_optional = "--optional" in sys.argv
    if install_optional:
        print("\n📦 Installing optional dependencies...")
        install_optional_dependencies()

    # Verify installation
    if verify_installation():
        print("\n🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python main.py --help' to see available commands")
        print("2. Try 'python main.py validate --all-protocols' to test the framework")
        print("3. Use 'python main.py gui --gui-type analysis' for the web interface")
    else:
        error = ConfigurationError(
            message="Installation verification failed",
            suggestion="Check error messages above and resolve dependency issues",
        )
        print(f"\n❌ {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
