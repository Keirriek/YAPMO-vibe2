#YAPMO_V3.0
"""Logging Integration  - Integrates result processor logs with existing logging service."""

import queue
import threading
import time
from typing import Optional
from core.logging_service import logging_service


class LoggingIntegration:
    """Integrates result processor logs with the existing logging service."""
    
    def __init__(self, logging_queue: queue.Queue):
        """
        Initialize the logging integration.
        
        Args:
            logging_queue: Queue containing log messages from result processor
        """
        self.logging_queue = logging_queue
        self.running = False
        self.thread = None
        self.processed_count = 0
        
    def start(self):
        """Start the logging integration in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the logging integration."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
    
    def _process_loop(self):
        """Main processing loop for log messages."""
        while self.running:
            try:
                # Try to get a log message from the queue
                try:
                    log_message = self.logging_queue.get(timeout=0.1)
                    self._process_log_message(log_message)
                except queue.Empty:
                    # No messages available, continue
                    continue
                    
            except Exception as e:
                logging_service.log("ERROR", f"Error in logging integration loop: {e}")
                time.sleep(0.1)
    
    def _process_log_message(self, log_message: str):
        """
        Process a single log message and send it to the logging service.
        
        Args:
            log_message: Log message from result processor
        """
        try:
            # Parse the log message format: "LEVEL: message"
            if ": " in log_message:
                level, message = log_message.split(": ", 1)
                level = level.strip().upper()
                message = message.strip()
                
                # Map levels to logging service levels
                if level == "INFO":
                    logging_service.log("INFO", message)
                elif level == "DEBUG":
                    logging_service.log("DEBUG", message)
                elif level == "WARNING":
                    logging_service.log("WARNING", message)
                elif level == "ERROR":
                    logging_service.log("ERROR", message)
                elif level == "INFO_EXTRA":
                    logging_service.log("INFO_EXTRA", message)
                elif level == "TEST_AI":
                    logging_service.log("TEST_AI", message)
                elif level == "TEST1":
                    logging_service.log("TEST1", message)
                elif level == "TEST2":
                    logging_service.log("TEST2", message)
                elif level == "TEST3":
                    logging_service.log("TEST3", message)
                elif level == "TEST4":
                    logging_service.log("TEST4", message)
                else:
                    # Default to WARNING for unknown levels
                    logging_service.log("WARNING", "UNKOWN LEVEL: " + log_message)
            else:
                # If no level specified, treat as WARNING
                logging_service.log("WARNING", "NO LEVEL: " + log_message)
            
            self.processed_count += 1
            
        except Exception as e:
            logging_service.log("ERROR", f"Error processing log message '{log_message}': {e}")
    
    def get_processed_count(self) -> int:
        """Get the number of processed log messages."""
        return self.processed_count
    
    def is_queue_empty(self) -> bool:
        """Check if the logging queue is empty."""
        return self.logging_queue.empty()
    
    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Wait for all log messages to be processed.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all messages processed, False if timeout
        """
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < timeout:
            if self.is_queue_empty():
                # Give a small delay to ensure all messages are processed
                time.sleep(0.1)
                if self.is_queue_empty():
                    return True
            time.sleep(0.1)
        
        return False
