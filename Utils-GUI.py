#!/usr/bin/env python3
"""
GUI to run all utils folder scripts
==========================================

A tkinter-based GUI that allows running all scripts in the utils folder
with output display and error handling.
"""

import sys
import tkinter as tk

from utils.script_runner_gui import ScriptRunnerGUI


class UtilsRunnerGUI(ScriptRunnerGUI):
    """Simple GUI for running utils scripts.

    Provides a tkinter-based interface to run utility scripts from the utils folder
    with real-time output display, error handling, and process management.
    """

    def __init__(self, root: tk.Tk):
        super().__init__(
            root,
            "utils",
            "APGI Utils Scripts Runner",
            "Available Scripts",
            "Run All Scripts",
            "Run the currently selected script",
            "Run all scripts in sequence",
            "Stop the currently running script",
        )


def main() -> None:
    """Launch the utils runner GUI."""
    try:
        # Create and run the GUI
        root = tk.Tk()
        UtilsRunnerGUI(root)

        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        root.mainloop()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("This script requires tkinter, which should come with Python.")
        sys.exit(1)
    except tk.TclError as e:
        print(f"❌ Tkinter Error: {e}")
        print("There was an error initializing the GUI.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
