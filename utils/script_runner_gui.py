#!/usr/bin/env python3
"""
Script Runner GUI Base Class
=============================

Provides a base tkinter GUI for running scripts with output display,
error handling, and process management.
"""

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional


class ScriptRunnerGUI:
    """Base GUI class for running scripts with output display."""

    # Tag constants for colored output
    TAG_INFO = "info"
    TAG_SUCCESS = "success"
    TAG_ERROR = "error"
    TAG_WARNING = "warning"

    def __init__(
        self,
        root: tk.Tk,
        script_dir: str,
        title: str,
        listbox_label: str,
        run_button_text: str,
        run_button_tooltip: str,
        run_all_button_text: str,
        run_all_button_tooltip: str,
        stop_button_text: str,
    ):
        """Initialize the script runner GUI."""
        self.root = root
        self.root.title(title)
        self.script_dir = Path(script_dir)
        self.current_process: Optional[subprocess.Popen] = None
        self.stop_requested = False

        # Create main layout
        self.create_layout(
            listbox_label,
            run_button_text,
            run_button_tooltip,
            run_all_button_text,
            run_all_button_tooltip,
            stop_button_text,
        )

        # Load scripts
        self.load_scripts()

        # Configure text tags for colored output
        self.configure_text_tags()

    def create_layout(
        self,
        listbox_label: str,
        run_button_text: str,
        run_button_tooltip: str,
        run_all_button_text: str,
        run_all_button_tooltip: str,
        stop_button_text: str,
    ) -> None:
        """Create the main GUI layout."""
        # Main container
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Control frame (top)
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        # Script listbox frame
        self.listbox_frame = tk.LabelFrame(self.control_frame, text=listbox_label, padx=5, pady=5)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(0, 10))

        # Script listbox with scrollbar
        self.listbox_scrollbar = tk.Scrollbar(self.listbox_frame)
        self.listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scripts_listbox = tk.Listbox(
            self.listbox_frame,
            yscrollcommand=self.listbox_scrollbar.set,
            height=10,
            width=50,
        )
        self.scripts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox_scrollbar.config(command=self.scripts_listbox.yview)

        # Button frame
        self.button_frame = tk.Frame(self.control_frame)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Run button
        self.run_button = tk.Button(
            self.button_frame,
            text=run_button_text,
            command=self.run_selected_script,
            width=15,
        )
        self.run_button.pack(pady=2)

        # Run all button
        self.run_all_button = tk.Button(
            self.button_frame,
            text=run_all_button_text,
            command=self.run_all_scripts,
            width=15,
        )
        self.run_all_button.pack(pady=2)

        # Stop button
        self.stop_button = tk.Button(
            self.button_frame,
            text=stop_button_text,
            command=self.stop_script,
            width=15,
            state=tk.DISABLED,
        )
        self.stop_button.pack(pady=2)

        # Progress bar
        self.progress = ttk.Progressbar(self.button_frame, mode="indeterminate")
        self.progress.pack(pady=(10, 0), fill=tk.X)

        # Output frame (bottom)
        self.output_frame = tk.LabelFrame(self.main_frame, text="Output", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True)

        # Output text with scrollbar
        self.output_scrollbar = tk.Scrollbar(self.output_frame)
        self.output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(
            self.output_frame,
            yscrollcommand=self.output_scrollbar.set,
            wrap=tk.WORD,
            height=15,
        )
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.output_scrollbar.config(command=self.output_text.yview)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(
            self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

    def configure_text_tags(self) -> None:
        """Configure text tags for colored output."""
        self.output_text.tag_configure(self.TAG_INFO, foreground="blue")
        self.output_text.tag_configure(self.TAG_SUCCESS, foreground="green")
        self.output_text.tag_configure(self.TAG_ERROR, foreground="red")
        self.output_text.tag_configure(self.TAG_WARNING, foreground="orange")

    def load_scripts(self) -> None:
        """Load available scripts from the script directory."""
        self.scripts: list[Path] = []
        if not self.script_dir.exists():
            self.log_output(f"Script directory not found: {self.script_dir}", self.TAG_ERROR)
            return

        # Find all test Python scripts recursively (test_*.py pattern)
        for script_path in sorted(self.script_dir.rglob("test_*.py")):
            # Skip __init__.py
            if script_path.name != "__init__.py":
                self.scripts.append(script_path)
                # Show relative path for better identification
                relative_path = script_path.relative_to(self.script_dir)
                self.scripts_listbox.insert(tk.END, str(relative_path))

        if not self.scripts:
            self.log_output("No scripts found in directory", self.TAG_WARNING)

    def log_output(self, message: str, tag: str = TAG_INFO) -> None:
        """Log a message to the output text widget."""
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)
        self.output_text.update_idletasks()

    def update_status(self, status: str) -> None:
        """Update the status bar."""
        self.status_var.set(status)

    def run_selected_script(self) -> None:
        """Run the currently selected script."""
        selection = self.scripts_listbox.curselection()
        if not selection:
            self.log_output("No script selected", self.TAG_WARNING)
            return

        index = selection[0]
        script = self.scripts[index]
        self.run_script(script)

    def run_script(self, script: Path, wait: bool = False) -> bool:
        """Run a script and display output."""
        self.log_output(f"Running: {script.name}", self.TAG_INFO)
        self.update_status(f"Running: {script.name}")
        self.progress.start()

        # Enable stop button, disable run buttons
        self.stop_button.config(state=tk.NORMAL)
        self.run_button.config(state=tk.DISABLED)
        self.run_all_button.config(state=tk.DISABLED)

        self.stop_requested = False
        success = False

        try:
            # Run the script
            self.current_process = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Read output in a thread
            def read_output():
                while True:
                    if self.stop_requested:
                        break
                    line = self.current_process.stdout.readline()
                    if not line:
                        break
                    self.root.after(0, self.log_output, line.rstrip())

            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            if wait:
                self.current_process.wait()
                output_thread.join()
                success = self.current_process.returncode == 0

                if self.stop_requested:
                    self.log_output(f"Script stopped: {script.name}", self.TAG_WARNING)
                elif success:
                    self.log_output(
                        f"Script completed successfully: {script.name}",
                        self.TAG_SUCCESS,
                    )
                else:
                    self.log_output(
                        f"Script failed with return code {self.current_process.returncode}: {script.name}",
                        self.TAG_ERROR,
                    )

                self.cleanup_after_run()
                return success

        except Exception as e:
            self.log_output(f"Error running script: {e}", self.TAG_ERROR)
            self.cleanup_after_run()
            return False

        return True

    def run_all_scripts(self) -> None:
        """Run all scripts sequentially (to be overridden by subclasses)."""
        self.log_output("run_all_scripts not implemented in base class", self.TAG_WARNING)

    def stop_script(self) -> None:
        """Stop the currently running script."""
        if self.current_process:
            self.stop_requested = True
            self.current_process.terminate()
            self.log_output("Stopping script...", self.TAG_WARNING)
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            self.log_output("Script stopped", self.TAG_INFO)
            self.cleanup_after_run()

    def cleanup_after_run(self) -> None:
        """Clean up after script execution."""
        self.progress.stop()
        self.stop_button.config(state=tk.DISABLED)
        self.run_button.config(state=tk.NORMAL)
        self.run_all_button.config(state=tk.NORMAL)
        self.update_status("Ready")
        self.current_process = None
