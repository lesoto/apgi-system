"""
Quick GUI launch test - opens GUI for 3 seconds then closes
"""

import tkinter as tk
import sys


def test_gui_launch():
    """Test that GUI can be launched."""
    print("Testing GUI launch...")
    print("Opening GUI window for 3 seconds...")

    try:
        # Import the GUI
        from apgi_gui import APGIGui

        # Create root window
        root = tk.Tk()

        # Create GUI instance
        app = APGIGui(root)

        print("✓ GUI window opened successfully!")
        print("  - Window title:", root.title())
        print("  - Window size:", root.geometry())

        # Close after 3 seconds
        root.after(3000, root.quit)

        # Run main loop
        root.mainloop()

        print("✓ GUI closed successfully!")
        return True

    except Exception as e:
        print(f"✗ GUI launch failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_gui_launch()
    sys.exit(0 if success else 1)
