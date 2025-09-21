#YAPMO_V3.0
"""Process single media file worker."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


def process_single_file(file_path: str, image_extensions: list, video_extensions: list, worker_id: int = 0) -> Dict[str, Any]:
    """
    Process a single media file and return JSON data.
    
    Args:
        file_path: Full path to the media file
        image_extensions: List of image file extensions
        video_extensions: List of video file extensions
        worker_id: ID of the worker processing this file
    
    Returns:
        Dictionary with processing result, JSON data and log messages
    """
    log_messages = []  # Collect log messages to return to main process
    
    try:
        # Log start of processing
        # log_messages.append(f"DEBUG: Worker {worker_id}: Starting process_single_file for {file_path}")#DEBUG_OFF Worker logging
        
        # Get file extension
        file_ext = Path(file_path).suffix.lower()
        
        # Determine media type
        if file_ext in image_extensions:
            media_type = "image"
        elif file_ext in video_extensions:
            media_type = "video"
        else:
            log_messages.append(f"WARNING: Worker {worker_id}: Unsupported file type: {file_ext}")
            return {
                "success": False,
                "error": f"Unsupported file type: {file_ext}",
                "file_path": file_path,
                "log_messages": log_messages
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
        
        # Log processing success
        # log_messages.append(f"DEBUG: Worker {worker_id}: {timestamp} | {filename} | {file_path} | SUCCESS")#DEBUG_OFF Worker logging
        
        return {
            "success": True,
            "json_data": json_data,
            "file_path": file_path,
            "media_type": media_type,
            "log_messages": log_messages
        }
        
    except Exception as e:
        # Log processing failure
        timestamp = datetime.now(timezone.utc).isoformat()
        filename = Path(file_path).name if file_path else "unknown"
        log_messages.append(f"ERROR: Worker {worker_id}: {timestamp} | {filename} | {file_path} | FAILURE: {str(e)}")
        
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path,
            "log_messages": log_messages
        }
