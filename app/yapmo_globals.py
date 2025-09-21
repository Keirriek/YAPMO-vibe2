"""Global abort manager for YAPMO application."""

import threading
from typing import Callable, Dict, Any, Set


class GlobalAbortManager:
    """Global abort manager for handling abort requests across the application."""
    
    def __init__(self):
        self.abort_handlers: Dict[str, Callable] = {}
        self.active_processes: Set[str] = set()
        self.lock = threading.Lock()
        # Legacy support
        self.processing_active = False
    
    def register_abort_handler(self, page_name: str, handler: Callable) -> None:
        """Register an abort handler for a specific page."""
        self.abort_handlers[page_name] = handler
    
    def unregister_abort_handler(self, page_name: str) -> None:
        """Unregister an abort handler for a specific page."""
        if page_name in self.abort_handlers:
            del self.abort_handlers[page_name]
    
    def register_process(self, process_id: str) -> None:
        """Register an active process."""
        with self.lock:
            self.active_processes.add(process_id)
            # print(f"DEBUG: Process {process_id} registered. Active: {len(self.active_processes)}") #DEBUG_OFF Process registration
    
    def unregister_process(self, process_id: str) -> None:
        """Unregister a completed process."""
        with self.lock:
            self.active_processes.discard(process_id)
            # print(f"DEBUG: Process {process_id} unregistered. Active: {len(self.active_processes)}") #DEBUG_OFF Process unregistration
    
    def has_active_processes(self) -> bool:
        """Check if there are any active processes."""
        with self.lock:
            return len(self.active_processes) > 0
    
    def get_active_processes(self) -> list[str]:
        """Get list of active process IDs."""
        with self.lock:
            return list(self.active_processes)
    
    def set_processing_active(self, active: bool) -> None:
        """Legacy method for backward compatibility."""
        self.processing_active = active
    
    def is_processing_active(self) -> bool:
        """Legacy method for backward compatibility."""
        return self.processing_active or self.has_active_processes()
    
    def abort_all(self) -> None:
        """Abort all registered handlers."""
        for page_name, handler in self.abort_handlers.items():
            try:
                handler()
            except Exception as e:
                print(f"Error aborting {page_name}: {e}")


# Global instance
abort_manager = GlobalAbortManager()

# Global progress variables
test_progress_current: int = 0
progress_total_files: int = 0
progress_current: int = 0

# Global scan counter variables
scan_total_files: int = 0
scan_media_files: int = 0
scan_sidecars: int = 0
scan_total_directories: int = 0

# Queue management flags (removed - not needed)

# State coordination flags
ui_update_finished: bool = False

# Unified action flag
action_finished_flag: bool = False

# Abort flag
abort_requested: bool = False

# Processing flags
stop_processing_flag: bool = False

# UI update timer (will be set by NiceGUI)
ui_update_timer: Any = None
