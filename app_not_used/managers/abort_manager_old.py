"""Abort Manager voor YAPMO - Direct abort coordination."""

import asyncio
from typing import Optional

from queues.logging_queue import LoggingQueue, LogLevel
from queues.result_queue import ResultQueue
from managers.database_manager import DatabaseManager
from managers.logging_manager import LoggingManager


class AbortManager:
    """Abort manager voor YAPMO - Direct abort coordination zonder queue."""
    
    def __init__(self, result_queue: ResultQueue, logging_queue: LoggingQueue, 
                 database_manager: DatabaseManager, logging_manager: LoggingManager):
        """Initialize AbortManager met alle components."""
        self.result_queue = result_queue
        self.logging_queue = logging_queue
        self.database_manager = database_manager
        self.logging_manager = logging_manager
        
        # Abort state
        self.is_aborted = False
        self.abort_source = None
        self.abort_reason = None
        
        print("DEBUG: AbortManager initialized successfully")
    
    def abort(self, source: str, reason: str) -> None:
        """Direct abort - geen queue nodig.
        
        Args:
            source: Wie heeft abort gestart (UI, ERROR, etc.)
            reason: Reden voor abort
        """
        if self.is_aborted:
            print(f"WARNING: Abort already in progress, ignoring new abort from {source}")
            return
        
        print(f"DEBUG: Abort initiated by {source}: {reason}")
        
        # Set abort state
        self.is_aborted = True
        self.abort_source = source
        self.abort_reason = reason
        
        # 1. Log abort
        self.logging_queue.put_log(LogLevel.NOTICE, f"Abort initiated by {source}: {reason}")
        
        # 2. Stop alle queues (leegmaken)
        print("DEBUG: Stopping all queues...")
        self.result_queue.set_abort()
        self.logging_queue.set_abort()
        
        # 3. Stop alle managers
        print("DEBUG: Stopping all managers...")
        self._stop_managers()
        
        # 4. Cleanup resources
        print("DEBUG: Cleaning up resources...")
        self._cleanup_resources()
        
        print("DEBUG: Abort sequence completed")
    
    def _stop_managers(self) -> None:
        """Stop alle managers."""
        try:
            # Stop database manager
            if hasattr(self.database_manager, 'stop'):
                self.database_manager.stop()
            else:
                self.database_manager.close()
            
            # Stop logging manager
            if hasattr(self.logging_manager, 'stop'):
                self.logging_manager.stop()
            else:
                self.logging_manager.close()
                
        except Exception as e:
            print(f"ERROR: Error stopping managers: {e}")
    
    def _cleanup_resources(self) -> None:
        """Cleanup alle resources."""
        try:
            # Close database connections
            if hasattr(self.database_manager, 'close'):
                self.database_manager.close()
            
            # Close logging manager
            if hasattr(self.logging_manager, 'close'):
                self.logging_manager.close()
                
        except Exception as e:
            print(f"ERROR: Error during resource cleanup: {e}")
    
    def is_abort_active(self) -> bool:
        """Check if abort is active."""
        return self.is_aborted
    
    def get_abort_info(self) -> tuple[Optional[str], Optional[str]]:
        """Get abort information.
        
        Returns:
            Tuple of (source, reason) or (None, None) if no abort
        """
        if self.is_aborted:
            return self.abort_source, self.abort_reason
        return None, None
    
    def reset_abort(self) -> None:
        """Reset abort state (voor nieuwe sessie)."""
        if self.is_aborted:
            print(f"DEBUG: Resetting abort state (was: {self.abort_source})")
            self.is_aborted = False
            self.abort_source = None
            self.abort_reason = None
    
    async def abort_async(self, source: str, reason: str) -> None:
        """Async version van abort voor NiceGUI compatibility."""
        # Run abort in background thread
        await asyncio.get_event_loop().run_in_executor(None, self.abort, source, reason)
    
    def close(self) -> None:
        """Close abort manager."""
        print("DEBUG: AbortManager closed")
