#YAPMO_V3.0
"""Result Processor - Processes results from the result queue."""

import queue
import threading
import time
from typing import Dict, Any
from core.logging_service_v2 import logging_service


class ResultProcessor:
    """Processes results from the result queue and creates log messages."""
    
    def __init__(self, result_queue: queue.Queue, logging_queue: queue.Queue):
        """
        Initialize the result processor.
        
        Args:
            result_queue: Queue containing processing results
            logging_queue: Queue for log messages
        """
        self.result_queue = result_queue
        self.logging_queue = logging_queue
        self.processed_count = 0
        self.successful_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        # logging_service.log("DEBUG", "ResultProcessor initialized")#DEBUG_OFF ResultProcessor initialized
    
    def start(self):
        """Start the result processor in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        # logging_service.log("DEBUG", "ResultProcessor started")#DEBUG_OFF ResultProcessor started
    
    def stop(self):
        """Stop the result processor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        # logging_service.log("DEBUG", "ResultProcessor stopped")#DEBUG_OFF ResultProcessor stopped
    
    def _process_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                # Try to get a result from the queue
                try:
                    result = self.result_queue.get(timeout=0.1)
                    self._process_result(result)
                except queue.Empty:
                    # No results available, continue
                    continue
                    
            except Exception as e:
                logging_service.log("ERROR", f"Error in result processing loop: {e}")
                time.sleep(0.1)
    
    def _process_result(self, result: Dict[str, Any]):
        """
        Process a single result and send to database.
        
        Args:
            result: Result from worker process
        """
        with self.lock:
            self.processed_count += 1
            
            if result.get('success', False):
                self.successful_count += 1
                # Success → Database
                from core.db_manager_v2 import db_dummy
                db_dummy(result)
            else:
                self.failed_count += 1
                # Failure → WARNING log + Database
                logging_service.log("WARNING", f"Failed to process file {result.get('file_path', 'unknown')}: {result.get('log_message', 'Unknown error')}")
                from core.db_manager_v2 import db_dummy
                db_dummy(result)
    
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        with self.lock:
            return {
                'processed_count': self.processed_count,
                'successful_count': self.successful_count,
                'failed_count': self.failed_count
            }
    
    def is_queue_empty(self) -> bool:
        """Check if the result queue is empty."""
        return self.result_queue.empty()
    
    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Wait for all results to be processed.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all results processed, False if timeout
        """
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < timeout:
            if self.is_queue_empty():
                # Give a small delay to ensure all results are processed
                time.sleep(0.1)
                if self.is_queue_empty():
                    return True
            time.sleep(0.1)
        
        return False
