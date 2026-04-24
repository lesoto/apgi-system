#!/usr/bin/env python3
"""
Utility Script Runner GUI

This GUI provides an interface to run various utility scripts
in the APGI Framework.
"""

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, ttk


class UtilsGUI:
    """GUI for running utility scripts."""

    def __init__(self):
        """Initialize the Utils GUI."""
        self.root = tk.Tk()
        self.root.title("APGI Framework - Utilities GUI")
        self.root.geometry("900x700")

        # Configure styles
        self.setup_styles()

        # Create widgets
        self.create_widgets()

        # Output from last run
        self.last_output = ""

    def setup_styles(self):
        """Setup custom styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(
            "Title.TLabel",
            font=("Helvetica", 24, "bold"),
            foreground="#2c3e50",
        )

        self.style.configure(
            "Subtitle.TLabel",
            font=("Helvetica", 12),
            foreground="#5c6b77",
        )

        self.style.configure(
            "Primary.TButton",
            font=("Helvetica", 11, "bold"),
            padding=(15, 8),
        )

    def create_widgets(self):
        """Create GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="APGI Framework Utilities",
            style="Title.TLabel",
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ttk.Label(
            main_frame,
            text="Run utility scripts and tools",
            style="Subtitle.TLabel",
        )
        subtitle_label.pack(pady=(0, 20))

        # Utilities frame
        utilities_frame = ttk.LabelFrame(main_frame, text="Available Utilities", padding=15)
        utilities_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Create scrollable area for utilities
        canvas = tk.Canvas(utilities_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(utilities_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Define utilities
        utilities = [
            {
                "name": "Delete Python Cache",
                "description": "Clean __pycache__ directories",
                "command": self.run_delete_cache,
            },
            {
                "name": "Diagnostics",
                "description": "Run system diagnostics",
                "command": self.run_diagnostics,
            },
            {
                "name": "Dependency Checker",
                "description": "Check system dependencies",
                "command": self.run_dependency_checker,
            },
            {
                "name": "Validate App",
                "description": "Validate application configuration",
                "command": self.run_validate_app,
            },
            {
                "name": "Config Manager",
                "description": "Manage system configuration",
                "command": self.run_config_manager,
            },
            {
                "name": "Cache Manager",
                "description": "Manage system cache",
                "command": self.run_cache_manager,
            },
            {
                "name": "Data Processor",
                "description": "Process and transform data",
                "command": self.run_data_processor,
            },
            {
                "name": "Batch Processor",
                "description": "Batch data processing",
                "command": self.run_batch_processor,
            },
        ]

        # Create utility buttons
        for util in utilities:
            util_frame = ttk.Frame(scrollable_frame)
            util_frame.pack(fill=tk.X, pady=8)

            # Utility info
            info_frame = ttk.Frame(util_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            name_label = ttk.Label(
                info_frame,
                text=util["name"],
                font=("Helvetica", 11, "bold"),
            )
            name_label.pack(anchor="w")

            desc_label = ttk.Label(
                info_frame,
                text=util["description"],
                font=("Helvetica", 9),
                foreground="#7f8c8d",
            )
            desc_label.pack(anchor="w")

            # Run button
            run_button = ttk.Button(
                util_frame,
                text="Run",
                command=util["command"],
                style="Primary.TButton",
            )
            run_button.pack(side=tk.RIGHT, padx=(10, 0))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=10,
            width=80,
            font=("Courier", 9),
            bg="#f8f9fa",
            fg="#2c3e50",
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        clear_button = ttk.Button(
            button_frame,
            text="Clear Output",
            command=self.clear_output,
        )
        clear_button.pack(side=tk.LEFT, padx=(0, 10))

        exit_button = ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit,
        )
        exit_button.pack(side=tk.RIGHT)

    def run_utility(self, script_name, display_name):
        """Run a utility script."""
        self.output_text.insert(tk.END, f"\n{'=' * 60}\n")
        self.output_text.insert(tk.END, f"Running: {display_name}\n")
        self.output_text.insert(tk.END, f"{'=' * 60}\n")
        self.output_text.see(tk.END)
        self.root.update()

        def run_in_thread():
            try:
                current_dir = Path(__file__).parent
                script_path = current_dir / script_name

                if not script_path.exists():
                    self.output_text.insert(
                        tk.END, f"Error: {script_name} not found at {script_path}\n"
                    )
                    return

                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                for line in process.stdout:
                    self.output_text.insert(tk.END, line)
                    self.output_text.see(tk.END)
                    self.root.update()

                process.wait()
                self.output_text.insert(
                    tk.END, f"\nCompleted with exit code: {process.returncode}\n"
                )

            except Exception as e:
                self.output_text.insert(tk.END, f"Error: {str(e)}\n")

            self.output_text.see(tk.END)

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()

    def run_delete_cache(self):
        """Run delete cache utility."""
        self.run_utility("delete_pycache.py", "Delete Python Cache")

    def run_diagnostics(self):
        """Run diagnostics utility."""
        self.run_utility("utils/diagnostics.py", "Diagnostics")

    def run_dependency_checker(self):
        """Run dependency checker."""
        self.run_utility("utils/dependency_checker.py", "Dependency Checker")

    def run_validate_app(self):
        """Run app validation."""
        self.run_utility("utils/validate_app.py", "Validate App")

    def run_config_manager(self):
        """Run config manager."""
        self.run_utility("utils/config_manager.py", "Config Manager")

    def run_cache_manager(self):
        """Run cache manager."""
        self.run_utility("utils/cache_manager.py", "Cache Manager")

    def run_data_processor(self):
        """Run data processor."""
        self.run_utility("utils/data_processor.py", "Data Processor")

    def run_batch_processor(self):
        """Run batch processor."""
        self.run_utility("utils/batch_processor.py", "Batch Processor")

    def clear_output(self):
        """Clear output text."""
        self.output_text.delete(1.0, tk.END)

    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Main entry point."""
    try:
        gui = UtilsGUI()
        gui.run()
    except Exception as e:
        print(f"Error launching Utils GUI: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
