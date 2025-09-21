"""
Queue Manager voor YAPMO applicatie.

Deze module coördineert alle queues (ResultQueue, LoggingQueue, ProgressQueue)
en biedt een uniforme interface voor queue operaties.
"""

import logging
from typing import Optional, List
from config import ConfigManager

# Import queues
try:
    from queues.result_queue import ResultQueue, MetadataResult
    from queues.logging_queue import LoggingQueue, LogMessage, LogLevel
    from queues.progress_queue import ProgressQueue, ProgressUpdate
except ImportError:
    # Fallback voor testing
    class MockQueue:
        async def put_result(self, result): pass
        def get_result(self): return None
        async def put_log(self, message): pass
        def get_log(self): return None
        async def put_progress(self, update): pass
        def get_progress(self): return None
        def abort(self): pass
        def reset(self): pass
    
    ResultQueue = LoggingQueue = ProgressQueue = MockQueue
    MetadataResult = LogMessage = ProgressUpdate = None
    LogLevel = None

logger = logging.getLogger(__name__)

class QueueManager:
    """
    Queue Manager - Coördineert alle queues
    
    Features:
    - Unified interface voor alle queue operaties
    - ResultQueue voor metadata results
    - LoggingQueue voor log messages
    - ProgressQueue voor progress updates
    - Abort functionality voor alle queues
    """
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize QueueManager met alle queues"""
        # Initialize queues with proper dependencies
        # Note: We need to create a circular dependency here
        # ResultQueue needs DatabaseManager, but DatabaseManager needs ResultQueue
        # We'll create a temporary ResultQueue first, then update it
        self.result_queue = None  # Will be set after DatabaseManager is created
        self.logging_queue = LoggingQueue()
        self.progress_queue = ProgressQueue(config_manager)
        
        logger.info("QueueManager initialized with all queues")
    
    # ResultQueue methods
    async def put_result(self, result: MetadataResult) -> bool:
        """Put metadata result in ResultQueue"""
        return await self.result_queue.put_result(result)
    
    def get_result(self) -> Optional[MetadataResult]:
        """Get metadata result from ResultQueue"""
        return self.result_queue.get_result()
    
    def get_all_results(self) -> List[MetadataResult]:
        """Get all available results from ResultQueue"""
        return self.result_queue.get_all_results()
    
    # LoggingQueue methods
    async def put_log(self, level: LogLevel, message: str, source: str = "ProcessManager") -> bool:
        """Put log message in LoggingQueue"""
        return await self.logging_queue.put_log(level, message, source)
    
    def get_log(self) -> Optional[LogMessage]:
        """Get log message from LoggingQueue"""
        return self.logging_queue.get_log()
    
    def get_all_logs(self) -> List[LogMessage]:
        """Get all available logs from LoggingQueue"""
        return self.logging_queue.get_all_logs()
    
    # ProgressQueue methods
    async def put_progress(self, update: ProgressUpdate) -> bool:
        """Put progress update in ProgressQueue"""
        return await self.progress_queue.put_progress(update)
    
    def get_progress(self) -> Optional[ProgressUpdate]:
        """Get progress update from ProgressQueue"""
        return self.progress_queue.get_progress()
    
    def get_all_progress(self) -> List[ProgressUpdate]:
        """Get all available progress updates from ProgressQueue"""
        return self.progress_queue.get_all_progress()
    
    # Queue management methods
    def abort_all(self):
        """Abort all queues"""
        self.result_queue.abort()
        self.logging_queue.abort()
        self.progress_queue.abort()
        logger.info("All queues aborted")
    
    def reset_all(self):
        """Reset all queues"""
        self.result_queue.reset()
        self.logging_queue.reset()
        self.progress_queue.reset()
        logger.info("All queues reset")
    
    def clear_all(self):
        """Clear all queues"""
        self.result_queue.clear()
        self.logging_queue.clear()
        self.progress_queue.clear()
        logger.info("All queues cleared")
    
    def get_queue_stats(self) -> dict:
        """Get statistics for all queues"""
        return {
            'result_queue': {
                'size': self.result_queue.size(),
                'is_full': self.result_queue.is_full(),
                'is_empty': self.result_queue.is_empty(),
                'is_aborted': self.result_queue.is_aborted()
            },
            'logging_queue': {
                'size': self.logging_queue.size(),
                'is_full': self.logging_queue.is_full(),
                'is_empty': self.logging_queue.is_empty(),
                'is_aborted': self.logging_queue.is_aborted()
            },
            'progress_queue': {
                'size': self.progress_queue.size(),
                'is_full': self.progress_queue.is_full(),
                'is_empty': self.progress_queue.is_empty(),
                'is_aborted': self.progress_queue.is_aborted()
            }
        }
