"""Global variables and services for YAPMO application."""

import contextlib
import json
import logging
import traceback as tb
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

import json5
from nicegui import ui

# pylint: disable=invalid-name

# ABORT signal - will be used to signal parallel processes and threads to stop
abort_requested = False

# Process status variables
processing_active = False
current_process_name = ""

# Progress tracking
progress_current = 0
progress_total = 0
progress_message = ""

# Results and data sharing
# These will be used to share results between different processes
process_results: list[object] = []
shared_data: dict[str, object] = {}

# UI control variables
# These will be used to control UI elements from different processes/threads
ui_update_needed = False
log_messages: list[str] = []
error_messages: list[str] = []

# NiceGUI update service
nicegui_update_timer = None
# nicegui_update_interval wordt nu uit config gehaald


class GlobalLoggingService:
    """Globale logging service voor de hele applicatie."""

    def __init__(self) -> None:
        """Initialize the logging service."""
        self.log_queue: Queue = Queue()
        self.ui_queue: Queue = Queue()  # Queue voor UI updates
        self.config: dict[str, object] = {}
        self.logging_thread: Thread | None = None
        self.should_stop = False
        self.ui_log_display: object = None  # type: ignore[assignment]

        # Load config
        self._load_config()

        # Start logging thread
        self._start_logging_thread()

    def _load_config(self) -> None:
        """Laad configuratie uit config.json."""
        try:
            # Probeer eerst in de huidige directory
            config_path = Path("config.json")
            if not config_path.exists():
                # Probeer in de app directory
                config_path = Path("app/config.json")
            if not config_path.exists():
                # Probeer in de parent directory
                config_path = Path("../config.json")

            with config_path.open(encoding="utf-8") as f:
                config_data = json5.load(f)
                self.config = config_data.get("logging", {})
        except (OSError, FileNotFoundError, json.JSONDecodeError):
            # Default config wordt nu uit config.py gehaald via get_param
            from config import get_param
            self.config = {
                "log_enabled": get_param("logging", "log_enabled"),
                "log_terminal": get_param("logging", "log_terminal"),
                "log_clean": get_param("logging", "log_clean"),
                "log_file": get_param("logging", "log_file"),
                "dev_log_enabled": get_param("logging", "dev_log_enabled"),
                "dev_log_file": get_param("logging", "dev_log_file"),
                "log_path": get_param("logging", "log_path"),
            }

    def _start_logging_thread(self) -> None:
        """Start de logging worker thread."""
        self.logging_thread = Thread(
            target=self._logging_worker, daemon=True)
        self.logging_thread.start()

    def _logging_worker(self) -> None:
        """Worker thread voor logging operaties."""
        log_file_path, dev_log_file_path = self._setup_log_files()
        self._clean_log_files(log_file_path, dev_log_file_path)

        while not self.should_stop:
            try:
                log_entry = self.log_queue.get(timeout=1)
                if log_entry is None:  # Stop signaal
                    break

                try:
                    # Process log entry
                    self._process_log_entry(log_entry, log_file_path, dev_log_file_path)
                except OSError:
                    # Handle file system errors specifically
                    logging.exception("File system error processing log")
                except Exception:
                    # Fallback for other unexpected errors
                    logging.exception("Unexpected error processing log")
                    logging.exception("Traceback: %s", tb.format_exc())

            except Empty:
                # Timeout is normaal, geen error
                continue
            except Exception:  # noqa: BLE001
                # Error logging alleen als log_terminal = true
                if self.config.get("log_terminal"):
                    import traceback
                    traceback.print_exc()
                continue

    def _setup_log_files(self) -> tuple[Path, Path]:
        """Set up log file paths and create directories."""
        # Check for missing config parameters and log warnings
        if "log_path" not in self.config:
            logging_service.log("WARNING", "Config parameter 'log_path' not found, using default: ./")
        if "log_file" not in self.config:
            logging_service.log("WARNING", "Config parameter 'log_file' not found, using default: yapmo.log")
        if "dev_log_file" not in self.config:
            logging_service.log("WARNING", "Config parameter 'dev_log_file' not found, using default: yapmo_dev.log")

        log_path = self.config.get("log_path")
        log_file = self.config.get("log_file")
        dev_log_file = self.config.get("dev_log_file")

        log_file_path = Path(str(log_path)) / str(log_file)
        dev_log_file_path = Path(str(log_path)) / str(dev_log_file)

        # Maak directories aan
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        dev_log_file_path.parent.mkdir(parents=True, exist_ok=True)

        return log_file_path, dev_log_file_path

    def _clean_log_files(self, log_file_path: Path, dev_log_file_path: Path) -> None:
        """Clean log files if configured."""
        # Check for missing config parameters and log warnings
        if "log_clean" not in self.config:
            logging_service.log("WARNING", "Config parameter 'log_clean' not found, using default: True")
        if self.config.get("log_clean"):
            try:
                log_file_path.write_text("", encoding="utf-8")
                dev_log_file_path.write_text("", encoding="utf-8")
            except OSError:
                pass

    def _process_log_entry(
        self,
        log_entry: dict[str, str],
        log_file_path: Path,
        dev_log_file_path: Path,
    ) -> None:
        """Process a single log entry."""
        level = log_entry["level"]
        message = log_entry["message"]
        timestamp = log_entry["timestamp"]

        # Log line maken
        log_line = f"{level} : {timestamp} {message}\n"

        # Terminal logging (alleen als log_terminal = true)
        if self.config.get("log_terminal"):  # Default naar false
            # DEBUG berichten alleen tonen als debug_mode = true
            if level != "DEBUG" or self.config.get("debug_mode"):
                logging.info(log_line.rstrip())

        # Check for missing config parameters and log warnings
        if "log_enabled" not in self.config:
            logging_service.log("WARNING", "Config parameter 'log_enabled' not found, using default: True")

        # File logging (alleen als log_enabled = true, behalve WARNING/ERROR/PROCESS)
        should_write_to_file = (
            self.config.get("log_enabled") or
            level in ["WARNING", "ERROR", "PROCESS"]
        )

        # DEBUG logging (alleen als debug_mode = true)
        if level == "DEBUG" and not self.config.get("debug_mode"):
            should_write_to_file = False

        if should_write_to_file and level != "DEV":
            try:
                with log_file_path.open("a", encoding="utf-8") as f:
                    f.write(log_line)
            except OSError:
                pass

        # Check for missing config parameters and log warnings
        if "dev_log_enabled" not in self.config:
            logging_service.log("WARNING", "Config parameter 'dev_log_enabled' not found, using default: True")
        if "debug_mode" not in self.config:
            logging_service.log("WARNING", "Config parameter 'debug_mode' not found, using default: False")

        # DEV logging naar aparte file (alleen als dev_log_enabled = true)
        if level == "DEV" and self.config.get("dev_log_enabled"):
            try:
                with dev_log_file_path.open("a", encoding="utf-8") as f:
                    f.write(log_line)
            except OSError:
                pass

        # UI logging volgens de regels
        if self._should_show_in_ui(level):
            self.ui_queue.put(log_entry)

    def _should_show_in_ui(self, level: str) -> bool:
        """Determine if log entry should be shown in UI."""
        if level in ["WARNING", "ERROR", "PROCESS"]:
            return True
        if level == "DEV":
            value = self.config.get("dev_log_enabled", True)
            return bool(value) if value is not None else True
        if level == "DEBUG":
            value = self.config.get("debug_mode", False)
            return bool(value) if value is not None else False
        if level == "INFO":
            value = self.config.get("log_enabled", True)
            return bool(value) if value is not None else True
        return False

    def get_ui_messages(self) -> list[dict[str, str]]:
        """Haal alle UI berichten op (thread-safe)."""
        messages = []
        while not self.ui_queue.empty():
            try:
                messages.append(self.ui_queue.get_nowait())
            except Empty:
                break
        return messages

    def log(self, level: str, message: str) -> None:
        """Globale log functie - één simpele call voor alles."""
        # Timestamp maken met lokale tijdzone
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Bericht in queue plaatsen
        self.log_queue.put({
            "level": level,
            "message": message,
            "timestamp": timestamp,
        })

    def set_ui_display(self, ui_display: object) -> None:
        """Zet UI display referentie."""
        self.ui_log_display = ui_display

    def stop(self) -> None:
        """Stop de logging service."""
        self.should_stop = True
        self.log_queue.put(None)  # Stop signaal
        if self.logging_thread and self.logging_thread.is_alive():
            self.logging_thread.join(timeout=5)


