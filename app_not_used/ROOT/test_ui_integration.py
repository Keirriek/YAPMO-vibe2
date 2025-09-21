#YAPMO_V3.0
"""Test script for UI Integration with Progress Tracker."""

import sys
import os
import time
import threading
sys.path.append('/workspaces/app')

from core.progress_tracker import ProgressTracker

def simulate_ui_callback(event_type: str, data):
    """Simulate UI callback for testing."""
    if event_type == 'processing_progress':
        print(f"UI Update: {data['processed_files']}/{data['total_files']} files "
              f"({data['file_progress']*100:.1f}%) - "
              f"{data['files_per_second']:.2f} files/sec - "
              f"ETA: {data['estimated_time_remaining']:.1f}s")

def test_ui_integration():
    """Test UI integration with progress tracker."""
    
    print("Testing UI Integration...")
    print("=" * 50)
    
    # Create progress tracker with UI callback
    tracker = ProgressTracker(progress_callback=simulate_ui_callback)
    
    print("Created ProgressTracker with UI callback")
    
    # Start processing
    total_files = 15
    total_directories = 3
    tracker.start_processing(total_files, total_directories)
    
    print(f"Started processing: {total_files} files, {total_directories} directories")
    
    # Simulate file processing with UI updates
    print("\nSimulating file processing with UI updates...")
    for i in range(total_files):
        # Simulate some processing time
        time.sleep(0.2)
        
        # Simulate success/failure (80% success rate)
        success = (i % 5) != 0
        tracker.update_file_processed(success)
        
        # Update directory every 5 files
        if (i + 1) % 5 == 0:
            tracker.update_directory_processed()
    
    # Final UI update
    print("\nFinal UI state:")
    final_data = tracker.get_progress_data()
    simulate_ui_callback('processing_progress', final_data)
    
    # Verify completion
    if tracker.is_complete():
        print("✓ Processing completed successfully")
    else:
        print("✗ Processing not completed")
    
    print("\n" + "=" * 50)
    print("UI Integration test completed!")

if __name__ == "__main__":
    test_ui_integration()
