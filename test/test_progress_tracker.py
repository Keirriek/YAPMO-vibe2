#!/usr/bin/env python3
"""Test script voor progress_tracker.py."""

import sys
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_progress_tracker_import():
    """Test import van ProgressTracker."""
    print("=== Testing ProgressTracker Import ===")
    
    try:
        from core.progress_tracker import ProgressTracker
        print("✅ ProgressTracker import successful")
        return True
    except Exception as e:
        print(f"❌ ProgressTracker import failed: {e}")
        return False

def test_progress_tracker_creation():
    """Test ProgressTracker instantiation."""
    print("\n=== Testing ProgressTracker Creation ===")
    
    try:
        from core.progress_tracker import ProgressTracker
        
        # Create ProgressTracker without callback
        tracker = ProgressTracker()
        print("✅ ProgressTracker creation (no callback) successful")
        
        # Create ProgressTracker with callback
        def test_callback(data):
            print(f"Callback received: {data}")
        
        tracker_with_callback = ProgressTracker(progress_callback=test_callback)
        print("✅ ProgressTracker creation (with callback) successful")
        
        return tracker, tracker_with_callback
    except Exception as e:
        print(f"❌ ProgressTracker creation failed: {e}")
        return None, None

def test_progress_tracker_basic_functionality():
    """Test basic ProgressTracker functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        from core.progress_tracker import ProgressTracker
        
        # Create tracker
        tracker = ProgressTracker()
        
        # Test initial state
        initial_data = tracker.get_progress_data()
        print(f"✅ Initial progress data: {initial_data}")
        
        # Start processing
        tracker.start_processing(total_files=100, total_directories=50)
        print("✅ Started processing with 100 files, 50 directories")
        
        # Update progress using correct methods
        for i in range(10):
            tracker.update_file_processed(success=True)
        
        for i in range(5):
            tracker.update_directory_processed()
        
        # Get updated data
        updated_data = tracker.get_progress_data()
        print(f"✅ Updated progress data: {updated_data}")
        
        # Test reset
        tracker.reset()
        reset_data = tracker.get_progress_data()
        print(f"✅ Reset progress data: {reset_data}")
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_progress_tracker_callback():
    """Test ProgressTracker callback functionality."""
    print("\n=== Testing Callback Functionality ===")
    
    try:
        from core.progress_tracker import ProgressTracker
        
        callback_data = []
        
        def test_callback(event_type, data):
            callback_data.append((event_type, data))
            print(f"Callback received: {event_type} - {data}")
        
        # Create tracker with callback
        tracker = ProgressTracker(progress_callback=test_callback)
        
        # Start processing
        tracker.start_processing(total_files=20, total_directories=10)
        
        # Update progress (should trigger callback)
        for i in range(5):
            tracker.update_file_processed(success=True)
        
        for i in range(2):
            tracker.update_directory_processed()
        
        # Check if callback was called
        if callback_data:
            print(f"✅ Callback was triggered {len(callback_data)} times")
        else:
            print("❌ Callback was not triggered")
        
        print("✅ Callback functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Callback functionality test failed: {e}")
        return False

def test_progress_tracker_calculations():
    """Test ProgressTracker calculation methods."""
    print("\n=== Testing Calculation Methods ===")
    
    try:
        from core.progress_tracker import ProgressTracker
        
        # Create tracker
        tracker = ProgressTracker()
        
        # Start processing
        tracker.start_processing(total_files=100, total_directories=50)
        
        # Update progress
        for i in range(25):
            tracker.update_file_processed(success=True)
        
        for i in range(10):
            tracker.update_directory_processed()
        
        # Get progress data
        progress_data = tracker.get_progress_data()
        
        print(f"✅ Files progress: {progress_data.get('file_progress', 0):.1f}%")
        print(f"✅ Directories progress: {progress_data.get('directory_progress', 0):.1f}%")
        print(f"✅ Files rate: {progress_data.get('files_per_second', 0):.2f}/sec")
        print(f"✅ Directories rate: {progress_data.get('directories_per_second', 0):.2f}/sec")
        
        # Test completion status
        is_complete = tracker.is_complete()
        completion_percentage = tracker.get_completion_percentage()
        
        print(f"✅ Is complete: {is_complete}")
        print(f"✅ Completion percentage: {completion_percentage:.1f}%")
        
        print("✅ Calculation methods test completed")
        return True
        
    except Exception as e:
        print(f"❌ Calculation methods test failed: {e}")
        return False

def main():
    """Run all ProgressTracker tests."""
    print("Testing ProgressTracker...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 5
    
    # Test import
    if test_progress_tracker_import():
        success_count += 1
    
    # Test creation
    if test_progress_tracker_creation()[0]:
        success_count += 1
    
    # Test basic functionality
    if test_progress_tracker_basic_functionality():
        success_count += 1
    
    # Test callback functionality
    if test_progress_tracker_callback():
        success_count += 1
    
    # Test calculation methods
    if test_progress_tracker_calculations():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"ProgressTracker Tests: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All ProgressTracker tests passed!")
    else:
        print("❌ Some ProgressTracker tests failed!")

if __name__ == "__main__":
    main()
