"""
Process Manager - Coordination van parallelle processen
Stage 1.3: Process Manager Implementation
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging

# Import from managers directory
from .abort_manager import AbortManager

# Import real ConfigManager
from config import ConfigManager

# Import real QueueManager
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

# TaskStatus enum removed - using file-based processing instead

# Task class removed - using file-based processing instead

@dataclass
class ProgressUpdate:
    """Progress update for UI"""
    task_id: str
    progress: float
    status: str
    eta: str
    message: str = ""
    timestamp: float = 0.0  # Timestamp when update was created

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

@dataclass
class TaskInfo:
    """Information about an active task"""
    task_id: str
    worker_id: str
    file_path: str
    start_time: float
    timeout: int = 30  # seconds

# ProgressTracker class removed - using file-based progress tracking instead

class ProcessManager:
    """
    Process Manager - Coordination van parallelle processen
    - File-based processing voor 200k+ files performance
    - Worker pool coordination (max 32 workers)
    - Progress tracking met real-time updates
    - Abort integration met AbortManager
    """
    
    def __init__(self, config_manager: ConfigManager, queue_manager: QueueManager, abort_manager: AbortManager):
        self.config_manager = config_manager
        self.queue_manager = queue_manager
        self.abort_manager = abort_manager
        
        # Worker pool settings
        self.max_workers = config_manager.get_param('processing', 'max_workers')
        self.worker_semaphore = asyncio.Semaphore(self.max_workers)
        
        # File-based processing counters
        self.total_files = 0
        self.finished_files = 0
        self.error_files = 0
        self.current_workers = 0
        
        # Progress tracking
        self.start_time: Optional[float] = None
        self.last_progress_update = 0.0
        self.progress_update_interval = 1.0  # Update every second
        
        # Threading
        self.lock = threading.Lock()
        self.running = False
        
        # Task tracking for timeout monitoring
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.task_counter = 0
        self.worker_timeout = config_manager.get_param('processing', 'worker_timeout') / 1000.0  # Convert ms to seconds
        
        logger.info(f"ProcessManager initialized with max_workers={self.max_workers}")
    
    async def _monitor_timeouts(self):
        """Monitor active tasks for timeouts and handle crashed workers"""
        while self.running:
            try:
                current_time = time.time()
                timed_out_tasks = []
                
                # Check for timed out tasks
                with self.lock:
                    for task_id, task_info in self.active_tasks.items():
                        if current_time - task_info.start_time > task_info.timeout:
                            timed_out_tasks.append(task_info)
                
                # Handle timed out tasks
                for task_info in timed_out_tasks:
                    logger.warning(
                        f"Worker {task_info.worker_id} timeout on file: {task_info.file_path} "
                        f"(running for {current_time - task_info.start_time:.1f}s)"
                    )
                    
                    # Remove from active tasks
                    with self.lock:
                        if task_info.task_id in self.active_tasks:
                            del self.active_tasks[task_info.task_id]
                    
                    # Increment error counter
                    with self.lock:
                        self.error_files += 1
                    
                    # Send progress update
                    await self._send_progress_update()
                
                # Sleep for 10 seconds before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in timeout monitoring: {e}")
                await asyncio.sleep(10)
    
    async def start(self):
        """Start the process manager"""
        with self.lock:
            if self.running:
                logger.warning("ProcessManager already running")
                return
            
            self.running = True
            self.start_time = time.time()
            
            # Start timeout monitoring task
            self.timeout_monitor_task = asyncio.create_task(self._monitor_timeouts())
            
            logger.info("ProcessManager started")
    
    async def stop(self):
        """Stop the process manager"""
        with self.lock:
            if not self.running:
                return
            
            self.running = False
            
            # Stop timeout monitoring task
            if hasattr(self, 'timeout_monitor_task'):
                self.timeout_monitor_task.cancel()
                try:
                    await self.timeout_monitor_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("ProcessManager stopped")
    
    async def process_files(self, file_list: List[str], process_func: Callable) -> None:
        """Process a list of files using worker pool"""
        if not self.running:
            raise RuntimeError("ProcessManager not running")
        
        with self.lock:
            self.total_files = len(file_list)
            self.finished_files = 0
            self.error_files = 0
            self.start_time = time.time()
        
        logger.info(f"Starting to process {self.total_files} files")
        
        # Send initial progress update
        await self._send_progress_update("Starting file processing")
        
        # Process files in parallel using worker pool
        tasks = []
        for file_path in file_list:
            task = asyncio.create_task(self._process_single_file(file_path, process_func))
            tasks.append(task)
        
        # Wait for all files to be processed
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Send final progress update
        await self._send_progress_update("File processing completed")
        
        logger.info(f"Completed processing {self.finished_files} files, {self.error_files} errors")
    
    async def _process_single_file(self, file_path: str, process_func: Callable):
        """Process a single file in the worker pool"""
        async with self.worker_semaphore:
            # Generate unique task ID and worker ID
            with self.lock:
                self.task_counter += 1
                task_id = f"task_{self.task_counter}"
                worker_id = f"worker_{self.task_counter}"
            
            # Create task info for timeout monitoring
            task_info = TaskInfo(
                task_id=task_id,
                worker_id=worker_id,
                file_path=file_path,
                start_time=time.time(),
                timeout=self.worker_timeout  # Already converted to seconds
            )
            
            # Add to active tasks
            with self.lock:
                self.active_tasks[task_id] = task_info
            
            try:
                # Check if aborted before starting
                if self.abort_manager.is_abort_active():
                    return
                
                # Execute file processing
                if asyncio.iscoroutinefunction(process_func):
                    result = await process_func(file_path)
                else:
                    # Run CPU-bound tasks in thread pool
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, process_func, file_path
                    )
                
                # Check if aborted during execution
                if self.abort_manager.is_abort_active():
                    return
                
                # Update counters
                with self.lock:
                    self.finished_files += 1
                
                # Send progress update if needed
                await self._send_progress_update_if_needed()
                
                logger.debug(f"File processed successfully: {file_path}")
                
            except Exception as e:
                # Update error counter
                with self.lock:
                    self.error_files += 1
                
                # Send progress update if needed
                await self._send_progress_update_if_needed()
                
                logger.error(f"File processing failed: {file_path} - {e}")
            
            finally:
                # Remove task from active tasks (success or failure)
                with self.lock:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
    
    async def abort_processing(self):
        """Abort file processing"""
        logger.info("Aborting file processing")
        await self._send_progress_update("Processing aborted")
    
    async def _send_progress_update_if_needed(self):
        """Send progress update if enough time has passed"""
        current_time = time.time()
        if current_time - self.last_progress_update >= self.progress_update_interval:
            await self._send_progress_update("Processing files")
            self.last_progress_update = current_time
    
    async def _send_progress_update(self, message: str = ""):
        """Send progress update to UI via queue"""
        with self.lock:
            processed_files = self.finished_files + self.error_files
            progress = (processed_files / self.total_files * 100) if self.total_files > 0 else 0
            eta = self._calculate_eta()
        
        update = ProgressUpdate(
            task_id="main_process",
            progress=progress,
            status="running" if processed_files < self.total_files else "completed",
            eta=eta,
            message=f"{message}: {self.finished_files} completed, {self.error_files} errors, {self.total_files - processed_files} remaining"
        )
        
        # Send to progress queue for UI updates
        await self.queue_manager.put_progress(update)
    
    def _calculate_eta(self) -> str:
        """Calculate ETA based on current progress and speed"""
        if self.finished_files + self.error_files <= 0 or self.start_time is None:
            return "Unknown"
        
        elapsed_time = time.time() - self.start_time
        processed_files = self.finished_files + self.error_files
        progress = processed_files / self.total_files if self.total_files > 0 else 0
        
        if progress <= 0:
            return "Unknown"
        
        # Calculate ETA: (100 - progress) / progress * elapsed_time
        remaining_progress = 1 - progress
        eta_seconds = (remaining_progress / progress) * elapsed_time
        
        return self._format_time(eta_seconds)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to readable time string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get file processing statistics"""
        with self.lock:
            return {
                'max_workers': self.max_workers,
                'current_workers': self.current_workers,
                'available_workers': self.max_workers - self.current_workers,
                'total_files': self.total_files,
                'finished_files': self.finished_files,
                'error_files': self.error_files,
                'remaining_files': self.total_files - self.finished_files - self.error_files
            }
    
    def is_running(self) -> bool:
        """Check if process manager is running"""
        with self.lock:
            return self.running
