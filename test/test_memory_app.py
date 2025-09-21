#!/usr/bin/env python3
"""
Memory Leak Test voor Fill Database V2 - App Integration

Test memory leaks met de daadwerkelijke app, maar met minimal imports
"""

import gc
import psutil
import sys
import time
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

def test_app_memory_leaks() -> None:
    """Test memory leaks with actual app functionality."""
    print("🔍 App Memory Leak Test")
    print("=" * 25)
    
    # Test directory setup
    test_dir = Path("/workspaces/test/app_test")
    test_dir.mkdir(exist_ok=True)
    
    # Create dummy files
    for i in range(10):
        (test_dir / f"test_{i}.jpg").write_text(f"Dummy content {i}")
    
    try:
        # Import only what we need
        from app.yapmo_globals import yapmo_globals
        from app.worker_functions import dummy_worker_process
        
        print("✅ Basic imports successful")
        
        # Test worker function directly
        print("\n🧪 Testing worker function memory usage:")
        
        process = psutil.Process()
        before_mb = process.memory_info().rss / 1024 / 1024
        print(f"   Before worker: {before_mb:.2f} MB")
        
        # Run worker function
        result = dummy_worker_process(str(test_dir / "test_0.jpg"), 1)
        
        after_mb = process.memory_info().rss / 1024 / 1024
        print(f"   After worker: {after_mb:.2f} MB")
        print(f"   Worker diff: {after_mb - before_mb:.2f} MB")
        
        # Test multiple workers
        print(f"\n🧪 Testing multiple workers:")
        
        for cycle in range(3):
            before_cycle = process.memory_info().rss / 1024 / 1024
            
            # Run multiple workers
            results = []
            for i in range(5):
                result = dummy_worker_process(str(test_dir / f"test_{i}.jpg"), i)
                results.append(result)
            
            after_cycle = process.memory_info().rss / 1024 / 1024
            cycle_diff = after_cycle - before_cycle
            
            print(f"   Cycle {cycle + 1}: {before_cycle:.2f} → {after_cycle:.2f} MB ({cycle_diff:+.2f} MB)")
            
            # Force cleanup
            del results
            gc.collect()
            time.sleep(0.1)
        
        # Test global variables
        print(f"\n🧪 Testing global variables:")
        print(f"   action_finished_flag: {yapmo_globals.action_finished_flag}")
        print(f"   ui_update_finished: {yapmo_globals.ui_update_finished}")
        print(f"   stop_processing_flag: {yapmo_globals.stop_processing_flag}")
        print(f"   abort_requested: {yapmo_globals.abort_requested}")
        
        print(f"\n✅ App memory testing completed")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This is expected - we're testing minimal functionality")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test directory
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)

def test_parallel_worker_memory() -> None:
    """Test memory usage of parallel worker system."""
    print(f"\n🔍 Parallel Worker Memory Test")
    print("=" * 35)
    
    try:
        # Import ParallelWorkerManager
        from app.pages.fill_db_page_v2 import ParallelWorkerManager
        
        print("✅ ParallelWorkerManager import successful")
        
        # Test directory setup
        test_dir = Path("/workspaces/test/parallel_test")
        test_dir.mkdir(exist_ok=True)
        
        # Create test files
        for i in range(20):
            (test_dir / f"test_{i}.jpg").write_text(f"Dummy content {i}")
        
        process = psutil.Process()
        
        # Test worker manager creation
        print(f"\n🧪 Testing ParallelWorkerManager creation:")
        before_mb = process.memory_info().rss / 1024 / 1024
        print(f"   Before manager: {before_mb:.2f} MB")
        
        # Create worker manager
        worker_manager = ParallelWorkerManager(max_workers=4)
        
        after_create_mb = process.memory_info().rss / 1024 / 1024
        print(f"   After creation: {after_create_mb:.2f} MB")
        print(f"   Creation diff: {after_create_mb - before_mb:.2f} MB")
        
        # Test worker submission
        print(f"\n🧪 Testing worker submission:")
        before_submit_mb = process.memory_info().rss / 1024 / 1024
        
        # Submit workers
        for i in range(10):
            worker_manager.submit_file(str(test_dir / f"test_{i}.jpg"), i)
        
        after_submit_mb = process.memory_info().rss / 1024 / 1024
        print(f"   Before submit: {before_submit_mb:.2f} MB")
        print(f"   After submit: {after_submit_mb:.2f} MB")
        print(f"   Submit diff: {after_submit_mb - before_submit_mb:.2f} MB")
        
        # Test cleanup
        print(f"\n🧪 Testing cleanup:")
        before_cleanup_mb = process.memory_info().rss / 1024 / 1024
        
        worker_manager.cleanup()
        del worker_manager
        gc.collect()
        time.sleep(0.5)
        
        after_cleanup_mb = process.memory_info().rss / 1024 / 1024
        print(f"   Before cleanup: {before_cleanup_mb:.2f} MB")
        print(f"   After cleanup: {after_cleanup_mb:.2f} MB")
        print(f"   Cleanup diff: {after_cleanup_mb - before_cleanup_mb:.2f} MB")
        
        # Check if memory was properly freed
        cleanup_diff = before_cleanup_mb - after_cleanup_mb
        if cleanup_diff > 0:
            print(f"   ✅ Memory properly freed: {cleanup_diff:.2f} MB")
        else:
            print(f"   ⚠️  Memory not fully freed: {cleanup_diff:.2f} MB")
        
        print(f"\n✅ Parallel worker memory testing completed")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   ParallelWorkerManager not available")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup test directory
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)

def main() -> None:
    """Run app memory leak tests."""
    print("🧪 Fill Database V2 - App Memory Testing")
    print("=" * 45)
    
    try:
        test_app_memory_leaks()
        test_parallel_worker_memory()
        
        print(f"\n✅ App memory testing completed successfully")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
