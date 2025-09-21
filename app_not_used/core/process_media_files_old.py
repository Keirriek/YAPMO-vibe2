"""Main controller for processing media files."""

import os
from pathlib import Path
from typing import Dict, Any, List
import time

from .process_directory import process_directory
from config import get_param
from core.logging_service import logging_service


def process_media_files(search_directory: str) -> Dict[str, Any]:
    """
    Process all media files in search directory and subdirectories.
    
    Args:
        search_directory: Root directory to search for media files
    
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    
    # Get configuration parameters
    max_workers = get_param("processing", "max_workers")
    worker_timeout = get_param("processing", "worker_timeout")
    image_extensions = get_param("extensions", "image_extensions")
    video_extensions = get_param("extensions", "video_extensions")
    
    # Validate directory
    if not os.path.exists(search_directory):
        return {
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "average_time_per_file": 0.0,
            "total_processing_time": 0.0,
            "errors": [{"error": f"Directory does not exist: {search_directory}"}]
        }
    
    if not os.access(search_directory, os.R_OK):
        return {
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "average_time_per_file": 0.0,
            "total_processing_time": 0.0,
            "errors": [{"error": f"Directory is not readable: {search_directory}"}]
        }
    
    # Process the directory
    result = process_directory(
        search_directory,
        image_extensions,
        video_extensions,
        max_workers,
        worker_timeout
    )
    
    # #DEBUG_OFF
    # logging_service.log("DEBUG", f"process_media_files called with search_directory: {search_directory}")
    
    # Add total processing time
    end_time = time.time()
    result["total_processing_time"] = end_time - start_time
    
    return result
