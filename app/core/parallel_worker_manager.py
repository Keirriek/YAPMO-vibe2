#YAPMO_V3.0
"""Parallel Worker Manager for file processing."""

import queue
import threading
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Callable, Optional
from core.logging_service import logging_service


class ParallelWorkerManager:
    """Manages parallel worker processes for file processing."""
    
    def __init__(self, max_workers: int, progress_callback: Optional[Callable] = None):
        """
        Initialize the parallel worker manager.
        
        Args:
            max_workers: Maximum number of parallel workers
            progress_callback: Optional callback for progress updates
        """
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        self.executor = None
        self.pending_futures = []
        self.result_queue = queue.Queue()
        self.logging_queue = queue.Queue()
        self.worker_counter = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.lock = threading.Lock()
        
    def start_workers(self):
        """Start the worker processes."""
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
    
    def submit_file(self, file_path: str, image_extensions: list, video_extensions: list):
        """
        Submit a file for processing.
        
        Args:
            file_path: Path to the file to process
            image_extensions: List of image file extensions
            video_extensions: List of video file extensions
        """
        if self.executor is None:
            self.start_workers()
        
        # Import here to avoid pickling issues
        from core.process_single_file import process_single_file
        
        # Submit file to worker
        future = self.executor.submit(
            process_single_file, 
            file_path, 
            image_extensions, 
            video_extensions, 
            self.worker_counter % self.max_workers
        )
        
        self.pending_futures.append(future)
        self.worker_counter += 1
        
    def process_completed_workers(self):
        """
        Process completed worker results and update queues.
        This should be called regularly to process completed work.
        """
        completed_futures = []
        
        # Check for completed futures
        for future in self.pending_futures[:]:
            if future.done():
                completed_futures.append(future)
                self.pending_futures.remove(future)
        
        # Process completed futures
        for future in completed_futures:
            try:
                result = future.result()
                self._process_worker_result(result)
            except Exception as e:
                logging_service.log("ERROR", f"Worker processing failed: {e}")
                self.failed_files += 1
        
        return len(completed_futures)
    
    def _process_worker_result(self, result: Dict[str, Any]):
        """
        Process a worker result and update queues.
        
        Args:
            result: Result from worker process
        """
        with self.lock:
            self.processed_files += 1
            
            if result.get('success', False):
                self.successful_files += 1
            else:
                self.failed_files += 1
            
            # Extract log messages and put in logging queue
            if 'log_messages' in result:
                for log_msg in result['log_messages']:
                    self.logging_queue.put(log_msg)
            
            # Put result in result queue (without log_messages)
            result_copy = result.copy()
            if 'log_messages' in result_copy:
                del result_copy['log_messages']
            self.result_queue.put(result_copy)
            
            # Call progress callback if available
            if self.progress_callback:
                self.progress_callback('file_processed', {
                    'processed_files': self.processed_files,
                    'successful_files': self.successful_files,
                    'failed_files': self.failed_files
                })
    
    def get_result_queue(self) -> queue.Queue:
        """Get the result queue."""
        return self.result_queue
    
    def get_logging_queue(self) -> queue.Queue:
        """Get the logging queue."""
        return self.logging_queue
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        with self.lock:
            return {
                'processed_files': self.processed_files,
                'successful_files': self.successful_files,
                'failed_files': self.failed_files,
                'pending_files': len(self.pending_futures)
            }
    
    def is_complete(self) -> bool:
        """Check if all work is complete."""
        return len(self.pending_futures) == 0 and self.result_queue.empty() and self.logging_queue.empty()
    
    def shutdown(self):
        """Shutdown the worker manager."""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None