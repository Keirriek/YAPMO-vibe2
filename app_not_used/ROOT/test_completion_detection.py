#YAPMO_V3.0
"""Test script for Completion Detection."""

import sys
import os
import tempfile
import time
import threading
sys.path.append('/workspaces/app')

from core.directory_processor import DirectoryProcessor

def create_large_test_directory():
    """Create a larger test directory to test completion detection."""
    test_dir = tempfile.mkdtemp(prefix="yapmo_completion_test_")
    
    # Create multiple subdirectories
    subdirs = [f"subdir_{i:03d}" for i in range(10)]
    for subdir in subdirs:
        os.makedirs(os.path.join(test_dir, subdir), exist_ok=True)
    
    # Create test files in each subdirectory
    test_files = []
    for i, subdir in enumerate(subdirs):
        for j in range(5):  # 5 files per subdirectory
            filename = f"file_{i:03d}_{j:03d}.jpg"
            file_path = os.path.join(test_dir, subdir, filename)
            with open(file_path, 'w') as f:
                f.write(f"Test content for {filename}")
            test_files.append(file_path)
    
    return test_dir, len(test_files)

def progress_callback(event_type: str, data):
    """Test progress callback with completion tracking."""
    if event_type == 'directory_processed':
        print(f"  - Directory processed: {os.path.basename(data)}")
    elif event_type == 'file_processed':
        stats = data
        print(f"  - Files processed: {stats['processed_files']}/{stats['processed_files'] + stats.get('pending_files', 0)}")
    elif event_type == 'processing_progress':
        stats = data
        print(f"  - Progress: {stats['processed_files']} processed, {stats.get('pending_files', 0)} pending")

def test_completion_detection():
    """Test completion detection with larger dataset."""
    
    print("Testing Completion Detection...")
    print("=" * 50)
    
    # Create larger test directory
    test_dir, expected_files = create_large_test_directory()
    print(f"Created test directory: {test_dir}")
    print(f"Expected files: {expected_files}")
    
    # Test data
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Create directory processor
    processor = DirectoryProcessor(max_workers=4, progress_callback=progress_callback)
    
    print("Created DirectoryProcessor with 4 workers")
    
    # Process directory
    print(f"\nProcessing directory: {test_dir}")
    start_time = time.time()
    
    result = processor.process_directory(test_dir, image_extensions, video_extensions)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Check result
    if result.get('success', False):
        print("✓ Directory processing completed successfully")
        stats = result.get('stats', {})
        print(f"Final statistics: {stats}")
        
        # Verify completion
        if stats.get('total_files') == expected_files:
            print(f"✓ Total files correct: {stats['total_files']}")
        else:
            print(f"✗ Total files incorrect: expected {expected_files}, got {stats.get('total_files')}")
        
        if stats.get('processed_files') == expected_files:
            print(f"✓ All files processed: {stats['processed_files']}")
        else:
            print(f"✗ Not all files processed: {stats.get('processed_files')}/{expected_files}")
        
        if stats.get('successful_files') == expected_files:
            print(f"✓ All files successful: {stats['successful_files']}")
        else:
            print(f"✗ Some files failed: {stats.get('successful_files')}/{expected_files}")
        
        if stats.get('directories_scanned') >= 10:
            print(f"✓ All directories scanned: {stats['directories_scanned']}")
        else:
            print(f"✗ Not all directories scanned: {stats.get('directories_scanned')}/10")
        
        # Performance metrics
        print(f"\nPerformance metrics:")
        print(f"  - Total time: {total_time:.2f} seconds")
        print(f"  - Files per second: {stats.get('files_per_second', 0):.2f}")
        print(f"  - Directories per second: {stats.get('directories_per_second', 0):.2f}")
        
        # Completion verification
        if stats.get('processed_files') == stats.get('total_files') == expected_files:
            print("✓ Completion detection: PERFECT")
        else:
            print("✗ Completion detection: ISSUES DETECTED")
        
    else:
        print(f"✗ Directory processing failed: {result.get('error', 'Unknown error')}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    print(f"\nCleaned up test directory: {test_dir}")
    
    print("\n" + "=" * 50)
    print("Completion detection test completed!")

if __name__ == "__main__":
    test_completion_detection()
