"""Process single media file worker."""

import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from core.logging_service import logging_service


def process_single_file(file_path: str, image_extensions: list, video_extensions: list, worker_id: int = 0) -> Dict[str, Any]:
    """
    Process a single media file and return JSON data.
    
    Args:
        file_path: Full path to the media file
        image_extensions: List of image file extensions
        video_extensions: List of video file extensions
        worker_id: ID of the worker processing this file
    
    Returns:
        Dictionary with processing result and JSON data
    """
    # #DEBUG_OFF
    # logging_service.log("DEBUG", f"Worker {worker_id}: Starting process_single_file for {file_path}", worker_id)
    
    try:
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        
        # Determine media type
        if file_ext in image_extensions:
            media_type = "image"
        elif file_ext in video_extensions:
            media_type = "video"
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_ext}",
                "file_path": file_path
            }
        
        # Get current timestamp in ISO format
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Get filename from path
        filename = Path(file_path).name
        
        # Create JSON data
        json_data = {
            "timestamp": timestamp,
            "filename": filename,
            "url": file_path,  # Full path including filename
            "mediatype": media_type
        }
        
        # #DEBUG_OFF  Log processing success
        # logging_service.log("DEBUG", f"Worker {worker_id}: {timestamp} | {filename} | {file_path} | SUCCESS", worker_id)
        
        return {
            "success": True,
            "json_data": json_data,
            "file_path": file_path,
            "media_type": media_type
        }
        
    except Exception as e:
        # Log processing failure
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = Path(file_path).name if file_path else "unknown"
        # #DEBUG_OFF
        # logging_service.log("DEBUG", f"Worker {worker_id}: {timestamp} | {filename} | {file_path} | FAILURE: {str(e)}", worker_id)
        
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }
