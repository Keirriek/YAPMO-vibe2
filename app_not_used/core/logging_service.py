"""Thread-safe logging service for YAPMO application."""

import threading
from collections import deque
from datetime import datetime
from typing import Optional
import json
from pathlib import Path


class LoggingService:
    """Thread-safe logging service with configurable routing."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._lock = threading.Lock()
            self._ui_messages = deque(maxlen=1000)
            self._config = self._load_config()
            self._clean_log_files_if_requested()  #TODO Check ENABLED Disabled: log clear only on Start Scanning
            self._initialized = True
    
    def _load_config(self) -> dict:
        """Load logging configuration from config.json."""
        try:
            config_path = Path("config.json")
            with config_path.open(encoding="utf-8") as f:
                config = json.load(f)
            return config.get("logging", {})
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "log_file_path": "./log/yapmo_log.log",
                "debug_file_path": "./log/yapmo_debug.log",
                "levels": {
                    "ERROR": ["ui", "t", "df"],
                    "WARNING": ["ui", "t", "df"],
                    "INFO": ["ui"],
                    "INFO_EXTRA": ["df"],
                    "DEBUG": ["df"],
                    "TEST_AI": [],
                    "TEST1": [],
                    "TEST2": [],
                    "TEST3": [],
                    "TEST4": []
                }
            }
    
    def log(self, level: str, message: str, worker_id: Optional[int] = None) -> None:
        """
        Log a message with level-based routing from config.
        
        Args:
            level: LOG level (ERROR, WARNING, INFO, INFO_EXTRA, DEBUG, TEST_AI, TEST1, TEST2, TEST3, TEST4)
            message: Log message
            worker_id: Optional worker ID
        """
        with self._lock:
            # Get routes from config
            levels_config = self._config.get("levels", {})
            routes = levels_config.get(level, [])
            
            # If no routes configured, don't log anything
            if not routes:
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            worker_str = f"Worker {worker_id}" if worker_id is not None else "Main"
            log_entry = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "worker_id": worker_id,
                "routes": routes
            }
            
            # Route to specific destinations based on config
            if "t" in routes:  # Terminal
                print(f"[{timestamp}] {worker_str} {level}: {message}")
            
            if "ui" in routes:  # UI logscreen
                self._ui_messages.append(log_entry)
            
            if "df" in routes:  # Debug file
                self._write_to_debug_file(log_entry)
            
            # Always write to main log file (if any route is configured)
            self._write_to_log_file(log_entry)
    
    def _ensure_log_directory(self, file_path: str) -> None:
        """Ensure log directory exists."""
        try:
            log_dir = Path(file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory: {e}")
    
    def _write_to_log_file(self, log_entry: dict) -> None:
        """Write to main log file."""
        try:
            log_file = self._config.get("log_file_path", "app.log")
            self._ensure_log_directory(log_file)
            with open(log_file, "a", encoding="utf-8") as f:
                worker_str = f"Worker {log_entry['worker_id']}" if log_entry['worker_id'] is not None else "Main"
                f.write(f"[{log_entry['timestamp']}] {worker_str} {log_entry['level']}: {log_entry['message']}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def _write_to_debug_file(self, log_entry: dict) -> None:
        """Write to debug log file."""
        try:
            debug_file = self._config.get("debug_file_path", "debug.log")
            self._ensure_log_directory(debug_file)
            with open(debug_file, "a", encoding="utf-8") as f:
                worker_str = f"Worker {log_entry['worker_id']}" if log_entry['worker_id'] is not None else "Main"
                f.write(f"[{log_entry['timestamp']}] {worker_str} {log_entry['level']}: {log_entry['message']}\n")
                f.flush()  #DEBUG check if this is really needed - tested: not strictly necessary but ensures immediate visibility
        except Exception as e:
            print(f"Error writing to debug file: {e}")
    
    def get_ui_messages(self) -> list:
        """Get and clear UI messages."""
        with self._lock:
            messages = list(self._ui_messages)
            self._ui_messages.clear()
            return messages
    
    def _clean_log_files_if_requested(self) -> None:
        """Clean log files if log_clean is enabled in config."""
        try:
            log_clean = self._config.get("log_clean", False)
            if log_clean:
                # Clean main log file
                log_file = self._config.get("log_file_path", "./log/yapmo_log.log")
                log_path = Path(log_file)
                if log_path.exists():
                    log_path.unlink()
                    # Use logging service instead of direct print
                    # self.log("INFO_EXTRA", f"Cleaned main log file: {log_file}")
                
                # Clean debug log file
                debug_file = self._config.get("debug_file_path", "./log/yapmo_debug.log")
                debug_path = Path(debug_file)
                if debug_path.exists():
                    debug_path.unlink()
                    # Use logging service instead of direct print
                    # self.log("INFO_EXTRA", f"Cleaned debug log file: {debug_file}")
        except Exception as e:
            # Use logging service for error messages
            self.log("ERROR", f"Error cleaning log files: {e}")
    
    def reload_config(self) -> None:
        """Reload configuration from config.json."""
        with self._lock:
            self._config = self._load_config()
            self._clean_log_files_if_requested()  #TODO Check ENABLED Disabled: log clear only on Start Scanning


# Global instance
logging_service = LoggingService()
