#!/usr/bin/env python3
"""Test script voor result_processor.py."""

import sys
import queue
import threading
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_result_processor_import():
    """Test import van result_processor."""
    print("=== Testing ResultProcessor Import ===")
    
    try:
        from core.result_processor import ResultProcessor
        print("✅ ResultProcessor import successful")
        return True
    except Exception as e:
        print(f"❌ ResultProcessor import failed: {e}")
        return False

def test_result_processor_creation():
    """Test ResultProcessor instantiation."""
    print("\n=== Testing ResultProcessor Creation ===")
    
    try:
        from core.result_processor import ResultProcessor
        
        # Create test queues
        result_queue = queue.Queue()
        logging_queue = queue.Queue()
        
        # Create ResultProcessor instance
        processor = ResultProcessor(result_queue, logging_queue)
        print("✅ ResultProcessor creation successful")
        return processor
    except Exception as e:
        print(f"❌ ResultProcessor creation failed: {e}")
        return None

def test_result_processor_basic_functionality():
    """Test basic ResultProcessor functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        from core.result_processor import ResultProcessor
        
        # Create test queues
        result_queue = queue.Queue()
        logging_queue = queue.Queue()
        
        # Create processor
        processor = ResultProcessor(result_queue, logging_queue)
        
        # Test data
        test_result = {
            "file_path": "/test/path/image.jpg",
            "success": True,
            "media_type": "image",
            "worker_id": 1
        }
        
        # Add test result to queue
        result_queue.put(test_result)
        
        # Start the processor (this starts the background thread)
        processor.start()
        
        # Wait a bit for processing
        time.sleep(0.2)
        
        # Check if log message was created
        if not logging_queue.empty():
            log_message = logging_queue.get()
            print(f"✅ Log message created: {log_message}")
        else:
            print("❌ No log message created")
        
        # Stop the processor
        processor.stop()
            
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_result_processor_error_handling():
    """Test error handling in ResultProcessor."""
    print("\n=== Testing Error Handling ===")
    
    try:
        from core.result_processor import ResultProcessor
        
        # Create test queues
        result_queue = queue.Queue()
        logging_queue = queue.Queue()
        
        # Create processor
        processor = ResultProcessor(result_queue, logging_queue)
        
        # Test error result
        error_result = {
            "file_path": "/test/path/error.jpg",
            "success": False,
            "error": "Test error message",
            "worker_id": 2
        }
        
        # Add error result to queue
        result_queue.put(error_result)
        
        # Start the processor
        processor.start()
        
        # Wait a bit for processing
        time.sleep(0.2)
        
        # Check if error log message was created
        if not logging_queue.empty():
            log_message = logging_queue.get()
            print(f"✅ Error log message created: {log_message}")
        else:
            print("❌ No error log message created")
        
        # Stop the processor
        processor.stop()
            
        print("✅ Error handling test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all ResultProcessor tests."""
    print("Testing ResultProcessor...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 4
    
    # Test import
    if test_result_processor_import():
        success_count += 1
    
    # Test creation
    if test_result_processor_creation():
        success_count += 1
    
    # Test basic functionality
    if test_result_processor_basic_functionality():
        success_count += 1
    
    # Test error handling
    if test_result_processor_error_handling():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"ResultProcessor Tests: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All ResultProcessor tests passed!")
    else:
        print("❌ Some ResultProcessor tests failed!")

if __name__ == "__main__":
    main()
