#!/usr/bin/env python3
"""
APGI Framework Dependency Checker
================================

Checks for optional dependencies and provides installation guidance.
This script helps users understand which optional packages are available
and how to install them for enhanced functionality.

Usage:
    python check_dependencies.py [--install]
"""

import sys
import subprocess
from typing import Dict, List, Tuple


class DependencyChecker:
    """Checks for optional dependencies and provides installation guidance."""

    def __init__(self):
        self.optional_packages = {
            "scikit-learn": {
                "description": "Machine learning algorithms and utilities",
                "pip_name": "scikit-learn",
                "import_name": "sklearn",
                "category": "ml",
                "importance": "high",
            },
            "torch": {
                "description": "PyTorch deep learning framework",
                "pip_name": "torch",
                "import_name": "torch",
                "category": "ml",
                "importance": "high",
            },
            "torchvision": {
                "description": "PyTorch computer vision library",
                "pip_name": "torchvision",
                "import_name": "torchvision",
                "category": "ml",
                "importance": "medium",
            },
            "customtkinter": {
                "description": "Modern tkinter GUI framework",
                "pip_name": "customtkinter",
                "import_name": "customtkinter",
                "category": "gui",
                "importance": "high",
            },
            "Pillow": {
                "description": "Image processing library",
                "pip_name": "Pillow",
                "import_name": "PIL",
                "category": "gui",
                "importance": "medium",
            },
            "mne": {
                "description": "MEG/EEG data analysis",
                "pip_name": "mne",
                "import_name": "mne",
                "category": "neural",
                "importance": "high",
            },
            "nibabel": {
                "description": "Neuroimaging data I/O",
                "pip_name": "nibabel",
                "import_name": "nibabel",
                "category": "neural",
                "importance": "medium",
            },
            "seaborn": {
                "description": "Statistical data visualization",
                "pip_name": "seaborn",
                "import_name": "seaborn",
                "category": "visualization",
                "importance": "low",
            },
            "plotly": {
                "description": "Interactive data visualization",
                "pip_name": "plotly",
                "import_name": "plotly",
                "category": "visualization",
                "importance": "low",
            },
            "jupyter": {
                "description": "Jupyter notebook environment",
                "pip_name": "jupyter",
                "import_name": "jupyter",
                "category": "jupyter",
                "importance": "medium",
            },
            "psutil": {
                "description": "System and process utilities",
                "pip_name": "psutil",
                "import_name": "psutil",
                "category": "performance",
                "importance": "low",
            },
            "statsmodels": {
                "description": "Statistical modeling and econometrics",
                "pip_name": "statsmodels",
                "import_name": "statsmodels",
                "category": "stats",
                "importance": "low",
            },
        }

    def check_package(self, package_info: Dict) -> Tuple[bool, str]:
        """Check if a package is available."""
        try:
            __import__(package_info["import_name"])
            return True, "Available"
        except ImportError:
            return False, "Not installed"

    def install_package(self, package_info: Dict) -> bool:
        """Install a package using pip."""
        pip_name = package_info["pip_name"]
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def run_check(self, install_missing: bool = False) -> None:
        """Run the dependency check."""
        print("🔍 APGI Framework Optional Dependencies Check")
        print("=" * 60)

        categories: Dict[str, List[Tuple[str, Dict]]] = {}
        for pkg, info in self.optional_packages.items():
            cat = info["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((pkg, info))

        for category, packages in categories.items():
            print(f"\n📦 {category.upper()} Dependencies:")
            print("-" * 40)

            for pkg_name, pkg_info in packages:
                available, status = self.check_package(pkg_info)
                importance = pkg_info["importance"]
                description = pkg_info["description"]

                status_icon = "✅" if available else "❌"
                print(f"  {status_icon} {pkg_name} ({importance})")
                print(f"      {description}")

                if not available:
                    pip_name = pkg_info["pip_name"]
                    print(f"      Install: pip install {pip_name}")

                    if install_missing:
                        print(f"      Installing {pkg_name}...")
                        if self.install_package(pkg_info):
                            print(f"      ✅ {pkg_name} installed successfully")
                        else:
                            print(f"      ❌ Failed to install {pkg_name}")

        print("\n💡 Usage Tips:")
        print("  • High importance packages significantly enhance functionality")
        print("  • Medium importance packages provide useful features")
        print("  • Low importance packages are nice-to-have enhancements")
        print("  • Use 'pip install -e .[ml]' to install ML dependencies")
        print("  • Use 'pip install -e .[gui]' to install GUI dependencies")

        print("\n📖 For more information, see pyproject.toml optional-dependencies")


def main():
    """Main entry point."""
    install_missing = "--install" in sys.argv

    checker = DependencyChecker()
    checker.run_check(install_missing=install_missing)


if __name__ == "__main__":
    main()
