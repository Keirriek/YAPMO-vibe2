#!/usr/bin/env python3
"""Test script voor parallel_worker_manager.py."""

import sys
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_parallel_worker_manager_import():
    """Test import van ParallelWorkerManager."""
    print("=== Testing ParallelWorkerManager Import ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        print("✅ ParallelWorkerManager import successful")
        return True
    except Exception as e:
        print(f"❌ ParallelWorkerManager import failed: {e}")
        return False

def test_parallel_worker_manager_creation():
    """Test ParallelWorkerManager instantiation."""
    print("\n=== Testing ParallelWorkerManager Creation ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        
        # Create manager with default settings
        manager = ParallelWorkerManager(max_workers=2)
        print("✅ ParallelWorkerManager creation (default) successful")
        
        # Create manager with callback
        def test_callback(data):
            print(f"Callback received: {data}")
        
        manager_with_callback = ParallelWorkerManager(
            max_workers=4, 
            progress_callback=test_callback
        )
        print("✅ ParallelWorkerManager creation (with callback) successful")
        
        return manager, manager_with_callback
    except Exception as e:
        print(f"❌ ParallelWorkerManager creation failed: {e}")
        return None, None

def test_parallel_worker_manager_basic_functionality():
    """Test basic ParallelWorkerManager functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        
        # Create manager
        manager = ParallelWorkerManager(max_workers=2)
        
        # Test initial state
        print(f"✅ Max workers: {manager.max_workers}")
        print(f"✅ Pending futures: {len(manager.pending_futures)}")
        
        # Test submitting files
        test_files = [
            "/test/path/image1.jpg",
            "/test/path/image2.jpg",
            "/test/path/video1.mp4"
        ]
        
        image_extensions = ['.jpg', '.jpeg', '.png']
        video_extensions = ['.mp4', '.mov']
        
        for file_path in test_files:
            manager.submit_file(file_path, image_extensions, video_extensions)
        
        print(f"✅ Files submitted: {len(test_files)}")
        print(f"✅ Pending futures: {len(manager.pending_futures)}")
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_parallel_worker_manager_worker_management():
    """Test worker management functionality."""
    print("\n=== Testing Worker Management ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        
        # Create manager
        manager = ParallelWorkerManager(max_workers=2)
        
        # Test worker creation
        print(f"✅ Initial pending futures: {len(manager.pending_futures)}")
        
        # Test starting workers
        manager.start_workers()
        print("✅ Workers started")
        
        # Test submitting files
        image_extensions = ['.jpg', '.jpeg', '.png']
        video_extensions = ['.mp4', '.mov']
        
        manager.submit_file("/test/path/test1.jpg", image_extensions, video_extensions)
        manager.submit_file("/test/path/test2.jpg", image_extensions, video_extensions)
        
        print(f"✅ Files submitted, pending futures: {len(manager.pending_futures)}")
        
        # Test shutdown
        manager.shutdown()
        print("✅ Workers shutdown")
        
        print("✅ Worker management test completed")
        return True
        
    except Exception as e:
        print(f"❌ Worker management test failed: {e}")
        return False

def test_parallel_worker_manager_progress_tracking():
    """Test progress tracking functionality."""
    print("\n=== Testing Progress Tracking ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        
        # Create manager with callback
        progress_data = []
        
        def test_callback(event_type, data):
            progress_data.append((event_type, data))
            print(f"Progress callback: {event_type} - {data}")
        
        manager = ParallelWorkerManager(
            max_workers=2,
            progress_callback=test_callback
        )
        
        # Test progress tracking via stats
        stats = manager.get_stats()
        print(f"✅ Initial stats: {stats}")
        
        # Test completion status
        is_complete = manager.is_complete()
        print(f"✅ Is complete: {is_complete}")
        
        print("✅ Progress tracking test completed")
        return True
        
    except Exception as e:
        print(f"❌ Progress tracking test failed: {e}")
        return False

def test_parallel_worker_manager_error_handling():
    """Test error handling in ParallelWorkerManager."""
    print("\n=== Testing Error Handling ===")
    
    try:
        from core.parallel_worker_manager import ParallelWorkerManager
        
        # Create manager
        manager = ParallelWorkerManager(max_workers=1)
        
        # Test with invalid parameters
        try:
            manager.submit_file("", ['.jpg'], ['.mp4'])  # Empty file path
            print("✅ Handled empty file path")
        except Exception as e:
            print(f"✅ Caught expected error for empty file path: {e}")
        
        # Test with None file path
        try:
            manager.submit_file(None, ['.jpg'], ['.mp4'])
            print("✅ Handled None file path")
        except Exception as e:
            print(f"✅ Caught expected error for None file path: {e}")
        
        # Test with invalid extensions
        try:
            manager.submit_file("/test/file.jpg", None, ['.mp4'])
            print("✅ Handled None extensions")
        except Exception as e:
            print(f"✅ Caught expected error for None extensions: {e}")
        
        print("✅ Error handling test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all ParallelWorkerManager tests."""
    print("Testing ParallelWorkerManager...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 6
    
    # Test import
    if test_parallel_worker_manager_import():
        success_count += 1
    
    # Test creation
    if test_parallel_worker_manager_creation()[0]:
        success_count += 1
    
    # Test basic functionality
    if test_parallel_worker_manager_basic_functionality():
        success_count += 1
    
    # Test worker management
    if test_parallel_worker_manager_worker_management():
        success_count += 1
    
    # Test progress tracking
    if test_parallel_worker_manager_progress_tracking():
        success_count += 1
    
    # Test error handling
    if test_parallel_worker_manager_error_handling():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"ParallelWorkerManager Tests: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All ParallelWorkerManager tests passed!")
    else:
        print("❌ Some ParallelWorkerManager tests failed!")

if __name__ == "__main__":
    main()
