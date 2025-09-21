#YAPMO_V3.0
"""Test script for DirectoryProcessor."""

import sys
import os
import tempfile
import time
sys.path.append('/workspaces/app')

from core.directory_processor import DirectoryProcessor

def create_test_directory():
    """Create a test directory with sample files."""
    test_dir = tempfile.mkdtemp(prefix="yapmo_test_")
    
    # Create subdirectories
    os.makedirs(os.path.join(test_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "videos"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "documents"), exist_ok=True)
    
    # Create test files
    test_files = [
        ("images", "sample1.jpg"),
        ("images", "sample2.png"),
        ("images", "sample3.gif"),
        ("videos", "sample1.mp4"),
        ("videos", "sample2.avi"),
        ("documents", "sample1.txt"),  # This should be ignored
        ("documents", "sample2.pdf"),  # This should be ignored
    ]
    
    for subdir, filename in test_files:
        file_path = os.path.join(test_dir, subdir, filename)
        with open(file_path, 'w') as f:
            f.write(f"Test content for {filename}")
    
    return test_dir

def progress_callback(event_type: str, data):
    """Test progress callback."""
    if event_type == 'directory_processed':
        print(f"  - Directory processed: {data}")
    elif event_type == 'file_processed':
        print(f"  - File processed: {data}")
    elif event_type == 'processing_progress':
        print(f"  - Processing progress: {data}")

def test_directory_processor():
    """Test the DirectoryProcessor."""
    
    print("Testing DirectoryProcessor...")
    print("=" * 50)
    
    # Create test directory
    test_dir = create_test_directory()
    print(f"Created test directory: {test_dir}")
    
    # Test data
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Create directory processor
    processor = DirectoryProcessor(max_workers=2, progress_callback=progress_callback)
    
    print("Created DirectoryProcessor")
    
    # Process directory
    print(f"\nProcessing directory: {test_dir}")
    result = processor.process_directory(test_dir, image_extensions, video_extensions)
    
    # Check result
    if result.get('success', False):
        print("✓ Directory processing completed successfully")
        stats = result.get('stats', {})
        print(f"Statistics: {stats}")
        
        # Verify statistics
        expected_files = 5  # 3 images + 2 videos (documents should be ignored)
        if stats.get('total_files') == expected_files:
            print(f"✓ Total files correct: {stats['total_files']}")
        else:
            print(f"✗ Total files incorrect: expected {expected_files}, got {stats.get('total_files')}")
        
        if stats.get('successful_files') == expected_files:
            print(f"✓ Successful files correct: {stats['successful_files']}")
        else:
            print(f"✗ Successful files incorrect: expected {expected_files}, got {stats.get('successful_files')}")
        
        if stats.get('directories_scanned') >= 3:  # At least 3 subdirectories
            print(f"✓ Directories scanned correct: {stats['directories_scanned']}")
        else:
            print(f"✗ Directories scanned incorrect: got {stats.get('directories_scanned')}")
        
        if stats.get('elapsed_time', 0) > 0:
            print(f"✓ Elapsed time recorded: {stats['elapsed_time']:.2f} seconds")
        else:
            print("✗ Elapsed time not recorded")
        
    else:
        print(f"✗ Directory processing failed: {result.get('error', 'Unknown error')}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    print(f"\nCleaned up test directory: {test_dir}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_directory_processor()
