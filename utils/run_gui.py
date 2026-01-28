#!/usr/bin/env python3
"""
APGI System GUI Launcher

Simple launcher script for the APGI GUI application.
Supports both normal launch and test mode.
"""

import argparse
import sys
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def launch_gui():
    """Launch the GUI application normally."""
    from apgi_gui import main

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
        traceback.print_exc()
        input("\nPress Enter to exit...")


def test_gui_launch(duration_seconds: int = 3):
    """
    Test that GUI can be launched.

    Args:
        duration_seconds: How long to keep GUI open before closing

    Returns:
        True if GUI launched successfully, False otherwise
    """
    import tkinter as tk

    print("Testing GUI launch...")
    print(f"Opening GUI window for {duration_seconds} seconds...")

    try:
        # Import the GUI
        from apgi_gui import APGIGui

        # Create root window
        root = tk.Tk()

        # Create GUI instance
        APGIGui(root)

        print("✓ GUI window opened successfully!")
        print(f"  - Window title: {root.title()}")
        print(f"  - Window size: {root.geometry()}")

        # Close after specified duration
        root.after(duration_seconds * 1000, root.quit)

        # Run main loop
        root.mainloop()

        print("✓ GUI closed successfully!")
        return True

    except Exception as e:
        print(f"✗ GUI launch failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Launch APGI System GUI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: launch GUI briefly then close",
    )
    parser.add_argument(
        "--test-duration",
        type=int,
        default=3,
        help="Duration in seconds for test mode",
    )

    args = parser.parse_args()

    if args.test:
        success = test_gui_launch(duration_seconds=args.test_duration)
        sys.exit(0 if success else 1)
    else:
        launch_gui()


if __name__ == "__main__":
    main()
