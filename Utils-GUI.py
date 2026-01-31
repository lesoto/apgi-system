#!/usr/bin/env python3
"""
GUI to run all utils folder scripts
==========================================

A tkinter-based GUI that allows running all scripts in the utils folder
with output display and error handling.
"""

import subprocess
import sys
import threading
import tkinter as tk
from collections import deque
from pathlib import Path
from tkinter import scrolledtext, ttk
from typing import Dict, List, Optional

# Import theme manager
try:
    from apgi_gui.theme_manager import ThemeManager

    THEME_MANAGER_AVAILABLE = True
except ImportError:
    THEME_MANAGER_AVAILABLE = False
    print("Warning: Theme manager not available. Theme support disabled.")


class ToolTip:
    """Consistent tooltip implementation for tkinter widgets"""

    def __init__(self, widget, text=""):
        """Initialize tooltip

        Args:
            widget: The widget to attach tooltip to
            text: Tooltip text to display
        """
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self._delay = 500

        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)

    def on_enter(self, event=None):
        """Show tooltip when mouse enters widget"""
        self.schedule()

    def on_leave(self, event=None):
        """Hide tooltip when mouse leaves widget"""
        self.unschedule()
        self.hidetip()

    def schedule(self):
        """Schedule tooltip display"""
        self.unschedule()
        self.id = self.widget.after(self._delay, self.showtip)

    def unschedule(self):
        """Cancel scheduled tooltip display"""
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self):
        """Display the tooltip"""
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(padx=1, pady=1)

    def hidetip(self):
        """Hide the tooltip"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

    def update_text(self, new_text):
        """Update tooltip text"""
        self.text = new_text


class UtilsRunnerGUI:
    """Simple GUI for running utils scripts.

    Provides a tkinter-based interface to run utility scripts from the utils folder
    with real-time output display, error handling, and process management.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("APGI Utils Scripts Runner")
        self.root.geometry("800x600")

        # Initialize theme manager
        self.theme_manager = None
        if THEME_MANAGER_AVAILABLE:
            self.theme_manager = ThemeManager(initial_theme="normal")

        # Get utils directory
        self.utils_dir = Path(__file__).parent / "utils"
        self.scripts = self.get_script_list()

        # Store running processes
        self.running_processes: Dict[str, subprocess.Popen] = {}

        # Output tag constants
        self.TAG_INFO = "info"
        self.TAG_ERROR = "error"
        self.TAG_SUCCESS = "success"
        self.TAG_WARNING = "warning"

        # Bounded output buffer to prevent memory leaks
        self.output_buffer_size = 10000  # Maximum number of output lines to keep
        self.output_buffer = deque(maxlen=self.output_buffer_size)

        self.setup_ui()

        # Add keyboard shortcut for quitting (Ctrl+Q or Cmd+Q)
        self.root.bind("<Control-q>", lambda e: self.quit_application())
        self.root.bind("<Command-q>", lambda e: self.quit_application())

        # Handle window close button
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

    def get_script_list(self) -> List[Path]:
        """Get all Python scripts in utils directory.

        Returns:
            List of Path objects for executable Python scripts.
        """
        scripts = []
        if self.utils_dir.exists() and self.utils_dir.is_dir():
            for file_path in self.utils_dir.glob("*.py"):
                if file_path.name != "__init__.py":
                    scripts.append(file_path)
        return sorted(scripts)

    def _create_menu_bar(self):
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
                    command=lambda t=theme_name: self._set_theme(t),
                    variable=tk.StringVar(value=self.theme_manager.current_theme),
                    value=theme_name,
                )

    def _set_theme(self, theme_name: str):
        """Set the current theme.

        Args:
            theme_name: Name of the theme to apply
        """
        if not self.theme_manager:
            return

        if self.theme_manager.set_theme(theme_name):
            self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self):
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
                self.status_label.config(fg=fg_color)
            except tk.TclError:
                pass

    def setup_ui(self):
        """Setup the user interface.

        Creates the main layout with script list, control buttons,
        status display, and output area.
        """
        # Create menu bar
        self._create_menu_bar()

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame, text="APGI Utils Scripts Runner", font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Scripts list frame
        list_frame = ttk.LabelFrame(main_frame, text="Available Scripts", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

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
            self.scripts_listbox.insert(tk.END, script.name)

        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))

        # Buttons
        self.run_button = ttk.Button(
            control_frame, text="Run Selected", command=self.run_selected_script
        )
        self.run_button.pack(pady=5, fill=tk.X)
        ToolTip(self.run_button, "Run the currently selected script")

        self.run_all_button = ttk.Button(
            control_frame, text="Run All Scripts", command=self.run_all_scripts
        )
        self.run_all_button.pack(pady=5, fill=tk.X)
        ToolTip(self.run_all_button, "Run all scripts in sequence")

        self.stop_button = ttk.Button(
            control_frame,
            text="Stop Selected",
            command=self.stop_selected_script,
            state=tk.DISABLED,
        )
        self.stop_button.pack(pady=5, fill=tk.X)
        ToolTip(self.stop_button, "Stop the currently running script")

        self.clear_button = ttk.Button(
            control_frame, text="Clear Output", command=self.clear_output
        )
        self.clear_button.pack(pady=5, fill=tk.X)
        ToolTip(self.clear_button, "Clear the output text area")

        self.quit_button = ttk.Button(control_frame, text="Quit", command=self.quit_application)
        self.quit_button.pack(pady=5, fill=tk.X)
        ToolTip(self.quit_button, "Exit the application")

        # Status frame
        status_frame = ttk.LabelFrame(control_frame, text="Status", padding="5")
        status_frame.pack(pady=20, fill=tk.X)

        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode="indeterminate", length=200)
        self.progress.pack(pady=10, fill=tk.X)

        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0)
        )

        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            output_frame, height=15, wrap=tk.WORD, font=("Courier", 9)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for different output types
        self.output_text.tag_config(self.TAG_INFO, foreground="black")
        self.output_text.tag_config(self.TAG_ERROR, foreground="red")
        self.output_text.tag_config(self.TAG_SUCCESS, foreground="green")
        self.output_text.tag_config(self.TAG_WARNING, foreground="orange")

    def log_output(self, message: str, tag: str = None):
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

    def _safe_log_output(self, message: str, tag: str):
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

    def update_status(self, message: str):
        """Update status label.

        Args:
            message: The status message to display.
        """
        self.root.after_idle(lambda: self._safe_update_status(message))

    def _safe_update_status(self, message: str):
        """Thread-safe status update."""
        self.status_label.config(text=message)

    def get_selected_script(self) -> Optional[Path]:
        """Get the currently selected script.

        Returns:
            Path to selected script or None if no selection.
        """
        selection = self.scripts_listbox.curselection()
        if selection:
            index = selection[0]
            return self.scripts[index]
        return None

    def run_selected_script(self):
        """Run the selected script in a separate thread."""
        script = self.get_selected_script()
        if not script:
            self.log_output("No script selected", self.TAG_ERROR)
            return

        self.run_script(script)

    def run_all_scripts(self):
        """Run all scripts sequentially."""
        if not self.scripts:
            self.log_output("No scripts found", self.TAG_ERROR)
            return

        def run_all():
            for i, script in enumerate(self.scripts):
                self.log_output(
                    f"Running script {i+1}/{len(self.scripts)}: {script.name}", self.TAG_INFO
                )
                self.scripts_listbox.selection_clear(0, tk.END)
                self.scripts_listbox.selection_set(i)
                self.scripts_listbox.see(i)

                success = self.run_script(script, wait=True)
                if not success:
                    self.log_output(
                        f"Script {script.name} failed, stopping execution", self.TAG_ERROR
                    )
                    break

            self.log_output("All scripts execution completed", self.TAG_SUCCESS)
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
            self.log_output(f"Starting: {script.name}", self.TAG_INFO)
            self.update_status(f"Running: {script.name}")
            self.progress.start()

            # Enable stop button when script starts
            self.root.after_idle(lambda: self.stop_button.config(state=tk.NORMAL))

            # Run the script
            process = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.utils_dir.parent,
            )

            self.running_processes[script.name] = process

            # Read output in real-time
            def read_output():
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        self.log_output(output.strip())

                # Wait for process to complete
                process.wait()
                return_code = process.returncode

                if return_code == 0:
                    self.log_output(f"✅ {script.name} completed successfully", self.TAG_SUCCESS)
                else:
                    self.log_output(
                        f"❌ {script.name} failed with return code {return_code}",
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
            self.log_output(f"Error running {script.name}: {str(e)}", self.TAG_ERROR)
            self.progress.stop()
            self.update_status("Error")
            # Disable stop button on error
            self.root.after_idle(self._update_stop_button_state)
            return False

    def _update_stop_button_state(self):
        """Update stop button state based on running processes."""
        if self.running_processes:
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.stop_button.config(state=tk.DISABLED)

    def stop_selected_script(self):
        """Stop the selected script if it's running."""
        script = self.get_selected_script()
        if not script:
            self.log_output("No script selected", self.TAG_ERROR)
            return

        if script.name in self.running_processes:
            try:
                process = self.running_processes[script.name]
                process.terminate()
                self.log_output(f"Stopped: {script.name}", self.TAG_WARNING)
                del self.running_processes[script.name]
                # Disable stop button if no processes are running
                self._update_stop_button_state()
                self.progress.stop()
                self.update_status("Ready")
            except Exception as e:
                self.log_output(f"Error stopping {script.name}: {str(e)}", self.TAG_ERROR)
        else:
            self.log_output(f"Script {script.name} is not running", self.TAG_WARNING)

    def clear_output(self):
        """Clear the output text area."""
        self.output_text.delete(1.0, tk.END)
        self.log_output("Output cleared", self.TAG_INFO)

    def quit_application(self):
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


def main():
    """Launch the utils runner GUI."""
    try:
        # Create and run the GUI
        root = tk.Tk()
        app = UtilsRunnerGUI(root)

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
