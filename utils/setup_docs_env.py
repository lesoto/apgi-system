#!/usr/bin/env python3
"""
Virtual Environment Setup for Screenshot Documentation

Sets up a virtual environment and installs dependencies for screenshot documentation.
"""

import subprocess
import sys
import venv
from pathlib import Path


def create_virtual_environment():
    """Create a virtual environment for documentation."""
    base_dir = Path(__file__).parent.parent
    venv_path = base_dir / "venv_docs"
    
    print(f"📦 Creating virtual environment at {venv_path}")
    
    try:
        venv.create(venv_path, with_pip=True)
        print("✅ Virtual environment created")
        return venv_path
    except Exception as e:
        print(f"❌ Error creating virtual environment: {e}")
        return None


def get_venv_python(venv_path):
    """Get the Python executable from the virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def install_dependencies(venv_python, enhanced=False):
    """Install dependencies in the virtual environment."""
    print("📦 Installing dependencies...")
    
    # Basic dependencies
    basic_deps = ["playwright", "pytest"]
    
    # Enhanced dependencies
    enhanced_deps = ["pyautogui", "pygetwindow", "pillow"]
    
    try:
        # Install basic dependencies
        subprocess.check_call([str(venv_python), "-m", "pip", "install"] + basic_deps)
        print("✅ Basic dependencies installed")
        
        # Install enhanced dependencies if requested
        if enhanced:
            subprocess.check_call([str(venv_python), "-m", "pip", "install"] + enhanced_deps)
            print("✅ Enhanced dependencies installed")
        
        # Install playwright browsers
        subprocess.check_call([str(venv_python), "-m", "playwright", "install"])
        print("✅ Playwright browsers installed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def run_documentation(venv_python, enhanced=False):
    """Run the documentation tool with the virtual environment."""
    base_dir = Path(__file__).parent.parent
    
    if enhanced:
        script_path = base_dir / "utils" / "enhanced_screenshot_docs.py"
        print("🚀 Running Enhanced Screenshot Documentation...")
    else:
        script_path = base_dir / "utils" / "screenshot_documentation.py"
        print("🚀 Running Basic Screenshot Documentation...")
    
    if not script_path.exists():
        print(f"❌ Documentation script not found: {script_path}")
        return False
    
    try:
        subprocess.run([str(venv_python), str(script_path)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running documentation: {e}")
        return False


def main():
    """Main entry point."""
    print("🎯 APGI System Screenshot Documentation - Setup")
    print("=" * 60)
    
    # Ask user which version to run
    print("Choose documentation mode:")
    print("1. Basic (Playwright only)")
    print("2. Enhanced (with window/terminal capture)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        enhanced = choice == "2"
    except KeyboardInterrupt:
        print("\n👋 Cancelled")
        return
    
    print()
    
    # Create virtual environment
    venv_path = create_virtual_environment()
    if not venv_path:
        print("❌ Failed to create virtual environment")
        return
    
    venv_python = get_venv_python(venv_path)
    
    print()
    
    # Install dependencies
    if not install_dependencies(venv_python, enhanced):
        print("❌ Failed to install dependencies")
        return
    
    print()
    
    # Run documentation
    if run_documentation(venv_python, enhanced):
        print("\n✅ Documentation completed successfully!")
        print("📸 Check the docs/screenshots/ directory for results")
        print(f"🐍 Virtual environment: {venv_path}")
        print(f"💡 To reuse this environment, run: {venv_python} utils/enhanced_screenshot_docs.py")
    else:
        print("\n❌ Documentation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
