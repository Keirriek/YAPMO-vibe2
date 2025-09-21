#!/usr/bin/env python3
"""Test script voor logging_integration.py."""

import sys
import queue
import time
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_logging_integration_import():
    """Test import van LoggingIntegration."""
    print("=== Testing LoggingIntegration Import ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        print("✅ LoggingIntegration import successful")
        return True
    except Exception as e:
        print(f"❌ LoggingIntegration import failed: {e}")
        return False

def test_logging_integration_creation():
    """Test LoggingIntegration instantiation."""
    print("\n=== Testing LoggingIntegration Creation ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create test logging queue
        logging_queue = queue.Queue()
        
        # Create LoggingIntegration instance
        integration = LoggingIntegration(logging_queue)
        print("✅ LoggingIntegration creation successful")
        
        return integration
    except Exception as e:
        print(f"❌ LoggingIntegration creation failed: {e}")
        return None

def test_logging_integration_basic_functionality():
    """Test basic LoggingIntegration functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create test logging queue
        logging_queue = queue.Queue()
        
        # Create integration
        integration = LoggingIntegration(logging_queue)
        
        # Add test log message to queue
        test_log = "INFO: Test log message"
        logging_queue.put(test_log)
        
        # Start the integration (this starts the background thread)
        integration.start()
        
        # Wait a bit for processing
        time.sleep(0.2)
        
        # Check if message was processed
        processed_count = integration.get_processed_count()
        print(f"✅ Processed count: {processed_count}")
        
        # Stop the integration
        integration.stop()
        
        print("✅ Basic functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_logging_integration_different_levels():
    """Test LoggingIntegration with different log levels."""
    print("\n=== Testing Different Log Levels ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create test logging queue
        logging_queue = queue.Queue()
        
        # Create integration
        integration = LoggingIntegration(logging_queue)
        
        # Test different log levels
        test_logs = [
            "INFO: Info message",
            "WARNING: Warning message", 
            "ERROR: Error message",
            "DEBUG: Debug message"
        ]
        
        # Add all test logs to queue
        for log in test_logs:
            logging_queue.put(log)
        
        # Start the integration
        integration.start()
        
        # Wait for processing
        time.sleep(0.3)
        
        # Check processed count
        processed_count = integration.get_processed_count()
        print(f"✅ Processed {processed_count} log messages")
        
        # Stop the integration
        integration.stop()
        
        print("✅ Different log levels test completed")
        return True
        
    except Exception as e:
        print(f"❌ Different log levels test failed: {e}")
        return False

def test_logging_integration_empty_queue():
    """Test LoggingIntegration with empty queue."""
    print("\n=== Testing Empty Queue ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create empty logging queue
        logging_queue = queue.Queue()
        
        # Create integration
        integration = LoggingIntegration(logging_queue)
        
        # Start integration with empty queue
        integration.start()
        
        # Wait a bit
        time.sleep(0.1)
        
        # Check if queue is empty
        is_empty = integration.is_queue_empty()
        print(f"✅ Queue is empty: {is_empty}")
        
        # Stop the integration
        integration.stop()
        
        print("✅ Empty queue test completed")
        return True
        
    except Exception as e:
        print(f"❌ Empty queue test failed: {e}")
        return False

def test_logging_integration_error_handling():
    """Test error handling in LoggingIntegration."""
    print("\n=== Testing Error Handling ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create test logging queue
        logging_queue = queue.Queue()
        
        # Create integration
        integration = LoggingIntegration(logging_queue)
        
        # Test with malformed log message
        malformed_log = "INVALID_FORMAT: This is not a proper log format"
        logging_queue.put(malformed_log)
        
        # Start integration
        integration.start()
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check processed count
        processed_count = integration.get_processed_count()
        print(f"✅ Processed {processed_count} log messages (including malformed)")
        
        # Stop the integration
        integration.stop()
        
        print("✅ Error handling test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_logging_integration_continuous_processing():
    """Test continuous log processing."""
    print("\n=== Testing Continuous Processing ===")
    
    try:
        from core.logging_integration import LoggingIntegration
        
        # Create test logging queue
        logging_queue = queue.Queue()
        
        # Create integration
        integration = LoggingIntegration(logging_queue)
        
        # Add multiple log messages
        for i in range(5):
            log_message = f"INFO: Continuous test message {i+1}"
            logging_queue.put(log_message)
        
        # Start integration
        integration.start()
        
        # Wait for processing
        time.sleep(0.3)
        
        # Check processed count
        processed_count = integration.get_processed_count()
        print(f"✅ Processed {processed_count} log messages continuously")
        
        # Stop the integration
        integration.stop()
        
        print("✅ Continuous processing test completed")
        return True
        
    except Exception as e:
        print(f"❌ Continuous processing test failed: {e}")
        return False

def main():
    """Run all LoggingIntegration tests."""
    print("Testing LoggingIntegration...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 7
    
    # Test import
    if test_logging_integration_import():
        success_count += 1
    
    # Test creation
    if test_logging_integration_creation():
        success_count += 1
    
    # Test basic functionality
    if test_logging_integration_basic_functionality():
        success_count += 1
    
    # Test different log levels
    if test_logging_integration_different_levels():
        success_count += 1
    
    # Test empty queue
    if test_logging_integration_empty_queue():
        success_count += 1
    
    # Test error handling
    if test_logging_integration_error_handling():
        success_count += 1
    
    # Test continuous processing
    if test_logging_integration_continuous_processing():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"LoggingIntegration Tests: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("✅ All LoggingIntegration tests passed!")
    else:
        print("❌ Some LoggingIntegration tests failed!")

if __name__ == "__main__":
    main()