# Globale logging service instantie
logging_service = GlobalLoggingService()


class NiceGUIUpdateService:
    """Universele NiceGUI update service voor alle pagina's."""

    def __init__(self) -> None:
        """Initialize the NiceGUI update service."""
        self.update_callbacks: list[object] = []
        self.timer: object = None
        self.interval = 200  # Default 200ms
        self.is_running = False

    def set_interval(self, interval_ms: int) -> None:
        """Set the update interval in milliseconds."""
        self.interval = interval_ms

    def add_callback(self, callback: Callable) -> None:
        """Add a callback function to be called on each update."""
        self.update_callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback function."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

    def _execute_callbacks(self) -> None:
        """Execute all registered callbacks."""
        for callback in self.update_callbacks:
            try:
                if callable(callback):
                    callback()
            except (RuntimeError, AttributeError):
                # Handle UI component errors specifically
                logging.exception("UI update error")
            except Exception:
                # Fallback for other unexpected errors
                logging.exception("Unexpected error in UI update")

    def _schedule_next_update(self, update_loop: Callable) -> None:
        """Schedule the next update."""
        if self.is_running:
            try:
                self.timer = ui.timer(self.interval / 1000.0, update_loop)
            except (RuntimeError, AttributeError):
                # Handle UI timer errors specifically
                logging.exception("Timer start error")
            except Exception:
                # Fallback for other unexpected errors
                logging.exception("Unexpected error starting timer")

    def _start_first_update(self, update_loop: Callable) -> None:
        """Start the first update."""
        try:
            self.timer = ui.timer(self.interval / 1000.0, update_loop)
        except (RuntimeError, AttributeError):
            # Handle UI timer errors specifically
            logging.exception("Timer start error")
        except Exception:
            # Fallback for other unexpected errors
            logging.exception("Unexpected error starting timer")

    def start(self) -> None:
        """Start the update timer."""
        if self.is_running or ui is None:
            return

        self.is_running = True

        def update_loop() -> None:
            if not self.is_running:
                return

            # Execute callbacks
            self._execute_callbacks()

            # Schedule next update
            self._schedule_next_update(update_loop)

        # Start first update
        self._start_first_update(update_loop)

    def stop(self) -> None:
        """Stop the update timer."""
        self.is_running = False
        try:
            # Stop timer
            if self.timer and hasattr(self.timer, "cancel"):
                self.timer.cancel()
        except (RuntimeError, AttributeError):
            # Handle UI timer errors specifically
            logging.exception("Timer stop error")
        except Exception:
            # Fallback for other unexpected errors
            logging.exception("Unexpected error stopping timer")

    def clear_callbacks(self) -> None:
        """Clear all callbacks."""
        self.update_callbacks.clear()


