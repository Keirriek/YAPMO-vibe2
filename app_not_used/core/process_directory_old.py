"""Process directory with media files."""

import os
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .process_single_file import process_single_file
import yapmo_globals as global_vars


def process_directory(
    directory_path: str,
    image_extensions: List[str],
    video_extensions: List[str],
    max_workers: int,
    worker_timeout: int
) -> Dict[str, Any]:
    """
    Process all media files in a directory using parallel workers.
    
    Args:
        directory_path: Path to the directory to process
        image_extensions: List of image file extensions
        video_extensions: List of video file extensions
        max_workers: Maximum number of parallel workers
        worker_timeout: Timeout for individual workers in seconds
    
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    processed_files = 0
    successful_files = 0
    failed_files = 0
    errors = []
    
    # Get all media files in directory
    media_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = Path(file).suffix.lower()
            
            # Check if it's a media file
            if file_ext in image_extensions or file_ext in video_extensions:
                media_files.append(file_path)
    
    #DEBUG_OFF
    # from core.logging_service import logging_service
    # logging_service.log("DEBUG", f"process_directory called with directory_path: {directory_path}")
    
    if not media_files:
        return {
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "average_time_per_file": 0.0,
            "total_processing_time": 0.0,
            "errors": []
        }
    
    # Process files with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks with worker IDs
        future_to_file = {}
        for i, file_path in enumerate(media_files):
            worker_id = i % max_workers  # Distribute files across workers
            future = executor.submit(process_single_file, file_path, image_extensions, video_extensions, worker_id)
            future_to_file[future] = file_path
        
        # Process completed tasks
        for future in as_completed(future_to_file, timeout=worker_timeout):
            file_path = future_to_file[future]
            processed_files += 1
            global_vars.progress_current += 1
            
            try:
                result = future.result(timeout=worker_timeout)
                
                if result["success"]:
                    successful_files += 1
                else:
                    failed_files += 1
                    errors.append({
                        "file_path": file_path,
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                failed_files += 1
                errors.append({
                    "file_path": file_path,
                    "error": str(e)
                })
    
    end_time = time.time()
    total_processing_time = end_time - start_time
    average_time_per_file = total_processing_time / processed_files if processed_files > 0 else 0.0
    
    return {
        "processed_files": processed_files,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "average_time_per_file": average_time_per_file,
        "total_processing_time": total_processing_time,
        "errors": errors
    }
