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
        
        # Batch processing
        self.batch_buffer = []
        from config import get_param
        self.batch_size = get_param("database", "database_write_batch_size")
        
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
        # Process any remaining results in buffer
        with self.lock:
            if self.batch_buffer:
                self._process_batch()
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
        Process a single result and add to batch buffer.
        
        Args:
            result: Result from worker process
        """
        with self.lock:
            self.processed_count += 1
            logging_service.log("DEBUG", f"_process_result: Processing result #{self.processed_count}")#DEBUG_ON _process_result: Processing result #X
            
            # Add to batch buffer
            self.batch_buffer.append(result)
            logging_service.log("DEBUG", f"_process_result: Added to buffer, buffer size now {len(self.batch_buffer)}/{self.batch_size}")#DEBUG_ON _process_result: Added to buffer, buffer size now X/Y
            
            # Check if this is END_OF_BATCH marker
            if result.get('is_last_result', False):
                logging_service.log("DEBUG", "_process_result: END_OF_BATCH marker detected, processing final batch")#DEBUG_ON _process_result: END_OF_BATCH marker detected, processing final batch
                # Process final batch
                self._process_batch()
                return
            
            # Check if batch is full
            if len(self.batch_buffer) >= self.batch_size:
                logging_service.log("DEBUG", f"_process_result: Batch full ({len(self.batch_buffer)}/{self.batch_size}), processing batch")#DEBUG_ON _process_result: Batch full (X/Y), processing batch
                self._process_batch()
    
    def _process_batch(self):
        """Process the current batch buffer."""
        logging_service.log("DEBUG", f"_process_batch called with {len(self.batch_buffer)} results in buffer")#DEBUG_ON _process_batch called with X results in buffer
        
        if not self.batch_buffer:
            # logging_service.log("DEBUG", "_process_batch: No results in buffer, returning")#DEBUG_OFF _process_batch: No results in buffer, returning
            return
            
        # Count successes and failures
        for result in self.batch_buffer:
            if result.get('success', False):
                self.successful_count += 1
            else:
                self.failed_count += 1
                # Log failures
                logging_service.log("WARNING", f"Failed to process file {result.get('file_path', 'unknown')}: {result.get('log_message', 'Unknown error')}")
        
        # logging_service.log("DEBUG", f"_process_batch: Sending {len(self.batch_buffer)} results to database")#DEBUG_OFF _process_batch: Sending X results to database
        
        # Send batch to database (no copy needed for efficiency)
        from core.db_manager_v3 import db_add_result
        db_add_result(self.batch_buffer)
        
        # Clear buffer
        self.batch_buffer.clear()
        # logging_service.log("DEBUG", "_process_batch: Batch processed and buffer cleared")#DEBUG_OFF _process_batch: Batch processed and buffer cleared
    
    
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