# Global instance
nicegui_update_service = NiceGUIUpdateService()

# Global abort button manager
class AbortButtonManager:
    """Global manager for the abort button state."""

    def __init__(self) -> None:
        """Initialize the abort button manager."""
        self.abort_button: object = None
        self._processing_active = False
        # Dictionary to store abort handlers per page
        self._abort_handlers: dict[str, Callable] = {}

    def set_abort_button(self, button: object) -> None:
        """Set the abort button reference."""
        self.abort_button = button

    def set_processing_active(self, *, active: bool) -> None:
        """Set processing state and update abort button."""
        self._processing_active = active
        if (
            self.abort_button
            and hasattr(self.abort_button, "enable")
            and hasattr(self.abort_button, "disable")
        ):
            if active:
                self.abort_button.enable()
            else:
                self.abort_button.disable()

    def is_processing_active(self) -> bool:
        """Check if processing is active."""
        return self._processing_active

    def register_abort_handler(self, page_name: str, handler: Callable) -> None:
        """Register an abort handler for a specific page."""
        self._abort_handlers[page_name] = handler

    def unregister_abort_handler(self, page_name: str) -> None:
        """Unregister an abort handler for a specific page."""
        if page_name in self._abort_handlers:
            del self._abort_handlers[page_name]

    def trigger_abort(self) -> None:
        """Trigger abort for all registered handlers."""
        for handler in self._abort_handlers.values():
            with contextlib.suppress(Exception):
                handler()

        # Reset processing state
        self.set_processing_active(active=False)

# Global abort button manager instance
abort_button_manager = AbortButtonManager()
