#!/usr/bin/env python3
"""
Shared GUI base class for running scripts from different directories
===================================================================

A tkinter-based GUI that allows running scripts from a specified directory
with output display and error handling.
"""

import json
import subprocess
import sys
import threading
import tkinter as tk
from collections import deque
from pathlib import Path
from tkinter import filedialog, scrolledtext, ttk
from typing import Any, Dict, List, Optional, Tuple

# Import theme manager
try:
    from apgi_gui.theme_manager import ThemeManager

    THEME_MANAGER_AVAILABLE = True
except ImportError:
    THEME_MANAGER_AVAILABLE = False
    print("Warning: Theme manager not available. Theme support disabled.")

# Import ToolTip from components
try:
    from apgi_gui.components.core import ToolTip
except ImportError:
    print("Warning: ToolTip component not available.")

    # Fallback no-op ToolTip class
    class ToolTip:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


class ScriptRunnerGUI:
    """Base GUI for running scripts from a directory.

    Provides a tkinter-based interface to run scripts from a specified directory
    with real-time output display, error handling, and process management.
    """

    def __init__(
        self,
        root: tk.Tk,
        script_dir_name: str,
        title: str,
        script_list_label: str,
        run_all_text: str,
        tooltip_selected: str,
        tooltip_all: str,
        tooltip_stop: str,
    ):
        self.root = root
        self.root.title(title)
        self.root.geometry("800x600")

        # Compatibility attributes for tests (Initialize early)
        self.status_var = tk.StringVar(value="Ready")
        self.config = {
            "timeout": 30,
            "working_directory": str(Path(__file__).parent.parent),
            "environment_vars": {},
        }
        self.execution_history: List[Dict[str, Any]] = []
        self.execution_thread: Optional[threading.Thread] = None
        self.utility_var = tk.StringVar() if hasattr(tk, "StringVar") else None

        self.script_dir_name = script_dir_name
        self.script_dir = Path(__file__).parent.parent / script_dir_name
        self.script_type = "test" if script_dir_name == "tests" else "script"
        self.scripts = self.get_script_list()
        self.utilities = [s.name for s in self.scripts]
        self.utility_descriptions: Dict[str, str] = {s.name: f"Run {s.name}" for s in self.scripts}

        # Initialize theme manager
        self.theme_manager = None
        if THEME_MANAGER_AVAILABLE:
            self.theme_manager = ThemeManager(initial_theme="normal")

        # Store running processes
        self.running_processes: Dict[str, subprocess.Popen[str]] = {}

        # Output tag constants
        self.TAG_INFO = "info"
        self.TAG_ERROR = "error"
        self.TAG_SUCCESS = "success"
        self.TAG_WARNING = "warning"

        # Bounded output buffer to prevent memory leaks
        self.output_buffer_size = 10000  # Maximum number of output lines to keep
        self.output_buffer: deque[Tuple[str, str]] = deque(maxlen=self.output_buffer_size)

        self.setup_ui(script_list_label, run_all_text, tooltip_selected, tooltip_all, tooltip_stop)

        # Add keyboard shortcut for quitting (Ctrl+Q or Cmd+Q)
        self.root.bind("<Control-q>", lambda e: self.quit_application())
        self.root.bind("<Command-q>", lambda e: self.quit_application())

        # Handle window close button
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        # Backward compatibility for tests
        self.output_scrollbar = (
            tk.Scrollbar(self.output_frame) if hasattr(tk, "Scrollbar") else None
        )

    def get_script_list(self) -> List[Path]:
        """Get all Python scripts in script directory.

        Returns:
            List of Path objects for executable Python scripts.
        """
        scripts = []
        if self.script_dir.exists() and self.script_dir.is_dir():
            if self.script_dir_name == "tests":
                # Tests directory uses recursive glob
                for file_path in self.script_dir.rglob("*.py"):
                    if file_path.name != "__init__.py":
                        scripts.append(file_path)
            else:
                # Other directories use non-recursive glob
                for file_path in self.script_dir.glob("*.py"):
                    if file_path.name != "__init__.py":
                        scripts.append(file_path)
        return sorted(scripts)

    def _create_menu_bar(self) -> None:
        """Create menu bar with theme options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Quit", command=self.quit_application)

        # Theme menu (only if theme manager is available)
        if self.theme_manager:
            theme_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Theme", menu=theme_menu)

            # Add theme options
            for theme_name in self.theme_manager.get_available_themes():
                theme_menu.add_radiobutton(
                    label=theme_name.capitalize(),
                    command=lambda t=theme_name: self._set_theme(t),  # type: ignore
                    variable=tk.StringVar(value=self.theme_manager.current_theme),
                    value=theme_name,
                )

    def _set_theme(self, theme_name: str) -> None:
        """Set the current theme.

        Args:
            theme_name: Name of the theme to apply
        """
        if not self.theme_manager:
            return

        if self.theme_manager.set_theme(theme_name):
            self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self) -> None:
        """Apply current theme to all widgets."""
        if not self.theme_manager:
            return

        # Apply theme to output text widget
        if hasattr(self, "output_text"):
            bg_color = self.theme_manager.get_theme_color("bg")
            fg_color = self.theme_manager.get_theme_color("fg")
            try:
                self.output_text.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
            except tk.TclError:
                pass

        # Apply theme to status label
        if hasattr(self, "status_label"):
            fg_color = self.theme_manager.get_theme_color("fg")
            try:
                self.status_label.config(fg=fg_color)  # type: ignore
            except tk.TclError:
                pass

    def setup_ui(
        self,
        script_list_label: str,
        run_all_text: str,
        tooltip_selected: str,
        tooltip_all: str,
        tooltip_stop: str,
    ) -> None:
        """Setup the user interface.

        Args:
            script_list_label: Label for the scripts list frame
            run_all_text: Text for the run all button
            tooltip_selected: Tooltip for run selected button
            tooltip_all: Tooltip for run all button
            tooltip_stop: Tooltip for stop button
        """
        # Create menu bar
        self._create_menu_bar()

        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(self.main_frame, text=self.root.title(), font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Scripts list frame
        list_frame = ttk.LabelFrame(self.main_frame, text=script_list_label, padding="5")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # Scripts listbox with scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scripts_listbox = tk.Listbox(
            list_frame, yscrollcommand=list_scrollbar.set, height=15, width=40
        )
        self.scripts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.config(command=self.scripts_listbox.yview)

        # Populate scripts list
        for script in self.scripts:
            if self.script_dir_name == "tests":
                relative_path = script.relative_to(self.script_dir)
                self.scripts_listbox.insert(tk.END, str(relative_path))
            else:
                self.scripts_listbox.insert(tk.END, script.name)

        # Control buttons frame
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10))

        # Buttons
        self.run_button = ttk.Button(
            self.control_frame, text="Run Selected", command=self.run_selected_script
        )
        self.run_button.pack(pady=5, fill=tk.X)
        ToolTip(self.run_button, tooltip_selected)

        self.run_all_button = ttk.Button(
            self.control_frame, text=run_all_text, command=self.run_all_scripts
        )
        self.run_all_button.pack(pady=5, fill=tk.X)
        ToolTip(self.run_all_button, tooltip_all)

        self.stop_button = ttk.Button(
            self.control_frame,
            text="Stop Selected",
            command=self.stop_selected_script,
            state=tk.DISABLED,
        )
        self.stop_button.pack(pady=5, fill=tk.X)
        ToolTip(self.stop_button, tooltip_stop)

        self.clear_button = ttk.Button(
            self.control_frame, text="Clear Output", command=self.clear_output
        )
        self.clear_button.pack(pady=5, fill=tk.X)
        ToolTip(self.clear_button, "Clear the output text area")

        self.export_button = ttk.Button(
            self.control_frame, text="Export Output", command=self.export_output
        )
        self.export_button.pack(pady=5, fill=tk.X)
        ToolTip(self.export_button, "Export the output text to a file")

        self.quit_button = ttk.Button(
            self.control_frame, text="Quit", command=self.quit_application
        )
        self.quit_button.pack(pady=5, fill=tk.X)
        ToolTip(self.quit_button, "Exit the application")

        # Arguments input
        args_label = ttk.Label(self.control_frame, text="Arguments:")
        args_label.pack(pady=(10, 0), anchor=tk.W)
        self.args_entry = ttk.Entry(self.control_frame)
        self.args_entry.pack(fill=tk.X, pady=(0, 10))
        ToolTip(self.args_entry, "Enter command-line arguments for the script (space-separated)")
        status_frame = ttk.LabelFrame(self.control_frame, text="Status", padding="5")
        status_frame.pack(pady=20, fill=tk.X)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(self.control_frame, mode="indeterminate", length=200)
        self.progress.pack(pady=10, fill=tk.X)

        # Output frame
        self.output_frame = ttk.LabelFrame(self.main_frame, text="Output", padding="5")
        self.output_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(10, 0))

        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame, height=15, wrap=tk.WORD, font=("Courier", 9)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for different output types
        self.output_text.tag_config(self.TAG_INFO, foreground="black")
        self.output_text.tag_config(self.TAG_ERROR, foreground="red")
        self.output_text.tag_config(self.TAG_SUCCESS, foreground="green")
        self.output_text.tag_config(self.TAG_WARNING, foreground="orange")

    def log_output(self, message: str, tag: Optional[str] = None) -> None:
        """Add message to output text area.

        Args:
            message: The message to log.
            tag: The color tag to apply (info, error, success, warning).
        """
        if tag is None:
            tag = self.TAG_INFO
        # Store in bounded buffer to prevent memory leaks
        self.output_buffer.append((message, tag))
        self.root.after_idle(lambda: self._safe_log_output(message, tag))

    def _safe_log_output(self, message: str, tag: str) -> None:
        """Thread-safe output logging with bounded buffer management."""
        # Clear and rebuild output if buffer is getting large
        if len(self.output_buffer) > 5000:
            self.output_text.delete(1.0, tk.END)
            # Re-add recent entries from buffer
            for msg, t in list(self.output_buffer)[-1000:]:
                self.output_text.insert(tk.END, msg + "\n", t)
        else:
            self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)

    def update_status(self, message: str) -> None:
        """Update status label.

        Args:
            message: The status message to display.
        """
        self.root.after_idle(lambda: self._safe_update_status(message))

    def _safe_update_status(self, message: str) -> None:
        """Thread-safe status update."""
        self.status_label.config(text=message)

    def get_selected_script(self) -> Optional[Path]:
        """Get the currently selected script.

        Returns:
            Path to selected script or None if no selection.
        """
        selection = tuple(self.scripts_listbox.curselection())  # type: ignore
        if selection:
            index = selection[0]
            return self.scripts[index]
        return None

    def run_selected_script(self) -> None:
        """Run the selected script in a separate thread."""
        script = self.get_selected_script()
        if not script:
            self.log_output(f"No {self.script_type} script selected", self.TAG_ERROR)
            return

        self.run_script(script)

    def run_all_scripts(self) -> None:
        """Run all scripts sequentially."""
        if not self.scripts:
            self.log_output(f"No {self.script_type} scripts found", self.TAG_ERROR)
            return

        def run_all() -> None:
            for i, script in enumerate(self.scripts):
                if self.script_dir_name == "tests":
                    relative_path = script.relative_to(self.script_dir)
                    display_name = str(relative_path)
                else:
                    display_name = script.name
                self.log_output(
                    f"Running {self.script_type} {i + 1}/{len(self.scripts)}: {display_name}",
                    self.TAG_INFO,
                )
                self.scripts_listbox.selection_clear(0, tk.END)
                self.scripts_listbox.selection_set(i)
                self.scripts_listbox.see(i)

                success = self.run_script(script, wait=True)
                if not success:
                    if self.script_dir_name == "tests":
                        relative_path = script.relative_to(self.script_dir)
                        display_name = str(relative_path)
                    else:
                        display_name = script.name
                    self.log_output(
                        f"{self.script_type.capitalize()} {display_name} failed, stopping execution",
                        self.TAG_ERROR,
                    )
                    break

            self.log_output(f"All {self.script_type}s execution completed", self.TAG_SUCCESS)
            self.update_status("Ready")
            self.progress.stop()

        # Run in separate thread to avoid blocking GUI
        thread = threading.Thread(target=run_all, daemon=True)
        thread.start()

    def run_script(self, script: Path, wait: bool = False) -> bool:
        """Run a single script.

        Args:
            script: Path to the script to run.
            wait: If True, block until script completes and return success status.
                 If False, run asynchronously and return True immediately.

        Returns:
            True if script started successfully, False if error occurred.
            When wait=True, returns True if script completed with return code 0.
        """
        try:
            if self.script_dir_name == "tests":
                relative_path = script.relative_to(self.script_dir)
                display_name = str(relative_path)
            else:
                display_name = script.name
            self.log_output(f"Starting: {display_name}", self.TAG_INFO)
            self.update_status(f"Running: {display_name}")
            self.progress.start()

            # Get arguments from entry
            args_str = self.args_entry.get().strip()
            args_list = args_str.split() if args_str else []

            # Enable stop button when script starts
            self.root.after_idle(lambda: self.stop_button.config(state=tk.NORMAL))

            # Ensure absolute paths for command execution (BUG-L13)
            python_exe = Path(sys.executable).resolve()
            abs_script_path = Path(script).resolve()

            # Start subprocess
            self.log_output(f"Starting {display_name}...", self.TAG_INFO)
            process = subprocess.Popen(
                [str(python_exe), str(abs_script_path)] + args_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.script_dir.parent,
            )

            self.running_processes[script.name] = process

            def read_output() -> None:
                """Read subprocess output and handle termination logic."""
                try:
                    if process.stdout:
                        while True:
                            output = process.stdout.readline()
                            if output == "" and process.poll() is not None:
                                break
                            if output:
                                self.log_output(output.strip())
                except (IOError, ValueError) as e:
                    self.log_output(f"Output stream error: {e}", self.TAG_WARNING)

                # Wait for process to complete with timeout to prevent hanging
                try:
                    process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    self.log_output(
                        f"Process {display_name} timed out during wait, terminating...",
                        self.TAG_ERROR,
                    )
                    process.kill()
                    process.wait()  # Ensure process is fully reaped

                return_code = process.returncode
                if return_code == 0:
                    self.log_output(f"[OK] {display_name} completed successfully", self.TAG_SUCCESS)
                else:
                    self.log_output(
                        f"[FAIL] {display_name} failed with return code {return_code}",
                        self.TAG_ERROR,
                    )

                # Clean up
                if script.name in self.running_processes:
                    del self.running_processes[script.name]

                # Disable stop button when script completes
                self.root.after_idle(self._update_stop_button_state)

                self.progress.stop()
                self.update_status("Ready")

            # Start output reading thread
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            if wait:
                output_thread.join()
                return process.returncode == 0
            else:
                return True

        except Exception as e:
            if self.script_dir_name == "tests":
                relative_path = script.relative_to(self.script_dir)
                display_name = str(relative_path)
            else:
                display_name = script.name
            self.log_output(f"Error running {display_name}: {str(e)}", self.TAG_ERROR)
            self.progress.stop()
            self.update_status("Error")
            # Disable stop button on error
            self.root.after_idle(self._update_stop_button_state)
            return False

    def _update_stop_button_state(self) -> None:
        """Update stop button state based on running processes."""
        if self.running_processes:
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.stop_button.config(state=tk.DISABLED)

    def stop_selected_script(self) -> None:
        """Stop the selected script if it's running."""
        script = self.get_selected_script()
        if not script:
            self.log_output(f"No {self.script_type} script selected", self.TAG_ERROR)
            return

        if script.name in self.running_processes:
            try:
                process = self.running_processes[script.name]
                process.terminate()
                if self.script_dir_name == "tests":
                    relative_path = script.relative_to(self.script_dir)
                    display_name = str(relative_path)
                else:
                    display_name = script.name
                self.log_output(f"Stopped: {display_name}", self.TAG_WARNING)
                del self.running_processes[script.name]
                # Disable stop button if no processes are running
                self._update_stop_button_state()
                self.progress.stop()
                self.update_status("Ready")
            except Exception as e:
                if self.script_dir_name == "tests":
                    relative_path = script.relative_to(self.script_dir)
                    display_name = str(relative_path)
                else:
                    display_name = script.name
                self.log_output(f"Error stopping {display_name}: {str(e)}", self.TAG_ERROR)
        else:
            if self.script_dir_name == "tests":
                relative_path = script.relative_to(self.script_dir)
                display_name = str(relative_path)
            else:
                display_name = script.name
            self.log_output(
                f"{self.script_type.capitalize()} {display_name} is not running", self.TAG_WARNING
            )

    def clear_output(self) -> None:
        """Clear the output text area."""
        self.output_text.delete(1.0, tk.END)
        self.log_output("Output cleared", self.TAG_INFO)

    def export_output(self) -> None:
        """Export the output text to a file."""
        filename = filedialog.asksaveasfilename(
            title="Export Output",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            try:
                with open(filename, "w") as f:
                    f.write(self.output_text.get("1.0", tk.END))
                self.log_output(f"Output exported to {filename}", self.TAG_SUCCESS)
            except Exception as e:
                self.log_output(f"Failed to export output: {str(e)}", self.TAG_ERROR)

    def quit_application(self) -> None:
        """Quit the application safely.

        Stops all running processes and closes the application.
        """
        # Stop all running processes
        for script_name, process in list(self.running_processes.items()):
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    self.log_output(f"Terminated process: {script_name}", self.TAG_WARNING)
            except Exception as e:
                self.log_output(f"Error terminating process {script_name}: {e}", self.TAG_ERROR)

        # Clear running processes
        self.running_processes.clear()

        # Log quit message
        self.log_output("Quitting application...", self.TAG_INFO)

        # Wait a moment for messages to be processed
        self.root.update_idletasks()

        # Quit the application
        self.root.quit()
        self.root.destroy()

    # Compatibility methods for tests
    def _update_status(self, message: str) -> None:
        self.status_var.set(message)
        self.root.update_idletasks()

    def _display_output(self, message: str) -> None:
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _clear_output(self) -> None:
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _validate_utility_selection(self, utility_name: str) -> bool:
        return any(s.name == utility_name for s in self.scripts)

    def _execute_utility(self, utility_name: str) -> None:
        script = next((s for s in self.scripts if s.name == utility_name), None)
        if script:
            self.run_script(script)

    def _run_utility_threaded(self, utility_name: str) -> None:
        script = next((s for s in self.scripts if s.name == utility_name), None)
        if script:
            self.execution_thread = threading.Thread(
                target=self.run_script, args=(script, True), daemon=True
            )
            self.execution_thread.start()

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        if "timeout" in config and config["timeout"] < 0:
            return False
        if "working_directory" in config and not Path(config["working_directory"]).exists():
            return False
        return True

    def _save_config(self, filename: str) -> None:
        with open(filename, "w") as f:
            json.dump(self.config, f)

    def _load_config(self, filename: str) -> None:
        with open(filename, "r") as f:
            self.config = json.load(f)

    def _export_output(self, filename: str) -> None:
        with open(filename, "w") as f:
            f.write(self.output_text.get("1.0", tk.END))

    def _export_execution_log(self, filename: str) -> None:
        with open(filename, "w") as f:
            json.dump(self.execution_history, f)


def main() -> None:
    """Launch the script runner GUI. This should be overridden in subclasses."""
    print("This is the base class. Please use a subclass like UtilsRunnerGUI or TestsRunnerGUI.")
    sys.exit(0)


if __name__ == "__main__":
    main()
