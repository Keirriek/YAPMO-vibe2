#YAPMO_V3.0
"""Test script for LoggingIntegration."""

import sys
import os
import time
import queue
sys.path.append('/workspaces/app')

from core.logging_integration import LoggingIntegration

def test_logging_integration():
    """Test the LoggingIntegration."""
    
    print("Testing LoggingIntegration...")
    print("=" * 50)
    
    # Create logging queue
    logging_queue = queue.Queue()
    
    # Create logging integration
    integration = LoggingIntegration(logging_queue)
    
    print("Created LoggingIntegration")
    
    # Start integration
    integration.start()
    print("Started LoggingIntegration")
    
    # Test log messages
    test_messages = [
        "DEBUG: Worker 1: Starting process_single_file for /test/images/sample1.jpg",
        "INFO: Successfully processed image file: /test/images/sample1.jpg",
        "WARNING: Failed to process file /test/documents/sample.txt: Unsupported file type",
        "ERROR: Critical error in worker process",
        "INFO: Processing completed successfully"
    ]
    
    # Add messages to queue
    print(f"\nAdding {len(test_messages)} log messages to queue...")
    for i, message in enumerate(test_messages, 1):
        logging_queue.put(message)
        print(f"  - Added message {i}: {message}")
    
    # Wait for processing
    print("\nWaiting for processing...")
    time.sleep(2.0)  # Give time for processing
    
    # Check processed count
    processed_count = integration.get_processed_count()
    print(f"\nProcessed {processed_count} log messages")
    
    # Check if queue is empty
    if integration.is_queue_empty():
        print("✓ Logging queue is empty")
    else:
        print("✗ Logging queue is not empty")
    
    # Test completion
    print("\nTesting completion...")
    completed = integration.wait_for_completion(timeout=5.0)
    if completed:
        print("✓ All log messages processed successfully")
    else:
        print("✗ Timeout waiting for completion")
    
    # Stop integration
    integration.stop()
    print("Integration stopped")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("Note: Check the log output above to see if messages were processed correctly")

if __name__ == "__main__":
    test_logging_integration()
