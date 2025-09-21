#!/usr/bin/env python3
"""
Memory Leak Testing voor Fill Database V2

Test scenario's:
1. Herhaalde scan/process cycles
2. ProcessPoolExecutor cleanup
3. Queue memory management
4. Worker process cleanup
"""

import gc
import os
import psutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

# Test directory setup
TEST_DIR = "/workspaces/test/test_data"
TEST_FILES = [
    "test_image_1.jpg",
    "test_image_2.png", 
    "test_video_1.mp4",
    "test_sidecar_1.xmp"
]

def setup_test_environment() -> None:
    """Create test directory and files."""
    test_path = Path(TEST_DIR)
    test_path.mkdir(parents=True, exist_ok=True)
    
    # Create dummy test files
    for filename in TEST_FILES:
        file_path = test_path / filename
        if not file_path.exists():
            file_path.write_text(f"Dummy content for {filename}")

def cleanup_test_environment() -> None:
    """Clean up test directory."""
    test_path = Path(TEST_DIR)
    if test_path.exists():
        import shutil
        shutil.rmtree(test_path)

def get_memory_info() -> Dict[str, float]:
    """Get current memory usage information."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
        'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
        'percent': process.memory_percent(),
        'num_threads': process.num_threads(),
        'num_fds': process.num_fds() if hasattr(process, 'num_fds') else 0
    }

def get_process_count() -> int:
    """Get number of active processes."""
    return len(psutil.pids())

def force_garbage_collection() -> None:
    """Force garbage collection."""
    gc.collect()
    time.sleep(0.1)  # Give time for cleanup

def test_memory_leak_cycles(max_cycles: int = 10) -> List[Dict[str, Any]]:
    """
    Test for memory leaks by running multiple scan/process cycles.
    
    Args:
        max_cycles: Number of cycles to run
        
    Returns:
        List of memory measurements per cycle
    """
    print(f"🧪 Testing memory leaks over {max_cycles} cycles...")
    
    # Import here to avoid circular imports
    try:
        from app.pages.fill_db_page_v2 import FillDatabasePageV2
        from app.yapmo_globals import yapmo_globals
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return []
    
    measurements = []
    
    # Initialize app
    app = FillDatabasePageV2()
    
    for cycle in range(max_cycles):
        print(f"\n📊 Cycle {cycle + 1}/{max_cycles}")
        
        # Force garbage collection before cycle
        force_garbage_collection()
        
        # Measure memory before cycle
        before_memory = get_memory_info()
        before_processes = get_process_count()
        
        print(f"   Before: {before_memory['rss_mb']:.2f} MB RSS, {before_processes} processes")
        
        try:
            # Simulate complete scan/process cycle
            print("   🔍 Starting scan...")
            app._set_state(app.ApplicationState.SCANNING)
            app._scan_directory_pure(TEST_DIR)
            app._set_state(app.ApplicationState.IDLE_ACTION_DONE)
            
            # Wait for UI updates
            time.sleep(0.5)
            
            print("   ⚙️ Starting processing...")
            app._set_state(app.ApplicationState.PROCESSING)
            app._process_files_parallel(TEST_DIR)
            app._set_state(app.ApplicationState.IDLE_ACTION_DONE)
            
            # Wait for completion
            time.sleep(1.0)
            
            # Force cleanup
            if hasattr(app, 'worker_manager') and app.worker_manager:
                app.worker_manager.cleanup()
            
            # Wait for cleanup
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error in cycle {cycle + 1}: {e}")
            continue
        
        # Measure memory after cycle
        force_garbage_collection()
        after_memory = get_memory_info()
        after_processes = get_process_count()
        
        # Calculate differences
        memory_diff = after_memory['rss_mb'] - before_memory['rss_mb']
        process_diff = after_processes - before_processes
        
        print(f"   After:  {after_memory['rss_mb']:.2f} MB RSS, {after_processes} processes")
        print(f"   Diff:   {memory_diff:+.2f} MB RSS, {process_diff:+d} processes")
        
        # Check for potential leaks
        if memory_diff > 10:  # More than 10MB increase
            print(f"   ⚠️  POTENTIAL MEMORY LEAK: {memory_diff:.2f} MB increase")
        
        if process_diff > 0:
            print(f"   ⚠️  PROCESS LEAK: {process_diff} processes not cleaned up")
        
        # Store measurement
        measurements.append({
            'cycle': cycle + 1,
            'before_memory': before_memory,
            'after_memory': after_memory,
            'memory_diff': memory_diff,
            'before_processes': before_processes,
            'after_processes': after_processes,
            'process_diff': process_diff
        })
    
    return measurements

def test_queue_memory() -> None:
    """Test if queues are properly cleared after processing."""
    print("\n🧪 Testing queue memory management...")
    
    try:
        from app.pages.fill_db_page_v2 import FillDatabasePageV2
        
        app = FillDatabasePageV2()
        
        # Run processing
        app._set_state(app.ApplicationState.PROCESSING)
        app._process_files_parallel(TEST_DIR)
        
        # Wait for completion
        time.sleep(2.0)
        
        # Check queue states
        if hasattr(app, 'worker_manager') and app.worker_manager:
            result_queue_size = app.worker_manager.result_queue.qsize()
            logging_queue_size = app.worker_manager.logging_queue.qsize()
            
            print(f"   Result queue size: {result_queue_size}")
            print(f"   Logging queue size: {logging_queue_size}")
            
            if result_queue_size > 0:
                print("   ⚠️  RESULT QUEUE NOT EMPTIED!")
            
            if logging_queue_size > 0:
                print("   ⚠️  LOGGING QUEUE NOT EMPTIED!")
            
            # Test cleanup
            app.worker_manager.cleanup()
            time.sleep(0.5)
            
            result_queue_size_after = app.worker_manager.result_queue.qsize()
            logging_queue_size_after = app.worker_manager.logging_queue.qsize()
            
            print(f"   After cleanup - Result queue: {result_queue_size_after}, Logging queue: {logging_queue_size_after}")
            
        else:
            print("   ❌ No worker manager found")
            
    except Exception as e:
        print(f"   ❌ Error testing queue memory: {e}")

def test_worker_cleanup() -> None:
    """Test if worker processes are properly cleaned up."""
    print("\n🧪 Testing worker process cleanup...")
    
    try:
        from app.pages.fill_db_page_v2 import FillDatabasePageV2
        
        app = FillDatabasePageV2()
        
        # Count processes before
        before_processes = get_process_count()
        print(f"   Processes before: {before_processes}")
        
        # Run processing
        app._set_state(app.ApplicationState.PROCESSING)
        app._process_files_parallel(TEST_DIR)
        
        # Wait for completion
        time.sleep(2.0)
        
        # Count processes during
        during_processes = get_process_count()
        print(f"   Processes during: {during_processes}")
        
        # Force cleanup
        if hasattr(app, 'worker_manager') and app.worker_manager:
            app.worker_manager.cleanup()
        
        # Wait for cleanup
        time.sleep(1.0)
        
        # Count processes after
        after_processes = get_process_count()
        print(f"   Processes after: {after_processes}")
        
        process_diff = after_processes - before_processes
        print(f"   Process difference: {process_diff:+d}")
        
        if process_diff > 0:
            print(f"   ⚠️  WORKER PROCESSES NOT CLEANED UP: {process_diff} processes remaining")
        else:
            print("   ✅ Worker processes properly cleaned up")
            
    except Exception as e:
        print(f"   ❌ Error testing worker cleanup: {e}")

def analyze_memory_trends(measurements: List[Dict[str, Any]]) -> None:
    """Analyze memory trends across cycles."""
    if not measurements:
        print("❌ No measurements to analyze")
        return
    
    print("\n📈 Memory Trend Analysis:")
    
    memory_diffs = [m['memory_diff'] for m in measurements]
    process_diffs = [m['process_diff'] for m in measurements]
    
    # Calculate statistics
    avg_memory_diff = sum(memory_diffs) / len(memory_diffs)
    max_memory_diff = max(memory_diffs)
    min_memory_diff = min(memory_diffs)
    
    avg_process_diff = sum(process_diffs) / len(process_diffs)
    max_process_diff = max(process_diffs)
    
    print(f"   Average memory difference: {avg_memory_diff:+.2f} MB")
    print(f"   Max memory difference: {max_memory_diff:+.2f} MB")
    print(f"   Min memory difference: {min_memory_diff:+.2f} MB")
    print(f"   Average process difference: {avg_process_diff:+.1f}")
    print(f"   Max process difference: {max_process_diff:+d}")
    
    # Check for trends
    if avg_memory_diff > 5:
        print("   ⚠️  CONSISTENT MEMORY LEAK DETECTED")
    elif max_memory_diff > 20:
        print("   ⚠️  SPORADIC MEMORY LEAK DETECTED")
    else:
        print("   ✅ No significant memory leaks detected")
    
    if avg_process_diff > 0.5:
        print("   ⚠️  CONSISTENT PROCESS LEAK DETECTED")
    elif max_process_diff > 2:
        print("   ⚠️  SPORADIC PROCESS LEAK DETECTED")
    else:
        print("   ✅ No significant process leaks detected")

def main() -> None:
    """Run all memory leak tests."""
    print("🔍 Fill Database V2 - Memory Leak Testing")
    print("=" * 50)
    
    # Setup test environment
    setup_test_environment()
    
    try:
        # Run tests
        measurements = test_memory_leak_cycles(max_cycles=5)
        test_queue_memory()
        test_worker_cleanup()
        
        # Analyze results
        analyze_memory_trends(measurements)
        
        print("\n✅ Memory leak testing completed")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test environment
        cleanup_test_environment()

if __name__ == "__main__":
    main()
