#!/usr/bin/env python3
"""
APGI System GUI Launcher

Simple launcher script for the APGI GUI application.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from apgi_gui import main

if __name__ == '__main__':
    print("=" * 60)
    print("APGI System - Consciousness Modeling Framework")
    print("=" * 60)
    print("\nStarting GUI application...")
    print("Please wait while the system initializes...\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication closed by user")
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
