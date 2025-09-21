#YAPMO_V3.0
"""Test script for ParallelWorkerManager."""

import sys
import os
import time
sys.path.append('/workspaces/app')

from core.parallel_worker_manager import ParallelWorkerManager

def progress_callback(event_type: str, data: dict):
    """Test progress callback."""
    print(f"Progress callback: {event_type} - {data}")

def test_parallel_worker_manager():
    """Test the ParallelWorkerManager."""
    
    print("Testing ParallelWorkerManager...")
    print("=" * 50)
    
    # Test data
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    # Test files
    test_files = [
        "/test/images/sample1.jpg",
        "/test/images/sample2.png", 
        "/test/videos/sample1.mp4",
        "/test/videos/sample2.avi",
        "/test/documents/sample.txt",  # This should fail
        "/test/images/sample3.gif"
    ]
    
    # Create worker manager
    manager = ParallelWorkerManager(max_workers=2, progress_callback=progress_callback)
    
    print(f"Created manager with {manager.max_workers} workers")
    
    # Submit files
    print(f"\nSubmitting {len(test_files)} files...")
    for file_path in test_files:
        manager.submit_file(file_path, image_extensions, video_extensions)
    
    print(f"Submitted files. Pending: {len(manager.pending_futures)}")
    
    # Process completed workers
    print("\nProcessing completed workers...")
    max_iterations = 20  # Prevent infinite loop
    iteration = 0
    
    while not manager.is_complete() and iteration < max_iterations:
        completed = manager.process_completed_workers()
        if completed > 0:
            print(f"Processed {completed} completed workers")
        
        # Check queues
        result_queue = manager.get_result_queue()
        logging_queue = manager.get_logging_queue()
        
        print(f"  - Pending futures: {len(manager.pending_futures)}")
        print(f"  - Result queue size: {result_queue.qsize()}")
        print(f"  - Logging queue size: {logging_queue.qsize()}")
        
        # Process some results from queues
        results_processed = 0
        while not result_queue.empty() and results_processed < 3:
            try:
                result = result_queue.get_nowait()
                print(f"  - Result: {result.get('success', 'unknown')} - {result.get('file_path', 'unknown')}")
                results_processed += 1
            except:
                break
        
        # Process some logs from queues
        logs_processed = 0
        while not logging_queue.empty() and logs_processed < 3:
            try:
                log_msg = logging_queue.get_nowait()
                print(f"  - Log: {log_msg}")
                logs_processed += 1
            except:
                break
        
        time.sleep(0.1)  # Small delay
        iteration += 1
    
    # Final stats
    stats = manager.get_stats()
    print(f"\nFinal stats: {stats}")
    
    # Check if complete
    if manager.is_complete():
        print("✓ All work completed successfully")
    else:
        print("✗ Work not completed (timeout or error)")
    
    # Shutdown
    manager.shutdown()
    print("Manager shutdown completed")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_parallel_worker_manager()
