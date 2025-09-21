"""Logging Manager voor YAPMO - Queue consumer voor logging."""

import asyncio
import os
from pathlib import Path
from typing import Optional

from config import get_param
from queues.logging_queue import LoggingQueue, LogMessage, LogLevel


class LoggingManager:
    """Logging manager voor YAPMO met queue-based processing."""
    
    def __init__(self, logging_queue: LoggingQueue):
        """Initialize LoggingManager met LoggingQueue."""
        self.logging_queue = logging_queue
        
        # Load configuratie parameters
        self.log_enabled = get_param("logging", "log_enabled")
        self.log_terminal = get_param("logging", "log_terminal")
        self.log_clean = get_param("logging", "log_clean")
        self.log_file = get_param("logging", "log_file")
        self.log_path = get_param("logging", "log_path")
        self.log_extended = get_param("logging", "log_extended")
        self.debug_mode = get_param("logging", "debug_mode")
        
        # File paths
        self.log_file_path = Path(self.log_path) / self.log_file
        self.debug_file_path = Path(self.log_path) / "debug.log"
        
        # Initialize logging
        self._initialize_logging()
        
        print("DEBUG: LoggingManager initialized successfully")
    
    def _initialize_logging(self) -> None:
        """Initialize logging files."""
        try:
            # Ensure log directory exists
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Clean log file if requested
            if self.log_clean and self.log_file_path.exists():
                self.log_file_path.unlink()
                print(f"DEBUG: Removed existing log file: {self.log_file_path}")
            
            # Clean debug file if requested
            if self.log_clean and self.debug_file_path.exists():
                self.debug_file_path.unlink()
                print(f"DEBUG: Removed existing debug file: {self.debug_file_path}")
            
            print("DEBUG: Logging initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Logging initialization failed: {e}"
            print(f"ERROR: {error_msg}")
            raise
    
    def _should_log_level(self, level: LogLevel) -> bool:
        """Check if log level should be processed based on config."""
        if not self.log_enabled:
            # Only process NOTICE, ERROR, WARNING when log_enabled=false
            return level in [LogLevel.NOTICE, LogLevel.ERROR, LogLevel.WARNING]
        else:
            # Process INFO, NOTICE, ERROR, WARNING when log_enabled=true
            if level in [LogLevel.INFO, LogLevel.NOTICE, LogLevel.ERROR, LogLevel.WARNING]:
                return True
            # Process EXTENDED only if log_extended=true
            if level == LogLevel.EXTENDED:
                return self.log_extended
            # Process DEBUG only if debug_mode=true
            if level == LogLevel.DEBUG:
                return self.debug_mode
            return False
    
    def _should_log_to_terminal(self, level: LogLevel) -> bool:
        """Check if log should go to terminal."""
        return self.log_terminal and self._should_log_level(level)
    
    def _should_log_to_file(self, level: LogLevel) -> bool:
        """Check if log should go to log file."""
        return level in [LogLevel.INFO, LogLevel.NOTICE, LogLevel.ERROR, LogLevel.WARNING, LogLevel.EXTENDED]
    
    def _should_log_to_debug(self, level: LogLevel) -> bool:
        """Check if log should go to debug file."""
        return self.debug_mode and level == LogLevel.DEBUG
    
    def _format_log_message(self, log_msg: LogMessage) -> str:
        """Format log message for output."""
        import datetime
        timestamp_str = datetime.datetime.fromtimestamp(log_msg.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp_str}] {log_msg.level.value}: {log_msg.message}"
    
    def _log_to_terminal(self, log_msg: LogMessage) -> None:
        """Log to terminal."""
        if self._should_log_to_terminal(log_msg.level):
            formatted_msg = self._format_log_message(log_msg)
            print(formatted_msg)
    
    def _log_to_file(self, log_msg: LogMessage) -> None:
        """Log to log file."""
        if self._should_log_to_file(log_msg.level):
            try:
                formatted_msg = self._format_log_message(log_msg)
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(formatted_msg + '\n')
            except Exception as e:
                print(f"ERROR: Failed to write to log file: {e}")
    
    def _log_to_debug(self, log_msg: LogMessage) -> None:
        """Log to debug file."""
        if self._should_log_to_debug(log_msg.level):
            try:
                formatted_msg = self._format_log_message(log_msg)
                with open(self.debug_file_path, 'a', encoding='utf-8') as f:
                    f.write(formatted_msg + '\n')
            except Exception as e:
                print(f"ERROR: Failed to write to debug file: {e}")
    
    async def start_consumer(self) -> None:
        """Start consuming logs from queue and writing to outputs."""
        print("DEBUG: Starting logging consumer")
        
        while True:
            if self.logging_queue.is_aborted():
                print("DEBUG: Logging consumer stopped due to abort")
                break
            
            # Get log from queue
            log_msg = self.logging_queue.get_log()
            
            if log_msg:
                # Check if we should process this log level
                if self._should_log_level(log_msg.level):
                    # Log to all appropriate outputs
                    self._log_to_terminal(log_msg)
                    self._log_to_file(log_msg)
                    self._log_to_debug(log_msg)
                    
                    # TODO: Add UI logging when UI component is ready
                    # self._log_to_ui(log_msg)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.01)
        
        print("DEBUG: Logging consumer finished")
    
    def close(self) -> None:
        """Close logging manager."""
        print("DEBUG: LoggingManager closed")
