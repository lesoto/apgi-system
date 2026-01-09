#!/usr/bin/env python3
"""
Quick Start Script for Screenshot Documentation

Simple script to get started with screenshot documentation.
Handles dependency installation and runs the appropriate documentation tool.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_dependencies(enhanced=False):
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    # Basic dependencies
    basic_deps = ["playwright", "pytest"]
    
    # Enhanced dependencies
    enhanced_deps = ["pyautogui", "pygetwindow", "pillow"]
    
    try:
        # Install basic dependencies
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + basic_deps)
        print("✅ Basic dependencies installed")
        
        # Install enhanced dependencies if requested
        if enhanced:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + enhanced_deps)
            print("✅ Enhanced dependencies installed")
        
        # Install playwright browsers
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("✅ Playwright browsers installed")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def run_documentation(enhanced=False):
    """Run the appropriate documentation tool."""
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
        subprocess.run([sys.executable, str(script_path)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running documentation: {e}")
        return False


def main():
    """Main entry point."""
    print("🎯 APGI System Screenshot Documentation - Quick Start")
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
    
    # Install dependencies
    if not install_dependencies(enhanced):
        print("❌ Failed to install dependencies")
        return
    
    print()
    
    # Run documentation
    if run_documentation(enhanced):
        print("\n✅ Documentation completed successfully!")
        print("📸 Check the docs/screenshots/ directory for results")
    else:
        print("\n❌ Documentation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
