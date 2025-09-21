#YAPMO_V3.0
"""Progress Tracker - Tracks file processing progress for UI updates."""

import time
import threading
from typing import Dict, Any, Optional, Callable


class ProgressTracker:
    """Tracks file processing progress and provides data for UI updates."""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize the progress tracker.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback
        self.lock = threading.Lock()
        
        # Progress counters
        self.total_files = 0
        self.processed_files = 0
        self.successful_files = 0
        self.failed_files = 0
        self.total_directories = 0
        self.processed_directories = 0
        
        # Timing
        self.start_time = None
        self.last_update_time = None
        
        # Performance metrics
        self.files_per_second = 0.0
        self.directories_per_second = 0.0
        self.estimated_time_remaining = 0.0
        
    def start_processing(self, total_files: int, total_directories: int):
        """
        Start tracking processing progress.
        
        Args:
            total_files: Total number of files to process
            total_directories: Total number of directories to scan
        """
        with self.lock:
            self.total_files = total_files
            self.total_directories = total_directories
            self.processed_files = 0
            self.successful_files = 0
            self.failed_files = 0
            self.processed_directories = 0
            self.start_time = time.time()
            self.last_update_time = self.start_time
            
        self._notify_progress()
    
    def update_file_processed(self, success: bool = True):
        """
        Update when a file has been processed.
        
        Args:
            success: Whether the file was processed successfully
        """
        with self.lock:
            self.processed_files += 1
            if success:
                self.successful_files += 1
            else:
                self.failed_files += 1
                
        self._notify_progress()
    
    def update_directory_processed(self):
        """Update when a directory has been processed."""
        with self.lock:
            self.processed_directories += 1
            
        self._notify_progress()
    
    def _notify_progress(self):
        """Notify about progress update."""
        if self.progress_callback:
            progress_data = self.get_progress_data()
            self.progress_callback('processing_progress', progress_data)
    
    def get_progress_data(self) -> Dict[str, Any]:
        """
        Get current progress data for UI updates.
        
        Returns:
            Dictionary with progress information
        """
        with self.lock:
            current_time = time.time()
            
            # Calculate elapsed time
            elapsed_time = current_time - self.start_time if self.start_time else 0
            
            # Calculate performance metrics
            if elapsed_time > 0:
                self.files_per_second = self.processed_files / elapsed_time
                self.directories_per_second = self.processed_directories / elapsed_time
                
                # Calculate estimated time remaining
                if self.files_per_second > 0 and self.total_files > self.processed_files:
                    remaining_files = self.total_files - self.processed_files
                    self.estimated_time_remaining = remaining_files / self.files_per_second
                else:
                    self.estimated_time_remaining = 0.0
            else:
                self.files_per_second = 0.0
                self.directories_per_second = 0.0
                self.estimated_time_remaining = 0.0
            
            # Calculate progress percentages
            file_progress = (self.processed_files / self.total_files) if self.total_files > 0 else 0.0
            directory_progress = (self.processed_directories / self.total_directories) if self.total_directories > 0 else 0.0
            
            return {
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'successful_files': self.successful_files,
                'failed_files': self.failed_files,
                'total_directories': self.total_directories,
                'processed_directories': self.processed_directories,
                'file_progress': file_progress,
                'directory_progress': directory_progress,
                'files_per_second': self.files_per_second,
                'directories_per_second': self.directories_per_second,
                'estimated_time_remaining': self.estimated_time_remaining,
                'elapsed_time': elapsed_time
            }
    
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        with self.lock:
            return (self.processed_files >= self.total_files and 
                    self.processed_directories >= self.total_directories)
    
    def get_completion_percentage(self) -> float:
        """Get overall completion percentage."""
        with self.lock:
            if self.total_files == 0:
                return 0.0
            return (self.processed_files / self.total_files) * 100.0
    
    def reset(self):
        """Reset all progress counters."""
        with self.lock:
            self.total_files = 0
            self.processed_files = 0
            self.successful_files = 0
            self.failed_files = 0
            self.total_directories = 0
            self.processed_directories = 0
            self.start_time = None
            self.last_update_time = None
            self.files_per_second = 0.0
            self.directories_per_second = 0.0
            self.estimated_time_remaining = 0.0
