"""Worker functions for parallel processing."""

import os
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import get_param


def check_exiftool_availability() -> bool:
    """Check if ExifTool is available and configured."""
    try:
        result = subprocess.run(
            ["exiftool", "-ver"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            check=False
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def validate_exiftool_config() -> Tuple[bool, str]:
    """Validate ExifTool configuration and availability."""
    use_exiftool = get_param("processing", "use_exiftool", False)
    
    if not use_exiftool:
        return True, "ExifTool disabled in config"
    
    if not check_exiftool_availability():
        return False, "ExifTool enabled in config but not available. Please install ExifTool or disable use_exiftool in config.json"
    
    return True, "ExifTool available and configured"


def extract_exiftool_metadata_tsv(file_path: str) -> Dict[str, str]:
    """Extract metadata using ExifTool TSV format (fastest)."""
    try:
        # Use charset=utf8 for proper handling of spaces and non-ASCII characters
        cmd = ["exiftool", "-charset", "filename=utf8", "-T", "-G", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=get_param("processing", "exiftool_timeout") / 1000.0)
        
        if result.returncode == 0:
            return parse_exiftool_tsv(result.stdout)
        else:
            return {"exiftool_error": result.stderr}
    except Exception as e:
        return {"exiftool_error": str(e)}


def parse_exiftool_tsv(tsv_output: str) -> Dict[str, str]:
    """Parse ExifTool TSV output (fast)."""
    metadata = {}
    for line in tsv_output.strip().split('\n'):
        if '\t' in line:
            field, value = line.split('\t', 1)
            metadata[field] = value
    return metadata


def map_metadata_fields(exiftool_metadata: Dict[str, str], media_type: str, config: Dict[str, Any]) -> Dict[str, str]:
    """Map ExifTool fields to database column names based on config."""
    mapped_metadata = {}
    
    # Get field mappings from config
    file_fields = config.get('metadata_fields_file', {})
    image_fields = config.get('metadata_fields_image', {})
    video_fields = config.get('metadata_fields_video', {})
    
    # Combine all field mappings
    all_field_mappings = {**file_fields, **image_fields, **video_fields}
    
    # Map ExifTool fields to database column names
    for exif_field, db_field in all_field_mappings.items():
        if exif_field in exiftool_metadata:
            mapped_metadata[db_field] = exiftool_metadata[exif_field]
        else:
            # Set to None for missing fields
            mapped_metadata[db_field] = None
    
    return mapped_metadata


def process_media_file(file_path: str, worker_id: int) -> Dict[str, Any]:
    """Process a single media file and extract metadata."""
    
    start_time = time.time()
    log_messages = []
    
    try:
        # Load config for extensions
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Extract file metadata
        file_name = os.path.basename(file_path)  # basename with extension, non-ASCII safe
        total_file_url = os.path.abspath(file_path)  # absolute path, UNIX style
        
        # Get file size
        try:
            os_disk_size = os.path.getsize(file_path)
        except OSError as e:
            log_messages.append({
                'level': 'WARNING',
                'message': f'File access error for {file_path}: {str(e)}'
            })
            os_disk_size = 0
        
        # Determine media type (case-insensitive)
        file_ext = os.path.splitext(file_path)[1].lower()
        image_extensions = [ext.lower() for ext in config['extensions']['image_extensions']]
        video_extensions = [ext.lower() for ext in config['extensions']['video_extensions']]
        
        if file_ext in image_extensions:
            media_type = "image"
        elif file_ext in video_extensions:
            media_type = "video"
        else:
            media_type = "unknown"
        
        # Find sidecar files (same directory, one per extension)
        sidecar_extensions = config['extensions']['sidecar_extensions']
        sidecars = []
        file_dir = os.path.dirname(file_path)
        file_base = os.path.splitext(os.path.basename(file_path))[0]
        
        for sidecar_ext in sidecar_extensions:
            sidecar_path = os.path.join(file_dir, file_base + sidecar_ext)
            if os.path.exists(sidecar_path):
                sidecars.append(sidecar_ext)
        
        # Extract ExifTool metadata
        exiftool_metadata = extract_exiftool_metadata_tsv(file_path)
        
        # Map metadata fields to database column names
        mapped_metadata = map_metadata_fields(exiftool_metadata, media_type, config)
        
        processing_time = time.time() - start_time
        
        # Success log messages
        log_messages = [
            #DEBUG_OFF Block Start - Worker logging ID, file name and processing time
            #{
            #    'level': 'DEBUG',
            #    'message': f'Worker {worker_id} processed {file_name} in {processing_time:.3f}s'
            #},#DEBUG_OFF Block End - Worker logging ID, file name and processing time
            #DEBUG_OFF Block Start - Worker logging Results: name={file_name}, size={os_disk_size}, type={media_type}, sidecars={sidecars}
            # {
            #     'level': 'DEBUG',
            #     'message': f'Results: name={file_name}, size={os_disk_size}, type={media_type}, sidecars={sidecars}'
            # },#DEBUG_OFF Block End - Worker logging Results: name={file_name}, size={os_disk_size}, type={media_type}, sidecars={sidecars}
            #DEBUG_OFF Block Start - Worker logging Metadata: {len(mapped_metadata)} fields extracted, exiftool_exit_code={exiftool_metadata.get("exiftool_error", 0)}
            #{
            #    'level': 'DEBUG',
            #    'message': f'Metadata: {len(mapped_metadata)} fields extracted, exiftool_exit_code={exiftool_metadata.get("exiftool_error", 0)}'
            #},#DEBUG_OFF Block End - Worker logging Metadata: {len(mapped_metadata)} fields extracted, exiftool_exit_code={exiftool_metadata.get("exiftool_error", 0)}
        ]
        
        result = {
            'file_path': file_path,
            'worker_id': worker_id,
            'success': True,
            'processing_time': processing_time,
            'file_name': file_name,
            'total_file_url': total_file_url,
            'os_disk_size': os_disk_size,
            'media_type': media_type,
            'sidecars': sidecars,
            'metadata': mapped_metadata,
            'exiftool_exit_code': exiftool_metadata.get('exiftool_error', 0),
            'log_messages': log_messages
        }
        
    except UnicodeDecodeError as e:
        processing_time = time.time() - start_time
        log_messages.append({
            'level': 'ERROR',
            'message': f'Unicode error processing {file_path}: {str(e)}'
        })
        
        result = {
            'file_path': file_path,
            'worker_id': worker_id,
            'success': False,
            'processing_time': processing_time,
            'log_message': f'Unicode error: {str(e)}',
            'log_messages': log_messages
        }
        
    except OSError as e:
        processing_time = time.time() - start_time
        log_messages.append({
            'level': 'ERROR',
            'message': f'OS error processing {file_path}: {str(e)}'
        })
        
        result = {
            'file_path': file_path,
            'worker_id': worker_id,
            'success': False,
            'processing_time': processing_time,
            'log_message': f'OS error: {str(e)}',
            'log_messages': log_messages
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_messages.append({
            'level': 'ERROR',
            'message': f'Unexpected error processing {file_path}: {str(e)}'
        })
        
        result = {
            'file_path': file_path,
            'worker_id': worker_id,
            'success': False,
            'processing_time': processing_time,
            'log_message': f'Unexpected error: {str(e)}',
            'log_messages': log_messages
        }
    
    return result
