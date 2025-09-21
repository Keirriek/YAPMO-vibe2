#YAPMO_V3.0
"""Directory Processor - Processes directories and submits files to parallel workers."""

import os
import time
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from core.logging_service import logging_service
from core.parallel_worker_manager import ParallelWorkerManager
from core.result_processor import ResultProcessor
from core.logging_integration import LoggingIntegration


class DirectoryProcessor:
    """Processes directories and coordinates file processing with parallel workers."""
    
    def __init__(self, max_workers: int, progress_callback: Optional[Callable] = None):
        """
        Initialize the directory processor.
        
        Args:
            max_workers: Maximum number of parallel workers
            progress_callback: Optional callback for progress updates
        """
        self.max_workers = max_workers
        self.progress_callback = progress_callback
        
        # Initialize components
        self.worker_manager = ParallelWorkerManager(max_workers, progress_callback)
        self.result_processor = None
        self.logging_integration = None
        
        # Processing statistics
        self.total_files = 0
        self.processed_files = 0
        self.directories_scanned = 0
        self.start_time = None
        
        logging_service.log("DEBUG", f"DirectoryProcessor initialized with {max_workers} workers")#DEBUG_ON DirectoryProcessor initialized with {max_workers} workers
    
    def process_directory(self, directory_path: str, image_extensions: List[str], video_extensions: List[str]) -> Dict[str, Any]:
        """
        Process all media files in a directory.
        
        Args:
            directory_path: Path to the directory to process
            image_extensions: List of image file extensions
            video_extensions: List of video file extensions
            
        Returns:
            Dictionary with processing results
        """
        self.start_time = time.time()
        
        # Validate directory
        if not os.path.exists(directory_path):
            error_msg = f"Directory does not exist: {directory_path}"
            logging_service.log("ERROR", error_msg)
            return {"success": False, "error": error_msg}
        
        if not os.path.isdir(directory_path):
            error_msg = f"Path is not a directory: {directory_path}"
            logging_service.log("ERROR", error_msg)
            return {"success": False, "error": error_msg}
        
        logging_service.log("DEBUG", f"Starting directory processing: {directory_path}")#DEBUG_ON Starting directory processing: {directory_path}
        
        # Initialize result processor and logging integration
        self.result_processor = ResultProcessor(
            self.worker_manager.get_result_queue(),
            self.worker_manager.get_logging_queue()
        )
        self.logging_integration = LoggingIntegration(
            self.worker_manager.get_logging_queue()
        )
        
        # Start background processors
        self.result_processor.start()
        self.logging_integration.start()
        
        try:
            # Scan directory and submit files
            self._scan_and_submit_files(directory_path, image_extensions, video_extensions)
            
            # Wait for all processing to complete
            self._wait_for_completion()
            
            # Get final statistics
            stats = self._get_final_statistics()
            
            logging_service.log("DEBUG", f"Directory processing completed: {stats}")#DEBUG_ON Directory processing completed: {stats}
            return {"success": True, "stats": stats}
            
        except Exception as e:
            error_msg = f"Error during directory processing: {e}"
            logging_service.log("ERROR", error_msg)
            return {"success": False, "error": error_msg}
            
        finally:
            # Cleanup
            self._cleanup()
    
    def _scan_and_submit_files(self, directory_path: str, image_extensions: List[str], video_extensions: List[str]):
        """Scan directory and submit files to worker manager."""
        media_extensions = set(image_extensions + video_extensions)
        
        logging_service.log("DEBUG", f"Scanning directory: {directory_path}")#DEBUG_ON Scanning directory: {directory_path}
        
        # Walk through directory
        log_files_count_update = get_param("logging", "log_files_count_update")
        for root, dirs, files in os.walk(directory_path):
            self.directories_scanned += 1
            
            # Track directory progress
            if self.progress_callback:
                self.progress_callback('directory_processed', root)
            
            # Process files in current directory
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                # Check if it's a media file
                if file_ext in media_extensions:
                    self.total_files += 1
                    self.worker_manager.submit_file(file_path, image_extensions, video_extensions)
                    
                    # Log progress every log_files_count_update files
                    if self.total_files % log_files_count_update == 0:
                        logging_service.log("INFO", f"Update: Submitted {self.total_files} files for processing")
        
        logging_service.log("INFO", f"Directory scan completed: {self.total_files} media files found in {self.directories_scanned} directories")
    
    def _wait_for_completion(self):
        """Wait for all processing to complete."""
        logging_service.log("INFO_EXTRA", "Waiting for all processing to complete...")
        
        max_wait_time = 300  # 5 minutes max
        start_wait = time.time()
        
        while (time.time() - start_wait) < max_wait_time:
            # Process completed workers
            completed = self.worker_manager.process_completed_workers()
            
            # Check if all work is complete
            if self.worker_manager.is_complete():
                break
            
            # Update progress
            if self.progress_callback:
                stats = self.worker_manager.get_stats()
                self.progress_callback('processing_progress', stats)
            
            time.sleep(0.1)  # Small delay
        
        # Final check
        if not self.worker_manager.is_complete():
            logging_service.log("WARNING", "Processing did not complete within timeout period")
    
    def _get_final_statistics(self) -> Dict[str, Any]:
        """Get final processing statistics."""
        worker_stats = self.worker_manager.get_stats()
        result_stats = self.result_processor.get_stats() if self.result_processor else {}
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            "total_files": self.total_files,
            "processed_files": worker_stats.get('processed_files', 0),
            "successful_files": worker_stats.get('successful_files', 0),
            "failed_files": worker_stats.get('failed_files', 0),
            "directories_scanned": self.directories_scanned,
            "elapsed_time": elapsed_time,
            "files_per_second": self.total_files / elapsed_time if elapsed_time > 0 else 0,
            "directories_per_second": self.directories_scanned / elapsed_time if elapsed_time > 0 else 0
        }
    
    def _cleanup(self):
        """Cleanup resources."""
        if self.result_processor:
            self.result_processor.stop()
        if self.logging_integration:
            self.logging_integration.stop()
        if self.worker_manager:
            self.worker_manager.shutdown()
        
        logging_service.log("INFO_EXTRA", "DirectoryProcessor cleanup completed")
