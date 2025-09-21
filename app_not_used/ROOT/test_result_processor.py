#YAPMO_V3.0
"""Test script for ResultProcessor."""

import sys
import os
import time
import queue
sys.path.append('/workspaces/app')

from core.result_processor import ResultProcessor

def test_result_processor():
    """Test the ResultProcessor."""
    
    print("Testing ResultProcessor...")
    print("=" * 50)
    
    # Create queues
    result_queue = queue.Queue()
    logging_queue = queue.Queue()
    
    # Create result processor
    processor = ResultProcessor(result_queue, logging_queue)
    
    print("Created ResultProcessor")
    
    # Start processor
    processor.start()
    print("Started ResultProcessor")
    
    # Test data - successful results
    success_results = [
        {
            "success": True,
            "file_path": "/test/images/sample1.jpg",
            "media_type": "image",
            "json_data": {"filename": "sample1.jpg", "mediatype": "image"}
        },
        {
            "success": True,
            "file_path": "/test/videos/sample1.mp4",
            "media_type": "video",
            "json_data": {"filename": "sample1.mp4", "mediatype": "video"}
        }
    ]
    
    # Test data - failed results
    failure_results = [
        {
            "success": False,
            "file_path": "/test/documents/sample.txt",
            "error": "Unsupported file type: .txt"
        }
    ]
    
    # Add results to queue
    print(f"\nAdding {len(success_results)} success results to queue...")
    for result in success_results:
        result_queue.put(result)
        print(f"  - Added: {result['file_path']}")
    
    print(f"\nAdding {len(failure_results)} failure results to queue...")
    for result in failure_results:
        result_queue.put(result)
        print(f"  - Added: {result['file_path']}")
    
    # Wait for processing
    print("\nWaiting for processing...")
    time.sleep(2.0)  # Give time for processing
    
    # Check stats
    stats = processor.get_stats()
    print(f"\nProcessor stats: {stats}")
    
    # Check logging queue
    print(f"\nLogging queue size: {logging_queue.qsize()}")
    print("Log messages:")
    while not logging_queue.empty():
        try:
            log_msg = logging_queue.get_nowait()
            print(f"  - {log_msg}")
        except queue.Empty:
            break
    
    # Check if queue is empty
    if processor.is_queue_empty():
        print("✓ Result queue is empty")
    else:
        print("✗ Result queue is not empty")
    
    # Test completion
    print("\nTesting completion...")
    completed = processor.wait_for_completion(timeout=5.0)
    if completed:
        print("✓ All results processed successfully")
    else:
        print("✗ Timeout waiting for completion")
    
    # Stop processor
    processor.stop()
    print("Processor stopped")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_result_processor()
