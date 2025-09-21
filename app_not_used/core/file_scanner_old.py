"""
File Scanner voor YAPMO applicatie.

Deze module implementeert directory traversal en file discovery met UI feedback.
Het is geoptimaliseerd voor grote directory structuren en integreert met alle managers.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

# Import managers
from managers.abort_manager import AbortManager
from managers.queue_manager import QueueManager
from config import ConfigManager

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    """Result of directory scanning"""
    total_files: int
    media_files: int
    sidecars: int
    directories: int
    by_extension: Dict[str, int]
    file_list: List[str]
    scan_duration: float
    scan_path: str

@dataclass
class ScanProgress:
    """Progress update during scanning"""
    current_directory: str
    files_found: int
    directories_scanned: int
    progress_percentage: float
    eta: str

class FileScanner:
    """
    File Scanner - Directory traversal en file discovery
    
    Features:
    - Recursive directory scanning
    - File filtering op basis van config extensies
    - Progress tracking per directory
    - Memory efficient scanning
    - Abort functionality
    - Queue integration voor UI updates
    """
    
    def __init__(self, config_manager: ConfigManager, queue_manager: QueueManager, abort_manager: AbortManager):
        self.config_manager = config_manager
        self.queue_manager = queue_manager
        self.abort_manager = abort_manager
        
        # Scan state
        self.scanning = False
        self.scan_start_time: Optional[float] = None
        self.scan_path: Optional[str] = None
        
        # Progress tracking
        self.files_found = 0
        self.directories_scanned = 0
        self.last_progress_update = 0.0
        self.progress_update_interval = 1.0  # Update every second
        
        logger.info("FileScanner initialized")
    
    async def scan_directory(self, directory: str, progress_callback: Optional[Callable] = None) -> ScanResult:
        """
        Scan directory recursively voor media files
        
        Args:
            directory: Directory path to scan
            progress_callback: Optional callback for progress updates
            
        Returns:
            ScanResult with scan statistics and file list
        """
        if self.scanning:
            raise RuntimeError("Scanner already running")
        
        # Validate directory
        if not Path(directory).exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        if not Path(directory).is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        # Initialize scan state
        self.scanning = True
        self.scan_start_time = time.time()
        self.scan_path = directory
        self.files_found = 0
        self.directories_scanned = 0
        self.last_progress_update = 0.0
        
        logger.info(f"Starting directory scan: {directory}")
        
        try:
            # Perform the scan
            result = await self._perform_scan(directory, progress_callback)
            
            # Calculate scan duration
            scan_duration = time.time() - self.scan_start_time
            result.scan_duration = scan_duration
            result.scan_path = directory
            
            logger.info(f"Scan completed: {result.media_files} media files found in {scan_duration:.2f}s")
            return result
            
        finally:
            self.scanning = False
    
    async def _perform_scan(self, directory: str, progress_callback: Optional[Callable] = None) -> ScanResult:
        """Perform the actual directory scanning"""
        # Get config parameters
        config = self._get_scan_config()
        
        # Initialize counters
        total_files = 0
        media_files = 0
        sidecars = 0
        directories = 0
        by_extension: Dict[str, int] = {}
        file_list: List[str] = []
        
        # Get supported extensions
        image_exts = config["image_extensions"]
        video_exts = config["video_extensions"]
        supported_extensions = image_exts + video_exts
        sidecar_extensions = config["sidecar_extensions"]
        
        # Scan directory recursively
        for root, dirs, files in os.walk(directory):
            # Check for abort
            if self.abort_manager.is_abort_active():
                logger.info("Scan aborted by user")
                break
            
            # Count directories
            directories += len(dirs)
            self.directories_scanned += 1
            
            # Process files in this directory
            for file in files:
                # Check for abort
                if self.abort_manager.is_abort_active():
                    break
                
                file_ext = Path(file).suffix.lower()
                total_files += 1
                self.files_found += 1
                
                # Count by extension
                if file_ext in by_extension:
                    by_extension[file_ext] += 1
                else:
                    by_extension[file_ext] = 1
                
                # Count media files
                if file_ext in supported_extensions:
                    media_files += 1
                    # Add to file list for processing phase
                    file_list.append(str(Path(root) / file))
                
                # Count sidecars
                if file_ext in sidecar_extensions:
                    sidecars += 1
            
            # Send progress update if needed
            await self._send_progress_update_if_needed(root, progress_callback)
            
            # Extensive logging if enabled
            if config.get("log_extended", False) and files:
                await self._log_directory_summary(root, files, supported_extensions, sidecar_extensions)
        
        # Create result
        result = ScanResult(
            total_files=total_files,
            media_files=media_files,
            sidecars=sidecars,
            directories=directories,
            by_extension=by_extension,
            file_list=file_list,
            scan_duration=0.0,  # Will be set by caller
            scan_path=directory
        )
        
        return result
    
    async def _send_progress_update_if_needed(self, current_directory: str, progress_callback: Optional[Callable] = None):
        """Send progress update if enough time has passed"""
        current_time = time.time()
        if current_time - self.last_progress_update >= self.progress_update_interval:
            await self._send_progress_update(current_directory, progress_callback)
            self.last_progress_update = current_time
    
    async def _send_progress_update(self, current_directory: str, progress_callback: Optional[Callable] = None):
        """Send progress update to UI via queue"""
        # Calculate progress percentage (rough estimate)
        progress_percentage = min(100.0, (self.directories_scanned / 100.0) * 100.0)  # Rough estimate
        
        # Calculate ETA
        eta = self._calculate_eta()
        
        # Create progress update
        progress = ScanProgress(
            current_directory=current_directory,
            files_found=self.files_found,
            directories_scanned=self.directories_scanned,
            progress_percentage=progress_percentage,
            eta=eta
        )
        
        # Send to queue
        await self.queue_manager.put_log("INFO", f"Scanning: {current_directory} - {self.files_found} files found")
        
        # Call progress callback if provided
        if progress_callback:
            progress_callback(progress)
    
    def _calculate_eta(self) -> str:
        """Calculate ETA based on current progress and speed"""
        if self.files_found <= 0 or self.scan_start_time is None:
            return "Unknown"
        
        elapsed_time = time.time() - self.scan_start_time
        files_per_second = self.files_found / elapsed_time if elapsed_time > 0 else 0
        
        if files_per_second <= 0:
            return "Unknown"
        
        # Rough estimate: assume we'll find 10x more files
        estimated_total = self.files_found * 10
        remaining_files = estimated_total - self.files_found
        eta_seconds = remaining_files / files_per_second
        
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
    
    async def _log_directory_summary(self, root: str, files: List[str], 
                                   supported_extensions: List[str], 
                                   sidecar_extensions: List[str]) -> None:
        """Log summary for a directory"""
        media_count = len([f for f in files if Path(f).suffix.lower() in supported_extensions])
        sidecar_count = len([f for f in files if Path(f).suffix.lower() in sidecar_extensions])
        
        if media_count > 0 or sidecar_count > 0:
            await self.queue_manager.put_log("DEBUG", 
                f"Directory {root}: {media_count} media, {sidecar_count} sidecars, {len(files)} total")
    
    def _get_scan_config(self) -> Dict[str, Any]:
        """Get scan configuration from config manager"""
        return {
            "image_extensions": self.config_manager.get_param("extensions", "image_extensions", []),
            "video_extensions": self.config_manager.get_param("extensions", "video_extensions", []),
            "sidecar_extensions": self.config_manager.get_param("extensions", "sidecar_extensions", []),
            "log_extended": self.config_manager.get_param("logging", "log_extended", False)
        }
    
    def is_scanning(self) -> bool:
        """Check if scanner is currently scanning"""
        return self.scanning
    
    def get_scan_stats(self) -> Dict[str, Any]:
        """Get current scan statistics"""
        return {
            "scanning": self.scanning,
            "scan_path": self.scan_path,
            "files_found": self.files_found,
            "directories_scanned": self.directories_scanned,
            "scan_duration": time.time() - self.scan_start_time if self.scan_start_time else 0.0
        }
    
    def abort_scan(self):
        """Abort current scan"""
        if self.scanning:
            logger.info("Aborting scan")
            # The actual abort is handled by AbortManager in the scan loop
