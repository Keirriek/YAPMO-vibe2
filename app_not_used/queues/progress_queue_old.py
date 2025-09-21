"""
Progress Queue voor YAPMO applicatie.

Deze module implementeert een queue voor progress updates van de ProcessManager
naar de UI. Het is geoptimaliseerd voor file-based processing van 200k+ files.
"""

import queue
import time
import logging
from typing import Optional, List
from dataclasses import dataclass
from config import ConfigManager

# Import config manager
try:
    from config import config_manager
except ImportError:
    # Fallback voor testing
    class MockConfigManager:
        def get_param(self, section: str, key: str, default=None):
            return default
    config_manager = MockConfigManager()

logger = logging.getLogger(__name__)

@dataclass
class ProgressUpdate:
    """Progress update voor UI"""
    task_id: str
    progress: float  # 0.0 - 100.0
    status: str      # "running", "completed", "error"
    eta: str         # Estimated time remaining
    message: str = ""  # Additional message
    timestamp: float = 0.0  # Timestamp when update was created

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class ProgressQueue:
    """
    Queue voor progress updates van ProcessManager naar UI.
    
    Features:
    - Thread-safe queue operations
    - Configurable queue depth en timeout
    - Abort functionality
    - Optimized voor file-based processing
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize ProgressQueue met config parameters"""
        # Config parameters
        self.queue_depth = config_manager.get_param('processing_queues', 'progress_queue_depth')
        self.get_timeout = config_manager.get_param('processing_queues', 'get_progress_timeout') / 1000.0
        
        # Queue setup
        self.queue = queue.Queue(maxsize=self.queue_depth)
        self.abort_flag = False
        
        logger.info(f"ProgressQueue initialized: depth={self.queue_depth}, timeout={self.get_timeout}s")
    
    async def put_progress(self, update: ProgressUpdate) -> bool:
        """
        Put progress update in queue (async wrapper)
        
        Args:
            update: ProgressUpdate object
            
        Returns:
            bool: True if successful, False if queue full or aborted
        """
        if self.abort_flag:
            logger.debug("ProgressQueue aborted, ignoring progress update")
            return False
        
        try:
            # Non-blocking put
            self.queue.put_nowait(update)
            logger.debug(f"Progress update queued: {update.task_id} - {update.progress:.1f}%")
            return True
        except queue.Full:
            logger.warning("ProgressQueue full, dropping update")
            return False
    
    def get_progress(self) -> Optional[ProgressUpdate]:
        """
        Get progress update from queue
        
        Returns:
            ProgressUpdate or None if timeout/aborted
        """
        if self.abort_flag:
            return None
        
        try:
            return self.queue.get(timeout=self.get_timeout)
        except queue.Empty:
            return None
    
    def get_all_progress(self) -> List[ProgressUpdate]:
        """
        Get all available progress updates (non-blocking)
        
        Returns:
            List of ProgressUpdate objects
        """
        updates = []
        
        while not self.queue.empty() and not self.abort_flag:
            try:
                update = self.queue.get_nowait()
                updates.append(update)
            except queue.Empty:
                break
        
        return updates
    
    def clear(self):
        """Clear all progress updates from queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("ProgressQueue cleared")
    
    def abort(self):
        """Abort queue operations"""
        self.abort_flag = True
        logger.info("ProgressQueue aborted")
    
    def reset(self):
        """Reset queue na abort"""
        self.abort_flag = False
        self.clear()
        logger.info("ProgressQueue reset")
    
    def is_aborted(self) -> bool:
        """Check if queue is aborted"""
        return self.abort_flag
    
    def size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def is_full(self) -> bool:
        """Check if queue is full"""
        return self.queue.full()
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()
