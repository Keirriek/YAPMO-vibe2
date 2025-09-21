#!/usr/bin/env python3
"""
Simple Memory Leak Test voor Fill Database V2

Test alleen memory monitoring zonder volledige app loading
"""

import gc
import psutil
import sys
import time
from pathlib import Path

def test_memory_monitoring() -> None:
    """Test basic memory monitoring functionality."""
    print("🔍 Simple Memory Monitoring Test")
    print("=" * 35)
    
    # Test memory monitoring
    process = psutil.Process()
    
    print(f"📊 Current Process Info:")
    print(f"   PID: {process.pid}")
    print(f"   Memory RSS: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"   Memory VMS: {process.memory_info().vms / 1024 / 1024:.2f} MB")
    print(f"   Memory %: {process.memory_percent():.1f}%")
    print(f"   Threads: {process.num_threads()}")
    print(f"   FDs: {process.num_fds() if hasattr(process, 'num_fds') else 'N/A'}")
    
    # Test memory allocation/deallocation
    print(f"\n🧪 Testing Memory Allocation:")
    
    # Allocate memory
    before_mb = process.memory_info().rss / 1024 / 1024
    print(f"   Before allocation: {before_mb:.2f} MB")
    
    # Create some data
    data = []
    for i in range(1000):
        data.append(f"Test data string {i}" * 100)
    
    after_alloc_mb = process.memory_info().rss / 1024 / 1024
    print(f"   After allocation: {after_alloc_mb:.2f} MB")
    print(f"   Allocation diff: {after_alloc_mb - before_mb:.2f} MB")
    
    # Deallocate memory
    del data
    gc.collect()
    time.sleep(0.1)
    
    after_dealloc_mb = process.memory_info().rss / 1024 / 1024
    print(f"   After deallocation: {after_dealloc_mb:.2f} MB")
    print(f"   Deallocation diff: {after_dealloc_mb - after_alloc_mb:.2f} MB")
    
    # Check if memory was properly freed
    memory_freed = after_alloc_mb - after_dealloc_mb
    if memory_freed > 0:
        print(f"   ✅ Memory properly freed: {memory_freed:.2f} MB")
    else:
        print(f"   ⚠️  Memory not fully freed: {memory_freed:.2f} MB")
    
    print(f"\n📈 Final Memory State:")
    print(f"   Current RSS: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"   Threads: {process.num_threads()}")
    print(f"   FDs: {process.num_fds() if hasattr(process, 'num_fds') else 'N/A'}")

def test_process_monitoring() -> None:
    """Test process monitoring functionality."""
    print(f"\n🔍 Process Monitoring Test")
    print("=" * 30)
    
    # Count total processes
    total_processes = len(psutil.pids())
    print(f"📊 Total system processes: {total_processes}")
    
    # Count Python processes
    python_processes = []
    for pid in psutil.pids():
        try:
            proc = psutil.Process(pid)
            if 'python' in proc.name().lower():
                python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"🐍 Python processes: {len(python_processes)}")
    
    # Show current Python process details
    current_proc = psutil.Process()
    print(f"📋 Current Python process:")
    print(f"   PID: {current_proc.pid}")
    print(f"   Name: {current_proc.name()}")
    print(f"   Memory: {current_proc.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"   CPU: {current_proc.cpu_percent():.1f}%")
    print(f"   Threads: {current_proc.num_threads()}")

def test_import_dependencies() -> None:
    """Test if we can import the required modules."""
    print(f"\n🔍 Import Dependencies Test")
    print("=" * 30)
    
    # Test basic imports
    try:
        import gc
        print("✅ gc module: OK")
    except ImportError as e:
        print(f"❌ gc module: {e}")
    
    try:
        import psutil
        print("✅ psutil module: OK")
    except ImportError as e:
        print(f"❌ psutil module: {e}")
    
    try:
        import sys
        print("✅ sys module: OK")
    except ImportError as e:
        print(f"❌ sys module: {e}")
    
    try:
        import time
        print("✅ time module: OK")
    except ImportError as e:
        print(f"❌ time module: {e}")
    
    try:
        from pathlib import Path
        print("✅ pathlib module: OK")
    except ImportError as e:
        print(f"❌ pathlib module: {e}")
    
    # Test app directory structure
    app_dir = Path("/workspaces/app")
    if app_dir.exists():
        print("✅ /workspaces/app directory: OK")
        
        # Check for key files
        key_files = [
            "pages/fill_db_page_v2.py",
            "yapmo_globals.py",
            "worker_functions.py"
        ]
        
        for file_path in key_files:
            full_path = app_dir / file_path
            if full_path.exists():
                print(f"✅ {file_path}: OK")
            else:
                print(f"❌ {file_path}: Missing")
    else:
        print("❌ /workspaces/app directory: Missing")

def main() -> None:
    """Run all simple memory tests."""
    print("🧪 Fill Database V2 - Simple Memory Testing")
    print("=" * 50)
    
    try:
        test_import_dependencies()
        test_memory_monitoring()
        test_process_monitoring()
        
        print(f"\n✅ Simple memory testing completed successfully")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
