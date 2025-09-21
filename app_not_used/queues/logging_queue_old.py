"""Logging Queue voor YAPMO - Log messages naar UI/files."""

import queue
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from nicegui import app

from config import get_param


class LogLevel(Enum):
    """Log levels voor YAPMO."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    INFO_EXTRA = "INFO_EXTRA"
    DEBUG = "DEBUG"


@dataclass
class LogMessage:
    """Log message voor YAPMO."""
    timestamp: float
    level: LogLevel
    message: str


class LoggingQueue:
    """Queue voor log messages naar logging manager."""
    
    def __init__(self):
        """Initialize LoggingQueue."""
        # Queue configuration
        self.queue_depth = get_param("processing_queues", "logging_queue_depth")
        self.get_timeout = get_param("processing_queues", "get_log_timeout") / 1000.0  # Convert ms to seconds
        
        # Initialize queue (reserve 1 place for ERROR messages)
        self.queue = queue.Queue(maxsize=self.queue_depth - 1)
        self.abort_flag = False
        
        print(f"DEBUG: LoggingQueue initialized with depth={self.queue_depth}, timeout={self.get_timeout}s")
    
    def put_log(self, level: LogLevel, message: str) -> bool:
        """Put log message in queue.
        
        Args:
            level: LogLevel enum
            message: Log message string
            
        Returns:
            True if successfully added, False if queue full or aborted
        """
        if self.abort_flag:
            print(f"WARNING: Attempted to add {level.value} log but queue is aborted")
            return False
        
        # Create log message
        log_msg = LogMessage(
            timestamp=time.time(),
            level=level,
            message=message
        )
        
        try:
            # Try to put log in queue (non-blocking)
            self.queue.put_nowait(log_msg)
            print(f"DEBUG: Added {level.value} log to queue (size: {self.queue.qsize()})")
            return True
            
        except queue.Full:
            # Queue is full - this is an ERROR condition
            error_msg = f"Logging queue is full (depth={self.queue_depth-1}). Cannot process {level.value} log"
            print(f"ERROR: {error_msg}")
            
            # For ERROR level, try to put directly (reserved space)
            if level == LogLevel.ERROR:
                try:
                    # Use reserved space for ERROR messages
                    self.queue.put_nowait(log_msg)
                    print(f"DEBUG: Added ERROR log using reserved space")
                    return True
                except queue.Full:
                    # Even reserved space is full - critical error
                    critical_error = f"CRITICAL: Even reserved ERROR space is full. System cannot log errors."
                    print(f"ERROR: {critical_error}")
                    
                    # Log ERROR and exit application
                    # Note: Using app.shutdown() instead of sys.exit() for clean NiceGUI shutdown
                    # This is consistent with other exit functionality in the application
                    try:
                        app.shutdown()
                    except (AttributeError, RuntimeError):
                        # Fallback for test context or when NiceGUI is not fully initialized
                        import sys
                        sys.exit(1)
                    return False
            else:
                # For non-ERROR levels, just fail silently
                print(f"WARNING: Dropped {level.value} log due to queue full")
                return False
    
    def get_log(self) -> Optional[LogMessage]:
        """Get log message from queue.
        
        Returns:
            LogMessage object or None if timeout/aborted
        """
        if self.abort_flag:
            return None
        
        try:
            log_msg = self.queue.get(timeout=self.get_timeout)
            print(f"DEBUG: Retrieved {log_msg.level.value} log from queue (size: {self.queue.qsize()})")
            return log_msg
            
        except queue.Empty:
            # Timeout - this is normal, not an error
            return None
    
    def set_abort(self) -> None:
        """Set abort flag and clear queue."""
        print("DEBUG: Setting abort flag for LoggingQueue")
        self.abort_flag = True
        
        # Clear all items from queue
        cleared_count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                cleared_count += 1
            except queue.Empty:
                break
        
        print(f"DEBUG: Cleared {cleared_count} items from LoggingQueue")
    
    def is_aborted(self) -> bool:
        """Check if queue is aborted."""
        return self.abort_flag
    
    def size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()
    
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self.queue.full()
