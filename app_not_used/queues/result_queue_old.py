"""Result Queue for YAPMO - Metadata results naar database."""

import queue
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from nicegui import app

from config import get_param


@dataclass
class MetadataResult:
    """Metadata result van file processing."""
    file_path: str
    exif_data: Dict[str, Any]
    file_info: Dict[str, Any]
    hash_value: str
    file_size: int
    timestamp: float
    is_end_signal: bool = False  # Signal to indicate end of results


class ResultQueue:
    """Queue voor metadata results naar database manager."""
    
    def __init__(self, database_manager):
        """Initialize ResultQueue met database manager."""
        self.database_manager = database_manager
        
        # Queue configuration
        self.queue_depth = get_param("processing_queues", "result_queue_depth")
        self.get_timeout = get_param("processing_queues", "get_result_timeout") / 1000.0  # Convert ms to seconds
        
        # Initialize queue
        self.queue = queue.Queue(maxsize=self.queue_depth)
        self.abort_flag = False
        
        print(f"DEBUG: ResultQueue initialized with depth={self.queue_depth}, timeout={self.get_timeout}s")
    
    def put_result(self, result: MetadataResult) -> bool:
        """Put metadata result in queue.
        
        Args:
            result: MetadataResult object
            
        Returns:
            True if successfully added, False if queue full or aborted
        """
        if self.abort_flag:
            print(f"WARNING: Attempted to add result for {result.file_path} but queue is aborted")
            return False
        
        try:
            # Try to put result in queue (non-blocking)
            self.queue.put_nowait(result)
            print(f"DEBUG: Added result for {result.file_path} to queue (size: {self.queue.qsize()})")
            return True
            
        except queue.Full:
            # Queue is full - this is an ERROR condition
            error_msg = f"Result queue is full (depth={self.queue_depth}). Cannot process {result.file_path}"
            print(f"ERROR: {error_msg}")
            
            # Log ERROR and exit application
            # TODO: Replace with proper logging service
            print(f"ERROR: {error_msg}")
            print("ERROR: Application will exit due to queue full condition")
            
            # Exit application
            # Note: Using app.shutdown() instead of sys.exit() for clean NiceGUI shutdown
            # This is consistent with other exit functionality in the application
            app.shutdown()
            return False
    
    def get_result(self) -> Optional[MetadataResult]:
        """Get metadata result from queue.
        
        Returns:
            MetadataResult object or None if timeout/aborted
        """
        if self.abort_flag:
            return None
        
        try:
            result = self.queue.get(timeout=self.get_timeout)
            print(f"DEBUG: Retrieved result for {result.file_path} from queue (size: {self.queue.qsize()})")
            return result
            
        except queue.Empty:
            # Timeout - this is normal, not an error
            return None
    
    def set_abort(self) -> None:
        """Set abort flag and clear queue."""
        print("DEBUG: Setting abort flag for ResultQueue")
        self.abort_flag = True
        
        # Clear all items from queue
        cleared_count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                cleared_count += 1
            except queue.Empty:
                break
        
        print(f"DEBUG: Cleared {cleared_count} items from ResultQueue")
    
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
