"""Database manager v2 for file processing results."""

from typing import Dict, Any
from core.logging_service_v2 import logging_service


def db_dummy(result: Dict[str, Any]) -> None:
    """Dummy database manager - accepts result and does nothing.
    
    This function is designed to be easily extended for future database operations.
    Currently accepts the result dictionary from file processing and does nothing.
    
    Args:
        result: Dictionary containing file processing results with keys:
            - file_path: Original file path
            - file_name: Basename with extension
            - total_file_url: Absolute file path
            - os_disk_size: File size in bytes
            - media_type: "image" or "video"
            - sidecars: List of sidecar extensions
            - worker_id: Worker ID for debugging
            - success: Boolean success/failure
            - processing_time: Processing time in seconds
            - log_messages: List of log messages
    """
    # TODO: Implement actual database operations
    # For now, just accept the result and do nothing
    logging_service.log("DEBUG", f"db_dummy YESYES received result: {result}")#DEBUG_ON Log all received data for testing
    pass
