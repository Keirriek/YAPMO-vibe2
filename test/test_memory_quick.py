#!/usr/bin/env python3
"""
Quick Memory Leak Test voor Fill Database V2

Snelle test voor development - 3 cycles max
"""

import gc
import psutil
import sys
import time
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, '/workspaces')

def quick_memory_test() -> None:
    """Quick memory leak test - 3 cycles."""
    print("🚀 Quick Memory Leak Test")
    print("=" * 30)
    
    # Setup test directory
    test_dir = Path("/workspaces/test/quick_test")
    test_dir.mkdir(exist_ok=True)
    
    # Create dummy files
    for i in range(5):
        (test_dir / f"test_{i}.jpg").write_text(f"Dummy content {i}")
    
    try:
        from app.pages.fill_db_page_v2 import FillDatabasePageV2
        
        app = FillDatabasePageV2()
        
        for cycle in range(3):
            print(f"\n📊 Cycle {cycle + 1}/3")
            
            # Memory before
            process = psutil.Process()
            before_mb = process.memory_info().rss / 1024 / 1024
            
            # Run processing
            app._set_state(app.ApplicationState.PROCESSING)
            app._process_files_parallel(str(test_dir))
            
            # Wait and cleanup
            time.sleep(1.0)
            if hasattr(app, 'worker_manager') and app.worker_manager:
                app.worker_manager.cleanup()
            
            # Memory after
            gc.collect()
            after_mb = process.memory_info().rss / 1024 / 1024
            diff_mb = after_mb - before_mb
            
            print(f"   Memory: {before_mb:.1f} → {after_mb:.1f} MB ({diff_mb:+.1f} MB)")
            
            if diff_mb > 10:
                print(f"   ⚠️  LEAK: {diff_mb:.1f} MB increase")
            else:
                print(f"   ✅ OK: {diff_mb:.1f} MB change")
        
        print("\n✅ Quick test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)

if __name__ == "__main__":
    quick_memory_test()
