"""Error Dialog Manager for APGI Framework to prevent dialog overload."""

import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from enum import Enum
from tkinter import messagebox
from typing import Dict, List, Optional

from ..logging.standardized_logging import get_logger


class ErrorDialogType(Enum):
    """Types of error dialogs."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class QueuedError:
    """Represents a queued error message."""

    message: str
    dialog_type: ErrorDialogType
    title: str
    details: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    similar_errors: int = 1


class ErrorDialogManager:
    """Manages error dialogs to prevent overload by queuing and aggregating similar errors."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "ErrorDialogManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.logger = get_logger(__name__)

            # Error queue and processing
            self._error_queue: queue.Queue = queue.Queue()
            self._processing_active = False
            self._processing_thread: Optional[threading.Thread] = None

            # Aggregation settings
            self._aggregation_window = 5.0  # 5 seconds
            self._max_dialogs_per_minute = 10
            self._dialog_timestamps: List[float] = []

            # Similar error tracking
            self._recent_errors: Dict[str, QueuedError] = {}
            self._recent_errors_lock = threading.Lock()
            self._cleanup_interval = 60.0  # Clean up old errors every minute

            # Start processing thread
            self._start_processing()

    def _start_processing(self) -> None:
        """Start the error processing thread."""
        if not self._processing_active:
            self._processing_active = True
            self._processing_thread = threading.Thread(
                target=self._process_error_queue, daemon=True, name="ErrorDialogManager"
            )
            if self._processing_thread:
                self._processing_thread.start()
            self.logger.info("Error dialog manager started")

    def show_error(
        self,
        message: str,
        title: str = "Error",
        dialog_type: ErrorDialogType = ErrorDialogType.ERROR,
        details: Optional[str] = None,
        parent: Optional[tk.Tk] = None,
    ) -> None:
        """Queue an error dialog for display."""
        queued_error = QueuedError(
            message=message, dialog_type=dialog_type, title=title, details=details
        )

        try:
            self._error_queue.put_nowait(queued_error)
        except queue.Full:
            self.logger.warning("Error queue is full, dropping error message")

    def _process_error_queue(self) -> None:
        """Process queued errors with rate limiting and aggregation."""
        while self._processing_active:
            try:
                # Get error from queue with timeout
                try:
                    queued_error = self._error_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                # Check rate limiting
                if self._is_rate_limited():
                    self.logger.debug("Rate limit reached, queuing error for later")
                    # Put it back in queue for later processing
                    time.sleep(1.0)
                    self._error_queue.put(queued_error)
                    continue

                # Check for similar errors to aggregate
                aggregated_error = self._check_aggregation(queued_error)

                # Display the error
                self._display_error_dialog(aggregated_error, parent=None)

                # Clean up old errors periodically
                self._cleanup_old_errors()

            except Exception as e:
                self.logger.error(f"Error processing error queue: {e}")

    def _is_rate_limited(self) -> bool:
        """Check if we've exceeded the rate limit for dialogs."""
        current_time = time.time()

        # Remove old timestamps (older than 1 minute)
        self._dialog_timestamps = [ts for ts in self._dialog_timestamps if current_time - ts < 60.0]

        # Check if we've exceeded the limit
        if len(self._dialog_timestamps) >= self._max_dialogs_per_minute:
            return True

        # Add current timestamp
        self._dialog_timestamps.append(current_time)
        return False

    def _check_aggregation(self, new_error: QueuedError) -> QueuedError:
        """Check if this error can be aggregated with similar recent errors."""
        current_time = time.time()

        # Create a key for similarity checking
        error_key = f"{new_error.title}:{new_error.message[:50]}"

        # Check for similar recent errors
        with self._recent_errors_lock:
            if error_key in self._recent_errors:
                recent_error = self._recent_errors[error_key]

                # Check if within aggregation window
                if current_time - recent_error.timestamp < self._aggregation_window:
                    # Aggregate the error
                    recent_error.similar_errors += 1
                    recent_error.timestamp = current_time

                    # Update message to show count
                    if recent_error.similar_errors > 1:
                        recent_error.message = (
                            f"{new_error.message} "
                            f"(occurred {recent_error.similar_errors} times)"
                        )

                    self.logger.debug(
                        f"Aggregated error: {error_key} " f"(count: {recent_error.similar_errors})"
                    )
                    return recent_error

            # No aggregation, store as new error
            self._recent_errors[error_key] = new_error
            return new_error

    def _cleanup_old_errors(self) -> None:
        """Clean up old errors from the tracking dictionary."""
        current_time = time.time()

        with self._recent_errors_lock:
            # Remove errors older than cleanup interval
            old_keys = [
                key
                for key, error in self._recent_errors.items()
                if current_time - error.timestamp > self._cleanup_interval
            ]

            for key in old_keys:
                del self._recent_errors[key]

        if old_keys:
            self.logger.debug(f"Cleaned up {len(old_keys)} old error entries")

    def _display_error_dialog(
        self, queued_error: QueuedError, parent: Optional[tk.Tk] = None
    ) -> None:
        """Display an error dialog in the main thread."""

        def show_dialog() -> None:
            try:
                # Choose appropriate dialog based on type
                if queued_error.dialog_type == ErrorDialogType.ERROR:
                    messagebox.showerror(
                        queued_error.title,
                        queued_error.message,
                        parent=parent,  # type: ignore[arg-type]
                    )
                elif queued_error.dialog_type == ErrorDialogType.WARNING:
                    messagebox.showwarning(
                        queued_error.title,
                        queued_error.message,
                        parent=parent,  # type: ignore[arg-type]
                    )
                else:  # INFO
                    messagebox.showinfo(
                        queued_error.title,
                        queued_error.message,
                        parent=parent,  # type: ignore[arg-type]
                    )

                # Log the display
                self.logger.info(
                    f"Displayed {queued_error.dialog_type.value} dialog: "
                    f"{queued_error.title} - {queued_error.message}"
                )

            except Exception as e:
                self.logger.error(f"Error displaying dialog: {e}")

        # Schedule dialog display in main thread
        if parent and parent.winfo_exists():
            parent.after(0, show_dialog)
        else:
            # Try to find the main application window
            try:
                # Get all existing tkinter windows
                root = getattr(tk, "_default_root", None)
                windows = []
                if root is not None:
                    windows = [
                        widget
                        for widget in root.winfo_children()
                        if isinstance(widget, (tk.Tk, tk.Toplevel))
                    ]
                if windows:
                    windows[0].after(0, show_dialog)
                else:
                    self.logger.warning("No suitable parent window found for dialog")
            except Exception:
                self.logger.warning("Could not find parent window for dialog")

    def clear_queue(self) -> None:
        """Clear all pending error dialogs."""
        while not self._error_queue.empty():
            try:
                self._error_queue.get_nowait()
            except queue.Empty:
                break
        self.logger.info("Cleared error dialog queue")

    def get_queue_size(self) -> int:
        """Get the current size of the error queue."""
        return self._error_queue.qsize()

    def shutdown(self) -> None:
        """Shutdown the error dialog manager."""
        self._processing_active = False
        if self._processing_thread:
            self._processing_thread.join(timeout=2.0)
        self.logger.info("Error dialog manager shutdown")


# Global instance
error_dialog_manager: ErrorDialogManager = ErrorDialogManager()


def show_error_dialog(
    message: str,
    title: str = "Error",
    dialog_type: ErrorDialogType = ErrorDialogType.ERROR,
    details: Optional[str] = None,
    parent: Optional[tk.Tk] = None,
) -> None:
    """Convenience function to show an error dialog with rate limiting."""
    error_dialog_manager.show_error(
        message=message,
        title=title,
        dialog_type=dialog_type,
        details=details,
        parent=parent,
    )


def show_error(message: str, title: str = "Error", parent: Optional[tk.Tk] = None) -> None:
    """Show an error dialog."""
    show_error_dialog(message, title, ErrorDialogType.ERROR, parent=parent)


def show_warning(message: str, title: str = "Warning", parent: Optional[tk.Tk] = None) -> None:
    """Show a warning dialog."""
    show_error_dialog(message, title, ErrorDialogType.WARNING, parent=parent)


def show_info(message: str, title: str = "Information", parent: Optional[tk.Tk] = None) -> None:
    """Show an info dialog."""
    show_error_dialog(message, title, ErrorDialogType.INFO, parent=parent)
