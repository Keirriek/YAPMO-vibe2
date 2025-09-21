#YAPMO_V3.0
"""Test script for ProgressTracker."""

import sys
import os
import time
import threading
sys.path.append('/workspaces/app')

from core.progress_tracker import ProgressTracker

def progress_callback(event_type: str, data):
    """Test progress callback."""
    if event_type == 'processing_progress':
        print(f"Progress update: {data['processed_files']}/{data['total_files']} files, "
              f"{data['processed_directories']}/{data['total_directories']} directories, "
              f"{data['files_per_second']:.2f} files/sec, "
              f"ETA: {data['estimated_time_remaining']:.2f}s")

def test_progress_tracker():
    """Test the ProgressTracker."""
    
    print("Testing ProgressTracker...")
    print("=" * 50)
    
    # Create progress tracker
    tracker = ProgressTracker(progress_callback=progress_callback)
    
    print("Created ProgressTracker")
    
    # Start processing
    total_files = 20
    total_directories = 5
    tracker.start_processing(total_files, total_directories)
    
    print(f"Started processing: {total_files} files, {total_directories} directories")
    
    # Simulate file processing
    print("\nSimulating file processing...")
    for i in range(total_files):
        # Simulate some processing time
        time.sleep(0.1)
        
        # Simulate success/failure (90% success rate)
        success = (i % 10) != 0
        tracker.update_file_processed(success)
        
        # Update directory every 4 files
        if (i + 1) % 4 == 0:
            tracker.update_directory_processed()
    
    # Final progress data
    print("\nFinal progress data:")
    final_data = tracker.get_progress_data()
    for key, value in final_data.items():
        print(f"  {key}: {value}")
    
    # Check completion
    if tracker.is_complete():
        print("✓ Processing completed successfully")
    else:
        print("✗ Processing not completed")
    
    completion_percentage = tracker.get_completion_percentage()
    print(f"Completion percentage: {completion_percentage:.1f}%")
    
    # Test reset
    print("\nTesting reset...")
    tracker.reset()
    reset_data = tracker.get_progress_data()
    print(f"After reset - processed_files: {reset_data['processed_files']}")
    
    print("\n" + "=" * 50)
    print("ProgressTracker test completed!")

if __name__ == "__main__":
    test_progress_tracker()
